# coding:utf-8

from dijsktra import Graph, dijsktra, createTopology, createGraph


class trafficManager:
    def __init__(self, topologyDict, crossDict, carDict, roadDict):
        self.topology = topologyDict
        self.crossDict = crossDict
        self.carDict = carDict
        self.roadDict = roadDict
        self.graph = None
        self.jobisDone = False
        self.TIME = 0
        self.TIME_STEP = 1
        self.result = dict()

    # 核心：演算
    def inference(self):
        self.TIME = 0   # 系统时间
        graph = self.getcurrentGraph()
        # 判断是否所有车辆运行结束
        while not self.isTaskCompleted():
            # TODO: Update Graph
            # update 太慢
            # graph = self.getcurrentGraph()

            # TODO: Update Car
            # 获取车辆列表
            carOnRoadList, carAtHomeList = self.updateCars()

            # 在此处需要添加派出多少辆车
            # 目前只处理第一辆车

            for id in carOnRoadList[:30]:
                onecarID = id
                onecar =self.carDict[onecarID]
                onecar.updateOneStep(self.TIME, self.roadDict, graph)

            for id in carAtHomeList[:10]:
                onecarID = id
                onecar =self.carDict[onecarID]
                onecar.updateOneStep(self.TIME, self.roadDict, graph)

            # onecarID = carlist[0]
            # onecar =self.carDict[onecarID]
            # onecar.updateOneStep(self.TIME, self.roadDict, graph)

            # TODO: Update Cross
            # 暂时不用

            # 更新时间
            self.TIME += self.TIME_STEP
            # print(self.TIME)

        # 所有车辆都运行完之后，还需要check一遍车辆，把最后一轮完成的更新一下
        _,_ = self.updateCars()
        print("Tasks Completed!")


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






