"""钓鱼系统"""
import math
import random
import pygame
from constants import *
from entities import FISH_DB, ITEMS_DB


def start_fishing(game):
    """开始钓鱼"""
    area = game.player.area
    available = [f for f in FISH_DB.values() if area in f.areas]
    if not available:
        game.message_queue.append(("这里似乎没有鱼...", 90))
        return
    # 按rarity加权: 普通3 稀有2 传说1, night时传说+50%
    weights = []
    for f in available:
        w = {1: 3, 2: 2, 3: 1}.get(f.rarity, 1)
        if f.rarity == 3 and game._get_time_phase() == 'night':
            w = int(w * 1.5) or 1
        weights.append(w)
    fish = random.choices(available, weights=weights, k=1)[0]
    game.fishing_fish = fish.fish_id
    game.fishing_target_pos = random.uniform(0.2, 0.8)
    game.fishing_catch_zone = fish.catch_zone
    game.fishing_speed = 1.5 + (fish.rarity - 1) * 0.5
    game.fishing_indicator = 0.0
    game.fishing_dir = 1
    game.fishing_state = 'casting'
    game.fishing_result = ''
    game.fishing_result_timer = 0
    from game import GameState
    game.state = GameState.FISHING


def handle_fishing_event(game, event):
    if event.type != pygame.KEYDOWN:
        return
    if game.fishing_state == 'casting':
        if event.key == pygame.K_j:
            # 判定
            fish = FISH_DB.get(game.fishing_fish)
            if fish:
                dist = abs(game.fishing_indicator - game.fishing_target_pos)
                if dist < game.fishing_catch_zone / 2:
                    # 成功
                    game.player.add_item(game.fishing_fish)
                    game.player.fish_caught[game.fishing_fish] = game.player.fish_caught.get(game.fishing_fish, 0) + 1
                    game.player.codex_fish.add(game.fishing_fish)
                    game.fishing_result = f"钓到了 {fish.name}！(★{'★' * (fish.rarity - 1)})"
                    px = SCREEN_W // 2
                    py = SCREEN_H // 2
                    colors = {1: (0, 200, 180), 2: (255, 200, 50), 3: (180, 60, 255)}
                    game.particles.emit(px, py, 20, colors.get(fish.rarity, (255, 255, 255)), 3, 50, 4, 'magic')
                else:
                    game.fishing_result = "鱼跑了...再试试？"
            game.fishing_state = 'result'
            game.fishing_result_timer = 90
        elif event.key in (pygame.K_ESCAPE, pygame.K_x):
            from game import GameState
            game.state = GameState.EXPLORE
    elif game.fishing_state == 'result':
        if event.key in (pygame.K_j, pygame.K_RETURN):
            # 重新钓
            start_fishing(game)
        elif event.key in (pygame.K_ESCAPE, pygame.K_x):
            from game import GameState
            game.state = GameState.EXPLORE


def draw_fishing(game):
    """钓鱼小游戏界面"""
    # 水面背景
    game.screen.fill((5, 15, 35))
    # 水波纹
    for y in range(0, SCREEN_H, 8):
        offset = int(math.sin(game.tick * 0.05 + y * 0.1) * 3)
        c = (10 + y // 10, 30 + y // 8, 60 + y // 6)
        pygame.draw.line(game.screen, c, (offset, y), (SCREEN_W + offset, y))

    fish = FISH_DB.get(game.fishing_fish)
    if fish:
        # 鱼名和稀有度
        stars = '★' * fish.rarity
        rarity_colors = {1: C_WHITE, 2: C_YELLOW, 3: C_NEON_PURPLE}
        draw_text(game.screen, f"{fish.name} {stars}",
                  (SCREEN_W // 2, 80), game.assets.font_lg,
                  rarity_colors.get(fish.rarity, C_WHITE), center=True)

    if game.fishing_state == 'casting':
        # 钓鱼条
        bar_w, bar_h = 400, 20
        bar_x = (SCREEN_W - bar_w) // 2
        bar_y = SCREEN_H - 120
        # 背景
        pygame.draw.rect(game.screen, (20, 30, 50), (bar_x, bar_y, bar_w, bar_h))
        pygame.draw.rect(game.screen, (60, 80, 120), (bar_x, bar_y, bar_w, bar_h), 2)
        # 绿色catch zone
        zone_x = bar_x + int((game.fishing_target_pos - game.fishing_catch_zone / 2) * bar_w)
        zone_w = int(game.fishing_catch_zone * bar_w)
        pygame.draw.rect(game.screen, (0, 180, 80), (zone_x, bar_y, zone_w, bar_h))
        # 白色指示器
        ind_x = bar_x + int(game.fishing_indicator * bar_w)
        pygame.draw.rect(game.screen, C_WHITE, (ind_x - 2, bar_y - 4, 4, bar_h + 8))
        # 提示
        draw_text(game.screen, "按 J 收线！", (SCREEN_W // 2, bar_y + 40),
                  game.assets.font_md, C_NEON_CYAN, center=True)

    elif game.fishing_state == 'result':
        color = C_GREEN if '钓到' in game.fishing_result else C_RED
        draw_text(game.screen, game.fishing_result, (SCREEN_W // 2, SCREEN_H // 2),
                  game.assets.font_lg, color, center=True)
        draw_text(game.screen, "J:再钓  X:返回", (SCREEN_W // 2, SCREEN_H // 2 + 50),
                  game.assets.font_md, (120, 140, 160), center=True)

    # 粒子
    game.particles.draw(game.screen, 0, 0)

    # 消息
    if game.message_queue:
        msg, timer = game.message_queue[0]
        draw_text(game.screen, msg, (SCREEN_W // 2, 40), game.assets.font_md, C_GOLD, center=True)

    draw_text(game.screen, "X:返回", (20, SCREEN_H - 30), game.assets.font_sm, (80, 100, 120))
