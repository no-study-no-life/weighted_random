import unittest
from weighted_random import random_int
from weighted_random import WeightedRandom 


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
		times = 5000000
		percent = 0.05
		m = WeightedRandom(weight)
		self.assertTrue(simula(m, weight, times, percent))

	pass


if __name__ == '__main__':
	unittest.main()
