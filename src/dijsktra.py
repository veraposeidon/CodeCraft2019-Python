# coding: utf-8
import sys
from collections import defaultdict
from collections import defaultdict
from heapq import *

WEIGHT_MAX = 10000


def create_topology(roads_dict):
    """
    从道路信息，构建拓扑信息
    :param roads_dict:
    :return:
    """
    topology_dict = defaultdict(lambda: [])

    for item in roads_dict.values():
        # 正向
        start = item['from']
        end = item['to']
        length = item['length']
        road_id = item['id']
        channel = item['channel']
        way = {'start': start, 'end': end, 'length': length, 'road_id': road_id, 'channel': channel}
        topology_dict[start].append(way)

        # 反向
        if item['isDuplex'] == 1:
            way = {'start': end, 'end': start, 'length': length, 'road_id': road_id, 'channel': channel}
            topology_dict[end].append(way)
    return topology_dict


def create_graph(topology_dict):
    """
    从拓扑数据生成有向图
    :param topology_dict:
    :return:
    """
    graph = Graph()

    for key, value in topology_dict.items():
        for item in value:
            graph.add_edge(item['start'], item['end'], item['weight'])
    graph.reconstruct_graph_for_heapq()
    return graph


class Graph:
    """
    有向图， 邻接矩阵
    """

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
        self.heapq = defaultdict(list)

    def add_edge(self, from_node, to_node, weight):
        self.edges[from_node].append(to_node)
        self.weights[(from_node, to_node)] = weight

    def reconstruct_graph_for_heapq(self):
        self.heapq = defaultdict(list)
        for edge_from in self.edges.keys():
            for edge_to in self.edges[edge_from]:
                weight = self.weights[(edge_from, edge_to)]
                self.heapq[edge_from].append((weight, edge_to))

    def update_weight(self, src, end, weight):
        # 更新weight列表
        self.weights[(src, end)] = weight
        # 更新heapq
        for i in range(len(self.heapq[src])):
            if self.heapq[src][i][1] == end:
                self.heapq[src][i] = (weight, end)


def dijsktra(graph, initial, end):
    """
    dijsktra 最短路径搜索
    直接实现。时间复杂度：O(n²)
    致谢： http://benalexkeen.com/implementing-djikstras-shortest-path-algorithm-with-python/
    :param graph:
    :param initial:
    :param end:
    :return:    shortest paths is a dict of nodes whose value is a tuple of (previous node, weight)
    """
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

        # # 遍历找最小可能会稍快。
        # current_node = list(next_destinations.keys())[0]
        # for key in next_destinations.keys():
        #     if next_destinations[key][1] < next_destinations[current_node][1]:
        #         current_node = key

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

def dijsktra_faster(graph, initial, end):
    """
    菲波那契堆实现， 使用Fibonacci Heap将复杂度降到O(E+VlogV)
    致谢：https://gist.github.com/kachayev/5990802
    :param graph:
    :param initial:
    :param end:
    :return:
    """
    # return dijsktra(graph, initial, end)  # 取消注释进行对比

    result = dijsktra_heapq(graph, initial, end)

    # 需要递归
    total_length = result[0]  # 整条路线代价
    result = result[1]
    route = []
    while result:
        route.append(result[0])
        result = result[1]
    route.reverse()

    return route


def dijsktra_heapq(graph, initial, end):
    g = graph.heapq

    q, seen, mins = [(0, initial, ())], set(), {initial: 0}

    while q:
        (cost, v1, path) = heappop(q)
        if v1 not in seen:
            seen.add(v1)
            path = (v1, path)
            if v1 == end: return (cost, path)

            for c, v2 in g.get(v1, ()):
                if v2 in seen: continue
                prev = mins.get(v2, None)
                next = cost + c
                if prev is None or next < prev:
                    mins[v2] = next
                    heappush(q, (next, v2, path))

    return float("inf")
