#!/usr/bin/env python3
"""
像素风 RPG 游戏 - 完整单文件版本
使用 pygame，所有素材程序化生成
"""

import pygame
import sys
import math
import random
import time
import json
import os
import traceback
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save.json')

# ============================================================
# 常量
# ============================================================
SCREEN_W, SCREEN_H = 960, 640
TILE = 32
FPS = 60

# 颜色
C_BLACK = (0, 0, 0)
C_WHITE = (255, 255, 255)
C_RED = (220, 50, 50)
C_GREEN = (50, 200, 80)
C_BLUE = (60, 100, 220)
C_YELLOW = (255, 220, 50)
C_GOLD = (255, 200, 50)
C_DARK = (20, 20, 30)
C_PANEL = (30, 25, 45)
C_PANEL_BORDER = (120, 100, 160)
C_HP_BAR = (220, 40, 40)
C_MP_BAR = (50, 100, 230)
C_EXP_BAR = (50, 200, 100)

# ============================================================
# 工具函数
# ============================================================
def lerp(a, b, t):
    return a + (b - a) * max(0, min(1, t))

def lerp_color(c1, c2, t):
    t = max(0, min(1, t))
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def draw_pixel_rect(surf, color, rect, border=2, border_color=None):
    """绘制像素风格矩形面板"""
    x, y, w, h = rect
    if border_color is None:
        border_color = tuple(min(255, c + 60) for c in color)
    pygame.draw.rect(surf, color, (x, y, w, h))
    pygame.draw.rect(surf, border_color, (x, y, w, h), border)
    # 高光
    hl = tuple(min(255, c + 30) for c in color)
    pygame.draw.line(surf, hl, (x + border, y + border), (x + w - border, y + border))
    pygame.draw.line(surf, hl, (x + border, y + border), (x + border, y + h - border))

def draw_text(surf, text, pos, font, color=C_WHITE, shadow=True, center=False):
    if shadow:
        s = font.render(text, False, (0, 0, 0))
        if center:
            sr = s.get_rect(center=(pos[0]+1, pos[1]+1))
            surf.blit(s, sr)
        else:
            surf.blit(s, (pos[0]+1, pos[1]+1))
    r = font.render(text, False, color)
    if center:
        rr = r.get_rect(center=pos)
        surf.blit(r, rr)
    else:
        surf.blit(r, pos)

def draw_bar(surf, x, y, w, h, ratio, color, bg=(40, 40, 40)):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    if ratio > 0:
        pygame.draw.rect(surf, color, (x, y, int(w * ratio), h))
    pygame.draw.rect(surf, (180, 180, 180), (x, y, w, h), 1)

# ============================================================
# 程序化素材生成
# ============================================================
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
        # 草地
        s = pygame.Surface((TILE, TILE))
        s.fill((80, 160, 60))
        for _ in range(12):
            px, py = random.randint(0, TILE-1), random.randint(0, TILE-1)
            c = random.choice([(70, 150, 50), (90, 170, 65), (60, 140, 45)])
            s.set_at((px, py), c)
        self.tiles['grass'] = s

        # 草地变体
        s2 = s.copy()
        for _ in range(5):
            bx = random.randint(2, TILE-4)
            for dy in range(3):
                s2.set_at((bx, TILE-4-dy), (50, 130, 40))
                s2.set_at((bx+1, TILE-5-dy), (60, 140, 45))
        self.tiles['grass2'] = s2

        # 路径
        s = pygame.Surface((TILE, TILE))
        s.fill((180, 160, 120))
        for _ in range(15):
            px, py = random.randint(0, TILE-1), random.randint(0, TILE-1)
            c = random.choice([(170, 150, 110), (190, 170, 130), (160, 140, 100)])
            s.set_at((px, py), c)
        self.tiles['path'] = s

        # 水
        for frame in range(4):
            s = pygame.Surface((TILE, TILE))
            base_b = 160 + frame * 10
            s.fill((40, 80, base_b))
            for _ in range(8):
                px = random.randint(0, TILE-1)
                py = (random.randint(0, TILE-1) + frame * 3) % TILE
                s.set_at((px, py), (80, 140, min(255, base_b + 40)))
            self.tiles[f'water_{frame}'] = s

        # 石墙
        s = pygame.Surface((TILE, TILE))
        s.fill((80, 75, 70))
        for bx in range(0, TILE, 8):
            for by in range(0, TILE, 6):
                off = 4 if (by // 6) % 2 else 0
                c = random.choice([(75, 70, 65), (85, 80, 75), (70, 65, 60)])
                pygame.draw.rect(s, c, (bx + off, by, 7, 5))
                pygame.draw.rect(s, (60, 55, 50), (bx + off, by, 7, 5), 1)
        self.tiles['wall'] = s

        # 地牢地板
        s = pygame.Surface((TILE, TILE))
        s.fill((55, 50, 60))
        for _ in range(10):
            px, py = random.randint(0, TILE-1), random.randint(0, TILE-1)
            s.set_at((px, py), random.choice([(50, 45, 55), (60, 55, 65)]))
        self.tiles['dungeon_floor'] = s

        # 树
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (100, 70, 40), (13, 20, 6, 12))
        for dy in range(0, 18, 2):
            w = max(2, 16 - abs(dy - 8) * 2)
            x = 16 - w // 2
            c = (30 + dy * 2, 100 + dy * 3, 20 + dy)
            pygame.draw.rect(s, c, (x, 2 + dy, w, 3))
        self.tiles['tree'] = s

        # 花
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        colors = [(220, 80, 80), (220, 180, 50), (180, 80, 220), (80, 180, 220)]
        for _ in range(3):
            fx, fy = random.randint(4, TILE-4), random.randint(4, TILE-4)
            fc = random.choice(colors)
            pygame.draw.rect(s, fc, (fx-1, fy-1, 3, 3))
            pygame.draw.rect(s, (50, 140, 50), (fx, fy+2, 1, 3))
        self.tiles['flower'] = s

        # 房屋
        s = pygame.Surface((TILE*2, TILE*2), pygame.SRCALPHA)
        pygame.draw.rect(s, (160, 120, 80), (4, 20, 56, 40))
        pygame.draw.rect(s, (120, 80, 50), (4, 20, 56, 40), 2)
        # 屋顶
        for i in range(20):
            w = 60 - i * 3
            if w < 4: break
            x = 2 + i * 1.5
            pygame.draw.rect(s, (180, 60, 40), (int(x), 2 + i, w, 2))
        # 门
        pygame.draw.rect(s, (80, 50, 30), (24, 38, 14, 22))
        pygame.draw.rect(s, (200, 180, 50), (35, 48, 2, 2))
        # 窗
        pygame.draw.rect(s, (100, 180, 220), (10, 32, 10, 10))
        pygame.draw.rect(s, (80, 60, 40), (10, 32, 10, 10), 1)
        pygame.draw.rect(s, (100, 180, 220), (44, 32, 10, 10))
        pygame.draw.rect(s, (80, 60, 40), (44, 32, 10, 10), 1)
        self.tiles['house'] = s

        # 宝箱
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (140, 90, 30), (8, 14, 16, 12))
        pygame.draw.rect(s, (180, 120, 40), (8, 10, 16, 6))
        pygame.draw.rect(s, (100, 60, 20), (8, 14, 16, 12), 1)
        pygame.draw.rect(s, (255, 220, 50), (14, 16, 4, 4))
        self.tiles['chest'] = s

        # 门口
        s = pygame.Surface((TILE, TILE))
        s.fill((55, 50, 60))
        pygame.draw.rect(s, (80, 60, 40), (8, 0, 16, 28))
        pygame.draw.rect(s, (60, 40, 25), (8, 0, 16, 28), 1)
        self.tiles['door'] = s

    def _gen_player(self):
        """生成玩家四方向行走帧"""
        dirs = ['down', 'left', 'right', 'up']
        body_color = (60, 120, 200)
        hair_color = (80, 50, 30)
        skin_color = (240, 200, 160)

        for d in dirs:
            frames = []
            for frame in range(4):
                s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
                # 身体
                pygame.draw.rect(s, body_color, (10, 14, 12, 12))
                # 头
                pygame.draw.rect(s, skin_color, (11, 4, 10, 10))
                # 头发
                pygame.draw.rect(s, hair_color, (10, 3, 12, 5))
                # 眼睛
                if d == 'down':
                    s.set_at((13, 9), C_BLACK)
                    s.set_at((18, 9), C_BLACK)
                elif d == 'up':
                    pass
                elif d == 'left':
                    s.set_at((12, 9), C_BLACK)
                else:
                    s.set_at((19, 9), C_BLACK)
                # 腿 - 动画
                leg_off = [-1, 0, 1, 0][frame]
                pygame.draw.rect(s, (50, 50, 120), (12 + leg_off, 26, 4, 4))
                pygame.draw.rect(s, (50, 50, 120), (17 - leg_off, 26, 4, 4))
                # 剑（右手）
                if d == 'right':
                    pygame.draw.rect(s, (180, 180, 190), (24, 14, 3, 10))
                    pygame.draw.rect(s, (200, 170, 50), (23, 12, 5, 3))
                elif d == 'down':
                    pygame.draw.rect(s, (180, 180, 190), (22, 16, 3, 10))
                    pygame.draw.rect(s, (200, 170, 50), (21, 14, 5, 3))
                frames.append(s)
            self.player_frames[d] = frames

    def _gen_npcs(self):
        npc_defs = {
            'elder': ((150, 100, 50), (200, 200, 200), (220, 190, 160)),
            'merchant': ((50, 140, 50), (100, 60, 30), (230, 200, 160)),
            'guard': ((120, 120, 130), (40, 40, 50), (220, 190, 150)),
            'witch': ((100, 40, 120), (60, 20, 80), (200, 180, 200)),
        }
        for name, (body, hair, skin) in npc_defs.items():
            s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
            pygame.draw.rect(s, body, (10, 14, 12, 12))
            pygame.draw.rect(s, skin, (11, 4, 10, 10))
            pygame.draw.rect(s, hair, (10, 3, 12, 5))
            s.set_at((13, 9), C_BLACK)
            s.set_at((18, 9), C_BLACK)
            pygame.draw.rect(s, body, (12, 26, 4, 4))
            pygame.draw.rect(s, body, (17, 26, 4, 4))
            if name == 'elder':
                pygame.draw.rect(s, (200, 170, 50), (8, 2, 16, 3))
            elif name == 'witch':
                for i in range(5):
                    pygame.draw.rect(s, (60, 20, 80), (12 - i, 1 + i, 8 + i*2, 1))
            self.npc_sprites[name] = s

        # 幽灵商人（半透明紫色）
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (120, 80, 180, 160), (10, 14, 12, 12))
        pygame.draw.rect(s, (180, 160, 220, 160), (11, 4, 10, 10))
        pygame.draw.rect(s, (80, 40, 120, 160), (10, 3, 12, 5))
        s.set_at((13, 9), (255, 255, 255, 200))
        s.set_at((18, 9), (255, 255, 255, 200))
        pygame.draw.rect(s, (120, 80, 180, 120), (12, 26, 4, 4))
        pygame.draw.rect(s, (120, 80, 180, 120), (17, 26, 4, 4))
        # 斗篷
        for i in range(3):
            pygame.draw.rect(s, (80, 40, 120, 100), (9 - i, 14 + i*4, 14 + i*2, 4))
        self.npc_sprites['ghost_merchant'] = s

    def _gen_enemies(self):
        # 史莱姆
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for y in range(10, 28):
            w = max(0, 20 - abs(y - 20) * 2)
            x = 16 - w // 2
            g = 180 + (y - 10) * 2
            pygame.draw.rect(s, (40, g, 60), (x, y, w, 1))
        s.set_at((12, 17), C_WHITE)
        s.set_at((13, 17), C_WHITE)
        s.set_at((19, 17), C_WHITE)
        s.set_at((20, 17), C_WHITE)
        s.set_at((12, 18), C_BLACK)
        s.set_at((20, 18), C_BLACK)
        self.enemy_sprites['slime'] = s

        # 骷髅
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (220, 220, 210), (11, 4, 10, 10))
        pygame.draw.rect(s, C_BLACK, (12, 7, 3, 3))
        pygame.draw.rect(s, C_BLACK, (17, 7, 3, 3))
        pygame.draw.rect(s, C_BLACK, (14, 11, 4, 2))
        pygame.draw.rect(s, (200, 200, 190), (12, 14, 8, 10))
        pygame.draw.rect(s, (200, 200, 190), (10, 16, 3, 6))
        pygame.draw.rect(s, (200, 200, 190), (19, 16, 3, 6))
        pygame.draw.rect(s, (200, 200, 190), (13, 24, 3, 6))
        pygame.draw.rect(s, (200, 200, 190), (17, 24, 3, 6))
        self.enemy_sprites['skeleton'] = s

        # 暗影龙
        s = pygame.Surface((TILE*2, TILE*2), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 20, 80), (16, 20, 32, 28))
        pygame.draw.rect(s, (80, 30, 100), (20, 8, 20, 16))
        pygame.draw.rect(s, (255, 50, 50), (24, 12, 4, 4))
        pygame.draw.rect(s, (255, 50, 50), (34, 12, 4, 4))
        # 翅膀
        for i in range(8):
            pygame.draw.rect(s, (50, 15, 70), (4 - i, 18 + i, 14, 2))
            pygame.draw.rect(s, (50, 15, 70), (46 + i, 18 + i, 14, 2))
        # 尾巴
        for i in range(6):
            pygame.draw.rect(s, (55, 18, 75), (22 + i*2, 48 + i, 8 - i, 3))
        self.enemy_sprites['dragon'] = s

        # 蝙蝠
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        pygame.draw.rect(s, (60, 40, 60), (13, 12, 6, 8))
        pygame.draw.rect(s, (255, 100, 100), (14, 14, 2, 2))
        pygame.draw.rect(s, (255, 100, 100), (17, 14, 2, 2))
        for i in range(5):
            pygame.draw.rect(s, (50, 30, 50), (4 + i, 10 + i, 8 - i, 2))
            pygame.draw.rect(s, (50, 30, 50), (21 - i, 10 + i, 8 - i, 2))
        self.enemy_sprites['bat'] = s

        # 金色史莱姆
        s = pygame.Surface((TILE, TILE), pygame.SRCALPHA)
        for y in range(10, 28):
            w = max(0, 20 - abs(y - 20) * 2)
            x = 16 - w // 2
            g = 200 + (y - 10) * 2
            r = 220 + (y - 10)
            pygame.draw.rect(s, (min(255, r), min(255, g), 50), (x, y, w, 1))
        s.set_at((12, 17), C_WHITE)
        s.set_at((13, 17), C_WHITE)
        s.set_at((19, 17), C_WHITE)
        s.set_at((20, 17), C_WHITE)
        s.set_at((12, 18), C_BLACK)
        s.set_at((20, 18), C_BLACK)
        # 金色光芒
        pygame.draw.rect(s, (255, 240, 100), (14, 8, 4, 3))
        self.enemy_sprites['golden_slime'] = s

    def _gen_items(self):
        # 生命药水
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (200, 40, 40), (8, 6, 8, 14))
        pygame.draw.rect(s, (220, 60, 60), (10, 4, 4, 4))
        pygame.draw.rect(s, (255, 100, 100), (10, 8, 4, 4))
        self.item_icons['hp_potion'] = s

        # 魔法药水
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (40, 60, 200), (8, 6, 8, 14))
        pygame.draw.rect(s, (60, 80, 220), (10, 4, 4, 4))
        pygame.draw.rect(s, (100, 140, 255), (10, 8, 4, 4))
        self.item_icons['mp_potion'] = s

        # 铁剑
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 180, 200), (11, 2, 2, 14))
        pygame.draw.rect(s, (140, 100, 40), (8, 16, 8, 3))
        pygame.draw.rect(s, (100, 70, 30), (10, 19, 4, 4))
        self.item_icons['iron_sword'] = s

        # 魔法戒指
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (200, 170, 50), (12, 12), 6, 2)
        pygame.draw.rect(s, (100, 200, 255), (10, 6, 4, 4))
        self.item_icons['magic_ring'] = s

        # 盾牌
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        for i in range(12):
            w = max(2, 14 - i)
            pygame.draw.rect(s, (100, 80, 50), (12 - w//2, 4 + i, w, 2))
        pygame.draw.rect(s, (200, 170, 50), (10, 8, 4, 4))
        self.item_icons['shield'] = s

        # 万能药水
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.rect(s, (180, 50, 200), (8, 6, 8, 14))
        pygame.draw.rect(s, (200, 80, 220), (10, 4, 4, 4))
        pygame.draw.rect(s, (255, 150, 255), (10, 8, 4, 4))
        self.item_icons['elixir'] = s

        # 幸运金币
        s = pygame.Surface((24, 24), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 200, 50), (12, 12), 8)
        pygame.draw.circle(s, (200, 160, 30), (12, 12), 8, 2)
        pygame.draw.rect(s, (200, 160, 30), (10, 9, 4, 6))
        self.item_icons['lucky_coin'] = s


# ============================================================
# 粒子系统
# ============================================================
class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'kind']
    def __init__(self, x, y, vx, vy, life, color, size=2, kind='default'):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.kind = kind

