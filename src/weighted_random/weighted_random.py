import bisect
from typing import Optional
from .binary_index_tree import BinaryIndexTree
from .utils import create_table, random_int, random_by_table


class WeightedRandom:
	""" 接受给定权重列表, 依据权重每次随机获取一个对应的位置. 
	
	Note:
		权重要求是整数.
		权重列表不能为空, 不能包含负权重; 总权重不能为0.
		如果需要支持pick, 则接受权重后, 原始权重不能修改.

	Args:
		weight (list[int]): 权重列表. 
		pick (bool): 是否需要支持无重复取样. 默认为 `False`.

	Attributes:
		avg (int): 计算后的权重均值.
		probs (list[int]): 每一个位置自身占据的权重.
		alias (list[int]): 如果自身没有占满权重, 则为补充权重的来源位置.
		bit (object): 树状数组. 支持快速无重复取样.

	"""

	__slots__ = ("avg", "probs", "alias", "bit")

	def __init__(self, weight: list[int], pick: bool = False):
		avg, probs, alias = create_table(weight)
		self.avg = avg
		self.probs = probs
		self.alias = alias
		if pick:
			self.bit = BinaryIndexTree(weight)
		else:
			self.bit = None

	def get(self) -> int:
		""" 依据权重随机获取一个位置 """
		return random_by_table(self.avg, self.probs, self.alias)

	def pick(self, count: int) -> list[int]:
		""" 依据权重, 选择 `count` 个位置.

		Note:
			当 初始化时 `pick` 为 False(默认) 时, 无法使用此函数(抛出ValueError).
			当 `count` 大于非0权重位置个数时, 将使用位置0填充.

		Args:
			count (int): 需要选择的位置个数.

		Returns:
			list[int]: 选择的位置列表.

		"""
		if self.bit is None:
			raise ValueError(f"if you want to use `pick`, set `pick` = True when init {self.__class__.__name__}.")

		if count == 1:
			return [self.get()]

		return self.bit.pick(count)

	def __repr__(self) -> str:
		title = f"{self.__class__.__name__}:"
		avg = f"\tavg: {self.avg}"
		probs = f"\tprobs: {self.probs}"
		alias = f"\talias: {self.alias}"
		return "\n".join([title, avg, probs, alias])

	def __call__(self) -> int:
		return self.get()


class WeightedRandomBulk:
	""" 接受一组权重列表. `WeightedRandom` 的批量版本. """

	__slots__ = ("info", "bits")

	def __init__(self, weight_list: list[list[int]], pick: bool = False):
		self.info = [create_table(w) for w in weight_list]
		if pick:
			self.bits = [BinaryIndexTree(w) for w in weight_list]
		else:
			self.bits = None

	def get(self, index: int = 0) -> int:
		""" 根据指定的权重选项, 返回随机选择的位置 """
		avg, probs, alias = self.info[index]
		return random_by_table(avg, probs, alias)

	def pick(self, count: int, index: int = 0) -> list[int]:
		""" 
		根据指定的权重选择, 返回无重复选择的位置. 
		同样的, 如果初始化时 `pick` 为 False, 则无法使用此函数. 
		"""
		if self.bits is None:
			raise ValueError(f"if you want to use `pick`, set `pick` = True when init {self.__class__.__name__}.")

		if count == 1:
			return [self.get(index)]

		return self.bits[index].pick(count)

	def __call__(self, index: int = 0) -> int:
		return self.get(index)


class WeightedWheel(WeightedRandom):
	""" 
	接受权重, 以及每一个位置上对应的值. 
	`WeightedRandom` 的简易包装版本. 
	"""

	__slots__ = ("wheel", )

	def __init__(self, wheel: list, weight: list[int], pick: bool = False):
		super().__init__(weight, pick)
		self.wheel = wheel

	def get(self):
		""" 根据权重, 返回随机选择的值. """
		index = super().get()
		return self.wheel[index]

	def pick(self, count: int) -> list:
		""" 
		依据权重, 选择 `count` 个(无重复位置)随机选择的 `wheel` 值. 
		要求初始化时 `pick` 为 True 
		"""
		indexs = super().pick(count)
		return [self.wheel[index] for index in indexs]

	def __call__(self):
		return self.get()


class WeightedWheelBulk(WeightedRandomBulk):
	"""
	接受权重列表, 以及每一个位置上对应的值. 
	`WeightedRandomBulk` 的简易包装版本. 
	"""

	__slots__ = ("wheel", )

	def __init__(self, wheel: list, weight_list: list[list[int]], pick: bool = False):
		super().__init__(weight_list, pick)
		self.wheel = wheel

	def get(self, index: int = 0):
		""" 根据指定的权重选项, 返回随机选择的值 """
		pos = super().get(index)
		return self.wheel[pos]

	def pick(self, count: int, index: int = 0) -> list:
		""" 
		根据指定权重选项, 选择 `count` 个(无重复位置)随机选择的 wheel 值. 
		要求初始化时 `pick` 为 True 
		"""
		indexs = super().pick(count, index)
		return [self.wheel[index] for index in indexs]

	def __call__(self, index: int = 0):
		return self.get(index)
