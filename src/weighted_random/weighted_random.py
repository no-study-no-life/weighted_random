from .utils import create_table, random_int, random_by_table


class WeightedRandom:
	""" 接受给定权重列表, 依据权重每次随机获取一个对应的位置. 
	
	Note:
		权重要求是整数.
		权重列表不能为空, 不能包含负权重; 总权重不能为0.

	Args:
		weight (list[int]): 权重列表. 

	Attributes:
		avg (int): 计算后的权重均值.
		probs (list[int]): 每一个位置自身占据的权重.
		alias (list[int]): 如果自身没有占满权重, 则为补充权重的来源位置.

	"""

	__slots__ = ("avg", "probs", "alias")

	def __init__(self, weight: list[int]):
		avg, probs, alias = create_table(weight)
		self.avg = avg
		self.probs = probs
		self.alias = alias

	def get(self) -> int:
		""" 依据权重随机获取一个位置 """
		return random_by_table(self.avg, self.probs, self.alias)

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

	__slots__ = ("info", )

	def __init__(self, weight_list: list[list[int]]):
		self.info = [create_table(w) for w in weight_list]

	def get(self, index: int = 0) -> int:
		""" 根据指定的权重选项, 返回随机选择的位置 """
		avg, probs, alias = self.info[index]
		return random_by_table(avg, probs, alias)

	def __call__(self, index: int = 0) -> int:
		return self.get(index)


class WeightedWheel(WeightedRandom):
	""" 
	接受权重, 以及每一个位置上对应的值. 
	`WeightedRandom` 的简易包装版本. 
	"""

	__slots__ = ("wheel", )

	def __init__(self, wheel, weight: list[int]):
		super().__init__(weight)
		self.wheel = wheel

	def get(self):
		""" 根据权重, 返回随机选择的值. """
		index = super().get()
		return self.wheel[index]

	def __call__(self):
		return self.get()


class WeightedWheelBulk(WeightedRandomBulk):
	"""
	接受权重列表, 以及每一个位置上对应的值. 
	`WeightedRandomBulk` 的简易包装版本. 
	"""

	__slots__ = ("wheel", )

	def __init__(self, wheel, weight_list: list[list[int]]):
		super().__init__(weight_list)
		self.wheel = wheel

	def get(self, index: int = 0):
		""" 根据指定的权重选项, 返回随机选择的值 """
		pos = super().get(index)
		return self.wheel[pos]

	def __call__(self, index: int = 0):
		return self.get(index)