class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x, y, count=1, color=(255,255,200), spread=1.0, life=60, size=2, kind='default'):
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread, spread)
            self.particles.append(Particle(x + random.uniform(-4,4), y + random.uniform(-4,4),
                                           vx, vy, life + random.randint(-10,10), color, size, kind))

    def update(self):
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.life -= 1
            if p.kind == 'firefly':
                p.vx += random.uniform(-0.1, 0.1)
                p.vy += random.uniform(-0.1, 0.1)
            elif p.kind == 'magic':
                p.vy -= 0.02
            elif p.kind == 'dust':
                p.vy += 0.01
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf, cam_x, cam_y):
        for p in self.particles:
            alpha = p.life / p.max_life
            sx = int(p.x - cam_x)
            sy = int(p.y - cam_y)
            if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
                c = tuple(int(p.color[i] * alpha) for i in range(3))
                sz = max(1, int(p.size * alpha))
                if p.kind == 'firefly':
                    glow = pygame.Surface((sz*4, sz*4), pygame.SRCALPHA)
                    a = int(120 * alpha)
                    pygame.draw.circle(glow, (*p.color, a), (sz*2, sz*2), sz*2)
                    pygame.draw.circle(glow, (*C_WHITE, min(255, a+60)), (sz*2, sz*2), sz)
                    surf.blit(glow, (sx - sz*2, sy - sz*2))
                else:
                    pygame.draw.rect(surf, c, (sx, sy, sz, sz))

# ============================================================
# 地图数据
# ============================================================
# 图块类型: 0=草, 1=路, 2=水, 3=墙, 4=树, 5=地牢地板, 6=花, 7=门
AREA_VILLAGE = 'village'
AREA_FOREST = 'forest'
AREA_DUNGEON = 'dungeon'

class GameMap:
    def __init__(self):
        self.maps: Dict[str, List[List[int]]] = {}
        self.map_w: Dict[str, int] = {}
        self.map_h: Dict[str, int] = {}
        self.transitions: Dict[str, List[Tuple]] = {}  # area -> [(x,y,target_area,tx,ty)]
        self._generate_maps()

    def _generate_maps(self):
        self._gen_village()
        self._gen_forest()
        self._gen_dungeon()

    def _gen_village(self):
        W, H = 40, 30
        m = [[0]*W for _ in range(H)]
        # 路径
        for x in range(W):
            m[14][x] = 1
            m[15][x] = 1
        for y in range(H):
            m[y][20] = 1
            m[y][21] = 1
        # 水池
        for y in range(8, 12):
            for x in range(5, 10):
                m[y][x] = 2
        # 花
        for _ in range(20):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 0:
                m[fy][fx] = 6
        # 树木边界
        for x in range(W):
            if m[0][x] == 0: m[0][x] = 4
            if m[H-1][x] == 0: m[H-1][x] = 4
        for y in range(H):
            if m[y][0] == 0: m[y][0] = 4
            if m[y][W-1] == 0: m[y][W-1] = 4
        # 出口到森林（右边）
        m[14][W-1] = 1
        m[15][W-1] = 1
        self.maps[AREA_VILLAGE] = m
        self.map_w[AREA_VILLAGE] = W
        self.map_h[AREA_VILLAGE] = H
        self.transitions[AREA_VILLAGE] = [
            (W-1, 14, AREA_FOREST, 1, 14),
            (W-1, 15, AREA_FOREST, 1, 15),
        ]

    def _gen_forest(self):
        W, H = 50, 40
        m = [[0]*W for _ in range(H)]
        # 密集树木
        for _ in range(200):
            tx, ty = random.randint(0, W-1), random.randint(0, H-1)
            m[ty][tx] = 4
        # 清理路径
        for x in range(W):
            for dy in [14, 15]:
                if dy < H:
                    m[dy][x] = 1
        for y in range(H):
            m[y][25] = 1
        # 清理入口区域
        for y in range(12, 18):
            for x in range(0, 4):
                m[y][x] = 0
        # 水流
        for y in range(5, 35):
            wx = 35 + int(math.sin(y * 0.3) * 3)
            for dx in range(3):
                if 0 <= wx+dx < W:
                    m[y][wx+dx] = 2
        # 花
        for _ in range(15):
            fx, fy = random.randint(0, W-1), random.randint(0, H-1)
            if m[fy][fx] == 0:
                m[fy][fx] = 6
        # 地牢入口
        m[25][25] = 7
        # 回村庄
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
        W, H = 30, 25
        m = [[3]*W for _ in range(H)]
        # 房间
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

    def get_tile(self, area, x, y):
        m = self.maps.get(area)
        if m and 0 <= y < len(m) and 0 <= x < len(m[0]):
            return m[y][x]
        return 3  # 墙

    def is_walkable(self, area, x, y):
        t = self.get_tile(area, x, y)
        return t in (0, 1, 5, 6, 7)

    def check_transition(self, area, tx, ty):
        for t in self.transitions.get(area, []):
            if t[0] == tx and t[1] == ty:
                return t[2], t[3], t[4]
        return None


