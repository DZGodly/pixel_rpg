"""地图数据与生成 - 赛博朋克主题"""

import math
import random
from typing import Dict, List, Tuple

AREA_VILLAGE = 'village'        # 数据港（初始安全区）
AREA_FOREST = 'forest'          # 废墟荒地
AREA_DUNGEON = 'dungeon'        # 旧数据中心
AREA_NEON_STREET = 'neon_street' # 霓虹商业街（上方，安全区）
AREA_FACTORY = 'factory'         # 废弃工厂（下方，中等难度）
AREA_CYBERSPACE = 'cyberspace'   # 网络空间（左方，高难度）
AREA_TUNNEL = 'tunnel'           # 地下通道（工厂→旧数据中心）
AREA_BLACK_MARKET = 'black_market'  # 黑市（霓虹街隐藏入口）

# 室内区域
AREA_HOUSE_V1 = 'house_v1'      # 数据港-房屋1
AREA_HOUSE_V2 = 'house_v2'      # 数据港-房屋2
AREA_HOUSE_V3 = 'house_v3'      # 数据港-房屋3
AREA_HOUSE_N1 = 'house_n1'      # 霓虹街-房屋1
AREA_HOUSE_N2 = 'house_n2'      # 霓虹街-房屋2
AREA_HOUSE_N3 = 'house_n3'      # 霓虹街-房屋3

INDOOR_AREAS = {AREA_HOUSE_V1, AREA_HOUSE_V2, AREA_HOUSE_V3,
                AREA_HOUSE_N1, AREA_HOUSE_N2, AREA_HOUSE_N3,
                AREA_BLACK_MARKET}

# 图块类型: 0=金属地板, 1=霓虹步道, 2=数据流, 3=金属墙, 4=信号塔, 5=电路板地板, 6=霓虹灯, 7=传送门
#           8=工厂地板, 9=网络地板, 10=霓虹地砖
#           11=室内地板, 12=室内墙, 13=桌子, 14=终端机
#           15=书架, 16=沙发, 17=地毯, 18=吧台
#           19=管道地板, 20=锈蚀墙


