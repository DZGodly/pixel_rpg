"""游戏实体：物品、玩家、NPC、敌人 - 赛博朋克主题"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from constants import TILE
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_TUNNEL, AREA_BLACK_MARKET)


# ============================================================
# 状态效果
# ============================================================
@dataclass
class StatusEffect:
    name: str          # 'poison', 'stun', 'atk_up', 'def_up', 'regen'
    duration: int      # 剩余回合数
    value: int         # 效果值


# ============================================================
# 技能树
# ============================================================
@dataclass
class SkillNode:
    skill_id: str
    name: str
    desc: str
    branch: str        # 'attack' / 'defense' / 'hack'
    tier: int          # 1-4
    cost: int          # 技能点消耗
    prereq: Optional[str]  # 前置技能ID，None为起始
    effect: Dict       # {'type': 'passive'/'combat_skill', ...}

SKILL_TREE: Dict[str, SkillNode] = {
    # 攻击分支
    'atk_t1': SkillNode('atk_t1', '强化攻击', '被动：ATK+5', 'attack', 1, 1, None,
                         {'type': 'passive', 'stat': 'atk', 'value': 5}),
    'atk_t2': SkillNode('atk_t2', '连击', '战斗技能：攻击2次，每次70%伤害', 'attack', 2, 1, 'atk_t1',
                         {'type': 'combat_skill', 'power_pct': 70, 'hits': 2, 'mp_cost': 8}),
    'atk_t3': SkillNode('atk_t3', '暴击', '被动：15%概率暴击(2倍伤害)', 'attack', 3, 2, 'atk_t2',
                         {'type': 'passive', 'crit_chance': 0.15, 'crit_mult': 2.0}),
    'atk_t4': SkillNode('atk_t4', '毁灭打击', '战斗技能：造成ATK*2.5的伤害', 'attack', 4, 2, 'atk_t3',
                         {'type': 'combat_skill', 'power_pct': 250, 'hits': 1, 'mp_cost': 18}),
    # 防御分支
    'def_t1': SkillNode('def_t1', '强化护甲', '被动：DEF+5', 'defense', 1, 1, None,
                         {'type': 'passive', 'stat': 'def', 'value': 5}),
    'def_t2': SkillNode('def_t2', '反击', '被动：受击时30%概率反弹伤害', 'defense', 2, 1, 'def_t1',
                         {'type': 'passive', 'counter_chance': 0.30}),
    'def_t3': SkillNode('def_t3', '生命汲取', '被动：攻击时回复10%伤害为HP', 'defense', 3, 2, 'def_t2',
                         {'type': 'passive', 'lifesteal': 0.10}),
    'def_t4': SkillNode('def_t4', '铁壁', '战斗技能：3回合DEF翻倍', 'defense', 4, 2, 'def_t3',
                         {'type': 'combat_skill', 'buff': 'def_up', 'duration': 3, 'mp_cost': 14}),
    # 黑客分支
    'hack_t1': SkillNode('hack_t1', '高效破解', '被动：技能EN消耗-30%', 'hack', 1, 1, None,
                          {'type': 'passive', 'mp_reduce': 0.30}),
    'hack_t2': SkillNode('hack_t2', '数据窃取', '战斗技能：造成伤害并偷取金币', 'hack', 2, 1, 'hack_t1',
                          {'type': 'combat_skill', 'power_pct': 80, 'steal_gold': True, 'mp_cost': 6}),
    'hack_t3': SkillNode('hack_t3', '病毒注入', '战斗技能：中毒3回合(每回合ATK*0.4)', 'hack', 3, 2, 'hack_t2',
                          {'type': 'combat_skill', 'poison_turns': 3, 'poison_pct': 0.4, 'mp_cost': 10}),
    'hack_t4': SkillNode('hack_t4', '系统接管', '战斗技能：眩晕敌人1回合', 'hack', 4, 2, 'hack_t3',
                          {'type': 'combat_skill', 'stun_turns': 1, 'mp_cost': 16}),
}


# ============================================================
# 物品
# ============================================================
@dataclass
class Item:
    name: str
    icon_key: str
    description: str
    item_type: str  # 'consumable', 'weapon', 'armor', 'accessory', 'material'
    hp_restore: int = 0
    mp_restore: int = 0
    atk_bonus: int = 0
    def_bonus: int = 0

ITEMS_DB = {
    'hp_potion': Item("纳米修复剂", "hp_potion", "注入纳米机器人，恢复50点HP", "consumable", hp_restore=50),
    'mp_potion': Item("能量核心", "mp_potion", "充能电池，恢复30点EN", "consumable", mp_restore=30),
    'iron_sword': Item("等离子刀", "iron_sword", "高频等离子刃，攻击力+8", "weapon", atk_bonus=8),
    'magic_ring': Item("神经接口", "magic_ring", "脑机接口芯片，攻击力+5", "accessory", atk_bonus=5),
    'shield': Item("能量护盾", "shield", "六角力场发生器，防御力+5", "armor", def_bonus=5),
    'elixir': Item("系统重启", "elixir", "完全重置，恢复全部HP和EN", "consumable", hp_restore=9999, mp_restore=9999),
    'lucky_coin': Item("加密货币", "lucky_coin", "饰品 攻击力+3，持有时战斗信用点翻倍", "accessory", atk_bonus=3),
    'emp_grenade': Item("EMP手雷", "emp_grenade", "电磁脉冲，攻击力+10", "weapon", atk_bonus=10),
    'quantum_chip': Item("量子芯片", "quantum_chip", "量子计算核心，攻击力+7 防御力+3", "accessory", atk_bonus=7, def_bonus=3),
    # 新增物品
    'precision_gear': Item("精密齿轮", "precision_gear", "工厂守卫掉落的精密零件", "material"),
    'data_sample': Item("数据样本", "data_sample", "网络空间采集的数据碎片", "material"),
    'encrypted_data': Item("加密数据", "encrypted_data", "各区域敌人掉落的加密信息", "material"),
    'worker_id': Item("工人证件", "worker_id", "失踪工人的身份证件", "material"),
    'plasma_rifle': Item("等离子步枪", "plasma_rifle", "高能等离子武器，攻击力+15", "weapon", atk_bonus=15),
    'nano_armor': Item("纳米装甲", "nano_armor", "自修复纳米材料，防御力+10", "armor", def_bonus=10),
    'hacker_gloves': Item("黑客手套", "hacker_gloves", "神经增幅手套，攻击力+5 防御力+5", "accessory", atk_bonus=5, def_bonus=5),
    'antivirus': Item("解毒程序", "antivirus", "清除所有负面状态效果", "consumable"),
}


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

    def get_total_atk(self):
        bonus = sum(ITEMS_DB[v].atk_bonus for v in self.equipped.values() if v)
        # 技能树被动加成
        if 'atk_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['atk_t1'].effect['value']
        return self.stats.atk + bonus

    def get_total_def(self):
        bonus = sum(ITEMS_DB[v].def_bonus for v in self.equipped.values() if v)
        if 'def_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['def_t1'].effect['value']
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
                return

    def has_item(self, item_key, count=1):
        for k, c in self.inventory:
            if k == item_key and c >= count:
                return True
        return False

    def item_count(self, item_key):
        for k, c in self.inventory:
            if k == item_key:
                return c
        return 0

    def use_item(self, item_key):
        item = ITEMS_DB.get(item_key)
        if not item:
            return
        if item.item_type == 'consumable':
            if item_key == 'antivirus':
                self.remove_item(item_key)
                return
            if item.hp_restore:
                self.stats.hp = min(self.stats.max_hp, self.stats.hp + item.hp_restore)
            if item.mp_restore:
                self.stats.mp = min(self.stats.max_mp, self.stats.mp + item.mp_restore)
            self.remove_item(item_key)
        elif item.item_type in ('weapon', 'armor', 'accessory'):
            slot = item.item_type
            old = self.equipped[slot]
            self.equipped[slot] = item_key
            self.remove_item(item_key)
            if old:
                self.add_item(old)

    def to_save_dict(self):
        return {
            'tx': self.tx, 'ty': self.ty,
            'direction': self.direction,
            'area': self.area,
            'stats': {
                'level': self.stats.level, 'hp': self.stats.hp, 'max_hp': self.stats.max_hp,
                'mp': self.stats.mp, 'max_mp': self.stats.max_mp,
                'atk': self.stats.atk, 'defense': self.stats.defense,
                'exp': self.stats.exp, 'exp_next': self.stats.exp_next, 'gold': self.stats.gold,
            },
            'inventory': self.inventory,
            'equipped': self.equipped,
            'quest_stage': self.quest_stage,
            'quest_flags': self.quest_flags,
            'boss_defeated': self.boss_defeated,
            'side_quests': self.side_quests,
            'quest_counters': self.quest_counters,
            'skill_points': self.skill_points,
            'unlocked_skills': list(self.unlocked_skills),
        }

    def load_save_dict(self, d):
        self.tx = d['tx']
        self.ty = d['ty']
        self.x = float(self.tx * TILE)
        self.y = float(self.ty * TILE)
        self.direction = d.get('direction', 'down')
        self.area = d.get('area', AREA_VILLAGE)
        s = d.get('stats', {})
        for k, v in s.items():
            setattr(self.stats, k, v)
        self.inventory = [tuple(i) for i in d.get('inventory', [])]
        self.equipped = d.get('equipped', {'weapon': None, 'armor': None, 'accessory': None})
        self.quest_stage = d.get('quest_stage', 0)
        self.quest_flags = d.get('quest_flags', {})
        self.boss_defeated = d.get('boss_defeated', {})
        self.side_quests = d.get('side_quests', {})
        self.quest_counters = d.get('quest_counters', {})
        self.skill_points = d.get('skill_points', 0)
        self.unlocked_skills = set(d.get('unlocked_skills', []))

    def can_unlock_skill(self, skill_id: str) -> bool:
        if skill_id in self.unlocked_skills:
            return False
        node = SKILL_TREE.get(skill_id)
        if not node:
            return False
        if self.skill_points < node.cost:
            return False
        if node.prereq and node.prereq not in self.unlocked_skills:
            return False
        return True

    def unlock_skill(self, skill_id: str) -> bool:
        if not self.can_unlock_skill(skill_id):
            return False
        node = SKILL_TREE[skill_id]
        self.skill_points -= node.cost
        self.unlocked_skills.add(skill_id)
        return True

    def get_combat_skills(self) -> List[Tuple[str, int, int]]:
        """返回战斗中可用的技能列表: [(name, power, mp_cost), ...]"""
        base_skills = [("黑客攻击", 15, 5), ("EMP脉冲", 25, 12), ("系统修复", 0, 8)]
        # MP减免
        mp_reduce = 0.0
        if 'hack_t1' in self.unlocked_skills:
            mp_reduce = SKILL_TREE['hack_t1'].effect['mp_reduce']
        if mp_reduce > 0:
            base_skills = [(n, p, max(1, int(c * (1 - mp_reduce)))) for n, p, c in base_skills]
        # 技能树战斗技能
        tree_combat = []
        for sid in self.unlocked_skills:
            node = SKILL_TREE.get(sid)
            if node and node.effect.get('type') == 'combat_skill':
                mp_cost = node.effect.get('mp_cost', 10)
                if mp_reduce > 0:
                    mp_cost = max(1, int(mp_cost * (1 - mp_reduce)))
                power = node.effect.get('power_pct', 0)
                tree_combat.append((node.name, power, mp_cost))
        return base_skills + tree_combat


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


# ============================================================
# 敌人
# ============================================================
@dataclass
class EnemyDef:
    name: str
    sprite_key: str
    hp: int
    atk: int
    defense: int
    exp: int
    gold: int
    skills: List[Tuple[str, int]] = field(default_factory=list)
    weakness: Optional[str] = None    # 'emp', 'hack', 'physical', None
    drops: List[Tuple[str, float]] = field(default_factory=list)  # (item_key, drop_rate)
    is_boss: bool = False

ENEMY_DEFS = {
    'slime': EnemyDef("纳米虫", "slime", 30, 6, 2, 18, 10,
                       [("腐蚀注入", 8)], weakness='physical',
                       drops=[('encrypted_data', 0.15)]),
    'bat': EnemyDef("侦察无人机", "bat", 25, 8, 1, 20, 15,
                     [("声波干扰", 10)], weakness='emp',
                     drops=[('encrypted_data', 0.10)]),
    'skeleton': EnemyDef("机械兵", "skeleton", 60, 14, 6, 45, 30,
                          [("激光斩", 18), ("导弹齐射", 15)], weakness='emp',
                          drops=[('precision_gear', 0.25)]),
    'dragon': EnemyDef("AI核心", "dragon", 200, 25, 12, 180, 150,
                        [("数据洪流", 35), ("电磁爪击", 28), ("系统尖啸", 20)], weakness='hack'),
    'golden_slime': EnemyDef("黄金纳米虫", "golden_slime", 50, 10, 4, 50, 100,
                              [("黄金冲击", 15)], weakness='physical'),
    'factory_guard': EnemyDef("工厂守卫", "factory_guard", 80, 16, 8, 55, 40,
                               [("电击", 20), ("钢铁冲撞", 16)], weakness='emp',
                               drops=[('precision_gear', 0.35)]),
    'glitch_bot': EnemyDef("故障机器人", "glitch_bot", 45, 12, 4, 25, 20,
                            [("数据干扰", 12)], weakness='emp',
                            drops=[('encrypted_data', 0.20)]),
    'cyber_virus': EnemyDef("网络病毒", "cyber_virus", 100, 20, 6, 80, 60,
                             [("数据腐蚀", 22), ("自我复制", 15)], weakness='hack',
                             drops=[('data_sample', 0.30)]),
    'data_ghost': EnemyDef("数据幽灵", "data_ghost", 70, 18, 3, 60, 45,
                            [("幽灵入侵", 20)], weakness='hack',
                            drops=[('data_sample', 0.35), ('encrypted_data', 0.15)]),
    'quantum_lord': EnemyDef("量子霸主", "quantum_lord", 400, 35, 18, 300, 250,
                              [("量子崩塌", 45), ("维度撕裂", 38), ("数据风暴", 30)], weakness='hack'),
    # 新Boss
    'mad_overseer': EnemyDef("失控监工", "mad_overseer", 150, 20, 10, 120, 100,
                              [("高压电击", 25), ("机械臂横扫", 20), ("过载冲击", 30)],
                              weakness='emp', is_boss=True),
    'ai_core_boss': EnemyDef("觉醒AI核心", "ai_core_boss", 250, 28, 14, 200, 180,
                              [("数据洪流", 35), ("防火墙", 0), ("核心过载", 40)],
                              weakness='hack', is_boss=True),
    'quantum_overlord': EnemyDef("量子霸主·真身", "quantum_overlord", 500, 40, 20, 500, 400,
                                  [("量子崩塌", 50), ("维度撕裂", 42), ("数据风暴", 35), ("时空扭曲", 55)],
                                  weakness='hack', is_boss=True),
    # 新普通敌人
    'pipe_worm': EnemyDef("管道蠕虫", "pipe_worm", 35, 10, 3, 22, 15,
                           [("酸液喷射", 12)], weakness='physical',
                           drops=[('encrypted_data', 0.15)]),
    'security_drone': EnemyDef("安保无人机", "security_drone", 65, 15, 6, 40, 30,
                                [("激光扫射", 18), ("自爆协议", 22)], weakness='emp',
                                drops=[('precision_gear', 0.20)]),
    'black_market_thug': EnemyDef("黑市打手", "black_market_thug", 90, 18, 8, 55, 50,
                                   [("暗器投掷", 20), ("连环拳", 16)], weakness='physical'),
    'darknet_guard': EnemyDef("暗网守卫", "darknet_guard", 120, 22, 10, 75, 60,
                               [("数据锁链", 24), ("暗网入侵", 20)], weakness='hack',
                               drops=[('data_sample', 0.25)]),
}

ENCOUNTER_TABLE = {
    AREA_VILLAGE: [],
    AREA_NEON_STREET: [],
    AREA_BLACK_MARKET: [],
    AREA_FOREST: ['slime', 'slime', 'bat', 'bat', 'skeleton'],
    AREA_DUNGEON: ['skeleton', 'skeleton', 'bat', 'skeleton', 'dragon'],
    AREA_FACTORY: ['glitch_bot', 'glitch_bot', 'factory_guard', 'factory_guard', 'glitch_bot'],
    AREA_CYBERSPACE: ['cyber_virus', 'cyber_virus', 'data_ghost', 'data_ghost', 'cyber_virus'],
    AREA_TUNNEL: ['pipe_worm', 'pipe_worm', 'security_drone', 'pipe_worm', 'security_drone'],
}
