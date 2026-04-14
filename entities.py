"""游戏实体：物品、玩家、NPC、敌人 - 赛博朋克主题"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Tuple, Set
from constants import TILE
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_TUNNEL, AREA_BLACK_MARKET, AREA_HOME)


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
    # 暗网Boss奖励
    'quantum_blade': Item("量子之刃", "quantum_blade", "暗网之主的遗物，攻击力+20", "weapon", atk_bonus=20),
    # 芯片融合产物
    'nano_amplifier': Item("纳米增幅器", "nano_amplifier", "融合饰品，ATK+8 DEF+4", "accessory", atk_bonus=8, def_bonus=4),
    'virus_shield': Item("病毒护盾", "virus_shield", "融合护甲，DEF+12", "armor", def_bonus=12),
    'overclock_core': Item("超频核心", "overclock_core", "融合饰品，ATK+12", "accessory", atk_bonus=12),
    'life_spring': Item("生命之泉", "life_spring", "融合消耗品，全恢复HP和EN", "consumable", hp_restore=9999, mp_restore=9999),
    # 农场物品
    'fertilizer': Item("纳米肥料", "fertilizer", "加速当前作物2倍生长速度", "material"),
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

    def get_total_atk(self):
        bonus = sum(ITEMS_DB[v].atk_bonus for v in self.equipped.values() if v)
        # 技能树被动加成
        if 'atk_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['atk_t1'].effect['value']
        # 宠物加成
        pet_bonus = self.get_pet_bonuses()
        if pet_bonus.get('type') == 'atk_boost':
            bonus += pet_bonus['value']
        # 成就加成
        if 'zero_day' in self.achievements:
            bonus += 8
        if 'completionist' in self.achievements:
            bonus += 3
        if 'darknet_conqueror' in self.achievements:
            bonus += 5
        return self.stats.atk + bonus

    def get_total_def(self):
        bonus = sum(ITEMS_DB[v].def_bonus for v in self.equipped.values() if v)
        if 'def_t1' in self.unlocked_skills:
            bonus += SKILL_TREE['def_t1'].effect['value']
        # 宠物加成
        pet_bonus = self.get_pet_bonuses()
        if pet_bonus.get('type') == 'def_boost':
            bonus += pet_bonus['value']
        # 成就加成
        if 'iron_wall' in self.achievements:
            bonus += 6
        if 'completionist' in self.achievements:
            bonus += 3
        if 'darknet_conqueror' in self.achievements:
            bonus += 5
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
            'affection': self.affection,
            'romance_events_seen': {k: list(v) for k, v in self.romance_events_seen.items()},
            'partner': self.partner,
            'partner_hp': self.partner_hp,
            'partner_exp': self.partner_exp,
            'partner_level': self.partner_level,
            'farm_plots': [{'crop_id': p.crop_id, 'growth': p.growth, 'ready': p.ready,
                            'fertilized': p.fertilized}
                           for p in self.farm_plots],
            'farm_step_counter': self.farm_step_counter,
            'farm_level': self.farm_level,
            'pets_owned': self.pets_owned,
            'active_pet': self.active_pet,
            'pet_exp': self.pet_exp,
            'pet_levels': self.pet_levels,
            'pet_happiness': self.pet_happiness,
            'pet_play_cooldown': self.pet_play_cooldown,
            'active_meal': self.active_meal,
            'meal_buff_turns': self.meal_buff_turns,
            'expedition': self.expedition,
            'achievements': list(self.achievements),
            'achievement_counters': self.achievement_counters,
            'visited_areas': list(self.visited_areas),
            'darknet_cleared': self.darknet_cleared,
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
        self.affection = d.get('affection', {})
        self.romance_events_seen = {k: set(v) for k, v in d.get('romance_events_seen', {}).items()}
        self.partner = d.get('partner', None)
        self.partner_hp = d.get('partner_hp', 0)
        self.partner_exp = d.get('partner_exp', 0)
        self.partner_level = d.get('partner_level', 1)
        farm_data = d.get('farm_plots', [])
        self.farm_plots = [PlotState(p.get('crop_id'), p.get('growth', 0), p.get('ready', False),
                                      p.get('fertilized', False))
                           for p in farm_data]
        # 确保有足够地块
        self.farm_level = d.get('farm_level', 0)
        target_plots = 6 + self.farm_level * 2
        while len(self.farm_plots) < target_plots:
            self.farm_plots.append(PlotState())
        self.farm_step_counter = d.get('farm_step_counter', 0)
        self.pets_owned = d.get('pets_owned', [])
        self.active_pet = d.get('active_pet', None)
        self.pet_exp = d.get('pet_exp', {})
        self.pet_levels = d.get('pet_levels', {})
        self.pet_happiness = d.get('pet_happiness', {})
        self.pet_play_cooldown = d.get('pet_play_cooldown', {})
        self.active_meal = d.get('active_meal', None)
        self.meal_buff_turns = d.get('meal_buff_turns', 0)
        self.expedition = d.get('expedition', None)
        self.achievements = set(d.get('achievements', []))
        self.achievement_counters = d.get('achievement_counters', {})
        self.visited_areas = set(d.get('visited_areas', []))
        self.darknet_cleared = d.get('darknet_cleared', False)

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

    def get_affection(self, char_id: str) -> int:
        return self.affection.get(char_id, 0)

    def add_affection(self, char_id: str, amount: int) -> int:
        """增加好感度，返回新值。已有伴侣时不能对其他人增加"""
        if self.partner and self.partner != char_id:
            return self.get_affection(char_id)
        cur = self.affection.get(char_id, 0)
        new_val = min(100, cur + amount)
        self.affection[char_id] = new_val
        return new_val

    def check_romance_event(self, char_id: str) -> Optional[Tuple[int, str, str]]:
        """检查是否有新的剧情事件可触发，返回 (阈值, 描述, 奖励类型) 或 None"""
        rc = ROMANCE_CHARS.get(char_id)
        if not rc:
            return None
        aff = self.get_affection(char_id)
        seen = self.romance_events_seen.get(char_id, set())
        for threshold, (desc, reward) in sorted(rc.story_events.items()):
            if threshold <= aff and threshold not in seen:
                return (threshold, desc, reward)
        return None

    def mark_romance_event(self, char_id: str, threshold: int):
        if char_id not in self.romance_events_seen:
            self.romance_events_seen[char_id] = set()
        self.romance_events_seen[char_id].add(threshold)

    def commit_partner(self, char_id: str):
        """确定伴侣"""
        rc = ROMANCE_CHARS[char_id]
        self.partner = char_id
        self.partner_hp = rc.combat_hp

    def get_partner_def(self) -> Optional[RomanceChar]:
        if self.partner:
            return ROMANCE_CHARS.get(self.partner)
        return None

    def init_farm(self):
        """初始化农场（如果还没有）"""
        target_plots = 6 + self.farm_level * 2  # Lv0:6, Lv1:8, Lv2:10, Lv3:12
        if not self.farm_plots:
            self.farm_plots = [PlotState() for _ in range(target_plots)]
        while len(self.farm_plots) < target_plots:
            self.farm_plots.append(PlotState())

    def farm_tick(self):
        """每走一定步数调用，推进作物生长"""
        self.farm_step_counter += 1
        if self.farm_step_counter >= 10:  # 每10步生长一次
            self.farm_step_counter = 0
            speed_mult = 1.0 + self.farm_level * 0.2  # Lv0:1x, Lv1:1.2x, Lv2:1.4x, Lv3:1.6x
            for plot in self.farm_plots:
                if plot.crop_id and not plot.ready:
                    crop = CROPS_DB.get(plot.crop_id)
                    if crop:
                        grow = speed_mult
                        if plot.fertilized:
                            grow *= 2
                        plot.growth += grow
                        if plot.growth >= crop.grow_time:
                            plot.ready = True

    def get_pet_bonuses(self) -> Dict:
        """获取当前宠物的被动加成（考虑进化和幸福度）"""
        if not self.active_pet:
            return {}
        pet = PETS_DB.get(self.active_pet)
        if not pet:
            return {}
        happiness = self.pet_happiness.get(self.active_pet, 50)
        if happiness < 20:
            return {}  # 幸福度过低，被动禁用
        if self.is_pet_evolved(self.active_pet):
            passive = dict(pet.evolved_passive)
        else:
            passive = dict(pet.passive)
        if happiness > 80:
            passive['value'] = int(passive.get('value', 0) * 1.5)
        return passive

    def add_pet_exp(self, pet_id: str, amount: int) -> Optional[int]:
        """给宠物加经验，返回新等级（如果升级了）否则None"""
        if pet_id not in self.pets_owned:
            return None
        self.pet_exp[pet_id] = self.pet_exp.get(pet_id, 0) + amount
        old_level = self.pet_levels.get(pet_id, 1)
        # 每级需要 level * 50 经验
        leveled = False
        while self.pet_exp[pet_id] >= self.get_pet_level(pet_id) * 50:
            self.pet_exp[pet_id] -= self.get_pet_level(pet_id) * 50
            self.pet_levels[pet_id] = self.pet_levels.get(pet_id, 1) + 1
            leveled = True
        return self.pet_levels.get(pet_id, 1) if leveled else None

    def get_pet_level(self, pet_id: str) -> int:
        return self.pet_levels.get(pet_id, 1)

    def is_pet_evolved(self, pet_id: str) -> bool:
        return self.get_pet_level(pet_id) >= 5

    def add_partner_exp(self, amount: int) -> Optional[int]:
        """给伴侣增加经验，返回新等级（如果升级了）否则None"""
        if not self.partner:
            return None
        self.partner_exp += amount
        leveled = False
        while self.partner_exp >= self.partner_level * 40:
            self.partner_exp -= self.partner_level * 40
            self.partner_level += 1
            leveled = True
        return self.partner_level if leveled else None

    def get_partner_combat_stats(self) -> Optional[Tuple[int, int, int]]:
        """返回伴侣成长后的 (hp, atk, def)"""
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


