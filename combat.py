"""战斗系统 - 赛博朋克主题"""

import random
import pygame
from enum import Enum, auto
from constants import (SCREEN_W, SCREEN_H, TILE, C_WHITE, C_YELLOW, C_RED, C_GREEN,
                       C_GOLD, C_PANEL, C_PANEL_BORDER, C_HP_BAR, C_MP_BAR,
                       C_NEON_CYAN, C_NEON_PINK, C_NEON_PURPLE,
                       draw_pixel_rect, draw_text, draw_bar)
from entities import (Player, ITEMS_DB, ENEMY_DEFS, StatusEffect, SKILL_TREE)
from particles import ParticleSystem
from assets import Assets


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
        self.enemy_key = enemy_key
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
        self.enemy_weakness = edef.weakness
        self.enemy_drops = edef.drops
        self.is_boss = edef.is_boss
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
        self.player_skills = player.get_combat_skills()
        self.show_items = False
        self.show_skills = False
        self.turn_count = 0
        # 状态效果
        self.player_effects: list[StatusEffect] = []
        self.enemy_effects: list[StatusEffect] = []
        # Boss阶段台词
        self.boss_phase_shown = set()
        # 掉落结果
        self.dropped_items: list[tuple[str, int]] = []

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
                elif self.menu_index == 3:  # 撤退
                    if self.is_boss:
                        self.message = "Boss战无法撤退！"
                        self.msg_timer = 60
                    elif random.random() < 0.5:
                        self.state = CombatState.FLEE
                        self.message = "成功撤退！"
                    else:
                        self.message = "撤退失败！"
                        self._start_anim('flee_fail')
        return True

    def _handle_item_menu(self, event):
        consumables = [(k, c) for k, c in self.player.inventory if ITEMS_DB[k].item_type == 'consumable']
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.show_items = False
        elif event.key == pygame.K_UP and consumables:
            self.item_index = (self.item_index - 1) % len(consumables)
        elif event.key == pygame.K_DOWN and consumables:
            self.item_index = (self.item_index + 1) % len(consumables)
        elif event.key in (pygame.K_RETURN, pygame.K_j) and consumables:
            if self.item_index < len(consumables):
                key, cnt = consumables[self.item_index]
                if key == 'antivirus':
                    # 清除负面状态
                    self.player_effects = [e for e in self.player_effects if e.name in ('atk_up', 'def_up', 'regen')]
                    self.player.remove_item(key)
                    self.message = "清除了所有负面状态！"
                else:
                    self.player.use_item(key)
                    item = ITEMS_DB[key]
                    self.message = f"使用了{item.name}！"
                self.show_items = False
                self._start_anim('item')
        return True

    def _handle_skill_menu(self, event):
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.show_skills = False
        elif event.key == pygame.K_UP:
            self.skill_index = (self.skill_index - 1) % len(self.player_skills)
        elif event.key == pygame.K_DOWN:
            self.skill_index = (self.skill_index + 1) % len(self.player_skills)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            name, power, cost = self.player_skills[self.skill_index]
            if self.player.stats.mp >= cost:
                self.player.stats.mp -= cost
                self._execute_skill(name, power)
                self.show_skills = False
            else:
                self.message = "EN不足！"
                self.msg_timer = 40
        return True

    def _execute_skill(self, name, power):
        """执行技能（包括基础技能和技能树技能）"""
        # 基础技能
        if name == "系统修复":
            heal = 30
            self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal)
            self.message = f"系统修复！HP恢复{heal}！"
            self._start_anim('heal')
            return
        if name == "黑客攻击":
            dmg = self._calc_skill_damage(power, 'hack')
            self.enemy_hp -= dmg
            self.message = f"黑客攻击！造成{dmg}点伤害！"
            self._apply_lifesteal(dmg)
            self._start_anim('skill')
            return
        if name == "EMP脉冲":
            dmg = self._calc_skill_damage(power, 'emp')
            self.enemy_hp -= dmg
            self.message = f"EMP脉冲！造成{dmg}点伤害！"
            self._apply_lifesteal(dmg)
            self._start_anim('skill')
            return

        # 技能树技能
        # 查找对应的技能节点
        node = None
        for sid, sn in SKILL_TREE.items():
            if sn.name == name and sid in self.player.unlocked_skills:
                node = sn
                break
        if not node:
            return

        eff = node.effect
        if node.skill_id == 'atk_t2':  # 连击
            total_dmg = 0
            for _ in range(eff['hits']):
                dmg = int(self.player.get_total_atk() * eff['power_pct'] / 100)
                dmg = max(1, dmg - self.enemy_def // 2)
                dmg = self._apply_crit(dmg)
                total_dmg += dmg
            self.enemy_hp -= total_dmg
            self.message = f"连击！{eff['hits']}次攻击共造成{total_dmg}点伤害！"
            self._apply_lifesteal(total_dmg)
            self._start_anim('skill')
        elif node.skill_id == 'atk_t4':  # 毁灭打击
            dmg = int(self.player.get_total_atk() * eff['power_pct'] / 100)
            dmg = max(1, dmg - self.enemy_def // 2)
            dmg = self._apply_crit(dmg)
            self.enemy_hp -= dmg
            self.message = f"毁灭打击！造成{dmg}点伤害！"
            self._apply_lifesteal(dmg)
            self._start_anim('skill')
        elif node.skill_id == 'def_t4':  # 铁壁
            self.player_effects.append(StatusEffect('def_up', eff['duration'], self.player.get_total_def()))
            self.message = f"铁壁！防御力翻倍{eff['duration']}回合！"
            self._start_anim('buff')
        elif node.skill_id == 'hack_t2':  # 数据窃取
            dmg = int(self.player.get_total_atk() * eff['power_pct'] / 100)
            dmg = max(1, dmg - self.enemy_def // 2)
            stolen = random.randint(5, 20)
            self.player.stats.gold += stolen
            self.enemy_hp -= dmg
            self.message = f"数据窃取！造成{dmg}伤害，偷取{stolen}信用点！"
            self._apply_lifesteal(dmg)
            self._start_anim('skill')
        elif node.skill_id == 'hack_t3':  # 病毒注入
            poison_val = int(self.player.get_total_atk() * eff['poison_pct'])
            self.enemy_effects.append(StatusEffect('poison', eff['poison_turns'], poison_val))
            self.message = f"病毒注入！敌人中毒{eff['poison_turns']}回合！"
            self._start_anim('skill')
        elif node.skill_id == 'hack_t4':  # 系统接管
            self.enemy_effects.append(StatusEffect('stun', eff['stun_turns'], 0))
            self.message = f"系统接管！敌人眩晕{eff['stun_turns']}回合！"
            self._start_anim('skill')

    def _calc_skill_damage(self, power, skill_type):
        """计算技能伤害，含弱点判定"""
        base = self.player.get_total_atk() + power
        dmg = max(1, base - self.enemy_def)
        # 弱点判定
        if self.enemy_weakness and self.enemy_weakness == skill_type:
            dmg = int(dmg * 1.5)
            self.message = ""  # 会被覆盖
        dmg = self._apply_crit(dmg)
        return dmg

    def _apply_crit(self, dmg):
        """暴击判定"""
        if 'atk_t3' in self.player.unlocked_skills:
            eff = SKILL_TREE['atk_t3'].effect
            if random.random() < eff['crit_chance']:
                dmg = int(dmg * eff['crit_mult'])
        return dmg

    def _apply_lifesteal(self, dmg):
        """生命汲取"""
        if 'def_t3' in self.player.unlocked_skills:
            heal = int(dmg * SKILL_TREE['def_t3'].effect['lifesteal'])
            if heal > 0:
                self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal)

    def _player_attack(self):
        atk = self.player.get_total_atk()
        # 弱点判定（普通攻击视为physical）
        weakness_hit = self.enemy_weakness == 'physical'
        dmg = max(1, atk - self.enemy_def + random.randint(-2, 2))
        if weakness_hit:
            dmg = int(dmg * 1.5)
        dmg = self._apply_crit(dmg)
        self.enemy_hp -= dmg
        self._apply_lifesteal(dmg)
        weak_text = " 弱点命中！" if weakness_hit else ""
        self.message = f"攻击！造成{dmg}点伤害！{weak_text}"
        self._start_anim('attack')

    def _start_anim(self, anim_type):
        self.anim_type = anim_type
        self.anim_timer = 30
        self.state = CombatState.ANIM

    def _apply_turn_start_effects(self, effects, is_player):
        """回合开始时应用状态效果"""
        msgs = []
        for eff in effects:
            if eff.name == 'poison':
                if is_player:
                    self.player.stats.hp -= eff.value
                    msgs.append(f"中毒！受到{eff.value}伤害")
                else:
                    self.enemy_hp -= eff.value
                    msgs.append(f"{self.enemy_name}中毒！受到{eff.value}伤害")
            elif eff.name == 'regen':
                if is_player:
                    self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + eff.value)
                    msgs.append(f"再生！恢复{eff.value}HP")
        return msgs

    def _tick_effects(self, effects):
        """减少持续时间，移除过期效果"""
        for eff in effects:
            eff.duration -= 1
        return [e for e in effects if e.duration > 0]

    def _is_stunned(self, effects):
        return any(e.name == 'stun' for e in effects)

    def _get_def_buff(self, effects):
        """获取防御增益"""
        for e in effects:
            if e.name == 'def_up':
                return e.value
        return 0

    def update(self):
        self.msg_timer = max(0, self.msg_timer - 1)
        self.particles.update()

        if self.state == CombatState.ANIM:
            self.anim_timer -= 1
            if self.anim_type in ('attack', 'skill'):
                self.shake_x = random.randint(-3, 3)
                self.shake_y = random.randint(-2, 2)
            else:
                self.shake_x = self.shake_y = 0
            if self.anim_timer <= 0:
                self.shake_x = self.shake_y = 0
                if self.enemy_hp <= 0:
                    self._on_victory()
                elif self.anim_type in ('flee_fail', 'attack', 'skill', 'item', 'heal', 'buff'):
                    self._enemy_turn()
                else:
                    self.state = CombatState.PLAYER_CHOOSE

    def _enemy_turn(self):
        self.turn_count += 1
        # 敌人回合开始：应用敌人状态效果
        msgs = self._apply_turn_start_effects(self.enemy_effects, False)
        self.enemy_effects = self._tick_effects(self.enemy_effects)
        if self.enemy_hp <= 0:
            self._on_victory()
            return
        # 眩晕检查
        if self._is_stunned(self.enemy_effects):
            self.message = f"{self.enemy_name}被眩晕，无法行动！"
            # 玩家回合开始效果
            p_msgs = self._apply_turn_start_effects(self.player_effects, True)
            self.player_effects = self._tick_effects(self.player_effects)
            if self.player.stats.hp <= 0:
                self.state = CombatState.DEFEAT
                self.message = "系统崩溃..."
                return
            self.state = CombatState.PLAYER_CHOOSE
            return

        # Boss阶段台词
        if self.is_boss:
            self._check_boss_phase()

        # 敌人行动
        if self.enemy_skills and random.random() < 0.4:
            skill_name, skill_power = random.choice(self.enemy_skills)
            if skill_name == "防火墙":
                # AI核心Boss特殊技能：回复HP
                heal = 20
                self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
                self.message = f"{self.enemy_name}启动防火墙！恢复{heal}HP！"
            else:
                player_def = self.player.get_total_def() + self._get_def_buff(self.player_effects)
                dmg = max(1, skill_power - player_def + random.randint(-2, 2))
                # 反击判定
                counter_dmg = self._check_counter(dmg)
                self.player.stats.hp -= dmg
                counter_text = f" 反击{counter_dmg}！" if counter_dmg > 0 else ""
                self.message = f"{self.enemy_name}使用{skill_name}！造成{dmg}点伤害！{counter_text}"
        else:
            player_def = self.player.get_total_def() + self._get_def_buff(self.player_effects)
            dmg = max(1, self.enemy_atk - player_def + random.randint(-2, 2))
            counter_dmg = self._check_counter(dmg)
            self.player.stats.hp -= dmg
            counter_text = f" 反击{counter_dmg}！" if counter_dmg > 0 else ""
            self.message = f"{self.enemy_name}攻击！造成{dmg}点伤害！{counter_text}"

        # 玩家回合开始效果
        p_msgs = self._apply_turn_start_effects(self.player_effects, True)
        self.player_effects = self._tick_effects(self.player_effects)

        if self.player.stats.hp <= 0:
            self.state = CombatState.DEFEAT
            self.message = "系统崩溃..."
        else:
            self.state = CombatState.PLAYER_CHOOSE

    def _check_counter(self, incoming_dmg):
        """反击判定"""
        if 'def_t2' in self.player.unlocked_skills:
            if random.random() < SKILL_TREE['def_t2'].effect['counter_chance']:
                counter_dmg = incoming_dmg // 3
                self.enemy_hp -= counter_dmg
                return counter_dmg
        return 0

    def _check_boss_phase(self):
        """Boss阶段台词"""
        hp_pct = self.enemy_hp / self.enemy_max_hp
        phases = {
            0.75: "哼，你还有点本事...",
            0.50: "不可能...我要全力出击！",
            0.25: "系统...过载...启动最终协议！",
        }
        for threshold, line in phases.items():
            if hp_pct <= threshold and threshold not in self.boss_phase_shown:
                self.boss_phase_shown.add(threshold)
                self.message = f"{self.enemy_name}：{line}"
                break

    def _on_victory(self):
        self.enemy_hp = 0
        self.state = CombatState.VICTORY
        exp = self.enemy_exp
        gold = self.enemy_gold
        # 加密货币翻倍
        if self.player.has_item('lucky_coin') or self.player.equipped.get('accessory') == 'lucky_coin':
            gold *= 2
        self.player.stats.exp += exp
        self.player.stats.gold += gold
        # 掉落物品
        self.dropped_items = []
        for item_key, rate in self.enemy_drops:
            if random.random() < rate:
                self.player.add_item(item_key)
                self.dropped_items.append((item_key, 1))
        drop_text = ""
        if self.dropped_items:
            names = [ITEMS_DB[k].name for k, _ in self.dropped_items]
            drop_text = f" 掉落：{'、'.join(names)}"
        self.message = f"胜利！获得{exp}EXP {gold}信用点！{drop_text}"
        # 升级检查
        while self.player.stats.exp >= self.player.stats.exp_next:
            self.player.stats.exp -= self.player.stats.exp_next
            self.player.stats.level += 1
            self.player.stats.max_hp += 15
            self.player.stats.hp = self.player.stats.max_hp
            self.player.stats.max_mp += 8
            self.player.stats.mp = self.player.stats.max_mp
            self.player.stats.atk += 3
            self.player.stats.defense += 2
            self.player.stats.exp_next = int(self.player.stats.exp_next * 1.5)
            self.player.skill_points += 1
            self.message += f" 升级到Lv{self.player.stats.level}！获得1技能点！"

    def draw(self, surf):
        surf.fill((8, 8, 18))
        # 战斗背景
        for y in range(0, SCREEN_H, 4):
            c = int(15 + y * 0.02)
            pygame.draw.line(surf, (c, c, c + 10), (0, y), (SCREEN_W, y))

        # 敌人
        ex = SCREEN_W // 2 - 32 + self.shake_x
        ey = 100 + self.shake_y
        enemy_sprite = self.assets.enemy_sprites.get(self.enemy_sprite_key)
        if enemy_sprite:
            surf.blit(enemy_sprite, (ex, ey))
        else:
            pygame.draw.rect(surf, C_RED, (ex, ey, 64, 64))
        # 敌人名字和HP
        draw_text(surf, self.enemy_name, (SCREEN_W // 2, 70), self.assets.font_md, C_NEON_PINK, center=True)
        bar_w = 200
        bar_x = SCREEN_W // 2 - bar_w // 2
        draw_bar(surf, bar_x, 185, bar_w, 10, self.enemy_hp / self.enemy_max_hp, C_HP_BAR)
        draw_text(surf, f"{max(0, self.enemy_hp)}/{self.enemy_max_hp}", (SCREEN_W // 2, 197),
                  self.assets.font_sm, C_WHITE, center=True)
        # 弱点提示
        if self.enemy_weakness:
            weak_names = {'emp': 'EMP', 'hack': '黑客', 'physical': '物理'}
            draw_text(surf, f"弱点:{weak_names.get(self.enemy_weakness, '?')}", (SCREEN_W // 2, 212),
                      self.assets.font_sm, C_YELLOW, center=True)
        # 敌人状态效果图标
        ex_eff = bar_x
        for eff in self.enemy_effects:
            eff_colors = {'poison': C_GREEN, 'stun': C_YELLOW, 'atk_up': C_RED, 'def_up': C_NEON_CYAN}
            c = eff_colors.get(eff.name, C_WHITE)
            draw_text(surf, f"[{eff.name[:3]}{eff.duration}]", (ex_eff, 228), self.assets.font_sm, c)
            ex_eff += 50

        # 面板
        panel_y = SCREEN_H - 180
        draw_pixel_rect(surf, C_PANEL, (0, panel_y, SCREEN_W, 180), 2, C_PANEL_BORDER)

        # 玩家信息
        px = 20
        draw_text(surf, f"Lv{self.player.stats.level} 赛博行者", (px, panel_y + 10), self.assets.font_md, C_NEON_CYAN)
        draw_bar(surf, px, panel_y + 32, 150, 10, self.player.stats.hp / self.player.stats.max_hp, C_HP_BAR)
        draw_text(surf, f"HP {self.player.stats.hp}/{self.player.stats.max_hp}", (px, panel_y + 44), self.assets.font_sm)
        draw_bar(surf, px, panel_y + 58, 150, 10, self.player.stats.mp / self.player.stats.max_mp, C_MP_BAR)
        draw_text(surf, f"EN {self.player.stats.mp}/{self.player.stats.max_mp}", (px, panel_y + 70), self.assets.font_sm)
        # 玩家状态效果
        pe_x = px
        for eff in self.player_effects:
            eff_colors = {'poison': C_GREEN, 'stun': C_YELLOW, 'def_up': C_NEON_CYAN, 'regen': (100, 255, 100)}
            c = eff_colors.get(eff.name, C_WHITE)
            draw_text(surf, f"[{eff.name[:3]}{eff.duration}]", (pe_x, panel_y + 86), self.assets.font_sm, c)
            pe_x += 50

        # 消息
        draw_text(surf, self.message, (px, panel_y + 105), self.assets.font_md, C_WHITE)

        # 菜单
        if self.state == CombatState.PLAYER_CHOOSE:
            menu_x = SCREEN_W - 200
            if self.show_items:
                self._draw_item_menu(surf, menu_x, panel_y + 10)
            elif self.show_skills:
                self._draw_skill_menu(surf, menu_x, panel_y + 10)
            else:
                options = ["[A] 攻击", "[S] 技能", "[I] 物品", "[R] 撤退"]
                for i, opt in enumerate(options):
                    color = C_YELLOW if i == self.menu_index else C_WHITE
                    prefix = ">> " if i == self.menu_index else "   "
                    draw_text(surf, prefix + opt, (menu_x, panel_y + 12 + i * 28), self.assets.font_md, color)

        if self.state in (CombatState.VICTORY, CombatState.DEFEAT, CombatState.FLEE):
            draw_text(surf, "按确认键继续...", (SCREEN_W//2, panel_y + 155), self.assets.font_sm, C_GOLD, center=True)

    def _draw_item_menu(self, surf, x, y):
        consumables = [(k, c) for k, c in self.player.inventory if ITEMS_DB[k].item_type == 'consumable']
        draw_text(surf, "【物品】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        if not consumables:
            draw_text(surf, "没有可用物品", (x, y + 22), self.assets.font_sm)
            return
        for i, (key, cnt) in enumerate(consumables):
            color = C_YELLOW if i == self.item_index else C_WHITE
            prefix = ">> " if i == self.item_index else "   "
            draw_text(surf, f"{prefix}{ITEMS_DB[key].name} x{cnt}", (x, y + 22 + i * 22), self.assets.font_sm, color)

    def _draw_skill_menu(self, surf, x, y):
        draw_text(surf, "【技能】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        for i, (name, power, cost) in enumerate(self.player_skills):
            color = C_YELLOW if i == self.skill_index else C_WHITE
            if self.player.stats.mp < cost:
                color = (100, 100, 100)
            prefix = ">> " if i == self.skill_index else "   "
            draw_text(surf, f"{prefix}{name} (EN:{cost})", (x, y + 22 + i * 22), self.assets.font_sm, color)
