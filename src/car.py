# coding:utf-8

from enum import Enum, unique
from dijsktra import dijsktra, Graph
from copy import deepcopy


@unique
class CarStatus(Enum):
    WAITING_HOME = 0  # 在家准备出发
    ON_ROAD_STATE_END = 1  # 在路上，调度完毕
    ON_ROAD_STATE_WAITING = 2  # 等待调度
    ON_ROAD_STATE_WAITING_OUT = 3  # 出路口等待调度
    ON_ROAD_STATE_WAITING_INSIDE = 4  # 不出路口等待调度
    SUCCEED = 5  # 成功抵达终点


class Car:
    """
    class 车辆：定义车辆状态
    """

    def __init__(self, car_id, origin, destination, speed, plan_time, topology):
        self.carID = car_id
        self.carFrom = origin
        self.carTo = destination
        self.carSpeed = speed
        self.carPlanTime = plan_time
        self.carStatus = CarStatus.WAITING_HOME  # 初始化为在家状态
        self.startTime = None
        self.map = topology
        self.carGPS = {'road_id': None, 'channel': None, 'pos': None, 'road_begin': None, 'road_end': None}
        # 规划路径, 动态更改
        self.strategy = None
        # 记录路过的路段，该结果为最终结果
        self.passed_by = []

    def is_ended(self):
        """
        判断是否结束
        :return:
        """
        if self.carStatus is CarStatus.SUCCEED:
            return True
        else:
            return False

    def mark_new_pos(self, road_id, channel, pos, this_cross, next_cross):
        """
        更新车辆的GPS记录
        :param road_id:
        :param channel:
        :param pos:
        :param this_cross:
        :param next_cross:
        :return:
        """
        # 标记新位置
        self.carGPS['road_id'] = road_id
        self.carGPS['channel'] = channel
        self.carGPS['pos'] = pos
        self.carGPS['road_begin'] = this_cross
        self.carGPS['road_end'] = next_cross

        # 标记状态为调度结束
        self.change2end()

        # 记录经过路段
        # 重点注意：可能会重复出现路线，因此应当与最后一个路进行比较即可
        if (len(self.passed_by) == 0) or (len(self.passed_by) > 0 and road_id != self.passed_by[-1]):
            self.passed_by.append(road_id)

    def try_start(self, graph, time):
        """
        尝试启动，找最佳路径并返回下一路段名称
        :param graph:
        :param time:
        :return:
        """
        # 对象类型断言检测
        assert isinstance(graph, Graph)

        # 如果已经上路就不需要启动了
        if self.carStatus != CarStatus.WAITING_HOME:
            return None

        # 如果未到时间就不要启动了
        if time < self.carPlanTime:
            return None

        # 1. 起点，终点 和 路径
        start = self.carFrom
        end = self.carTo
        self.strategy = dijsktra(graph, start, end)
        now_cross = self.strategy[0]
        next_cross = self.strategy[1]

        # 2. 下段路名称
        name = str(now_cross) + "_" + str(next_cross)

        # 3. 记录时间
        self.startTime = time

        return name

    def change2waiting(self):
        """
        更改为等待状态
        :return:
        """
        self.carStatus = CarStatus.ON_ROAD_STATE_WAITING

    def change2end(self):
        """
        更改调度结束状态
        :return:
        """
        self.carStatus = CarStatus.ON_ROAD_STATE_END

    def change2success(self):
        """
        更改为到家状态
        :return:
        """
        self.carStatus = CarStatus.SUCCEED

    def change2waiting_out(self):
        """
        更改为出路口等待调度状态
        :return:
        """
        self.carStatus = CarStatus.ON_ROAD_STATE_WAITING_OUT

    def change2waiting_inside(self):
        """
        更改为不出路口等待调度状态
        :return:
        """
        self.carStatus = CarStatus.ON_ROAD_STATE_WAITING_INSIDE

    def is_car_on_road(self):
        """
        判断是否在路上
        :return:
        """
        return self.is_car_waiting() or (self.carStatus is CarStatus.ON_ROAD_STATE_END)

    def is_car_waiting(self):
        """
        判断是否在路上等待调度
        :return:
        """
        return (self.carStatus is CarStatus.ON_ROAD_STATE_WAITING) or \
               (self.carStatus is CarStatus.ON_ROAD_STATE_WAITING_OUT) or \
               (self.carStatus is CarStatus.ON_ROAD_STATE_WAITING_INSIDE)

    def is_car_waiting_out(self):
        """
        判断车辆是否等待调度出路口
        :return:
        """
        return self.carStatus is CarStatus.ON_ROAD_STATE_WAITING_OUT

    def is_car_waiting_home(self):
        """
        判断车辆是否等待在家
        :return:
        """
        return self.carStatus is CarStatus.WAITING_HOME

    def is_car_way_home(self):
        """
        判断车辆是否处在连接终点的道路上
        :return:
        """
        road_id = self.carGPS['road_id']

        last = self.strategy[-2]
        end = self.strategy[-1]
        for item in self.map[last]:
            if item['end'] == end:
                if item['road_id'] == road_id:
                    return True

        return False

    def next_road_name(self, cross_id):
        """
        判断下一条路的名称
        :param cross_id:
        :return:
        """
        # 如果到终点则返回None
        if cross_id is self.carTo:
            return None

        index = self.strategy.index(cross_id)
        next_cross = self.strategy[index + 1]

        road_name = str(cross_id) + "_" + str(next_cross)
        return road_name

    def update_new_strategy(self, graph):
        """
        更新策略的时候一定要注意不走回头路。
        :param graph:
        :return:
        """
        if self.is_car_way_home():  # 回家路上无需更新
            return

        this_cross = self.carGPS['road_begin']
        next_cross = self.carGPS['road_end']

        self.strategy = dijsktra(graph, next_cross, self.carTo)  # 下一路口到终点的路

        # 如果新策略走回头路，需要制止
        if this_cross == self.strategy[1]:
            # 深拷贝，避免影响原有拓扑
            new_graph = deepcopy(graph)
            new_graph.weights[(next_cross, this_cross)] = 1000              # 加大权重
            self.strategy = dijsktra(new_graph, next_cross, self.carTo)     # 下一路口到家的路
            # 节省内存
            del new_graph
