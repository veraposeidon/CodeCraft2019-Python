# coding:utf-8

LOOPS_EVERY_CROSS = 1

# 交叉路口对象
# 还可以在此处安排优先级
# 相当于交叉路口安排一个调度员
# 对于一条道路，有多少车要准备出去，有多少车要准备近来。出去多少长度，近来多少长度
# 也就是说，我认为，调度的顺序应该是计算预测下一步的操作，进行判断，遍历完之后，再统一更新状态。
class cross(object):
    def __init__(self, id, road1, road2, road3, road4):
        self.crossID = id
        self.roads = [road1, road2, road3, road4]  # 道路分布
        self.roads_prior = self.get_priors()  # 道路调度优先级

    def get_priors(self):
        roadPrior = self.roads.copy()  # 此处要用深拷贝
        roadPrior.sort()  # 升序
        roadPrior = [x for x in roadPrior if x != -1]  # 去掉-1
        return roadPrior

    def update_cross(self, road_dict, car_dict):
        # 2. 重复调度每个道路（处理每个道路的第一优先级），应该调度N遍即可。实在完不成就只能等其他路口调度完了再回来。
        for i in range(LOOPS_EVERY_CROSS):
            # 获取待调度道路信息
            next_roads = self.get_first_order_info(road_dict, car_dict)
            road_priors = sorted(next_roads.keys())

            # 2. 根据优先级，分别判断每个路口是否满足出路口（路口规则）
            for roadID in road_priors:
                last_car = next_roads[roadID]['carO']   # 待调度车辆

                while roadID in next_roads:     # 确保路口的每一轮调度都最大化道路的运输能力，除非转弯顺序不允许或者没有待转弯车辆了。

                    # 对方向进行判断
                    dirct = next_roads[roadID]['direction']
                    if dirct is "D":    # 直行优先
                        pass
                    elif dirct is "L":  # 左转需要判断有无直行到目标道路车辆
                        if self.has_straight_to_conflict(next_roads, next_roads[roadID]['next_road_id']):  # 有直行车辆，跳过
                            break   # 跳出while 调度下一道路
                    elif dirct is "R":  # 右转需要哦安短有无直行或左转到目标道路车辆
                        if self.has_straight_left_to_conflict(next_roads,
                                                          next_roads[roadID]['next_road_id']):  # 有直行或左转车辆，跳过
                            break   # 跳出while 调度下一道路

                    # 调度车辆
                    carO = next_roads[roadID]['carO']
                    thisRoad = road_dict[next_roads[roadID]['road_name']]
                    nextRoad = road_dict[next_roads[roadID]['next_road_name']]
                    self.move_car_across(carO, thisRoad, nextRoad, car_dict)

                    next_roads = self.get_first_order_info(road_dict, car_dict)     # 获取新的第一优先级的信息

                    # 判断更新后的优先车辆是否没动
                    if roadID in next_roads:
                        this_car = next_roads[roadID]['carO']
                        if this_car == last_car:
                            break   # 跳出，调度下一道路
                        else:
                            last_car = this_car

    def get_direction(self, roadID, next_road):
        """
        判断出路口转向
        :param roadID:
        :param next_road:
        :return:
        """
        index_now = self.roads.index(roadID)
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
    def has_straight_to_conflict(roads_map, target_road_ID):
        """
        判断有无直行进入目标车道的车辆发生冲突
        :param road_name:
        :return:
        """
        for key in roads_map.keys():
            if roads_map[key]['next_road_id'] == target_road_ID and roads_map[key]['direction'] == 'D':
                return True
        return False

    @staticmethod
    def has_straight_left_to_conflict(roads_map, target_road_ID):
        """
        判断有无直行或左转进入目标车道的车辆发生冲突
        :param roads_map:
        :param target_road_ID:
        :return:
        """
        for key in roads_map.keys():
            if roads_map[key]['next_road_id'] == target_road_ID and (
                    roads_map[key]['direction'] == 'D' or roads_map[key]['direction'] == 'L'):
                return True
        return False

    def get_first_order_info(self, road_dict, car_dict):
        """
        更新获取第一优先级车辆信息，如果第一优先级的车是回家的车，就直接回家，不参与
        :return:
        """
        roadPrior = [self.find_road_name_to_cross(road_dict, id) for id in self.roads_prior]
        roadPrior = [o for o in roadPrior if o is not None]  # 单向道路会产生None

        next_roads = dict()

        for road_name in roadPrior[:]:
            while True:
                carO = road_dict[road_name].get_first_order_car(car_dict)
                if carO is None:  # 当前道路没有待出路口车辆
                    roadPrior.remove(road_name)  # 当前道路不参与调度
                    break

                else:  # 当前道路有待出路口车辆,
                    if carO.next_road_name(self.crossID) is None:  # 判断是否要回家的
                        # 更新回家车辆
                        road_dict[road_name].move_car_home(carO)
                        # 更新车道信息
                        road_dict[road_name].update_channel(carO.carLocation['channel'], car_dict)
                        continue  # 继续更新本条道路的第一优先级

                    else:
                        # 车辆下一条路的名称
                        next_road_name = carO.next_road_name(self.crossID)

                        # 获取道路ID
                        road_now_id = road_dict[road_name].roadID
                        road_next_id = road_dict[next_road_name].roadID
                        assert road_now_id != road_next_id  # 聊胜于无  # 出现相同是因为计划路线出现了掉头，这个是不允许的。要在车辆更新路线时进行否定

                        # 获取方向,填入信息
                        direction = self.get_direction(road_now_id, road_next_id)
                        next_roads[road_now_id] = {'carO': carO,
                                                   'road_name': road_name,
                                                   'next_road_id': road_next_id,
                                                   'next_road_name': next_road_name,
                                                   'direction': direction}
                        break  # 换道
        return next_roads

    def find_road_name_to_cross(self, road_dict, road_ID):
        """
        根据道路ID和路口名称找道路
        :param road_ID:
        :param road_dict:
        :return:
        """
        for key in road_dict.keys():
            if (road_dict[key].roadID == road_ID) and (road_dict[key].roadDest == self.crossID):
                return key
        return None

    def move_car_across(self, carO, thisRoad, nextRoad, car_dict):
        """
        跨路口移动车辆，较为复杂, 需要耐心
        TODO: 假设这些待转车辆前方都没有阻挡的车的。
        假设前方的车 已经 end 了，后方的车会更新到end
        假设前方的车 在waiting， 后方的车轮不到第一优先级。
        :param carO: 车辆对象
        :param thisRoad: 当前道路对象
        :param nextRoad: 目标道路对象
        :return:
        """
        # 1. 找到待进入车道：
        next_channel, next_pos = nextRoad.getcheckInPlace()

        # 前方道路堵住
        # 前方道路堵住需要探讨（前方道路的车是终结态还是等待态，只要最后有车等待，那就可以等待，如果最后一排的车全为终结，那就终结）
        if next_channel is None:  # 表示下一道路全满
            # print("真堵车了")
            # 判断下一道路最后一辆车的状态
            if nextRoad.last_row_are_waiting(car_dict):  # 如果下一条道路有车在等待,则本车也只能等待
                carO.change2waiting_out()  # 后面的车不需要动
            else:  # 前车终止态，本车运行到道路前方
                new_pos = thisRoad.roadLength - 1  # 注意下标
                new_channel = carO.carLocation['channel']

                # 判断位置是否为相同
                if carO.carLocation['pos'] == new_pos:
                    carO.change2end()  # 保持不动
                else:
                    # 注册新位置
                    thisRoad.roadStatus[new_channel, new_pos] = carO.carID
                    # 抹除旧位置
                    thisRoad.roadStatus[new_channel, carO.carLocation['pos']] = -1  # 将车辆所在位置置空
                    # 更新到车辆信息
                    carO.mark_new_pos(roadID=thisRoad.roadID, channel=new_channel, pos=new_pos,this_cross=thisRoad.roadOrigin, next_cross=thisRoad.roadDest)
                    # 标记车辆为EndState
                    carO.change2end()

                # 更新后面车道的车辆
                thisRoad.update_channel(new_channel, car_dict)
            return

        # 前方道路没堵住
        assert thisRoad.roadStatus[carO.carLocation['channel'], carO.carLocation['pos']] == carO.carID  # 聊胜于无的断言

        remain_dis = (thisRoad.roadLength - 1) - carO.carLocation['pos']  # 上端剩余距离
        speed = min(carO.carSpeed, nextRoad.roadSpeedLimit)
        real_dis = max(speed - remain_dis, 0)
        if real_dis == 0:  # 表示不支持转入下一道路，现在调度到本车道终点处，不变channel
            new_pos = thisRoad.roadLength - 1  # 注意下标
            old_channel = carO.carLocation['channel']
            old_pos = carO.carLocation['pos']

            # 判断位置是否为相同
            if carO.carLocation['pos'] == new_pos:
                carO.change2end()  # 保持不动
            else:
                # 注册新位置
                thisRoad.roadStatus[old_channel, new_pos] = carO.carID
                # 抹除旧位置
                thisRoad.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                carO.mark_new_pos(roadID=thisRoad.roadID, channel=old_channel, pos=new_pos,this_cross=thisRoad.roadOrigin,next_cross=thisRoad.roadDest)
                # 标记车辆为EndState
                carO.change2end()

            # 更新后面车道的车辆
            thisRoad.update_channel(old_channel, car_dict)
            return

        else:  # 有机会调度到下一道路# 三种情况，够长，直接到位；前方有车，endstate，追尾；前方有车，waiting,不动waiting。
            new_pos = real_dis - 1  # 注意下标
            old_channel = carO.carLocation['channel']
            old_pos = carO.carLocation['pos']

            # 判断前方有无车辆
            has_car, front_pos, front_id = nextRoad.has_car(next_channel, 0, new_pos + 1)
            if has_car:  # 前方有车
                if car_dict[front_id].iscarWaiting():  # 前车正在等待
                    carO.change2waiting_out()  # 标记为等待出路口
                else:  # 前车结束
                    dis = front_pos
                    assert dis >= 1  # 要是距离短于1就见鬼了
                    new_pos = front_pos - 1  # 还能前进一段，新位置在前车屁股
                    # 注册新位置
                    nextRoad.roadStatus[next_channel, new_pos] = carO.carID
                    # 抹除旧位置
                    thisRoad.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                    # 更新到车辆信息
                    carO.mark_new_pos(roadID=nextRoad.roadID, channel=next_channel, pos=new_pos, this_cross=nextRoad.roadOrigin, next_cross=nextRoad.roadDest)
                    # 标记车辆为EndState
                    carO.change2end()
            else:
                # 注册新位置
                nextRoad.roadStatus[next_channel, new_pos] = carO.carID
                # 抹除旧位置
                thisRoad.roadStatus[old_channel, old_pos] = -1  # 将车辆所在位置置空
                # 更新到车辆信息
                carO.mark_new_pos(roadID=nextRoad.roadID, channel=next_channel, pos=new_pos,this_cross=nextRoad.roadOrigin, next_cross=nextRoad.roadDest)
                # 标记车辆为EndState
                carO.change2end()
            # 更新后方车道
            thisRoad.update_channel(old_channel, car_dict)
            return
