import warnings
from collections.abc import Hashable
from math import gcd
from typing import Any, NamedTuple, Optional

from .weighted_random import WeightedWheel

__all__ = [
	"Node",
	"flatten",
	"WeightedWheelTree",
]


class Node(NamedTuple):
	""" 嵌套权重配置中的一个节点. 

	Note:
		转换后的扁平权重是逐层通分得到的, 与"先按本层权重选分支, 再在分支内部
		按子权重选择"的结果完全等价(全程整数, 无浮点误差).
		**不能**把各层权重直接相乘, 因为不同分支的本层总权重不同, 分母并不统一. 

		``key`` 在**叶子**节点上代表最终结果; 在**内部**节点上仅作为层级路径的
		标签, 不参与结果输出. 
		``children`` 为 ``None`` 或空列表时, 该节点视为叶子. 

	Args:
		key (Hashable): 节点标识. 
		weight (int): 该节点在**当前层级**中的权重, 要求非负整数. 
		children (Optional[list]): 子节点列表, 元素同样接受 `Node`/`dict`/`tuple`. 

	"""

	key: Hashable
	weight: int
	children: Optional[list] = None


def _path_text(path: tuple) -> str:
	""" 把层级路径格式化为便于阅读的字符串. """
	return "/".join(str(key) for key in path) if path else "<root>"


def _as_node(item) -> Node:
	""" 把 `Node`/`dict`/`tuple` 统一转换为 `Node`. """
	if isinstance(item, Node):
		return item

	if isinstance(item, dict):
		try:
			key, weight = item["key"], item["weight"]
		except KeyError as err:
			raise KeyError(f"node dict must contain 'key' and 'weight', got: {sorted(item)}") from err
		return Node(key, weight, item.get("children"))

	if isinstance(item, (tuple, list)):
		if len(item) == 2:
			return Node(item[0], item[1], None)
		if len(item) == 3:
			return Node(item[0], item[1], item[2])
		raise ValueError(f"node tuple must have 2 or 3 items, got {len(item)}: {item!r}")

	raise TypeError(f"cannot parse node from {type(item).__name__}: {item!r}")


