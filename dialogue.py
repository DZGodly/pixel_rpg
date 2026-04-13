"""对话系统 - 赛博朋克主题"""

import pygame
from typing import List, Tuple
from constants import (SCREEN_W, SCREEN_H, C_WHITE, C_YELLOW, C_GOLD, C_GREEN,
                       C_NEON_CYAN, C_NEON_PURPLE,
                       draw_pixel_rect, draw_text)
from entities import Player, NPC, ITEMS_DB
from assets import Assets


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

    def start(self, npc: NPC, quest_stage: int = 0):
        self.active = True
        self.npc_name = npc.name
        self.lines = npc.get_dialogues(quest_stage)
        self.line_index = 0
        self.char_index = 0
        self.char_timer = 0
        self.shop_mode = False
        self.shop_tab = 0
        self.sell_index = 0
        self.shop_msg = ""
        self.shop_msg_timer = 0
        # 升级商店模式
        self.upgrade_mode = False
        self.upgrade_index = 0
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
                        self.shop_msg = "信用点不足！"
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
                        self.shop_msg = f"卖出{ITEMS_DB[item_key].name}，获得{sell_price}信用点"
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
        # 对话框 - 赛博朋克风
        bx, by, bw, bh = 40, SCREEN_H - 170, SCREEN_W - 80, 140
        draw_pixel_rect(surf, (8, 10, 25), (bx, by, bw, bh), 3, (0, 200, 180))

        # NPC名字
        name_w = self.assets.font_md.size(self.npc_name)[0] + 20
        draw_pixel_rect(surf, (15, 18, 35), (bx + 10, by - 16, name_w, 28), 2, (0, 200, 180))
        draw_text(surf, self.npc_name, (bx + 20, by - 12), self.assets.font_md, C_NEON_CYAN)

        if self.shop_mode:
            # Tab 标签：购买 / 出售
            tab_w = 80
            for ti, tab_name in enumerate(["购买", "出售"]):
                tx = bx + 20 + ti * (tab_w + 10)
                ty = by + 8
                if ti == self.shop_tab:
                    draw_pixel_rect(surf, (20, 25, 50), (tx, ty, tab_w, 22), 2, (0, 255, 200))
                    draw_text(surf, tab_name, (tx + tab_w//2, ty + 3), self.assets.font_sm, C_NEON_CYAN, center=True)
                else:
                    draw_pixel_rect(surf, (12, 14, 30), (tx, ty, tab_w, 22), 1, (60, 70, 90))
                    draw_text(surf, tab_name, (tx + tab_w//2, ty + 3), self.assets.font_sm, (100, 110, 130), center=True)
            # ←→ 提示
            draw_text(surf, "←→切换", (bx + bw - 80, by + 12), self.assets.font_sm, (120, 120, 140))

            list_y = by + 36
            desc_item = None  # 当前选中物品，用于显示描述
            if self.shop_tab == 0:
                # 购买列表
                for i, (key, price) in enumerate(self.shop_items):
                    item = ITEMS_DB[key]
                    color = C_YELLOW if i == self.shop_index else C_WHITE
                    prefix = ">> " if i == self.shop_index else "   "
                    affordable = "  " if player and player.stats.gold >= price else "✗ "
                    draw_text(surf, f"{prefix}{affordable}{item.name} - {price}G", (bx + 30, list_y + i * 22), self.assets.font_sm, color)
                if self.shop_index < len(self.shop_items):
                    desc_item = ITEMS_DB[self.shop_items[self.shop_index][0]]
                li = len(self.shop_items)
                color = C_YELLOW if self.shop_index == li else C_WHITE
                prefix = ">> " if self.shop_index == li else "   "
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
                    prefix = ">> " if i == self.sell_index else "   "
                    draw_text(surf, f"{prefix}{item.name} x{cnt} → {sell_price}G", (bx + 30, list_y + i * 22), self.assets.font_sm, color)
                if sellable and self.sell_index < len(sellable):
                    desc_item = ITEMS_DB[sellable[self.sell_index][0]]
                li = len(sellable)
                color = C_YELLOW if self.sell_index == li else C_WHITE
                prefix = ">> " if self.sell_index == li else "   "
                draw_text(surf, f"{prefix}离开", (bx + 30, list_y + li * 22), self.assets.font_sm, color)
                if not sellable:
                    draw_text(surf, "没有可出售的物品", (bx + 30, list_y), self.assets.font_sm, (140, 140, 140))

            # 物品描述
            if desc_item:
                draw_text(surf, desc_item.description, (bx + 30, by + bh - 38), self.assets.font_sm, (180, 180, 200))

            # 信用点
            gold = player.stats.gold if player else 0
            draw_text(surf, f"信用点: {gold}", (bx + bw - 130, by + 12), self.assets.font_sm, C_GOLD)
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