class GameMap:
    def __init__(self):
        self.maps: Dict[str, List[List[int]]] = {}
        self.map_w: Dict[str, int] = {}
        self.map_h: Dict[str, int] = {}
        self.transitions: Dict[str, List[Tuple]] = {}
        self._generate_maps()

    def _generate_maps(self):
        self._gen_village()
        self._gen_forest()
        self._gen_dungeon()
        self._gen_neon_street()
        self._gen_factory()
        self._gen_cyberspace()
        self._gen_houses()
        self._gen_tunnel()
        self._gen_black_market()

    def _gen_village(self):
        """数据港 - 初始安全区"""
        W, H = 40, 30
        m = [[0]*W for _ in range(H)]
        # 主干道（霓虹步道）
        for x in range(W):
            m[14][x] = 1
            m[15][x] = 1
        for y in range(H):
            m[y][20] = 1
            m[y][21] = 1
        # 数据池（中央广场）
        for y in range(8, 12):
            for x in range(5, 10):
                m[y][x] = 2
        # 霓虹灯装饰
        for _ in range(20):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 0:
                m[fy][fx] = 6
        # 房屋占地（3x3，门口留空）
        for hx, hy in [(12, 6), (26, 8), (30, 18)]:
            for dy in range(3):
                for dx in range(3):
                    m[hy + dy][hx + dx] = 3  # 墙
            m[hy + 2][hx + 1] = 7  # 门口 = 传送门
        # 信号塔边界
        for x in range(W):
            if m[0][x] == 0: m[0][x] = 4
            if m[H-1][x] == 0: m[H-1][x] = 4
        for y in range(H):
            if m[y][0] == 0: m[y][0] = 4
            if m[y][W-1] == 0: m[y][W-1] = 4

        # 右出口 → 废墟荒地
        m[14][W-1] = 1
        m[15][W-1] = 1
        # 上出口 → 霓虹商业街
        m[0][20] = 1
        m[0][21] = 1
        # 下出口 → 废弃工厂
        m[H-1][20] = 1
        m[H-1][21] = 1
        # 左出口 → 网络空间
        m[14][0] = 1
        m[15][0] = 1

        self.maps[AREA_VILLAGE] = m
        self.map_w[AREA_VILLAGE] = W
        self.map_h[AREA_VILLAGE] = H
        self.transitions[AREA_VILLAGE] = [
            (W-1, 14, AREA_FOREST, 1, 14),
            (W-1, 15, AREA_FOREST, 1, 15),
            (20, 0, AREA_NEON_STREET, 20, 28),
            (21, 0, AREA_NEON_STREET, 21, 28),
            (20, H-1, AREA_FACTORY, 20, 1),
            (21, H-1, AREA_FACTORY, 21, 1),
            (0, 14, AREA_CYBERSPACE, 38, 20),
            (0, 15, AREA_CYBERSPACE, 38, 21),
            # 进入房屋（门口坐标 = hx+1, hy+2）
            (13, 8, AREA_HOUSE_V1, 15, 18),
            (27, 10, AREA_HOUSE_V2, 15, 18),
            (31, 20, AREA_HOUSE_V3, 15, 18),
        ]

    def _gen_forest(self):
        """废墟荒地"""
        W, H = 50, 40
        m = [[0]*W for _ in range(H)]
        # 废墟残骸（信号塔/建筑残骸）
        for _ in range(200):
            tx, ty = random.randint(0, W-1), random.randint(0, H-1)
            m[ty][tx] = 4
        # 主路
        for x in range(W):
            for dy in [14, 15]:
                if dy < H:
                    m[dy][x] = 1
        for y in range(H):
            m[y][25] = 1
        # 入口区域清理
        for y in range(12, 18):
            for x in range(0, 4):
                m[y][x] = 0
        # 数据泄漏流
        for y in range(5, 35):
            wx = 35 + int(math.sin(y * 0.3) * 3)
            for dx in range(3):
                if 0 <= wx+dx < W:
                    m[y][wx+dx] = 2
        # 霓虹灯残留
        for _ in range(15):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 0:
                m[fy][fx] = 6
        # 旧数据中心入口
        m[25][25] = 7
        # 回数据港
        m[14][0] = 1
        m[15][0] = 1
        self.maps[AREA_FOREST] = m
        self.map_w[AREA_FOREST] = W
        self.map_h[AREA_FOREST] = H
        self.transitions[AREA_FOREST] = [
            (0, 14, AREA_VILLAGE, 38, 14),
            (0, 15, AREA_VILLAGE, 38, 15),
            (25, 25, AREA_DUNGEON, 5, 1),
        ]

    def _gen_dungeon(self):
        """旧数据中心"""
        W, H = 30, 25
        m = [[3]*W for _ in range(H)]
        rooms = [(2, 2, 10, 8), (14, 2, 10, 8), (2, 14, 10, 8), (14, 14, 14, 9)]
        for rx, ry, rw, rh in rooms:
            for y in range(ry, ry+rh):
                for x in range(rx, rx+rw):
                    if 0 <= x < W and 0 <= y < H:
                        m[y][x] = 5
        # 走廊
        for x in range(10, 16):
            m[6][x] = 5
            m[7][x] = 5
        for y in range(8, 16):
            m[y][6] = 5
            m[y][7] = 5
        for y in range(8, 16):
            m[y][18] = 5
            m[y][19] = 5
        for x in range(10, 16):
            m[18][x] = 5
            m[19][x] = 5
        # 出口
        m[1][5] = 7
        self.maps[AREA_DUNGEON] = m
        self.map_w[AREA_DUNGEON] = W
        self.map_h[AREA_DUNGEON] = H
        self.transitions[AREA_DUNGEON] = [
            (5, 1, AREA_FOREST, 25, 24),
        ]

    def _gen_neon_street(self):
        """霓虹商业街 - 安全区，商店多"""
        W, H = 45, 30
        m = [[10]*W for _ in range(H)]  # 霓虹地砖为主
        # 主街道
        for x in range(W):
            m[14][x] = 1
            m[15][x] = 1
        for y in range(H):
            m[y][20] = 1
            m[y][21] = 1
        # 商店建筑区（金属墙围成的区域）
        for bx, by, bw, bh in [(3, 3, 8, 6), (14, 3, 8, 6), (30, 3, 10, 6),
                                 (3, 20, 8, 6), (14, 20, 8, 6), (30, 20, 10, 6)]:
            for y in range(by, by+bh):
                for x in range(bx, bx+bw):
                    if 0 <= x < W and 0 <= y < H:
                        if y == by or y == by+bh-1 or x == bx or x == bx+bw-1:
                            m[y][x] = 3  # 墙
                        else:
                            m[y][x] = 10  # 内部地砖
        # 数据喷泉（中央）
        for y in range(12, 18):
            for x in range(18, 24):
                if not (x in [20, 21] and y in [14, 15]):
                    m[y][x] = 2
        # 霓虹灯装饰
        for _ in range(30):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 10:
                m[fy][fx] = 6
        # 房屋占地（3x3，门口留空）
        for hx, hy in [(12, 6), (26, 8), (30, 18)]:
            for dy in range(3):
                for dx in range(3):
                    if 0 <= hy+dy < H and 0 <= hx+dx < W:
                        m[hy + dy][hx + dx] = 3
            m[hy + 2][hx + 1] = 7  # 门口
        # 边界信号塔
        for x in range(W):
            if m[0][x] not in (1, 7): m[0][x] = 4
            if m[H-1][x] not in (1, 7): m[H-1][x] = 4
        for y in range(H):
            if m[y][0] not in (1, 7): m[y][0] = 4
            if m[y][W-1] not in (1, 7): m[y][W-1] = 4
        # 下出口 → 数据港
        m[H-1][20] = 1
        m[H-1][21] = 1
        self.maps[AREA_NEON_STREET] = m
        self.map_w[AREA_NEON_STREET] = W
        self.map_h[AREA_NEON_STREET] = H
        self.transitions[AREA_NEON_STREET] = [
            (20, H-1, AREA_VILLAGE, 20, 1),
            (21, H-1, AREA_VILLAGE, 21, 1),
            # 进入房屋
            (13, 8, AREA_HOUSE_N1, 15, 18),
            (27, 10, AREA_HOUSE_N2, 15, 18),
            (31, 20, AREA_HOUSE_N3, 15, 18),
        ]

    def _gen_factory(self):
        """废弃工厂 - 中等难度"""
        W, H = 45, 35
        m = [[8]*W for _ in range(H)]  # 工厂地板
        # 传送带通道
        for x in range(W):
            m[10][x] = 1
            m[11][x] = 1
            m[24][x] = 1
            m[25][x] = 1
        for y in range(H):
            m[y][20] = 1
            m[y][21] = 1
        # 机械区（金属墙围成）
        for bx, by, bw, bh in [(3, 3, 12, 6), (28, 3, 14, 6),
                                 (3, 28, 12, 5), (28, 28, 14, 5)]:
            for y in range(by, by+bh):
                for x in range(bx, bx+bw):
                    if 0 <= x < W and 0 <= y < H:
                        if y == by or y == by+bh-1 or x == bx or x == bx+bw-1:
                            m[y][x] = 3
                        else:
                            m[y][x] = 8
        # 危险数据泄漏
        for y in range(14, 22):
            for x in range(8, 12):
                m[y][x] = 2
        for y in range(14, 22):
            for x in range(33, 37):
                m[y][x] = 2
        # 边界
        for x in range(W):
            if m[0][x] not in (1, 7): m[0][x] = 3
            if m[H-1][x] not in (1, 7): m[H-1][x] = 3
        for y in range(H):
            if m[y][0] not in (1, 7): m[y][0] = 3
            if m[y][W-1] not in (1, 7): m[y][W-1] = 3
        # 上出口 → 数据港
        m[0][20] = 1
        m[0][21] = 1
        self.maps[AREA_FACTORY] = m
        self.map_w[AREA_FACTORY] = W
        self.map_h[AREA_FACTORY] = H
        self.transitions[AREA_FACTORY] = [
            (20, 0, AREA_VILLAGE, 20, 28),
            (21, 0, AREA_VILLAGE, 21, 28),
        ]

    def _gen_cyberspace(self):
        """网络空间 - 高难度，最终boss"""
        W, H = 40, 40
        m = [[9]*W for _ in range(H)]  # 网络地板
        # 数据高速路
        for x in range(W):
            m[20][x] = 1
            m[21][x] = 1
        for y in range(H):
            m[y][20] = 1
            m[y][21] = 1
        # 数据节点房间
        rooms = [(3, 3, 10, 8), (27, 3, 10, 8),
                 (3, 29, 10, 8), (27, 29, 10, 8),
                 (15, 15, 10, 10)]  # 中央boss房
        for rx, ry, rw, rh in rooms:
            for y in range(ry, ry+rh):
                for x in range(rx, rx+rw):
                    if 0 <= x < W and 0 <= y < H:
                        m[y][x] = 9
            # 房间边框用数据流
            for x in range(rx, rx+rw):
                if 0 <= rx < W and 0 <= ry < H:
                    m[ry][x] = 2
                if 0 <= rx < W and 0 <= ry+rh-1 < H:
                    m[ry+rh-1][x] = 2
            for y in range(ry, ry+rh):
                if 0 <= rx < W:
                    m[y][rx] = 2
                if 0 <= rx+rw-1 < W:
                    m[y][rx+rw-1] = 2
        # 走廊连接
        for x in range(12, 16):
            m[7][x] = 9
            m[8][x] = 9
        for x in range(24, 28):
            m[7][x] = 9
            m[8][x] = 9
        for x in range(12, 16):
            m[33][x] = 9
            m[34][x] = 9
        for x in range(24, 28):
            m[33][x] = 9
            m[34][x] = 9
        # 霓虹灯
        for _ in range(20):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 9:
                m[fy][fx] = 6
        # 边界
        for x in range(W):
            if m[0][x] not in (1, 7): m[0][x] = 3
            if m[H-1][x] not in (1, 7): m[H-1][x] = 3
        for y in range(H):
            if m[y][0] not in (1, 7): m[y][0] = 3
            if m[y][W-1] not in (1, 7): m[y][W-1] = 3
        # 右出口 → 数据港
        m[20][W-1] = 1
        m[21][W-1] = 1
        self.maps[AREA_CYBERSPACE] = m
        self.map_w[AREA_CYBERSPACE] = W
        self.map_h[AREA_CYBERSPACE] = H
        self.transitions[AREA_CYBERSPACE] = [
            (W-1, 20, AREA_VILLAGE, 1, 14),
            (W-1, 21, AREA_VILLAGE, 1, 15),
        ]

    def _gen_houses(self):
        """生成所有室内地图 (30x20, 铺满屏幕)"""
        # (室内区域, 外部区域, 门口外部坐标)
        house_defs = [
            (AREA_HOUSE_V1, AREA_VILLAGE, 13, 9),
            (AREA_HOUSE_V2, AREA_VILLAGE, 27, 11),
            (AREA_HOUSE_V3, AREA_VILLAGE, 31, 21),
            (AREA_HOUSE_N1, AREA_NEON_STREET, 13, 9),
            (AREA_HOUSE_N2, AREA_NEON_STREET, 27, 11),
            (AREA_HOUSE_N3, AREA_NEON_STREET, 31, 21),
        ]
        W, H = 30, 20
        for i, (area_name, outer_area, door_x, door_y) in enumerate(house_defs):
            m = [[11]*W for _ in range(H)]
            # 外墙
            for x in range(W):
                m[0][x] = 12
                m[H-1][x] = 12
            for y in range(H):
                m[y][0] = 12
                m[y][W-1] = 12
            # 门口
            m[H-1][15] = 11
            m[H-1][14] = 11
            # 每个房子独特布局
            if i == 0:  # V1: 维修工坊 — 大量工作台和终端
                # 左侧工作区
                for x in range(2, 8):
                    m[2][x] = 13  # 工作台
                for x in range(2, 5):
                    m[5][x] = 14  # 终端
                # 右侧存储区
                for y in range(2, 8):
                    m[y][W-2] = 15  # 书架
                for x in range(20, 26):
                    m[2][x] = 13
                # 中间隔墙
                for y in range(2, 10):
                    m[y][14] = 12
                m[5][14] = 11  # 隔墙通道
                # 右侧休息区
                for x in range(16, 20):
                    m[12][x] = 16  # 沙发
                # 地毯
                for y in range(10, 16):
                    for x in range(4, 12):
                        if m[y][x] == 11:
                            m[y][x] = 17
                # 霓虹灯
                for x in [4, 10, 18, 24]:
                    m[1][x] = 6
            elif i == 1:  # V2: 数据分析室 — 终端阵列
                # 终端阵列（左侧）
                for y in range(3, 12, 3):
                    for x in range(2, 6):
                        m[y][x] = 14
                # 中央大桌
                for y in range(6, 10):
                    for x in range(10, 20):
                        m[y][x] = 13
                # 右侧书架墙
                for y in range(2, 16):
                    m[y][W-2] = 15
                # 上方沙发
                for x in range(10, 16):
                    m[2][x] = 16
                # 地毯
                for y in range(12, 18):
                    for x in range(10, 20):
                        if m[y][x] == 11:
                            m[y][x] = 17
                # 霓虹灯
                for x in [3, 9, 15, 22]:
                    m[1][x] = 6
            elif i == 2:  # V3: 退休黑客的书房 — 书架环绕
                # 书架环绕
                for x in range(2, W-2):
                    m[2][x] = 15
                for y in range(3, 14):
                    m[y][1] = 15
                    m[y][W-2] = 15
                # 中央阅读区
                for y in range(7, 11):
                    for x in range(10, 20):
                        m[y][x] = 17  # 地毯
                m[8][12] = 13  # 桌
                m[8][13] = 13
                m[8][16] = 13
                m[8][17] = 13
                # 终端角落
                m[4][3] = 14
                m[4][4] = 14
                m[4][W-4] = 14
                m[4][W-3] = 14
                # 沙发
                for x in range(10, 14):
                    m[6][x] = 16
                for x in range(16, 20):
                    m[6][x] = 16
                # 霓虹灯
                for x in [6, 14, 22]:
                    m[1][x] = 6
            elif i == 3:  # N1: 酒吧 — 吧台+卡座
                # 长吧台
                for x in range(3, 16):
                    m[5][x] = 18
                # 吧台后面的酒架
                for x in range(3, 16):
                    m[3][x] = 15
                # 卡座区（右侧）
                for y in range(4, 16, 4):
                    m[y][20] = 13
                    m[y][21] = 13
                    m[y-1][19] = 16
                    m[y-1][22] = 16
                # 舞池地毯
                for y in range(10, 17):
                    for x in range(4, 14):
                        if m[y][x] == 11:
                            m[y][x] = 17
                # 霓虹灯（酒吧多一些）
                for x in [3, 7, 11, 15, 20, 25]:
                    m[1][x] = 6
            elif i == 4:  # N2: 改装店 — 展示柜+工作台
                # 展示柜（上方）
                for x in range(2, 12):
                    m[2][x] = 15
                for x in range(18, W-2):
                    m[2][x] = 15
                # 中央工作台
                for y in range(7, 11):
                    for x in range(8, 14):
                        m[y][x] = 13
                # 终端区
                for y in range(7, 11):
                    m[y][W-3] = 14
                # 左侧沙发等候区
                for x in range(2, 6):
                    m[14][x] = 16
                for x in range(2, 6):
                    m[16][x] = 16
                m[15][2] = 13  # 茶几
                # 地毯
                for y in range(13, 18):
                    for x in range(2, 7):
                        if m[y][x] == 11:
                            m[y][x] = 17
                # 霓虹灯
                for x in [4, 10, 16, 24]:
                    m[1][x] = 6
            elif i == 5:  # N3: 线人密室 — 暗室风格
                # 隔间（多个小房间）
                for y in range(2, 10):
                    m[y][10] = 12
                m[5][10] = 11  # 通道
                for y in range(2, 10):
                    m[y][20] = 12
                m[5][20] = 11  # 通道
                # 左隔间：终端
                for x in range(2, 5):
                    m[3][x] = 14
                m[6][3] = 16
                # 中隔间：会议桌
                for x in range(12, 18):
                    m[4][x] = 13
                for x in range(12, 18):
                    m[6][x] = 16
                # 右隔间：书架+终端
                for y in range(2, 9):
                    m[y][W-2] = 15
                m[4][22] = 14
                m[4][23] = 14
                # 下方开放区
                for y in range(12, 17):
                    for x in range(8, 22):
                        if m[y][x] == 11:
                            m[y][x] = 17
                m[14][10] = 13
                m[14][11] = 13
                m[14][18] = 13
                m[14][19] = 13
                # 霓虹灯
                for x in [5, 15, 25]:
                    m[1][x] = 6

            self.maps[area_name] = m
            self.map_w[area_name] = W
            self.map_h[area_name] = H
            self.transitions[area_name] = [
                (14, H-1, outer_area, door_x, door_y),
                (15, H-1, outer_area, door_x, door_y),
            ]

    def _gen_tunnel(self):
        """地下通道 - 连接工厂→旧数据中心"""
        W, H = 35, 25
        m = [[20]*W for _ in range(H)]  # 锈蚀墙填充
        # 主通道 - 蜿蜒走廊
        cx, cy = 2, 12
        for x in range(2, W - 2):
            # 蜿蜒
            cy += random.choice([-1, 0, 0, 1])
            cy = max(3, min(H - 4, cy))
            for dy in range(-1, 2):
                if 0 <= cy + dy < H:
                    m[cy + dy][x] = 19  # 管道地板
        # 入口区域（左侧，从工厂来）
        for y in range(10, 15):
            for x in range(0, 4):
                m[y][x] = 19
        m[12][0] = 7  # 传送门回工厂
        # 出口区域（右侧，到旧数据中心）
        for y in range(10, 15):
            for x in range(W - 4, W):
                m[y][x] = 19
        m[12][W - 1] = 7  # 传送门到地牢
        # 岔路房间
        rooms = [(8, 4, 6, 5), (18, 16, 7, 5), (26, 6, 5, 4)]
        for rx, ry, rw, rh in rooms:
            for dy in range(rh):
                for dx in range(rw):
                    if 0 <= ry + dy < H and 0 <= rx + dx < W:
                        m[ry + dy][rx + dx] = 19
        self.maps[AREA_TUNNEL] = m
        self.map_w[AREA_TUNNEL] = W
        self.map_h[AREA_TUNNEL] = H
        self.transitions[AREA_TUNNEL] = [
            (0, 12, AREA_FACTORY, 38, 15),
            (W - 1, 12, AREA_DUNGEON, 1, 15),
        ]
        # 工厂侧添加到地下通道的传送点
        if AREA_FACTORY in self.transitions:
            self.transitions[AREA_FACTORY].append((38, 15, AREA_TUNNEL, 1, 12))
        # 地牢侧添加到地下通道的传送点
        if AREA_DUNGEON in self.transitions:
            self.transitions[AREA_DUNGEON].append((1, 15, AREA_TUNNEL, W - 2, 12))

    def _gen_black_market(self):
        """黑市 - 从霓虹街隐藏入口进入"""
        W, H = 25, 20
        m = [[12]*W for _ in range(H)]  # 室内墙填充
        # 主区域
        for y in range(2, H - 2):
            for x in range(2, W - 2):
                m[y][x] = 11  # 室内地板
        # 摊位区域（用桌子和吧台）
        for x in range(5, 10):
            m[5][x] = 18  # 吧台 - 军火商摊位
        for x in range(15, 20):
            m[5][x] = 13  # 桌子 - 信息贩子摊位
        # 中央地毯
        for y in range(8, 14):
            for x in range(8, 17):
                if m[y][x] == 11:
                    m[y][x] = 17
        # 装饰
        for x in [3, 12, 21]:
            if m[3][x] == 11:
                m[3][x] = 6  # 霓虹灯
        # 出口（底部回霓虹街）
        m[H - 1][12] = 7
        m[H - 1][13] = 7
        self.maps[AREA_BLACK_MARKET] = m
        self.map_w[AREA_BLACK_MARKET] = W
        self.map_h[AREA_BLACK_MARKET] = H
        self.transitions[AREA_BLACK_MARKET] = [
            (12, H - 1, AREA_NEON_STREET, 20, 5),
            (13, H - 1, AREA_NEON_STREET, 21, 5),
        ]
        # 霓虹街添加到黑市的隐藏入口
        if AREA_NEON_STREET in self.transitions:
            self.transitions[AREA_NEON_STREET].append((20, 4, AREA_BLACK_MARKET, 12, H - 2))

    def get_tile(self, area, x, y):
        m = self.maps.get(area)
        if m and 0 <= y < len(m) and 0 <= x < len(m[0]):
            return m[y][x]
        return 3  # 墙

    def is_walkable(self, area, x, y):
        t = self.get_tile(area, x, y)
        return t in (0, 1, 5, 6, 7, 8, 9, 10, 11, 17, 19)

    def check_transition(self, area, tx, ty):
        for t in self.transitions.get(area, []):
            if t[0] == tx and t[1] == ty:
                return t[2], t[3], t[4]
        return None
