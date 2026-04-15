"""游戏实体：玩家、NPC + 数据层再导出"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from constants import TILE
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_TUNNEL, AREA_BLACK_MARKET, AREA_HOME)

# 从 data.py 导入所有数据定义，并在此模块再导出以保持向后兼容
from data import (  # noqa: F401 — re-export
    FishDef, FISH_DB,
    BountyDef, BOUNTY_POOL,
    CraftRecipe, AFFIXES, CRAFT_RECIPES,
    HACK_WORDS,
    CodexEntry, QuestChainStep, QuestChain, QUEST_CHAINS,
    ARENA_WAVES,
    DailyModifier, DAILY_MODIFIERS,
    PetBattleMove, PET_BATTLE_MOVES, PetBattleNPC, PET_BATTLE_NPCS,
    FurnitureDef, FURNITURE_DB,
    StatusEffect,
    SkillNode, SKILL_TREE,
    Item, ITEMS_DB,
    FUSION_RECIPES,
    Achievement, ACHIEVEMENTS,
    MealDef, MEALS_DB,
    RomanceChar, ROMANCE_CHARS,
    CropDef, PlotState, CROPS_DB,
    PetDef, PETS_DB,
    EnemyDef, ENEMY_DEFS, ENCOUNTER_TABLE,
    GraffitiDef, GRAFFITI_DB, GRAFFITI_SETS, GRAFFITI_POS,
)


# ============================================================
# 玩家
# ============================================================
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
        self.tx = x
        self.ty = y
        self.speed = 2.5
        self.run_speed = 4.5
        self.direction = 'down'
        self.anim_frame = 0
        self.anim_timer = 0
        self.moving = False
        self.stats = PlayerStats()
        self.inventory: List[Tuple[str, int]] = [('hp_potion', 3), ('mp_potion', 2)]
        self.equipped: Dict[str, Optional[str]] = {'weapon': None, 'armor': None, 'accessory': None}
        self.area = AREA_VILLAGE
        # 主线任务
        self.quest_stage: int = 0          # 0-5
        self.quest_flags: Dict[str, bool] = {}
        self.boss_defeated: Dict[str, bool] = {}
        # 支线任务
        self.side_quests: Dict[str, int] = {}   # 0=未接 1=进行中 2=完成
        self.quest_counters: Dict[str, int] = {}
        # 技能树
        self.skill_points: int = 0
        self.unlocked_skills: Set[str] = set()
        # 恋爱系统
        self.affection: Dict[str, int] = {}          # {char_id: 好感度}
        self.romance_events_seen: Dict[str, Set[int]] = {}  # {char_id: {已触发的阈值}}
        self.partner: Optional[str] = None            # 最终选择的伴侣char_id
        self.partner_hp: int = 0                      # 伴侣当前HP
        # 家园系统
        self.farm_plots: List = []                    # [PlotState, ...]  6块地
        self.farm_step_counter: int = 0               # 步数计数器
        self.farm_level: int = 0                      # 农场等级 0-3
        # 烹饪系统
        self.active_meal: Optional[str] = None        # 当前料理buff
        self.meal_buff_turns: int = 0                 # 料理buff剩余回合
        # 宠物探险
        self.expedition: Optional[Dict] = None        # {'pet_id': str, 'steps_left': int, 'reward_tier': int}
        # 宠物系统
        self.pets_owned: List[str] = []               # 拥有的宠物ID列表
        self.active_pet: Optional[str] = None         # 当前出战宠物
        self.pet_exp: Dict[str, int] = {}             # 宠物经验
        self.pet_levels: Dict[str, int] = {}          # 宠物等级
        self.pet_happiness: Dict[str, int] = {}       # 宠物幸福度 0-100
        self.pet_play_cooldown: Dict[str, int] = {}   # 玩耍冷却（步数）
        # 伴侣成长
        self.partner_exp: int = 0
        self.partner_level: int = 1
        # 成就系统
        self.achievements: Set[str] = set()
        self.achievement_counters: Dict[str, int] = {}  # flee_streak, damage_taken, etc.
        self.visited_areas: Set[str] = set()
        # 暗网连战
        self.darknet_cleared: bool = False
        # 钓鱼系统
        self.fish_caught: Dict[str, int] = {}
        # 天气/时间系统
        self.world_time: int = 0
        self.weather: str = 'clear'
        self.weather_timer: int = 10800
        # 悬赏板系统
        self.active_bounties: List[Dict] = []       # [{bounty_id, progress}] 最多3个
        self.completed_bounties: Set[str] = set()
        self.bounty_board: List[str] = []            # 当前板上3个id
        self.bounty_refresh_flag: bool = True
        # v0.13 新系统
        # 装备合成 — 已合成装备的词缀记录 {item_key: {'prefix': str, 'suffix': str, 'bonus_atk': int, 'bonus_def': int}}
        self.crafted_affixes: Dict[str, Dict] = {}
        # 图鉴
        self.codex_monsters: Set[str] = set()
        self.codex_fish: Set[str] = set()
        self.codex_recipes: Set[str] = set()
        # NPC任务链
        self.quest_chains: Dict[str, Dict] = {}  # {chain_id: {'step': int, 'progress': int, 'done': bool}}
        # 竞技场
        self.arena_best_wave: int = 0
        # 每日挑战
        self.daily_completed_date: str = ''  # 'YYYY-MM-DD'
        self.daily_best_streak: int = 0
        self.daily_streak: int = 0
        # 宠物对战
        self.pet_battle_wins: int = 0
        self.pet_battle_defeated: Set[str] = set()  # NPC names defeated
        # 据点/家园
        self.furniture: Set[str] = set()  # owned furniture IDs
        # New Game+
        self.ng_plus: int = 0  # 0=normal, 1=NG+, 2=NG++...
        # 随机事件扩展
        self.black_market_timer: int = 0  # >0 时黑市商人出现
        # 赛博涂鸦收集
        self.graffiti_found: Set[str] = set()
        self.graffiti_sets_claimed: Set[str] = set()  # 已领取奖励的套装

    def get_total_atk(self):
        bonus = sum(ITEMS_DB[v].atk_bonus for v in self.equipped.values() if v)
        # 合成词缀加成
        for v in self.equipped.values():
            if v and v in self.crafted_affixes:
                bonus += self.crafted_affixes[v].get('bonus_atk', 0)
        if 'atk_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['atk_t1'].effect['value']
        # 宠物被动
        if self.active_pet:
            pet = PETS_DB.get(self.active_pet)
            if pet:
                passive = pet.evolved_passive if self.is_pet_evolved(self.active_pet) else pet.passive
                if passive.get('type') == 'atk_boost':
                    val = passive['value']
                    happiness = self.pet_happiness.get(self.active_pet, 50)
                    if happiness < 20:
                        val = 0
                    elif happiness > 80:
                        val = int(val * 1.5)
                    bonus += val
        # 家具加成
        for fid in self.furniture:
            fd = FURNITURE_DB.get(fid)
            if fd and fd.passive_type == 'atk':
                bonus += fd.passive_value
        # NG+加成
        bonus += self.ng_plus * 2
        return self.stats.atk + bonus

    def get_total_def(self):
        bonus = sum(ITEMS_DB[v].def_bonus for v in self.equipped.values() if v)
        for v in self.equipped.values():
            if v and v in self.crafted_affixes:
                bonus += self.crafted_affixes[v].get('bonus_def', 0)
        if 'def_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['def_t1'].effect['value']
        # 宠物被动
        if self.active_pet:
            pet = PETS_DB.get(self.active_pet)
            if pet:
                passive = pet.evolved_passive if self.is_pet_evolved(self.active_pet) else pet.passive
                if passive.get('type') == 'def_boost':
                    val = passive['value']
                    happiness = self.pet_happiness.get(self.active_pet, 50)
                    if happiness < 20:
                        val = 0
                    elif happiness > 80:
                        val = int(val * 1.5)
                    bonus += val
        # 家具加成
        for fid in self.furniture:
            fd = FURNITURE_DB.get(fid)
            if fd and fd.passive_type == 'def':
                bonus += fd.passive_value
        # NG+加成
        bonus += self.ng_plus * 2
        return self.stats.defense + bonus

    def has_item(self, key):
        return any(k == key for k, c in self.inventory)

    def item_count(self, key):
        for k, c in self.inventory:
            if k == key:
                return c
        return 0

    def add_item(self, key, count=1):
        for i, (k, c) in enumerate(self.inventory):
            if k == key:
                self.inventory[i] = (k, c + count)
                return
        self.inventory.append((key, count))

    def remove_item(self, key, count=1):
        for i, (k, c) in enumerate(self.inventory):
            if k == key:
                if c <= count:
                    self.inventory.pop(i)
                else:
                    self.inventory[i] = (k, c - count)
                return

    def equip(self, item_key):
        item = ITEMS_DB.get(item_key)
        if not item:
            return
        slot = item.equip_slot
        if not slot:
            return
        old = self.equipped.get(slot)
        self.equipped[slot] = item_key
        return old

    def use_item(self, item_key):
        item = ITEMS_DB.get(item_key)
        if not item or not item.use_effect:
            return False
        eff = item.use_effect
        st = self.stats
        if eff.get('hp'):
            st.hp = min(st.max_hp, st.hp + eff['hp'])
        if eff.get('mp'):
            st.mp = min(st.max_mp, st.mp + eff['mp'])
        if eff.get('full_restore'):
            st.hp = st.max_hp
            st.mp = st.max_mp
        self.remove_item(item_key)
        return True

    def level_up(self):
        st = self.stats
        while st.exp >= st.exp_next:
            st.exp -= st.exp_next
            st.level += 1
            st.max_hp += 8
            st.hp = st.max_hp
            st.max_mp += 4
            st.mp = st.max_mp
            st.atk += 2
            st.defense += 1
            st.exp_next = int(st.exp_next * 1.35) + 5
            self.skill_points += 1

    def load_from_dict(self, d):
        st = self.stats
        st.level = d.get('level', 1)
        st.hp = d.get('hp', 100)
        st.max_hp = d.get('max_hp', 100)
        st.mp = d.get('mp', 40)
        st.max_mp = d.get('max_mp', 40)
        st.atk = d.get('atk', 12)
        st.defense = d.get('defense', 5)
        st.exp = d.get('exp', 0)
        st.exp_next = d.get('exp_next', 30)
        st.gold = d.get('gold', 50)
        self.inventory = [(k, c) for k, c in d.get('inventory', [('hp_potion', 3), ('mp_potion', 2)])]
        self.equipped = d.get('equipped', {'weapon': None, 'armor': None, 'accessory': None})
        self.area = d.get('area', AREA_VILLAGE)
        self.tx = d.get('tx', 5)
        self.ty = d.get('ty', 5)
        self.x = float(self.tx * TILE)
        self.y = float(self.ty * TILE)
        self.quest_stage = d.get('quest_stage', 0)
        self.quest_flags = d.get('quest_flags', {})
        self.boss_defeated = d.get('boss_defeated', {})
        self.side_quests = d.get('side_quests', {})
        self.quest_counters = d.get('quest_counters', {})
        self.skill_points = d.get('skill_points', 0)
        self.unlocked_skills = set(d.get('unlocked_skills', []))
        self.affection = d.get('affection', {})
        self.romance_events_seen = {k: set(v) for k, v in d.get('romance_events_seen', {}).items()}
        self.partner = d.get('partner', None)
        self.partner_hp = d.get('partner_hp', 0)
        self.partner_exp = d.get('partner_exp', 0)
        self.partner_level = d.get('partner_level', 1)
        self.achievements = set(d.get('achievements', []))
        self.achievement_counters = d.get('achievement_counters', {})
        self.visited_areas = set(d.get('visited_areas', []))
        self.darknet_cleared = d.get('darknet_cleared', False)
        # 家园
        self.farm_level = d.get('farm_level', 0)
        self.farm_step_counter = d.get('farm_step_counter', 0)
        farm_data = d.get('farm_plots', [])
        if farm_data:
            self.farm_plots = [PlotState(p.get('crop_id'), p.get('growth', 0), p.get('ready', False),
                                          p.get('fertilized', False)) for p in farm_data]
        else:
            target_plots = 6 + self.farm_level * 2
            for _ in range(target_plots):
                self.farm_plots.append(PlotState())
        # 烹饪
        self.active_meal = d.get('active_meal', None)
        self.meal_buff_turns = d.get('meal_buff_turns', 0)
        # 宠物
        self.pets_owned = d.get('pets_owned', [])
        self.active_pet = d.get('active_pet', None)
        self.pet_exp = d.get('pet_exp', {})
        self.pet_levels = d.get('pet_levels', {})
        self.pet_happiness = d.get('pet_happiness', {})
        self.pet_play_cooldown = d.get('pet_play_cooldown', {})
        self.expedition = d.get('expedition', None)
        # 钓鱼
        self.fish_caught = d.get('fish_caught', {})
        # 天气/时间
        self.world_time = d.get('world_time', 0)
        self.weather = d.get('weather', 'clear')
        self.weather_timer = d.get('weather_timer', 10800)
        # 悬赏
        self.active_bounties = d.get('active_bounties', [])
        self.completed_bounties = set(d.get('completed_bounties', []))
        self.bounty_board = d.get('bounty_board', [])
        # v0.13
        self.crafted_affixes = d.get('crafted_affixes', {})
        self.codex_monsters = set(d.get('codex_monsters', []))
        self.codex_fish = set(d.get('codex_fish', []))
        self.codex_recipes = set(d.get('codex_recipes', []))
        self.quest_chains = d.get('quest_chains', {})
        self.arena_best_wave = d.get('arena_best_wave', 0)
        self.daily_completed_date = d.get('daily_completed_date', '')
        self.daily_best_streak = d.get('daily_best_streak', 0)
        self.daily_streak = d.get('daily_streak', 0)
        self.pet_battle_wins = d.get('pet_battle_wins', 0)
        self.pet_battle_defeated = set(d.get('pet_battle_defeated', []))
        self.furniture = set(d.get('furniture', []))
        self.ng_plus = d.get('ng_plus', 0)
        self.graffiti_found = set(d.get('graffiti_found', []))
        self.graffiti_sets_claimed = set(d.get('graffiti_sets_claimed', []))

    # 别名兼容
    load_save_dict = load_from_dict

    def to_save_dict(self):
        st = self.stats
        return {
            'level': st.level, 'hp': st.hp, 'max_hp': st.max_hp,
            'mp': st.mp, 'max_mp': st.max_mp, 'atk': st.atk, 'defense': st.defense,
            'exp': st.exp, 'exp_next': st.exp_next, 'gold': st.gold,
            'inventory': list(self.inventory),
            'equipped': self.equipped,
            'area': self.area, 'tx': self.tx, 'ty': self.ty,
            'quest_stage': self.quest_stage, 'quest_flags': self.quest_flags,
            'boss_defeated': self.boss_defeated,
            'side_quests': self.side_quests, 'quest_counters': self.quest_counters,
            'skill_points': self.skill_points,
            'unlocked_skills': list(self.unlocked_skills),
            'affection': self.affection,
            'romance_events_seen': {k: list(v) for k, v in self.romance_events_seen.items()},
            'partner': self.partner, 'partner_hp': self.partner_hp,
            'partner_exp': self.partner_exp, 'partner_level': self.partner_level,
            'achievements': list(self.achievements),
            'achievement_counters': self.achievement_counters,
            'visited_areas': list(self.visited_areas),
            'darknet_cleared': self.darknet_cleared,
            'farm_level': self.farm_level, 'farm_step_counter': self.farm_step_counter,
            'farm_plots': [{'crop_id': p.crop_id, 'growth': p.growth,
                            'ready': p.ready, 'fertilized': p.fertilized}
                           for p in self.farm_plots],
            'active_meal': self.active_meal, 'meal_buff_turns': self.meal_buff_turns,
            'pets_owned': self.pets_owned, 'active_pet': self.active_pet,
            'pet_exp': self.pet_exp, 'pet_levels': self.pet_levels,
            'pet_happiness': self.pet_happiness, 'pet_play_cooldown': self.pet_play_cooldown,
            'expedition': self.expedition,
            'fish_caught': self.fish_caught,
            'world_time': self.world_time, 'weather': self.weather,
            'weather_timer': self.weather_timer,
            'active_bounties': self.active_bounties,
            'completed_bounties': list(self.completed_bounties),
            'bounty_board': self.bounty_board,
            'crafted_affixes': self.crafted_affixes,
            'codex_monsters': list(self.codex_monsters),
            'codex_fish': list(self.codex_fish),
            'codex_recipes': list(self.codex_recipes),
            'quest_chains': self.quest_chains,
            'arena_best_wave': self.arena_best_wave,
            'daily_completed_date': self.daily_completed_date,
            'daily_best_streak': self.daily_best_streak,
            'daily_streak': self.daily_streak,
            'pet_battle_wins': self.pet_battle_wins,
            'pet_battle_defeated': list(self.pet_battle_defeated),
            'furniture': list(self.furniture),
            'ng_plus': self.ng_plus,
            'graffiti_found': list(self.graffiti_found),
            'graffiti_sets_claimed': list(self.graffiti_sets_claimed),
        }

    def unlock_skill(self, skill_id):
        node = SKILL_TREE.get(skill_id)
        if not node:
            return False
        if skill_id in self.unlocked_skills:
            return False
        if self.skill_points < node.cost:
            return False
        # 检查前置
        for req in node.requires:
            if req not in self.unlocked_skills:
                return False
        self.skill_points -= node.cost
        self.unlocked_skills.add(skill_id)
        # 应用效果
        eff = node.effect
        if eff.get('type') == 'stat':
            stat_name = eff['stat']
            value = eff['value']
            if stat_name == 'atk':
                pass  # 通过 get_total_atk 动态计算
            elif stat_name == 'defense':
                pass
            elif stat_name == 'max_hp':
                self.stats.max_hp += value
                self.stats.hp += value
            elif stat_name == 'max_mp':
                self.stats.max_mp += value
                self.stats.mp += value
        return True

    def get_available_skills(self):
        """返回战斗中可用的技能列表 [(name, power, mp_cost)]"""
        skills = [("黑客入侵", 15, 8)]  # 基础技能
        if 'hack_t1' in self.unlocked_skills:
            mp_reduce = SKILL_TREE['hack_t1'].effect['mp_reduce']
            skills[0] = ("黑客入侵", 15, max(1, 8 - mp_reduce))
        for sid in self.unlocked_skills:
            node = SKILL_TREE.get(sid)
            if node and node.effect.get('type') == 'skill':
                skills.append((node.effect['name'], node.effect['power'], node.effect['mp_cost']))
        return skills

    # 恋爱系统
    def get_affection(self, char_id: str) -> int:
        return self.affection.get(char_id, 0)

    def add_affection(self, char_id: str, amount: int) -> int:
        current = self.affection.get(char_id, 0)
        new_val = max(0, min(100, current + amount))
        self.affection[char_id] = new_val
        return new_val

    def check_romance_event(self, char_id: str):
        rc = ROMANCE_CHARS.get(char_id)
        if not rc:
            return None
        aff = self.get_affection(char_id)
        seen = self.romance_events_seen.get(char_id, set())
        for threshold, desc, reward_type in rc.events:
            if aff >= threshold and threshold not in seen:
                return (threshold, desc, reward_type)
        return None

    def mark_romance_event(self, char_id: str, threshold: int):
        if char_id not in self.romance_events_seen:
            self.romance_events_seen[char_id] = set()
        self.romance_events_seen[char_id].add(threshold)

    def get_partner_def(self):
        if not self.partner:
            return None
        return ROMANCE_CHARS.get(self.partner)

    def init_farm(self):
        target_plots = 6 + self.farm_level * 2
        if len(self.farm_plots) < target_plots:
            while len(self.farm_plots) < target_plots:
                self.farm_plots.append(PlotState())

    def update_farm(self, steps=1):
        """每步更新农场"""
        for plot in self.farm_plots:
            if plot.crop_id and not plot.ready:
                crop = CROPS_DB.get(plot.crop_id)
                if crop:
                    growth_rate = 1
                    # 农场等级加速
                    growth_rate += self.farm_level * 0.2
                    # 施肥加速
                    if plot.fertilized:
                        growth_rate *= 2
                    # 雨天加速
                    if self.weather == 'rain':
                        growth_rate *= 1.5
                    plot.growth += growth_rate * steps
                    if plot.growth >= crop.grow_time:
                        plot.ready = True

    # 宠物系统
    def get_pet_level(self, pet_id: str) -> int:
        exp = self.pet_exp.get(pet_id, 0)
        level = 1
        while exp >= level * 50:
            exp -= level * 50
            level += 1
        return level

    def add_pet_exp(self, pet_id: str, amount: int):
        self.pet_exp[pet_id] = self.pet_exp.get(pet_id, 0) + amount

    def is_pet_evolved(self, pet_id: str) -> bool:
        return self.get_pet_level(pet_id) >= 5

    def get_active_pet_passive(self):
        if not self.active_pet:
            return None
        pet = PETS_DB.get(self.active_pet)
        if not pet:
            return None
        evolved = self.is_pet_evolved(self.active_pet)
        passive = pet.evolved_passive if evolved else pet.passive
        happiness = self.pet_happiness.get(self.active_pet, 50)
        if happiness < 20:
            return None
        return passive

    def get_partner_combat_stats(self):
        rc = self.get_partner_def()
        if not rc:
            return None
        lvl = self.partner_level - 1  # 额外等级加成
        hp = rc.combat_hp + lvl * 5
        atk = rc.combat_atk + lvl * 2
        defense = rc.combat_def + lvl * 1
        return (hp, atk, defense)

    def get_partner_skills(self) -> List[Tuple[str, int, int]]:
        """返回伴侣当前可用技能列表 [(name, power, mp_cost)]"""
        rc = self.get_partner_def()
        if not rc:
            return []
        skills = list(rc.combat_skills)
        for req_level, name, power, cost in rc.growth_skills:
            if self.partner_level >= req_level:
                skills.append((name, power, cost))
        return skills

    def gift_to_partner_char(self, char_id: str, item_key: str) -> Tuple[int, str]:
        """送礼给角色，返回 (好感度变化, 反应类型 'liked'/'disliked'/'normal')"""
        rc = ROMANCE_CHARS.get(char_id)
        if not rc:
            return (0, 'normal')
        if item_key in rc.liked_gifts:
            delta = 10
            reaction = 'liked'
        elif item_key in rc.disliked_gifts:
            delta = -5
            reaction = 'disliked'
        else:
            delta = 3
            reaction = 'normal'
        self.add_affection(char_id, delta)
        self.remove_item(item_key)
        return (delta, reaction)


# ============================================================
# NPC
# ============================================================
@dataclass
class NPC:
    x: int
    y: int
    sprite_key: str
    name: str
    dialogues: List[str]
    area: str
    shop_items: List[Tuple[str, int]] = field(default_factory=list)
    quest_dialogues: Dict[int, List[str]] = field(default_factory=dict)

    def get_dialogues(self, quest_stage: int = 0) -> List[str]:
        """根据主线阶段返回对话"""
        if self.quest_dialogues:
            # 找到 <= quest_stage 的最大key
            best = -1
            for k in self.quest_dialogues:
                if k <= quest_stage and k > best:
                    best = k
            if best >= 0:
                return self.quest_dialogues[best]
        return self.dialogues
