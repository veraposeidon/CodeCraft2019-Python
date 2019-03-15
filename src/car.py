# coding:utf-8

from enum import Enum, unique
from dijsktra import dijsktra

@unique
class car_status(Enum):
    WAITING_HOME = 0    # 在家准备出发
    ON_RAOD = 1         # 上路，在路上
    STUCK = 2           # 堵住
    WAITING_CROSS = 3   # 等待路口调度
    SUCCEED = 4         # 成功抵达终点


# 定义车辆状态的对象
# 车辆的等待、运行、终止、结束等状态很重要
class car:
    def __init__(self, id, origin, destination, speed, plantime, topology):
        self.carID = id
        self.carFrom = origin
        self.carTo = destination
        self.carSpeed = speed
        self.carPlanStartTime = plantime
        self.carStatus = car_status.WAITING_HOME
        self.startTime = None
        self.map = topology
        # 定位用道路，channel，长度表示
        self.location = dict()

        # 规划路径
        self.strategy = None

        # 当前道路
        self.nowRoad = None

        # 经过道路
        self.passby = []

    # 最短路径
    def findShortestPath(self, graph):
        path = dijsktra(graph, self.carFrom, self.carTo)
        return path

    # 是否运行结束
    def isEnded(self):
        if self.carStatus is car_status.SUCCEED:
            return True
        else:
            return False

    # 是否在路上
    def isOnRoad(self):
        if self.carStatus != car_status.WAITING_HOME:
            return True
        else:
            return False

    # 单步运行
    def updateOneStep(self, time, roads, graph):
        # 如果还没有开始运行，则启动
        if self.carStatus is car_status.WAITING_HOME:
            # 当时间到了则开始运行
            if time >= self.carPlanStartTime:
                # 更新状态
                self.carStatus = car_status.ON_RAOD

                # 设定起始时间
                self.startTime = time

                # 打印信息
                # print("car: " + str(self.carID) + " 启动了。")

                # 查找最优路径
                self.strategy = self.findShortestPath(graph=graph)

                # 放置在第一条路的起点
                start = self.strategy[0]
                to = self.strategy[1]
                roadid = self.find_road(start, to)
                # 轨迹上增添第一条道路
                self.passby.append(roadid)

                # 一辆车一辆车跑的时候默认都在1车道跑
                self.location = {'pos': 0, 'begin': start, 'end': to}

                # TODO 开始上路 处理路上情况
                self.step(roads)
        else:
            # TODO 处理路上情况
            # print("car: " + str(self.carID) + " 正在路上")
            self.step(roads)

    def step(self, roads):
        # 当前位置
        pos = self.location['pos']
        road_name = str(self.location['begin']) + "_" + str(self.location['end'])
        road = roads[road_name]
        # channel = self.location['channel'] # 暂时用不到

        # 获取道路限速，长度
        length = road.roadLength
        spedLimit = road.roadSpeedLimit
        remainLen = length - pos
        # 限速
        speed = min(self.carSpeed, spedLimit)

        # 分情况进行讨论
        if remainLen >= speed:
            # 直接前行状态
            newPos = pos + speed
            self.location['pos'] = newPos
        else:
            # pass
            # 通过路口
            # 1. 先找到下一条路（需要判断是否到了终点）
            newbegin = self.location['end']

            # TODO 判断终点
            if newbegin == self.carTo:
                self.carStatus = car_status.SUCCEED
                # print("car: " + str(self.carID) + " 到终点了")
            else:
                index = self.strategy.index(newbegin)
                newend = self.strategy[index+1]

                roadid = self.find_road(newbegin, newend)

                # 轨迹上增添第一条道路
                self.passby.append(roadid)

                road_name = str(newbegin) + "_" + str(newend)
                road = roads[road_name]
                # channel = self.location['channel'] # 暂时用不到

                # 获取道路限速，长度
                length = road.roadLength
                spedLimit = road.roadSpeedLimit

                # 限速
                speed = min(self.carSpeed, spedLimit)

                newpos = speed - remainLen
                self.location = {'pos': newpos, 'begin': newbegin, 'end': newend}

            # 2. 确定新路的起始位置


    # 查地图，找道路
    def find_road(self,start, to):
        item = self.map[start]
        for path in item:
            if path['end'] is to:
                return path['roadid']
