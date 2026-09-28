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
		weight_sum += weight

		if node.children:
			entries, subtotal = _build_group(node.children, path)
		else:
			entries, subtotal = [(node.key, path, 1)], 1
		parts.append((weight, entries, subtotal))

	if weight_sum <= 0:
		raise ValueError(f"sum of weights must be positive at {_path_text(prefix)}")

	# 逐层通分: 乘以各组总权重的最小公倍数, 保证不同分支的分母统一;
	common = 1
	for _weight, _entries, subtotal in parts:
		common = common // gcd(common, subtotal) * subtotal

	out = []
	for weight, entries, subtotal in parts:
		factor = weight * (common // subtotal)
		if factor:  # 0 权重的分支整棵剪掉;
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


def _merge(entries: list[tuple]) -> Optional[dict]:
	""" 把相同 key 的权重相加. key 不可哈希时返回 None. """
	merged = {}
	try:
		for key, _path, weight in entries:
			merged[key] = merged.get(key, 0) + weight
	except TypeError:  # key 不可哈希;
		return None
	return merged


class WeightedWheelTree(WeightedWheel):
	""" 接受嵌套的权重配置, 展开为扁平的带权列表后取样. 
	`WeightedWheel` 的嵌套版本. 

	Note:
		展开过程全程使用整数, 与逐层多次取样完全等价; 之后每次 `get` 的
		时间复杂度仍为 O(1). 

		同一个 key 出现在多个分支时, 默认保留多份(此时可用 `paths` 判断命中了
		哪个分支); 设置 ``merge = True`` 可将相同 key 的权重相加, 此时 `paths`
		为 ``None``. 无重复取样 `pick` 建议配合 ``merge = True``, 否则可能返回
		重复的 key. 

	Args:
		config (list): 嵌套配置, 元素接受 `Node`/`dict`/`tuple`. 
		pick (bool): 是否需要支持无重复取样. 默认为 `False`. 
		merge (bool): 是否合并相同 key 的权重. 默认为 `False`. 

	Attributes:
		keys (list): 参与取样的 key 列表(扁平, 或合并后的).
		weights (list[int]): 与 `keys` 一一对应的绝对权重列表.
		paths (Optional[list[tuple]]): 与 `keys` 一一对应的层级路径; 合并时为 ``None``. 
		total (int): 总权重. 
		merged (Optional[dict]): 相同 key 权重相加的结果; key 不可哈希时为 ``None``. 

	"""

	__slots__ = ("keys", "weights", "paths", "total", "merged")

	def __init__(self, config, pick: bool = False, merge: bool = False):
		entries, total = _flatten(config)
		merged = _merge(entries)

		if merge:
			if merged is None:
				raise TypeError("merge = True requires hashable keys")
			keys = list(merged)
			weights = list(merged.values())
			paths = None
		else:
			keys = [key for key, _path, _weight in entries]
			weights = [weight for _key, _path, weight in entries]
			paths = [path for _key, path, _weight in entries]

		self.keys = keys
		self.weights = weights
		self.paths = paths
		self.total = total
		self.merged = merged
		super().__init__(keys, weights, pick)

	def draw(self) -> tuple[Any, Optional[tuple]]:
		""" 随机获取一个 key, 同时返回其层级路径(例如 ``("SSR", "UP", "角色A")``). 

		Note:
			当 ``merge = True`` 时没有路径信息, 返回的路径为 ``None``. 

		"""
		index = self._get_index()
		path = None if self.paths is None else self.paths[index]
		return self.wheel[index], path

	def __repr__(self) -> str:
		title = f"{self.__class__.__name__}:"
		total = f"\ttotal: {self.total}"
		keys = f"\tkeys: {self.keys}"
		weights = f"\tweights: {self.weights}"
		return "\n".join([title, total, keys, weights])
