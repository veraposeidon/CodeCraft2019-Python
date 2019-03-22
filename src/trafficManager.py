# coding:utf-8

from dijsktra import create_graph
import random

random.seed(42)

# 超参数
# 定义特别大的值则不考虑场上车辆
# CARS_ON_ROAD = 2500   # 大地图2500辆
CARS_ON_ROAD = 1700

# 一次上路车辆 基数     动态上路
CAR_GET_START_BASE = 200

# 路口全部调度多少次重新更新车辆路线
LOOPS_TO_UPDATE = 4

# 路口调度多少次直接判为死锁
LOOPS_TO_DEAD_CLOCK = 100

# 路口占比权重
ROAD_WEIGHTS_CALC = 3


class TrafficManager:
    """
    调度中心
    """

    def __init__(self, topology_dict, cross_dict, car_dict, road_dict):
        self.topology = topology_dict  # 拓扑信息
        self.crossDict = cross_dict  # 路口对象
        self.carDict = car_dict  # 车辆对象
        self.roadDict = road_dict  # 道路对象
        self.graph = None  # 图模型

        # 时间系统
        self.TIME = -1  # 系统时间
        self.TIME_STEP = 1  # 系统步进时间
        # 调度结果
        self.result = dict()

        # 超参数
        # 定义特别大的值则不考虑场上车辆
        self.CARS_ON_ROAD = CARS_ON_ROAD

        # 一次上路车辆 基数     动态上路
        self.CAR_GET_START_BASE = CAR_GET_START_BASE

        # 路口全部调度多少次重新更新车辆路线
        self.LOOPS_TO_UPDATE = LOOPS_TO_UPDATE

        # 路口调度多少次直接判为死锁
        self.LOOPS_TO_DEAD_CLOCK = LOOPS_TO_DEAD_CLOCK

        # 路口占比权重
        self.ROAD_WEIGHTS_CALC = ROAD_WEIGHTS_CALC

    def inference(self):
        """
        推演
        :return:
        """
        # 初始化时间
        self.TIME = 0
        # 初始化有向图
        graph = self.get_new_map(self.roadDict)
        # 初始化列表
        carAtHomeList, carOnRoadList, _ = self.update_cars()

        # 进入调度任务，直至完成
        while not self.is_task_completed():

            # 1. 更新时间片
            self.TIME += self.TIME_STEP

            # 2. 更新所有车道（调度一轮即可）。
            # 2.1 获取道路ID列表 调度顺序无关
            roadList = self.roadDict.keys()
            # 2.2 更新所有车道
            for roadName in roadList:
                road = self.roadDict[roadName]
                road.update_road(self.carDict)

            # 3. 更新所有路口（需要调度多轮确保所有车辆完成终止态）
            # 3.1 对路口进行排序，升序调度路口
            crossList = sorted(self.crossDict.keys())

            # 重置路口的完成标记
            for crossID in crossList:
                cross = self.crossDict[crossID]
                cross.reset_end_flag()

            # 3.2 这个While 是刚需，必须要完成道路所有车辆的调度才能进行下一个时间片
            cross_loop_alert = 0
            while self.any_car_waiting():
                # 调度一轮所有路口
                # TODO: 在此处检查哪些路口调度次数过多。后面更新权重时将加大这些区域的权重
                for crossID in crossList:
                    cross = self.crossDict[crossID]
                    if not cross.if_cross_ended():
                        cross.update_cross(self.roadDict, self.carDict)  # 道路和车辆对象送入

                cross_loop_alert += 1

                if cross_loop_alert > self.LOOPS_TO_DEAD_CLOCK:
                    print("路口循环调度次数太多进行警告")
                    assert False

                if cross_loop_alert >= self.LOOPS_TO_UPDATE:
                    # TODO: 怂恿堵着的车辆换路线
                    # TODO: 高速路开高速车
                    # TODO: 定时更新策略
                    # 更新 有向图 权重
                    graph = self.get_new_map(self.roadDict)
                    # 更新 路上车辆 路线。
                    for carID in carOnRoadList[:int(lenOnRoad / 2)]:  # 大地图用
                    # for carID in carOnRoadList[:int(lenOnRoad)]:
                        self.carDict[carID].update_new_strategy(graph)

            print("TIME: " + str(self.TIME) + ", LOOPs " + str(cross_loop_alert))

            # 4. 处理准备上路的车辆
            # 4.2 获取车辆列表
            carAtHomeList, carOnRoadList, succeed = self.update_cars()
            lenOnRoad = len(carOnRoadList)
            lenAtHome = len(carAtHomeList)

            # TODO: 动态更改地图车辆容量
            # TODO: 动态上路数目
            if lenOnRoad < self.CARS_ON_ROAD:
                # if len(carAtHomeList) < self.CARS_ON_ROAD:
                #     how_many = len(carAtHomeList)
                # else:
                #     how_many = self.CARS_ON_ROAD - lenOnRoad
                how_many = self.CARS_ON_ROAD - lenOnRoad

                # how_many = int(self.CAR_GET_START_BASE / (cross_loop_alert + 1.0))

                count_start = 0
                for car_id in carAtHomeList[:how_many]:
                    carObj = self.carDict[car_id]
                    road_name = carObj.try_start(graph, self.TIME)
                    if road_name is not None:
                        if self.roadDict[road_name].try_on_road(carObj):
                            count_start += 1

                print(count_start, lenAtHome, lenOnRoad, succeed)

        print("Tasks Completed! and Schedule Time is: " + str(self.TIME))

    def get_result(self):
        """
        处理结果
        :return:
        """
        for key in self.carDict.keys():
            self.result[self.carDict[key].carID] = {'startTime': self.carDict[key].startTime,
                                                    'roads': self.carDict[key].passed_by}
        return self.result

    def get_new_map(self, road_dict):
        """
        TODO : 重点，更新整个地图的权重，可以融合诸多规则。
        :param road_dict:
        :return:
        """
        for start in self.topology.keys():
            for item in self.topology[start]:
                road_name = str(start) + "_" + str(item['end'])
                road_weight = road_dict[road_name].get_road_weight()
                item['weight'] = item['length'] * (1 + road_weight * self.ROAD_WEIGHTS_CALC)

        graph = create_graph(self.topology)

        return graph

    def is_task_completed(self):
        """
        是否所有车辆演算结束
        :return:
        """
        for carid in self.carDict.keys():
            car = self.carDict[carid]
            if not car.is_ended():
                return False
        return True

    def update_cars(self):
        """
        遍历车辆，获取状态
        :return:
        """
        carAtHomeList = []
        carOnRoadList = []
        carSucceed = 0
        for carid in self.carDict.keys():
            car = self.carDict[carid]
            if car.is_car_waiting_home():
                carAtHomeList.append(car.carID)
            elif car.is_car_on_road():
                carOnRoadList.append(car.carID)
            elif car.is_ended():
                carSucceed += 1

        # carAtHomeList.sort(reverse=False)
        # carOnRoadList.sort(reverse=False)
        # random.shuffle(carAtHomeList)

        return carAtHomeList, carOnRoadList, carSucceed

    def any_car_waiting(self):
        """
        判断道路上是否有车等待调度
        :return:
        """
        for key in self.carDict.keys():
            if self.carDict[key].is_car_waiting():
                return True
        return False
