#coding:utf-8

# 交叉路口对象
# 还可以在此处安排优先级
# 相当于交叉路口安排一个调度员
# 对于一条道路，有多少车要准备出去，有多少车要准备近来。出去多少长度，近来多少长度
# 也就是说，我认为，调度的顺序应该是计算预测下一步的操作，进行判断，遍历完之后，再统一更新状态。
class cross(object):
    def __init__(self, id, road1, road2, road3, road4):
        self.crossID = id
        self.road_0clock = road1
        self.road_3clock = road2
        self.road_6clock = road3
        self.road_9clock = road4
        self.roads = [road1, road2, road3, road4]



