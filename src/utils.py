# coding:utf-8


def read_road(road_path):
    """
    道路信息读取
    format: (id,length,speed,channel,from,to,isDuplex)
    :param road_path:
    :return:
    """
    roads_dict = dict()
    with open(str(road_path), 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            data = line.strip().strip('(').strip(')').split(', ')
            road = dict()
            road['id'] = int(data[0])
            road['length'] = int(data[1])
            road['speed'] = int(data[2])
            road['channel'] = int(data[3])
            road['from'] = int(data[4])
            road['to'] = int(data[5])
            road['isDuplex'] = int(data[6])
            roads_dict[road['id']] = road
    return roads_dict


def read_cross(cross_path):
    """
    路口信息读取
    format: (id,roadId,roadId,roadId,roadId)
    :param cross_path:
    :return:
    """
    crosses_dict = dict()
    with open(str(cross_path), 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            data = line.strip().strip('(').strip(')').split(', ')
            cross = dict()
            cross['id'] = int(data[0])
            cross['road1'] = int(data[1])
            cross['road2'] = int(data[2])
            cross['road3'] = int(data[3])
            cross['road4'] = int(data[4])
            crosses_dict[cross['id']] = cross
    return crosses_dict


def read_car(car_path):
    """
    车辆信息读取
    format: (id,from,to,speed,planTime)
    :param car_path:
    :return:
    """
    cars_dict = dict()
    with open(str(car_path), 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            data = line.strip().strip('(').strip(')').split(', ')
            car = dict()
            car['id'] = int(data[0])
            car['from'] = int(data[1])
            car['to'] = int(data[2])
            car['speed'] = int(data[3])
            car['planTime'] = int(data[4])
            cars_dict[car['id']] = car
    return cars_dict


# def networkx(topology_dict, plot=False):
#     """
#     networkx 工具箱
#     :param topology_dict:
#     :param plot:
#     :return:
#     """
#     import networkx as nx
#     g = nx.DiGraph()
#
#     # 节点
#     for node in topology_dict.keys():
#         g.add_node(node)
#
#     # 边
#     edge_label = dict()
#     for item in topology_dict.items():
#         for edge in item[1]:
#             g.add_edge(edge['start'], edge['end'], length=edge['length'], weight=edge['length'])
#             edge_label[(edge['start'], edge['end'])] = str(edge['road_id']) + ":" + str(edge['length'])
#
#     print(g.number_of_nodes())
#     print(g.number_of_edges())
#
#     if plot:
#         import matplotlib.pyplot as plt
#         pos = nx.spring_layout(g, weight='length')
#         nx.draw(g, pos, with_labels=True, edge_color='blue', font_weight='bold', node_size=200, node_color='pink')
#         nx.draw_networkx_edge_labels(g, pos, edge_labels=edge_label)
#         plt.show()
#
#     return g
