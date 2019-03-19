# coding:utf-8
import numpy as np
from car import car

# 切记数组下标与实际道路长度
# 定义道路信息
class road(object):
    def __init__(self, id, length, speedlimit, channel, origin, dest):
        self.roadID = id
        self.roadLength = length
        self.roadSpeedLimit = speedlimit
        self.roadChannel = channel
        self.roadOrigin = origin
        self.roadDest = dest
        self.roadStatus = self.initializeRoad()

    # (channel, length), channel递增，length从道路起点到终点递增
    def initializeRoad(self):
        channel = self.roadChannel
        length = self.roadLength
        roadDetail = np.ones((channel, length)) * -1
        return roadDetail.astype(np.int16)  # 位数也很重要

    # 更新一遍即可
    def update_road(self, carDict):
        # 根据优先序列遍历车辆
        for grid in range(self.roadLength-1, -1, -1):
            for channel in range(self.roadChannel):
                if self.roadStatus[channel, grid] != -1:
                    # 获取车对象
                    car = carDict[self.roadStatus[channel, grid]]
                    # 标记所有车辆为待处理状态
                    car.change2waiting()
                    # 调度车辆
                    self.update_car(car, channel, grid, carDict)

    # 调度车辆（出路口只标记为等待）
    def update_car(self, car, channel, grid, carDict):
        # 1. 获取车辆位置,并进行比对
        car_channel = car.carLocation['channel']
        car_pos = car.carLocation['pos']
        # 断言检测
        assert car_channel == channel
        assert car_pos == grid

        # 2. 获取车速，判断剩余长度，判断车辆行驶类型
        speed = min(car.carSpeed, self.roadSpeedLimit)
        lenRemain = self.roadLength - (car_pos + 1)

        if lenRemain < speed:   # 准备出路口
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos+1, self.roadLength)
            if has_car:     # 前方有车
                if carDict[front_id].iscarWaiting():    # 前车正在等待
                    car.change2waiting_out()    # 标记为等待出去
                    # TODO: 此处可以重新进行路径规划，以确定下一阶段道路在哪和出路口方向
                else:
                    car.change2end()        # 标记为调度结束
            else:           # 前方无车
                # 出路口，前方无车(两种情况：到达终点和准备出路口)
                if car.iscar_wayhome():     # 前方到家，更改状态，抹除该车
                    car.change2success()    # 更改车辆状态
                    self.roadStatus[car_channel,car_pos] = -1  # 将车辆所在位置置空
                else:                           # 前方出路口，获取转弯方向
                    car.change2waiting_out()    # 标记为等待出去
                    # TODO: 此处可以重新进行路径规划，以确定下一阶段道路在哪和出路口方向
        else:                   # 不会出路口
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos + 1, car_pos+speed+1)
            if has_car:     # 前方有车
                if carDict[front_id].iscarWaiting():    # 前车正在等待
                    car.change2waiting_inside()         # 标记为等待且不出路口
                else:                           # 前车结束调度，需判断还能否前进
                    dis = front_pos - car_pos
                    assert dis >= 1             # 要是距离短于1就见鬼了
                    if dis == 1:
                        car.change2end()        # 本就在前车屁股，无需调度
                    else:
                        new_pos = front_pos - 1     # 还能前进一段，新位置在前车屁股
                        # 注册新位置
                        self.roadStatus[car_channel, new_pos] = car.carID
                        # 抹除旧位置
                        self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
                        # 更新到车辆信息
                        car.mark_new_pos(roadID=self.roadID, channel=car_channel, pos=new_pos)
                        # 标记车辆为EndState
                        car.change2end()

            else:           # 前方无车
                new_pos = car_pos + speed
                # 注册新位置
                self.roadStatus[car_channel, new_pos] = car.carID
                # 抹除旧位置
                self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                car.mark_new_pos(roadID=self.roadID, channel=car_channel, pos=new_pos)
                # 标记车辆为EndState
                car.change2end()


    def has_car(self, channel, start, end):
        """
        判断车道内某段区域是否有车
        :param channel:
        :param start:
        :param end:
        :return:
        """
        if start == end:    # 已在道路最前端
            return False, None, None
        channeldetail = self.roadStatus[channel, :].flatten()
        for grid in range(start, end, 1):
            if channeldetail[grid] == -1:
                continue
            else:   # 有车阻挡
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
        assert isinstance(carObj, car)

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
        carObj.mark_new_pos(roadID=self.roadID, channel=channel, pos=pos)

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
            return 0, self.roadLength - 1   # 注意下标

        # 道路不为空
        for channel in range(self.roadChannel):
            # channel 满(判断最后一辆车就好)
            if self.roadStatus[channel, 0] != -1:
                continue
            # channel 不满
            for pos in range(self.roadLength):
                if self.roadStatus[channel, pos] == -1:
                    if pos == self.roadLength - 1:   # 到头，那就是最大长度
                        return channel, pos
                    continue
                else:
                    return channel, pos-1   # 返回空位置，而不是有阻挡的位置
        # 全满
        return None, None

    def get_first_order_car(self, carDict):
        """
        获取本条道路的第一优先级车辆（只考虑出路口哦）
        TODO 其实最优路径的更新也可以放在此处
        :return:
        """
        # 根据优先序列遍历车辆
        for grid in range(self.roadLength - 1, -1, -1):
            for channel in range(self.roadChannel):
                if self.roadStatus[channel, grid] != -1:
                    # 获取车对象
                    car = carDict[self.roadStatus[channel, grid]]
                    if car.iscarWaiting_out():
                        return car

        # 如果没有则返回NONE
        return None

    def move_car_home(self, carO):
        """
        移动车辆回家
        :param carO:
        :return:
        """
        assert carO.iscar_wayhome(self.roadID)     # 直接断言 道路正确
        car_id = carO.carID
        car_channel = carO.carLocation['channel']
        car_pos = carO.carLocation['pos']
        assert self.roadStatus[car_channel, car_pos] is car_id  # 直接断言 车辆所处位置正确

        car.change2success()  # 更改车辆状态
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
                if car.iscarWaiting():
                    # 调度车辆
                    self.update_car(car, channel_id, grid, car_dict)

    def last_row_are_waiting(self,car_dict):
        """
        判断道路起始位置的三辆车是否存在等待情况
        函数至此，已假定最后一排存在三辆车，此条件用以用于断言
        :return:
        """
        assert np.all(self.roadStatus[:, 0] != -1)  # 断言，不应该出现空位存在
        for i in range(self.roadChannel):
            if car_dict[self.roadStatus[i, 0]].iscarWaiting():
                return True
        return False


