# coding:utf-8
import numpy as np
from car import Car


class Road(object):
    """
    道路信息
    """
    def __init__(self, road_id, length, speed_limit, channel, origin, dest):
        self.roadID = road_id  # 道路编号
        self.roadLength = length  # 道路长度
        self.roadSpeedLimit = speed_limit  # 道路限速
        self.roadChannel = channel  # 车道数目
        self.roadOrigin = origin  # 道路起点
        self.roadDest = dest  # 道路终点
        self.roadStatus = self.initialize_road()  # 道路详情

    def initialize_road(self):
        """
        初始化道路详情，全部置-1
        :return:
        """
        channel = self.roadChannel
        length = self.roadLength
        road_detail = np.ones((channel, length)) * -1
        return road_detail.astype(np.int16)  # 车辆编号较大

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
                    # 获取车对象
                    car_obj = car_dict[self.roadStatus[channel, grid]]
                    # 标记所有车辆为待处理状态
                    car_obj.change2waiting()
                    # 调度车辆
                    self.update_car(car_obj, channel, grid, car_dict)

    def update_car(self, car_obj, channel, grid, car_dict):
        """
        调度车辆(第一轮调度，待出路口只标记为等待)
        :param car_obj:
        :param channel:
        :param grid:
        :param car_dict:
        :return:
        """
        # 断言检测 车辆位置
        car_channel = car_obj.carGPS['channel']
        car_pos = car_obj.carGPS['pos']
        assert car_channel == channel
        assert car_pos == grid

        speed = min(car_obj.carSpeed, self.roadSpeedLimit)  # 获取车速
        len_remain = self.roadLength - (car_pos + 1)  # 道路剩余长度

        # 准备出路口
        if len_remain < speed:
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos + 1, self.roadLength)
            # 前方有车
            if has_car:
                # 前车正在等待
                if car_dict[front_id].is_car_waiting():
                    car_obj.change2waiting_out()  # 标记为等待调度出路口
                # 前车调度结束
                else:
                    dis = front_pos - car_pos
                    assert dis >= 1  # 两车相距大于一
                    if dis == 1:
                        car_obj.change2end()  # 本就在前车屁股，无需调度
                    else:
                        new_pos = front_pos - 1  # 还能前进一段，新位置在前车屁股
                        self.move_car_to(car_channel, car_pos, new_pos, car_obj)  # 移动车辆
            # 前方无车
            else:
                # 前方到家
                if car_obj.is_car_way_home():
                    self.move_car_home(car_obj)  # 到家
                # 前方出路口
                else:
                    car_obj.change2waiting_out()  # 标记为等待调度出路口
        # 不准备出路口
        else:
            has_car, front_pos, front_id = self.has_car(car_channel, car_pos + 1, car_pos + speed + 1)
            # 前方有车
            if has_car:
                # 前车正在等待
                if car_dict[front_id].is_car_waiting():
                    car_obj.change2waiting_inside()  # 标记为等待且不出路口
                # 前车结束调度
                else:
                    dis = front_pos - car_pos
                    assert dis >= 1  # 要是距离短于1就见鬼了
                    if dis == 1:
                        car_obj.change2end()  # 本就在前车屁股，无需调度
                    else:
                        new_pos = front_pos - 1  # 还能前进一段，新位置在前车屁股
                        self.move_car_to(car_channel, car_pos, new_pos, car_obj)  # 移动车辆
            # 前方无车
            else:
                new_pos = car_pos + speed
                self.move_car_to(car_channel, car_pos, new_pos, car_obj)  # 移动车辆

    def move_car_to(self, car_channel, car_pos, new_pos, car_obj):
        """
        移动车辆到指定位置
        :return:
        """
        # 注册新位置
        self.roadStatus[car_channel, new_pos] = car_obj.carID
        # 抹除旧位置
        if car_pos != -1:  # 也存在车从家里出发的情况
            self.roadStatus[car_channel, car_pos] = -1
        # 更新到车辆信息
        car_obj.mark_new_pos(road_id=self.roadID, channel=car_channel, pos=new_pos, this_cross=self.roadOrigin,
                             next_cross=self.roadDest)
        # 标记车辆为EndState
        car_obj.change2end()

    def has_car(self, channel, start, end):
        """
        判断车道内某段区域是否有车
        :param channel:     车道
        :param start:       车前方一格
        :param end:         目标占领点前方一格
        :return:            bool, front_pos, front_id
        """
        # 车已在目标位置
        if start == end:
            return False, None, None
        channel_detail = self.roadStatus[channel, :].flatten()

        for grid in range(start, end, 1):
            if channel_detail[grid] == -1:
                continue
            else:  # 有车阻挡
                return True, grid, channel_detail[grid]
        return False, None, None

    def try_on_road(self, car_obj):
        """
        # 车辆入驻道路
        # 输入：car对象
        # 输出：True,成功； False,失败
        :param car_obj:
        :return:
        """
        # 对象断言检测
        assert isinstance(car_obj, Car)
        # 1. 找车位
        channel, pos = self.get_checkin_place()
        if channel is None:
            return False  # 上路失败

        # 2. 根据车速和前车位置 判断新位置
        new_pos = min(car_obj.carSpeed - 1, self.roadSpeedLimit - 1, pos)
        # 3. 移动车辆
        self.move_car_to(channel, -1, new_pos, car_obj)

        return True  # 上路成功

    def get_checkin_place(self):
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

    def get_first_order_car(self, car_dict):
        """
        获取本条道路的第一优先级车辆（只考虑出路口的车辆）
        此处效率要优化
        :return:
        """
        # 根据优先序列遍历车辆
        for grid in range(self.roadLength - 1, -1, -1):
            for channel in range(self.roadChannel):
                if self.roadStatus[channel, grid] != -1:
                    # 获取车对象
                    car = car_dict[self.roadStatus[channel, grid]]
                    if car.is_car_waiting_out():
                        return car

        # 如果没有则返回NONE
        return None

    def move_car_home(self, car_obj):
        """
        移动车辆回家
        :param car_obj:
        :return:
        """
        assert car_obj.is_car_way_home()  # 直接断言 道路正确
        car_id = car_obj.carID
        car_channel = car_obj.carGPS['channel']
        car_pos = car_obj.carGPS['pos']
        assert self.roadStatus[car_channel, car_pos] == car_id  # 直接断言 车辆所处位置正确

        self.roadStatus[car_channel, car_pos] = -1  # 将车辆所在位置置空
        car_obj.change2success()  # 更改车辆状态

    def update_channel(self, channel_id, car_dict):
        """
        当有车更新到终止态之后，要更新一次当前车道的车辆
        :param car_dict:
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

    def get_road_weight(self, dist_k=1.0):
        """
        车越多越堵，数值越大
        简单版本： 只统计个数
        复杂版本： 从后到前，权重加大
        也可以超参
        :return:
        """
        # 占车位百分比，越大越堵
        car_number = np.sum(self.roadStatus != -1)
        cars_percent = car_number * 1.0 / (self.roadLength * self.roadChannel)

        # 分布分数，越大越堵
        wheres_car = np.where(self.roadStatus != -1)
        cars_pos_sum = np.sum(wheres_car[1])
        distribution_score = 2 * (car_number * self.roadLength - cars_pos_sum) / (
                (self.roadLength + 1) * self.roadLength * self.roadChannel)

        return cars_percent + distribution_score*dist_k
