"""家园种菜系统"""
import random
import pygame
from constants import *
from entities import CROPS_DB, ITEMS_DB


def get_farm_plot_index(game, tx, ty):
    """根据地图坐标返回菜地索引"""
    plots_pos = []
    for i in range(3):
        for j in range(2):
            fx = 3 + i * 5
            fy = 3 + j * 5
            plots_pos.append((fx, fy))
            plots_pos.append((fx + 1, fy))
    # 每块地占2格，6块地
    for idx in range(6):
        i, j = idx % 3, idx // 3
        fx = 3 + i * 5
        fy = 3 + j * 5
        if (tx == fx or tx == fx + 1) and ty == fy:
            return idx
    return 0


def handle_farm_event(game, event):
    """家园种菜界面"""
    if event.type != pygame.KEYDOWN:
        return
    p = game.player
    p.init_farm()
    num_plots = len(p.farm_plots)

    if game.farm_mode == 0:  # 查看模式
        cols = min(num_plots, 4)
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            from game import GameState
            game.state = GameState.EXPLORE
        elif event.key == pygame.K_LEFT:
            game.farm_index = (game.farm_index - 1) % num_plots
        elif event.key == pygame.K_RIGHT:
            game.farm_index = (game.farm_index + 1) % num_plots
        elif event.key == pygame.K_UP:
            game.farm_index = (game.farm_index - cols) % num_plots
        elif event.key == pygame.K_DOWN:
            game.farm_index = (game.farm_index + cols) % num_plots
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            plot = p.farm_plots[game.farm_index]
            if plot.ready:
                # 收获
                crop = CROPS_DB[plot.crop_id]
                count = crop.harvest_count
                # 变异收获：farm_level>=3 有10%概率产出翻倍
                mutated = False
                if p.farm_level >= 3 and random.random() < 0.1:
                    count *= 2
                    mutated = True
                p.add_item(crop.harvest_item, count)
                msg = f"收获了 {ITEMS_DB[crop.harvest_item].name} x{count}！"
                if mutated:
                    msg += " [变异！产出翻倍！]"
                    px = SCREEN_W // 2
                    py = SCREEN_H // 2
                    game.particles.emit(px, py, 20, (255, 200, 50), 3, 50, 4, 'magic')
                game.message_queue.append((msg, 120))
                plot.crop_id = None
                plot.growth = 0
                plot.ready = False
                plot.fertilized = False
            elif plot.crop_id is None:
                # 进入种子选择
                game.farm_mode = 1
                game.farm_seed_index = 0
        elif event.key == pygame.K_u:
            # 农场升级
            upgrade_costs = {0: 300, 1: 600, 2: 1200}
            cost = upgrade_costs.get(p.farm_level)
            if cost is None:
                game.message_queue.append(("农场已满级！", 90))
            elif p.stats.gold >= cost:
                p.stats.gold -= cost
                p.farm_level += 1
                p.init_farm()
                effects = {1: "+2地块 生长+20%", 2: "+2地块 生长+40%", 3: "+2地块 生长+60% 10%变异"}
                game.message_queue.append((f"农场升级到Lv{p.farm_level}！{effects[p.farm_level]} (-{cost}G)", 150))
            else:
                game.message_queue.append((f"信用点不足！需要{cost}G", 90))
        elif event.key == pygame.K_f:
            # 施肥
            plot = p.farm_plots[game.farm_index]
            if plot.crop_id and not plot.ready and not plot.fertilized:
                if p.item_count('fertilizer') > 0:
                    p.remove_item('fertilizer')
                    plot.fertilized = True
                    game.message_queue.append(("施肥成功！生长速度x2！", 120))
                else:
                    game.message_queue.append(("没有纳米肥料！", 90))
            elif plot.fertilized:
                game.message_queue.append(("已经施过肥了！", 90))
            else:
                game.message_queue.append(("需要先种植作物！", 90))

    elif game.farm_mode == 1:  # 选种子
        seeds = list(CROPS_DB.values())
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            game.farm_mode = 0
        elif event.key == pygame.K_UP:
            game.farm_seed_index = (game.farm_seed_index - 1) % len(seeds)
        elif event.key == pygame.K_DOWN:
            game.farm_seed_index = (game.farm_seed_index + 1) % len(seeds)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            crop = seeds[game.farm_seed_index]
            if p.stats.gold >= crop.seed_price:
                p.stats.gold -= crop.seed_price
                plot = p.farm_plots[game.farm_index]
                plot.crop_id = crop.crop_id
                plot.growth = 0
                plot.ready = False
                plot.fertilized = False
                game.message_queue.append((f"种下了 {crop.name}！(-{crop.seed_price}G)", 120))
                game.farm_mode = 0
            else:
                game.message_queue.append(("信用点不足！", 90))


