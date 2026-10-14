# WeightedRandom · 带权重的随机数生成工具

[![Tests](https://github.com/no-study-no-life/weighted_random/actions/workflows/test.yml/badge.svg)](https://github.com/no-study-no-life/weighted_random/actions/workflows/test.yml)
[![Python Version](https://img.shields.io/badge/python-3.9%20%7C%203.10%20%7C%203.11%20%7C%203.12%20%7C%203.13%20%7C%203.14-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

一个简易的 Python 随机库: 根据给定的非负整数权重, 随机选择对应位置的元素. 

尽量减少 `random` 的调用. 

内部 **完全使用整数** 实现, 避免浮点数误差. 

目前支持: 
- 单次带权取样. 
- 无重复多次带权/均匀取样.
- 嵌套权重的一次性展开取样(如: 先选星级, 再选 UP/非UP, 最后选角色).

## 时空复杂度

#### 无重复多次均匀取样(function: random_pick):

单次调用时间复杂度 $\mathcal{O}(n)$ , 空间复杂度 $\mathcal{O}(n)$ .
至多调用 `n` 次 `random_int`.

#### 无需多次带权取样(初始化参数 `pick = False`):

初始化时间复杂度 $\mathcal{O}(n)$ , 空间复杂度 $\mathcal{O}(n)$ . 
之后每次调用获取一个随机数的时间复杂度为 $\mathcal{O}(1)$ .

#### 需要使用多次带权取样(初始化参数 `pick = True`):

初始化时间复杂度 $\mathcal{O}(n \cdot \log n)$ , 空间复杂度 $\mathcal{O}(n)$ .

获取一个随机数的时间复杂度不变, 为 $\mathcal{O}(1)$ .
获取 `k` 个无重复位置的时间复杂度为 $\mathcal{O}(n + k \cdot \log^2 n)$ .

## Examples

#### 快速生成随机数
```python
from weighted_random import random_int

result = random_int(10)  # 需要确保参数大于0.
print(result)  # 随机输出 0 - 9的整数
```

#### 均匀随机取样
```python
from weighted_random import random_pick

src = ["red", "orange", "yellow", "green"]
n = 2
result = random_pick(src, n)
print(result)  # src 中任意 2 个元素的列表. 不检查 src 内是否有重复.
```

#### 按单个权重抽取
```python
from weighted_random import WeightedWheel

wheel = ["red", "orange", "yellow", "green"]
weight = [0, 3, 1, 2]
m = WeightedWheel(wheel, weight)

result = m.get()  # or: result = m()
# result为 "orange"/"yellow"/"green"中的一个;
# 由于"red"是0权重, 不会被选择.
```

#### 多个权重选择一个抽取
```python
from weighted_random import WeightedWheelBulk

wheel = [0, 1, 2, 3, 4, 5]
weights = [
	[1, 1, 1, 1, 1, 1],
	[0, 1, 2, 3, 4, 5],
	[1, 0, 0, 0, 0, 1],
]

m = WeightedWheelBulk(wheel, weights)

result1 = m.get(0)  # result1将在0-5随机选取;
result2 = m.get(1)  # result2将在1-4选取, 且选择的概率逐渐增加
```

#### 单权重无重复选取
```python
from weighted_random import WeightedWheel

wheel = ["red", "orange", "yellow", "green"]
weight = [0, 3, 1, 2]
m = WeightedWheel(wheel, weight, pick=True)

result = m.pick(2)
# result是一个列表, 可能包含 "orange"/"yellow"/"green" 的任意两个
# 出现概率为对应权重.
```

#### 嵌套权重一次性抽取
```python
from weighted_random import WeightedWheelTree

# 先按星级选, 再按 UP/非UP 选, 最后按角色权重选;
# 每一项是 (key, 当前层级权重, 子节点列表), 没有子节点则为叶子(即最终结果).
config = [
	("SSR", 1, [
		("UP",   7, [("角色A", 1), ("角色B", 1)]),
		("非UP", 3, [("角色C", 1), ("角色D", 3), ("角色E", 6)]),
	]),
	("SR", 9, [("角色F", 1), ("角色G", 1)]),
]

m = WeightedWheelTree(config)
result = m.get()      # 一次取样即可得到最终角色;
key, path = m.draw()  # 同时拿到层级路径(如 ("SSR", "UP", "角色A")), 可判断是否歪了;

print(m.total)  # 总权重;
print(m.paths)  # 与 keys 一一对应的层级路径;
```

> 默认要求所有叶子 `key` **全局唯一**, 出现重复 `key` 会抛出 `ValueError`(信息中会列出
> 该 key 及它出现的所有路径). 若同一个 `key` 确实需要出现在多个分支, 传 `allow_duplicate=True`,
> 此时每个分支各保留一份, 权重各自独立. `key` 不可哈希时无法校验唯一性, 会给出 `UserWarning`.

也可以只生成扁平的 `key` 列表与总权重列表, 自行取样:
```python
import bisect
from weighted_random import flatten, random_int

keys, weights = flatten(config)
# flatten 只做数学展开, 不校验唯一性: 同一个 key 出现在多个分支时会重复出现;
# 上例中 keys    = ["角色A", "角色B", "角色C", "角色D", "角色E", "角色F", "角色G"]
#       weights = [35, 35, 3, 9, 18, 450, 450], 总权重 1000;
# 注意 SR 分支被通分放大: 450/1000 = (9/10) * (1/2), 正是它真实的概率.

prefix = []
total = 0
for weight in weights:
	total += weight
	prefix.append(total)

r = random_int(total)
result = keys[bisect.bisect_right(prefix, r)]
```

配置项同样接受 `dict` 形式: `{"key": "SSR", "weight": 1, "children": [...]}`. 

> **注意**: 嵌套权重**不能**把各层权重直接相乘. 不同分支的本层总权重不同, 
> 分母并不统一, 必须逐层通分. 本库内部使用整数通分, 与"逐层多次取样"完全等价.
