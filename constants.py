"""常量、颜色、工具函数 - 赛博朋克主题"""

import os
import pygame

SAVE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'save.json')

# ============================================================
# 常量
# ============================================================
SCREEN_W, SCREEN_H = 960, 640
TILE = 32
FPS = 60

# 赛博朋克颜色
C_BLACK = (0, 0, 0)
C_WHITE = (220, 225, 235)
C_RED = (255, 40, 80)
C_GREEN = (0, 255, 140)
C_BLUE = (40, 120, 255)
C_YELLOW = (255, 220, 50)
C_GOLD = (0, 255, 200)       # 霓虹青
C_DARK = (8, 8, 18)
C_PANEL = (10, 12, 30)       # 深蓝黑
C_PANEL_BORDER = (140, 60, 200)  # 霓虹紫
C_HP_BAR = (255, 40, 80)     # 霓虹红
C_MP_BAR = (0, 180, 255)     # 霓虹蓝
C_EXP_BAR = (0, 255, 140)    # 霓虹绿

# 赛博朋克专用色
C_NEON_PINK = (255, 50, 150)
C_NEON_CYAN = (0, 255, 220)
C_NEON_GREEN = (0, 255, 100)
C_NEON_PURPLE = (180, 60, 255)

# ============================================================
# 工具函数
# ============================================================
def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def draw_pixel_rect(surf, color, rect, border=2, border_color=None):
    x, y, w, h = rect
    pygame.draw.rect(surf, color, (x, y, w, h))
    if border_color:
        pygame.draw.rect(surf, border_color, (x, y, w, h), border)
    # 像素角
    corner = border_color or color
    for cx, cy in [(x, y), (x+w-1, y), (x, y+h-1), (x+w-1, y+h-1)]:
        pygame.draw.rect(surf, corner, (cx, cy, 2, 2))
    # 内角高光
    hl = tuple(min(255, c + 30) for c in color)
    pygame.draw.line(surf, hl, (x + 2, y + 2), (x + w - 4, y + 2))
    pygame.draw.line(surf, hl, (x + 2, y + 2), (x + 2, y + h - 4))

def draw_text(surf, text, pos, font, color=C_WHITE, shadow=True, center=False):
    if center:
        ts = font.render(text, True, color)
        if shadow:
            sh = font.render(text, True, (0, 0, 0))
            surf.blit(sh, (pos[0] - ts.get_width()//2 + 1, pos[1] + 1))
        surf.blit(ts, (pos[0] - ts.get_width()//2, pos[1]))
    else:
        if shadow:
            sh = font.render(text, True, (0, 0, 0))
            surf.blit(sh, (pos[0] + 1, pos[1] + 1))
        ts = font.render(text, True, color)
        surf.blit(ts, pos)

def draw_bar(surf, x, y, w, h, ratio, color, bg=(15, 15, 25)):
    pygame.draw.rect(surf, bg, (x, y, w, h))
    pygame.draw.rect(surf, color, (x, y, int(w * max(0, min(1, ratio))), h))
    pygame.draw.rect(surf, (100, 100, 140), (x, y, w, h), 1)