def draw_farm(game):
    """家园种菜界面"""
    game.screen.fill((10, 15, 10))
    p = game.player
    p.init_farm()
    num_plots = len(p.farm_plots)
    cols = min(num_plots, 4)
    rows = (num_plots + cols - 1) // cols

    draw_text(game.screen, f"【家园 - 农场 Lv{p.farm_level}】", (SCREEN_W//2, 20), game.assets.font_lg, C_GOLD, center=True)
    draw_text(game.screen, f"信用点: {p.stats.gold}", (SCREEN_W - 120, 20), game.assets.font_sm, C_GOLD)

    plot_w, plot_h = 110, 90
    start_x = (SCREEN_W - cols * (plot_w + 10)) // 2
    start_y = 60

    for idx in range(num_plots):
        col, row = idx % cols, idx // cols
        bx = start_x + col * (plot_w + 10)
        by = start_y + row * (plot_h + 10)

        selected = idx == game.farm_index
        border_color = C_NEON_CYAN if selected else (60, 60, 60)
        bg_color = (20, 30, 20) if not selected else (30, 45, 30)
        draw_pixel_rect(game.screen, bg_color, (bx, by, plot_w, plot_h), 2, border_color)

        plot = p.farm_plots[idx]
        if plot.crop_id:
            crop = CROPS_DB.get(plot.crop_id)
            if crop:
                name_text = crop.name
                if plot.fertilized:
                    name_text += " [肥]"
                draw_text(game.screen, name_text, (bx + plot_w//2, by + 5),
                          game.assets.font_sm, C_WHITE, center=True)
                if plot.ready:
                    draw_text(game.screen, "✓ 可收获!", (bx + plot_w//2, by + 28),
                              game.assets.font_sm, C_GREEN, center=True)
                else:
                    pct = plot.growth / crop.grow_time if crop.grow_time > 0 else 0
                    draw_bar(game.screen, bx + 8, by + 32, plot_w - 16, 8, min(1.0, pct), (80, 200, 80))
                    draw_text(game.screen, f"{int(min(100, pct*100))}%", (bx + plot_w//2, by + 45),
                              game.assets.font_sm, (150, 200, 150), center=True)
                item = ITEMS_DB.get(crop.harvest_item)
                if item:
                    draw_text(game.screen, f"→ {item.name} x{crop.harvest_count}", (bx + plot_w//2, by + 65),
                              game.assets.font_sm, (120, 150, 120), center=True)
        else:
            draw_text(game.screen, "空地", (bx + plot_w//2, by + 25),
                      game.assets.font_sm, (80, 80, 80), center=True)
            draw_text(game.screen, "[J] 种植", (bx + plot_w//2, by + 50),
                      game.assets.font_sm, (100, 100, 100), center=True)

    # 种子选择面板
    if game.farm_mode == 1:
        sw, sh = 300, 240
        sx = SCREEN_W // 2 - sw // 2
        sy = SCREEN_H // 2 - sh // 2
        draw_pixel_rect(game.screen, (15, 20, 15), (sx, sy, sw, sh), 2, C_NEON_CYAN)
        draw_text(game.screen, "【选择种子】", (sx + sw//2, sy + 10), game.assets.font_md, C_GOLD, center=True)
        seeds = list(CROPS_DB.values())
        for i, crop in enumerate(seeds):
            color = C_YELLOW if i == game.farm_seed_index else C_WHITE
            prefix = ">> " if i == game.farm_seed_index else "   "
            draw_text(game.screen, f"{prefix}{crop.name} ({crop.seed_price}G)",
                      (sx + 20, sy + 40 + i * 26), game.assets.font_sm, color)
        # 选中种子的详情
        if game.farm_seed_index < len(seeds):
            sel = seeds[game.farm_seed_index]
            item = ITEMS_DB.get(sel.harvest_item)
            info = f"收获: {item.name if item else '?'} x{sel.harvest_count}"
            draw_text(game.screen, info, (sx + 20, sy + sh - 30), game.assets.font_sm, (150, 200, 150))

    # 升级信息
    upgrade_costs = {0: 300, 1: 600, 2: 1200}
    cost = upgrade_costs.get(p.farm_level)
    if cost:
        draw_text(game.screen, f"[U] 升级农场 ({cost}G)", (20, SCREEN_H - 80), game.assets.font_sm, (100, 200, 150))

    # 操作提示
    draw_text(game.screen, "方向键选择  J:种植/收获  F:施肥  U:升级  X:返回", (SCREEN_W//2, SCREEN_H - 30),
              game.assets.font_sm, (100, 120, 100), center=True)

    # 消息
    if game.message_queue:
        msg, timer = game.message_queue[0]
        draw_text(game.screen, msg, (SCREEN_W//2, SCREEN_H - 60), game.assets.font_md, C_GOLD, center=True)
