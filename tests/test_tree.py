import random
import unittest
from fractions import Fraction

from weighted_random import Node, WeightedWheelTree, flatten


UP_CONFIG = [
	("SSR", 1, [
		("UP", 7, [
			("角色A", 1, None),
			("角色B", 1, None),
		]),
		("非UP", 3, [
			("角色A", 1, None),
			("角色C", 3, None),
			("角色D", 6, None),
		]),
	]),
]


def exact_probs(nodes: list) -> dict:
	""" 参考实现: 用 Fraction 逐层计算每个 key 的真实概率. """
	acc = {}

	def walk(group, prob):
		total = sum(weight for _key, weight, _children in group)
		for key, weight, children in group:
			p = prob * Fraction(weight, total)
			if p == 0:  # 0 权重的祖先 -> 整棵子树都取不到;
				continue
			if children:
				walk(children, p)
			else:
				acc[key] = acc.get(key, 0) + p

	walk(nodes, Fraction(1))
	return acc


def flat_probs(keys: list, weights: list[int]) -> dict:
	""" 把扁平结果转换成 key -> 概率. """
	total = sum(weights)
	acc = {}
	for key, weight in zip(keys, weights):
		acc[key] = acc.get(key, 0) + Fraction(weight, total)
	return acc


def random_tree(rng: random.Random, depth: int) -> list:
	""" 随机生成嵌套配置. 故意复用 key, 以覆盖同 key 跨分支的情况. """
	count = rng.randint(1, 4)
	while True:
		weights = [rng.choice([0, 0, 1, 2, 3, 5]) for _ in range(count)]
		if sum(weights) > 0:
			break

	nodes = []
	for i, weight in enumerate(weights):
		children = random_tree(rng, depth - 1) if depth > 1 and rng.random() < 0.7 else None
		nodes.append((f"k{i}", weight, children))
	return nodes


class TestFlatten(unittest.TestCase):

	def test_exact_against_fraction(self):
		# 随机嵌套配置, 与逐层 Fraction 参考实现做精确比对;
		rng = random.Random(20240926)
		for _ in range(300):
			config = random_tree(rng, 4)
			keys, weights = flatten(config)
			self.assertEqual(len(keys), len(weights))
			self.assertGreater(sum(weights), 0)
			self.assertEqual(flat_probs(keys, weights), exact_probs(config))

	def test_nested_weight_is_not_naive_product(self):
		# 不同分支的本层总权重不同, 直接相乘是错的;
		config = [
			("X", 1, None),
			("Y", 1, [("y1", 1, None), ("y2", 1, None)]),
		]
		probs = flat_probs(*flatten(config))
		self.assertEqual(probs["X"], Fraction(1, 2))
		self.assertEqual(probs["y1"], Fraction(1, 4))
		self.assertEqual(probs["y2"], Fraction(1, 4))
		# 朴素相乘会得到 X: 1/3, y1: 1/3, y2: 1/3. 必须不相等, 防止被"优化"回去.
		self.assertNotEqual(probs["X"], Fraction(1, 3))

	def test_up_pool(self):
		# 先星级, 再 UP/非UP, 再角色;
		keys, weights = flatten(UP_CONFIG)
		self.assertEqual(keys, ["角色A", "角色B", "角色A", "角色C", "角色D"])
		self.assertEqual(weights, [35, 35, 3, 9, 18])
		self.assertEqual(sum(weights), 100)
		self.assertEqual(flat_probs(keys, weights), exact_probs(UP_CONFIG))

	def test_input_forms(self):
		# Node / dict / tuple 三种写法等价;
		tree = [Node("x", 1, [Node("y", 2, None), Node("z", 1, None)])]
		as_dict = [{"key": "x", "weight": 1, "children": [
			{"key": "y", "weight": 2},
			{"key": "z", "weight": 1, "children": None},
		]}]
		as_tuple = [("x", 1, [("y", 2), ("z", 1, [])])]
		expected = (["y", "z"], [2, 1])
		self.assertEqual(flatten(tree), expected)
		self.assertEqual(flatten(as_dict), expected)
		self.assertEqual(flatten(as_tuple), expected)

	def test_single_node(self):
		# 只有一个结果时, 权重被约分为1;
		keys, weights = flatten([("only", 5, None)])
		self.assertEqual(keys, ["only"])
		self.assertEqual(weights, [1])

	def test_deep_chain(self):
		# 深层单链, 结果唯一;
		config = [("leaf", 3, None)]
		for i in range(20):
			config = [(f"lv{i}", 2, config)]
		keys, weights = flatten(config)
		self.assertEqual(keys, ["leaf"])
		self.assertEqual(weights, [1])

	def test_zero_weight_pruned(self):
		# 0 权重分支(含其整棵子树)被剪掉;
		keys, weights = flatten([("a", 0, [("a1", 1, None)]), ("b", 1, None)])
		self.assertEqual((keys, weights), (["b"], [1]))

		keys, weights = flatten([("a", 1, None), ("b", 0, None), ("c", 3, None)])
		self.assertEqual((keys, weights), (["a", "c"], [1, 3]))

	def test_gcd_reduced(self):
		# 结果会被整体约分;
		keys, weights = flatten([("a", 4, None), ("b", 6, None)])
		self.assertEqual((keys, weights), (["a", "b"], [2, 3]))

	def test_errors(self):
		with self.assertRaises(ValueError):
			flatten([])

		with self.assertRaises(TypeError):
			flatten("not a list")

		with self.assertRaises(ValueError):
			flatten([("a", 0, None), ("b", 0, None)])

		with self.assertRaises(ValueError):
			flatten([("a", 1, [("x", 0, None), ("y", 0, None)])])

		with self.assertRaises(ValueError) as ctx:
			flatten([("SSR", 1, [("UP", -1, None)])])
		self.assertIn("SSR/UP", str(ctx.exception))

		with self.assertRaises(TypeError):
			flatten([("a", 1.5, None)])

		with self.assertRaises(ValueError):
			flatten([("a", 1, None, "extra")])

		with self.assertRaises(TypeError):
			flatten([42])

		with self.assertRaises(KeyError):
			flatten([{"key": "a"}])