# ============================================================
# 游戏实体
# ============================================================
@dataclass
class Item:
    name: str
    icon_key: str
    description: str
    item_type: str  # 'consumable', 'weapon', 'armor', 'accessory'
    hp_restore: int = 0
    mp_restore: int = 0
    atk_bonus: int = 0
    def_bonus: int = 0

ITEMS_DB = {
    'hp_potion': Item("生命药水", "hp_potion", "恢复50点生命值", "consumable", hp_restore=50),
    'mp_potion': Item("魔法药水", "mp_potion", "恢复30点魔法值", "consumable", mp_restore=30),
    'iron_sword': Item("铁剑", "iron_sword", "攻击力+8", "weapon", atk_bonus=8),
    'magic_ring': Item("魔法戒指", "magic_ring", "魔法攻击力+5", "accessory", atk_bonus=5),
    'shield': Item("铁盾", "shield", "防御力+5", "armor", def_bonus=5),
    'elixir': Item("万能药水", "elixir", "完全恢复HP和MP", "consumable", hp_restore=9999, mp_restore=9999),
    'lucky_coin': Item("幸运金币", "lucky_coin", "攻击力+3，据说能带来好运", "accessory", atk_bonus=3),
}

@dataclass
class PlayerStats:
    level: int = 1
    hp: int = 100
    max_hp: int = 100
    mp: int = 40
    max_mp: int = 40
    atk: int = 12
    defense: int = 5
    exp: int = 0
    exp_next: int = 30
    gold: int = 50

class Player:
    def __init__(self, x, y):
        self.x = float(x * TILE)
        self.y = float(y * TILE)
        self.tx = x  # tile x
        self.ty = y  # tile y
        self.speed = 2.5
        self.direction = 'down'
        self.anim_frame = 0
        self.anim_timer = 0
        self.moving = False
        self.stats = PlayerStats()
        self.inventory: List[Tuple[str, int]] = [('hp_potion', 3), ('mp_potion', 2)]
        self.equipped: Dict[str, Optional[str]] = {'weapon': None, 'armor': None, 'accessory': None}
        self.area = AREA_VILLAGE

    def get_total_atk(self):
        bonus = sum(ITEMS_DB[v].atk_bonus for v in self.equipped.values() if v)
        return self.stats.atk + bonus

    def get_total_def(self):
        bonus = sum(ITEMS_DB[v].def_bonus for v in self.equipped.values() if v)
        return self.stats.defense + bonus

    def add_item(self, item_key, count=1):
        for i, (k, c) in enumerate(self.inventory):
            if k == item_key:
                self.inventory[i] = (k, c + count)
                return
        self.inventory.append((item_key, count))

    def remove_item(self, item_key, count=1):
        for i, (k, c) in enumerate(self.inventory):
            if k == item_key:
                if c <= count:
                    self.inventory.pop(i)
                else:
                    self.inventory[i] = (k, c - count)
                return True
        return False

    def has_item(self, item_key):
        return any(k == item_key for k, c in self.inventory)

    def use_item(self, item_key):
        item = ITEMS_DB.get(item_key)
        if not item:
            return False
        if item.item_type == 'consumable':
            if self.remove_item(item_key):
                self.stats.hp = min(self.stats.max_hp, self.stats.hp + item.hp_restore)
                self.stats.mp = min(self.stats.max_mp, self.stats.mp + item.mp_restore)
                return True
        elif item.item_type in ('weapon', 'armor', 'accessory'):
            slot = item.item_type
            old = self.equipped[slot]
            self.equipped[slot] = item_key
            if old:
                self.add_item(old)
            self.remove_item(item_key)
            return True
        return False

    def gain_exp(self, amount):
        self.stats.exp += amount
        leveled = False
        while self.stats.exp >= self.stats.exp_next:
            self.stats.exp -= self.stats.exp_next
            self.stats.level += 1
            self.stats.max_hp += 15
            self.stats.hp = self.stats.max_hp
            self.stats.max_mp += 8
            self.stats.mp = self.stats.max_mp
            self.stats.atk += 3
            self.stats.defense += 2
            self.stats.exp_next = int(self.stats.exp_next * 1.5)
            leveled = True
        return leveled

    def to_save_dict(self):
        return {
            'tx': self.tx, 'ty': self.ty, 'area': self.area,
            'direction': self.direction,
            'stats': {
                'level': self.stats.level, 'hp': self.stats.hp, 'max_hp': self.stats.max_hp,
                'mp': self.stats.mp, 'max_mp': self.stats.max_mp,
                'atk': self.stats.atk, 'defense': self.stats.defense,
                'exp': self.stats.exp, 'exp_next': self.stats.exp_next, 'gold': self.stats.gold,
            },
            'inventory': self.inventory,
            'equipped': self.equipped,
        }

    def load_save_dict(self, data):
        self.tx = data['tx']
        self.ty = data['ty']
        self.x = float(self.tx * TILE)
        self.y = float(self.ty * TILE)
        self.area = data['area']
        self.direction = data.get('direction', 'down')
        s = data['stats']
        self.stats = PlayerStats(
            level=s['level'], hp=s['hp'], max_hp=s['max_hp'],
            mp=s['mp'], max_mp=s['max_mp'], atk=s['atk'], defense=s['defense'],
            exp=s['exp'], exp_next=s['exp_next'], gold=s['gold'],
        )
        self.inventory = [tuple(i) for i in data['inventory']]
        self.equipped = data['equipped']

@dataclass
class NPC:
    x: int  # tile
    y: int  # tile
    sprite_key: str
    name: str
    dialogues: List[str]
    area: str
    shop_items: Optional[List[Tuple[str, int]]] = None  # (item_key, price)

@dataclass
class EnemyDef:
    name: str
    sprite_key: str
    hp: int
    atk: int
    defense: int
    exp: int
    gold: int
    skills: List[Tuple[str, int]] = field(default_factory=list)  # (name, power)

ENEMY_DEFS = {
    'slime': EnemyDef("史莱姆", "slime", 30, 6, 2, 18, 10,
                       [("粘液攻击", 8)]),
    'bat': EnemyDef("蝙蝠", "bat", 25, 8, 1, 20, 15,
                     [("超声波", 10)]),
    'skeleton': EnemyDef("骷髅战士", "skeleton", 60, 14, 6, 45, 30,
                          [("骨刃斩", 18), ("暗影箭", 15)]),
    'dragon': EnemyDef("暗影龙", "dragon", 200, 25, 12, 180, 150,
                        [("龙息", 35), ("暗影爪", 28), ("龙啸", 20)]),
    'golden_slime': EnemyDef("金色史莱姆", "golden_slime", 50, 10, 4, 50, 100,
                              [("黄金冲击", 15)]),
}

ENCOUNTER_TABLE = {
    AREA_VILLAGE: [],
    AREA_FOREST: ['slime', 'slime', 'bat', 'bat', 'skeleton'],
    AREA_DUNGEON: ['skeleton', 'skeleton', 'bat', 'skeleton', 'dragon'],
}


# ============================================================
# 战斗系统
# ============================================================
class CombatState(Enum):
    PLAYER_CHOOSE = auto()
    PLAYER_ATTACK = auto()
    PLAYER_SKILL = auto()
    PLAYER_ITEM = auto()
    ENEMY_TURN = auto()
    ANIM = auto()
    VICTORY = auto()
    DEFEAT = auto()
    FLEE = auto()

