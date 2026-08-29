# WeightedRandom · 带权重的随机数生成工具

一个简易的 Python 随机数生成库, 用于根据指定非负整数权重, 选择对应位置的元素. 

内部使用整数实现, 避免浮点数误差. 

目前支持: 
- 单次带权取样. 
- 无重复多次带权取样.

## 时空复杂度

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

## 许可证
本项目基于 [MIT](LICENSE) 许可证发布. 
