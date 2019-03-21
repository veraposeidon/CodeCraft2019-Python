# coding:utf-8
import numpy as np
from car import Car


# 定义道路信息
class Road(object):
    def __init__(self, road_id, length, speed_limit, channel, origin, dest):
        self.roadID = road_id                       # 道路ID
        self.roadLength = length                    # 道路长度
        self.roadSpeedLimit = speed_limit           # 速度限制
        self.roadChannel = channel                  # 通道数
        self.roadOrigin = origin                    # 道路起点
        self.roadDest = dest                        # 道路终点
        self.roadStatus = self.initialize_road()    # 道路详情

    def initialize_road(self):
        """
        初始化道路详情，全部置-1
        :return:
        """
        channel = self.roadChannel
        length = self.roadLength
        road_detail = np.ones((channel, length)) * -1
        return road_detail.astype(np.int16)  # 位数也很重要

    def update_road(self, car_dict):
        """
        更新道路，时间片内第一次调度
        :param car_dict:
        :return:
        """
        # 根据优先序列遍历车辆
        for grid in range(self.roadLength - 1, -1, -1):
            for channel in range(self.roadChannel):
                if self.roadStatus[channel, grid] != -1:
                    # 车辆对象
                    car = car_dict[self.roadStatus[channel, grid]]
                    # 标记所有车辆为待处理状态
                    car.change2waiting()
                    # 调度每一车辆
                    self.update_car(car, channel, grid, car_dict)

    def update_car(self, car, channel, grid, car_dict):
        """
        调度车辆。
        :param car:
        :param channel:
        :param grid:
        :param car_dict:
        :return:
        """
        # 断言检测 车辆位置
        car_channel = car.carGPS['channel']
        car_pos = car.carGPS['pos']
        assert car_channel == channel
        assert car_pos == grid

        speed = min(car.carSpeed, self.roadSpeedLimit)  # 获取车速
        len_remain = self.roadLength - (car_pos + 1)    # 道路剩余长度

        if len_remain < speed:  # 准备出路口
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos+1, self.roadLength)  # 车前方一格到道路终点有无车辆阻拦
            if has_car:  # 前方有车
                if car_dict[front_id].is_car_waiting():  # 前车正在等待
                    car.change2waiting_out()  # 标记为等待出去
                    # TODO: 此处可以重新进行路径规划，以确定下一阶段道路在哪和出路口方向
                else:
                    car.change2end()  # 标记为调度结束
            else:  # 前方无车
                # 出路口，前方无车(两种情况：到达终点和准备出路口)
                if car.is_car_way_home():  # 前方到家，更改状态，抹除该车
                    car.change2success()  # 更改车辆状态
                    self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
                else:  # 前方出路口，获取转弯方向
                    car.change2waiting_out()  # 标记为等待出去
                    # TODO: 此处可以重新进行路径规划，以确定下一阶段道路在哪和出路口方向
        else:  # 不会出路口
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos + 1, car_pos + speed + 1)
            if has_car:  # 前方有车
                if car_dict[front_id].is_car_waiting():  # 前车正在等待
                    car.change2waiting_inside()  # 标记为等待且不出路口
                else:  # 前车结束调度，需判断还能否前进
                    dis = front_pos - car_pos
                    assert dis >= 1  # 要是距离短于1就见鬼了
                    if dis == 1:
                        car.change2end()  # 本就在前车屁股，无需调度
                    else:
                        new_pos = front_pos - 1  # 还能前进一段，新位置在前车屁股
                        # 注册新位置
                        self.roadStatus[car_channel, new_pos] = car.carID
                        # 抹除旧位置
                        self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
                        # 更新到车辆信息
                        car.mark_new_pos(road_id=self.roadID, channel=car_channel, pos=new_pos,
                                         this_cross=self.roadOrigin, next_cross=self.roadDest)
                        # 标记车辆为EndState
                        car.change2end()

            else:  # 前方无车
                new_pos = car_pos + speed
                # 注册新位置
                self.roadStatus[car_channel, new_pos] = car.carID
                # 抹除旧位置
                self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                car.mark_new_pos(road_id=self.roadID, channel=car_channel, pos=new_pos, this_cross=self.roadOrigin,
                                 next_cross=self.roadDest)
                # 标记车辆为EndState
                car.change2end()

    def has_car(self, channel, start, end):
        """
        判断车道内某段区域是否有车
        :param channel:
        :param start:   车前方一格
        :param end:     道路终点
        :return:
        """
        if start == end:  # 已在道路最前端
            return False, None, None
        channeldetail = self.roadStatus[channel, :].flatten()
        for grid in range(start, end, 1):
            if channeldetail[grid] == -1:
                continue
            else:  # 有车阻挡
                return True, grid, channeldetail[grid]  # 返回bool, 位置， 车号

        # 无车阻挡
        return False, grid, None

    def try_on_road(self, carObj):
        """
        # 车辆入驻道路
        # 输入：car对象
        # 输出：True,成功； False,失败
        :param carObj:
        :return:
        """
        # 对象断言检测
        assert isinstance(carObj, Car)

        # 1. 找车位, 需要判空
        channel, pos = self.getcheckInPlace()
        if channel is None:
            return False

        # 2. 根据车速判断位置
        speed = min(carObj.carSpeed, self.roadSpeedLimit)
        speed_pos = speed - 1

        # 速度低于空位置，则前进最大速度
        # 否则置于pos处
        if speed_pos <= pos:
            pos = speed_pos

        # 注册新位置
        self.roadStatus[channel, pos] = carObj.carID

        # 更新到车辆信息
        carObj.mark_new_pos(road_id=self.roadID, channel=channel, pos=pos, this_cross=self.roadOrigin,
                            next_cross=self.roadDest)

        # 打印一下信息
        # print(str(carObj.carID) + "出发了")

    def getcheckInPlace(self):
        """
        # 获取进入道路时的空位置
        # 要是没有返回None
        # 必须要找小编号车道优先原则
        :return:
        """
        # 道路为空
        if np.all(self.roadStatus == -1):
            return 0, self.roadLength - 1  # 注意下标

        # 道路不为空
        for channel in range(self.roadChannel):
            # channel 满(判断最后一辆车就好)
            if self.roadStatus[channel, 0] != -1:
                continue
            # channel 不满
            for pos in range(self.roadLength):
                if self.roadStatus[channel, pos] == -1:
                    if pos == self.roadLength - 1:  # 到头，那就是最大长度
                        return channel, pos
                    continue
                else:
                    return channel, pos - 1  # 返回空位置，而不是有阻挡的位置
        # 全满
        return None, None

    def get_first_order_car(self, carDict):
        """
        获取本条道路的第一优先级车辆（只考虑出路口哦）
        TODO 其实最优路径的更新也可以放在此处
        此处效率要优化
        :return:
        """
        # 根据优先序列遍历车辆
        for grid in range(self.roadLength - 1, -1, -1):
            for channel in range(self.roadChannel):
                if self.roadStatus[channel, grid] != -1:
                    # 获取车对象
                    car = carDict[self.roadStatus[channel, grid]]
                    if car.is_car_waiting_out():
                        return car

        # 如果没有则返回NONE
        return None

    def move_car_home(self, carO):
        """
        移动车辆回家
        :param carO:
        :return:
        """
        assert carO.is_car_way_home(self.roadID)  # 直接断言 道路正确
        car_id = carO.carID
        car_channel = carO.carGPS['channel']
        car_pos = carO.carGPS['pos']
        assert self.roadStatus[car_channel, car_pos] is car_id  # 直接断言 车辆所处位置正确

        Car.change2success()  # 更改车辆状态
        self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
        # print(str(carO.carID) + " 到家")

    def update_channel(self, channel_id, car_dict):
        """
        当有车更新到终止态之后，要更新一次当前车道的车辆
        :param channel_id:
        :return:
        """
        for grid in range(self.roadLength - 1, -1, -1):
            if self.roadStatus[channel_id, grid] != -1:
                # 获取车对象
                car = car_dict[self.roadStatus[channel_id, grid]]
                # 判断车辆状态，END跳过
                if car.is_car_waiting():
                    # 调度车辆
                    self.update_car(car, channel_id, grid, car_dict)

    def last_row_are_waiting(self, car_dict):
        """
        判断道路起始位置的三辆车是否存在等待情况
        函数至此，已假定最后一排存在三辆车，此条件用以用于断言
        :return:
        """
        assert np.all(self.roadStatus[:, 0] != -1)  # 断言，不应该出现空位存在
        for i in range(self.roadChannel):
            if car_dict[self.roadStatus[i, 0]].is_car_waiting():
                return True
        return False

    def get_road_weight(self):
        """
        车越多越堵，数值越大
        简单版本： 只统计个数
        复杂版本： 从后到前，权重加大
        :return:
        """
        # 占车位百分比，越大越堵
        carNumber = np.sum(self.roadStatus != -1)
        carsPercent = carNumber * 1.0 / (self.roadLength * self.roadChannel)

        # 分布分数，越大越堵
        wheresCar = np.where(self.roadStatus != -1)
        carsPosSum = np.sum(wheresCar[1])

        distribution_score = 2 * (carNumber * self.roadLength - carsPosSum) / ((self.roadLength + 1) * self.roadLength * self.roadChannel)

        return carsPercent + distribution_score
