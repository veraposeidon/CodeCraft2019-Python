# coding:utf-8

from dijsktra import Graph, dijsktra, createTopology, createGraph


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

    # 核心：演算
    def inference(self):
        self.TIME = 0  # 系统时间
        graph = self.getcurrentGraph()
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
                if cross_loop_alert > 5:
                    print("路口循环调度次数太多进行警告")

            # 4. 处理准备上路的车辆 暂时举例
            carObj = self.carDict[10005]
            road_name = carObj.try_start(graph, self.TIME)
            if road_name is not None:
                self.roadDict[road_name].try_on_road(carObj)

            # 还要更新一边车辆，把跑完的车的结果记录一下

        print("Tasks Completed! and Time cost: " + str(self.TIME))

    # 得到结果并返回
    def getResult(self):
        return self.result

    # 计算当前Graph
    def getcurrentGraph(self):
        pass
        # TODO 获取每条路况信息

        # TODO 更改每条路况权重

        # TODO 更新拓扑信息

        # TODO 生成简要Graph信息
        graph = createGraph(self.topology)

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
        carOnRoadList = []
        carAtHomeList = []
        for carid in self.carDict.keys():
            car = self.carDict[carid]
            if car.isEnded():
                # 先将任务列表中已经结束的车辆剔除掉
                # 注意剔除时要先保存一下行驶记录。
                self.result[car.carID] = {'startTime': car.startTime,
                                          'roads': car.passby}
                # 那就不删除了， 结束车辆
                # del self.carDict[carid]
            else:
                if car.isOnRoad():
                    carOnRoadList.append(car.carID)
                else:
                    carAtHomeList.append(car.carID)

        # # 排序
        # # 如果按顺序更新的，我认为车要更新两遍，因为第一遍可能被前面车给挡住了
        carOnRoadList.sort(reverse=False)
        carAtHomeList.sort(reverse=False)

        return carOnRoadList, carAtHomeList

    def anyCar_waiting(self):
        """
        判断道路上是否有车等待调度
        :return:
        """
        for key in self.carDict.keys():
            if self.carDict[key].iscarWaiting():
                return True
        return False