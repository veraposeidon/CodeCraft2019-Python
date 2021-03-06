# coding:utf-8

import logging
import sys

from utils import read_road, read_cross, read_car
from car import Car
from cross import Cross
from road import Road

from trafficManager import TrafficManager
from dijsktra import create_topology

logging.basicConfig(level=logging.DEBUG,
                    filename='./logs/CodeCraft-2019.log',
                    format='[%(asctime)s] %(levelname)s [%(funcName)s: %(filename)s, %(lineno)d] %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S',
                    filemode='a')


def main():
    if len(sys.argv) != 5:
        # logging.info('please input args: car_path, road_path, cross_path, answerPath')
        print('please input args: car_path, road_path, cross_path, answerPath')
        exit(1)

    car_path = sys.argv[1]
    road_path = sys.argv[2]
    cross_path = sys.argv[3]
    answer_path = sys.argv[4]

    logging.info("car_path is %s" % (car_path))
    logging.info("road_path is %s" % (road_path))
    logging.info("cross_path is %s" % (cross_path))
    logging.info("answer_path is %s" % (answer_path))

    # 简单来说就是一本任务手册，有三大部分。
    # 1.1 读入road文件
    roads_dict = read_road(road_path)
    # 1.2 读入cross文件
    crosses_dict = read_cross(cross_path)
    # 1.3 读入car文件
    cars_dict = read_car(car_path)

    # 2. process 调度数据

    # 2.1 根据 Road 生成拓扑地图
    topologyDict = create_topology(roads_dict)

    # # 绘图
    # from utils import networkx
    # G = networkx(topologyDict, plot=True)

    # 2.2 生成车辆对象
    cars = {}
    for item in cars_dict.keys():
        car_ = Car(car_id=cars_dict[item]['id'],
                   origin=cars_dict[item]['from'],
                   destination=cars_dict[item]['to'],
                   speed=cars_dict[item]['speed'],
                   plan_time=cars_dict[item]['planTime'],
                   topology=topologyDict)
        cars[car_.carID] = car_
    # 删除变量，释放内存
    del cars_dict


    # 2.3 生成道路对象
    roads = {}
    for item in roads_dict.keys():
        road_ = Road(road_id=roads_dict[item]['id'],
                     length=roads_dict[item]['length'],
                     speed_limit=roads_dict[item]['speed'],
                     channel=roads_dict[item]['channel'],
                     origin=roads_dict[item]['from'],
                     dest=roads_dict[item]['to'])
        roads[str(road_.roadOrigin) + "_" + str(road_.roadDest)] = road_

        if roads_dict[item]['isDuplex'] == 1:
            road_ = Road(road_id=roads_dict[item]['id'],
                         length=roads_dict[item]['length'],
                         speed_limit=roads_dict[item]['speed'],
                         channel=roads_dict[item]['channel'],
                         origin=roads_dict[item]['to'],
                         dest=roads_dict[item]['from'])
            roads[str(road_.roadOrigin) + "_" + str(road_.roadDest)] = road_
    # 删除变量，释放内存
    del roads_dict

    # 2.4 根据 Cross 生成每个信号灯对象
    # 可以删除cross_dict对象了
    crosses = {}
    for item in crosses_dict.keys():
        cross_ = Cross(cross_id=crosses_dict[item]['id'],
                       road1=crosses_dict[item]['road1'],
                       road2=crosses_dict[item]['road2'],
                       road3=crosses_dict[item]['road3'],
                       road4=crosses_dict[item]['road4'],
                       road_dict=roads)
        crosses[cross_.crossID] = cross_
    # 删除变量，释放内存
    del crosses_dict


    # 将世界地图和调度任务送入调度中心，由调度中心进行演算，得到安排结果
    manager = TrafficManager(topology_dict=topologyDict,
                             cross_dict=crosses,
                             car_dict=cars,
                             road_dict=roads)
    # 进行演算
    manager.inference()

    # 得到演算结果
    result = manager.get_result()

    # 3. 调度结果写入输出文件
    # TODO: 写入 answer_path
    with open(str(answer_path), 'w') as f:
        # result.keys().sort()    # 看有没有排序要求了
        for carID in result.keys():
            text = '(' + str(carID) + ", " + str(result[carID]['startTime']) + ", " + ", ".join(
                str(x) for x in result[carID]['roads']) + ")" + "\n"
            f.write(text)


if __name__ == "__main__":
    import time

    start = time.clock()

    main()

    elapsed = (time.clock() - start)
    print("Program Time:" + str(elapsed))
