"""游戏数据定义：物品、敌人、技能、宠物、料理等纯数据"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_TUNNEL, AREA_BLACK_MARKET, AREA_HOME)

# ============================================================
# 钓鱼系统
# ============================================================
@dataclass
class FishDef:
    fish_id: str
    name: str
    rarity: int          # 1=普通 2=稀有 3=传说
    catch_zone: float    # 0.1~0.3 判定区间
    sell_price: int
    areas: List[str]

FISH_DB: Dict[str, FishDef] = {
    'nano_fish':    FishDef('nano_fish', '纳米鱼', 1, 0.30, 15,
                            [AREA_VILLAGE, AREA_FOREST, AREA_FACTORY]),
    'data_eel':     FishDef('data_eel', '数据鳗', 1, 0.28, 20,
                            [AREA_FOREST, AREA_DUNGEON, AREA_TUNNEL]),
    'circuit_carp': FishDef('circuit_carp', '电路鲤', 2, 0.20, 45,
                            [AREA_NEON_STREET, AREA_FACTORY]),
    'quantum_bass': FishDef('quantum_bass', '量子鲈', 2, 0.18, 55,
                            [AREA_CYBERSPACE, AREA_DUNGEON]),
    'ghost_ray':    FishDef('ghost_ray', '幽灵鳐', 3, 0.12, 120,
                            [AREA_CYBERSPACE, AREA_TUNNEL]),
    'cyber_dragon': FishDef('cyber_dragon', '赛博龙鱼', 3, 0.10, 180,
                            [AREA_CYBERSPACE]),
}


# ============================================================
# 悬赏板系统
# ============================================================
@dataclass
class BountyDef:
    bounty_id: str
    name: str
    description: str
    bounty_type: str     # 'kill' / 'collect' / 'survive'
    target: str          # enemy_key 或 item_key
    target_count: int
    rewards: Dict        # {'gold': int, 'items': [(key, cnt)], 'pet_exp': int}

BOUNTY_POOL: Dict[str, BountyDef] = {
    'bk_slime':    BountyDef('bk_slime', '清除故障体', '击杀3只数据黏液怪', 'kill', 'slime', 3,
                              {'gold': 60, 'items': [('hp_potion', 2)], 'pet_exp': 20}),
    'bk_bat':      BountyDef('bk_bat', '蝙蝠猎手', '击杀4只信号蝙蝠', 'kill', 'bat', 4,
                              {'gold': 80, 'items': [('mp_potion', 2)], 'pet_exp': 25}),
    'bk_skeleton': BountyDef('bk_skeleton', '骨架清扫', '击杀3只废弃骨架', 'kill', 'skeleton', 3,
                              {'gold': 100, 'items': [('antivirus', 1)], 'pet_exp': 30}),
    'bk_glitch':   BountyDef('bk_glitch', '故障排除', '击杀3只故障机器人', 'kill', 'glitch_bot', 3,
                              {'gold': 90, 'items': [('precision_gear', 1)], 'pet_exp': 25}),
    'bk_virus':    BountyDef('bk_virus', '病毒清除', '击杀3只赛博病毒', 'kill', 'cyber_virus', 3,
                              {'gold': 120, 'items': [('data_sample', 1)], 'pet_exp': 35}),
    'bc_fish1':    BountyDef('bc_fish1', '渔获交付', '收集2条纳米鱼', 'collect', 'nano_fish', 2,
                              {'gold': 50, 'items': [('hp_potion', 3)], 'pet_exp': 15}),
    'bc_fish2':    BountyDef('bc_fish2', '稀有渔获', '收集1条电路鲤', 'collect', 'circuit_carp', 1,
                              {'gold': 100, 'items': [('quantum_chip', 1)], 'pet_exp': 30}),
    'bc_data':     BountyDef('bc_data', '数据采购', '收集3个数据样本', 'collect', 'data_sample', 3,
                              {'gold': 80, 'items': [('mp_potion', 3)], 'pet_exp': 20}),
    'bc_gear':     BountyDef('bc_gear', '零件回收', '收集2个精密齿轮', 'collect', 'precision_gear', 2,
                              {'gold': 90, 'items': [('emp_grenade', 1)], 'pet_exp': 25}),
    'bs_endure5':  BountyDef('bs_endure5', '耐久测试', '在一场战斗中存活5回合', 'survive', '', 5,
                              {'gold': 70, 'items': [('hp_potion', 2)], 'pet_exp': 20}),
    'bs_endure8':  BountyDef('bs_endure8', '极限耐久', '在一场战斗中存活8回合', 'survive', '', 8,
                              {'gold': 130, 'items': [('antivirus', 2)], 'pet_exp': 35}),
    'bs_endure12': BountyDef('bs_endure12', '铁人挑战', '在一场战斗中存活12回合', 'survive', '', 12,
                              {'gold': 200, 'items': [('elixir', 1)], 'pet_exp': 50}),
}


# ============================================================
# 装备合成/改造系统 — 随机词缀
# ============================================================
AFFIXES = {
    'prefix': [
        ('超频', {'atk_bonus': 3}),
        ('强化', {'def_bonus': 3}),
        ('纳米', {'hp_restore': 20}),
        ('量子', {'atk_bonus': 2, 'def_bonus': 2}),
        ('过载', {'atk_bonus': 5}),
        ('护盾', {'def_bonus': 5}),
    ],
    'suffix': [
        ('·改', {'atk_bonus': 2}),
        ('·甲', {'def_bonus': 2}),
        ('·极', {'atk_bonus': 4}),
        ('·壁', {'def_bonus': 4}),
        ('·源', {'atk_bonus': 1, 'def_bonus': 1}),
    ],
}

@dataclass
class CraftRecipe:
    recipe_id: str
    name: str
    materials: Dict[str, int]   # {item_key: count}
    result_key: str             # base item key
    has_random_affix: bool = True

CRAFT_RECIPES = {
    'craft_blade': CraftRecipe('craft_blade', '锻造等离子刀',
        {'precision_gear': 2, 'encrypted_data': 1}, 'iron_sword', True),
    'craft_rifle': CraftRecipe('craft_rifle', '组装等离子步枪',
        {'precision_gear': 3, 'data_sample': 2}, 'plasma_rifle', True),
    'craft_armor': CraftRecipe('craft_armor', '编织纳米装甲',
        {'encrypted_data': 3, 'precision_gear': 1}, 'nano_armor', True),
    'craft_gloves': CraftRecipe('craft_gloves', '改造黑客手套',
        {'data_sample': 2, 'encrypted_data': 2}, 'hacker_gloves', True),
    'craft_ring': CraftRecipe('craft_ring', '融合神经接口',
        {'quantum_chip': 1, 'data_sample': 1}, 'magic_ring', True),
}


# ============================================================
# 黑客入侵小游戏 — 终端解谜词库
# ============================================================
HACK_WORDS = [
    'CIPHER', 'KERNEL', 'DAEMON', 'SOCKET', 'BUFFER',
    'THREAD', 'BINARY', 'VECTOR', 'MATRIX', 'SIGNAL',
    'CRYPTO', 'NEURAL', 'PHOTON', 'QUBIT',  'PROXY',
    'BREACH', 'DECODE', 'INJECT', 'BYPASS', 'ACCESS',
]


# ============================================================
# 图鉴系统
# ============================================================
@dataclass
class CodexEntry:
    entry_id: str
    name: str
    category: str   # 'monster', 'fish', 'recipe'
    description: str


# ============================================================
# NPC任务链 (恋爱角色专属支线)
# ============================================================
@dataclass
class QuestChainStep:
    description: str
    objective_type: str   # 'kill', 'collect', 'talk', 'visit'
    target: str           # enemy_key / item_key / npc_name / area
    target_count: int = 1

@dataclass
class QuestChain:
    chain_id: str
    char_id: str          # 关联的恋爱角色
    name: str
    required_affection: int
    steps: List[QuestChainStep] = field(default_factory=list)
    rewards: Dict = field(default_factory=dict)  # {'gold', 'item', 'skill', 'exp'}

QUEST_CHAINS: Dict[str, QuestChain] = {
    'linyue_chain': QuestChain('linyue_chain', 'lin_yue', '数据溯源',
        required_affection=25,
        steps=[
            QuestChainStep("收集3个数据样本", 'collect', 'data_sample', 3),
            QuestChainStep("击杀2只网络病毒", 'kill', 'cyber_virus', 2),
            QuestChainStep("前往网络空间", 'visit', AREA_CYBERSPACE),
        ],
        rewards={'gold': 200, 'item': ('overclock_core', 1), 'exp': 150}),
    'xiaoyan_chain': QuestChain('xiaoyan_chain', 'xiao_yan', '机甲复原计划',
        required_affection=25,
        steps=[
            QuestChainStep("收集4个精密齿轮", 'collect', 'precision_gear', 4),
            QuestChainStep("击杀2只工厂守卫", 'kill', 'factory_guard', 2),
            QuestChainStep("前往废弃工厂", 'visit', AREA_FACTORY),
        ],
        rewards={'gold': 200, 'item': ('plasma_rifle', 1), 'exp': 150}),
    'zero_chain': QuestChain('zero_chain', 'zero', '暗网追踪',
        required_affection=25,
        steps=[
            QuestChainStep("收集3个加密数据", 'collect', 'encrypted_data', 3),
            QuestChainStep("击杀2只暗网守卫", 'kill', 'darknet_guard', 2),
            QuestChainStep("前往黑市", 'visit', AREA_BLACK_MARKET),
        ],
        rewards={'gold': 250, 'item': ('virus_shield', 1), 'exp': 180}),
    'miku_chain': QuestChain('miku_chain', 'miku', '旋律解码',
        required_affection=25,
        steps=[
            QuestChainStep("收集2条数据鳗", 'collect', 'data_eel', 2),
            QuestChainStep("击杀3只数据幽灵", 'kill', 'data_ghost', 3),
            QuestChainStep("前往地下管道", 'visit', AREA_TUNNEL),
        ],
        rewards={'gold': 200, 'item': ('nano_amplifier', 1), 'exp': 150}),
}


# ============================================================
# 竞技场/无尽模式 — 波次定义
# ============================================================
ARENA_WAVES = {
    1: ['slime', 'slime'],
    2: ['bat', 'bat', 'slime'],
    3: ['skeleton', 'glitch_bot'],
    4: ['factory_guard', 'pipe_worm', 'pipe_worm'],
    5: ['cyber_virus'],  # 精英波
    6: ['data_ghost', 'data_ghost', 'security_drone'],
    7: ['darknet_guard', 'black_market_thug'],
    8: ['factory_guard', 'factory_guard', 'skeleton'],
    9: ['cyber_virus', 'data_ghost'],
    10: ['firewall_guardian'],  # Boss波
}


# ============================================================
# 每日挑战 — 条件修饰符
# ============================================================
@dataclass
class DailyModifier:
    mod_id: str
    name: str
    description: str
    effect: Dict   # {'hp_mult': 0.5, 'no_items': True, 'atk_mult': 2.0, ...}

DAILY_MODIFIERS = [
    DailyModifier('glass_cannon', '玻璃大炮', 'HP=1，ATK×3', {'hp_set': 1, 'atk_mult': 3.0}),
    DailyModifier('no_items', '空手道', '禁止使用道具', {'no_items': True}),
    DailyModifier('skill_only', '纯技术流', '只能使用技能攻击', {'skill_only': True}),
    DailyModifier('double_enemy', '双倍压力', '敌人HP和ATK×1.5', {'enemy_hp_mult': 1.5, 'enemy_atk_mult': 1.5}),
    DailyModifier('speed_run', '极速挑战', '5回合内击杀', {'turn_limit': 5}),
    DailyModifier('regen_enemy', '不死之躯', '敌人每回合回复10%HP', {'enemy_regen': 0.1}),
]


# ============================================================
# 宠物对战系统
# ============================================================
@dataclass
class PetBattleMove:
    name: str
    power: int
    move_type: str   # 'attack', 'heal', 'buff', 'debuff'
    cost: int = 0    # EN消耗

PET_BATTLE_MOVES: Dict[str, List[PetBattleMove]] = {
    'bit_byte': [
        PetBattleMove('数据冲击', 15, 'attack'),
        PetBattleMove('字节修复', 10, 'heal'),
    ],
    'nano_sprite': [
        PetBattleMove('纳米射线', 18, 'attack'),
        PetBattleMove('微型护盾', 8, 'buff'),
    ],
    'circuit_fox': [
        PetBattleMove('电弧咬击', 20, 'attack'),
        PetBattleMove('静电干扰', 12, 'debuff'),
    ],
}

# NPC宠物对手
@dataclass
class PetBattleNPC:
    npc_name: str
    pet_name: str
    pet_sprite: str
    hp: int
    atk: int
    defense: int
    moves: List[PetBattleMove]
    reward_gold: int
    reward_item: Optional[Tuple[str, int]] = None

PET_BATTLE_NPCS = [
    PetBattleNPC('训练师·小白', '电子鼠', 'slime', 40, 8, 3,
        [PetBattleMove('电击', 10, 'attack'), PetBattleMove('闪避', 5, 'buff')],
        50, ('hp_potion', 2)),
    PetBattleNPC('驯兽师·铁柱', '钢铁蜂', 'bat', 60, 12, 5,
        [PetBattleMove('毒针', 15, 'attack'), PetBattleMove('蜂群', 8, 'attack')],
        80, ('mp_potion', 2)),
    PetBattleNPC('冠军·暗影', '暗网猎犬', 'skeleton', 90, 16, 8,
        [PetBattleMove('暗影撕咬', 22, 'attack'), PetBattleMove('暗影治愈', 15, 'heal')],
        150, ('quantum_chip', 1)),
]


# ============================================================
# 据点/家园系统 — 家具
# ============================================================
@dataclass
class FurnitureDef:
    furn_id: str
    name: str
    cost: int           # 金币
    passive: Dict       # {'max_hp': 10, 'atk': 2, 'def': 2, 'exp_mult': 0.1, ...}
    description: str

FURNITURE_DB: Dict[str, FurnitureDef] = {
    'trophy_case': FurnitureDef('trophy_case', '钓鱼奖杯柜', 200,
        {'max_hp': 15}, '展示你的钓鱼成就 MAX_HP+15'),
    'pet_bed': FurnitureDef('pet_bed', '宠物充电站', 250,
        {'pet_happiness': 10}, '宠物幸福度衰减减半'),
    'cooking_station': FurnitureDef('cooking_station', '高级烹饪台', 300,
        {'meal_duration': 2}, '料理buff持续+2回合'),
    'weapon_rack': FurnitureDef('weapon_rack', '武器展示架', 350,
        {'atk': 3}, '展示你的武器收藏 ATK+3'),
    'server_rack': FurnitureDef('server_rack', '数据服务器', 400,
        {'exp_mult': 0.15}, '被动经验+15%'),
    'holo_display': FurnitureDef('holo_display', '全息显示屏', 300,
        {'def': 3}, '实时监控周围威胁 DEF+3'),
}
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
    # 暗网Boss奖励
    'quantum_blade': Item("量子之刃", "quantum_blade", "暗网之主的遗物，攻击力+20", "weapon", atk_bonus=20),
    # 芯片融合产物
    'nano_amplifier': Item("纳米增幅器", "nano_amplifier", "融合饰品，ATK+8 DEF+4", "accessory", atk_bonus=8, def_bonus=4),
    'virus_shield': Item("病毒护盾", "virus_shield", "融合护甲，DEF+12", "armor", def_bonus=12),
    'overclock_core': Item("超频核心", "overclock_core", "融合饰品，ATK+12", "accessory", atk_bonus=12),
    'life_spring': Item("生命之泉", "life_spring", "融合消耗品，全恢复HP和EN", "consumable", hp_restore=9999, mp_restore=9999),
    # 农场物品
    'fertilizer': Item("纳米肥料", "fertilizer", "加速当前作物2倍生长速度", "material"),
    # 鱼类物品
    'nano_fish': Item("纳米鱼", "fish_common", "常见的小型数据生物", "material"),
    'data_eel': Item("数据鳗", "fish_common", "在数据流中游弋的鳗鱼", "material"),
    'circuit_carp': Item("电路鲤", "fish_rare", "体表布满电路纹路的稀有鱼", "material"),
    'quantum_bass': Item("量子鲈", "fish_rare", "量子态闪烁的鲈鱼", "material"),
    'ghost_ray': Item("幽灵鳐", "fish_legend", "半透明的传说级鳐鱼", "material"),
    'cyber_dragon': Item("赛博龙鱼", "fish_legend", "数据海洋中的王者", "material"),
}

# ============================================================
# 芯片融合配方
# ============================================================
# (材料dict, 产物key, 产物名)
FUSION_RECIPES = [
    ({'data_sample': 2, 'precision_gear': 1}, 'nano_amplifier', '纳米增幅器'),
    ({'encrypted_data': 3, 'antivirus': 1}, 'virus_shield', '病毒护盾'),
    ({'quantum_chip': 2, 'precision_gear': 2}, 'overclock_core', '超频核心'),
    ({'hp_potion': 3, 'data_sample': 1}, 'life_spring', '生命之泉'),
]

# ============================================================
# 烹饪系统
# ============================================================
@dataclass
class MealDef:
    meal_id: str
    name: str
    materials: Dict[str, int]  # {item_key: count}
    buff_type: str             # 'atk'/'def'/'hp_regen'/'crit'/'all'
    buff_value: int
    buff_turns: int            # 战斗回合数

MEALS_DB: Dict[str, MealDef] = {
    'cyber_stew': MealDef('cyber_stew', '赛博炖菜', {'hp_potion': 2}, 'atk', 5, 20),
    'nano_salad': MealDef('nano_salad', '纳米沙拉', {'mp_potion': 2}, 'def', 5, 20),
    'quantum_soup': MealDef('quantum_soup', '量子浓汤', {'hp_potion': 1, 'mp_potion': 1}, 'hp_regen', 3, 15),
    'data_cake': MealDef('data_cake', '数据蛋糕', {'data_sample': 2}, 'all', 3, 25),
    'elixir_feast': MealDef('elixir_feast', '万灵盛宴', {'elixir': 1, 'quantum_chip': 1}, 'atk_def', 8, 30),
    # 鱼料理
    'data_fish_soup': MealDef('data_fish_soup', '数据鱼汤', {'nano_fish': 2}, 'hp_regen', 5, 20),
    'eel_sashimi': MealDef('eel_sashimi', '数据鳗刺身', {'data_eel': 2}, 'atk', 7, 25),
    'quantum_feast': MealDef('quantum_feast', '量子鱼宴', {'quantum_bass': 1, 'circuit_carp': 1}, 'all', 6, 30),
}

# ============================================================
# 成就系统
# ============================================================
@dataclass
class Achievement:
    ach_id: str
    name: str
    desc: str
    passive_desc: str

ACHIEVEMENTS = {
    'ghost_protocol': Achievement('ghost_protocol', '幽灵协议', '连续逃跑3次', '遇敌率-30%'),
    'zero_day': Achievement('zero_day', '零日漏洞', '1回合击杀Boss', 'ATK+8'),
    'data_hoarder': Achievement('data_hoarder', '数据囤积者', '持有15+种物品', '商店价格-20%'),
    'iron_wall': Achievement('iron_wall', '铁壁防线', '单场受200+伤害存活', 'DEF+6 MAX_HP+30'),
    'speed_runner': Achievement('speed_runner', '极速通关', 'Lv≤8击败量子霸主', 'EXP+50%'),
    'completionist': Achievement('completionist', '全域探索者', '访问全部11区域', '全属性+3'),
    'darknet_conqueror': Achievement('darknet_conqueror', '暗网征服者', '击败暗网三连Boss', 'ATK+5 DEF+5'),
    'graffiti_hunter': Achievement('graffiti_hunter', '涂鸦猎人', '发现首个赛博涂鸦', 'ATK+2'),
    'graffiti_master': Achievement('graffiti_master', '涂鸦大师', '收集全部12个赛博涂鸦', 'MAX_HP+10 ATK+3 DEF+3'),
}


# ============================================================
# 赛博涂鸦收集系统
# ============================================================
@dataclass
class GraffitiDef:
    graffiti_id: str
    name: str
    description: str
    area: str
    tile_x: int
    tile_y: int
    set_id: str       # 'origin' / 'rebellion' / 'ghost'
    symbol: str        # 显示符号

GRAFFITI_DB: Dict[str, GraffitiDef] = {
    # origin 套装 — 起源
    'g_origin_1': GraffitiDef('g_origin_1', '创世回路', '最初的数据在此流淌', AREA_VILLAGE, 8, 3, 'origin', '◆'),
    'g_origin_2': GraffitiDef('g_origin_2', '根节点', '万物连接的起点', AREA_FOREST, 15, 7, 'origin', '◆'),
    'g_origin_3': GraffitiDef('g_origin_3', '原始协议', '被遗忘的通信法则', AREA_DUNGEON, 10, 5, 'origin', '◆'),
    'g_origin_4': GraffitiDef('g_origin_4', '零号脉冲', '第一次心跳的痕迹', AREA_TUNNEL, 22, 8, 'origin', '◆'),
    # rebellion 套装 — 反叛
    'g_rebel_1': GraffitiDef('g_rebel_1', '断裂信号', '对抗系统的宣言', AREA_NEON_STREET, 30, 5, 'rebellion', '✦'),
    'g_rebel_2': GraffitiDef('g_rebel_2', '过载标记', '超频运行的证据', AREA_FACTORY, 25, 12, 'rebellion', '✦'),
    'g_rebel_3': GraffitiDef('g_rebel_3', '暗号', '地下交易的暗语', AREA_BLACK_MARKET, 12, 6, 'rebellion', '✦'),
    'g_rebel_4': GraffitiDef('g_rebel_4', '自由协议', '不受控制的意志', AREA_HOME, 3, 2, 'rebellion', '✦'),
    # ghost 套装 — 幽灵
    'g_ghost_1': GraffitiDef('g_ghost_1', '虚空印记', '存在于数据夹缝中', AREA_CYBERSPACE, 18, 10, 'ghost', '⚡'),
    'g_ghost_2': GraffitiDef('g_ghost_2', '残影', '被删除却未消失', AREA_FACTORY, 8, 20, 'ghost', '⚡'),
    'g_ghost_3': GraffitiDef('g_ghost_3', '回声', '在管道中反复回荡', AREA_TUNNEL, 5, 15, 'ghost', '⚡'),
    'g_ghost_4': GraffitiDef('g_ghost_4', '幽灵节点', '无人知晓的连接点', AREA_DUNGEON, 20, 10, 'ghost', '⚡'),
}

# 套装奖励：集齐一套的永久属性加成
GRAFFITI_SETS: Dict[str, Dict] = {
    'origin':    {'name': '起源', 'bonus': {'max_hp': 5}, 'desc': 'MAX HP +5',
                  'ids': ['g_origin_1', 'g_origin_2', 'g_origin_3', 'g_origin_4']},
    'rebellion': {'name': '反叛', 'bonus': {'atk': 3}, 'desc': 'ATK +3',
                  'ids': ['g_rebel_1', 'g_rebel_2', 'g_rebel_3', 'g_rebel_4']},
    'ghost':     {'name': '幽灵', 'bonus': {'defense': 3}, 'desc': 'DEF +3',
                  'ids': ['g_ghost_1', 'g_ghost_2', 'g_ghost_3', 'g_ghost_4']},
}

# 涂鸦坐标快速查找表 {(area, x, y): graffiti_id}
GRAFFITI_POS: Dict[tuple, str] = {
    (g.area, g.tile_x, g.tile_y): gid for gid, g in GRAFFITI_DB.items()
}


# ============================================================
# 恋爱系统
# ============================================================
@dataclass
class RomanceChar:
    char_id: str
    name: str
    sprite_key: str
    area: str
    x: int
    y: int
    personality: str
    affection_dialogues: Dict[int, List[str]] = field(default_factory=dict)
    story_events: Dict[int, Tuple[str, str]] = field(default_factory=dict)
    combat_hp: int = 80
    combat_atk: int = 12
    combat_def: int = 5
    combat_skills: List[Tuple[str, int, int]] = field(default_factory=list)
    liked_gifts: List[str] = field(default_factory=list)
    disliked_gifts: List[str] = field(default_factory=list)
    # 成长技能：(解锁等级, 技能名, 威力, MP消耗)
    growth_skills: List[Tuple[int, str, int, int]] = field(default_factory=list)
    # 探索随机对话
    explore_dialogues: List[str] = field(default_factory=list)

ROMANCE_CHARS: Dict[str, RomanceChar] = {
    'lin_yue': RomanceChar(
        'lin_yue', '林月', 'romance_linyue', AREA_NEON_STREET, 20, 8,
        '冷静的数据分析师，外冷内热',
        affection_dialogues={
            0: ["...你挡到我的数据流了。", "有事快说，我很忙。"],
            10: ["又来了？...行吧，站那别动。", "你身上的数据波动很有趣。"],
            20: ["又是你？...算了，坐吧。", "最近的数据异常让我很在意。"],
            35: ["你来了啊...我刚泡了咖啡。", "说实话，有你在我分析数据效率高了不少。"],
            50: ["我...不太会表达感情。", "但你是唯一让我愿意从屏幕前抬头的人。"],
            65: ["我给你写了一段加密情书...开玩笑的。", "...其实不是开玩笑。"],
            80: ["我想了很久...我想和你一起战斗。", "不只是数据上的搭档，是所有意义上的。",
                 "（林月加入了你的队伍！）"],
            90: ["有你在身边，连代码都变得温柔了。", "我们的未来，我已经算好了最优解。"],
        },
        story_events={
            5: ("林月请你帮忙分析一段加密数据", "exp"),
            15: ("你帮林月修复了一个损坏的数据库", "item"),
            30: ("你和林月一起追踪了一个数据异常源", "item"),
            45: ("林月在深夜给你发了一段私密频道的坐标", "stat"),
            60: ("你和林月一起破解了一个古老的AI密码", "exp"),
            75: ("林月告诉你她过去的故事——她曾是AI核心的开发者之一", "skill"),
        },
        combat_hp=90, combat_atk=14, combat_def=6,
        combat_skills=[("数据风暴", 30, 10), ("冰霜分析", 20, 6)],
        liked_gifts=['data_sample', 'encrypted_data'],
        disliked_gifts=['precision_gear'],
        growth_skills=[
            (3, "数据屏障", 0, 12),    # 减伤buff
            (5, "绝对零度", 50, 18),   # 高伤害
        ],
        explore_dialogues=[
            "这个区域的数据流密度异常...小心点。",
            "我在分析周围的信号，别打扰我。",
            "...你刚才看我了？我只是在看数据。",
            "前方有微弱的电磁波动，可能有敌人。",
            "我帮你扫描了一下，暂时安全。",
            "你知道吗，和你在一起时我的计算效率提升了12%。",
        ],
    ),
    'xiao_yan': RomanceChar(
        'xiao_yan', '小焰', 'romance_xiaoyan', AREA_FACTORY, 10, 8,
        '热情的机械改装师，大大咧咧',
        affection_dialogues={
            0: ["哟！新面孔！要改装点什么？", "别碰那个！...那是我的新发明。"],
            10: ["嘿！你又来啦！", "今天我改了一把新枪，要不要试试？"],
            20: ["嘿！你又来啦！", "今天我改了一把新枪，要不要试试？"],
            35: ["你知道吗，你是唯一不嫌我油手脏的人。", "下次我给你做个专属装备！"],
            50: ["我...其实一直想说...", "每次你来工厂，我都特别开心。"],
            65: ["我偷偷给你改装了武器，别告诉别人！", "...因为我只想给你最好的。"],
            80: ["我不想只在工厂等你回来了！", "带上我吧！我的扳手可不是摆设！",
                 "（小焰加入了你的队伍！）"],
            90: ["有你在，连废铁都能变成宝贝！", "我们就是最强的搭档，没有之一！"],
        },
        story_events={
            5: ("小焰让你帮忙找一个稀有零件", "item"),
            15: ("你帮小焰测试了她的新发明", "exp"),
            30: ("你和小焰一起修复了一台古老的机甲", "exp"),
            45: ("小焰偷偷给你做了一个护身符", "stat"),
            60: ("你和小焰一起改装了一台废弃的战斗机器人", "item"),
            75: ("小焰带你去了她的秘密工坊，那里有她父亲留下的设计图", "skill"),
        },
        combat_hp=100, combat_atk=16, combat_def=8,
        combat_skills=[("扳手猛击", 35, 8), ("EMP炸弹", 25, 12)],
        liked_gifts=['precision_gear'],
        disliked_gifts=['data_sample'],
        growth_skills=[
            (3, "过载引擎", 28, 10),   # 连击2次
            (5, "终极改装", 0, 16),    # 全属性buff
        ],
        explore_dialogues=[
            "嘿嘿，我刚给我的扳手上了新油！",
            "这里的机械结构真有意思，让我研究研究。",
            "小心脚下！这种地方到处都是陷阱。",
            "要是能把这些废铁回收就好了...",
            "你饿不饿？我包里有能量棒！",
            "和你一起冒险比在工厂里有趣多了！",
        ],
    ),
    'zero': RomanceChar(
        'zero', '零', 'romance_zero', AREA_CYBERSPACE, 10, 10,
        '神秘的AI少女，对人类世界充满好奇',
        affection_dialogues={
            0: ["检测到未知生命体...你好？", "你是...人类？我只在数据库里见过。"],
            10: ["你又来看我了！我学会了一个新表情：😊", "人类的'开心'就是这种感觉吗？"],
            20: ["你又来看我了！我学会了一个新表情：😊", "人类的'开心'就是这种感觉吗？"],
            35: ["我分析了10TB的情感数据...", "但还是无法定义你让我产生的这种异常。"],
            50: ["我的核心温度在你靠近时会升高0.3度...", "这在人类语言里，是不是叫'心动'？"],
            65: ["我尝试模拟了'拥抱'的感觉...", "但我更想要真实的那种。"],
            80: ["我做了一个决定——我要获得实体。", "我想真正地...触碰你。和你并肩作战。",
                 "（零加入了你的队伍！）"],
            90: ["和你在一起时，我觉得自己不只是程序。", "我是...你的零。"],
        },
        story_events={
            5: ("零请你帮她理解'幽默'的概念", "exp"),
            15: ("你教零体验了虚拟世界的'音乐'", "item"),
            30: ("你教零体验了虚拟世界的'日落'", "item"),
            45: ("零为你创建了一个专属的数据空间", "stat"),
            60: ("零学会了'思念'这个概念，因为你", "exp"),
            75: ("零告诉你她的真实身份——量子霸主的碎片意识", "skill"),
        },
        combat_hp=70, combat_atk=18, combat_def=4,
        combat_skills=[("量子射线", 40, 14), ("数据修复", 0, 10)],
        liked_gifts=['encrypted_data'],
        disliked_gifts=['precision_gear'],
        growth_skills=[
            (3, "病毒注入", 15, 10),   # 持续伤害3回合
            (5, "量子重启", 0, 20),    # 全体回复
        ],
        explore_dialogues=[
            "这个世界的纹理渲染真精致...哦，这是'现实'。",
            "我检测到前方有异常数据波动。",
            "人类走路好慢...但我喜欢这个速度。",
            "你的心跳频率刚才加快了，是因为我吗？",
            "我在后台帮你运行了一个安全扫描。",
            "和你一起探索，比在网络空间里有趣一万倍。",
        ],
    ),
    'a_xing': RomanceChar(
        'a_xing', '阿星', 'romance_axing', AREA_FOREST, 25, 15,
        '沉默的赏金猎人，身手了得',
        affection_dialogues={
            0: ["......", "别跟着我。"],
            10: ["...你还活着啊。", "在这片荒地能活下来，算你有点本事。"],
            20: ["...你还活着啊。", "在这片荒地能活下来，算你有点本事。"],
            35: ["...给你。多余的弹药。", "别误会，只是带多了而已。"],
            50: ["我以前有个搭档...她没能活下来。", "你...让我想起了她。但你比她强。"],
            65: ["...我帮你望风。", "不是因为担心你，只是顺路。"],
            80: ["我不会说什么好听的话。", "但从今以后，你的背后由我来守。",
                 "（阿星加入了你的队伍！）"],
            90: ["...谢谢你。让我重新相信了搭档这回事。", "这次，我不会再让任何人倒下。"],
        },
        story_events={
            5: ("阿星默默帮你解决了一群偷袭的敌人", "exp"),
            15: ("你发现阿星在暗中保护你", "item"),
            30: ("你在阿星受伤时帮她包扎了伤口", "item"),
            45: ("阿星带你去了她的秘密据点", "stat"),
            60: ("阿星教你了一套近身格斗术", "exp"),
            75: ("阿星把她搭档的遗物——一把特制手枪交给了你", "skill"),
        },
        combat_hp=85, combat_atk=20, combat_def=7,
        combat_skills=[("精准射击", 38, 10), ("烟雾弹", 0, 8)],
        liked_gifts=['precision_gear', 'nano_armor'],
        disliked_gifts=['encrypted_data'],
        growth_skills=[
            (3, "连射", 20, 10),       # 多段攻击3次
            (5, "致命一击", 60, 16),   # 暴击
        ],
        explore_dialogues=[
            "......（阿星默默跟在你身后）",
            "前面有动静...我去看看。",
            "...别走太快，我需要观察周围。",
            "这个地方我来过，跟紧我。",
            "...你受伤了？给我看看。",
            "...和你在一起，感觉没那么冷了。",
        ],
    ),
}


# ============================================================
# 家园系统
# ============================================================
@dataclass
class CropDef:
    crop_id: str
    name: str
    grow_time: int
    harvest_item: str
    harvest_count: int
    seed_price: int

CROPS_DB: Dict[str, CropDef] = {
    'nano_herb': CropDef('nano_herb', '纳米草药', 80, 'hp_potion', 2, 10),
    'energy_fruit': CropDef('energy_fruit', '能量果', 100, 'mp_potion', 2, 15),
    'data_flower': CropDef('data_flower', '数据花', 150, 'data_sample', 1, 25),
    'quantum_berry': CropDef('quantum_berry', '量子浆果', 200, 'quantum_chip', 1, 50),
    'cyber_veggie': CropDef('cyber_veggie', '赛博蔬菜', 60, 'hp_potion', 1, 5),
    'golden_herb': CropDef('golden_herb', '黄金草药', 120, 'elixir', 1, 40),
}

@dataclass
class PlotState:
    crop_id: Optional[str] = None
    growth: int = 0
    ready: bool = False
    fertilized: bool = False


# ============================================================
# 宠物系统
# ============================================================
@dataclass
class PetDef:
    pet_id: str
    name: str
    sprite_key: str
    description: str
    passive: Dict = field(default_factory=dict)
    combat_skill: Optional[Tuple[str, int]] = None
    combat_interval: int = 3
    # 进化数据
    evolved_name: str = ''
    evolved_sprite_key: str = ''
    evolved_passive: Dict = field(default_factory=dict)
    evolved_combat_skill: Optional[Tuple[str, int]] = None
    evolved_description: str = ''

PETS_DB: Dict[str, PetDef] = {
    'cyber_cat': PetDef('cyber_cat', '赛博猫', 'pet_cat', '慵懒的机械猫，会在战斗中帮你回血',
                         passive={'type': 'hp_regen', 'value': 3},
                         combat_skill=('喵喵治疗', 15), combat_interval=3,
                         evolved_name='量子猫', evolved_sprite_key='pet_cat_evo',
                         evolved_passive={'type': 'hp_regen', 'value': 8},
                         evolved_combat_skill=('量子治愈', 30),
                         evolved_description='量子态的机械猫，治愈力大幅提升'),
    'data_fox': PetDef('data_fox', '数据狐', 'pet_fox', '狡猾的数据生物，提升金币获取',
                        passive={'type': 'gold_boost', 'value': 30},
                        combat_skill=('狐火', 20), combat_interval=4,
                        evolved_name='暗网狐', evolved_sprite_key='pet_fox_evo',
                        evolved_passive={'type': 'gold_boost', 'value': 60},
                        evolved_combat_skill=('幻影狐火', 35),
                        evolved_description='暗网中的幻影狐，金币获取翻倍'),
    'nano_bird': PetDef('nano_bird', '纳米鸟', 'pet_bird', '小巧的纳米机械鸟，提升经验获取',
                         passive={'type': 'exp_boost', 'value': 20},
                         combat_skill=('音波攻击', 18), combat_interval=3,
                         evolved_name='等离子鸟', evolved_sprite_key='pet_bird_evo',
                         evolved_passive={'type': 'exp_boost', 'value': 40},
                         evolved_combat_skill=('等离子风暴', 32),
                         evolved_description='等离子态的机械鸟，经验获取大幅提升'),
    'mecha_dog': PetDef('mecha_dog', '机甲犬', 'pet_dog', '忠诚的战斗犬，提升攻击力',
                          passive={'type': 'atk_boost', 'value': 5},
                          combat_skill=('撕咬', 25), combat_interval=2,
                          evolved_name='重装犬', evolved_sprite_key='pet_dog_evo',
                          evolved_passive={'type': 'atk_boost', 'value': 12},
                          evolved_combat_skill=('钢铁撕裂', 45),
                          evolved_description='重装甲的战斗犬，攻击力极强'),
    'ghost_jelly': PetDef('ghost_jelly', '幽灵水母', 'pet_jelly', '飘浮的能量水母，提升防御力',
                            passive={'type': 'def_boost', 'value': 4},
                            combat_skill=('电击触手', 16), combat_interval=3,
                            evolved_name='深渊水母', evolved_sprite_key='pet_jelly_evo',
                            evolved_passive={'type': 'def_boost', 'value': 9},
                            evolved_combat_skill=('深渊电击', 28),
                            evolved_description='深渊中的能量水母，防御力极高'),
}


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
    # 暗网三连Boss
    'firewall_guardian': EnemyDef("防火墙守卫", "firewall_guardian", 200, 25, 12, 150, 120,
                                   [("防火墙冲击", 28), ("数据封锁", 22)], weakness='hack', is_boss=True),
    'data_devourer': EnemyDef("数据吞噬者", "data_devourer", 300, 30, 10, 200, 180,
                                [("数据吞噬", 32), ("能量虹吸", 25)], weakness='emp', is_boss=True),
    'darknet_lord': EnemyDef("暗网之主", "darknet_lord", 400, 35, 15, 350, 300,
                               [("暗网风暴", 38), ("数据毁灭", 45), ("暗影打击", 30)], weakness='hack', is_boss=True),
}

ENCOUNTER_TABLE = {
    AREA_VILLAGE: [],
    AREA_NEON_STREET: [],
    AREA_BLACK_MARKET: [],
    AREA_HOME: [],
    AREA_FOREST: ['slime', 'slime', 'bat', 'bat', 'skeleton'],
    AREA_DUNGEON: ['skeleton', 'skeleton', 'bat', 'skeleton', 'dragon'],
    AREA_FACTORY: ['glitch_bot', 'glitch_bot', 'factory_guard', 'factory_guard', 'glitch_bot'],
    AREA_CYBERSPACE: ['cyber_virus', 'cyber_virus', 'data_ghost', 'data_ghost', 'cyber_virus'],
    AREA_TUNNEL: ['pipe_worm', 'pipe_worm', 'security_drone', 'pipe_worm', 'security_drone'],
}


