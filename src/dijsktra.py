# coding: utf-8

# 有向图graph类的实现
# 最短路径搜索算法：Dijkstra的实现
# 参考：http://benalexkeen.com/implementing-djikstras-shortest-path-algorithm-with-python/

import collections
from collections import defaultdict

# 根据道路信息 生成拓扑(注意双向则应有两条)
# （线段：首ID,尾ID，长度，道路ID）
# 地图拓扑
# 有了这份信息之后，road.txt可以抛弃了。
def createTopology(roads_dict):
    topologyDict = collections.defaultdict(lambda: [])

    for item in roads_dict.items():
        start = item[1]['from']
        end = item[1]['to']
        length = item[1]['length']
        roadid = item[1]['id']
        channel = item[1]['channel']
        oneway = {'start': start, 'end': end, 'length': length, 'roadid': roadid, 'channel': channel}
        topologyDict[start].append(oneway)
        if item[1]['isDuplex'] == 1:
            oneway = {'start': end, 'end': start, 'length': length, 'roadid': roadid, 'channel': channel}
            topologyDict[end].append(oneway)
    return topologyDict


# 创建图模型
def createGraph(topologyDict):
    graph = Graph()
    # topologyDict为
    for key, value in topologyDict.items():
        # value 为 list
        for item in value:
            graph.add_edge(item['start'], item['end'], item['weight'])

    return graph


# 个人理解，Graph应交由调度中心进行管理，管理他的weight,这样繁忙的时候加大他的weight,避免别人走这条路
class Graph():
    def __init__(self):
        """
         self.edges is a dict of all possible next nodes
         e.g. {'X': ['A', 'B', 'C', 'E'], ...}
         self.weights has all the weights between two nodes,
         with the two nodes as a tuple as the key
         e.g. {('X', 'A'): 7, ('X', 'B'): 2, ...}
         """
        self.edges = defaultdict(list)
        self.weights = {}

    def add_edge(self, from_node, to_node, weight):
        # 源作假设所有路径为双向，此处我改为单向
        # # Note: assumes edges are bi-directional
        # self.edges[from_node].append(to_node)
        # self.edges[to_node].append(from_node)
        # self.weights[(from_node, to_node)] = weight
        # self.weights[(to_node, from_node)] = weight

        # 注意本应用中，来去道路不同，应视为不同的边和不用的权重
        self.edges[from_node].append(to_node)
        self.weights[(from_node,to_node)] = weight


#
def dijsktra(graph, initial, end):
    # shortest paths is a dict of nodes
    # whose value is a tuple of (previous node, weight)

    shortest_paths = {initial: (None, 0)}
    current_node = initial
    visited = set()

    while current_node != end:
        visited.add(current_node)
        destinations = graph.edges[current_node]
        weight_to_current_node = shortest_paths[current_node][1]

        for next_node in destinations:
            weight = graph.weights[(current_node, next_node)] + weight_to_current_node
            if next_node not in shortest_paths:
                shortest_paths[next_node] = (current_node, weight)
            else:
                current_shortest_weight = shortest_paths[next_node][1]
                if current_shortest_weight > weight:
                    shortest_paths[next_node] = (current_node, weight)

        next_destinations = {node: shortest_paths[node] for node in shortest_paths if node not in visited}

        if not next_destinations:
            return "Route Not Possible"
        # next node is the destination with the lowest weight
        current_node = min(next_destinations, key=lambda k: next_destinations[k][1])

    # Work back through destinations in shortest path
    path = []
    while current_node is not None:
        path.append(current_node)
        next_node = shortest_paths[current_node][0]
        current_node = next_node
    # Reverse path
    path = path[::-1]
    return path



# def unitTest():
#     graph = Graph()
#
#     edges = [
#         ('X', 'A', 7),
#         ('X', 'B', 2),
#         ('X', 'C', 3),
#         ('X', 'E', 4),
#         ('A', 'B', 3),
#         ('A', 'D', 4),
#         ('B', 'D', 4),
#         ('B', 'H', 5),
#         ('C', 'L', 2),
#         ('D', 'F', 1),
#         ('F', 'H', 3),
#         ('G', 'H', 2),
#         ('G', 'Y', 2),
#         ('I', 'J', 6),
#         ('I', 'K', 4),
#         ('I', 'L', 4),
#         ('J', 'L', 1),
#         ('K', 'Y', 5),
#     ]
#
#     for edge in edges:
#         graph.add_edge(*edge)