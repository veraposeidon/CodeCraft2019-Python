# coding:utf-8

from enum import Enum, unique
from dijsktra import dijsktra, Graph
from copy import copy, deepcopy

@unique
class car_status(Enum):
    WAITING_HOME = 0  # 在家准备出发
    ON_RAOD_STATE_END = 1  # 在路上，调度完毕
    ON_RAOD_STATE_WAITING = 2  # 等待调度
    ON_RAOD_STATE_WAITING_OUTCROSS = 3  # 出路口等待调度
    ON_RAOD_STATE_WAITING_INCROSS = 4  # 不出路口等待调度
    SUCCEED = 5  # 成功抵达终点


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
        self.carLocation = {'roadID': None, 'channel': None, 'pos': None, 'now': None ,'next': None}

        # 规划路径
        self.strategy = None

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

    # 标记新位置
    def mark_new_pos(self, roadID, channel, pos,this_cross, next_cross):
        # 标记位置
        self.carLocation['roadID'] = roadID
        self.carLocation['channel'] = channel
        self.carLocation['pos'] = pos
        self.carLocation['next'] = next_cross
        self.carLocation['now'] = this_cross

        # 标记状态,车辆调度结束
        self.carStatus = car_status.ON_RAOD_STATE_END

        # 记录经过路段
        # 重点注意：可能会重复出现路线，因此应当与最后一个路进行比较即可
        if (len(self.passby) == 0) or (len(self.passby) > 0 and roadID != self.passby[-1]):
            self.passby.append(roadID)
            # print(str(self.carID) + "经过： " + str(roadID))


    # 尝试找车辆路径，和下一路段名称
    def try_start(self, graph, TIME):
        # 对象类型断言检测
        assert isinstance(graph, Graph)

        # 如果已经在路上就不需要再启动了
        if self.carStatus != car_status.WAITING_HOME:
            return None
        # 如果时间未到那就不要启动了
        if TIME < self.carPlanStartTime:
            return None

        # 1. 起点，终点 和 路径
        start = self.carFrom
        end = self.carTo
        self.strategy = dijsktra(graph, start, end)

        now = self.strategy[0]
        next = self.strategy[1]

        # 2. 下段路名称
        name = str(now) + "_" + str(next)

        # 3. 时间
        self.startTime = TIME

        return name

    # 更改状态为等待处理
    def change2waiting(self):
        self.carStatus = car_status.ON_RAOD_STATE_WAITING

    # 更改状态为处理完成
    def change2end(self):
        self.carStatus = car_status.ON_RAOD_STATE_END

    # 更改状态为到达终点
    def change2success(self):
        self.carStatus = car_status.SUCCEED
        # print(str(self.carID) + " 到家了")

    # 更改状态为出路口等待调度
    def change2waiting_out(self):
        self.carStatus = car_status.ON_RAOD_STATE_WAITING_OUTCROSS

    # 更改状态为不出路口等待调度
    def change2waiting_inside(self):
        self.carStatus = car_status.ON_RAOD_STATE_WAITING_INCROSS

    # 更改状态为不出路口等待调度
    def iscarOnRoad(self):
        return self.iscarWaiting() or (self.carStatus is car_status.ON_RAOD_STATE_END)

    # 判断车辆是否为等待处理
    def iscarWaiting(self):
        return (self.carStatus is car_status.ON_RAOD_STATE_WAITING) or \
               (self.carStatus is car_status.ON_RAOD_STATE_WAITING_OUTCROSS) or \
               (self.carStatus is car_status.ON_RAOD_STATE_WAITING_INCROSS)

    # 判断车辆是否等待出路口
    def iscarWaiting_out(self):
        return self.carStatus is car_status.ON_RAOD_STATE_WAITING_OUTCROSS

    def iscarWaiting_home(self):
        return self.carStatus is car_status.WAITING_HOME

    # 判断车辆是否在回家的路上
    def iscar_wayhome(self):
        roadID = self.carLocation['roadID']

        last = self.strategy[-2]
        end = self.strategy[-1]
        for item in self.map[last]:
            if item['end'] == end:
                if item['roadid'] == roadID:
                    return True

        return False

    def next_road_name(self, crossID):
        """
        判断下一条路,需要判断是否到终点
        :param crossID:
        :return:
        """
        if crossID is self.carTo:   # 到终点
            return None

        index = self.strategy.index(crossID)    # 下一个路口
        next_cross = self.strategy[index+1]

        road_name = str(crossID) + "_" + str(next_cross)
        return road_name

    def updateNewStratogy(self, graph):
        """
        更新策略的时候一定要注意不走回头路。
        :param graph:
        :return:
        """
        if self.iscar_wayhome():     # 回家路上没有用
            return

        nextcross = self.carLocation['next']
        thiscross = self.carLocation['now']

        self.strategy = dijsktra(graph, nextcross, self.carTo)  # 下一路口到家的路
        # 判断走没有所在的路，要是有，就重新更新下Graph,重新找最优路径
        if thiscross == self.strategy[1]:
            # 深拷贝，避免影响原有拓扑
            new_graph = deepcopy(graph)
            new_graph.weights[(nextcross,thiscross)] = 1000     # 加大权重
            self.strategy = dijsktra(new_graph, nextcross, self.carTo)  # 下一路口到家的路
            del new_graph   # 节省内存
