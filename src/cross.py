# coding:utf-8
from copy import deepcopy


class Cross(object):
    """
    路口信息
    """

    def __init__(self, cross_id, road1, road2, road3, road4, road_dict,
                 loops_every_cross=1):
        self.crossID = cross_id
        self.roads = [road1, road2, road3, road4]  # 道路分布
        # 本路口道路调度优先级    id表示
        self.roads_prior_id = self.get_road_priors()
        # 本路口道路调度优先级    name表示
        self.roads_prior_name = [self.find_road_name_to_cross(road_dict, r_id) for r_id in self.roads_prior_id]
        self.roads_prior_name = [o for o in self.roads_prior_name if o is not None]  # 去除单向道路
        self.LOOPS_EVERY_CROSS = loops_every_cross  # 路口调度循环次数

    def get_road_priors(self):
        """
        路口调度道路的优先级，按照id升序
        :return:
        """
        road_prior = deepcopy(self.roads)  # 此处要用深拷贝,避免影响原有分布
        road_prior.sort()  # 升序
        road_prior = [x for x in road_prior if x != -1]  # 去掉-1
        return road_prior

    def find_road_name_to_cross(self, road_dict, road_id):
        """
        根据道路ID和路口名称找道路名称
        :param road_id:     道路ID
        :param road_dict:   道路字典
        :return:            道路名称
        """
        for key in road_dict.keys():
            if (road_dict[key].roadID == road_id) and (road_dict[key].roadDest == self.crossID):
                return key
        return None

    def update_cross(self, road_dict, car_dict):
        """
        调度路口多次。
        需要注意，单一路口调度不一定能够完成，需要配合其他路口调度。
        所以多次调度之后即可跳出，调度无法完成的车辆会在下次遍历到该路口时继续调度。
        :param road_dict:
        :param car_dict:
        :return:
        """
        for i in range(self.LOOPS_EVERY_CROSS):
            # 获取待调度道路和车辆信息
            next_roads = self.get_first_order_info(road_dict, car_dict)
            road_priors = sorted(next_roads.keys())

            # 2. 根据优先级，分别判断每个路口是否满足出路口（路口规则）
            for roadID in road_priors:
                last_car = next_roads[roadID]['carO']  # 待调度车辆
                while roadID in next_roads:  # 确保路口的每一轮调度都最大化道路的运输能力，除非转弯顺序不允许或者没有待转弯车辆了。

                    # 对方向进行判断
                    direct = next_roads[roadID]['direction']
                    if direct is "D":  # 直行优先
                        pass
                    elif direct is "L":
                        # 左转需要判断有无直行到目标道路车辆
                        # 有直行车辆冲突，跳过
                        if self.has_straight_to_conflict(next_roads, next_roads[roadID]['next_road_id']):
                            break  # 跳出while 调度下一道路
                    elif direct is "R":
                        # 右转需要哦安短有无直行或左转到目标道路车辆
                        # 有直行或左转车辆冲突，跳过
                        if self.has_straight_left_to_conflict(next_roads,
                                                              next_roads[roadID]['next_road_id']):
                            break  # 跳出while 调度下一道路

                    # 调度车辆
                    car_o = next_roads[roadID]['carO']
                    this_road = road_dict[next_roads[roadID]['road_name']]
                    next_road = road_dict[next_roads[roadID]['next_road_name']]
                    self.move_car_across(car_o, this_road, next_road, car_dict)

                    # 调度之后除去道路第一优先序车辆记录
                    this_road.first_order_car = None

                    # 只更新该道路的优先序车辆
                    road_id, first_info = self.get_road_first_order_info(next_roads[roadID]['road_name'], road_dict,
                                                                         car_dict)
                    # 该道路还有待调度车辆
                    if road_id is not None:
                        next_roads[road_id] = first_info
                        # 判断更新后的第一辆车还是不是之前的
                        this_car = next_roads[roadID]['carO']
                        if this_car is last_car:
                            break  # 还是上一辆，说明没动，跳出，调度下一道路
                        else:
                            last_car = this_car
                    else:
                        del next_roads[roadID]
                        break

    def get_direction(self, road_id, next_road):
        """
        判断出路口转向
        :param road_id:
        :param next_road:
        :return:
        """
        index_now = self.roads.index(road_id)
        index_next = self.roads.index(next_road)
        assert index_next is not index_now  # 虽然废话，断言依旧

        error = index_next - index_now

        if error == 2 or error == -2:
            return 'D'
        elif error == 3 or error == -1:
            return 'R'
        elif error == 1 or error == -3:
            return 'L'

    @staticmethod
    def has_straight_to_conflict(roads_map, target_road__i_d):
        """
        判断有无直行进入目标车道的车辆发生冲突
        :param target_road__i_d:
        :param roads_map:
        :return:
        """
        for key in roads_map.keys():
            if roads_map[key]['next_road_id'] == target_road__i_d and roads_map[key]['direction'] == 'D':
                return True
        return False

    @staticmethod
    def has_straight_left_to_conflict(roads_map, target_road__i_d):
        """
        判断有无直行或左转进入目标车道的车辆发生冲突
        :param roads_map:
        :param target_road__i_d:
        :return:
        """
        for key in roads_map.keys():
            if roads_map[key]['next_road_id'] == target_road__i_d and (
                    roads_map[key]['direction'] == 'D' or roads_map[key]['direction'] == 'L'):
                return True
        return False

    def get_first_order_info(self, road_dict, car_dict):
        """
        获取第一优先级车辆信息。
        :param road_dict:
        :param car_dict:
        :return:
        """
        road_prior = self.roads_prior_name.copy()
        next_roads = dict()

        for road_name in road_prior:
            road_id, first_info = self.get_road_first_order_info(road_name, road_dict, car_dict)
            if road_id is not None:
                next_roads[road_id] = first_info
        return next_roads

    def get_road_first_order_info(self, road_name, road_dict, car_dict):
        """
        获取道路的出路口第一优先级车辆
        :param car_dict:
        :param road_dict:
        :param road_name:
        :return: None 或者 first_order_info：dict
        """
        while True:
            car_obj = road_dict[road_name].get_first_order_car(car_dict)
            # 当前道路没有待出路口车辆
            if car_obj is None:
                return None, None

            # 当前道路有待出路口车辆
            else:
                if car_obj.next_road_name(self.crossID) is None:  # 是否下一站到家
                    # 车辆回家
                    road_dict[road_name].move_car_home(car_obj)
                    # 更新车道后方信息
                    road_dict[road_name].update_channel(car_obj.carGPS['channel'], car_dict)
                    # 除去道路第一优先序车辆记录
                    road_dict[road_name].first_order_car = None
                    continue  # 继续更新本条道路的第一优先级
                else:
                    # 不回家车辆的下一条路名称
                    next_road_name = car_obj.next_road_name(self.crossID)

                    # 获取道路ID
                    road_now_id = road_dict[road_name].roadID
                    road_next_id = road_dict[next_road_name].roadID
                    assert road_now_id != road_next_id  # 聊胜于无  # 出现相同是因为计划路线出现了掉头，这个是不允许的。要在车辆更新路线时进行否定

                    # 获取方向,填入信息
                    direction = self.get_direction(road_now_id, road_next_id)
                    first_order_info = {'carO': car_obj,
                                        'road_name': road_name,
                                        'next_road_id': road_next_id,
                                        'next_road_name': next_road_name,
                                        'direction': direction}
                    return road_now_id, first_order_info

    @staticmethod
    def move_car_across(car_obj, this_road, next_road, car_dict):
        """
        跨路口移动车辆，较为复杂, 需要耐心
        可论证： 这些待转车辆前方都没有阻挡的车的。
        假设前方的车 已经 end 了，后方的车会更新到end
        假设前方的车 在waiting， 后方的车轮不到第一优先级。
        :param car_dict:
        :param car_obj: 车辆对象
        :param this_road: 当前道路对象
        :param next_road: 目标道路对象
        :return:
        """
        # 1. 找到待进入车道：
        next_channel, next_pos = next_road.get_checkin_place()

        # 前方道路堵住
        # 前方道路堵住需要探讨（前方道路的车是终结态还是等待态，只要最后有车等待，那就可以等待，如果最后一排的车全为终结，那就终结）
        if next_channel is None:  # 表示下一道路全满
            # print("真堵车了")
            # 判断下一道路最后一辆车的状态
            if next_road.last_row_are_waiting(car_dict):  # 如果下一条道路有车在等待,则本车也只能等待
                car_obj.change2waiting_out()  # 后面的车不需要动
            else:  # 前车终止态，本车运行到道路前方
                new_pos = this_road.roadLength - 1  # 注意下标
                new_channel = car_obj.carGPS['channel']

                # 判断位置是否为相同
                if car_obj.carGPS['pos'] == new_pos:
                    car_obj.change2end()  # 保持不动
                else:
                    # 注册新位置
                    this_road.roadStatus[new_channel, new_pos] = car_obj.carID
                    # 抹除旧位置
                    this_road.roadStatus[new_channel, car_obj.carGPS['pos']] = -1  # 将车辆所在位置置空
                    # 更新到车辆信息
                    car_obj.mark_new_pos(road_id=this_road.roadID, channel=new_channel, pos=new_pos,
                                         this_cross=this_road.roadOrigin, next_cross=this_road.roadDest)
                    # 标记车辆为EndState
                    car_obj.change2end()

                # 更新后面车道的车辆
                this_road.update_channel(new_channel, car_dict)
            return

        # 前方道路没堵住
        assert this_road.roadStatus[car_obj.carGPS['channel'], car_obj.carGPS['pos']] == car_obj.carID  # 聊胜于无的断言

        remain_dis = (this_road.roadLength - 1) - car_obj.carGPS['pos']  # 上端剩余距离
        speed = min(car_obj.carSpeed, next_road.roadSpeedLimit)
        real_dis = max(speed - remain_dis, 0)
        if real_dis == 0:  # 表示不支持转入下一道路，现在调度到本车道终点处，不变channel
            new_pos = this_road.roadLength - 1  # 注意下标
            old_channel = car_obj.carGPS['channel']
            old_pos = car_obj.carGPS['pos']

            # 判断位置是否为相同
            if car_obj.carGPS['pos'] == new_pos:
                car_obj.change2end()  # 保持不动
            else:
                # 注册新位置
                this_road.roadStatus[old_channel, new_pos] = car_obj.carID
                # 抹除旧位置
                this_road.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                car_obj.mark_new_pos(road_id=this_road.roadID, channel=old_channel, pos=new_pos,
                                     this_cross=this_road.roadOrigin, next_cross=this_road.roadDest)
                # 标记车辆为EndState
                car_obj.change2end()

            # 更新后面车道的车辆
            this_road.update_channel(old_channel, car_dict)
            return

        else:  # 有机会调度到下一道路# 三种情况，够长，直接到位；前方有车，endstate，追尾；前方有车，waiting,不动waiting。
            new_pos = real_dis - 1  # 注意下标
            old_channel = car_obj.carGPS['channel']
            old_pos = car_obj.carGPS['pos']

            # 判断前方有无车辆
            has_car, front_pos, front_id = next_road.has_car(next_channel, 0, new_pos + 1)
            if has_car:  # 前方有车
                if car_dict[front_id].is_car_waiting():  # 前车正在等待
                    car_obj.change2waiting_out()  # 标记为等待出路口
                else:  # 前车结束
                    dis = front_pos
                    assert dis >= 1  # 要是距离短于1就见鬼了
                    new_pos = front_pos - 1  # 还能前进一段，新位置在前车屁股
                    # 注册新位置
                    next_road.roadStatus[next_channel, new_pos] = car_obj.carID
                    # 抹除旧位置
                    this_road.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                    # 更新到车辆信息
                    car_obj.mark_new_pos(road_id=next_road.roadID, channel=next_channel, pos=new_pos,
                                         this_cross=next_road.roadOrigin, next_cross=next_road.roadDest)
                    # 标记车辆为EndState
                    car_obj.change2end()
            else:
                # 注册新位置
                next_road.roadStatus[next_channel, new_pos] = car_obj.carID
                # 抹除旧位置
                this_road.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                car_obj.mark_new_pos(road_id=next_road.roadID, channel=next_channel, pos=new_pos,
                                     this_cross=next_road.roadOrigin, next_cross=next_road.roadDest)
                # 标记车辆为EndState
                car_obj.change2end()
            # 更新后方车道
            this_road.update_channel(old_channel, car_dict)
            return
