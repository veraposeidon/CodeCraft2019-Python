# coding:utf-8

from dijsktra import Graph, dijsktra, create_topology, create_graph
import random
random.seed(42)

# 超参数
# 定义特别大的值则不考虑场上车辆
CARS_ON_ROAD = 1200

# 一次上路车辆 基数     动态上路
CAR_GET_START_BASE = 50

# 路口全部调度多少次重新更新车辆路线
LOOPS_TO_UPDATE = 3

# 路口调度多少次直接判为死锁
LOOPS_TO_DEAD_CLOCK = 100

# 路口占比权重
ROAD_WEIGHTS_CALC = 3

class trafficManager:
    def __init__(self, topologyDict, crossDict, carDict, roadDict):
        self.topology = topologyDict  # 拓扑信息
        self.crossDict = crossDict  # 路口对象
        self.carDict = carDict  # 车辆对象
        self.roadDict = roadDict  # 道路对象
        self.graph = None  # 图模型

        # 时间片和步进时间
        self.TIME = -1  # 系统时间
        self.TIME_STEP = 1  # 系统步进时间

        self.result = dict()  # 调度结果

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


    # 核心：演算
    def inference(self):
        self.TIME = 0  # 系统时间
        graph = self.getcurrentGraph(self.roadDict)
        carAtHomeList, carOnRoadList, _ = self.updateCars()
        # 判断是否所有车辆运行结束
        while not self.isTaskCompleted():

            # 1. 更新时间片
            self.TIME += self.TIME_STEP
            print(self.TIME)

            # 2. 更新所有车道（调度一轮即可）。
            # 2.1 获取道路ID列表 调度顺序：随机
            roadList = self.roadDict.keys()
            # 2.2 更新所有车道
            for roadName in roadList:
                road = self.roadDict[roadName]
                road.update_road(self.carDict)  # 车辆对象集送入

            # 3. 更新所有路口（需要调度多轮确保所有车辆完成终止态）
            # 3.1 对路口进行排序
            crossList = sorted(self.crossDict.keys())
            cross_loop_alert = 0

            # 3.2 这个While 是刚需，必须要完成道路所有车辆的调度才能进行下一个时间片
            while self.anyCar_waiting():
                # 调度一轮所有路口
                for crossID in crossList:
                    cross = self.crossDict[crossID]
                    cross.update_cross(self.roadDict, self.carDict)  # 道路和车辆对象送入

                cross_loop_alert += 1
                if cross_loop_alert >= self.LOOPS_TO_UPDATE:
                    # TODO: 动态更改拓扑图的权重
                    graph = self.getcurrentGraph(self.roadDict)
                    # 更新在路上的车的路线。
                    for carID in carOnRoadList:
                        self.carDict[carID].updateNewStratogy(graph)

                if cross_loop_alert > self.LOOPS_TO_DEAD_CLOCK:
                    print("路口循环调度次数太多进行警告")
                    import time
                    print(time.clock)
                    assert False
            print("LOOPs " + str(cross_loop_alert))

            # 4. 处理准备上路的车辆
            # 4.2 获取车辆列表
            carAtHomeList, carOnRoadList, succed = self.updateCars()
            lenOnRoad = len(carOnRoadList)

            # self.CARS_ON_ROAD = CARS_ON_ROAD / (cross_loop_alert+0.1)

            if lenOnRoad < self.CARS_ON_ROAD:       # TODO: 动态更改地图车辆容量
                # TODO: 动态上路数目
                # if len(carAtHomeList) < self.CARS_ON_ROAD:
                #     how_many = len(carAtHomeList)
                # else:
                #     how_many = self.CARS_ON_ROAD - lenOnRoad
                how_many = self.CARS_ON_ROAD - lenOnRoad
                # how_many = int(self.CAR_GET_START_BASE / (cross_loop_alert + 1.0))

                for id in carAtHomeList[:how_many]:
                    carObj = self.carDict[id]
                    road_name = carObj.try_start(graph, self.TIME)
                    if road_name is not None:
                        self.roadDict[road_name].try_on_road(carObj)

                print(len(carAtHomeList),self.CARS_ON_ROAD, lenOnRoad, succed)

        print("Tasks Completed! and Time cost: " + str(self.TIME))

    # 得到结果并返回
    def getResult(self):
        for key in self.carDict.keys():
            self.result[self.carDict[key].carID] = {'startTime': self.carDict[key].startTime,
                                                    'roads': self.carDict[key].passby}
        return self.result

    def getcurrentGraph(self, road_dict):
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

    # Update Car status
    def isTaskCompleted(self):
        for carid in self.carDict.keys():
            car = self.carDict[carid]
            if not car.isEnded():
                return False
        return True

    # 更新任务车辆列表
    # 遍历完成任务的车辆，保留记录信
    # 返回在路上的车辆和在家的车辆
    def updateCars(self):
        # 获取列表
        carAtHomeList = []
        carOnRoadList = []
        carSucceed = 0
        for carid in self.carDict.keys():
            car = self.carDict[carid]
            if car.iscarWaiting_home():
                carAtHomeList.append(car.carID)
            elif car.iscarOnRoad():
                carOnRoadList.append(car.carID)
            elif car.isEnded():
                carSucceed += 1

        # carAtHomeList.sort(reverse=False)
        # carOnRoadList.sort(reverse=False)
        # random.shuffle(carAtHomeList)

        return carAtHomeList, carOnRoadList, carSucceed


    def anyCar_waiting(self):
        """
        判断道路上是否有车等待调度
        :return:
        """
        for key in self.carDict.keys():
            if self.carDict[key].iscarWaiting():
                return True
        return False