class TestWeightedWheelTree(unittest.TestCase):

	def test_attributes(self):
		m = WeightedWheelTree(UP_CONFIG)
		self.assertEqual(m.keys, ["角色A", "角色B", "角色A", "角色C", "角色D"])
		self.assertEqual(m.weights, [35, 35, 3, 9, 18])
		self.assertEqual(m.total, 100)
		self.assertEqual(m.merged["角色A"], 38)
		self.assertEqual(sum(m.merged.values()), 100)
		self.assertEqual(m.paths[0], ("SSR", "UP", "角色A"))
		self.assertEqual(m.paths[2], ("SSR", "非UP", "角色A"))

	def test_draw(self):
		# 同 key 的不同分支要能区分出来;
		m = WeightedWheelTree(UP_CONFIG)
		random.seed(1)
		for _ in range(200):
			key, path = m.draw()
			self.assertEqual(path[-1], key)
			self.assertIn(path, [("SSR", "UP", "角色A"), ("SSR", "UP", "角色B"),
			                     ("SSR", "非UP", "角色A"), ("SSR", "非UP", "角色C"),
			                     ("SSR", "非UP", "角色D")])

	def test_merge(self):
		m = WeightedWheelTree(UP_CONFIG, merge=True)
		self.assertEqual(m.keys, ["角色A", "角色B", "角色C", "角色D"])
		self.assertEqual(m.weights, [38, 35, 9, 18])
		self.assertEqual(m.total, 100)
		self.assertIsNone(m.paths)
		key, path = m.draw()
		self.assertIsNone(path)
		self.assertIn(key, m.keys)

	def test_call_and_get(self):
		m = WeightedWheelTree(UP_CONFIG)
		self.assertIn(m(), m.keys)
		self.assertIn(m.get(), m.keys)

	def test_pick(self):
		m = WeightedWheelTree(UP_CONFIG, pick=True, merge=True)
		# 合并后不会取到重复 key;
		for _ in range(200):
			picked = m.pick(3)
			self.assertEqual(len(picked), 3)
			self.assertEqual(len(set(picked)), 3)
			for key in picked:
				self.assertIn(key, m.keys)

		# pick(1) 也要返回真正的 key;
		for _ in range(100):
			picked = m.pick(1)
			self.assertEqual(len(picked), 1)
			self.assertIn(picked[0], m.keys)

		# 未开启 pick 时不可用;
		with self.assertRaises(ValueError):
			WeightedWheelTree(UP_CONFIG).pick(2)

	def test_merge_requires_hashable(self):
		m = WeightedWheelTree([(["unhashable"], 1, None)])
		self.assertEqual(m.keys, [["unhashable"]])
		self.assertIsNone(m.merged)
		with self.assertRaises(TypeError):
			WeightedWheelTree([(["unhashable"], 1, None)], merge=True)

	def test_sampling_matches_weights(self):
		# 采样分布应与扁平权重一致(注意同 key 会在多个分支出现, 需要先合并);
		m = WeightedWheelTree(UP_CONFIG)
		expect = flat_probs(m.keys, m.weights)
		random.seed(42)
		times = 50000
		cnt = {}
		for _ in range(times):
			key = m.get()
			cnt[key] = cnt.get(key, 0) + 1

		for key, prob in expect.items():
			self.assertLess(abs(cnt.get(key, 0) / times - float(prob)), 0.01)

	def test_nested_sampling(self):
		# 嵌套深一点也要与解析概率一致;
		config = [
			("A", 3, [
				("A1", 1, [("a", 1, None), ("b", 4, None)]),
				("A2", 2, None),
			]),
			("B", 5, [("c", 1, None)]),
		]
		m = WeightedWheelTree(config)
		expect = exact_probs(config)
		random.seed(7)
		times = 50000
		cnt = {}
		for _ in range(times):
			key = m.get()
			cnt[key] = cnt.get(key, 0) + 1
		for key, prob in expect.items():
			self.assertLess(abs(cnt.get(key, 0) / times - float(prob)), 0.01)

	pass


if __name__ == '__main__':
	unittest.main()
