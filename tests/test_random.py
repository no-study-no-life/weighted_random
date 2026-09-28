import unittest
from weighted_random import random_int
from weighted_random import WeightedRandom 
from weighted_random import WeightedWheel, WeightedWheelBulk


def simula(m, ref: list[int], times: int = 10000, percent: float = 0.05):
	total = sum(ref)
	cnt = [0] * len(ref)
	prob = [0.0] * len(ref)
	for i, x in enumerate(ref):
		prob[i] = x / total

	for _ in range(times):
		idx = m.get()
		cnt[idx] += 1

	for i, x in enumerate(cnt):
		# 0权重的话, 不允许有出现;
		if ref[i] == 0: 
			if x > 0:
				return False
			else:
				continue
		actual = x / times
		# 与原始相差不能超过percent.
		if abs(actual / prob[i] - 1) > percent:
			return False
	return True


class TestWeightedRandom(unittest.TestCase):

	def test_random_int(self):
		# 测试产生随机数;
		self.assertEqual(random_int(1), 0)

		x = 100
		for _ in range(100):
			self.assertTrue(0 <= random_int(x) < x)
		

	def test_same_weight(self):
		# 测试相同的权重;
		weight = [1] * 10
		times = 100000
		percent = 0.05
		m = WeightedRandom(weight)
		self.assertTrue(simula(m, weight, times, percent))

	def test_incr_weight(self):
		# 测试递增权重
		weight = list(range(10))
		times = 100000
		percent = 0.05
		m = WeightedRandom(weight)
		self.assertTrue(simula(m, weight, times, percent))

	def test_big_weight(self):
		# 测试相差大的权重
		weight = [0, 1, 10, 100, 1000, 10000]
		times = 10000000
		percent = 0.05
		m = WeightedRandom(weight)
		self.assertTrue(simula(m, weight, times, percent))

	def test_simple_pick(self):
		# 测试简易无重复选择.
		weight = [0, 1, 1, 0, 1, 0]
		m = WeightedRandom(weight, pick=True)
		times = 10000
		percent = 0.05
		# pick all
		total = sum(weight)
		count = 3
		cnt = [0] * len(weight)
		for _ in range(times):
			idxs = m.pick(count)
			for idx in idxs:
				self.assertTrue(weight[idx] > 0)
				cnt[idx] += 1
		for (curr, actual) in zip(cnt, weight):
			curr /= times
			self.assertTrue(abs(curr - actual) < percent)

		# pick 2
		count = 2
		cnt = [0] * len(weight)
		for _ in range(times):
			idxs = m.pick(count)
			for idx in idxs:
				self.assertTrue(weight[idx] > 0)
				cnt[idx] += 1
		for (curr, actual) in zip(cnt, weight):
			curr /= times
			actual *= count / total
			self.assertTrue(abs(curr - actual) < percent)

	def test_pick_one(self):
		# pick(1) 必须等价于 get(), 不能因为父类内部调用 self.get() 
		# 而取到子类重写后的"值"(子类 get 返回的是 wheel 里的值, 不是位置).
		weight = [1, 0, 0, 3]
		m = WeightedRandom(weight, pick=True)
		for _ in range(100):
			idxs = m.pick(1)
			self.assertEqual(len(idxs), 1)
			self.assertTrue(weight[idxs[0]] > 0)

		# 值恰好也是合法下标时, 旧实现会静默返回错误的值;
		m = WeightedWheel([1, 0, 0], [1, 0, 0], pick=True)
		for _ in range(100):
			self.assertEqual(m.pick(1), [1])

		# 字符串轮盘在旧实现下会直接抛 TypeError;
		m = WeightedWheel(["a", "b"], [0, 1], pick=True)
		for _ in range(100):
			self.assertEqual(m.pick(1), ["b"])  # 0 权重不会被选中;

		# Bulk 版本同理;
		m = WeightedWheelBulk(["a", "b"], [[0, 1]], pick=True)
		for _ in range(100):
			self.assertEqual(m.pick(1), ["b"])
			self.assertEqual(m.pick(1, 0), ["b"])

	pass


if __name__ == '__main__':
	unittest.main()
