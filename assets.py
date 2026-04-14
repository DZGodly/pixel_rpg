"""程序化素材生成 - 赛博朋克像素风"""

import random
import pygame
from constants import TILE


class Assets:
    def __init__(self):
        self.font_sm = pygame.font.SysFont("PingFang SC,Hiragino Sans GB,Microsoft YaHei,SimHei,Arial", 14)
        self.font_md = pygame.font.SysFont("PingFang SC,Hiragino Sans GB,Microsoft YaHei,SimHei,Arial", 18)
        self.font_lg = pygame.font.SysFont("PingFang SC,Hiragino Sans GB,Microsoft YaHei,SimHei,Arial", 26)
        self.font_title = pygame.font.SysFont("PingFang SC,Hiragino Sans GB,Microsoft YaHei,SimHei,Arial", 36)
        self.tiles = {}
        self.player_frames = {}
        self.npc_sprites = {}
        self.enemy_sprites = {}
        self.item_icons = {}
        self._generate_all()

    def _generate_all(self):
        self._gen_tiles()
        self._gen_player()
        self._gen_npcs()
        self._gen_enemies()
        self._gen_items()

    def _gen_tiles(self):
        # --- grass: 暗金属地板 + 电路点 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((30, 35, 45))
        for _ in range(15):
            px, py = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
            c = random.choice([(0, 255, 200, 40), (40, 45, 55), (25, 30, 40)])
            s.set_at((px, py), c[:3])
        # 电路线
        for y in range(0, TILE, 8):
            pygame.draw.line(s, (40, 50, 60), (0, y), (TILE, y))
        for x in range(0, TILE, 8):
            pygame.draw.line(s, (40, 50, 60), (x, 0), (x, TILE))
        # 电路节点
        for _ in range(3):
            nx, ny = random.randint(2, TILE - 3), random.randint(2, TILE - 3)
            pygame.draw.rect(s, (0, 180, 150), (nx, ny, 2, 2))
        self.tiles['grass'] = s

        # --- grass2: 金属地板变体 + LED 点 ---
        s2 = pygame.Surface((TILE, TILE))
        s2.fill((35, 38, 48))
        for _ in range(10):
            px, py = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
            s2.set_at((px, py), random.choice([(45, 50, 60), (30, 33, 43)]))
        for _ in range(4):
            lx, ly = random.randint(2, TILE - 3), random.randint(2, TILE - 3)
            c = random.choice([(0, 255, 200), (255, 50, 150), (0, 255, 100)])
            pygame.draw.rect(s2, c, (lx, ly, 1, 1))
        self.tiles['grass2'] = s2

        # --- path: 霓虹步道 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((40, 40, 60))
        # 青色/紫色发光线
        pygame.draw.line(s, (0, 200, 180), (0, 0), (TILE, 0))
        pygame.draw.line(s, (0, 200, 180), (0, TILE - 1), (TILE, TILE - 1))
        pygame.draw.line(s, (140, 50, 200), (0, TILE // 2), (TILE, TILE // 2))
        for _ in range(6):
            px, py = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
            s.set_at((px, py), (50, 50, 70))
        self.tiles['path'] = s

        # --- water_*: 数据流 (动画, 青/紫流动) ---
        for frame in range(4):
            s = pygame.Surface((TILE, TILE))
            s.fill((8, 12, 30))
            offset = frame * 4
            for y in range(0, TILE, 4):
                shifted_y = (y + offset) % TILE
                c = (0, 180 + random.randint(0, 40), 200) if y % 8 == 0 else (120, 40, 200)
                pygame.draw.line(s, c, (0, shifted_y), (TILE, shifted_y))
            # 流动数据点
            for _ in range(8):
                dx = random.randint(0, TILE - 1)
                dy = (random.randint(0, TILE - 1) + frame * 6) % TILE
                s.set_at((dx, dy), (0, 255, 220))
            # 偶尔的亮点
            for _ in range(3):
                bx, by = random.randint(0, TILE - 2), random.randint(0, TILE - 2)
                pygame.draw.rect(s, (180, 60, 255), (bx, by, 2, 1))
            self.tiles[f'water_{frame}'] = s

        # --- wall: 金属墙 + 铆钉 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((50, 55, 65))
        # 金属板块
        for bx in range(0, TILE, 8):
            for by in range(0, TILE, 8):
                c = random.choice([(48, 53, 63), (55, 60, 70), (45, 50, 60)])
                pygame.draw.rect(s, c, (bx, by, 7, 7))
                pygame.draw.rect(s, (35, 40, 50), (bx, by, 8, 8), 1)
        # 铆钉
        for rx, ry in [(3, 3), (TILE - 4, 3), (3, TILE - 4), (TILE - 4, TILE - 4)]:
            pygame.draw.rect(s, (100, 110, 130), (rx, ry, 2, 2))
            pygame.draw.rect(s, (70, 75, 85), (rx + 1, ry + 1, 1, 1))
        self.tiles['wall'] = s

        # --- dungeon_floor: 电路板地板 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((20, 25, 40))
        # 电路走线
        for _ in range(4):
            sx = random.randint(0, TILE - 1)
            sy = random.randint(0, TILE - 1)
            ex = random.randint(0, TILE - 1)
            pygame.draw.line(s, (0, 120, 100), (sx, sy), (ex, sy))
            pygame.draw.line(s, (0, 120, 100), (ex, sy), (ex, random.randint(0, TILE - 1)))
        # 芯片节点
        for _ in range(3):
            cx, cy = random.randint(4, TILE - 6), random.randint(4, TILE - 6)
            pygame.draw.rect(s, (0, 180, 140), (cx, cy, 3, 3))
            pygame.draw.rect(s, (0, 100, 80), (cx, cy, 3, 3), 1)
        self.tiles['dungeon_floor'] = s

        # --- tree: 信号塔/天线 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # 金属杆
        pygame.draw.rect(s, (100, 110, 130), (14, 8, 4, 24))
        pygame.draw.rect(s, (80, 85, 95), (15, 8, 1, 24))
        # 横杆
        pygame.draw.rect(s, (90, 100, 120), (10, 14, 12, 2))
        pygame.draw.rect(s, (90, 100, 120), (12, 20, 8, 2))
        # 顶部闪烁灯
        pygame.draw.rect(s, (255, 40, 80), (14, 4, 4, 4))
        pygame.draw.rect(s, (255, 100, 120), (15, 5, 2, 2))
        # 底座
        pygame.draw.rect(s, (60, 65, 75), (10, 28, 12, 4))
        self.tiles['tree'] = s

        # --- flower: 霓虹灯具 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((30, 35, 45))
        neon_colors = [(0, 255, 200), (255, 50, 150), (180, 60, 255), (0, 255, 100)]
        for _ in range(5):
            fx, fy = random.randint(3, TILE - 4), random.randint(3, TILE - 4)
            c = random.choice(neon_colors)
            pygame.draw.rect(s, c, (fx, fy, 2, 2))
            # 发光效果
            glow = tuple(min(255, v // 3) for v in c)
            pygame.draw.rect(s, glow, (fx - 1, fy - 1, 4, 4), 1)
        self.tiles['flower'] = s

        # --- door: 全息传送门 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((30, 35, 45))
        # 发光青色框架
        pygame.draw.rect(s, (0, 255, 200), (6, 2, 20, 28), 2)
        pygame.draw.rect(s, (0, 180, 150), (8, 4, 16, 24), 1)
        # 内部全息效果
        for hy in range(6, 26, 2):
            alpha_c = (0, 100 + random.randint(0, 80), 120 + random.randint(0, 60))
            pygame.draw.line(s, alpha_c, (9, hy), (23, hy))
        # 顶部/底部发光
        pygame.draw.rect(s, (0, 255, 220), (8, 2, 16, 2))
        pygame.draw.rect(s, (0, 255, 220), (8, 28, 16, 2))
        self.tiles['door'] = s

        # --- chest: 数据终端 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # 终端机身
        pygame.draw.rect(s, (50, 55, 70), (6, 12, 20, 16))
        pygame.draw.rect(s, (70, 75, 90), (6, 12, 20, 16), 1)
        # 屏幕
        pygame.draw.rect(s, (0, 40, 60), (8, 14, 16, 8))
        # 屏幕内容 (闪烁数据)
        pygame.draw.rect(s, (0, 255, 200), (10, 16, 8, 1))
        pygame.draw.rect(s, (0, 200, 160), (10, 18, 5, 1))
        pygame.draw.rect(s, (0, 180, 140), (10, 20, 10, 1))
        # 指示灯
        pygame.draw.rect(s, (0, 255, 100), (10, 24, 2, 2))
        pygame.draw.rect(s, (255, 50, 50), (16, 24, 2, 2))
        self.tiles['chest'] = s

        # --- chest_open: 打开的数据终端 ---
        s2 = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s2, (50, 55, 70), (6, 12, 20, 16))
        pygame.draw.rect(s2, (70, 75, 90), (6, 12, 20, 16), 1)
        # 屏幕 - 全亮
        pygame.draw.rect(s2, (0, 80, 100), (8, 14, 16, 8))
        pygame.draw.rect(s2, (0, 255, 200), (9, 15, 14, 6))
        # 数据传输光束
        pygame.draw.line(s2, (0, 255, 200), (16, 12), (16, 6))
        pygame.draw.line(s2, (0, 200, 160), (14, 12), (12, 6))
        pygame.draw.line(s2, (0, 200, 160), (18, 12), (20, 6))
        # 指示灯全绿
        pygame.draw.rect(s2, (0, 255, 100), (10, 24, 2, 2))
        pygame.draw.rect(s2, (0, 255, 100), (16, 24, 2, 2))
        self.tiles['chest_open'] = s2

        # --- house: 霓虹建筑 (3x3) ---
        house = pygame.Surface((TILE * 3, TILE * 3), pygame.SRCALPHA)
        # 建筑主体
        pygame.draw.rect(house, (40, 45, 60), (8, 24, 80, 64))
        pygame.draw.rect(house, (55, 60, 75), (8, 24, 80, 64), 2)
        # 屋顶 - 金属
        pygame.draw.rect(house, (60, 65, 80), (4, 16, 88, 12))
        pygame.draw.rect(house, (80, 85, 100), (4, 16, 88, 12), 1)
        # 天线
        pygame.draw.rect(house, (100, 110, 130), (44, 4, 3, 14))
        pygame.draw.rect(house, (255, 40, 80), (43, 2, 5, 3))
        # 霓虹招牌
        pygame.draw.rect(house, (255, 50, 150), (20, 28, 56, 8))
        pygame.draw.rect(house, (200, 30, 120), (22, 30, 52, 4))
        # 门
        pygame.draw.rect(house, (0, 60, 80), (34, 60, 28, 28))
        pygame.draw.rect(house, (0, 255, 200), (34, 60, 28, 28), 2)
        # 窗户 - 发光
        pygame.draw.rect(house, (0, 60, 80), (14, 42, 16, 14))
        pygame.draw.rect(house, (0, 200, 180), (14, 42, 16, 14), 1)
        pygame.draw.rect(house, (0, 60, 80), (66, 42, 16, 14))
        pygame.draw.rect(house, (0, 200, 180), (66, 42, 16, 14), 1)
        # 窗户内光
        pygame.draw.rect(house, (0, 140, 120), (16, 44, 12, 10))
        pygame.draw.rect(house, (0, 140, 120), (68, 44, 12, 10))
        self.tiles['house'] = house

        # --- indoor_floor: 室内地板 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((35, 30, 50))
        for y in range(0, TILE, 8):
            pygame.draw.line(s, (45, 40, 60), (0, y), (TILE, y))
        for x in range(0, TILE, 8):
            pygame.draw.line(s, (45, 40, 60), (x, 0), (x, TILE))
        for _ in range(2):
            nx, ny = random.randint(2, TILE-3), random.randint(2, TILE-3)
            pygame.draw.rect(s, (60, 50, 80), (nx, ny, 2, 2))
        self.tiles['indoor_floor'] = s

        # --- indoor_wall: 室内墙壁 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((50, 45, 65))
        pygame.draw.rect(s, (60, 55, 75), (0, 0, TILE, TILE), 2)
        pygame.draw.line(s, (70, 65, 90), (0, TILE//2), (TILE, TILE//2))
        for x in range(4, TILE, 8):
            pygame.draw.rect(s, (80, 70, 100), (x, 2, 2, 2))
        self.tiles['indoor_wall'] = s

        # --- table: 桌子 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (80, 60, 40), (4, 8, 24, 16))
        pygame.draw.rect(s, (100, 80, 50), (4, 8, 24, 16), 2)
        pygame.draw.rect(s, (60, 45, 30), (6, 24, 4, 6))
        pygame.draw.rect(s, (60, 45, 30), (22, 24, 4, 6))
        # 桌上物品
        pygame.draw.rect(s, (0, 200, 180), (10, 10, 6, 4))
        self.tiles['table'] = s

        # --- terminal: 终端机 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 30, 45), (6, 4, 20, 18))
        pygame.draw.rect(s, (50, 50, 70), (6, 4, 20, 18), 2)
        pygame.draw.rect(s, (0, 40, 60), (8, 6, 16, 12))
        pygame.draw.rect(s, (0, 255, 200), (10, 8, 12, 8))
        # 屏幕文字线
        for ly in range(9, 15, 2):
            pygame.draw.line(s, (0, 180, 150), (11, ly), (20, ly))
        # 底座
        pygame.draw.rect(s, (40, 40, 55), (10, 22, 12, 6))
        pygame.draw.rect(s, (50, 50, 65), (8, 28, 16, 3))
        self.tiles['terminal'] = s

        # --- bookshelf: 书架 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (50, 35, 25), (2, 2, 28, 28))  # 木框
        pygame.draw.rect(s, (65, 45, 30), (2, 2, 28, 28), 2)  # 边框
        # 三层书
        for sy_off in [4, 13, 22]:
            pygame.draw.rect(s, (40, 30, 20), (4, sy_off, 24, 8))  # 层板
            # 书本
            colors = [(180, 40, 60), (40, 120, 200), (0, 200, 160), (200, 160, 40), (160, 60, 200)]
            bx = 5
            for ci in range(5):
                bw = random.randint(3, 5)
                pygame.draw.rect(s, colors[ci % len(colors)], (bx, sy_off + 1, bw, 6))
                bx += bw + 1
                if bx > 26:
                    break
        self.tiles['bookshelf'] = s

        # --- sofa: 沙发 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 30, 80), (2, 10, 28, 16))  # 坐垫
        pygame.draw.rect(s, (80, 40, 100), (2, 10, 28, 16), 2)  # 边框
        pygame.draw.rect(s, (50, 25, 70), (2, 6, 6, 20))  # 左扶手
        pygame.draw.rect(s, (50, 25, 70), (24, 6, 6, 20))  # 右扶手
        pygame.draw.rect(s, (45, 20, 65), (2, 4, 28, 8))  # 靠背
        # 坐垫纹理
        pygame.draw.line(s, (70, 35, 90), (10, 14), (10, 24))
        pygame.draw.line(s, (70, 35, 90), (22, 14), (22, 24))
        # 霓虹装饰线
        pygame.draw.line(s, (180, 60, 255), (3, 26), (29, 26))
        self.tiles['sofa'] = s

        # --- carpet: 地毯 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((45, 25, 55))
        # 花纹边框
        pygame.draw.rect(s, (60, 35, 70), (1, 1, TILE-2, TILE-2), 1)
        pygame.draw.rect(s, (55, 30, 65), (3, 3, TILE-6, TILE-6), 1)
        # 中心图案
        pygame.draw.rect(s, (50, 28, 60), (8, 8, 16, 16))
        pygame.draw.line(s, (70, 40, 80), (8, 8), (24, 24))
        pygame.draw.line(s, (70, 40, 80), (24, 8), (8, 24))
        # 角落装饰
        for cx, cy in [(4, 4), (TILE-5, 4), (4, TILE-5), (TILE-5, TILE-5)]:
            pygame.draw.rect(s, (80, 45, 90), (cx, cy, 2, 2))
        self.tiles['carpet'] = s

        # --- bar_counter: 吧台 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (35, 30, 50), (2, 8, 28, 18))  # 台面
        pygame.draw.rect(s, (50, 45, 70), (2, 8, 28, 18), 2)  # 边框
        pygame.draw.rect(s, (25, 20, 40), (2, 8, 28, 4))  # 台面顶部
        # 霓虹灯条
        pygame.draw.line(s, (0, 255, 200), (4, 12), (28, 12))
        pygame.draw.line(s, (255, 50, 150), (4, 24), (28, 24))
        # 杯子
        pygame.draw.rect(s, (180, 200, 220), (8, 9, 4, 3))
        pygame.draw.rect(s, (0, 200, 180), (9, 10, 2, 1))  # 液体
        pygame.draw.rect(s, (180, 200, 220), (20, 9, 4, 3))
        pygame.draw.rect(s, (255, 100, 50), (21, 10, 2, 1))  # 液体
        self.tiles['bar_counter'] = s

        # --- factory_floor: 工业格栅 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((45, 40, 35))
        # 格栅线
        for gx in range(0, TILE, 4):
            pygame.draw.line(s, (55, 50, 45), (gx, 0), (gx, TILE))
        for gy in range(0, TILE, 4):
            pygame.draw.line(s, (55, 50, 45), (0, gy), (TILE, gy))
        # 黄色危险标记
        pygame.draw.line(s, (200, 180, 0), (0, 0), (6, 0), 2)
        pygame.draw.line(s, (200, 180, 0), (TILE - 6, 0), (TILE, 0), 2)
        pygame.draw.line(s, (200, 180, 0), (0, TILE - 1), (6, TILE - 1), 2)
        pygame.draw.line(s, (200, 180, 0), (TILE - 6, TILE - 1), (TILE, TILE - 1), 2)
        self.tiles['factory_floor'] = s

        # --- cyber_floor: 虚拟网格地板 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((10, 10, 30))
        # 明亮网格线
        for gx in range(0, TILE, 8):
            pygame.draw.line(s, (0, 100, 200), (gx, 0), (gx, TILE))
        for gy in range(0, TILE, 8):
            pygame.draw.line(s, (0, 100, 200), (0, gy), (TILE, gy))
        # 交叉点发光
        for gx in range(0, TILE, 8):
            for gy in range(0, TILE, 8):
                pygame.draw.rect(s, (0, 180, 255), (gx, gy, 2, 2))
        self.tiles['cyber_floor'] = s

        # --- neon_tile: 霓虹步道 ---
        s = pygame.Surface((TILE, TILE))
        s.fill((20, 15, 40))
        # 粉/青交替发光
        pygame.draw.rect(s, (255, 50, 150), (0, 0, TILE, 2))
        pygame.draw.rect(s, (0, 255, 200), (0, TILE - 2, TILE, 2))
        pygame.draw.rect(s, (255, 50, 150), (0, 0, 2, TILE))
        pygame.draw.rect(s, (0, 255, 200), (TILE - 2, 0, 2, TILE))
        # 中心发光
        pygame.draw.rect(s, (40, 25, 60), (4, 4, TILE - 8, TILE - 8))
        for _ in range(4):
            nx, ny = random.randint(6, TILE - 7), random.randint(6, TILE - 7)
            pygame.draw.rect(s, (180, 60, 255), (nx, ny, 1, 1))
        self.tiles['neon_tile'] = s

        # --- pipe_floor: 管道地板（地下通道用）---
        s = pygame.Surface((TILE, TILE))
        s.fill((25, 22, 18))
        # 锈迹
        for _ in range(20):
            px, py = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
            c = random.choice([(35, 28, 20), (45, 35, 25), (30, 25, 18)])
            s.set_at((px, py), c)
        # 管道线
        pygame.draw.line(s, (50, 40, 30), (0, TILE // 3), (TILE, TILE // 3))
        pygame.draw.line(s, (50, 40, 30), (0, TILE * 2 // 3), (TILE, TILE * 2 // 3))
        # 铆钉
        for rx in range(4, TILE, 8):
            pygame.draw.rect(s, (70, 60, 45), (rx, TILE // 3 - 1, 2, 2))
            pygame.draw.rect(s, (70, 60, 45), (rx, TILE * 2 // 3 - 1, 2, 2))
        self.tiles['pipe_floor'] = s

        # --- rust_wall: 锈蚀墙（地下通道用）---
        s = pygame.Surface((TILE, TILE))
        s.fill((40, 30, 22))
        for _ in range(25):
            px, py = random.randint(0, TILE - 1), random.randint(0, TILE - 1)
            c = random.choice([(55, 40, 28), (35, 25, 18), (60, 45, 30)])
            s.set_at((px, py), c)
        # 锈蚀纹理
        for y in range(0, TILE, 6):
            pygame.draw.line(s, (50, 38, 25), (0, y), (TILE, y))
        pygame.draw.rect(s, (30, 22, 15), (0, 0, TILE, TILE), 1)
        self.tiles['rust_wall'] = s

        # 农田地块 (tile 21)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        s.fill((40, 30, 15))
        # 土壤纹理
        for y in range(4, TILE, 6):
            pygame.draw.line(s, (55, 40, 20), (2, y), (TILE - 2, y))
        pygame.draw.rect(s, (60, 45, 25), (0, 0, TILE, TILE), 1)
        self.tiles['farm_plot'] = s

        # 围栏 (tile 22)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        s.fill((50, 40, 30))
        pygame.draw.rect(s, (80, 65, 45), (2, 8, TILE - 4, 4))
        pygame.draw.rect(s, (80, 65, 45), (2, 20, TILE - 4, 4))
        pygame.draw.rect(s, (70, 55, 35), (6, 4, 3, 24))
        pygame.draw.rect(s, (70, 55, 35), (TILE - 9, 4, 3, 24))
        self.tiles['fence'] = s

    def _gen_player(self):
        jacket_c = (20, 20, 35)
        visor_c = (0, 255, 200)
        trim_c = (0, 200, 180)
        skin_c = (180, 160, 140)
        pants_c = (15, 15, 25)
        for direction in ['down', 'up', 'left', 'right']:
            frames = []
            for frame in range(4):
                s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                # 身体 - 暗色夹克
                pygame.draw.rect(s, jacket_c, (10, 14, 12, 12))
                # 霓虹青色边线
                pygame.draw.line(s, trim_c, (10, 14), (10, 25))
                pygame.draw.line(s, trim_c, (21, 14), (21, 25))
                pygame.draw.line(s, trim_c, (10, 25), (21, 25))
                # 胸口发光线
                pygame.draw.line(s, visor_c, (14, 18), (18, 18))
                # 头
                pygame.draw.rect(s, skin_c, (10, 4, 12, 12))
                # 头发 - 深色
                pygame.draw.rect(s, (15, 15, 25), (10, 4, 12, 5))

                if direction == 'down':
                    # LED 护目镜
                    pygame.draw.rect(s, visor_c, (11, 9, 10, 3))
                    pygame.draw.rect(s, (0, 200, 160), (12, 10, 3, 1))
                    pygame.draw.rect(s, (0, 200, 160), (17, 10, 3, 1))
                elif direction == 'up':
                    pygame.draw.rect(s, (15, 15, 25), (10, 4, 12, 7))
                    # 后脑发光条
                    pygame.draw.line(s, trim_c, (12, 8), (20, 8))
                elif direction == 'left':
                    pygame.draw.rect(s, visor_c, (10, 9, 6, 3))
                    pygame.draw.rect(s, (0, 200, 160), (11, 10, 2, 1))
                elif direction == 'right':
                    pygame.draw.rect(s, visor_c, (16, 9, 6, 3))
                    pygame.draw.rect(s, (0, 200, 160), (19, 10, 2, 1))

                # 腿 - 暗色裤子 + 霓虹条
                leg_off = [0, 2, 0, -2][frame]
                pygame.draw.rect(s, pants_c, (11, 26, 4, 5))
                pygame.draw.rect(s, pants_c, (17, 26 + leg_off, 4, 5))
                # 腿部霓虹线
                pygame.draw.line(s, trim_c, (11, 30), (14, 30))
                pygame.draw.line(s, trim_c, (17, 30 + leg_off), (20, 30 + leg_off))
                frames.append(s)
            self.player_frames[direction] = frames

    def _gen_npcs(self):
        # --- elder → 城市管理员: 深色西装, 全息徽章, 白银发 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (25, 25, 40), (10, 14, 12, 12))  # 深色西装
        pygame.draw.rect(s, (180, 160, 140), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (200, 210, 220), (10, 4, 12, 4))  # 白银发
        pygame.draw.rect(s, (80, 90, 100), (12, 9, 2, 2))  # 眼
        pygame.draw.rect(s, (80, 90, 100), (18, 9, 2, 2))
        # 全息徽章
        pygame.draw.rect(s, (0, 255, 200), (13, 17, 3, 3))
        pygame.draw.rect(s, (0, 180, 150), (14, 18, 1, 1))
        # 西装边线
        pygame.draw.line(s, (60, 65, 80), (16, 14), (16, 25))
        pygame.draw.rect(s, (20, 20, 35), (11, 26, 4, 5))
        pygame.draw.rect(s, (20, 20, 35), (17, 26, 4, 5))
        self.npc_sprites['elder'] = s

        # --- merchant → 数据贩子: 兜帽, 绿色霓虹 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 30, 20), (10, 14, 12, 12))  # 暗绿外套
        pygame.draw.rect(s, (160, 140, 120), (10, 4, 12, 12))  # 头
        # 兜帽
        pygame.draw.rect(s, (15, 25, 15), (8, 2, 16, 10))
        pygame.draw.rect(s, (0, 255, 100), (8, 11, 16, 1))  # 兜帽边缘发光
        pygame.draw.rect(s, (40, 40, 40), (12, 9, 2, 2))
        pygame.draw.rect(s, (40, 40, 40), (18, 9, 2, 2))
        # 绿色霓虹线
        pygame.draw.line(s, (0, 255, 100), (10, 14), (10, 25))
        pygame.draw.line(s, (0, 255, 100), (21, 14), (21, 25))
        pygame.draw.rect(s, (15, 20, 15), (11, 26, 4, 5))
        pygame.draw.rect(s, (15, 20, 15), (17, 26, 4, 5))
        self.npc_sprites['merchant'] = s

        # --- guard → 安保机器人: 金属身体, 红色面罩 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (100, 110, 130), (10, 14, 12, 12))  # 金属身体
        pygame.draw.rect(s, (120, 130, 150), (10, 4, 12, 12))  # 金属头
        pygame.draw.rect(s, (140, 150, 170), (10, 4, 12, 4))  # 头顶
        # 红色面罩
        pygame.draw.rect(s, (255, 40, 40), (11, 9, 10, 3))
        pygame.draw.rect(s, (255, 80, 80), (13, 10, 2, 1))
        pygame.draw.rect(s, (255, 80, 80), (17, 10, 2, 1))
        # 肩甲
        pygame.draw.rect(s, (80, 90, 110), (7, 14, 4, 4))
        pygame.draw.rect(s, (80, 90, 110), (21, 14, 4, 4))
        pygame.draw.rect(s, (90, 100, 120), (11, 26, 4, 5))
        pygame.draw.rect(s, (90, 100, 120), (17, 26, 4, 5))
        self.npc_sprites['guard'] = s

        # --- witch → 黑客: 紫色帽衫, 发光眼 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 20, 80), (10, 14, 12, 12))  # 紫色帽衫
        pygame.draw.rect(s, (160, 140, 120), (10, 4, 12, 12))  # 头
        # 帽衫兜帽
        pygame.draw.rect(s, (50, 15, 70), (8, 2, 16, 10))
        pygame.draw.rect(s, (180, 60, 255), (8, 11, 16, 1))  # 紫色边缘
        # 发光眼
        pygame.draw.rect(s, (180, 60, 255), (12, 9, 2, 2))
        pygame.draw.rect(s, (180, 60, 255), (18, 9, 2, 2))
        # 键盘全息投影
        pygame.draw.rect(s, (0, 200, 180), (8, 22, 16, 2))
        pygame.draw.rect(s, (40, 15, 55), (11, 26, 4, 5))
        pygame.draw.rect(s, (40, 15, 55), (17, 26, 4, 5))
        self.npc_sprites['witch'] = s

        # --- ghost_merchant → 幽灵黑客: 半透明紫色, 故障效果 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # 半透明身体
        pygame.draw.rect(s, (120, 60, 180), (10, 14, 12, 12))
        pygame.draw.rect(s, (160, 120, 200), (10, 4, 12, 12))
        pygame.draw.rect(s, (100, 40, 140), (10, 4, 12, 4))
        # 发光眼
        pygame.draw.rect(s, (255, 50, 150), (12, 9, 2, 2))
        pygame.draw.rect(s, (255, 50, 150), (18, 9, 2, 2))
        # 故障线条
        pygame.draw.line(s, (0, 255, 200), (8, 16), (24, 16))
        pygame.draw.line(s, (255, 50, 150), (6, 22), (26, 22))
        # 斗篷
        pygame.draw.rect(s, (80, 40, 120), (8, 12, 16, 16))
        pygame.draw.rect(s, (60, 30, 100), (10, 26, 4, 5))
        pygame.draw.rect(s, (60, 30, 100), (17, 26, 4, 5))
        self.npc_sprites['ghost_merchant'] = s

        # --- arms_dealer → 军火商: 重甲, 橙色霓虹 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (50, 45, 40), (9, 13, 14, 13))  # 重甲身体
        pygame.draw.rect(s, (160, 140, 120), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (40, 35, 30), (10, 4, 12, 5))  # 头盔
        # 橙色霓虹线
        pygame.draw.line(s, (255, 140, 0), (9, 13), (9, 25))
        pygame.draw.line(s, (255, 140, 0), (22, 13), (22, 25))
        pygame.draw.line(s, (255, 140, 0), (9, 19), (22, 19))
        # 面罩
        pygame.draw.rect(s, (255, 100, 0), (12, 8, 8, 3))
        # 肩甲
        pygame.draw.rect(s, (60, 55, 50), (6, 13, 4, 5))
        pygame.draw.rect(s, (60, 55, 50), (22, 13, 4, 5))
        pygame.draw.rect(s, (40, 35, 30), (11, 26, 4, 5))
        pygame.draw.rect(s, (40, 35, 30), (17, 26, 4, 5))
        self.npc_sprites['arms_dealer'] = s

        # --- info_broker → 情报商: 纤细, 蓝色霓虹眼镜 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 20, 30), (11, 14, 10, 12))  # 纤细身体
        pygame.draw.rect(s, (170, 150, 130), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (15, 15, 25), (10, 4, 12, 4))  # 头发
        # 蓝色霓虹眼镜
        pygame.draw.rect(s, (40, 120, 255), (10, 8, 12, 4))
        pygame.draw.rect(s, (80, 160, 255), (11, 9, 4, 2))
        pygame.draw.rect(s, (80, 160, 255), (17, 9, 4, 2))
        # 领带发光
        pygame.draw.line(s, (40, 120, 255), (16, 14), (16, 24))
        pygame.draw.rect(s, (15, 15, 25), (12, 26, 3, 5))
        pygame.draw.rect(s, (15, 15, 25), (17, 26, 3, 5))
        self.npc_sprites['info_broker'] = s

        # --- factory_worker → 工厂工人: 黄色安全帽, 橙色背心 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (200, 120, 0), (10, 14, 12, 12))  # 橙色背心
        pygame.draw.rect(s, (170, 150, 130), (10, 4, 12, 12))  # 头
        # 黄色安全帽
        pygame.draw.rect(s, (220, 200, 0), (8, 2, 16, 6))
        pygame.draw.rect(s, (255, 230, 0), (10, 4, 12, 2))
        # 眼
        pygame.draw.rect(s, (40, 40, 40), (12, 9, 2, 2))
        pygame.draw.rect(s, (40, 40, 40), (18, 9, 2, 2))
        # 反光条
        pygame.draw.line(s, (255, 255, 0), (10, 18), (21, 18))
        pygame.draw.line(s, (255, 255, 0), (10, 22), (21, 22))
        pygame.draw.rect(s, (60, 55, 50), (11, 26, 4, 5))
        pygame.draw.rect(s, (60, 55, 50), (17, 26, 4, 5))
        self.npc_sprites['factory_worker'] = s

        # --- ai_prophet → AI 先知: 白袍, 青色光芒 ---
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        # 白色长袍
        pygame.draw.rect(s, (200, 210, 220), (9, 12, 14, 16))
        pygame.draw.rect(s, (180, 190, 200), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (220, 230, 240), (10, 4, 12, 3))  # 白发
        # 青色发光眼
        pygame.draw.rect(s, (0, 255, 200), (12, 9, 2, 2))
        pygame.draw.rect(s, (0, 255, 200), (18, 9, 2, 2))
        # 青色光芒线
        pygame.draw.line(s, (0, 255, 200), (9, 12), (9, 27))
        pygame.draw.line(s, (0, 255, 200), (22, 12), (22, 27))
        pygame.draw.line(s, (0, 200, 180), (12, 28), (12, 31))
        pygame.draw.line(s, (0, 200, 180), (19, 28), (19, 31))
        # 全息符文
        pygame.draw.rect(s, (0, 180, 160), (13, 16, 6, 1))
        pygame.draw.rect(s, (0, 180, 160), (14, 20, 4, 1))
        self.npc_sprites['ai_prophet'] = s

        # --- 恋爱角色精灵 ---
        # 林月: 冷色调，蓝色短发，白大褂
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (220, 230, 240), (10, 14, 12, 12))  # 白大褂
        pygame.draw.rect(s, (180, 160, 140), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (60, 120, 200), (9, 3, 14, 6))  # 蓝色短发
        pygame.draw.rect(s, (40, 100, 180), (12, 9, 2, 2))  # 眼
        pygame.draw.rect(s, (40, 100, 180), (18, 9, 2, 2))
        pygame.draw.rect(s, (0, 180, 255), (14, 17, 4, 3))  # 数据板
        pygame.draw.rect(s, (200, 210, 220), (11, 26, 4, 5))
        pygame.draw.rect(s, (200, 210, 220), (17, 26, 4, 5))
        self.npc_sprites['romance_linyue'] = s

        # 小焰: 暖色调，红色马尾，工装
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 100, 40), (10, 14, 12, 12))  # 橙色工装
        pygame.draw.rect(s, (180, 160, 140), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (220, 60, 30), (9, 2, 14, 7))  # 红发
        pygame.draw.rect(s, (220, 60, 30), (22, 4, 3, 10))  # 马尾
        pygame.draw.rect(s, (60, 40, 20), (12, 9, 2, 2))
        pygame.draw.rect(s, (60, 40, 20), (18, 9, 2, 2))
        pygame.draw.rect(s, (120, 130, 140), (8, 18, 3, 6))  # 扳手
        pygame.draw.rect(s, (160, 80, 30), (11, 26, 4, 5))
        pygame.draw.rect(s, (160, 80, 30), (17, 26, 4, 5))
        self.npc_sprites['romance_xiaoyan'] = s

        # 零: 全息感，淡紫色，半透明
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 160, 220), (10, 14, 12, 12))  # 淡紫衣
        pygame.draw.rect(s, (200, 190, 230), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (160, 140, 255), (9, 3, 14, 5))  # 紫发
        pygame.draw.rect(s, (0, 255, 200), (12, 9, 2, 2))  # 发光眼
        pygame.draw.rect(s, (0, 255, 200), (18, 9, 2, 2))
        # 全息光环
        pygame.draw.rect(s, (0, 200, 180, 100), (8, 2, 16, 1))
        pygame.draw.rect(s, (0, 200, 180, 100), (7, 14, 1, 12))
        pygame.draw.rect(s, (0, 200, 180, 100), (24, 14, 1, 12))
        pygame.draw.rect(s, (160, 140, 220), (11, 26, 4, 5))
        pygame.draw.rect(s, (160, 140, 220), (17, 26, 4, 5))
        self.npc_sprites['romance_zero'] = s

        # 阿星: 暗色调，黑色长发，披风
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 35, 45), (10, 14, 12, 12))  # 暗色披风
        pygame.draw.rect(s, (180, 160, 140), (10, 4, 12, 12))  # 头
        pygame.draw.rect(s, (20, 20, 30), (9, 2, 14, 8))  # 黑发
        pygame.draw.rect(s, (20, 20, 30), (8, 6, 2, 12))  # 长发左
        pygame.draw.rect(s, (20, 20, 30), (22, 6, 2, 12))  # 长发右
        pygame.draw.rect(s, (200, 160, 100), (12, 9, 2, 2))  # 琥珀色眼
        pygame.draw.rect(s, (200, 160, 100), (18, 9, 2, 2))
        # 披风
        pygame.draw.rect(s, (35, 30, 40), (7, 16, 3, 10))
        pygame.draw.rect(s, (35, 30, 40), (22, 16, 3, 10))
        pygame.draw.rect(s, (35, 30, 40), (11, 26, 4, 5))
        pygame.draw.rect(s, (35, 30, 40), (17, 26, 4, 5))
        self.npc_sprites['romance_axing'] = s

        # --- 宠物精灵 ---
        # 赛博猫
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (100, 110, 130), (8, 14, 16, 12))  # 身体
        pygame.draw.ellipse(s, (120, 130, 150), (10, 6, 12, 10))  # 头
        pygame.draw.polygon(s, (120, 130, 150), [(10, 8), (12, 2), (14, 8)])  # 左耳
        pygame.draw.polygon(s, (120, 130, 150), [(18, 8), (20, 2), (22, 8)])  # 右耳
        pygame.draw.rect(s, (0, 255, 200), (12, 10, 2, 2))  # 发光眼
        pygame.draw.rect(s, (0, 255, 200), (18, 10, 2, 2))
        pygame.draw.line(s, (0, 200, 180), (16, 20), (16, 28))  # 尾巴
        pygame.draw.line(s, (0, 200, 180), (16, 28), (20, 26))
        self.npc_sprites['pet_cat'] = s

        # 数据狐
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (200, 120, 40), (8, 14, 16, 12))  # 身体
        pygame.draw.ellipse(s, (220, 140, 60), (10, 6, 12, 10))  # 头
        pygame.draw.polygon(s, (220, 140, 60), [(10, 8), (11, 1), (14, 7)])  # 左耳
        pygame.draw.polygon(s, (220, 140, 60), [(18, 7), (21, 1), (22, 8)])  # 右耳
        pygame.draw.rect(s, (255, 200, 0), (12, 10, 2, 2))
        pygame.draw.rect(s, (255, 200, 0), (18, 10, 2, 2))
        # 大尾巴
        pygame.draw.ellipse(s, (220, 140, 60), (18, 18, 10, 8))
        pygame.draw.ellipse(s, (255, 255, 255), (24, 22, 4, 4))  # 尾尖白
        self.npc_sprites['pet_fox'] = s

        # 纳米鸟
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (100, 200, 255), (10, 10, 12, 10))  # 身体
        pygame.draw.ellipse(s, (120, 220, 255), (12, 6, 8, 8))  # 头
        pygame.draw.rect(s, (255, 200, 0), (19, 9, 4, 2))  # 喙
        pygame.draw.rect(s, (0, 0, 0), (14, 8, 2, 2))  # 眼
        # 翅膀
        pygame.draw.polygon(s, (80, 180, 240), [(8, 12), (4, 8), (10, 14)])
        pygame.draw.polygon(s, (80, 180, 240), [(22, 12), (28, 8), (22, 14)])
        self.npc_sprites['pet_bird'] = s

        # 机甲犬
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (140, 150, 160), (8, 14, 16, 10))  # 身体
        pygame.draw.rect(s, (160, 170, 180), (10, 8, 10, 8))  # 头
        pygame.draw.rect(s, (255, 60, 40), (12, 10, 2, 2))  # 眼
        pygame.draw.rect(s, (255, 60, 40), (18, 10, 2, 2))
        pygame.draw.rect(s, (120, 130, 140), (8, 24, 3, 4))  # 腿
        pygame.draw.rect(s, (120, 130, 140), (13, 24, 3, 4))
        pygame.draw.rect(s, (120, 130, 140), (18, 24, 3, 4))
        pygame.draw.rect(s, (120, 130, 140), (22, 24, 3, 4))
        self.npc_sprites['pet_dog'] = s

        # 幽灵水母
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (100, 200, 255, 150), (8, 6, 16, 12))  # 伞盖
        pygame.draw.ellipse(s, (150, 220, 255, 100), (10, 8, 12, 8))  # 内部
        # 触手
        for tx in range(10, 24, 3):
            pygame.draw.line(s, (80, 180, 255, 120), (tx, 18), (tx + 1, 28))
        pygame.draw.rect(s, (200, 255, 255), (14, 10, 2, 2))  # 眼
        pygame.draw.rect(s, (200, 255, 255), (18, 10, 2, 2))
        self.npc_sprites['pet_jelly'] = s

        # --- 进化宠物精灵 ---
        # 量子猫 (进化)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (60, 80, 180), (6, 12, 20, 14))  # 身体
        pygame.draw.ellipse(s, (80, 100, 200), (8, 4, 16, 12))  # 头
        pygame.draw.polygon(s, (100, 120, 220), [(8, 6), (10, 0), (13, 6)])  # 左耳
        pygame.draw.polygon(s, (100, 120, 220), [(19, 6), (22, 0), (24, 6)])  # 右耳
        pygame.draw.rect(s, (0, 255, 255), (11, 8, 3, 3))  # 发光眼
        pygame.draw.rect(s, (0, 255, 255), (18, 8, 3, 3))
        pygame.draw.line(s, (0, 255, 255), (16, 20), (16, 28))  # 尾巴
        pygame.draw.line(s, (0, 255, 255), (16, 28), (22, 24))
        # 量子光环
        pygame.draw.circle(s, (0, 200, 255, 80), (16, 16), 14, 1)
        self.npc_sprites['pet_cat_evo'] = s

        # 暗网狐 (进化)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (150, 40, 80), (6, 12, 20, 14))  # 身体
        pygame.draw.ellipse(s, (180, 60, 100), (8, 4, 16, 12))  # 头
        pygame.draw.polygon(s, (180, 60, 100), [(8, 6), (9, 0), (13, 5)])
        pygame.draw.polygon(s, (180, 60, 100), [(19, 5), (23, 0), (24, 6)])
        pygame.draw.rect(s, (255, 100, 0), (11, 8, 3, 3))
        pygame.draw.rect(s, (255, 100, 0), (18, 8, 3, 3))
        pygame.draw.ellipse(s, (180, 60, 100), (20, 16, 12, 10))  # 大尾巴
        pygame.draw.ellipse(s, (255, 150, 50), (26, 20, 6, 6))  # 尾尖
        self.npc_sprites['pet_fox_evo'] = s

        # 等离子鸟 (进化)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (50, 150, 255), (8, 8, 16, 14))  # 身体
        pygame.draw.ellipse(s, (80, 180, 255), (10, 4, 12, 10))  # 头
        pygame.draw.rect(s, (255, 255, 0), (21, 7, 5, 3))  # 喙
        pygame.draw.rect(s, (255, 255, 255), (13, 6, 3, 3))  # 眼
        pygame.draw.polygon(s, (30, 120, 255), [(6, 10), (0, 4), (8, 12)])  # 左翅
        pygame.draw.polygon(s, (30, 120, 255), [(24, 10), (30, 4), (24, 12)])  # 右翅
        # 等离子尾
        pygame.draw.line(s, (100, 200, 255), (14, 22), (10, 28))
        pygame.draw.line(s, (100, 200, 255), (18, 22), (22, 28))
        self.npc_sprites['pet_bird_evo'] = s

        # 重装犬 (进化)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (100, 110, 130), (6, 12, 20, 12))  # 身体
        pygame.draw.rect(s, (120, 130, 150), (8, 6, 14, 10))  # 头
        pygame.draw.rect(s, (255, 30, 30), (10, 8, 3, 3))  # 眼
        pygame.draw.rect(s, (255, 30, 30), (19, 8, 3, 3))
        # 装甲
        pygame.draw.rect(s, (80, 90, 100), (6, 14, 20, 4))
        pygame.draw.rect(s, (90, 100, 110), (6, 24, 4, 5))  # 腿
        pygame.draw.rect(s, (90, 100, 110), (12, 24, 4, 5))
        pygame.draw.rect(s, (90, 100, 110), (18, 24, 4, 5))
        pygame.draw.rect(s, (90, 100, 110), (24, 24, 4, 5))
        self.npc_sprites['pet_dog_evo'] = s

        # 深渊水母 (进化)
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (60, 100, 200, 180), (6, 4, 20, 14))  # 伞盖
        pygame.draw.ellipse(s, (100, 150, 255, 120), (8, 6, 16, 10))  # 内部
        for tx in range(8, 26, 3):
            pygame.draw.line(s, (40, 80, 200, 150), (tx, 18), (tx + 2, 30))
        pygame.draw.rect(s, (150, 200, 255), (12, 8, 3, 3))  # 眼
        pygame.draw.rect(s, (150, 200, 255), (19, 8, 3, 3))
        self.npc_sprites['pet_jelly_evo'] = s

    def _gen_enemies(self):
        # --- slime → 纳米虫: 小型金属昆虫, 绿色发光 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 金属虫身
        pygame.draw.ellipse(s, (60, 70, 80), (14, 24, 36, 24))
        pygame.draw.ellipse(s, (80, 90, 100), (18, 28, 28, 16))
        # 绿色发光
        pygame.draw.ellipse(s, (0, 255, 100), (22, 30, 20, 10))
        # 眼
        pygame.draw.rect(s, (0, 255, 100), (22, 28, 3, 3))
        pygame.draw.rect(s, (0, 255, 100), (37, 28, 3, 3))
        # 触角
        pygame.draw.line(s, (100, 110, 130), (24, 24), (18, 16))
        pygame.draw.line(s, (100, 110, 130), (38, 24), (44, 16))
        # 腿
        for lx in [16, 24, 32, 40]:
            pygame.draw.line(s, (80, 90, 100), (lx, 44), (lx - 4, 52))
            pygame.draw.line(s, (80, 90, 100), (lx + 2, 44), (lx + 6, 52))
        self.enemy_sprites['slime'] = s

        # --- bat → 侦察无人机: 小型飞行器 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 机身
        pygame.draw.ellipse(s, (80, 90, 110), (22, 22, 20, 16))
        pygame.draw.rect(s, (100, 110, 130), (28, 20, 8, 4))
        # 螺旋桨
        pygame.draw.line(s, (140, 150, 170), (18, 18), (8, 14), 2)
        pygame.draw.line(s, (140, 150, 170), (46, 18), (56, 14), 2)
        pygame.draw.circle(s, (180, 190, 200), (8, 14), 3, 1)
        pygame.draw.circle(s, (180, 190, 200), (56, 14), 3, 1)
        # 红色指示灯
        pygame.draw.rect(s, (255, 40, 40), (30, 26, 4, 3))
        # 底部扫描光
        pygame.draw.line(s, (255, 40, 80), (28, 38), (36, 38))
        pygame.draw.line(s, (200, 30, 60), (26, 42), (38, 42))
        self.enemy_sprites['bat'] = s

        # --- skeleton → 机甲士兵: 人形机器人, 红眼 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 头
        pygame.draw.rect(s, (100, 110, 130), (22, 4, 20, 16))
        pygame.draw.rect(s, (120, 130, 150), (24, 6, 16, 12))
        # 红眼
        pygame.draw.rect(s, (255, 40, 40), (26, 10, 4, 3))
        pygame.draw.rect(s, (255, 40, 40), (34, 10, 4, 3))
        # 嘴部格栅
        pygame.draw.rect(s, (60, 65, 75), (28, 14, 8, 3))
        # 身体
        pygame.draw.rect(s, (80, 90, 110), (24, 20, 16, 20))
        pygame.draw.rect(s, (100, 110, 130), (26, 22, 12, 16))
        # 胸口红灯
        pygame.draw.rect(s, (255, 40, 40), (30, 26, 4, 4))
        # 手臂
        pygame.draw.rect(s, (90, 100, 120), (18, 22, 6, 16))
        pygame.draw.rect(s, (90, 100, 120), (40, 22, 6, 16))
        # 武器 (右手枪)
        pygame.draw.rect(s, (140, 150, 170), (42, 34, 10, 3))
        # 腿
        pygame.draw.rect(s, (80, 90, 110), (26, 40, 5, 14))
        pygame.draw.rect(s, (80, 90, 110), (33, 40, 5, 14))
        # 关节发光
        pygame.draw.rect(s, (255, 40, 40), (27, 40, 3, 2))
        pygame.draw.rect(s, (255, 40, 40), (34, 40, 3, 2))
        self.enemy_sprites['skeleton'] = s

        # --- dragon → AI 核心: 大型机械实体 (96x96) ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 核心球体
        pygame.draw.ellipse(s, (40, 45, 70), (20, 20, 56, 56))
        pygame.draw.ellipse(s, (60, 65, 90), (26, 26, 44, 44))
        # 中心眼
        pygame.draw.circle(s, (255, 40, 80), (48, 48), 10)
        pygame.draw.circle(s, (255, 100, 120), (48, 48), 6)
        pygame.draw.circle(s, (255, 200, 200), (48, 48), 3)
        # 电缆
        for angle_x, angle_y in [(-1, -1), (1, -1), (-1, 1), (1, 1), (0, -1), (0, 1)]:
            ex = 48 + angle_x * 36
            ey = 48 + angle_y * 36
            pygame.draw.line(s, (0, 200, 180), (48, 48), (ex, ey), 2)
            pygame.draw.circle(s, (0, 255, 200), (ex, ey), 3)
        # 外环
        pygame.draw.ellipse(s, (0, 180, 160), (16, 16, 64, 64), 2)
        pygame.draw.ellipse(s, (180, 60, 255), (10, 10, 76, 76), 1)
        # 数据碎片
        for _ in range(8):
            fx = random.randint(14, 82)
            fy = random.randint(14, 82)
            pygame.draw.rect(s, (0, 255, 200), (fx, fy, 2, 2))
        self.enemy_sprites['dragon'] = s

        # --- golden_slime → 黄金纳米虫: 金色金属昆虫 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (180, 150, 40), (14, 24, 36, 24))
        pygame.draw.ellipse(s, (220, 190, 60), (18, 28, 28, 16))
        # 金色发光
        pygame.draw.ellipse(s, (255, 220, 80), (22, 30, 20, 10))
        pygame.draw.rect(s, (255, 200, 50), (22, 28, 3, 3))
        pygame.draw.rect(s, (255, 200, 50), (37, 28, 3, 3))
        # 触角
        pygame.draw.line(s, (200, 170, 50), (24, 24), (18, 16))
        pygame.draw.line(s, (200, 170, 50), (38, 24), (44, 16))
        # 闪光
        pygame.draw.rect(s, (255, 255, 200), (30, 22, 3, 3))
        pygame.draw.rect(s, (255, 255, 200), (18, 30, 2, 2))
        # 腿
        for lx in [16, 24, 32, 40]:
            pygame.draw.line(s, (200, 170, 50), (lx, 44), (lx - 4, 52))
            pygame.draw.line(s, (200, 170, 50), (lx + 2, 44), (lx + 6, 52))
        self.enemy_sprites['golden_slime'] = s

        # --- factory_guard → 工厂守卫: 重型工业机器人 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 厚重身体
        pygame.draw.rect(s, (70, 65, 55), (18, 18, 28, 28))
        pygame.draw.rect(s, (90, 85, 75), (20, 20, 24, 24))
        # 头
        pygame.draw.rect(s, (80, 75, 65), (24, 6, 16, 14))
        # 黄色警示眼
        pygame.draw.rect(s, (255, 200, 0), (27, 10, 4, 4))
        pygame.draw.rect(s, (255, 200, 0), (35, 10, 4, 4))
        # 肩甲
        pygame.draw.rect(s, (60, 55, 45), (12, 18, 8, 10))
        pygame.draw.rect(s, (60, 55, 45), (44, 18, 8, 10))
        # 危险条纹
        for sy in range(20, 42, 4):
            pygame.draw.line(s, (200, 180, 0), (20, sy), (43, sy))
        # 腿
        pygame.draw.rect(s, (70, 65, 55), (22, 46, 8, 12))
        pygame.draw.rect(s, (70, 65, 55), (34, 46, 8, 12))
        self.enemy_sprites['factory_guard'] = s

        # --- glitch_bot → 故障机器人: 损坏机器人, 静电效果 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 扭曲身体
        pygame.draw.rect(s, (80, 90, 100), (22, 20, 18, 22))
        pygame.draw.rect(s, (90, 100, 110), (24, 22, 14, 18))
        # 头 - 歪斜
        pygame.draw.rect(s, (100, 110, 120), (24, 6, 18, 14))
        # 故障眼 - 一红一蓝
        pygame.draw.rect(s, (255, 40, 40), (27, 10, 4, 4))
        pygame.draw.rect(s, (0, 200, 255), (35, 12, 4, 4))
        # 静电线
        for _ in range(6):
            sx = random.randint(18, 46)
            sy = random.randint(8, 48)
            ex = sx + random.randint(-8, 8)
            pygame.draw.line(s, (0, 255, 200), (sx, sy), (ex, sy + random.randint(2, 6)))
        # 断裂手臂
        pygame.draw.rect(s, (80, 90, 100), (16, 22, 6, 12))
        pygame.draw.rect(s, (80, 90, 100), (42, 24, 6, 8))
        # 腿
        pygame.draw.rect(s, (70, 80, 90), (24, 42, 5, 12))
        pygame.draw.rect(s, (70, 80, 90), (35, 42, 5, 14))
        self.enemy_sprites['glitch_bot'] = s

        # --- cyber_virus → 赛博病毒: 抽象数字实体, 红/紫 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 核心
        pygame.draw.circle(s, (180, 30, 60), (32, 32), 14)
        pygame.draw.circle(s, (255, 50, 100), (32, 32), 10)
        pygame.draw.circle(s, (255, 120, 150), (32, 32), 5)
        # 触手/数据流
        for angle in range(0, 360, 45):
            import math
            rad = math.radians(angle)
            ex = int(32 + 24 * math.cos(rad))
            ey = int(32 + 24 * math.sin(rad))
            c = (180, 60, 255) if angle % 90 == 0 else (255, 40, 80)
            pygame.draw.line(s, c, (32, 32), (ex, ey), 1)
            pygame.draw.circle(s, c, (ex, ey), 2)
        # 外环
        pygame.draw.circle(s, (180, 60, 255), (32, 32), 22, 1)
        self.enemy_sprites['cyber_virus'] = s

        # --- data_ghost → 数据幽灵: 半透明数字幽灵 (64x64) ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 幽灵身体 - 半透明蓝
        pygame.draw.ellipse(s, (40, 80, 160), (16, 10, 32, 36))
        pygame.draw.ellipse(s, (60, 100, 180), (20, 14, 24, 28))
        # 眼
        pygame.draw.rect(s, (0, 255, 200), (24, 22, 4, 4))
        pygame.draw.rect(s, (0, 255, 200), (36, 22, 4, 4))
        # 嘴
        pygame.draw.rect(s, (0, 180, 160), (28, 30, 8, 3))
        # 底部波浪/消散效果
        for bx in range(18, 46, 4):
            h = random.randint(4, 10)
            pygame.draw.rect(s, (40, 80, 160), (bx, 42, 3, h))
        # 数据碎片
        for _ in range(5):
            fx, fy = random.randint(14, 50), random.randint(8, 48)
            pygame.draw.rect(s, (0, 255, 220), (fx, fy, 2, 1))
        self.enemy_sprites['data_ghost'] = s

        # --- quantum_lord → 量子领主: 巨型实体, 多色发光 (96x96) ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 主体 - 多层
        pygame.draw.ellipse(s, (30, 20, 50), (16, 16, 64, 64))
        pygame.draw.ellipse(s, (50, 30, 70), (22, 22, 52, 52))
        pygame.draw.ellipse(s, (70, 40, 90), (28, 28, 40, 40))
        # 核心
        pygame.draw.circle(s, (255, 255, 255), (48, 48), 8)
        pygame.draw.circle(s, (200, 200, 255), (48, 48), 5)
        # 多色光环
        colors = [(0, 255, 200), (255, 50, 150), (180, 60, 255), (0, 255, 100), (255, 220, 50)]
        for i, c in enumerate(colors):
            r = 30 + i * 4
            pygame.draw.circle(s, c, (48, 48), r, 1)
        # 能量射线
        import math
        for i in range(8):
            rad = math.radians(i * 45)
            ex = int(48 + 40 * math.cos(rad))
            ey = int(48 + 40 * math.sin(rad))
            c = colors[i % len(colors)]
            pygame.draw.line(s, c, (48, 48), (ex, ey), 2)
            pygame.draw.circle(s, (255, 255, 255), (ex, ey), 3)
            pygame.draw.circle(s, c, (ex, ey), 2)
        # 浮动符文
        for _ in range(6):
            rx, ry = random.randint(10, 86), random.randint(10, 86)
            pygame.draw.rect(s, random.choice(colors), (rx, ry, 3, 3))
        self.enemy_sprites['quantum_lord'] = s

        # --- mad_overseer: 失控监工Boss - 大型机械人 ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 身体
        pygame.draw.rect(s, (80, 60, 40), (28, 25, 40, 50))
        pygame.draw.rect(s, (100, 75, 50), (28, 25, 40, 50), 2)
        # 头部
        pygame.draw.rect(s, (90, 70, 45), (35, 10, 26, 20))
        # 红色眼睛
        pygame.draw.rect(s, (255, 40, 40), (40, 16, 5, 5))
        pygame.draw.rect(s, (255, 40, 40), (51, 16, 5, 5))
        # 机械臂
        pygame.draw.rect(s, (70, 55, 35), (15, 30, 13, 8))
        pygame.draw.rect(s, (70, 55, 35), (68, 30, 13, 8))
        # 钳子
        pygame.draw.polygon(s, (120, 90, 50), [(15, 38), (8, 50), (20, 50)])
        pygame.draw.polygon(s, (120, 90, 50), [(68, 38), (75, 50), (83, 50)])
        # 电弧
        pygame.draw.line(s, (255, 255, 0), (20, 50), (25, 55), 2)
        pygame.draw.line(s, (255, 255, 0), (75, 50), (70, 55), 2)
        # 腿
        pygame.draw.rect(s, (60, 45, 30), (35, 75, 10, 15))
        pygame.draw.rect(s, (60, 45, 30), (51, 75, 10, 15))
        self.enemy_sprites['mad_overseer'] = s

        # --- ai_core_boss: 觉醒AI核心 - 发光球体 ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        pygame.draw.circle(s, (20, 40, 80), (48, 48), 35)
        pygame.draw.circle(s, (40, 80, 160), (48, 48), 28)
        pygame.draw.circle(s, (80, 140, 220), (48, 48), 20)
        pygame.draw.circle(s, (150, 200, 255), (48, 48), 10)
        # 数据环
        import math
        for i in range(12):
            rad = math.radians(i * 30)
            ex = int(48 + 32 * math.cos(rad))
            ey = int(48 + 32 * math.sin(rad))
            pygame.draw.rect(s, (0, 200, 255), (ex - 1, ey - 1, 3, 3))
        self.enemy_sprites['ai_core_boss'] = s

        # --- quantum_overlord: 量子霸主·真身 ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 巨大能量体
        pygame.draw.circle(s, (60, 20, 100), (48, 48), 40)
        pygame.draw.circle(s, (100, 40, 160), (48, 48), 30)
        pygame.draw.circle(s, (160, 80, 220), (48, 48), 18)
        pygame.draw.circle(s, (220, 150, 255), (48, 48), 8)
        # 量子光环
        for i in range(16):
            rad = math.radians(i * 22.5)
            ex = int(48 + 42 * math.cos(rad))
            ey = int(48 + 42 * math.sin(rad))
            c = [(255, 50, 150), (0, 255, 200), (180, 60, 255)][i % 3]
            pygame.draw.line(s, c, (48, 48), (ex, ey), 1)
            pygame.draw.circle(s, (255, 255, 255), (ex, ey), 2)
        # 符文
        for _ in range(8):
            rx, ry = random.randint(8, 88), random.randint(8, 88)
            pygame.draw.rect(s, (255, 200, 255), (rx, ry, 2, 2))
        self.enemy_sprites['quantum_overlord'] = s

        # --- pipe_worm: 管道蠕虫 ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 蠕虫身体（弯曲）
        pts = [(10, 40), (20, 30), (32, 35), (44, 28), (54, 32)]
        for i in range(len(pts) - 1):
            pygame.draw.line(s, (80, 100, 60), pts[i], pts[i + 1], 6)
        # 头部
        pygame.draw.circle(s, (100, 120, 70), (54, 32), 8)
        pygame.draw.circle(s, (200, 50, 50), (57, 30), 2)  # 眼
        # 分泌物
        pygame.draw.circle(s, (120, 180, 40), (10, 42), 3)
        self.enemy_sprites['pipe_worm'] = s

        # --- security_drone: 安保无人机 ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 机身
        pygame.draw.ellipse(s, (60, 70, 90), (16, 24, 32, 16))
        pygame.draw.ellipse(s, (80, 90, 110), (16, 24, 32, 16), 1)
        # 旋翼
        pygame.draw.line(s, (100, 110, 130), (12, 28), (4, 20), 2)
        pygame.draw.line(s, (100, 110, 130), (52, 28), (60, 20), 2)
        # 红色扫描灯
        pygame.draw.circle(s, (255, 40, 40), (32, 36), 3)
        pygame.draw.circle(s, (255, 100, 100), (32, 36), 5, 1)
        # 枪管
        pygame.draw.rect(s, (80, 80, 100), (30, 40, 4, 8))
        self.enemy_sprites['security_drone'] = s

        # --- black_market_thug: 黑市打手 ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 身体
        pygame.draw.rect(s, (40, 35, 50), (22, 20, 20, 28))
        # 头
        pygame.draw.circle(s, (60, 50, 45), (32, 14), 10)
        # 面罩
        pygame.draw.rect(s, (30, 25, 40), (26, 12, 12, 6))
        # 红色眼
        pygame.draw.rect(s, (255, 40, 40), (28, 14, 3, 2))
        pygame.draw.rect(s, (255, 40, 40), (35, 14, 3, 2))
        # 武器
        pygame.draw.rect(s, (100, 100, 120), (44, 25, 3, 18))
        # 腿
        pygame.draw.rect(s, (35, 30, 45), (25, 48, 7, 12))
        pygame.draw.rect(s, (35, 30, 45), (36, 48, 7, 12))
        self.enemy_sprites['black_market_thug'] = s

        # --- darknet_guard: 暗网守卫 ---
        s = pygame.Surface((64, 64), pygame.SRCALPHA)
        # 数字化身体
        pygame.draw.rect(s, (20, 10, 40), (20, 15, 24, 35))
        # 数据流纹理
        for y in range(15, 50, 3):
            c = random.choice([(0, 180, 200), (140, 50, 200)])
            pygame.draw.line(s, c, (20, y), (44, y))
        # 头部（全息）
        pygame.draw.circle(s, (0, 200, 180), (32, 10), 8)
        pygame.draw.circle(s, (0, 255, 220), (32, 10), 5)
        # 眼
        pygame.draw.rect(s, (255, 255, 255), (29, 8, 2, 3))
        pygame.draw.rect(s, (255, 255, 255), (35, 8, 2, 3))
        # 数据链
        pygame.draw.line(s, (0, 255, 200), (15, 25), (10, 35), 2)
        pygame.draw.line(s, (0, 255, 200), (49, 25), (54, 35), 2)
        self.enemy_sprites['darknet_guard'] = s

        # --- firewall_guardian: 防火墙守卫 (96x96) ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 六角盾形身体
        pygame.draw.polygon(s, (30, 60, 100), [(48, 8), (80, 28), (80, 68), (48, 88), (16, 68), (16, 28)])
        pygame.draw.polygon(s, (40, 80, 130), [(48, 14), (74, 32), (74, 64), (48, 82), (22, 64), (22, 32)])
        # 防火墙纹理
        for y in range(20, 80, 6):
            c = (0, 200, 255) if y % 12 == 0 else (0, 140, 200)
            pygame.draw.line(s, c, (24, y), (72, y), 1)
        # 中心眼
        pygame.draw.circle(s, (255, 100, 0), (48, 48), 12)
        pygame.draw.circle(s, (255, 180, 50), (48, 48), 7)
        pygame.draw.circle(s, (255, 255, 200), (48, 48), 3)
        # 外环
        pygame.draw.polygon(s, (0, 200, 255), [(48, 8), (80, 28), (80, 68), (48, 88), (16, 68), (16, 28)], 2)
        self.enemy_sprites['firewall_guardian'] = s

        # --- data_devourer: 数据吞噬者 (96x96) ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 巨大嘴形
        pygame.draw.ellipse(s, (60, 20, 60), (12, 20, 72, 56))
        pygame.draw.ellipse(s, (80, 30, 80), (18, 26, 60, 44))
        # 嘴巴（张开）
        pygame.draw.ellipse(s, (20, 5, 30), (28, 38, 40, 24))
        # 牙齿
        for tx in range(32, 64, 6):
            pygame.draw.polygon(s, (200, 200, 220), [(tx, 38), (tx + 3, 46), (tx + 6, 38)])
            pygame.draw.polygon(s, (200, 200, 220), [(tx, 62), (tx + 3, 54), (tx + 6, 62)])
        # 眼睛（多只）
        for ex, ey in [(28, 28), (48, 22), (68, 28)]:
            pygame.draw.circle(s, (255, 0, 80), (ex, ey), 5)
            pygame.draw.circle(s, (255, 100, 150), (ex, ey), 2)
        # 数据流触手
        import math
        for angle in range(0, 360, 60):
            rad = math.radians(angle)
            ex = int(48 + 40 * math.cos(rad))
            ey = int(48 + 40 * math.sin(rad))
            pygame.draw.line(s, (180, 0, 180), (48, 48), (ex, ey), 2)
            pygame.draw.circle(s, (255, 0, 200), (ex, ey), 3)
        self.enemy_sprites['data_devourer'] = s

        # --- darknet_lord: 暗网之主 (96x96) ---
        s = pygame.Surface((96, 96), pygame.SRCALPHA)
        # 暗影身体
        pygame.draw.circle(s, (20, 0, 40), (48, 48), 38)
        pygame.draw.circle(s, (40, 10, 60), (48, 48), 28)
        pygame.draw.circle(s, (60, 20, 80), (48, 48), 18)
        # 王冠
        for cx in [36, 44, 52, 60]:
            pygame.draw.polygon(s, (180, 60, 255), [(cx, 12), (cx + 4, 4), (cx + 8, 12)])
        pygame.draw.rect(s, (140, 40, 200), (34, 12, 28, 4))
        # 双眼
        pygame.draw.rect(s, (255, 0, 0), (38, 40, 6, 4))
        pygame.draw.rect(s, (255, 0, 0), (52, 40, 6, 4))
        pygame.draw.rect(s, (255, 200, 200), (40, 41, 2, 2))
        pygame.draw.rect(s, (255, 200, 200), (54, 41, 2, 2))
        # 暗网光环
        for i in range(12):
            rad = math.radians(i * 30)
            ex = int(48 + 44 * math.cos(rad))
            ey = int(48 + 44 * math.sin(rad))
            c = [(180, 60, 255), (120, 0, 200), (255, 0, 150)][i % 3]
            pygame.draw.line(s, c, (48, 48), (ex, ey), 1)
            pygame.draw.circle(s, c, (ex, ey), 2)
        # 符文碎片
        for _ in range(10):
            rx, ry = random.randint(10, 86), random.randint(10, 86)
            pygame.draw.rect(s, (180, 60, 255), (rx, ry, 2, 2))
        self.enemy_sprites['darknet_lord'] = s

    def _gen_items(self):
        # --- hp_potion → 纳米注射器: 注射器形状, 红色液体 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 针管
        pygame.draw.rect(s, (140, 150, 170), (10, 4, 4, 16))
        # 红色液体
        pygame.draw.rect(s, (255, 40, 80), (11, 8, 2, 8))
        # 针头
        pygame.draw.rect(s, (180, 190, 200), (11, 20, 2, 3))
        # 推杆
        pygame.draw.rect(s, (120, 130, 150), (9, 3, 6, 2))
        pygame.draw.rect(s, (100, 110, 130), (11, 2, 2, 2))
        # 刻度线
        pygame.draw.line(s, (0, 200, 160), (14, 8), (14, 10))
        pygame.draw.line(s, (0, 200, 160), (14, 12), (14, 14))
        self.item_icons['hp_potion'] = s

        # --- mp_potion → 能量电池: 电池形状, 蓝色发光 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 电池外壳
        pygame.draw.rect(s, (60, 70, 90), (7, 6, 10, 14))
        pygame.draw.rect(s, (80, 90, 110), (7, 6, 10, 14), 1)
        # 正极
        pygame.draw.rect(s, (100, 110, 130), (9, 4, 6, 3))
        # 蓝色能量
        pygame.draw.rect(s, (0, 140, 255), (9, 9, 6, 8))
        pygame.draw.rect(s, (40, 180, 255), (10, 10, 4, 6))
        # 发光
        pygame.draw.rect(s, (100, 200, 255), (11, 11, 2, 4))
        self.item_icons['mp_potion'] = s

        # --- iron_sword → 等离子刀: 发光青色刀刃 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 刀刃 - 青色发光
        pygame.draw.rect(s, (0, 255, 200), (11, 2, 2, 12))
        pygame.draw.rect(s, (0, 200, 160), (10, 2, 4, 12))
        # 刀尖
        pygame.draw.polygon(s, (0, 255, 220), [(12, 0), (10, 4), (14, 4)])
        # 护手
        pygame.draw.rect(s, (100, 110, 130), (8, 14, 8, 2))
        # 手柄
        pygame.draw.rect(s, (50, 55, 65), (10, 16, 4, 5))
        pygame.draw.rect(s, (0, 180, 150), (11, 17, 2, 1))
        # 底部
        pygame.draw.rect(s, (80, 90, 100), (9, 21, 6, 2))
        self.item_icons['iron_sword'] = s

        # --- magic_ring → 神经接口: 电路环 + 芯片 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 电路环
        pygame.draw.circle(s, (80, 90, 110), (12, 12), 7, 2)
        pygame.draw.circle(s, (0, 200, 180), (12, 12), 7, 1)
        # 芯片
        pygame.draw.rect(s, (0, 255, 200), (10, 5, 4, 4))
        pygame.draw.rect(s, (0, 200, 160), (11, 6, 2, 2))
        # 电路线
        pygame.draw.line(s, (0, 180, 150), (8, 8), (6, 6))
        pygame.draw.line(s, (0, 180, 150), (16, 8), (18, 6))
        self.item_icons['magic_ring'] = s

        # --- shield → 能量护盾: 六角盾, 蓝色发光 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 六角形
        pts = [(12, 2), (20, 6), (20, 16), (12, 22), (4, 16), (4, 6)]
        pygame.draw.polygon(s, (20, 40, 80), pts)
        pygame.draw.polygon(s, (0, 180, 255), pts, 2)
        # 内部发光
        inner = [(12, 6), (17, 8), (17, 14), (12, 18), (7, 14), (7, 8)]
        pygame.draw.polygon(s, (40, 100, 180), inner)
        pygame.draw.polygon(s, (0, 200, 255), inner, 1)
        # 中心
        pygame.draw.rect(s, (100, 200, 255), (10, 10, 4, 4))
        self.item_icons['shield'] = s

        # --- elixir → 系统重启: 金色芯片/卡 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 芯片卡
        pygame.draw.rect(s, (180, 150, 40), (6, 5, 12, 14))
        pygame.draw.rect(s, (220, 190, 60), (6, 5, 12, 14), 1)
        # 芯片图案
        pygame.draw.rect(s, (255, 220, 80), (9, 8, 6, 6))
        pygame.draw.rect(s, (200, 170, 40), (10, 9, 4, 4))
        # 引脚
        for py in [8, 10, 12]:
            pygame.draw.line(s, (220, 190, 60), (6, py), (4, py))
            pygame.draw.line(s, (220, 190, 60), (17, py), (19, py))
        # 发光
        pygame.draw.rect(s, (255, 255, 200), (11, 10, 2, 2))
        self.item_icons['elixir'] = s

        # --- lucky_coin → 加密货币: 数字硬币 + 电路图案 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 硬币
        pygame.draw.circle(s, (0, 200, 180), (12, 12), 9)
        pygame.draw.circle(s, (0, 160, 140), (12, 12), 9, 2)
        pygame.draw.circle(s, (0, 255, 200), (12, 12), 7, 1)
        # 电路图案
        pygame.draw.line(s, (0, 255, 220), (8, 12), (16, 12))
        pygame.draw.line(s, (0, 255, 220), (12, 8), (12, 16))
        pygame.draw.rect(s, (0, 255, 220), (10, 10, 4, 4), 1)
        self.item_icons['lucky_coin'] = s

        # --- emp_grenade → EMP 手雷: 小球体, 黄色电弧 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 球体
        pygame.draw.circle(s, (60, 65, 80), (12, 12), 7)
        pygame.draw.circle(s, (80, 85, 100), (12, 12), 5)
        # 黄色电弧
        pygame.draw.line(s, (255, 255, 0), (5, 8), (8, 12), 1)
        pygame.draw.line(s, (255, 255, 0), (8, 12), (5, 16), 1)
        pygame.draw.line(s, (255, 220, 0), (19, 6), (16, 10), 1)
        pygame.draw.line(s, (255, 220, 0), (16, 10), (19, 14), 1)
        pygame.draw.line(s, (255, 240, 0), (10, 3), (12, 7), 1)
        pygame.draw.line(s, (255, 240, 0), (14, 17), (12, 21), 1)
        # 顶部引信
        pygame.draw.rect(s, (140, 150, 170), (10, 4, 4, 3))
        # 中心发光
        pygame.draw.rect(s, (255, 255, 150), (10, 10, 4, 4))
        self.item_icons['emp_grenade'] = s

        # --- quantum_chip → 量子芯片: 紫色发光芯片 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        # 芯片基板
        pygame.draw.rect(s, (40, 20, 60), (6, 6, 12, 12))
        pygame.draw.rect(s, (60, 30, 80), (6, 6, 12, 12), 1)
        # 内核发光
        pygame.draw.rect(s, (180, 60, 255), (9, 9, 6, 6))
        pygame.draw.rect(s, (220, 100, 255), (10, 10, 4, 4))
        pygame.draw.rect(s, (255, 180, 255), (11, 11, 2, 2))
        # 引脚
        for px in [8, 10, 12, 14]:
            pygame.draw.line(s, (140, 50, 200), (px, 6), (px, 3))
            pygame.draw.line(s, (140, 50, 200), (px, 17), (px, 20))
        for py_val in [8, 10, 12, 14]:
            pygame.draw.line(s, (140, 50, 200), (6, py_val), (3, py_val))
            pygame.draw.line(s, (140, 50, 200), (17, py_val), (20, py_val))
        self.item_icons['quantum_chip'] = s

        # --- precision_gear: 精密齿轮 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (140, 130, 110), (12, 12), 8)
        pygame.draw.circle(s, (100, 90, 75), (12, 12), 5)
        pygame.draw.circle(s, (60, 55, 45), (12, 12), 2)
        for i in range(8):
            import math as _m
            rad = _m.radians(i * 45)
            ex = int(12 + 9 * _m.cos(rad))
            ey = int(12 + 9 * _m.sin(rad))
            pygame.draw.rect(s, (160, 150, 130), (ex - 1, ey - 1, 3, 3))
        self.item_icons['precision_gear'] = s

        # --- data_sample: 数据样本 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (20, 40, 60), (6, 4, 12, 16))
        pygame.draw.rect(s, (0, 180, 200), (6, 4, 12, 16), 1)
        for y in range(6, 18, 2):
            pygame.draw.line(s, (0, 200, 220), (8, y), (16, y))
        pygame.draw.rect(s, (0, 255, 220), (10, 9, 4, 4))
        self.item_icons['data_sample'] = s

        # --- encrypted_data: 加密数据 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 20, 50), (5, 5, 14, 14))
        pygame.draw.rect(s, (140, 50, 200), (5, 5, 14, 14), 1)
        # 锁图标
        pygame.draw.rect(s, (180, 60, 255), (9, 10, 6, 6))
        pygame.draw.arc(s, (180, 60, 255), (9, 6, 6, 8), 0, 3.14, 1)
        self.item_icons['encrypted_data'] = s

        # --- worker_id: 工人证件 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 170, 150), (5, 4, 14, 16))
        pygame.draw.rect(s, (140, 130, 110), (5, 4, 14, 16), 1)
        pygame.draw.rect(s, (100, 140, 180), (8, 7, 8, 6))  # 照片区
        pygame.draw.line(s, (80, 80, 80), (7, 15), (17, 15))
        pygame.draw.line(s, (80, 80, 80), (7, 17), (14, 17))
        self.item_icons['worker_id'] = s

        # --- plasma_rifle: 等离子步枪 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (80, 80, 100), (3, 10, 18, 5))
        pygame.draw.rect(s, (60, 60, 80), (3, 15, 5, 5))  # 握把
        pygame.draw.rect(s, (0, 200, 255), (18, 11, 4, 3))  # 枪口发光
        pygame.draw.rect(s, (100, 220, 255), (19, 12, 2, 1))
        self.item_icons['plasma_rifle'] = s

        # --- nano_armor: 纳米装甲 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 60, 80), (7, 5, 10, 14))
        pygame.draw.rect(s, (60, 100, 140), (7, 5, 10, 14), 1)
        # 肩甲
        pygame.draw.rect(s, (50, 80, 110), (4, 5, 4, 4))
        pygame.draw.rect(s, (50, 80, 110), (16, 5, 4, 4))
        # 纳米纹理
        for y in range(7, 17, 2):
            pygame.draw.line(s, (80, 140, 180), (9, y), (15, y))
        self.item_icons['nano_armor'] = s

        # --- hacker_gloves: 黑客手套 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (30, 30, 40), (6, 8, 12, 12))
        pygame.draw.rect(s, (0, 200, 180), (6, 8, 12, 12), 1)
        # 手指
        for fx in [7, 10, 13, 16]:
            pygame.draw.rect(s, (35, 35, 45), (fx, 5, 2, 4))
        # 电路
        pygame.draw.line(s, (0, 255, 200), (8, 12), (16, 12))
        pygame.draw.rect(s, (0, 255, 200), (11, 14, 2, 2))
        self.item_icons['hacker_gloves'] = s

        # --- antivirus: 解毒程序 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 180, 100), (12, 12), 8)
        pygame.draw.circle(s, (0, 220, 130), (12, 12), 5)
        # 盾牌+号
        pygame.draw.line(s, (255, 255, 255), (12, 8), (12, 16), 2)
        pygame.draw.line(s, (255, 255, 255), (8, 12), (16, 12), 2)
        self.item_icons['antivirus'] = s

        # --- quantum_blade: 量子之刃 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 60, 255), (10, 1, 4, 14))
        pygame.draw.rect(s, (220, 100, 255), (11, 2, 2, 12))
        pygame.draw.polygon(s, (255, 150, 255), [(12, 0), (9, 4), (15, 4)])
        pygame.draw.rect(s, (100, 110, 130), (8, 15, 8, 2))
        pygame.draw.rect(s, (60, 20, 80), (10, 17, 4, 4))
        self.item_icons['quantum_blade'] = s

        # --- nano_amplifier: 纳米增幅器 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (0, 200, 180), (12, 12), 8)
        pygame.draw.circle(s, (0, 255, 220), (12, 12), 5)
        pygame.draw.circle(s, (180, 60, 255), (12, 12), 2)
        pygame.draw.circle(s, (0, 200, 180), (12, 12), 10, 1)
        self.item_icons['nano_amplifier'] = s

        # --- virus_shield: 病毒护盾 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.polygon(s, (40, 80, 40), [(12, 2), (22, 8), (20, 20), (12, 22), (4, 20), (2, 8)])
        pygame.draw.polygon(s, (60, 120, 60), [(12, 4), (20, 9), (18, 19), (12, 20), (6, 19), (4, 9)])
        pygame.draw.rect(s, (0, 255, 100), (10, 10, 4, 4))
        self.item_icons['virus_shield'] = s

        # --- overclock_core: 超频核心 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (80, 20, 20), (6, 6, 12, 12))
        pygame.draw.rect(s, (200, 50, 50), (8, 8, 8, 8))
        pygame.draw.rect(s, (255, 150, 50), (10, 10, 4, 4))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            pygame.draw.line(s, (255, 100, 0), (12, 12), (12 + dx * 10, 12 + dy * 10), 1)
        self.item_icons['overclock_core'] = s

        # --- life_spring: 生命之泉 ---
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 100, 200), (4, 8, 16, 14))
        pygame.draw.ellipse(s, (0, 180, 255), (6, 10, 12, 10))
        pygame.draw.rect(s, (200, 255, 200), (10, 4, 4, 6))
        pygame.draw.circle(s, (255, 255, 255), (12, 4), 2)
        self.item_icons['life_spring'] = s
