"""探索界面渲染：地图、NPC、HUD、小地图"""

import math
import pygame
from constants import (TILE, SCREEN_W, SCREEN_H,
                       C_GOLD, C_YELLOW, C_WHITE, C_NEON_CYAN, C_NEON_PINK,
                       C_HP_BAR, C_MP_BAR, C_EXP_BAR,
                       draw_text, draw_bar, draw_pixel_rect)
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_TUNNEL, AREA_BLACK_MARKET, AREA_HOME)
from entities import ITEMS_DB, ROMANCE_CHARS
from data import GRAFFITI_DB, GRAFFITI_SETS


# ============================================================
# 主线任务路标系统
# ============================================================
# 每个 quest_stage 的目标: (目标区域, 目标tx, 目标ty, 标签)
# 如果玩家不在目标区域，箭头指向通往目标区域的传送点
_QUEST_WAYPOINTS = {
    0: (AREA_VILLAGE, 18, 12, "管理员"),       # 城市管理员
    1: (AREA_FACTORY, 35, 30, "Boss"),         # 工厂Boss
    2: (AREA_TUNNEL, 20, 12, "密道"),          # 地下通道
    3: (AREA_CYBERSPACE, 20, 5, "AI先知"),     # AI先知
    4: (AREA_CYBERSPACE, 20, 20, "Boss"),      # 量子霸主
}

# 区域间路径：从A到B应该走哪个区域中转
# (from_area, to_area) → 下一跳区域
_AREA_ROUTE = {
    # 到工厂
    (AREA_VILLAGE, AREA_FACTORY): AREA_FACTORY,
    (AREA_FOREST, AREA_FACTORY): AREA_VILLAGE,
    (AREA_NEON_STREET, AREA_FACTORY): AREA_VILLAGE,
    (AREA_CYBERSPACE, AREA_FACTORY): AREA_VILLAGE,
    (AREA_DUNGEON, AREA_FACTORY): AREA_TUNNEL,
    # 到隧道
    (AREA_FACTORY, AREA_TUNNEL): AREA_TUNNEL,
    (AREA_VILLAGE, AREA_TUNNEL): AREA_FACTORY,
    (AREA_FOREST, AREA_TUNNEL): AREA_VILLAGE,
    (AREA_NEON_STREET, AREA_TUNNEL): AREA_VILLAGE,
    (AREA_CYBERSPACE, AREA_TUNNEL): AREA_VILLAGE,
    (AREA_DUNGEON, AREA_TUNNEL): AREA_TUNNEL,
    # 到网络空间
    (AREA_VILLAGE, AREA_CYBERSPACE): AREA_CYBERSPACE,
    (AREA_FOREST, AREA_CYBERSPACE): AREA_VILLAGE,
    (AREA_NEON_STREET, AREA_CYBERSPACE): AREA_VILLAGE,
    (AREA_FACTORY, AREA_CYBERSPACE): AREA_VILLAGE,
    (AREA_DUNGEON, AREA_CYBERSPACE): AREA_TUNNEL,
    (AREA_TUNNEL, AREA_CYBERSPACE): AREA_VILLAGE,
    # 到数据港
    (AREA_FOREST, AREA_VILLAGE): AREA_VILLAGE,
    (AREA_NEON_STREET, AREA_VILLAGE): AREA_VILLAGE,
    (AREA_FACTORY, AREA_VILLAGE): AREA_VILLAGE,
    (AREA_CYBERSPACE, AREA_VILLAGE): AREA_VILLAGE,
    # 到废墟荒地
    (AREA_VILLAGE, AREA_FOREST): AREA_FOREST,
    # 到旧数据中心
    (AREA_TUNNEL, AREA_DUNGEON): AREA_DUNGEON,
    (AREA_VILLAGE, AREA_DUNGEON): AREA_FACTORY,
    (AREA_FACTORY, AREA_DUNGEON): AREA_TUNNEL,
}


def _get_waypoint_target(g):
    """获取当前任务的导航目标坐标，返回 (tx, ty) 或 None"""
    wp = _QUEST_WAYPOINTS.get(g.player.quest_stage)
    if not wp:
        return None
    target_area, target_tx, target_ty, _label = wp
    cur_area = g.player.area

    if cur_area == target_area:
        return target_tx, target_ty

    # 不在目标区域 → 找通往目标区域的传送点
    next_area = _AREA_ROUTE.get((cur_area, target_area))
    if not next_area:
        return None

    transitions = g.game_map.transitions.get(cur_area, [])
    for t in transitions:
        if t[2] == next_area:
            return t[0], t[1]
    return None