class Combat:
    def __init__(self, player: Player, enemy_key: str, assets: Assets):
        self.player = player
        edef = ENEMY_DEFS[enemy_key]
        self.enemy_name = edef.name
        self.enemy_sprite_key = edef.sprite_key
        self.enemy_hp = edef.hp
        self.enemy_max_hp = edef.hp
        self.enemy_atk = edef.atk
        self.enemy_def = edef.defense
        self.enemy_exp = edef.exp
        self.enemy_gold = edef.gold
        self.enemy_skills = edef.skills
        self.state = CombatState.PLAYER_CHOOSE
        self.menu_index = 0
        self.item_index = 0
        self.skill_index = 0
        self.message = f"遭遇了 {self.enemy_name}！"
        self.msg_timer = 0
        self.anim_timer = 0
        self.anim_type = ''
        self.particles = ParticleSystem()
        self.assets = assets
        self.shake_x = 0
        self.shake_y = 0
        self.player_skills = [("斩击", 15, 5), ("火球术", 25, 12), ("治愈术", 0, 8)]
        self.show_items = False
        self.show_skills = False
        self.turn_count = 0

    def handle_input(self, event):
        if self.state == CombatState.ANIM:
            return True
        if self.state in (CombatState.VICTORY, CombatState.DEFEAT, CombatState.FLEE):
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_j):
                return False  # 战斗结束
            return True

        if event.type != pygame.KEYDOWN:
            return True

        if self.state == CombatState.PLAYER_CHOOSE:
            if self.show_items:
                return self._handle_item_menu(event)
            if self.show_skills:
                return self._handle_skill_menu(event)
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % 4
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % 4
            elif event.key in (pygame.K_RETURN, pygame.K_j):
                if self.menu_index == 0:  # 攻击
                    self._player_attack()
                elif self.menu_index == 1:  # 技能
                    self.show_skills = True
                    self.skill_index = 0
                elif self.menu_index == 2:  # 物品
                    self.show_items = True
                    self.item_index = 0
                elif self.menu_index == 3:  # 逃跑
                    if random.random() < 0.5:
                        self.state = CombatState.FLEE
                        self.message = "成功逃跑了！"
                    else:
                        self.message = "逃跑失败！"
                        self._start_enemy_turn()
        return True

    def _handle_item_menu(self, event):
        consumables = [(k, c) for k, c in self.player.inventory if ITEMS_DB[k].item_type == 'consumable']
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            self.show_items = False
            return True
        if not consumables:
            self.show_items = False
            return True
        if event.key == pygame.K_UP:
            self.item_index = (self.item_index - 1) % len(consumables)
        elif event.key == pygame.K_DOWN:
            self.item_index = (self.item_index + 1) % len(consumables)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            key, cnt = consumables[self.item_index]
            item = ITEMS_DB[key]
            self.player.use_item(key)
            self.message = f"使用了{item.name}！"
            if item.hp_restore > 0:
                self.message += f" HP+{item.hp_restore}"
            if item.mp_restore > 0:
                self.message += f" MP+{item.mp_restore}"
            self.show_items = False
            self._start_enemy_turn()
        return True

    def _handle_skill_menu(self, event):
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            self.show_skills = False
            return True
        if event.key == pygame.K_UP:
            self.skill_index = (self.skill_index - 1) % len(self.player_skills)
        elif event.key == pygame.K_DOWN:
            self.skill_index = (self.skill_index + 1) % len(self.player_skills)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            name, power, cost = self.player_skills[self.skill_index]
            if self.player.stats.mp < cost:
                self.message = "魔法值不足！"
                return True
            self.player.stats.mp -= cost
            self.show_skills = False
            if name == "治愈术":
                heal = power + self.player.stats.level * 3
                self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal)
                self.message = f"使用{name}！恢复{heal}点HP！"
                self.particles.emit(SCREEN_W//2, SCREEN_H//2 - 40, 15, (100, 255, 100), 2, 40, 3, 'magic')
                self._start_enemy_turn()
            else:
                total_atk = self.player.get_total_atk() + power
                dmg = max(1, total_atk - self.enemy_def + random.randint(-3, 3))
                self.enemy_hp = max(0, self.enemy_hp - dmg)
                self.message = f"使用{name}！造成{dmg}点伤害！"
                color = (255, 100, 50) if '火' in name else (200, 200, 255)
                self.particles.emit(SCREEN_W//2 + 100, SCREEN_H//2 - 60, 20, color, 3, 40, 3, 'magic')
                self.shake_x = 8
                if self.enemy_hp <= 0:
                    self._victory()
                else:
                    self._start_enemy_turn()
        return True

    def _player_attack(self):
        total_atk = self.player.get_total_atk()
        crit = random.random() < 0.15
        dmg = max(1, total_atk - self.enemy_def + random.randint(-2, 4))
        if crit:
            dmg = int(dmg * 1.8)
        self.enemy_hp = max(0, self.enemy_hp - dmg)
        self.message = f"{'暴击！' if crit else ''}造成{dmg}点伤害！"
        self.particles.emit(SCREEN_W//2 + 100, SCREEN_H//2 - 60, 8, (255, 255, 200), 2, 30, 2)
        self.shake_x = 6
        self.anim_timer = 20
        self.anim_type = 'player_atk'
        self.state = CombatState.ANIM
        if self.enemy_hp <= 0:
            self._victory()
        else:
            self._start_enemy_turn()

    def _start_enemy_turn(self):
        self.anim_timer = 40
        self.anim_type = 'enemy_atk'
        self.state = CombatState.ANIM
        self.turn_count += 1

    def _enemy_attack(self):
        if self.enemy_skills and random.random() < 0.4:
            skill_name, skill_power = random.choice(self.enemy_skills)
            dmg = max(1, self.enemy_atk + skill_power - self.player.get_total_def() + random.randint(-3, 3))
            self.message = f"{self.enemy_name}使用了{skill_name}！造成{dmg}点伤害！"
            self.particles.emit(SCREEN_W//2 - 100, SCREEN_H//2 - 40, 12, (200, 50, 50), 2, 30, 3, 'magic')
        else:
            dmg = max(1, self.enemy_atk - self.player.get_total_def() + random.randint(-2, 3))
            self.message = f"{self.enemy_name}发动攻击！造成{dmg}点伤害！"
            self.particles.emit(SCREEN_W//2 - 100, SCREEN_H//2 - 40, 6, (255, 200, 200), 2, 25, 2)
        self.player.stats.hp = max(0, self.player.stats.hp - dmg)
        self.shake_y = 5
        if self.player.stats.hp <= 0:
            self.state = CombatState.DEFEAT
            self.message = "你被击败了..."
        else:
            self.state = CombatState.PLAYER_CHOOSE

    def _victory(self):
        self.state = CombatState.VICTORY
        leveled = self.player.gain_exp(self.enemy_exp)
        self.player.stats.gold += self.enemy_gold
        self.message = f"胜利！获得{self.enemy_exp}经验 {self.enemy_gold}金币"
        if leveled:
            self.message += f" 升级到Lv.{self.player.stats.level}！"
        # 随机掉落
        if random.random() < 0.5:
            drop = random.choice(['hp_potion', 'mp_potion'])
            self.player.add_item(drop)
            self.message += f" 获得{ITEMS_DB[drop].name}！"

    def update(self):
        self.particles.update()
        if self.shake_x > 0:
            self.shake_x *= 0.85
            if self.shake_x < 0.5: self.shake_x = 0
        if self.shake_y > 0:
            self.shake_y *= 0.85
            if self.shake_y < 0.5: self.shake_y = 0
        if self.state == CombatState.ANIM:
            self.anim_timer -= 1
            if self.anim_timer <= 0:
                if self.anim_type == 'enemy_atk':
                    self._enemy_attack()
                else:
                    if self.enemy_hp <= 0:
                        pass  # already handled
                    else:
                        self.state = CombatState.PLAYER_CHOOSE

    def draw(self, surf):
        # 战斗背景
        area = self.player.area
        if area == AREA_DUNGEON:
            for y in range(SCREEN_H):
                r = lerp(20, 40, y / SCREEN_H)
                g = lerp(15, 30, y / SCREEN_H)
                b = lerp(35, 55, y / SCREEN_H)
                pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (SCREEN_W, y))
        elif area == AREA_FOREST:
            for y in range(SCREEN_H):
                r = lerp(20, 50, y / SCREEN_H)
                g = lerp(60, 100, y / SCREEN_H)
                b = lerp(30, 50, y / SCREEN_H)
                pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (SCREEN_W, y))
        else:
            for y in range(SCREEN_H):
                r = lerp(60, 100, y / SCREEN_H)
                g = lerp(80, 140, y / SCREEN_H)
                b = lerp(120, 80, y / SCREEN_H)
                pygame.draw.line(surf, (int(r), int(g), int(b)), (0, y), (SCREEN_W, y))

        # 地面线
        pygame.draw.rect(surf, (60, 50, 40), (0, SCREEN_H//2 + 60, SCREEN_W, SCREEN_H//2 - 60))

        sx = int(random.uniform(-self.shake_x, self.shake_x))
        sy = int(random.uniform(-self.shake_y, self.shake_y))

        # 敌人
        esprite = self.assets.enemy_sprites.get(self.enemy_sprite_key)
        if esprite and self.enemy_hp > 0:
            ew, eh = esprite.get_size()
            ex = SCREEN_W//2 + 100 - ew//2 + sx
            ey = SCREEN_H//2 - 80 - eh//2 + sy
            surf.blit(esprite, (ex, ey))
            # 敌人HP条
            draw_bar(surf, ex - 10, ey - 16, ew + 20, 8, self.enemy_hp / self.enemy_max_hp, C_HP_BAR)
            draw_text(surf, self.enemy_name, (ex + ew//2, ey - 28), self.assets.font_sm, C_WHITE, center=True)

        # 玩家精灵
        pframes = self.assets.player_frames.get('right', [])
        if pframes:
            pf = pframes[0]
            px = SCREEN_W//2 - 140 + sy
            py = SCREEN_H//2 - 40
            scaled = pygame.transform.scale(pf, (TILE*2, TILE*2))
            surf.blit(scaled, (px, py))

        # 粒子
        self.particles.draw(surf, 0, 0)

        # UI面板
        panel_y = SCREEN_H - 160
        draw_pixel_rect(surf, C_PANEL, (10, panel_y, SCREEN_W - 20, 150), 2, C_PANEL_BORDER)

        # 消息
        draw_text(surf, self.message, (30, panel_y + 10), self.assets.font_md)

        # 玩家状态
        st = self.player.stats
        draw_text(surf, f"Lv.{st.level} 勇者", (30, panel_y + 38), self.assets.font_sm, C_GOLD)
        draw_bar(surf, 130, panel_y + 38, 120, 12, st.hp / st.max_hp, C_HP_BAR)
        draw_text(surf, f"HP {st.hp}/{st.max_hp}", (132, panel_y + 37), self.assets.font_sm)
        draw_bar(surf, 130, panel_y + 54, 120, 12, st.mp / st.max_mp, C_MP_BAR)
        draw_text(surf, f"MP {st.mp}/{st.max_mp}", (132, panel_y + 53), self.assets.font_sm)

        # 菜单
        if self.state == CombatState.PLAYER_CHOOSE:
            menu_x = SCREEN_W - 200
            if self.show_items:
                self._draw_item_menu(surf, menu_x, panel_y + 10)
            elif self.show_skills:
                self._draw_skill_menu(surf, menu_x, panel_y + 10)
            else:
                options = ["⚔ 攻击", "✦ 技能", "🎒 物品", "🏃 逃跑"]
                for i, opt in enumerate(options):
                    color = C_YELLOW if i == self.menu_index else C_WHITE
                    prefix = "▸ " if i == self.menu_index else "  "
                    draw_text(surf, prefix + opt, (menu_x, panel_y + 12 + i * 28), self.assets.font_md, color)

        if self.state in (CombatState.VICTORY, CombatState.DEFEAT, CombatState.FLEE):
            draw_text(surf, "按确认键继续...", (SCREEN_W//2, panel_y + 130), self.assets.font_sm, C_GOLD, center=True)

    def _draw_item_menu(self, surf, x, y):
        consumables = [(k, c) for k, c in self.player.inventory if ITEMS_DB[k].item_type == 'consumable']
        draw_text(surf, "【物品】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        if not consumables:
            draw_text(surf, "没有可用物品", (x, y + 22), self.assets.font_sm)
            return
        for i, (key, cnt) in enumerate(consumables):
            color = C_YELLOW if i == self.item_index else C_WHITE
            prefix = "▸ " if i == self.item_index else "  "
            draw_text(surf, f"{prefix}{ITEMS_DB[key].name} x{cnt}", (x, y + 22 + i * 22), self.assets.font_sm, color)

    def _draw_skill_menu(self, surf, x, y):
        draw_text(surf, "【技能】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        for i, (name, power, cost) in enumerate(self.player_skills):
            color = C_YELLOW if i == self.skill_index else C_WHITE
            if self.player.stats.mp < cost:
                color = (100, 100, 100)
            prefix = "▸ " if i == self.skill_index else "  "
            draw_text(surf, f"{prefix}{name} (MP:{cost})", (x, y + 22 + i * 22), self.assets.font_sm, color)


# ============================================================
# 对话系统
# ============================================================
class DialogueBox:
    def __init__(self, assets: Assets):
        self.assets = assets
        self.active = False
        self.npc_name = ""
        self.lines: List[str] = []
        self.line_index = 0
        self.char_index = 0
        self.char_timer = 0
        self.char_speed = 2
        self.shop_mode = False
        self.shop_items: List[Tuple[str, int]] = []
        self.shop_index = 0
        self.shop_tab = 0  # 0=买, 1=卖
        self.sell_index = 0
        self.shop_msg = ""
        self.shop_msg_timer = 0

    def start(self, npc: NPC):
        self.active = True
        self.npc_name = npc.name
        self.lines = npc.dialogues
        self.line_index = 0
        self.char_index = 0
        self.char_timer = 0
        self.shop_mode = False
        self.shop_tab = 0
        self.sell_index = 0
        self.shop_msg = ""
        self.shop_msg_timer = 0
        if npc.shop_items:
            self.shop_items = npc.shop_items
        else:
            self.shop_items = []

    def handle_input(self, event, player: Player):
        if not self.active:
            return
        if event.type != pygame.KEYDOWN:
            return
        if self.shop_mode:
            # 左右切换买/卖 tab
            if event.key == pygame.K_LEFT or event.key == pygame.K_a:
                self.shop_tab = 0
                self.shop_index = 0
            elif event.key == pygame.K_RIGHT or event.key == pygame.K_d:
                self.shop_tab = 1
                self.sell_index = 0
            elif event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
                self.active = False
            elif self.shop_tab == 0:
                # 购买
                total = len(self.shop_items) + 1  # +1 离开
                if event.key == pygame.K_UP:
                    self.shop_index = (self.shop_index - 1) % total
                elif event.key == pygame.K_DOWN:
                    self.shop_index = (self.shop_index + 1) % total
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    if self.shop_index >= len(self.shop_items):
                        self.active = False
                        return
                    item_key, price = self.shop_items[self.shop_index]
                    if player.stats.gold >= price:
                        player.stats.gold -= price
                        player.add_item(item_key)
                        self.shop_msg = f"购买了{ITEMS_DB[item_key].name}！"
                        self.shop_msg_timer = 60
                    else:
                        self.shop_msg = "金币不足！"
                        self.shop_msg_timer = 60
            else:
                # 出售
                sellable = [(k, c) for k, c in player.inventory]
                total = len(sellable) + 1  # +1 离开
                if event.key == pygame.K_UP:
                    self.sell_index = (self.sell_index - 1) % total
                elif event.key == pygame.K_DOWN:
                    self.sell_index = (self.sell_index + 1) % total
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    if self.sell_index >= len(sellable):
                        self.active = False
                        return
                    if sellable:
                        item_key, cnt = sellable[self.sell_index]
                        # 出售价 = 购买价的一半（从 shop_items 查，没有的按 15 金币）
                        base_price = 15
                        for sk, sp in self.shop_items:
                            if sk == item_key:
                                base_price = sp
                                break
                        sell_price = max(1, base_price // 2)
                        player.stats.gold += sell_price
                        player.remove_item(item_key)
                        self.shop_msg = f"卖出{ITEMS_DB[item_key].name}，获得{sell_price}金币"
                        self.shop_msg_timer = 60
                        if self.sell_index >= len(player.inventory):
                            self.sell_index = max(0, len(player.inventory) - 1)
            return

        if event.key in (pygame.K_RETURN, pygame.K_j):
            current_text = self.lines[self.line_index]
            if self.char_index < len(current_text):
                self.char_index = len(current_text)
            else:
                self.line_index += 1
                self.char_index = 0
                if self.line_index >= len(self.lines):
                    if self.shop_items:
                        self.shop_mode = True
                        self.shop_index = 0
                    else:
                        self.active = False
        elif event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            self.active = False

    def update(self):
        if not self.active:
            return
        if self.shop_msg_timer > 0:
            self.shop_msg_timer -= 1
        if self.shop_mode:
            return
        if self.line_index < len(self.lines):
            self.char_timer += 1
            if self.char_timer >= self.char_speed:
                self.char_timer = 0
                if self.char_index < len(self.lines[self.line_index]):
                    self.char_index += 1

    def draw(self, surf, player=None):
        if not self.active:
            return
        # 对话框
        bx, by, bw, bh = 40, SCREEN_H - 170, SCREEN_W - 80, 140
        draw_pixel_rect(surf, (20, 18, 40), (bx, by, bw, bh), 3, (140, 120, 180))

        # NPC名字
        name_w = self.assets.font_md.size(self.npc_name)[0] + 20
        draw_pixel_rect(surf, (40, 30, 70), (bx + 10, by - 16, name_w, 28), 2, (140, 120, 180))
        draw_text(surf, self.npc_name, (bx + 20, by - 12), self.assets.font_md, C_GOLD)

        if self.shop_mode:
            # Tab 标签：购买 / 出售
            tab_w = 80
            for ti, tab_name in enumerate(["购买", "出售"]):
                tx = bx + 20 + ti * (tab_w + 10)
                ty = by + 8
                if ti == self.shop_tab:
                    draw_pixel_rect(surf, (60, 50, 90), (tx, ty, tab_w, 22), 2, (180, 160, 220))
                    draw_text(surf, tab_name, (tx + tab_w//2, ty + 3), self.assets.font_sm, C_YELLOW, center=True)
                else:
                    draw_pixel_rect(surf, (35, 30, 55), (tx, ty, tab_w, 22), 1, (100, 90, 130))
                    draw_text(surf, tab_name, (tx + tab_w//2, ty + 3), self.assets.font_sm, (140, 140, 160), center=True)
            # ←→ 提示
            draw_text(surf, "←→切换", (bx + bw - 80, by + 12), self.assets.font_sm, (120, 120, 140))

            list_y = by + 36
            if self.shop_tab == 0:
                # 购买列表
                for i, (key, price) in enumerate(self.shop_items):
                    item = ITEMS_DB[key]
                    color = C_YELLOW if i == self.shop_index else C_WHITE
                    prefix = "▸ " if i == self.shop_index else "  "
                    affordable = "  " if player and player.stats.gold >= price else "✗ "
                    draw_text(surf, f"{prefix}{affordable}{item.name} - {price}G", (bx + 30, list_y + i * 22), self.assets.font_sm, color)
                li = len(self.shop_items)
                color = C_YELLOW if self.shop_index == li else C_WHITE
                prefix = "▸ " if self.shop_index == li else "  "
                draw_text(surf, f"{prefix}  离开", (bx + 30, list_y + li * 22), self.assets.font_sm, color)
            else:
                # 出售列表
                sellable = list(player.inventory) if player else []
                for i, (key, cnt) in enumerate(sellable):
                    item = ITEMS_DB[key]
                    base_price = 15
                    for sk, sp in self.shop_items:
                        if sk == key:
                            base_price = sp
                            break
                    sell_price = max(1, base_price // 2)
                    color = C_YELLOW if i == self.sell_index else C_WHITE
                    prefix = "▸ " if i == self.sell_index else "  "
                    draw_text(surf, f"{prefix}{item.name} x{cnt} → {sell_price}G", (bx + 30, list_y + i * 22), self.assets.font_sm, color)
                li = len(sellable)
                color = C_YELLOW if self.sell_index == li else C_WHITE
                prefix = "▸ " if self.sell_index == li else "  "
                draw_text(surf, f"{prefix}离开", (bx + 30, list_y + li * 22), self.assets.font_sm, color)
                if not sellable:
                    draw_text(surf, "没有可出售的物品", (bx + 30, list_y), self.assets.font_sm, (140, 140, 140))

            # 金币
            gold = player.stats.gold if player else 0
            draw_text(surf, f"金币: {gold}", (bx + bw - 120, by + 12), self.assets.font_sm, C_GOLD)
            # 操作提示消息
            if self.shop_msg and self.shop_msg_timer > 0:
                draw_text(surf, self.shop_msg, (bx + bw//2, by + bh - 18), self.assets.font_sm, C_GREEN, center=True)
        else:
            if self.line_index < len(self.lines):
                text = self.lines[self.line_index][:self.char_index]
                draw_text(surf, text, (bx + 20, by + 20), self.assets.font_md)
                # 提示
                if self.char_index >= len(self.lines[self.line_index]):
                    t = pygame.time.get_ticks()
                    if (t // 500) % 2:
                        draw_text(surf, "▼", (bx + bw - 30, by + bh - 25), self.assets.font_sm, C_GOLD)


# ============================================================
# 主游戏类
# ============================================================
class GameState(Enum):
    TITLE = auto()
    EXPLORE = auto()
    COMBAT = auto()
    MENU = auto()
    GAME_OVER = auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("像素冒险 - Pixel Quest")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.game_map = GameMap()
        self.player = Player(20, 16)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.state = GameState.TITLE
        self.combat: Optional[Combat] = None
        self.dialogue = DialogueBox(self.assets)
        self.particles = ParticleSystem()
        self.tick = 0
        self.encounter_steps = 0
        self.menu_index = 0
        self.inv_index = 0
        self.show_inventory = False
        self.title_blink = 0
        self.title_index = 0
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_target = None
        self.chests_opened = set()
        self.message_queue: List[Tuple[str, int]] = []

        # NPC 定义
        self.npcs = [
            NPC(18, 12, 'elder', '村长',
                ["欢迎来到像素村！", "东边的森林里有很多怪物，小心行事。", "听说森林深处有一个地牢，里面住着一条暗影龙..."],
                AREA_VILLAGE),
            NPC(25, 14, 'merchant', '商人',
                ["欢迎光临！看看有什么需要的吧。"],
                AREA_VILLAGE,
                shop_items=[('hp_potion', 20), ('mp_potion', 30), ('iron_sword', 100), ('shield', 80)]),
            NPC(15, 18, 'guard', '守卫',
                ["我负责守护村庄的安全。", "如果你要去森林，记得带足药水。", "按J键与人对话，方向键移动。"],
                AREA_VILLAGE),
            NPC(10, 10, 'witch', '魔女',
                ["呵呵...你想变强吗？", "在战斗中使用技能可以造成更多伤害。", "火球术对付史莱姆特别有效哦~"],
                AREA_FOREST),
        ]

        # 宝箱位置
        self.chest_positions = {
            (AREA_VILLAGE, 30, 10): ('iron_sword', 1),
            (AREA_FOREST, 40, 20): ('magic_ring', 1),
            (AREA_DUNGEON, 22, 18): ('hp_potion', 5),
            (AREA_DUNGEON, 6, 4): ('mp_potion', 3),
        }

        # 隐藏宝箱（随机位置，不可见）
        self.hidden_chests = {}
        self.hidden_chests_opened = set()
        self._generate_hidden_chests()

        # 幽灵商人（森林中随机位置）
        self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
        self.ghost_merchant_npc = NPC(
            self.ghost_merchant_pos[0], self.ghost_merchant_pos[1],
            'ghost_merchant', '幽灵商人',
            ["嘿嘿...你能看到我？", "我有些稀有的好东西...要看看吗？"],
            AREA_FOREST,
            shop_items=[('elixir', 200), ('lucky_coin', 150), ('hp_potion', 10), ('mp_potion', 15)],
        )

        # 随机事件步数计数
        self.random_event_steps = 0

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self._handle_event(event)
            self._update()
            self._draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _handle_event(self, event):
        if self.state == GameState.TITLE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.title_index = (self.title_index - 1) % 2
                elif event.key == pygame.K_DOWN:
                    self.title_index = (self.title_index + 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    if self.title_index == 0:  # 新游戏
                        self.state = GameState.EXPLORE
                    elif self.title_index == 1 and os.path.exists(SAVE_PATH):  # 读取存档
                        self._load_game()
        elif self.state == GameState.EXPLORE:
            if self.dialogue.active:
                self.dialogue.handle_input(event, self.player)
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                    self.menu_index = 0
                    self.show_inventory = False
                elif event.key == pygame.K_j:
                    self._interact()
        elif self.state == GameState.COMBAT:
            if self.combat:
                still_fighting = self.combat.handle_input(event)
                if not still_fighting:
                    if self.combat.state == CombatState.DEFEAT:
                        self.state = GameState.GAME_OVER
                    else:
                        self.state = GameState.EXPLORE
                    self.combat = None
        elif self.state == GameState.MENU:
            self._handle_menu_event(event)
        elif self.state == GameState.GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_j):
                self._restart()

    def _handle_menu_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.show_inventory:
            items = self.player.inventory
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
                self.show_inventory = False
            elif items:
                if event.key == pygame.K_UP:
                    self.inv_index = (self.inv_index - 1) % len(items)
                elif event.key == pygame.K_DOWN:
                    self.inv_index = (self.inv_index + 1) % len(items)
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    key, cnt = items[self.inv_index]
                    self.player.use_item(key)
                    if self.inv_index >= len(self.player.inventory):
                        self.inv_index = max(0, len(self.player.inventory) - 1)
            return

        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            self.state = GameState.EXPLORE
        elif event.key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % 5
        elif event.key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % 5
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            if self.menu_index == 0:  # 物品
                self.show_inventory = True
                self.inv_index = 0
            elif self.menu_index == 1:  # 装备（显示当前装备）
                pass
            elif self.menu_index == 2:  # 保存
                self._save_game()
                self.state = GameState.EXPLORE
            elif self.menu_index == 3:  # 读取
                self._load_game()
            elif self.menu_index == 4:  # 返回
                self.state = GameState.EXPLORE

    def _interact(self):
        """与面前的NPC/物体交互"""
        dx, dy = 0, 0
        if self.player.direction == 'up': dy = -1
        elif self.player.direction == 'down': dy = 1
        elif self.player.direction == 'left': dx = -1
        elif self.player.direction == 'right': dx = 1

        target_tx = self.player.tx + dx
        target_ty = self.player.ty + dy

        # 幽灵商人
        if (self.player.area == AREA_FOREST and
            self.ghost_merchant_npc.x == target_tx and
            self.ghost_merchant_npc.y == target_ty):
            self.dialogue.start(self.ghost_merchant_npc)
            return

        # NPC
        for npc in self.npcs:
            if npc.area == self.player.area and npc.x == target_tx and npc.y == target_ty:
                self.dialogue.start(npc)
                return

        # 宝箱
        chest_key = (self.player.area, target_tx, target_ty)
        if chest_key in self.chest_positions and chest_key not in self.chests_opened:
            item_key, count = self.chest_positions[chest_key]
            self.player.add_item(item_key, count)
            self.chests_opened.add(chest_key)
            item = ITEMS_DB[item_key]
            self.message_queue.append((f"获得 {item.name} x{count}！", 120))
            self.particles.emit(target_tx * TILE + 16, target_ty * TILE + 16, 15, C_GOLD, 2, 40, 3, 'magic')
            return

        # 隐藏宝箱（检测玩家当前位置和面前位置）
        for check_key in [chest_key, (self.player.area, self.player.tx, self.player.ty)]:
            if check_key in self.hidden_chests and check_key not in self.hidden_chests_opened:
                item_key, count = self.hidden_chests[check_key]
                self.player.add_item(item_key, count)
                self.hidden_chests_opened.add(check_key)
                item = ITEMS_DB[item_key]
                self.message_queue.append((f"★ 发现隐藏宝箱！获得 {item.name} x{count}！", 150))
                px = check_key[1] * TILE + 16
                py = check_key[2] * TILE + 16
                self.particles.emit(px, py, 25, (255, 200, 100), 3, 50, 3, 'magic')
                self.particles.emit(px, py, 15, (255, 255, 200), 2, 40, 2, 'firefly')
                return

    def _update(self):
        self.tick += 1

        if self.state == GameState.EXPLORE:
            self.dialogue.update()
            if not self.dialogue.active:
                self._update_player_movement()
            self._update_camera()
            self._update_ambient_particles()
            self.particles.update()
            # 消息队列
            if self.message_queue:
                self.message_queue[0] = (self.message_queue[0][0], self.message_queue[0][1] - 1)
                if self.message_queue[0][1] <= 0:
                    self.message_queue.pop(0)

        elif self.state == GameState.COMBAT:
            if self.combat:
                self.combat.update()

        elif self.state == GameState.TITLE:
            self.title_blink += 1

    def _update_player_movement(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        # 朝向取最后变化的轴方向
        if dx != 0 or dy != 0:
            if abs(dx) >= abs(dy):
                self.player.direction = 'left' if dx < 0 else 'right'
            else:
                self.player.direction = 'up' if dy < 0 else 'down'

        self.player.moving = dx != 0 or dy != 0

        if self.player.moving:
            # 斜向移动时归一化，保持速度一致
            if dx != 0 and dy != 0:
                factor = 0.7071  # 1/sqrt(2)
            else:
                factor = 1.0
            mx = dx * self.player.speed * factor
            my = dy * self.player.speed * factor
            nx = self.player.x + mx
            ny = self.player.y + my
            ntx = int(nx + TILE//2) // TILE
            nty = int(ny + TILE//2) // TILE

            # 碰撞检测
            can_move_x = self.game_map.is_walkable(self.player.area, int((nx + TILE//2) // TILE), self.player.ty)
            can_move_y = self.game_map.is_walkable(self.player.area, self.player.tx, int((ny + TILE//2) // TILE))

            if can_move_x and dx != 0:
                self.player.x = nx
            if can_move_y and dy != 0:
                self.player.y = ny

            self.player.tx = int((self.player.x + TILE//2) // TILE)
            self.player.ty = int((self.player.y + TILE//2) // TILE)

            # 动画
            self.player.anim_timer += 1
            if self.player.anim_timer >= 8:
                self.player.anim_timer = 0
                self.player.anim_frame = (self.player.anim_frame + 1) % 4

            # 区域转换
            trans = self.game_map.check_transition(self.player.area, self.player.tx, self.player.ty)
            if trans:
                target_area, tx, ty = trans
                self.player.area = target_area
                self.player.x = float(tx * TILE)
                self.player.y = float(ty * TILE)
                self.player.tx = tx
                self.player.ty = ty
                self.encounter_steps = 0
                # 进入森林时重新随机幽灵商人位置
                if target_area == AREA_FOREST:
                    self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
                    self.ghost_merchant_npc.x = self.ghost_merchant_pos[0]
                    self.ghost_merchant_npc.y = self.ghost_merchant_pos[1]

            # 随机遇敌
            self.encounter_steps += 1
            encounter_list = ENCOUNTER_TABLE.get(self.player.area, [])
            if encounter_list and self.encounter_steps > 30:
                if random.random() < 0.004:
                    # 1% 概率遇到金色史莱姆
                    if random.random() < 0.01:
                        enemy = 'golden_slime'
                        self.message_queue.append(("★ 稀有敌人出现了！", 90))
                    else:
                        enemy = random.choice(encounter_list)
                    self.combat = Combat(self.player, enemy, self.assets)
                    self.state = GameState.COMBAT
                    self.encounter_steps = 0

            # 随机事件
            self.random_event_steps += 1
            if self.random_event_steps > 50 and random.random() < 0.003:
                self.random_event_steps = 0
                self._trigger_random_event()

    def _trigger_random_event(self):
        """走路时小概率触发的随机事件"""
        px = self.player.x + TILE // 2
        py = self.player.y + TILE // 2
        event = random.choice(['gold', 'potion', 'trap', 'blessing'])
        if event == 'gold':
            amount = random.randint(5, 20)
            self.player.stats.gold += amount
            self.message_queue.append((f"你在地上发现了{amount}金币！", 120))
            self.particles.emit(px, py, 10, C_GOLD, 1.5, 30, 2, 'magic')
        elif event == 'potion':
            self.player.add_item('hp_potion')
            self.message_queue.append(("草丛中藏着一瓶药水！", 120))
            self.particles.emit(px, py, 8, C_GREEN, 1.5, 30, 2, 'magic')
        elif event == 'trap':
            dmg = random.randint(5, 15)
            self.player.stats.hp = max(1, self.player.stats.hp - dmg)
            self.message_queue.append((f"你踩到了陷阱！受到{dmg}点伤害！", 120))
            self.particles.emit(px, py, 12, C_RED, 2, 25, 2)
        elif event == 'blessing':
            heal_hp = random.randint(10, 25)
            heal_mp = random.randint(5, 15)
            self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal_hp)
            self.player.stats.mp = min(self.player.stats.max_mp, self.player.stats.mp + heal_mp)
            self.message_queue.append((f"一股神秘力量涌入体内！HP+{heal_hp} MP+{heal_mp}", 120))
            self.particles.emit(px, py, 15, (200, 200, 255), 2, 40, 3, 'magic')

    def _update_camera(self):
        target_x = self.player.x - SCREEN_W // 2 + TILE // 2
        target_y = self.player.y - SCREEN_H // 2 + TILE // 2
        mw = self.game_map.map_w.get(self.player.area, 40) * TILE
        mh = self.game_map.map_h.get(self.player.area, 30) * TILE
        target_x = max(0, min(target_x, mw - SCREEN_W))
        target_y = max(0, min(target_y, mh - SCREEN_H))
        self.camera_x = lerp(self.camera_x, target_x, 0.08)
        self.camera_y = lerp(self.camera_y, target_y, 0.08)

    def _update_ambient_particles(self):
        area = self.player.area
        if area == AREA_FOREST and self.tick % 15 == 0:
            fx = self.camera_x + random.randint(0, SCREEN_W)
            fy = self.camera_y + random.randint(0, SCREEN_H)
            self.particles.emit(fx, fy, 1, (180, 220, 100), 0.3, 90, 2, 'firefly')
        elif area == AREA_DUNGEON and self.tick % 20 == 0:
            fx = self.camera_x + random.randint(0, SCREEN_W)
            fy = self.camera_y + random.randint(0, SCREEN_H)
            self.particles.emit(fx, fy, 1, (100, 60, 140), 0.2, 60, 2, 'dust')
        elif area == AREA_VILLAGE and self.tick % 25 == 0:
            fx = self.camera_x + random.randint(0, SCREEN_W)
            fy = self.camera_y + random.randint(0, SCREEN_H)
            self.particles.emit(fx, fy, 1, (255, 255, 200), 0.15, 80, 1, 'dust')

    def _restart(self):
        self.player = Player(20, 16)
        self.state = GameState.EXPLORE
        self.combat = None
        self.chests_opened.clear()
        self.hidden_chests_opened.clear()
        self.encounter_steps = 0
        self.random_event_steps = 0
        self._generate_hidden_chests()
        self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
        self.ghost_merchant_npc.x = self.ghost_merchant_pos[0]
        self.ghost_merchant_npc.y = self.ghost_merchant_pos[1]

    def _random_walkable_tile(self, area):
        """在指定区域随机选一个可行走的 tile"""
        mdata = self.game_map.maps.get(area, [])
        w = self.game_map.map_w.get(area, 0)
        h = self.game_map.map_h.get(area, 0)
        for _ in range(200):
            tx = random.randint(2, w - 3)
            ty = random.randint(2, h - 3)
            if self.game_map.is_walkable(area, tx, ty):
                # 避开 NPC、宝箱、转换点
                occupied = False
                for npc in self.npcs:
                    if npc.area == area and npc.x == tx and npc.y == ty:
                        occupied = True
                        break
                if (area, tx, ty) in self.chest_positions:
                    occupied = True
                if not occupied:
                    return (tx, ty)
        return (w // 2, h // 2)

    def _generate_hidden_chests(self):
        """为每个区域随机生成 1-2 个隐藏宝箱"""
        self.hidden_chests = {}
        hidden_loot = {
            AREA_FOREST: [('elixir', 1), ('lucky_coin', 1), ('magic_ring', 1)],
            AREA_DUNGEON: [('elixir', 1), ('mp_potion', 5), ('iron_sword', 1)],
            AREA_VILLAGE: [('hp_potion', 3), ('mp_potion', 2)],
        }
        for area in [AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON]:
            count = random.randint(1, 2)
            loot_pool = hidden_loot.get(area, [('hp_potion', 1)])
            for _ in range(count):
                pos = self._random_walkable_tile(area)
                key = (area, pos[0], pos[1])
                if key not in self.hidden_chests and key not in self.chest_positions:
                    item = random.choice(loot_pool)
                    self.hidden_chests[key] = item

    def _save_game(self):
        data = {
            'player': self.player.to_save_dict(),
            'chests_opened': [list(c) for c in self.chests_opened],
            'hidden_chests': {f"{a},{x},{y}": list(v) for (a, x, y), v in self.hidden_chests.items()},
            'hidden_chests_opened': [list(c) for c in self.hidden_chests_opened],
            'ghost_merchant_pos': list(self.ghost_merchant_pos),
        }
        try:
            with open(SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.message_queue.append(("游戏已保存！", 120))
        except Exception as e:
            traceback.print_exc()
            self.message_queue.append((f"保存失败！{e}", 120))

    def _load_game(self):
        if not os.path.exists(SAVE_PATH):
            self.message_queue.append(("没有找到存档！", 120))
            return
        try:
            with open(SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.player.load_save_dict(data['player'])
            self.chests_opened = set(tuple(c) for c in data.get('chests_opened', []))
            # 恢复隐藏宝箱状态
            hc = data.get('hidden_chests', {})
            self.hidden_chests = {}
            for k, v in hc.items():
                parts = k.split(',')
                self.hidden_chests[(parts[0], int(parts[1]), int(parts[2]))] = tuple(v)
            self.hidden_chests_opened = set(tuple(c) for c in data.get('hidden_chests_opened', []))
            # 恢复幽灵商人位置
            gmp = data.get('ghost_merchant_pos')
            if gmp:
                self.ghost_merchant_pos = tuple(gmp)
                self.ghost_merchant_npc.x = gmp[0]
                self.ghost_merchant_npc.y = gmp[1]
            self.combat = None
            self.encounter_steps = 0
            self.random_event_steps = 0
            self.state = GameState.EXPLORE
            self.show_inventory = False
            # 重置相机到玩家位置
            self.camera_x = self.player.x - SCREEN_W // 2
            self.camera_y = self.player.y - SCREEN_H // 2
            self.message_queue.append(("读取存档成功！", 120))
        except Exception as e:
            traceback.print_exc()
            self.message_queue.append((f"读取失败！{e}", 120))


    # ============================================================
    # 绘制
    # ============================================================
    def _draw(self):
        if self.state == GameState.TITLE:
            self._draw_title()
        elif self.state == GameState.EXPLORE:
            self._draw_explore()
        elif self.state == GameState.COMBAT:
            if self.combat:
                self.combat.draw(self.screen)
        elif self.state == GameState.MENU:
            self._draw_explore()
            self._draw_menu()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()

    def _draw_title(self):
        # 渐变天空
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(lerp(20, 60, t))
            g = int(lerp(10, 30, t))
            b = int(lerp(50, 100, t))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

        # 星星
        random.seed(42)
        for _ in range(80):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H // 2)
            brightness = random.randint(100, 255)
            flicker = math.sin(self.tick * 0.05 + sx) * 30
            b = max(0, min(255, int(brightness + flicker)))
            self.screen.set_at((sx, sy), (b, b, b))
        random.seed()

        # 山脉剪影
        for x in range(SCREEN_W):
            h = int(80 + math.sin(x * 0.01) * 40 + math.sin(x * 0.03) * 20)
            pygame.draw.line(self.screen, (30, 20, 50), (x, SCREEN_H - h), (x, SCREEN_H))

        # 标题
        draw_text(self.screen, "像素冒险", (SCREEN_W//2, 180), self.assets.font_title, C_GOLD, center=True)
        draw_text(self.screen, "Pixel Quest", (SCREEN_W//2, 230), self.assets.font_lg, (180, 160, 220), center=True)

        # 菜单选项
        has_save = os.path.exists(SAVE_PATH)
        options = ["▶ 新游戏", "📂 读取存档"]
        for i, opt in enumerate(options):
            if i == 1 and not has_save:
                color = (80, 80, 80)
            elif i == self.title_index:
                color = C_YELLOW
            else:
                color = C_WHITE
            prefix = "▸ " if i == self.title_index else "  "
            draw_text(self.screen, prefix + opt, (SCREEN_W//2, 340 + i * 36), self.assets.font_md, color, center=True)

        # 操作说明
        draw_text(self.screen, "方向键/WASD: 移动  J: 确认/交互  X: 取消  ESC: 菜单",
                  (SCREEN_W//2, SCREEN_H - 60), self.assets.font_sm, (150, 150, 170), center=True)

    def _draw_explore(self):
        area = self.player.area
        cam_x, cam_y = int(self.camera_x), int(self.camera_y)

        # 天空渐变
        self._draw_sky(area)

        # 地图瓦片
        mdata = self.game_map.maps.get(area, [])
        start_tx = max(0, cam_x // TILE)
        start_ty = max(0, cam_y // TILE)
        end_tx = min(self.game_map.map_w.get(area, 0), (cam_x + SCREEN_W) // TILE + 2)
        end_ty = min(self.game_map.map_h.get(area, 0), (cam_y + SCREEN_H) // TILE + 2)

        water_frame = (self.tick // 15) % 4

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                sx = tx * TILE - cam_x
                sy = ty * TILE - cam_y
                tile = self.game_map.get_tile(area, tx, ty)

                if tile == 0:  # 草
                    key = 'grass2' if (tx + ty) % 3 == 0 else 'grass'
                    self.screen.blit(self.assets.tiles[key], (sx, sy))
                elif tile == 1:  # 路
                    self.screen.blit(self.assets.tiles['path'], (sx, sy))
                elif tile == 2:  # 水
                    self.screen.blit(self.assets.tiles[f'water_{water_frame}'], (sx, sy))
                    # 水面反光
                    if self.tick % 30 < 15 and random.random() < 0.02:
                        self.screen.set_at((sx + random.randint(0, TILE-1), sy + random.randint(0, TILE//2)),
                                           (180, 220, 255))
                elif tile == 3:  # 墙
                    self.screen.blit(self.assets.tiles['wall'], (sx, sy))
                elif tile == 4:  # 树
                    # 先画草地底
                    self.screen.blit(self.assets.tiles['grass'], (sx, sy))
                    # 树有轻微摇摆
                    sway = int(math.sin(self.tick * 0.03 + tx * 0.5) * 1)
                    self.screen.blit(self.assets.tiles['tree'], (sx + sway, sy))
                elif tile == 5:  # 地牢地板
                    self.screen.blit(self.assets.tiles['dungeon_floor'], (sx, sy))
                elif tile == 6:  # 花
                    self.screen.blit(self.assets.tiles['grass'], (sx, sy))
                    self.screen.blit(self.assets.tiles['flower'], (sx, sy))
                elif tile == 7:  # 门
                    self.screen.blit(self.assets.tiles['door'], (sx, sy))

        # 宝箱
        for (a, cx, cy), (item_key, cnt) in self.chest_positions.items():
            if a == area and (a, cx, cy) not in self.chests_opened:
                sx = cx * TILE - cam_x
                sy = cy * TILE - cam_y
                self.screen.blit(self.assets.tiles['chest'], (sx, sy))

        # 房屋（村庄特有）
        if area == AREA_VILLAGE:
            houses = [(12, 6), (26, 8), (30, 18)]
            for hx, hy in houses:
                sx = hx * TILE - cam_x
                sy = hy * TILE - cam_y
                self.screen.blit(self.assets.tiles['house'], (sx, sy))

        # NPC
        for npc in self.npcs:
            if npc.area == area:
                sx = npc.x * TILE - cam_x
                sy = npc.y * TILE - cam_y
                sprite = self.assets.npc_sprites.get(npc.sprite_key)
                if sprite:
                    # NPC 轻微浮动
                    bob = int(math.sin(self.tick * 0.05 + npc.x) * 2)
                    self.screen.blit(sprite, (sx, sy + bob))
                    # 名字
                    draw_text(self.screen, npc.name, (sx + TILE//2, sy - 8),
                              self.assets.font_sm, C_GOLD, center=True)
                    # 交互提示
                    dist = abs(self.player.tx - npc.x) + abs(self.player.ty - npc.y)
                    if dist <= 2:
                        if (self.tick // 20) % 2:
                            # 气泡背景
                            bw_hint = self.assets.font_sm.size("[J]")[0] + 8
                            bh_hint = 18
                            bx_hint = sx + TILE//2 - bw_hint//2
                            by_hint = sy - 28
                            pygame.draw.rect(self.screen, (30, 25, 50), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                            pygame.draw.rect(self.screen, (160, 140, 200), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                            draw_text(self.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                      self.assets.font_sm, C_YELLOW, center=True)

        # 幽灵商人（森林中，闪烁半透明效果）
        if area == AREA_FOREST:
            gx, gy = self.ghost_merchant_npc.x, self.ghost_merchant_npc.y
            sx = gx * TILE - cam_x
            sy = gy * TILE - cam_y
            # 闪烁：用 sin 控制可见度，部分 tick 不显示
            flicker = math.sin(self.tick * 0.08) * 0.5 + 0.5  # 0~1
            if flicker > 0.2:  # 80% 时间可见
                ghost_sprite = self.assets.npc_sprites.get('ghost_merchant')
                if ghost_sprite:
                    # 半透明效果
                    alpha = int(100 + flicker * 100)  # 100~200
                    temp = ghost_sprite.copy()
                    temp.set_alpha(alpha)
                    bob = int(math.sin(self.tick * 0.04 + gx) * 3)
                    self.screen.blit(temp, (sx, sy + bob))
                    # 名字（也半透明）
                    name_color = (180, 140, 255)
                    draw_text(self.screen, "???", (sx + TILE//2, sy - 8),
                              self.assets.font_sm, name_color, center=True)
                    # 交互提示
                    dist = abs(self.player.tx - gx) + abs(self.player.ty - gy)
                    if dist <= 2:
                        if (self.tick // 15) % 2:
                            bw_hint = self.assets.font_sm.size("[J]")[0] + 8
                            bh_hint = 18
                            bx_hint = sx + TILE//2 - bw_hint//2
                            by_hint = sy - 28
                            pygame.draw.rect(self.screen, (40, 20, 60), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                            pygame.draw.rect(self.screen, (180, 140, 220), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                            draw_text(self.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                      self.assets.font_sm, (200, 160, 255), center=True)

        # 玩家
        frames = self.assets.player_frames.get(self.player.direction, [])
        if frames:
            frame_idx = self.player.anim_frame if self.player.moving else 0
            psurf = frames[frame_idx % len(frames)]
            px = int(self.player.x) - cam_x
            py = int(self.player.y) - cam_y
            self.screen.blit(psurf, (px, py))

        # 粒子
        self.particles.draw(self.screen, cam_x, cam_y)

        # 对话框
        self.dialogue.draw(self.screen, self.player)

        # HUD
        self._draw_hud()

        # 小地图
        self._draw_minimap()

        # 消息
        if self.message_queue:
            msg, timer = self.message_queue[0]
            alpha = min(255, timer * 4)
            draw_text(self.screen, msg, (SCREEN_W//2, 80), self.assets.font_md, C_GOLD, center=True)

        # 区域名称（进入时短暂显示）
        if self.encounter_steps < 60:
            area_names = {AREA_VILLAGE: "像素村", AREA_FOREST: "迷雾森林", AREA_DUNGEON: "暗影地牢"}
            name = area_names.get(area, "")
            alpha = max(0, 60 - self.encounter_steps) / 60
            c = tuple(int(255 * alpha) for _ in range(3))
            draw_text(self.screen, name, (SCREEN_W//2, 50), self.assets.font_lg, c, center=True)

    def _draw_sky(self, area):
        if area == AREA_VILLAGE:
            # 日间天空
            time_cycle = (math.sin(self.tick * 0.002) + 1) / 2
            top = lerp_color((100, 160, 230), (200, 120, 80), time_cycle)
            bot = lerp_color((180, 220, 255), (240, 180, 120), time_cycle)
        elif area == AREA_FOREST:
            top = (30, 60, 30)
            bot = (60, 100, 50)
        else:
            top = (15, 10, 25)
            bot = (30, 25, 45)

        for y in range(SCREEN_H):
            t = y / SCREEN_H
            c = lerp_color(top, bot, t)
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_W, y))

    def _draw_hud(self):
        st = self.player.stats
        # 状态栏背景
        draw_pixel_rect(self.screen, (20, 15, 35, 180), (8, 8, 220, 60), 2, (100, 80, 140))

        draw_text(self.screen, f"Lv.{st.level} 勇者", (16, 12), self.assets.font_sm, C_GOLD)
        draw_bar(self.screen, 16, 30, 140, 10, st.hp / st.max_hp, C_HP_BAR)
        draw_text(self.screen, f"HP {st.hp}/{st.max_hp}", (160, 28), self.assets.font_sm)
        draw_bar(self.screen, 16, 44, 140, 10, st.mp / st.max_mp, C_MP_BAR)
        draw_text(self.screen, f"MP {st.mp}/{st.max_mp}", (160, 42), self.assets.font_sm)
        draw_bar(self.screen, 16, 58, 140, 8, st.exp / max(1, st.exp_next), C_EXP_BAR)
        draw_text(self.screen, f"EXP {st.exp}/{st.exp_next}", (160, 55), self.assets.font_sm)

        # 金币
        draw_text(self.screen, f"💰 {st.gold}", (16, 74), self.assets.font_sm, C_GOLD)

    def _draw_minimap(self):
        mm_w, mm_h = 120, 90
        mm_x, mm_y = SCREEN_W - mm_w - 10, 10
        mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm_surf.fill((0, 0, 0, 140))

        area = self.player.area
        mw = self.game_map.map_w.get(area, 1)
        mh = self.game_map.map_h.get(area, 1)
        sx = mm_w / mw
        sy = mm_h / mh

        mdata = self.game_map.maps.get(area, [])
        for ty, row in enumerate(mdata):
            for tx, tile in enumerate(row):
                px = int(tx * sx)
                py = int(ty * sy)
                pw = max(1, int(sx))
                ph = max(1, int(sy))
                if tile == 0 or tile == 6:
                    c = (80, 160, 60, 180)
                elif tile == 1:
                    c = (180, 160, 120, 180)
                elif tile == 2:
                    c = (40, 80, 180, 180)
                elif tile == 3:
                    c = (80, 75, 70, 180)
                elif tile == 4:
                    c = (30, 100, 30, 180)
                elif tile == 5:
                    c = (55, 50, 60, 180)
                elif tile == 7:
                    c = (200, 150, 50, 180)
                else:
                    c = (40, 40, 40, 180)
                pygame.draw.rect(mm_surf, c, (px, py, pw, ph))

        # 玩家位置
        ppx = int(self.player.tx * sx)
        ppy = int(self.player.ty * sy)
        pygame.draw.rect(mm_surf, (255, 50, 50, 255), (ppx - 1, ppy - 1, 3, 3))

        # NPC位置
        for npc in self.npcs:
            if npc.area == area:
                npx = int(npc.x * sx)
                npy = int(npc.y * sy)
                pygame.draw.rect(mm_surf, (255, 220, 50, 255), (npx, npy, 2, 2))

        # 边框
        pygame.draw.rect(mm_surf, (140, 120, 180, 200), (0, 0, mm_w, mm_h), 2)

        self.screen.blit(mm_surf, (mm_x, mm_y))

    def _draw_menu(self):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        # 主面板
        pw, ph = 400, 420
        px = (SCREEN_W - pw) // 2
        py = (SCREEN_H - ph) // 2
        draw_pixel_rect(self.screen, C_PANEL, (px, py, pw, ph), 3, C_PANEL_BORDER)

        draw_text(self.screen, "【菜单】", (px + pw//2, py + 16), self.assets.font_lg, C_GOLD, center=True)

        st = self.player.stats

        # 角色信息
        info_y = py + 50
        draw_text(self.screen, f"Lv.{st.level} 勇者", (px + 20, info_y), self.assets.font_md, C_GOLD)
        draw_bar(self.screen, px + 20, info_y + 28, 200, 14, st.hp / st.max_hp, C_HP_BAR)
        draw_text(self.screen, f"HP {st.hp}/{st.max_hp}", (px + 230, info_y + 26), self.assets.font_sm)
        draw_bar(self.screen, px + 20, info_y + 48, 200, 14, st.mp / st.max_mp, C_MP_BAR)
        draw_text(self.screen, f"MP {st.mp}/{st.max_mp}", (px + 230, info_y + 46), self.assets.font_sm)

        draw_text(self.screen, f"攻击力: {self.player.get_total_atk()}", (px + 20, info_y + 72), self.assets.font_sm)
        draw_text(self.screen, f"防御力: {self.player.get_total_def()}", (px + 20, info_y + 92), self.assets.font_sm)
        draw_text(self.screen, f"金币: {st.gold}", (px + 200, info_y + 72), self.assets.font_sm, C_GOLD)
        draw_text(self.screen, f"经验: {st.exp}/{st.exp_next}", (px + 200, info_y + 92), self.assets.font_sm)

        # 装备
        draw_text(self.screen, "【装备】", (px + 20, info_y + 120), self.assets.font_sm, C_GOLD)
        equip_names = {'weapon': '武器', 'armor': '防具', 'accessory': '饰品'}
        ey = info_y + 142
        for slot, label in equip_names.items():
            eq = self.player.equipped[slot]
            name = ITEMS_DB[eq].name if eq else "无"
            draw_text(self.screen, f"{label}: {name}", (px + 30, ey), self.assets.font_sm)
            ey += 20

        # 菜单选项
        if self.show_inventory:
            self._draw_inventory_panel(px + 20, info_y + 220, pw - 40)
        else:
            options = ["📦 物品", "📊 状态", "💾 保存", "📂 读取", "↩ 返回"]
            for i, opt in enumerate(options):
                color = C_YELLOW if i == self.menu_index else C_WHITE
                prefix = "▸ " if i == self.menu_index else "  "
                draw_text(self.screen, prefix + opt, (px + 30, info_y + 220 + i * 30), self.assets.font_md, color)

    def _draw_inventory_panel(self, x, y, w):
        draw_text(self.screen, "【物品栏】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        items = self.player.inventory
        if not items:
            draw_text(self.screen, "空空如也...", (x + 10, y + 24), self.assets.font_sm)
            return
        for i, (key, cnt) in enumerate(items):
            item = ITEMS_DB.get(key)
            if not item:
                continue
            color = C_YELLOW if i == self.inv_index else C_WHITE
            prefix = "▸ " if i == self.inv_index else "  "
            # 图标
            icon = self.assets.item_icons.get(key)
            iy = y + 24 + i * 26
            if icon:
                self.screen.blit(icon, (x + 4, iy))
            draw_text(self.screen, f"{prefix}{item.name} x{cnt}", (x + 30, iy + 2), self.assets.font_sm, color)
            # 选中时显示描述
            if i == self.inv_index:
                draw_text(self.screen, item.description, (x + 10, y + 24 + len(items) * 26 + 10),
                          self.assets.font_sm, (180, 180, 200))
                draw_text(self.screen, "J: 使用/装备", (x + 10, y + 24 + len(items) * 26 + 30),
                          self.assets.font_sm, (150, 150, 170))

    def _draw_game_over(self):
        self.screen.fill(C_BLACK)
        draw_text(self.screen, "游戏结束", (SCREEN_W//2, SCREEN_H//2 - 40), self.assets.font_title, C_RED, center=True)
        draw_text(self.screen, "你倒在了冒险的途中...", (SCREEN_W//2, SCREEN_H//2 + 20), self.assets.font_md, C_WHITE, center=True)
        if (self.tick // 30) % 2:
            draw_text(self.screen, "按 Enter 重新开始", (SCREEN_W//2, SCREEN_H//2 + 80), self.assets.font_md, C_GOLD, center=True)

# ============================================================
# 入口
# ============================================================
if __name__ == '__main__':
    game = Game()
    game.run()
