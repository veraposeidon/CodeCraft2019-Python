# coding:utf-8

import logging
import sys

from utils import read_road, read_cross, read_car
from car import car
from cross import cross
from road import road

from trafficManager import trafficManager
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

    # 一、 读取文件
    # 1.1 读入road文件
    roads_dict = read_road(road_path)
    # 1.2 读入cross文件
    crosses_dict = read_cross(cross_path)
    # 1.3 读入car文件
    cars_dict = read_car(car_path)

    # 二、 处理数据
    # 2.1 生成拓扑地图
    topology_dict = create_topology(roads_dict)
    # networkx 可视化
    # from utils import networkx
    # g = networkx(topology_dict, plot=True)

    # 2.2 生成路口对象字典
    crosses = {}
    for item in crosses_dict.keys():
        cross_ = cross(id=crosses_dict[item]['id'],
                       road1=crosses_dict[item]['road1'],
                       road2=crosses_dict[item]['road2'],
                       road3=crosses_dict[item]['road3'],
                       road4=crosses_dict[item]['road4'])
        crosses[cross_.crossID] = cross_
    # 释放内存
    del crosses_dict

    # 2.3 生成车辆对象字典
    cars = {}
    for item in cars_dict.keys():
        car_ = car(id=cars_dict[item]['id'],
                   origin=cars_dict[item]['from'],
                   destination=cars_dict[item]['to'],
                   speed=cars_dict[item]['speed'],
                   plantime=cars_dict[item]['planTime'],
                   topology=topology_dict)
        cars[car_.carID] = car_
    # 释放内存
    del cars_dict

    # 2.4 生成道路对象字典
    roads = {}
    for item in roads_dict.keys():
        # 正向道路
        road_ = road(id=roads_dict[item]['id'],
                     length=roads_dict[item]['length'],
                     speedlimit=roads_dict[item]['speed'],
                     channel=roads_dict[item]['channel'],
                     origin=roads_dict[item]['from'],
                     dest=roads_dict[item]['to'])
        roads[str(road_.roadOrigin) + "_" + str(road_.roadDest)] = road_    # 为区分道路，使用首尾路口名来进行命名

        # 反向道路
        if roads_dict[item]['isDuplex'] == 1:
            road_ = road(id=roads_dict[item]['id'],
                         length=roads_dict[item]['length'],
                         speedlimit=roads_dict[item]['speed'],
                         channel=roads_dict[item]['channel'],
                         origin=roads_dict[item]['to'],
                         dest=roads_dict[item]['from'])
            roads[str(road_.roadOrigin) + "_" + str(road_.roadDest)] = road_
    # 释放内存
    del roads_dict

    # 构建调度中心对象
    manager = trafficManager(topologyDict=topology_dict,
                             crossDict=crosses,
                             carDict=cars,
                             roadDict=roads)
    # 调度推演
    manager.inference()

    # 演算结果
    result = manager.getResult()

    # 三、 结果写入文件
    with open(str(answer_path), 'w') as f:
        for carID in result.keys():
            text = '(' + str(carID) + ", " + str(result[carID]['startTime']) + ", " + ", ".join(
                str(x) for x in result[carID]['roads']) + ")" + "\n"
            f.write(text)


if __name__ == "__main__":
    import time
    start = time.clock()

    main()

    elapsed = (time.clock() - start)
    print("运算时间：" + str(elapsed))