def draw_explore(g):
    """探索界面主绘制"""
    area = g.player.area
    cam_x, cam_y = int(g.camera_x), int(g.camera_y)

    # 天空渐变
    g._draw_sky(area)

    # 地图瓦片
    mdata = g.game_map.maps.get(area, [])
    start_tx = max(0, cam_x // TILE)
    start_ty = max(0, cam_y // TILE)
    end_tx = min(g.game_map.map_w.get(area, 0), (cam_x + SCREEN_W) // TILE + 2)
    end_ty = min(g.game_map.map_h.get(area, 0), (cam_y + SCREEN_H) // TILE + 2)

    water_frame = (g.tick // 15) % 4

    for ty in range(start_ty, end_ty):
        for tx in range(start_tx, end_tx):
            sx = tx * TILE - cam_x
            sy = ty * TILE - cam_y
            tile = g.game_map.get_tile(area, tx, ty)

            if tile == 0:  # 金属地板变体
                key = 'grass2' if (tx + ty) % 3 == 0 else 'grass'
                g.screen.blit(g.assets.tiles[key], (sx, sy))
            elif tile == 2:  # 数据流（动画）
                g.screen.blit(g.assets.tiles[f'water_{water_frame}'], (sx, sy))
            else:
                entry = g._tile_map.get(tile)
                if entry:
                    g.screen.blit(g.assets.tiles[entry[0]], (sx, sy))
                    if entry[1]:
                        g.screen.blit(g.assets.tiles[entry[1]], (sx, sy))

    # 赛博涂鸦标记
    _SET_COLORS = {'origin': (0, 255, 200), 'rebellion': (255, 50, 150), 'ghost': (180, 60, 255)}
    for gid, gdef in GRAFFITI_DB.items():
        if gdef.area != area:
            continue
        gsx = gdef.tile_x * TILE - cam_x
        gsy = gdef.tile_y * TILE - cam_y
        if not (-TILE < gsx < SCREEN_W + TILE and -TILE < gsy < SCREEN_H + TILE):
            continue
        color = _SET_COLORS.get(gdef.set_id, (0, 255, 200))
        if gid in g.player.graffiti_found:
            # 已发现：明亮符号
            draw_text(g.screen, gdef.symbol, (gsx + TILE // 2, gsy + TILE // 2 - 4),
                      g.assets.font_sm, color, center=True)
        else:
            # 未发现：微弱闪烁霓虹点
            alpha = int(80 + 40 * math.sin(g.tick * 0.08 + gdef.tile_x * 3.7))
            dot_surf = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(dot_surf, (*color, alpha), (3, 3), 3)
            g.screen.blit(dot_surf, (gsx + TILE // 2 - 3, gsy + TILE // 2 - 3))

    # 宝箱
    for (a, cx, cy), (item_key, cnt) in g.chest_positions.items():
        if a == area and (a, cx, cy) not in g.chests_opened:
            sx = cx * TILE - cam_x
            sy = cy * TILE - cam_y
            g.screen.blit(g.assets.tiles['chest'], (sx, sy))

    # 建筑（数据港和霓虹街特有）
    if area in (AREA_VILLAGE, AREA_NEON_STREET):
        houses = [(12, 6), (26, 8), (30, 18)]
        for hx, hy in houses:
            sx = hx * TILE - cam_x
            sy = hy * TILE - cam_y
            g.screen.blit(g.assets.tiles['house'], (sx, sy))

    # NPC
    for npc in g.npcs:
        if npc.area == area:
            sx = npc.x * TILE - cam_x
            sy = npc.y * TILE - cam_y
            sprite = g.assets.npc_sprites.get(npc.sprite_key)
            if sprite:
                # NPC 轻微浮动
                bob = int(math.sin(g.tick * 0.05 + npc.x) * 2)
                g.screen.blit(sprite, (sx, sy + bob))
                # 名字
                draw_text(g.screen, npc.name, (sx + TILE//2, sy - 8),
                          g.assets.font_sm, C_GOLD, center=True)
                # 交互提示
                dist = abs(g.player.tx - npc.x) + abs(g.player.ty - npc.y)
                if dist <= 2:
                    if (g.tick // 20) % 2:
                        # 气泡背景
                        bw_hint = g.assets.font_sm.size("[J]")[0] + 8
                        bh_hint = 18
                        bx_hint = sx + TILE//2 - bw_hint//2
                        by_hint = sy - 28
                        pygame.draw.rect(g.screen, (30, 25, 50), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                        pygame.draw.rect(g.screen, (160, 140, 200), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                        draw_text(g.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                  g.assets.font_sm, C_YELLOW, center=True)

    # 幽灵商人（森林中，闪烁半透明效果）
    if area == AREA_FOREST:
        gx, gy = g.ghost_merchant_npc.x, g.ghost_merchant_npc.y
        sx = gx * TILE - cam_x
        sy = gy * TILE - cam_y
        # 闪烁：用 sin 控制可见度，部分 tick 不显示
        flicker = math.sin(g.tick * 0.08) * 0.5 + 0.5  # 0~1
        if flicker > 0.2:  # 80% 时间可见
            ghost_sprite = g.assets.npc_sprites.get('ghost_merchant')
            if ghost_sprite:
                # 半透明效果
                alpha = int(100 + flicker * 100)  # 100~200
                temp = ghost_sprite.copy()
                temp.set_alpha(alpha)
                bob = int(math.sin(g.tick * 0.04 + gx) * 3)
                g.screen.blit(temp, (sx, sy + bob))
                # 名字（也半透明）
                name_color = (180, 140, 255)
                draw_text(g.screen, "???", (sx + TILE//2, sy - 8),
                          g.assets.font_sm, name_color, center=True)
                # 交互提示
                dist = abs(g.player.tx - gx) + abs(g.player.ty - gy)
                if dist <= 2:
                    if (g.tick // 15) % 2:
                        bw_hint = g.assets.font_sm.size("[J]")[0] + 8
                        bh_hint = 18
                        bx_hint = sx + TILE//2 - bw_hint//2
                        by_hint = sy - 28
                        pygame.draw.rect(g.screen, (40, 20, 60), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                        pygame.draw.rect(g.screen, (180, 140, 220), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                        draw_text(g.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                  g.assets.font_sm, (200, 160, 255), center=True)

    # 恋爱NPC（带心形标记）
    for npc in g.romance_npcs:
        if npc.area == area:
            sx = npc.x * TILE - cam_x
            sy = npc.y * TILE - cam_y
            sprite = g.assets.npc_sprites.get(npc.sprite_key)
            if sprite:
                bob = int(math.sin(g.tick * 0.05 + npc.x * 3) * 2)
                g.screen.blit(sprite, (sx, sy + bob))
                # 名字（粉色）
                draw_text(g.screen, npc.name, (sx + TILE//2, sy - 8),
                          g.assets.font_sm, C_NEON_PINK, center=True)
                # 好感度心形
                rc = None
                for cid, rchar in ROMANCE_CHARS.items():
                    if rchar.name == npc.name:
                        rc = rchar
                        break
                if rc:
                    aff = g.player.get_affection(rc.char_id)
                    if aff > 0:
                        hearts = min(5, aff // 20 + 1)
                        heart_str = "♥" * hearts
                        draw_text(g.screen, heart_str, (sx + TILE//2, sy - 20),
                                  g.assets.font_sm, (255, 80, 120), center=True)
                # 交互提示
                dist = abs(g.player.tx - npc.x) + abs(g.player.ty - npc.y)
                if dist <= 2:
                    if (g.tick // 20) % 2:
                        bw_hint = g.assets.font_sm.size("[J]")[0] + 8
                        bh_hint = 18
                        bx_hint = sx + TILE//2 - bw_hint//2
                        by_hint = sy - 30
                        pygame.draw.rect(g.screen, (50, 20, 30), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                        pygame.draw.rect(g.screen, (255, 100, 150), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                        draw_text(g.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                  g.assets.font_sm, (255, 150, 180), center=True)

    # 玩家
    frames = g.assets.player_frames.get(g.player.direction, [])
    if frames:
        frame_idx = g.player.anim_frame if g.player.moving else 0
        psurf = frames[frame_idx % len(frames)]
        px = int(g.player.x) - cam_x
        py = int(g.player.y) - cam_y
        g.screen.blit(psurf, (px, py))

    # 粒子
    g.particles.draw(g.screen, cam_x, cam_y)

    # 天气/时间视觉叠加
    g._draw_weather_overlay()

    # 对话框
    g.dialogue.draw(g.screen, g.player)

    # HUD
    g._draw_hud()

    # 小地图
    g._draw_minimap()

    # 消息
    if g.message_queue:
        msg, timer = g.message_queue[0]
        alpha = min(255, timer * 4)
        draw_text(g.screen, msg, (SCREEN_W//2, 80), g.assets.font_md, C_GOLD, center=True)

    # 区域名称（进入时短暂显示）
    if g.encounter_steps < 60:
        area_names = {AREA_VILLAGE: "数据港", AREA_FOREST: "废墟荒地", AREA_DUNGEON: "旧数据中心",
                      AREA_NEON_STREET: "霓虹商业街", AREA_FACTORY: "废弃工厂", AREA_CYBERSPACE: "网络空间",
                      AREA_TUNNEL: "地下通道", AREA_BLACK_MARKET: "黑市", AREA_HOME: "家园"}
        name = area_names.get(area, "")
        alpha = max(0, 60 - g.encounter_steps) / 60
        c = tuple(int(255 * alpha) for _ in range(3))
        draw_text(g.screen, name, (SCREEN_W//2, 50), g.assets.font_lg, c, center=True)

    # 送礼界面覆盖层
    if g.gift_mode and g.gift_char_id:
        rc = ROMANCE_CHARS.get(g.gift_char_id)
        giftable = [(k, c) for k, c in g.player.inventory
                     if ITEMS_DB[k].item_type == 'material']
        if rc and giftable:
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            g.screen.blit(overlay, (0, 0))
            bw, bh = 320, 40 + len(giftable) * 26 + 30
            bx = SCREEN_W // 2 - bw // 2
            by = SCREEN_H // 2 - bh // 2
            draw_pixel_rect(g.screen, (18, 14, 32), (bx, by, bw, bh), 2, (255, 80, 150))
            draw_text(g.screen, f"送礼给{rc.name} (X返回)", (SCREEN_W//2, by + 12),
                      g.assets.font_md, C_NEON_PINK, center=True)
            for i, (key, cnt) in enumerate(giftable):
                item = ITEMS_DB[key]
                color = C_YELLOW if i == g.gift_index else C_WHITE
                prefix = ">> " if i == g.gift_index else "   "
                draw_text(g.screen, f"{prefix}{item.name} x{cnt}",
                          (bx + 30, by + 40 + i * 26), g.assets.font_sm, color)

    # 恋爱告白选择覆盖层
    if g.romance_choice_active and g.romance_choice_char:
        rc = ROMANCE_CHARS.get(g.romance_choice_char)
        if rc:
            # 半透明背景
            overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            g.screen.blit(overlay, (0, 0))
            # 选择框
            bw, bh = 360, 160
            bx = SCREEN_W // 2 - bw // 2
            by = SCREEN_H // 2 - bh // 2
            draw_pixel_rect(g.screen, (18, 14, 32), (bx, by, bw, bh), (255, 80, 150))
            draw_text(g.screen, f"♥ {rc.name}向你告白了 ♥", (SCREEN_W//2, by + 20),
                      g.assets.font_md, (255, 150, 200), center=True)
            draw_text(g.screen, "接受后将成为你的伴侣并加入队伍", (SCREEN_W//2, by + 50),
                      g.assets.font_sm, C_WHITE, center=True)
            draw_text(g.screen, "（注意：只能选择一位伴侣！）", (SCREEN_W//2, by + 70),
                      g.assets.font_sm, (255, 200, 100), center=True)
            options = ["接受", "再想想"]
            for i, opt in enumerate(options):
                color = C_NEON_PINK if i == g.romance_choice_index else C_WHITE
                prefix = ">> " if i == g.romance_choice_index else "   "
                draw_text(g.screen, prefix + opt, (SCREEN_W//2, by + 105 + i * 30),
                          g.assets.font_md, color, center=True)


def draw_hud(g):
    """HUD绘制"""
    st = g.player.stats
    # 状态栏背景 - 赛博朋克风
    draw_pixel_rect(g.screen, (8, 10, 25), (8, 8, 220, 60), 2, (0, 130, 120))

    draw_text(g.screen, f"Lv.{st.level} 黑客", (16, 12), g.assets.font_sm, C_NEON_CYAN)
    draw_bar(g.screen, 16, 30, 140, 10, st.hp / st.max_hp, C_HP_BAR)
    draw_text(g.screen, f"HP {st.hp}/{st.max_hp}", (160, 28), g.assets.font_sm)
    draw_bar(g.screen, 16, 44, 140, 10, st.mp / st.max_mp, C_MP_BAR)
    draw_text(g.screen, f"EN {st.mp}/{st.max_mp}", (160, 42), g.assets.font_sm)
    draw_bar(g.screen, 16, 58, 140, 8, st.exp / max(1, st.exp_next), C_EXP_BAR)
    draw_text(g.screen, f"EXP {st.exp}/{st.exp_next}", (160, 55), g.assets.font_sm)

    # 信用点
    draw_text(g.screen, f"CR {st.gold}", (16, 74), g.assets.font_sm, C_NEON_CYAN)
    # 技能点
    if g.player.skill_points > 0:
        draw_text(g.screen, f"SP:{g.player.skill_points}", (100, 74), g.assets.font_sm, C_YELLOW)
    # 主线任务提示
    quest_hints = {
        0: "与城市管理员对话",
        1: "击败工厂Boss：失控监工",
        2: "通过地下通道到旧数据中心",
        3: "前往网络空间找AI先知",
        4: "击败量子霸主·真身",
        5: "通关！自由探索",
    }
    hint = quest_hints.get(g.player.quest_stage, "")
    if hint:
        draw_text(g.screen, f"[主线] {hint}", (SCREEN_W // 2, SCREEN_H - 16),
                  g.assets.font_sm, C_GOLD, center=True)

    # 方向指示箭头
    wp_target = _get_waypoint_target(g)
    if wp_target:
        _draw_direction_arrow(g, wp_target)

    # 天气/时间 HUD (右上角小地图下方)
    phase = g._get_time_phase()
    weather = g.player.weather
    phase_icons = {'dawn': '☀', 'day': '☀', 'dusk': '☾', 'night': '☾'}
    weather_icons = {'clear': '', 'rain': '🌧', 'fog': '🌫', 'storm': '⚡'}
    phase_names = {'dawn': '黎明', 'day': '白天', 'dusk': '黄昏', 'night': '夜晚'}
    weather_names = {'clear': '晴朗', 'rain': '雨天', 'fog': '迷雾', 'storm': '风暴'}
    time_text = f"{phase_icons.get(phase, '')} {phase_names.get(phase, '')} {weather_icons.get(weather, '')} {weather_names.get(weather, '')}"
    draw_text(g.screen, time_text, (SCREEN_W - 140, 108), g.assets.font_sm, (140, 160, 180))


def _draw_direction_arrow(g, target):
    """在屏幕边缘绘制指向目标的方向箭头"""
    tx, ty = target
    px, py = g.player.tx, g.player.ty
    dx, dy = tx - px, ty - py
    dist = math.sqrt(dx * dx + dy * dy)
    if dist < 2:
        # 目标很近，画一个脉冲圆圈提示而非箭头
        scr_tx = (tx - px) * TILE + SCREEN_W // 2
        scr_ty = (ty - py) * TILE + SCREEN_H // 2
        if 0 <= scr_tx < SCREEN_W and 0 <= scr_ty < SCREEN_H:
            pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 80) + 40
            ring_surf = pygame.Surface((28, 28), pygame.SRCALPHA)
            pygame.draw.circle(ring_surf, (0, 255, 200, pulse), (14, 14), 12, 2)
            g.screen.blit(ring_surf, (scr_tx - 14, scr_ty - 14))
        return

    angle = math.atan2(dy, dx)
    # 箭头位置：屏幕边缘，任务提示上方
    arrow_cx = SCREEN_W // 2 + int(math.cos(angle) * 60)
    arrow_cy = SCREEN_H - 38

    # 脉冲透明度
    pulse_a = int(abs(math.sin(pygame.time.get_ticks() * 0.004)) * 100) + 155
    arrow_surf = pygame.Surface((24, 24), pygame.SRCALPHA)

    # 画三角箭头（指向angle方向）
    size = 10
    tip = (12 + math.cos(angle) * size, 12 + math.sin(angle) * size)
    left = (12 + math.cos(angle + 2.5) * size * 0.7, 12 + math.sin(angle + 2.5) * size * 0.7)
    right = (12 + math.cos(angle - 2.5) * size * 0.7, 12 + math.sin(angle - 2.5) * size * 0.7)
    pygame.draw.polygon(arrow_surf, (0, 255, 200, pulse_a), [tip, left, right])

    g.screen.blit(arrow_surf, (arrow_cx - 12, arrow_cy - 12))

    # 距离文字
    wp = _QUEST_WAYPOINTS.get(g.player.quest_stage)
    if wp:
        label = wp[3]
        in_same_area = g.player.area == wp[0]
        dist_text = f"{label} {int(dist)}" if in_same_area else f"→{label}"
        draw_text(g.screen, dist_text, (arrow_cx, arrow_cy + 10),
                  g.assets.font_sm, (0, 220, 180), center=True)


_MINIMAP_TILE_COLORS = {
    0: (30, 35, 45, 180),
    6: (30, 35, 45, 180),
    1: (0, 150, 130, 180),
    2: (0, 100, 180, 180),
    3: (50, 55, 65, 180),
    4: (80, 90, 110, 180),
    5: (20, 25, 40, 180),
    7: (0, 255, 200, 180),
    8: (45, 40, 35, 180),
    9: (10, 10, 30, 180),
    10: (20, 15, 40, 180),
    19: (25, 22, 18, 180),
    20: (40, 30, 22, 180),
    21: (50, 35, 15, 180),
    22: (60, 50, 35, 180),
}
_MINIMAP_DEFAULT_COLOR = (15, 15, 25, 180)


def draw_minimap(g):
    """小地图绘制"""
    mm_w, mm_h = 120, 90
    mm_x, mm_y = SCREEN_W - mm_w - 10, 10
    mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
    mm_surf.fill((0, 0, 0, 140))

    area = g.player.area
    mw = g.game_map.map_w.get(area, 1)
    mh = g.game_map.map_h.get(area, 1)
    sx = mm_w / mw
    sy = mm_h / mh

    mdata = g.game_map.maps.get(area, [])
    for ty, row in enumerate(mdata):
        for tx, tile in enumerate(row):
            px = int(tx * sx)
            py = int(ty * sy)
            pw = max(1, int(sx))
            ph = max(1, int(sy))
            c = _MINIMAP_TILE_COLORS.get(tile, _MINIMAP_DEFAULT_COLOR)
            pygame.draw.rect(mm_surf, c, (px, py, pw, ph))

    # 玩家位置
    ppx = int(g.player.tx * sx)
    ppy = int(g.player.ty * sy)
    pygame.draw.rect(mm_surf, (0, 255, 200, 255), (ppx - 1, ppy - 1, 3, 3))

    # NPC位置
    for npc in g.npcs:
        if npc.area == area:
            npx = int(npc.x * sx)
            npy = int(npc.y * sy)
            pygame.draw.rect(mm_surf, (255, 220, 50, 255), (npx, npy, 2, 2))

    # 任务目标标记（脉冲菱形）
    wp_target = _get_waypoint_target(g)
    if wp_target:
        wtx, wty = wp_target
        wmx = int(wtx * sx)
        wmy = int(wty * sy)
        pulse = int(abs(math.sin(pygame.time.get_ticks() * 0.005)) * 155) + 100
        pygame.draw.polygon(mm_surf, (255, 80, 80, pulse),
                            [(wmx, wmy - 3), (wmx + 3, wmy), (wmx, wmy + 3), (wmx - 3, wmy)])

    # 出口标记（小地图边缘的绿色短线）
    transitions = g.game_map.transitions.get(area, [])
    for t in transitions:
        ex = int(t[0] * sx)
        ey = int(t[1] * sy)
        ex = max(0, min(mm_w - 2, ex))
        ey = max(0, min(mm_h - 2, ey))
        pygame.draw.rect(mm_surf, (0, 255, 140, 200), (ex, ey, 2, 2))

    # 边框
    pygame.draw.rect(mm_surf, (140, 120, 180, 200), (0, 0, mm_w, mm_h), 2)

    g.screen.blit(mm_surf, (mm_x, mm_y))

    # 小地图下方显示区域名
    _AREA_NAMES = {
        AREA_VILLAGE: "数据港", AREA_FOREST: "废墟荒地", AREA_DUNGEON: "旧数据中心",
        AREA_NEON_STREET: "霓虹街", AREA_FACTORY: "废弃工厂", AREA_CYBERSPACE: "网络空间",
        AREA_TUNNEL: "地下通道", AREA_BLACK_MARKET: "黑市", AREA_HOME: "家园",
    }
    area_name = _AREA_NAMES.get(area, area)
    draw_text(g.screen, area_name, (mm_x + mm_w // 2, mm_y + mm_h + 2),
              g.assets.font_sm, (120, 140, 160), center=True)