def _build_group(group, prefix: tuple) -> tuple[list[tuple], int]:
	""" 展开一个兄弟节点组. 

	Returns:
		tuple: 叶子条目列表 ``[(key, path, weight), ...]`` 与该组的总权重. 

	"""
	parts = []
	weight_sum = 0
	for item in group:
		node = _as_node(item)
		path = prefix + (node.key, )
		weight = node.weight
		if not isinstance(weight, int):
			raise TypeError(f"weight must be int, got {type(weight).__name__} at {_path_text(path)}")
		if weight < 0:
			raise ValueError(f"negative weight at {_path_text(path)}")
		if weight == 0:
			continue
		weight_sum += weight

		if node.children:
			entries, subtotal = _build_group(node.children, path)
		else:
			entries, subtotal = [(node.key, path, 1)], 1
		parts.append((weight, entries, subtotal))

	if weight_sum <= 0:
		raise ValueError(f"sum of weights must be positive at {_path_text(prefix)}")

	# 各子树返回的是"组内相对权重", 分母为各自的 subtotal;
	# 取这些 subtotal 的最小公倍数作为公共分母 common(用 lcm 而非乘积, 抑制权重膨胀),
	# 每个子树再乘 common // subtotal 折算到同一分母, 之后才能乘上本层权重合并;
	common = 1
	for _weight, _entries, subtotal in parts:
		common = common // gcd(common, subtotal) * subtotal

	out = []
	for weight, entries, subtotal in parts:
		factor = weight * (common // subtotal)
		out.extend((key, path, value * factor) for key, path, value in entries)

	# 整体约分, 抑制权重膨胀;
	divisor = 0
	for _key, _path, value in out:
		divisor = gcd(divisor, value)
	if divisor > 1:
		out = [(key, path, value // divisor) for key, path, value in out]

	return out, sum(value for _key, _path, value in out)


def _flatten(config) -> tuple[list[tuple], int]:
	""" 展开嵌套配置, 返回 ``[(key, path, weight), ...]`` 与总权重. """
	if not isinstance(config, (list, tuple)):
		raise TypeError(f"config must be a list of nodes, got {type(config).__name__}")
	if len(config) == 0:
		raise ValueError("empty config!")
	return _build_group(config, ())


def flatten(config) -> tuple[list, list[int]]:
	""" 把嵌套权重配置展开为扁平的 key 列表与总权重列表. 

	Note:
		同一个 key 出现在多个分支时, 会在结果中重复出现, 权重各自独立. 
		展开后的结果可直接用于 `WeightedWheel`, 一次取样即可得到最终结果. 

	Args:
		config (list): 嵌套配置, 元素接受 `Node`/`dict`/`tuple`. 

	Returns:
		tuple: ``(keys, weights)``, 两者一一对应且等长. 

	Raises:
		TypeError: ``config`` 不是列表, 节点格式无法解析, 或权重不是整数. 
		ValueError: ``config`` 为空, 节点元组长度不为2/3, 出现负权重, 或某一层权重全为0. 

	"""
	entries, _total = _flatten(config)
	return [key for key, _path, _weight in entries], [weight for _key, _path, weight in entries]


def _check_duplicate(entries: list[tuple]):
	""" 校验所有叶子 key 全局唯一. 

	Note:
		key 不可哈希时无法校验, 给出 UserWarning 后放行. 

	Raises:
		ValueError: 存在重复的 key, 信息中列出该 key 及它出现的所有路径. 

	"""
	seen = {}
	try:
		for key, path, _weight in entries:
			seen.setdefault(key, []).append(path)
	except TypeError:  # key 不可哈希, 无法校验;
		warnings.warn("keys are not hashable, duplicate keys cannot be checked", stacklevel=3)
		return

	duplicates = [(key, paths) for key, paths in seen.items() if len(paths) > 1]
	if duplicates:
		detail = "; ".join(
			f"{key!r} at {', '.join(_path_text(path) for path in paths)}"
			for key, paths in duplicates
		)
		raise ValueError(f"duplicate keys found: {detail}")


class WeightedWheelTree(WeightedWheel):
	""" 接受嵌套的权重配置, 展开为扁平的带权列表后取样. 
	`WeightedWheel` 的嵌套版本. 

	Note:
		展开过程全程使用整数, 与逐层多次取样完全等价; 之后每次 `get` 的
		时间复杂度仍为 O(1). 

		默认要求所有叶子 key 全局唯一, 出现重复 key 时抛出 ValueError;
		若同一个 key 确实需要在多个分支出现, 设置 ``allow_duplicate = True``
		保留每个分支一份(此时 `pick` 可能返回重复的 key). 
		key 不可哈希时无法校验唯一性, 会给出 UserWarning. 

	Args:
		config (list): 嵌套配置, 元素接受 `Node`/`dict`/`tuple`. 
		pick (bool): 是否需要支持无重复取样. 默认为 `False`. 
		allow_duplicate (bool): 是否允许出现重复的 key. 默认为 `False`. 

	Attributes:
		keys (list): 参与取样的 key 列表.
		weights (list[int]): 与 `keys` 一一对应的绝对权重列表.
		paths (list[tuple]): 与 `keys` 一一对应的层级路径. 
		total (int): 总权重. 

	"""

	__slots__ = ("keys", "weights", "paths", "total")

	def __init__(self, config, pick: bool = False, allow_duplicate: bool = False):
		entries, total = _flatten(config)
		if not allow_duplicate:
			_check_duplicate(entries)

		keys, paths, weights = map(list, zip(*entries))
		self.keys = keys
		self.weights = weights
		self.paths = paths
		self.total = total
		super().__init__(keys, weights, pick)

	def draw(self) -> tuple[Any, tuple]:
		""" 随机获取一个 key, 同时返回其层级路径(例如 ``("SSR", "UP", "角色A")``). """
		index = self._get_index()
		return self.wheel[index], self.paths[index]

	def __repr__(self) -> str:
		title = f"{self.__class__.__name__}:"
		total = f"\ttotal: {self.total}"
		keys = f"\tkeys: {self.keys}"
		weights = f"\tweights: {self.weights}"
		return "\n".join([title, total, keys, weights])
