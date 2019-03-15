# coding:utf-8


# 读取road文件
def read_road(road_path):
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


# 读取cross文件
def read_cross(cross_path):
    crosses_dict = dict()
    with open(str(cross_path), 'r') as f:
        for line in f.readlines():
            if line.startswith('#'):
                continue
            data = line.strip().strip('(').strip(')').split(', ')
            cross = dict()
            cross['id'] = int(data[0])
            cross['roadId0Clock'] = int(data[1])
            cross['roadId3Clock'] = int(data[2])
            cross['roadId6Clock'] = int(data[3])
            cross['roadId9Clock'] = int(data[4])
            crosses_dict[cross['id']] = cross
    return crosses_dict


# 读取car文件
def read_car(car_path):
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

# # networkx 工具箱
# def networkx(topologyDict, plot=False):
#     import networkx as nx
#     G = nx.DiGraph()

#     # 节点
#     for node in topologyDict.keys():
#         G.add_node(node)

#     # 边
#     edge_label = dict()
#     for item in topologyDict.items():
#         for edge in item[1]:
#             G.add_edge(edge['start'], edge['end'], length=edge['length'], weight = edge['length'])
#             edge_label[(edge['start'], edge['end'])] = str(edge['roadid']) + ":" + str(edge['length'])

#     print(G.number_of_nodes())
#     print(G.number_of_edges())

#     if plot:
#         import matplotlib.pyplot as plt
#         # G = nx.petersen_graph()
#         # plt.subplot(121)
#         pos = nx.spring_layout(G, weight='length')
#         nx.draw(G, pos, with_labels=True, edge_color='blue', font_weight='bold', node_size=200, node_color='pink')
#         nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_label)
#         plt.show()

#     return G
