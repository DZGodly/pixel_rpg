"""战斗系统 - 赛博朋克主题"""

import random
import pygame
from enum import Enum, auto
from constants import (SCREEN_W, SCREEN_H, TILE, C_WHITE, C_YELLOW, C_RED, C_GREEN,
                       C_GOLD, C_PANEL, C_PANEL_BORDER, C_HP_BAR, C_MP_BAR,
                       C_NEON_CYAN, C_NEON_PINK, C_NEON_PURPLE,
                       draw_pixel_rect, draw_text, draw_bar)
from entities import (Player, ITEMS_DB, ENEMY_DEFS, StatusEffect, SKILL_TREE,
                      ROMANCE_CHARS, PETS_DB, ACHIEVEMENTS, MEALS_DB)
from particles import ParticleSystem
from assets import Assets


class CombatState(Enum):
    PLAYER_CHOOSE = auto()
    PLAYER_ATTACK = auto()
    PLAYER_SKILL = auto()
    PLAYER_ITEM = auto()
    PLAYER_PARTNER = auto()
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
        # 成就追踪
        self.damage_taken = 0
        # 数据残响（连击系统）
        self.action_history: list[str] = []
        # 状态效果
        self.player_effects: list[StatusEffect] = []
        self.enemy_effects: list[StatusEffect] = []
        # Boss阶段台词
        self.boss_phase_shown = set()
        # 掉落结果
        self.dropped_items: list[tuple[str, int]] = []
        # 伴侣参战
        self.partner_def = player.get_partner_def()
        if self.partner_def:
            stats = player.get_partner_combat_stats()
            self.partner_max_hp = stats[0]
            self.partner_atk = stats[1]
            self.partner_defense = stats[2]
            self.partner_hp = min(player.partner_hp, self.partner_max_hp)
            self.partner_skills = player.get_partner_skills()
        else:
            self.partner_max_hp = 0
            self.partner_atk = 0
            self.partner_defense = 0
            self.partner_hp = 0
            self.partner_skills = []
        self.partner_skill_index = 0
        self.show_partner_skills = False
        # 宠物参战
        self.pet_def = PETS_DB.get(player.active_pet) if player.active_pet else None
        self.pet_timer = 0  # 宠物技能计时
        # 进化宠物使用进化技能
        if self.pet_def and player.active_pet and player.is_pet_evolved(player.active_pet):
            if self.pet_def.evolved_combat_skill:
                self.pet_evolved = True
            else:
                self.pet_evolved = False
        else:
            self.pet_evolved = False
        # 料理buff
        self.meal_buff_turns = player.meal_buff_turns
        self.meal_def = MEALS_DB.get(player.active_meal) if player.active_meal else None

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
            if self.show_partner_skills:
                return self._handle_partner_skill_menu(event)
            menu_count = 5 if (self.partner_def and self.partner_hp > 0) else 4
            if event.key == pygame.K_UP:
                self.menu_index = (self.menu_index - 1) % menu_count
            elif event.key == pygame.K_DOWN:
                self.menu_index = (self.menu_index + 1) % menu_count
            elif event.key in (pygame.K_RETURN, pygame.K_j):
                if self.menu_index == 0:  # 攻击
                    self._player_attack()
                elif self.menu_index == 1:  # 技能
                    self.show_skills = True
                    self.skill_index = 0
                elif self.menu_index == 2:  # 物品
                    self.show_items = True
                    self.item_index = 0
                elif self.menu_index == 3 and menu_count == 5:  # 伴侣
                    self.show_partner_skills = True
                    self.partner_skill_index = 0
                elif (self.menu_index == 3 and menu_count == 4) or (self.menu_index == 4):  # 撤退
                    if self.is_boss:
                        self.message = "Boss战无法撤退！"
                        self.msg_timer = 60
                    elif random.random() < 0.5:
                        self.state = CombatState.FLEE
                        self.message = "成功撤退！"
                        # 幽灵协议成就：连续逃跑计数
                        p = self.player
                        p.achievement_counters['flee_streak'] = p.achievement_counters.get('flee_streak', 0) + 1
                        if p.achievement_counters['flee_streak'] >= 3 and 'ghost_protocol' not in p.achievements:
                            p.achievements.add('ghost_protocol')
                            self.message += " 【成就解锁：幽灵协议！遇敌率-30%】"
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

    def _handle_partner_skill_menu(self, event):
        if not self.partner_skills:
            self.show_partner_skills = False
            return True
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.show_partner_skills = False
        elif event.key == pygame.K_UP:
            self.partner_skill_index = (self.partner_skill_index - 1) % len(self.partner_skills)
        elif event.key == pygame.K_DOWN:
            self.partner_skill_index = (self.partner_skill_index + 1) % len(self.partner_skills)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            name, power, cost = self.partner_skills[self.partner_skill_index]
            if self.player.stats.mp >= cost:
                self.player.stats.mp -= cost
                self._execute_partner_skill(name, power)
                self.show_partner_skills = False
            else:
                self.message = "EN不足！"
                self.msg_timer = 40
        return True

    def _execute_partner_skill(self, name, power):
        """执行伴侣技能"""
        pname = self.partner_def.name
        # 回复类技能
        if name in ("数据修复", "数据屏障", "量子重启", "终极改装", "烟雾弹"):
            if name == "数据修复":
                heal = 25
                self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal)
                self.message = f"{pname}：数据修复！HP+{heal}！"
                self._start_anim('heal')
            elif name == "数据屏障":
                self.player_effects.append(StatusEffect('def_up', 3, self.player.get_total_def()))
                self.message = f"{pname}：数据屏障！防御力提升3回合！"
                self._start_anim('buff')
            elif name == "量子重启":
                heal_hp = 40
                heal_mp = 15
                self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal_hp)
                self.player.stats.mp = min(self.player.stats.max_mp, self.player.stats.mp + heal_mp)
                self.partner_hp = min(self.partner_max_hp, self.partner_hp + 20)
                self.message = f"{pname}：量子重启！全体恢复HP+{heal_hp} EN+{heal_mp}！"
                self._start_anim('heal')
            elif name == "终极改装":
                self.player_effects.append(StatusEffect('atk_up', 3, 10))
                self.player_effects.append(StatusEffect('def_up', 3, 8))
                self.message = f"{pname}：终极改装！全属性提升3回合！"
                self._start_anim('buff')
            elif name == "烟雾弹":
                self.player_effects.append(StatusEffect('def_up', 2, 15))
                self.message = f"{pname}：烟雾弹！防御提升2回合！"
                self._start_anim('buff')
            return
        # 攻击类技能
        if name == "过载引擎":
            total = 0
            for _ in range(2):
                dmg = max(1, self.partner_atk + power - self.enemy_def // 2 + random.randint(-2, 2))
                total += dmg
            self.enemy_hp -= total
            self.message = f"{pname}：过载引擎！2连击共{total}伤害！"
        elif name == "连射":
            total = 0
            for _ in range(3):
                dmg = max(1, self.partner_atk + power - self.enemy_def // 2 + random.randint(-2, 2))
                total += dmg
            self.enemy_hp -= total
            self.message = f"{pname}：连射！3连击共{total}伤害！"
        elif name == "病毒注入":
            poison_val = max(5, self.partner_atk // 2)
            self.enemy_effects.append(StatusEffect('poison', 3, poison_val))
            self.message = f"{pname}：病毒注入！敌人中毒3回合！"
        elif name == "致命一击":
            dmg = max(1, self.partner_atk * 2 + power - self.enemy_def + random.randint(-2, 2))
            self.enemy_hp -= dmg
            self.message = f"{pname}：致命一击！造成{dmg}伤害！"
        else:
            # 通用攻击技能
            dmg = max(1, self.partner_atk + power - self.enemy_def // 2 + random.randint(-2, 2))
            self.enemy_hp -= dmg
            self.message = f"{pname}：{name}！造成{dmg}伤害！"
        self._start_anim('skill')

    def _execute_skill(self, name, power):
        """执行技能（包括基础技能和技能树技能）"""
        # 记录技能到连击历史
        skill_action_map = {
            '黑客攻击': 'hack_attack', 'EMP脉冲': 'emp_pulse', '系统修复': 'heal',
            '连击': 'combo_strike', '毁灭打击': 'devastate', '铁壁': 'iron_wall',
            '数据窃取': 'data_steal', '病毒注入': 'virus_inject', '系统接管': 'system_hack',
        }
        action_key = skill_action_map.get(name, name)
        self.action_history.append(action_key)
        combo = self._check_combo()
        if combo:
            return
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
        base = self.player.get_total_atk() + self._get_atk_buff(self.player_effects) + power
        dmg = max(1, base - self.enemy_def + random.randint(-2, 2))
        # 弱点判定
        if self.enemy_weakness and self.enemy_weakness == skill_type:
            dmg = int(dmg * 1.5)
            self.message = ""  # 会被覆盖
        # 风暴天气：hack/emp技能+20%
        if self.player.weather == 'storm' and skill_type in ('hack', 'emp'):
            dmg = int(dmg * 1.2)
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

    def _check_combo(self):
        """数据残响：检测连续3回合技能序列触发连锁攻击"""
        if len(self.action_history) < 3:
            return False
        last3 = self.action_history[-3:]
        # 漏洞链: 黑客攻击→EMP脉冲→任意攻击 (需要hack_t3)
        if (last3[0] == 'hack_attack' and last3[1] == 'emp_pulse'
                and last3[2] == 'attack'
                and 'hack_t3' in self.player.unlocked_skills):
            atk = self.player.get_total_atk() + self._get_atk_buff(self.player_effects)
            dmg = max(1, atk * 4 - self.enemy_def)
            self.enemy_hp -= dmg
            self.enemy_effects.append(StatusEffect('stun', 2, 0))
            self.message = f"【数据残响·漏洞链】！造成{dmg}伤害+眩晕2回合！"
            self.particles.emit(SCREEN_W // 2, 120, 30, (0, 255, 200), 3, 50, 4, 'magic')
            self.particles.emit(SCREEN_W // 2, 120, 20, (255, 50, 150), 2, 40, 3, 'magic')
            self.action_history.clear()
            self._start_anim('skill')
            return True
        # 铁壁反击: 铁壁→攻击→攻击 (需要def_t4)
        if (last3[0] == 'iron_wall' and last3[1] == 'attack' and last3[2] == 'attack'
                and 'def_t4' in self.player.unlocked_skills):
            atk = self.player.get_total_atk() + self._get_atk_buff(self.player_effects)
            dmg = max(1, atk * 3 - self.enemy_def)
            self.enemy_hp -= dmg
            self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + 50)
            self.message = f"【数据残响·铁壁反击】！造成{dmg}伤害+回复50HP！"
            self.particles.emit(SCREEN_W // 2, 120, 25, (0, 200, 255), 3, 50, 4, 'magic')
            self.particles.emit(SCREEN_W // 2, 120, 15, (255, 255, 100), 2, 40, 3, 'magic')
            self.action_history.clear()
            self._start_anim('skill')
            return True
        # 毁灭协议: 连击→毁灭打击→数据窃取 (需要atk_t4+hack_t2)
        if (last3[0] == 'combo_strike' and last3[1] == 'devastate' and last3[2] == 'data_steal'
                and 'atk_t4' in self.player.unlocked_skills
                and 'hack_t2' in self.player.unlocked_skills):
            atk = self.player.get_total_atk() + self._get_atk_buff(self.player_effects)
            dmg = max(1, atk * 6 - self.enemy_def)
            self.enemy_hp -= dmg
            self.player.stats.gold += 100
            self.message = f"【数据残响·毁灭协议】！造成{dmg}伤害+偷取100信用点！"
            self.particles.emit(SCREEN_W // 2, 120, 35, (255, 50, 50), 4, 60, 5, 'magic')
            self.particles.emit(SCREEN_W // 2, 120, 25, (180, 60, 255), 3, 50, 4, 'magic')
            self.action_history.clear()
            self._start_anim('skill')
            return True
        return False

    def _player_attack(self):
        self.action_history.append('attack')
        combo = self._check_combo()
        if combo:
            return
        atk = self.player.get_total_atk() + self._get_atk_buff(self.player_effects)
        atk += self._get_meal_atk_bonus()
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
        total = 0
        for e in effects:
            if e.name == 'def_up':
                total += e.value
        return total

    def _get_atk_buff(self, effects):
        """获取攻击增益"""
        total = 0
        for e in effects:
            if e.name == 'atk_up':
                total += e.value
        return total

    def _get_meal_atk_bonus(self):
        """获取料理ATK加成"""
        if not self.meal_def or self.meal_buff_turns <= 0:
            return 0
        if self.meal_def.buff_type in ('atk', 'atk_def'):
            return self.meal_def.buff_value
        if self.meal_def.buff_type == 'all':
            return self.meal_def.buff_value
        return 0

    def _get_meal_def_bonus(self):
        """获取料理DEF加成"""
        if not self.meal_def or self.meal_buff_turns <= 0:
            return 0
        if self.meal_def.buff_type == 'def':
            return self.meal_def.buff_value
        if self.meal_def.buff_type == 'atk_def':
            return 5
        if self.meal_def.buff_type == 'all':
            return self.meal_def.buff_value
        return 0

    def _apply_meal_turn_effects(self):
        """每回合应用料理效果"""
        if not self.meal_def or self.meal_buff_turns <= 0:
            return
        self.meal_buff_turns -= 1
        if self.meal_def.buff_type == 'hp_regen':
            heal = self.meal_def.buff_value
            self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal)
            self.message += f" 料理回复{heal}HP！"
        if self.meal_buff_turns <= 0:
            self.player.active_meal = None
            self.player.meal_buff_turns = 0

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

        # 敌人行动 - 30%概率攻击伴侣
        target_partner = (self.partner_def and self.partner_hp > 0
                          and random.random() < 0.3)
        if target_partner:
            # 攻击伴侣
            if self.enemy_skills and random.random() < 0.4:
                skill_name, skill_power = random.choice(self.enemy_skills)
                if skill_name == "防火墙":
                    heal = 20
                    self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
                    self.message = f"{self.enemy_name}启动防火墙！恢复{heal}HP！"
                else:
                    dmg = max(1, skill_power - self.partner_defense + random.randint(-2, 2))
                    self.partner_hp -= dmg
                    self.message = f"{self.enemy_name}对{self.partner_def.name}使用{skill_name}！造成{dmg}伤害！"
            else:
                dmg = max(1, self.enemy_atk - self.partner_defense + random.randint(-2, 2))
                self.partner_hp -= dmg
                self.message = f"{self.enemy_name}攻击{self.partner_def.name}！造成{dmg}伤害！"
            if self.partner_hp <= 0:
                self.partner_hp = 0
                self.message += f" {self.partner_def.name}倒下了！"
        elif self.enemy_skills and random.random() < 0.4:
            skill_name, skill_power = random.choice(self.enemy_skills)
            if skill_name == "防火墙":
                # AI核心Boss特殊技能：回复HP
                heal = 20
                self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
                self.message = f"{self.enemy_name}启动防火墙！恢复{heal}HP！"
            else:
                player_def = self.player.get_total_def() + self._get_def_buff(self.player_effects) + self._get_meal_def_bonus()
                dmg = max(1, skill_power - player_def + random.randint(-2, 2))
                # 反击判定
                counter_dmg = self._check_counter(dmg)
                self.player.stats.hp -= dmg
                self.damage_taken += dmg
                counter_text = f" 反击{counter_dmg}！" if counter_dmg > 0 else ""
                self.message = f"{self.enemy_name}使用{skill_name}！造成{dmg}点伤害！{counter_text}"
        else:
            player_def = self.player.get_total_def() + self._get_def_buff(self.player_effects) + self._get_meal_def_bonus()
            dmg = max(1, self.enemy_atk - player_def + random.randint(-2, 2))
            counter_dmg = self._check_counter(dmg)
            self.player.stats.hp -= dmg
            self.damage_taken += dmg
            counter_text = f" 反击{counter_dmg}！" if counter_dmg > 0 else ""
            self.message = f"{self.enemy_name}攻击！造成{dmg}点伤害！{counter_text}"

        # 暗网Boss特殊AI
        if self.enemy_key == 'firewall_guardian' and self.turn_count % 3 == 0:
            heal = 30
            self.enemy_hp = min(self.enemy_max_hp, self.enemy_hp + heal)
            self.message += f" 防火墙自修复+{heal}HP！"
        elif self.enemy_key == 'data_devourer':
            steal_en = 5
            self.player.stats.mp = max(0, self.player.stats.mp - steal_en)
            self.message += f" 吞噬了{steal_en}EN！"
        elif self.enemy_key == 'darknet_lord':
            if self.enemy_hp <= self.enemy_max_hp // 2 and not hasattr(self, '_darknet_lord_enraged'):
                self._darknet_lord_enraged = True
                self.enemy_atk *= 2
                self.message += " 暗网之主暴怒！ATK翻倍！"

        # 玩家回合开始效果
        p_msgs = self._apply_turn_start_effects(self.player_effects, True)
        self.player_effects = self._tick_effects(self.player_effects)

        if self.player.stats.hp <= 0:
            self.state = CombatState.DEFEAT
            self.message = "系统崩溃..."
        else:
            # 伴侣自动攻击
            if self.partner_def and self.partner_hp > 0 and self.enemy_hp > 0:
                p_dmg = max(1, self.partner_atk - self.enemy_def // 2 + random.randint(-2, 2))
                self.enemy_hp -= p_dmg
                self.message += f" {self.partner_def.name}攻击{p_dmg}！"
                if self.enemy_hp <= 0:
                    self._on_victory()
                    return
            # 宠物技能
            if self.pet_def and self.enemy_hp > 0:
                self.pet_timer += 1
                if self.pet_timer >= self.pet_def.combat_interval:
                    self.pet_timer = 0
                    # 使用进化技能或普通技能
                    if self.pet_evolved and self.pet_def.evolved_combat_skill:
                        skill_name, skill_val = self.pet_def.evolved_combat_skill
                    elif self.pet_def.combat_skill:
                        skill_name, skill_val = self.pet_def.combat_skill
                    else:
                        skill_name, skill_val = None, 0
                    if skill_name:
                        pet_name = self.pet_def.evolved_name if self.pet_evolved else self.pet_def.name
                        if '治疗' in skill_name or '治愈' in skill_name or '修复' in skill_name:
                            heal = skill_val
                            self.player.stats.hp = min(self.player.stats.max_hp,
                                                       self.player.stats.hp + heal)
                            self.message += f" {pet_name}:{skill_name}+{heal}HP！"
                        else:
                            pet_dmg = max(1, skill_val - self.enemy_def // 3)
                            self.enemy_hp -= pet_dmg
                            self.message += f" {pet_name}:{skill_name}{pet_dmg}！"
                            if self.enemy_hp <= 0:
                                self._on_victory()
                                return
            # 料理回合效果
            self._apply_meal_turn_effects()
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
        # 宠物加成
        pet_bonus = self.player.get_pet_bonuses()
        if pet_bonus.get('type') == 'gold_boost':
            gold = int(gold * (1 + pet_bonus['value'] / 100))
        if pet_bonus.get('type') == 'exp_boost':
            exp = int(exp * (1 + pet_bonus['value'] / 100))
        # 成就：极速通关 EXP+50%
        if 'speed_runner' in self.player.achievements:
            exp = int(exp * 1.5)
        self.player.stats.exp += exp
        self.player.stats.gold += gold
        # 伴侣HP同步回存 + 经验
        if self.partner_def:
            # 战斗结束后伴侣HP恢复到至少1
            self.player.partner_hp = max(1, self.partner_hp)
            # 伴侣获得经验
            partner_exp = exp // 2
            new_level = self.player.add_partner_exp(partner_exp)
            if new_level:
                self.message += f" {self.partner_def.name}升到Lv{new_level}！"
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
        # 宠物经验
        if self.player.active_pet:
            pet_exp = exp // 3
            new_level = self.player.add_pet_exp(self.player.active_pet, pet_exp)
            pet = PETS_DB.get(self.player.active_pet)
            if pet:
                pet_name = pet.evolved_name if self.player.is_pet_evolved(self.player.active_pet) else pet.name
                if new_level:
                    self.message += f" {pet_name}升到Lv{new_level}！"
                    if new_level == 5:
                        self.message += f" ★{pet_name}进化为{pet.evolved_name}！★"
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
            self.player.stats.exp_next = int(self.player.stats.exp_next * 1.35) + 5
            self.player.skill_points += 1
            self.message += f" 升级到Lv{self.player.stats.level}！获得1技能点！"
        # 成就检查
        self._check_victory_achievements()
        # 悬赏板：击杀类进度 + 存活类进度
        for ab in self.player.active_bounties:
            from entities import BOUNTY_POOL
            bdef = BOUNTY_POOL.get(ab['bounty_id'])
            if not bdef:
                continue
            if bdef.bounty_type == 'kill' and bdef.target == self.enemy_key:
                ab['progress'] = ab.get('progress', 0) + 1
            if bdef.bounty_type == 'survive':
                ab['progress'] = max(ab.get('progress', 0), self.turn_count)

    def _check_victory_achievements(self):
        """胜利后检查成就"""
        p = self.player
        # 零日漏洞：1回合击杀Boss
        if self.is_boss and self.turn_count <= 1 and 'zero_day' not in p.achievements:
            p.achievements.add('zero_day')
            self.message += " 【成就解锁：零日漏洞！ATK+8】"
        # 铁壁防线：单场受200+伤害存活
        if self.damage_taken >= 200 and 'iron_wall' not in p.achievements:
            p.achievements.add('iron_wall')
            p.stats.max_hp += 30
            p.stats.hp = min(p.stats.max_hp, p.stats.hp + 30)
            self.message += " 【成就解锁：铁壁防线！DEF+6 MAX_HP+30】"
        # 极速通关：Lv<=8击败量子霸主
        if self.enemy_key in ('quantum_lord', 'quantum_overlord') and p.stats.level <= 8 and 'speed_runner' not in p.achievements:
            p.achievements.add('speed_runner')
            self.message += " 【成就解锁：极速通关！EXP+50%】"
        # 数据囤积者：持有15+种物品
        if len(p.inventory) >= 15 and 'data_hoarder' not in p.achievements:
            p.achievements.add('data_hoarder')
            self.message += " 【成就解锁：数据囤积者！商店价格-20%】"
        # 逃跑连击重置
        p.achievement_counters['flee_streak'] = 0

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
        eff_labels = {'poison': '毒', 'stun': '晕', 'atk_up': '攻↑', 'def_up': '防↑', 'regen': '回'}
        eff_colors = {'poison': C_GREEN, 'stun': C_YELLOW, 'atk_up': C_RED, 'def_up': C_NEON_CYAN, 'regen': (100, 255, 100)}
        for eff in self.enemy_effects:
            label = eff_labels.get(eff.name, eff.name[:2])
            c = eff_colors.get(eff.name, C_WHITE)
            draw_text(surf, f"[{label}{eff.duration}]", (ex_eff, 228), self.assets.font_sm, c)
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
        eff_labels = {'poison': '毒', 'stun': '晕', 'atk_up': '攻↑', 'def_up': '防↑', 'regen': '回'}
        eff_colors = {'poison': C_GREEN, 'stun': C_YELLOW, 'atk_up': C_RED, 'def_up': C_NEON_CYAN, 'regen': (100, 255, 100)}
        for eff in self.player_effects:
            label = eff_labels.get(eff.name, eff.name[:2])
            c = eff_colors.get(eff.name, C_WHITE)
            draw_text(surf, f"[{label}{eff.duration}]", (pe_x, panel_y + 86), self.assets.font_sm, c)
            pe_x += 50

        # 伴侣信息
        if self.partner_def:
            partner_x = 200
            draw_text(surf, f"♥{self.partner_def.name} Lv{self.player.partner_level}",
                      (partner_x, panel_y + 10), self.assets.font_sm, C_NEON_PINK)
            if self.partner_hp > 0:
                draw_bar(surf, partner_x, panel_y + 26, 80, 8,
                         self.partner_hp / self.partner_max_hp, (255, 120, 160))
                draw_text(surf, f"{self.partner_hp}/{self.partner_max_hp}",
                          (partner_x, panel_y + 36), self.assets.font_sm, (200, 150, 170))
            else:
                draw_text(surf, "倒下", (partner_x, panel_y + 26), self.assets.font_sm, (100, 60, 60))

        # 宠物信息
        if self.pet_def:
            pet_x = 200
            pet_y_off = 55 if self.partner_def else 10
            pet_name = self.pet_def.evolved_name if self.pet_evolved else self.pet_def.name
            draw_text(surf, f"★{pet_name}", (pet_x, panel_y + pet_y_off), self.assets.font_sm, C_NEON_CYAN)
            if self.pet_def.combat_skill:
                cd_left = self.pet_def.combat_interval - self.pet_timer
                draw_text(surf, f"技能CD:{cd_left}", (pet_x, panel_y + pet_y_off + 14),
                          self.assets.font_sm, (100, 180, 160))

        # 消息
        draw_text(surf, self.message, (px, panel_y + 105), self.assets.font_md, C_WHITE)

        # 菜单
        if self.state == CombatState.PLAYER_CHOOSE:
            menu_x = SCREEN_W - 200
            if self.show_items:
                self._draw_item_menu(surf, menu_x, panel_y + 10)
            elif self.show_skills:
                self._draw_skill_menu(surf, menu_x, panel_y + 10)
            elif self.show_partner_skills:
                self._draw_partner_skill_menu(surf, menu_x, panel_y + 10)
            else:
                options = ["[A] 攻击", "[S] 技能", "[I] 物品"]
                if self.partner_def and self.partner_hp > 0:
                    options.append("[P] 伴侣")
                options.append("[R] 撤退")
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

    def _draw_partner_skill_menu(self, surf, x, y):
        pname = self.partner_def.name if self.partner_def else "伴侣"
        draw_text(surf, f"【{pname}技能】(X返回)", (x, y), self.assets.font_sm, C_NEON_PINK)
        if not self.partner_skills:
            draw_text(surf, "没有可用技能", (x, y + 22), self.assets.font_sm)
            return
        for i, (name, power, cost) in enumerate(self.partner_skills):
            color = C_YELLOW if i == self.partner_skill_index else C_WHITE
            if self.player.stats.mp < cost:
                color = (100, 100, 100)
            prefix = ">> " if i == self.partner_skill_index else "   "
            draw_text(surf, f"{prefix}{name} (EN:{cost})", (x, y + 22 + i * 22), self.assets.font_sm, color)
