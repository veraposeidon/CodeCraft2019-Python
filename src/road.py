# coding:utf-8
# import numpy as np

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

    # -1 表示没车， 否则为车号
    # 关于表示道路的矩阵，车道号从小到大排，道路位置从小到大是以从道路起点到道路终点
    def initializeRoad(self):
        channel = self.roadChannel
        length = self.roadLength
        # roadDetail = np.array((channel, length))
        roadDetail = None
        return roadDetail


