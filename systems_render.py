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
            draw_pixel_rect(g.screen, (20, 10, 30), (bx, by, bw, bh), 2, (255, 80, 150))
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
            draw_pixel_rect(g.screen, (20, 10, 30), (bx, by, bw, bh), (255, 80, 150))
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
    draw_pixel_rect(g.screen, (8, 10, 25), (8, 8, 220, 60), 2, (0, 150, 130))

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

    # 天气/时间 HUD (右上角小地图下方)
    phase = g._get_time_phase()
    weather = g.player.weather
    phase_icons = {'dawn': '☀', 'day': '☀', 'dusk': '☾', 'night': '☾'}
    weather_icons = {'clear': '', 'rain': '🌧', 'fog': '🌫', 'storm': '⚡'}
    phase_names = {'dawn': '黎明', 'day': '白天', 'dusk': '黄昏', 'night': '夜晚'}
    weather_names = {'clear': '晴朗', 'rain': '雨天', 'fog': '迷雾', 'storm': '风暴'}
    time_text = f"{phase_icons.get(phase, '')} {phase_names.get(phase, '')} {weather_icons.get(weather, '')} {weather_names.get(weather, '')}"
    draw_text(g.screen, time_text, (SCREEN_W - 140, 108), g.assets.font_sm, (140, 160, 180))


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

    # 边框
    pygame.draw.rect(mm_surf, (140, 120, 180, 200), (0, 0, mm_w, mm_h), 2)

    g.screen.blit(mm_surf, (mm_x, mm_y))
