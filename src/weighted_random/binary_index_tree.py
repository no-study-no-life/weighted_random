from .utils import random_int

__all__ = [
	"BinaryIndexTree",
]


def _low_bit(x):
	# 获取最低位. 假定 `x` > 0.
	return x & (-x) 


class BinaryIndexTree:
	""" 接受一个整数数组, 生成对应的 前缀和 树状数组.
	支持单点更新, 区间求和.

	Args:
		data (list[int]): 原始整数列表. 保证不会对其进行修改.

	Attributes:
		origin (list[int]): 原始数组. 方便快速更新数据.
		data (list[int]): 内部维护的树状数组.
	
	"""

	__slots__ = ("data", "ori")

	def __init__(self, data: list[int]):
		n = len(data)
		arr = [0] * (n + 1)
		
		for i in range(1, n + 1):
			arr[i] += data[i - 1]
			j = _low_bit(i) + i
			if j <= n:
				arr[j] += arr[i]
		
		self.data = arr
		self.ori = data

	def query(self, right: int) -> int:
		""" 查询区间 `[0, right]` 的前缀和. 含 `right` 位置.
		
		Args:
			right (int): 区间右端点(0 base, 闭区间);

		Returns:
			int: 区间 `[0, right]` 的前缀和.

		"""
		right += 1  # 内部实际 1 base 
		ans = 0
		while right > 0:
			ans += self.data[right]
			right &= right - 1
		return ans

	def __len__(self) -> int:
		return len(self.ori)

	def set(self, index: int, value: int):
		""" 更新位于索引 `index` 的值为 `value`.

		Args:
			index (int): 原始数据所在索引. 0 base.
			value (int): 需要更新的目标值.
		"""
		ori = self.ori[index]
		diff = value - ori
		index += 1  # 内部实际 1 base 
		n = len(self.data)
		while index < n:
			self.data[index] += diff
			index += _low_bit(index)

	def pick(self, count: int) -> list[int]:
		"""
		依据权重, 选择 `count` 个位置.

		Note:
			当 `count` 大于非0权重位置个数时, 将使用位置0填充.

		Args:
			count (int): 需要选择的位置个数.

		Returns:
			list[int]: 选择的位置列表.
		"""
		data = self.data[:]
		n = len(self.ori)
		ans = [0] * count
		total = self.query(n - 1)
		
		for i in range(count):
			if total <= 0:
				break
			r = random_int(total) + 1
			left, right = 0, n
			while left < right:
				mid = (left + right) // 2
				if self.query(mid) < r:
					left = mid + 1
				else:
					right = mid
			ans[i] = left
			total -= self.ori[left]
			self.set(left, 0)
		self.data = data
		return ans

