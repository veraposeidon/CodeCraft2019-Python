# coding:utf-8

from dijsktra import create_graph
import random
from collections import defaultdict

random.seed(1118)

# 场上车辆数目
# CARS_ON_ROAD = 1000  # 大地图2500辆
CARS_ON_ROAD = 1800
# 一次上路车辆 基数     动态上路
CAR_GET_START_BASE = 250
# 路口全部调度多少次重新更新车辆路线
LOOPS_TO_UPDATE = 3
# 路口调度多少次直接判为死锁
LOOPS_TO_DEAD_CLOCK = 50
# 路口占比权重
ROAD_WEIGHTS_CALC = 3
# 一个路口连续循环几次才转下个路口调度
CROSS_LOOP_TIMES = 1


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
        self.TIME = -1  # 调度系统时间
        self.TIME_STEP = 1  # 调度系统时间单位

        self.CARS_ON_ROAD = CARS_ON_ROAD  # 超参数 场上控制车数
        self.CAR_GET_START_BASE = CAR_GET_START_BASE  # 超参数 上路车辆基数
        self.LOOPS_TO_UPDATE = LOOPS_TO_UPDATE  # 超参数 更新策略阈值
        self.LOOPS_TO_DEAD_CLOCK = LOOPS_TO_DEAD_CLOCK  # 超参数 死锁判定阈值
        self.ROAD_WEIGHTS_CALC = ROAD_WEIGHTS_CALC  # 超参数 道路权重参数
        self.CROSS_LOOP_TIMES = CROSS_LOOP_TIMES  # 超参数 路口遍历次数

        self.result = dict()  # 调度结果

        self.launch_order = self.get_start_list()

    def get_start_list(self):
        """
        初始化上路顺序
        :return:
        """

        # 系统给的顺序
        # random_order = [obj.carID for obj in self.carDict.values()]
        # return random_order

        # # 随机顺序
        # import random
        # shuffle_order = random_order
        # random.shuffle(shuffle_order)
        # return shuffle_order

        # # # 上路时间排序
        # timer_order = sorted(self.carDict, key=lambda k: self.carDict[k].carPlanTime)
        # return timer_order

        # 1. 先获取发车地点分布(crossID : list(carID))
        area_dist = defaultdict(lambda: [])
        for item in self.carDict.values():
            area_dist[item.carFrom].append(item.carID)
        # 2. 每个地点的车辆按出发时间排序
        for cross in area_dist:
            area_dist[cross] = sorted(area_dist[cross], key=lambda k: self.carDict[k].carPlanTime)
        # # 3. 按每个地点的车辆的形式距离
        # for cross in area_dist:
        #     area_dist[cross] = sorted(area_dist[cross], key=lambda k: self.carDict[k].carTo - self.carDict[k].carFrom)
        #     area_dist[cross].reverse()
        # 3. 拼接在一起
        car_num = len(self.carDict)
        complexorder = []
        while len(complexorder) < car_num:
            for cross in area_dist.keys():
                if area_dist[cross]:
                    complexorder.append(area_dist[cross][0])
                    area_dist[cross].pop(0)
        assert len(complexorder) == car_num
        return complexorder

        # # 按照行驶距离来聚类
        # dis_order = sorted(self.carDict, key=lambda k: abs(self.carDict[k].carTo - self.carDict[k].carFrom))
        # dis_order.reverse()
        # return dis_order

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
            while self.any_car_waiting(carOnRoadList):
                # 调度一轮所有路口
                # TODO: 在此处检查哪些路口调度次数过多。后面更新权重时将加大这些区域的权重
                for crossID in crossList:
                    cross = self.crossDict[crossID]
                    if not cross.if_cross_ended():
                        cross.update_cross(self.roadDict, self.carDict,
                                           loops_every_cross=self.CROSS_LOOP_TIMES)  # 道路和车辆对象送入

                cross_loop_alert += 1

                if cross_loop_alert > self.LOOPS_TO_DEAD_CLOCK:
                    print("路口循环调度次数太多进行警告")
                    # TODO 取消断言，换成返回bool，重新设置参数运行
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
            carAtHomeList, carOnRoadList, carsOnEnd = self.update_cars()
            lenOnRoad = len(carOnRoadList)
            lenAtHome = len(carAtHomeList)

            # TODO: 动态更改地图车辆容量
            # TODO: 动态上路数目
            if lenOnRoad < self.CARS_ON_ROAD:
                # # 如果太堵就不发车了
                # if cross_loop_alert >= 7:
                #     continue

                # # # 这段话有奇效
                # # if cross_loop_alert == 0:
                # #     how_many = CAR_GET_START_BASE
                if len(carAtHomeList) < self.CARS_ON_ROAD / 3:
                    # self.CARS_ON_ROAD += len(carAtHomeList)
                    how_many = len(carAtHomeList)
                else:
                    how_many = self.CARS_ON_ROAD - lenOnRoad
                    # how_many = int(self.CAR_GET_START_BASE / (cross_loop_alert+0.01))
                # how_many = self.CARS_ON_ROAD - lenOnRoad
                # how_many = int(self.CAR_GET_START_BASE / (cross_loop_alert + 0.1))

                count_start = 0
                car_start_list = carAtHomeList[:how_many].copy()
                sorted(car_start_list)  # 小号优先

                # for car_id in carAtHomeList[:how_many]:
                for car_id in car_start_list:
                    carObj = self.carDict[car_id]
                    road_name = carObj.try_start(graph, self.TIME)
                    if road_name is not None:
                        if self.roadDict[road_name].try_on_road(carObj):
                            count_start += 1
                            carOnRoadList.append(carObj.carID)
                            lenOnRoad += 1
                            lenAtHome -= 1

                print(count_start, lenAtHome, lenOnRoad, carsOnEnd)

        print("Tasks Completed! and Schedule Time is: " + str(self.TIME))
        return True # 返回正确

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
        在发车列表上进行遍历
        :return:
        """
        carAtHomeList = []
        carOnRoadList = []
        carSucceedNum = 0
        for car_id in self.launch_order[:]:
            car = self.carDict[car_id]
            if car.is_car_waiting_home():
                carAtHomeList.append(car.carID)
            elif car.is_car_on_road():
                carOnRoadList.append(car.carID)
            elif car.is_ended():
                carSucceedNum += 1  # 本轮到家车辆数目
                self.launch_order.remove(car_id)    # 有remove动作，需要在遍历时加上[:]

        # carAtHomeList.sort(reverse=False)
        # carOnRoadList.sort(reverse=False)
        # random.shuffle(carAtHomeList)

        return carAtHomeList, carOnRoadList, carSucceedNum

    def any_car_waiting(self, carOnRoadList):
        """
        判断道路上是否有车等待调度
        仅判断在路上的车辆即可
        :return:
        """
        for car_id in carOnRoadList:
            if self.carDict[car_id].is_car_waiting():
                return True
        return False

