import math
import random

__all__ = [
	"create_table",
	"random_int",
	"random_by_table",
]


def create_table(weight: list[int]) -> tuple[int, list[int], list[int]]:
	"""
	依据传入的权重, 创建用于方便索引的数据表.

	Note:
		不允许包含负数权重. 不允许列表为空或权重全部为0.

	Args:
		weight (list[int]): 每一个位置的权重列表.

	Returns:
		tuple: avg, probs, alias.
			- avg (int): 计算后的权重均值. 
			- probs (list[int]): 每一个位置自身占据的权重.
			- alias (list[int]): 如果自身没有占满权重, 则为补充权重的来源位置.

	Raises:
		AssertError: 在非release模式下, ``weight``符合以下任意条件:
			- 包含负权重
			- 列表长度为0
			- 总权重为0

	"""

	assert len(weight) > 0, "empty weight!"
	assert all(v >= 0 for v in weight), "negative weight found!"
	total = sum(weight)
	assert total > 0, "zero weight!"

	length = len(weight)
	factor = math.gcd(total, length)  # 最大公因数
	multi = length // factor  # 需要乘以的倍数, 确保权重是整数
	less, more = [], []
	alias = [0] * length  # 别名位置;
	probs = [0] * length  # 自身概率;
	avg = total // factor  # 均值, 判断放入大还是小; (toatl * multi / length)
	for i, x in enumerate(weight):
		x *= multi
		probs[i] = x
		alias[i] = i;
		if x < avg:
			less.append(i)
		elif avg < x:
			more.append(i)
	
	# 平均化;
	while less and more:
		l, m = less.pop(), more.pop()
		probs[m] -= avg - probs[l]  # 空缺的一定要填满, 因为只能填一个;
		alias[l] = m  # 标记对应别名;
		# 检查剩余部分;
		if probs[m] < avg:
			less.append(m)
		elif avg < probs[m]:
			more.append(m)
	
	return avg, probs, alias


def random_int(to: int) -> int:
	""" 快速获取位于 [0, to) 的随机整数.
	
	Note:
		需要 ``to`` > 0. 否则会出现无限循环;  

	Args:
		to (int): 产生随机数的上界, 不包含在内.

	Returns:
		int: [0, to)范围的随机数.

	Raises:
		AssertError: 在非release模式下, ``to`` > 0 不满足时.

	"""
	assert to > 0

	k = (to - 1).bit_length()  # 需要python >= 3.9;
	r = random.getrandbits(k)
	while r >= to:
		r = random.getrandbits(k)
	return r


def random_by_table(avg: int, probs: list[int], alias: list[int]) -> int:
	""" 依据权重随机获取一个位置.
	
	Note:
		参数需要为 `create_table` 返回的结果.

	Args:
		avg (int): 平均权重;
		probs (list[int]): 每一个位置自身占据的权重.
		alias (list[int]): 如果自身没有占满权重, 则为补充权重的来源位置.

	Returns:
		int: 随机选择的位置

	"""
	length = len(probs)
	# 1. 选择基础位置
	pos = random_int(length)
	# 2. 判断是否需要替换
	r = random_int(avg)
	if r >= probs[pos]:
		pos = alias[pos]
	return pos
