"""
赛博入侵 - Cyber Breach
主游戏模块：GameState, Game 类及入口
"""
import pygame
import sys
import math
import random
import time
import json
import os
import traceback
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple

from constants import *
from assets import Assets
from particles import ParticleSystem
from game_map import (GameMap, AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON,
                      AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE,
                      AREA_HOUSE_V1, AREA_HOUSE_V2, AREA_HOUSE_V3,
                      AREA_HOUSE_N1, AREA_HOUSE_N2, AREA_HOUSE_N3,
                      AREA_TUNNEL, AREA_BLACK_MARKET,
                      INDOOR_AREAS)
from entities import (Item, ITEMS_DB, PlayerStats, Player, NPC, EnemyDef, ENEMY_DEFS, ENCOUNTER_TABLE,
                      SKILL_TREE, StatusEffect)
from combat import Combat, CombatState
from dialogue import DialogueBox

# ============================================================
# 主游戏类
# ============================================================
class GameState(Enum):
    TITLE = auto()
    EXPLORE = auto()
    COMBAT = auto()
    MENU = auto()
    GAME_OVER = auto()
    ENDING = auto()
    SKILL_TREE = auto()
    UPGRADE_SHOP = auto()

class Game:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption("赛博入侵 - Cyber Breach")
        self.clock = pygame.time.Clock()
        self.assets = Assets()
        self.game_map = GameMap()
        self.player = Player(20, 16)
        self.camera_x = 0.0
        self.camera_y = 0.0
        self.state = GameState.TITLE
        self.combat: Optional[Combat] = None
        self.dialogue = DialogueBox(self.assets)
        self.particles = ParticleSystem()
        self.tick = 0
        self.encounter_steps = 0
        self.menu_index = 0
        self.inv_index = 0
        self.show_inventory = False
        self.title_blink = 0
        self.title_index = 0
        self.transition_alpha = 0
        self.transitioning = False
        self.transition_target = None
        self.chests_opened = set()
        self.message_queue: List[Tuple[str, int]] = []
        # 技能树UI
        self.skill_tree_branch = 0  # 0=attack, 1=defense, 2=hack
        self.skill_tree_tier = 0
        # 升级商店
        self.upgrade_index = 0
        # 通关动画
        self.ending_timer = 0
        self.ending_particles = ParticleSystem()
        # Boss触发点
        self.boss_positions = {
            (AREA_FACTORY, 35, 30): 'mad_overseer',
            (AREA_DUNGEON, 15, 12): 'ai_core_boss',
            (AREA_CYBERSPACE, 20, 20): 'quantum_overlord',
        }

        # NPC 定义（含主线对话分支）
        self.npcs = [
            NPC(18, 12, 'elder', '城市管理员',
                ["欢迎来到数据港。", "东边的废墟荒地有大量失控机器人，注意安全。"],
                AREA_VILLAGE,
                quest_dialogues={
                    0: ["欢迎来到数据港，新来的。", "这个世界正在崩溃...机器人失控，数据异常。",
                        "你看起来有点本事。去废墟荒地调查一下吧。",
                        "（主线任务：前往废墟荒地调查）"],
                    1: ["你回来了！工厂深处有个失控监工。", "击败它，也许能找到通往旧数据中心的密道。"],
                    2: ["密道已经打通了？太好了！", "旧数据中心里封存着觉醒的AI核心，那才是真正的威胁。"],
                    3: ["AI核心被击败了！但网络空间的量子霸主还在...", "去网络空间找AI先知。"],
                    4: ["最终决战...一切都靠你了。", "击败量子霸主，拯救这个世界！"],
                    5: ["你做到了！世界恢复了秩序。", "英雄，自由探索吧。"],
                }),
            NPC(25, 14, 'merchant', '数据贩子',
                ["嘿，需要点装备吗？看看货架。"],
                AREA_VILLAGE,
                shop_items=[('hp_potion', 20), ('mp_potion', 30), ('iron_sword', 100), ('shield', 80)]),
            NPC(15, 18, 'guard', '安保机器人',
                ["区域安全等级：正常。", "前往废墟荒地前，建议携带足够的纳米修复剂。", "按J键交互，方向键移动。按ESC打开菜单。"],
                AREA_VILLAGE),
            NPC(10, 10, 'witch', '黑客',
                ["嘿嘿...想提升战斗力？", "战斗中使用技能可以造成更多伤害。", "EMP脉冲对付机械敌人特别有效~"],
                AREA_FOREST),
            # 霓虹商业街 NPC
            NPC(10, 14, 'arms_dealer', '军火商',
                ["最新型号的武器，都在这了。"],
                AREA_NEON_STREET,
                shop_items=[('iron_sword', 100), ('emp_grenade', 180), ('shield', 80), ('hp_potion', 15)]),
            NPC(35, 14, 'info_broker', '情报商',
                ["需要情报？我什么都知道。", "废弃工厂里有重型守卫机器人，小心。", "网络空间的量子霸主...那可是最危险的存在。"],
                AREA_NEON_STREET,
                quest_dialogues={
                    1: ["工厂深处有个失控监工，它弱EMP攻击。", "击败它就能找到密道入口。"],
                    3: ["量子霸主在网络空间中央节点。", "它弱黑客类攻击，准备好再去。"],
                }),
            # 废弃工厂 NPC
            NPC(22, 5, 'factory_worker', '工厂工人',
                ["这里以前是自动化工厂...", "机器人失控后就没人敢来了。", "深处好像还有更强的守卫在巡逻。"],
                AREA_FACTORY,
                quest_dialogues={
                    1: ["你是来调查的？小心深处的失控监工！", "它在工厂最深处附近巡逻。"],
                    2: ["你击败了监工？太厉害了！", "密道入口就在工厂右侧边缘。"],
                }),
            # 网络空间 NPC
            NPC(20, 5, 'ai_prophet', 'AI先知',
                ["你来了...我预见到了这一刻。", "量子霸主在中央节点等着你。", "只有击败它，网络空间才能恢复秩序。"],
                AREA_CYBERSPACE,
                quest_dialogues={
                    3: ["你来了...我预见到了这一刻。", "量子霸主在中央节点(20,20)等着你。",
                        "准备好了就去吧，这是最终决战。"],
                    5: ["秩序恢复了...感谢你，赛博行者。"],
                }),
            # 室内NPC - 数据港·维修工坊 (V1)
            NPC(6, 4, 'guard', '维修技师',
                ["需要修理装备？可惜我现在缺关键零件。",
                 "废墟荒地的机器人身上有精密齿轮，能帮我搞几个来吗？",
                 "隔壁的数据分析师说网络空间的数据异常...我觉得跟工厂失控有关。",
                 "你要是去工厂，帮我问问那个工人，他以前是我徒弟。"],
                AREA_HOUSE_V1),
            NPC(18, 6, 'factory_worker', '学徒机械师',
                ["师父让我在这看店，他自己整天研究那些破零件。",
                 "听说霓虹街的改装师有一批新货，比师父的手艺还好...别告诉他我说的。",
                 "工厂那边的工人是我老同事，他说深处有条密道，但我没敢去验证。"],
                AREA_HOUSE_V1),
            # 数据港·分析室 (V2)
            NPC(12, 4, 'witch', '数据分析师',
                ["我一直在分析网络空间的数据流，发现了异常波动。",
                 "维修工坊的技师也注意到了——工厂的机器人行为模式变了。",
                 "退休黑客老陈说这跟十年前的'大崩溃'事件很像...",
                 "你去找他聊聊吧，他住在街尾那栋房子里。多带些纳米修复剂。"],
                AREA_HOUSE_V2),
            NPC(4, 8, 'ai_prophet', '实习分析员',
                ["前辈教了我很多数据分析的技巧。",
                 "她说网络空间的防火墙最近异常强化，好像有什么东西在里面觉醒了。",
                 "霓虹街酒吧的酒保消息灵通，你可以去打听打听。"],
                AREA_HOUSE_V2),
            # 数据港·退休黑客书房 (V3)
            NPC(14, 9, 'elder', '退休黑客·老陈',
                ["年轻人，分析师让你来找我的吧？",
                 "十年前的'大崩溃'...旧数据中心的AI核心失控，整个网络差点瘫痪。",
                 "我当年亲手封印了它，但最近封印似乎在松动。",
                 "工厂失控、数据异常...都是前兆。你得去旧数据中心看看。",
                 "记住，技能比蛮力重要。霓虹街那个线人知道一些AI核心的弱点。"],
                AREA_HOUSE_V3),
            NPC(18, 5, 'witch', '老陈的孙女',
                ["爷爷总是讲当年的故事，我都听腻了...但最近他变得很严肃。",
                 "他说'大崩溃'要重演了，让我别去网络空间。",
                 "维修工坊的技师叔叔说会保护我们的，但我还是有点害怕。"],
                AREA_HOUSE_V3),
            # 霓虹街·酒吧 (N1)
            NPC(8, 7, 'merchant', '酒保·阿杰',
                ["来一杯？这里的消息比酒还烈。",
                 "最近来了不少从工厂逃出来的人，说机器人越来越疯狂了。",
                 "隔壁改装店的老板娘跟我说，有人在大量收购EMP手雷...不知道在搞什么。",
                 "对了，数据港那个分析师托我告诉来这儿的冒险者——网络空间的数据流在加速。"],
                AREA_HOUSE_N1,
                shop_items=[('hp_potion', 15), ('mp_potion', 25), ('elixir', 200)]),
            NPC(22, 5, 'guard', '醉酒佣兵',
                ["嗝...我刚从废墟荒地回来，差点没命。",
                 "那些机器人比以前强多了...维修技师说是因为工厂的控制信号变了。",
                 "你要去冒险的话，先去改装店升级装备，老板娘人不错。"],
                AREA_HOUSE_N1),
            NPC(12, 14, 'witch', '驻唱歌手',
                ["♪ 霓虹灯下的影子...数据流中的幽灵... ♪",
                 "别看我只是个歌手，我也听到不少消息。",
                 "线人那边最近很忙，好像在调查什么大事。你可以去找他。"],
                AREA_HOUSE_N1),
            # 霓虹街·改装店 (N2)
            NPC(10, 4, 'arms_dealer', '改装师·小薇',
                ["想升级装备？看看这些，都是最新的。",
                 "最近EMP手雷卖得特别好，酒吧的阿杰说有人在囤货。",
                 "维修工坊的技师手艺不错，但他缺零件。你要是能帮他搞到，他能做出更好的东西。",
                 "对了，线人说量子霸主怕EMP脉冲，你可以多备几个。"],
                AREA_HOUSE_N2,
                shop_items=[('emp_grenade', 150), ('quantum_chip', 300), ('iron_sword', 80), ('shield', 70)]),
            NPC(4, 15, 'elder', '老顾客',
                ["小薇的手艺是这条街最好的，没有之一。",
                 "我上次买的护盾在废墟荒地救了我一命。",
                 "你要是去旧数据中心，一定要带上EMP手雷。那个退休黑客老陈也是这么说的。"],
                AREA_HOUSE_N2),
            # 霓虹街·线人密室 (N3)
            NPC(4, 5, 'info_broker', '线人·影子',
                ["嘘...关上门再说。",
                 "废弃工厂深处有条隐藏通道，通向旧数据中心的后门。",
                 "网络空间的量子霸主有个致命弱点——EMP脉冲能暂时瘫痪它的护盾。",
                 "改装店的小薇那里有EMP手雷卖，多买几个。",
                 "退休黑客老陈十年前封印过AI核心，他的经验对你有用。去找他聊聊。"],
                AREA_HOUSE_N3),
            NPC(14, 5, 'merchant', '神秘客商',
                ["我从很远的地方来，带了些稀有货物。",
                 "这些量子芯片是网络空间的硬通货，在那里能派上大用场。",
                 "酒吧的阿杰是我老朋友了，他帮我打听本地的行情。"],
                AREA_HOUSE_N3,
                shop_items=[('quantum_chip', 250), ('elixir', 180), ('magic_ring', 500)]),
            NPC(14, 14, 'factory_worker', '逃亡工人',
                ["我...我是从工厂逃出来的。",
                 "那里的机器人全疯了，好像被什么东西控制了。",
                 "维修工坊的技师以前是我师兄，他一直想搞清楚工厂出了什么问题。",
                 "影子说工厂深处有密道...我不敢回去了，但你可以试试。"],
                AREA_HOUSE_N3),
            # 黑市NPC
            NPC(7, 4, 'arms_dealer', '黑市军火商',
                ["这里的货，外面可买不到。"],
                AREA_BLACK_MARKET,
                shop_items=[('plasma_rifle', 300), ('nano_armor', 250), ('hacker_gloves', 200),
                            ('elixir', 150), ('antivirus', 50)]),
            NPC(17, 4, 'info_broker', '信息贩子',
                ["情报就是力量。", "工厂Boss弱EMP，AI核心弱黑客攻击。",
                 "量子霸主·真身是最强的存在，做好万全准备。"],
                AREA_BLACK_MARKET),
        ]

        # 宝箱位置
        self.chest_positions = {
            (AREA_VILLAGE, 30, 10): ('iron_sword', 1),
            (AREA_FOREST, 40, 20): ('magic_ring', 1),
            (AREA_DUNGEON, 22, 18): ('hp_potion', 5),
            (AREA_DUNGEON, 6, 4): ('mp_potion', 3),
            (AREA_NEON_STREET, 6, 5): ('quantum_chip', 1),
            (AREA_NEON_STREET, 36, 22): ('elixir', 1),
            (AREA_FACTORY, 8, 5): ('emp_grenade', 1),
            (AREA_FACTORY, 35, 30): ('hp_potion', 5),
            (AREA_CYBERSPACE, 6, 5): ('quantum_chip', 1),
            (AREA_CYBERSPACE, 33, 5): ('elixir', 2),
            (AREA_CYBERSPACE, 6, 33): ('mp_potion', 5),
            # 室内宝箱
            (AREA_HOUSE_V1, 24, 4): ('hp_potion', 3),
            (AREA_HOUSE_V1, 3, 12): ('iron_sword', 1),
            (AREA_HOUSE_V2, 26, 4): ('mp_potion', 3),
            (AREA_HOUSE_V2, 16, 14): ('quantum_chip', 1),
            (AREA_HOUSE_V3, 6, 8): ('magic_ring', 1),
            (AREA_HOUSE_V3, 24, 6): ('elixir', 1),
            (AREA_HOUSE_N1, 24, 12): ('elixir', 2),
            (AREA_HOUSE_N2, 22, 14): ('emp_grenade', 2),
            (AREA_HOUSE_N2, 6, 4): ('shield', 1),
            (AREA_HOUSE_N3, 24, 4): ('quantum_chip', 2),
            (AREA_HOUSE_N3, 8, 14): ('emp_grenade', 3),
            # 新区域宝箱
            (AREA_TUNNEL, 10, 5): ('hp_potion', 5),
            (AREA_TUNNEL, 26, 7): ('antivirus', 2),
            (AREA_TUNNEL, 20, 18): ('emp_grenade', 1),
            (AREA_BLACK_MARKET, 12, 10): ('hacker_gloves', 1),
            # 工厂隐藏宝箱（支线：失踪工人证件）
            (AREA_FACTORY, 5, 28): ('worker_id', 1),
        }

        # 隐藏宝箱（随机位置，不可见）
        self.hidden_chests = {}
        self.hidden_chests_opened = set()
        self._generate_hidden_chests()

        # 幽灵黑客（废墟荒地中随机位置）
        self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
        self.ghost_merchant_npc = NPC(
            self.ghost_merchant_pos[0], self.ghost_merchant_pos[1],
            'ghost_merchant', '幽灵黑客',
            ["嘿嘿...你能看到我的信号？", "我有些稀有的好东西...要看看吗？"],
            AREA_FOREST,
            shop_items=[('elixir', 200), ('lucky_coin', 150), ('hp_potion', 10), ('mp_potion', 15)],
        )

        # 随机事件步数计数
        self.random_event_steps = 0

    def run(self):
        running = True
        while running:
            dt = self.clock.tick(FPS)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                self._handle_event(event)
            self._update()
            self._draw()
            pygame.display.flip()
        pygame.quit()
        sys.exit()

    def _handle_event(self, event):
        if self.state == GameState.TITLE:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.title_index = (self.title_index - 1) % 2
                elif event.key == pygame.K_DOWN:
                    self.title_index = (self.title_index + 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    if self.title_index == 0:  # 新游戏
                        self.state = GameState.EXPLORE
                    elif self.title_index == 1 and os.path.exists(SAVE_PATH):  # 读取存档
                        self._load_game()
        elif self.state == GameState.EXPLORE:
            if self.dialogue.active:
                self.dialogue.handle_input(event, self.player)
                return
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.state = GameState.MENU
                    self.menu_index = 0
                    self.show_inventory = False
                elif event.key == pygame.K_j:
                    self._interact()
        elif self.state == GameState.COMBAT:
            if self.combat:
                still_fighting = self.combat.handle_input(event)
                if not still_fighting:
                    self._on_combat_end()
                    if self.combat and self.combat.state == CombatState.DEFEAT:
                        self.state = GameState.GAME_OVER
                    elif self.state != GameState.ENDING:
                        self.state = GameState.EXPLORE
                    self.combat = None
        elif self.state == GameState.MENU:
            self._handle_menu_event(event)
        elif self.state == GameState.SKILL_TREE:
            self._handle_skill_tree_event(event)
        elif self.state == GameState.UPGRADE_SHOP:
            self._handle_upgrade_shop_event(event)
        elif self.state == GameState.GAME_OVER:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_j):
                self._restart()
        elif self.state == GameState.ENDING:
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_j):
                if self.ending_timer > 180:
                    self.state = GameState.EXPLORE
                    self.message_queue.append(("通关！自由探索模式已解锁。", 180))

    def _handle_menu_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if self.show_inventory:
            items = self.player.inventory
            if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
                self.show_inventory = False
            elif items:
                if event.key == pygame.K_UP:
                    self.inv_index = (self.inv_index - 1) % len(items)
                elif event.key == pygame.K_DOWN:
                    self.inv_index = (self.inv_index + 1) % len(items)
                elif event.key in (pygame.K_RETURN, pygame.K_j):
                    key, cnt = items[self.inv_index]
                    self.player.use_item(key)
                    if self.inv_index >= len(self.player.inventory):
                        self.inv_index = max(0, len(self.player.inventory) - 1)
            return

        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            self.state = GameState.EXPLORE
        elif event.key == pygame.K_UP:
            self.menu_index = (self.menu_index - 1) % 6
        elif event.key == pygame.K_DOWN:
            self.menu_index = (self.menu_index + 1) % 6
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            if self.menu_index == 0:  # 物品
                self.show_inventory = True
                self.inv_index = 0
            elif self.menu_index == 1:  # 装备
                pass
            elif self.menu_index == 2:  # 技能树
                self.state = GameState.SKILL_TREE
                self.skill_tree_branch = 0
                self.skill_tree_tier = 0
            elif self.menu_index == 3:  # 保存
                self._save_game()
                self.state = GameState.EXPLORE
            elif self.menu_index == 4:  # 读取
                self._load_game()
            elif self.menu_index == 5:  # 返回
                self.state = GameState.EXPLORE

    def _interact(self):
        """与面前的NPC/物体交互"""
        dx, dy = 0, 0
        if self.player.direction == 'up': dy = -1
        elif self.player.direction == 'down': dy = 1
        elif self.player.direction == 'left': dx = -1
        elif self.player.direction == 'right': dx = 1

        target_tx = self.player.tx + dx
        target_ty = self.player.ty + dy

        # 检查面前一格和当前站的格子
        check_positions = [(target_tx, target_ty), (self.player.tx, self.player.ty)]

        # 幽灵商人
        if self.player.area == AREA_FOREST:
            for cx, cy in check_positions:
                if self.ghost_merchant_npc.x == cx and self.ghost_merchant_npc.y == cy:
                    self.dialogue.start(self.ghost_merchant_npc, self.player.quest_stage)
                    return

        # NPC
        for npc in self.npcs:
            if npc.area == self.player.area:
                for cx, cy in check_positions:
                    if npc.x == cx and npc.y == cy:
                        self._handle_npc_interact(npc)
                        return

        # 宝箱
        chest_key = (self.player.area, target_tx, target_ty)
        if chest_key in self.chest_positions and chest_key not in self.chests_opened:
            item_key, count = self.chest_positions[chest_key]
            self.player.add_item(item_key, count)
            self.chests_opened.add(chest_key)
            item = ITEMS_DB[item_key]
            self.message_queue.append((f"获得 {item.name} x{count}！", 120))
            self.particles.emit(target_tx * TILE + 16, target_ty * TILE + 16, 15, C_GOLD, 2, 40, 3, 'magic')
            return

        # 隐藏宝箱（检测玩家当前位置和面前位置）
        for check_key in [chest_key, (self.player.area, self.player.tx, self.player.ty)]:
            if check_key in self.hidden_chests and check_key not in self.hidden_chests_opened:
                item_key, count = self.hidden_chests[check_key]
                self.player.add_item(item_key, count)
                self.hidden_chests_opened.add(check_key)
                item = ITEMS_DB[item_key]
                self.message_queue.append((f"[!] 发现隐藏终端! 获得 {item.name} x{count}!", 150))
                px = check_key[1] * TILE + 16
                py = check_key[2] * TILE + 16
                self.particles.emit(px, py, 25, (255, 200, 100), 3, 50, 3, 'magic')
                self.particles.emit(px, py, 15, (0, 255, 200), 2, 40, 2, 'firefly')
                return

    def _handle_npc_interact(self, npc):
        """处理NPC交互，含任务逻辑"""
        p = self.player
        # 主线：城市管理员 - Stage 0 → 1
        if npc.name == '城市管理员' and p.quest_stage == 0:
            p.quest_stage = 1
            self.message_queue.append(("【主线】前往废弃工厂，击败失控监工！", 180))
        # 主线：AI先知 - Stage 3 → 4
        elif npc.name == 'AI先知' and p.quest_stage == 3:
            p.quest_stage = 4
            self.message_queue.append(("【主线】前往网络空间中央(20,20)，击败量子霸主·真身！", 180))

        # 支线：维修技师 - 零件收集
        if npc.name == '维修技师':
            sq = p.side_quests.get('gear_collect', 0)
            if sq == 0:
                p.side_quests['gear_collect'] = 1
                p.quest_counters['gear_collect'] = p.item_count('precision_gear')
                self.message_queue.append(("【支线】零件收集：收集3个精密齿轮", 150))
            elif sq == 1 and p.item_count('precision_gear') >= 3:
                p.remove_item('precision_gear', 3)
                p.side_quests['gear_collect'] = 2
                p.quest_flags['upgrade_unlocked'] = True
                self.message_queue.append(("【支线完成】零件收集！解锁装备升级服务！", 180))

        # 支线：数据分析师 - 数据采样
        if npc.name == '数据分析师':
            sq = p.side_quests.get('data_collect', 0)
            if sq == 0:
                p.side_quests['data_collect'] = 1
                self.message_queue.append(("【支线】数据采样：收集2个数据样本", 150))
            elif sq == 1 and p.item_count('data_sample') >= 2:
                p.remove_item('data_sample', 2)
                p.side_quests['data_collect'] = 2
                p.stats.exp += 80
                p.add_item('quantum_chip')
                self.message_queue.append(("【支线完成】数据采样！获得80EXP+量子芯片！", 180))

        # 支线：醉酒佣兵 - 佣兵委托
        if npc.name == '醉酒佣兵':
            sq = p.side_quests.get('merc_hunt', 0)
            if sq == 0:
                p.side_quests['merc_hunt'] = 1
                p.quest_counters['merc_hunt'] = 0
                self.message_queue.append(("【支线】佣兵委托：击败10个敌人", 150))
            elif sq == 1 and p.quest_counters.get('merc_hunt', 0) >= 10:
                p.side_quests['merc_hunt'] = 2
                p.stats.gold += 300
                self.message_queue.append(("【支线完成】佣兵委托！获得300信用点！", 180))

        # 支线：逃亡工人 - 失踪工人
        if npc.name == '逃亡工人':
            sq = p.side_quests.get('missing_worker', 0)
            if sq == 0:
                p.side_quests['missing_worker'] = 1
                self.message_queue.append(("【支线】失踪工人：在工厂找到工人证件", 150))
            elif sq == 1 and p.has_item('worker_id'):
                p.remove_item('worker_id')
                p.side_quests['missing_worker'] = 2
                p.stats.exp += 60
                p.add_item('hp_potion', 5)
                self.message_queue.append(("【支线完成】失踪工人！获得60EXP+纳米修复剂x5！", 180))

        # 支线：线人·影子 - 黑市通行证
        if npc.name == '线人·影子':
            sq = p.side_quests.get('black_market_pass', 0)
            if sq == 0:
                p.side_quests['black_market_pass'] = 1
                self.message_queue.append(("【支线】黑市通行证：收集3个加密数据", 150))
            elif sq == 1 and p.item_count('encrypted_data') >= 3:
                p.remove_item('encrypted_data', 3)
                p.side_quests['black_market_pass'] = 2
                p.quest_flags['black_market_open'] = True
                self.message_queue.append(("【支线完成】黑市通行证！霓虹街黑市入口已解锁！", 180))

        self.dialogue.start(npc, p.quest_stage)

    def _check_boss_trigger(self):
        """检查是否踩到Boss触发点"""
        p = self.player
        key = (p.area, p.tx, p.ty)
        boss_key = self.boss_positions.get(key)
        if not boss_key:
            return
        # 检查门控条件
        if boss_key == 'mad_overseer' and p.quest_stage < 1:
            return
        if boss_key == 'ai_core_boss' and p.quest_stage < 2:
            return
        if boss_key == 'quantum_overlord' and p.quest_stage < 4:
            return
        # 已击败不再触发
        if p.boss_defeated.get(boss_key):
            return
        # 触发Boss战
        self.combat = Combat(p, boss_key, self.assets)
        self.state = GameState.COMBAT
        self.message_queue.append((f"【Boss战】{ENEMY_DEFS[boss_key].name}出现了！", 120))

    def _on_combat_end(self):
        """战斗结束后的处理"""
        if not self.combat:
            return
        p = self.player
        # Boss击败处理
        if self.combat.state == CombatState.VICTORY and self.combat.is_boss:
            boss_key = self.combat.enemy_key
            p.boss_defeated[boss_key] = True
            if boss_key == 'mad_overseer' and p.quest_stage == 1:
                p.quest_stage = 2
                self.message_queue.append(("【主线】失控监工被击败！地下通道已开启！", 180))
            elif boss_key == 'ai_core_boss' and p.quest_stage == 2:
                p.quest_stage = 3
                self.message_queue.append(("【主线】觉醒AI核心被击败！前往网络空间！", 180))
            elif boss_key == 'quantum_overlord' and p.quest_stage == 4:
                p.quest_stage = 5
                self.state = GameState.ENDING
                self.ending_timer = 0
                return

        # 支线：佣兵委托计数
        if self.combat.state == CombatState.VICTORY:
            if p.side_quests.get('merc_hunt') == 1:
                p.quest_counters['merc_hunt'] = p.quest_counters.get('merc_hunt', 0) + 1
                cnt = p.quest_counters['merc_hunt']
                if cnt <= 10:
                    self.message_queue.append((f"佣兵委托进度: {cnt}/10", 60))

    def _update(self):
        self.tick += 1

        if self.state == GameState.EXPLORE:
            self.dialogue.update()
            if not self.dialogue.active:
                self._update_player_movement()
                self._check_boss_trigger()
            self._update_camera()
            self._update_ambient_particles()
            self.particles.update()
            # 消息队列
            if self.message_queue:
                self.message_queue[0] = (self.message_queue[0][0], self.message_queue[0][1] - 1)
                if self.message_queue[0][1] <= 0:
                    self.message_queue.pop(0)

        elif self.state == GameState.COMBAT:
            if self.combat:
                self.combat.update()

        elif self.state == GameState.TITLE:
            self.title_blink += 1

        elif self.state == GameState.ENDING:
            self.ending_timer += 1
            self.ending_particles.update()
            if self.ending_timer % 3 == 0:
                x = random.randint(100, SCREEN_W - 100)
                y = random.randint(100, SCREEN_H - 100)
                c = random.choice([(0, 255, 200), (255, 50, 150), (180, 60, 255), (0, 255, 100)])
                self.ending_particles.emit(x, y, 3, c, 1.5, 80, 3, 'magic')

    def _update_player_movement(self):
        keys = pygame.key.get_pressed()
        dx, dy = 0, 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx += 1
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy -= 1
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy += 1

        # 朝向取最后变化的轴方向
        if dx != 0 or dy != 0:
            if abs(dx) >= abs(dy):
                self.player.direction = 'left' if dx < 0 else 'right'
            else:
                self.player.direction = 'up' if dy < 0 else 'down'

        self.player.moving = dx != 0 or dy != 0

        if self.player.moving:
            # Shift跑步
            running = keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT]
            spd = self.player.run_speed if running else self.player.speed
            # 斜向移动时归一化，保持速度一致
            if dx != 0 and dy != 0:
                factor = 0.7071  # 1/sqrt(2)
            else:
                factor = 1.0
            mx = dx * spd * factor
            my = dy * spd * factor
            nx = self.player.x + mx
            ny = self.player.y + my
            ntx = int(nx + TILE//2) // TILE
            nty = int(ny + TILE//2) // TILE

            # 碰撞检测
            can_move_x = self.game_map.is_walkable(self.player.area, int((nx + TILE//2) // TILE), self.player.ty)
            can_move_y = self.game_map.is_walkable(self.player.area, self.player.tx, int((ny + TILE//2) // TILE))

            if can_move_x and dx != 0:
                self.player.x = nx
            if can_move_y and dy != 0:
                self.player.y = ny

            self.player.tx = int((self.player.x + TILE//2) // TILE)
            self.player.ty = int((self.player.y + TILE//2) // TILE)

            # 动画（跑步时加快）
            anim_speed = 4 if running else 8
            self.player.anim_timer += 1
            if self.player.anim_timer >= anim_speed:
                self.player.anim_timer = 0
                self.player.anim_frame = (self.player.anim_frame + 1) % 4

            # 区域转换
            trans = self.game_map.check_transition(self.player.area, self.player.tx, self.player.ty)
            if trans:
                target_area, tx, ty = trans
                # 门控检查
                blocked = False
                if target_area == AREA_TUNNEL and self.player.quest_stage < 2:
                    self.message_queue.append(("需要先击败工厂Boss才能进入地下通道。", 120))
                    blocked = True
                elif target_area == AREA_BLACK_MARKET:
                    if not self.player.quest_flags.get('black_market_open') and self.player.quest_stage < 1:
                        self.message_queue.append(("这里有一扇隐藏的门...需要通行证。", 120))
                        blocked = True
                if not blocked:
                    self.player.area = target_area
                    self.player.x = float(tx * TILE)
                    self.player.y = float(ty * TILE)
                    self.player.tx = tx
                    self.player.ty = ty
                    self.encounter_steps = 0
                    # 进入森林时重新随机幽灵商人位置
                    if target_area == AREA_FOREST:
                        self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
                        self.ghost_merchant_npc.x = self.ghost_merchant_pos[0]
                        self.ghost_merchant_npc.y = self.ghost_merchant_pos[1]

            # 随机遇敌（室内安全）
            if self.player.area not in INDOOR_AREAS:
                self.encounter_steps += 1
                encounter_list = ENCOUNTER_TABLE.get(self.player.area, [])
                if encounter_list and self.encounter_steps > 30:
                    if random.random() < 0.004:
                        # 1% 概率遇到金色史莱姆
                        if random.random() < 0.01:
                            enemy = 'golden_slime'
                            self.message_queue.append(("[!] 稀有敌人出现了!", 90))
                        else:
                            enemy = random.choice(encounter_list)
                        self.combat = Combat(self.player, enemy, self.assets)
                        self.state = GameState.COMBAT
                        self.encounter_steps = 0

            # 随机事件
            if self.player.area not in INDOOR_AREAS:
                self.random_event_steps += 1
            if self.random_event_steps > 50 and random.random() < 0.003:
                self.random_event_steps = 0
                self._trigger_random_event()

    def _trigger_random_event(self):
        """走路时小概率触发的随机事件"""
        px = self.player.x + TILE // 2
        py = self.player.y + TILE // 2
        event = random.choice(['gold', 'potion', 'trap', 'blessing'])
        if event == 'gold':
            amount = random.randint(5, 20)
            self.player.stats.gold += amount
            self.message_queue.append((f"你在地上发现了{amount}信用点！", 120))
            self.particles.emit(px, py, 10, C_GOLD, 1.5, 30, 2, 'magic')
        elif event == 'potion':
            self.player.add_item('hp_potion')
            self.message_queue.append(("废墟中发现了一瓶纳米修复剂！", 120))
            self.particles.emit(px, py, 8, C_GREEN, 1.5, 30, 2, 'magic')
        elif event == 'trap':
            dmg = random.randint(5, 15)
            self.player.stats.hp = max(1, self.player.stats.hp - dmg)
            self.message_queue.append((f"触发了安全陷阱！受到{dmg}点伤害！", 120))
            self.particles.emit(px, py, 12, C_RED, 2, 25, 2)
        elif event == 'blessing':
            heal_hp = random.randint(10, 25)
            heal_mp = random.randint(5, 15)
            self.player.stats.hp = min(self.player.stats.max_hp, self.player.stats.hp + heal_hp)
            self.player.stats.mp = min(self.player.stats.max_mp, self.player.stats.mp + heal_mp)
            self.message_queue.append((f"接入修复节点！HP+{heal_hp} EN+{heal_mp}", 120))
            self.particles.emit(px, py, 15, (200, 200, 255), 2, 40, 3, 'magic')

    def _update_camera(self):
        target_x = self.player.x - SCREEN_W // 2 + TILE // 2
        target_y = self.player.y - SCREEN_H // 2 + TILE // 2
        mw = self.game_map.map_w.get(self.player.area, 40) * TILE
        mh = self.game_map.map_h.get(self.player.area, 30) * TILE
        target_x = max(0, min(target_x, mw - SCREEN_W))
        target_y = max(0, min(target_y, mh - SCREEN_H))
        self.camera_x = lerp(self.camera_x, target_x, 0.08)
        self.camera_y = lerp(self.camera_y, target_y, 0.08)

    def _update_ambient_particles(self):
        area = self.player.area
        fx = self.camera_x + random.randint(0, SCREEN_W)
        fy = self.camera_y + random.randint(0, SCREEN_H)
        if area == AREA_FOREST and self.tick % 15 == 0:
            self.particles.emit(fx, fy, 1, (0, 200, 160), 0.3, 90, 2, 'firefly')
        elif area == AREA_DUNGEON and self.tick % 20 == 0:
            self.particles.emit(fx, fy, 1, (0, 120, 100), 0.2, 60, 2, 'dust')
        elif area == AREA_VILLAGE and self.tick % 25 == 0:
            self.particles.emit(fx, fy, 1, (0, 180, 150), 0.15, 80, 1, 'dust')
        elif area == AREA_NEON_STREET and self.tick % 12 == 0:
            c = random.choice([(255, 50, 150), (0, 255, 200), (180, 60, 255)])
            self.particles.emit(fx, fy, 1, c, 0.2, 70, 2, 'firefly')
        elif area == AREA_FACTORY and self.tick % 18 == 0:
            self.particles.emit(fx, fy, 1, (200, 150, 0), 0.3, 50, 2, 'dust')
        elif area == AREA_CYBERSPACE and self.tick % 10 == 0:
            c = random.choice([(0, 255, 200), (180, 60, 255), (0, 200, 255)])
            self.particles.emit(fx, fy, 1, c, 0.4, 60, 2, 'magic')

    def _restart(self):
        self.player = Player(20, 16)
        self.state = GameState.EXPLORE
        self.combat = None
        self.chests_opened.clear()
        self.hidden_chests_opened.clear()
        self.encounter_steps = 0
        self.random_event_steps = 0
        self._generate_hidden_chests()
        self.ghost_merchant_pos = self._random_walkable_tile(AREA_FOREST)
        self.ghost_merchant_npc.x = self.ghost_merchant_pos[0]
        self.ghost_merchant_npc.y = self.ghost_merchant_pos[1]

    def _handle_skill_tree_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.state = GameState.MENU
            return
        branches = ['attack', 'defense', 'hack']
        if event.key == pygame.K_LEFT:
            self.skill_tree_branch = (self.skill_tree_branch - 1) % 3
            self.skill_tree_tier = 0
        elif event.key == pygame.K_RIGHT:
            self.skill_tree_branch = (self.skill_tree_branch + 1) % 3
            self.skill_tree_tier = 0
        elif event.key == pygame.K_UP:
            self.skill_tree_tier = max(0, self.skill_tree_tier - 1)
        elif event.key == pygame.K_DOWN:
            self.skill_tree_tier = min(3, self.skill_tree_tier + 1)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            branch = branches[self.skill_tree_branch]
            tier = self.skill_tree_tier + 1
            # 找到对应节点
            for sid, node in SKILL_TREE.items():
                if node.branch == branch and node.tier == tier:
                    if self.player.unlock_skill(sid):
                        self.message_queue.append((f"解锁技能：{node.name}！", 120))
                    elif sid in self.player.unlocked_skills:
                        self.message_queue.append(("已解锁该技能。", 60))
                    else:
                        if self.player.skill_points < node.cost:
                            self.message_queue.append(("技能点不足！", 60))
                        elif node.prereq and node.prereq not in self.player.unlocked_skills:
                            self.message_queue.append(("需要先解锁前置技能！", 60))
                    break

    def _handle_upgrade_shop_event(self, event):
        if event.type != pygame.KEYDOWN:
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            self.state = GameState.EXPLORE
            return
        upgradeable = []
        for slot in ['weapon', 'armor']:
            item_key = self.player.equipped.get(slot)
            if item_key:
                upgradeable.append((slot, item_key))
        if not upgradeable:
            return
        if event.key == pygame.K_UP:
            self.upgrade_index = (self.upgrade_index - 1) % len(upgradeable)
        elif event.key == pygame.K_DOWN:
            self.upgrade_index = (self.upgrade_index + 1) % len(upgradeable)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            if self.upgrade_index < len(upgradeable):
                slot, item_key = upgradeable[self.upgrade_index]
                cost = 100
                if self.player.stats.gold >= cost and self.player.has_item('precision_gear'):
                    self.player.stats.gold -= cost
                    self.player.remove_item('precision_gear')
                    item = ITEMS_DB[item_key]
                    item.atk_bonus += 3
                    item.def_bonus += 3
                    self.message_queue.append((f"{item.name}升级成功！ATK/DEF+3！", 120))
                else:
                    self.message_queue.append(("需要100信用点+1个精密齿轮！", 90))

    def _random_walkable_tile(self, area):
        """在指定区域随机选一个可行走的 tile"""
        mdata = self.game_map.maps.get(area, [])
        w = self.game_map.map_w.get(area, 0)
        h = self.game_map.map_h.get(area, 0)
        for _ in range(200):
            tx = random.randint(2, w - 3)
            ty = random.randint(2, h - 3)
            if self.game_map.is_walkable(area, tx, ty):
                # 避开 NPC、宝箱、转换点
                occupied = False
                for npc in self.npcs:
                    if npc.area == area and npc.x == tx and npc.y == ty:
                        occupied = True
                        break
                if (area, tx, ty) in self.chest_positions:
                    occupied = True
                if not occupied:
                    return (tx, ty)
        return (w // 2, h // 2)

    def _generate_hidden_chests(self):
        """为每个区域随机生成 1-2 个隐藏宝箱"""
        self.hidden_chests = {}
        hidden_loot = {
            AREA_FOREST: [('elixir', 1), ('lucky_coin', 1), ('magic_ring', 1)],
            AREA_DUNGEON: [('elixir', 1), ('mp_potion', 5), ('iron_sword', 1)],
            AREA_VILLAGE: [('hp_potion', 3), ('mp_potion', 2)],
            AREA_NEON_STREET: [('quantum_chip', 1), ('elixir', 1)],
            AREA_FACTORY: [('emp_grenade', 1), ('hp_potion', 5), ('iron_sword', 1)],
            AREA_CYBERSPACE: [('quantum_chip', 1), ('elixir', 2), ('emp_grenade', 1)],
        }
        for area in [AREA_VILLAGE, AREA_FOREST, AREA_DUNGEON, AREA_NEON_STREET, AREA_FACTORY, AREA_CYBERSPACE]:
            count = random.randint(1, 2)
            loot_pool = hidden_loot.get(area, [('hp_potion', 1)])
            for _ in range(count):
                pos = self._random_walkable_tile(area)
                key = (area, pos[0], pos[1])
                if key not in self.hidden_chests and key not in self.chest_positions:
                    item = random.choice(loot_pool)
                    self.hidden_chests[key] = item

    def _save_game(self):
        data = {
            'player': self.player.to_save_dict(),
            'chests_opened': [list(c) for c in self.chests_opened],
            'hidden_chests': {f"{a},{x},{y}": list(v) for (a, x, y), v in self.hidden_chests.items()},
            'hidden_chests_opened': [list(c) for c in self.hidden_chests_opened],
            'ghost_merchant_pos': list(self.ghost_merchant_pos),
        }
        try:
            with open(SAVE_PATH, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.message_queue.append(("游戏已保存！", 120))
        except Exception as e:
            traceback.print_exc()
            self.message_queue.append((f"保存失败！{e}", 120))

    def _load_game(self):
        if not os.path.exists(SAVE_PATH):
            self.message_queue.append(("没有找到存档！", 120))
            return
        try:
            with open(SAVE_PATH, 'r', encoding='utf-8') as f:
                data = json.load(f)
            self.player.load_save_dict(data['player'])
            self.chests_opened = set(tuple(c) for c in data.get('chests_opened', []))
            # 恢复隐藏宝箱状态
            hc = data.get('hidden_chests', {})
            self.hidden_chests = {}
            for k, v in hc.items():
                parts = k.split(',')
                self.hidden_chests[(parts[0], int(parts[1]), int(parts[2]))] = tuple(v)
            self.hidden_chests_opened = set(tuple(c) for c in data.get('hidden_chests_opened', []))
            # 恢复幽灵商人位置
            gmp = data.get('ghost_merchant_pos')
            if gmp:
                self.ghost_merchant_pos = tuple(gmp)
                self.ghost_merchant_npc.x = gmp[0]
                self.ghost_merchant_npc.y = gmp[1]
            self.combat = None
            self.encounter_steps = 0
            self.random_event_steps = 0
            self.state = GameState.EXPLORE
            self.show_inventory = False
            # 重置相机到玩家位置
            self.camera_x = self.player.x - SCREEN_W // 2
            self.camera_y = self.player.y - SCREEN_H // 2
            self.message_queue.append(("读取存档成功！", 120))
        except Exception as e:
            traceback.print_exc()
            self.message_queue.append((f"读取失败！{e}", 120))


    # ============================================================
    # 绘制
    # ============================================================
    def _draw(self):
        if self.state == GameState.TITLE:
            self._draw_title()
        elif self.state == GameState.EXPLORE:
            self._draw_explore()
        elif self.state == GameState.COMBAT:
            if self.combat:
                self.combat.draw(self.screen)
        elif self.state == GameState.MENU:
            self._draw_explore()
            self._draw_menu()
        elif self.state == GameState.SKILL_TREE:
            self._draw_skill_tree()
        elif self.state == GameState.UPGRADE_SHOP:
            self._draw_upgrade_shop()
        elif self.state == GameState.GAME_OVER:
            self._draw_game_over()
        elif self.state == GameState.ENDING:
            self._draw_ending()

    def _draw_title(self):
        # 赛博朋克渐变天空
        for y in range(SCREEN_H):
            t = y / SCREEN_H
            r = int(lerp(5, 15, t))
            g = int(lerp(5, 10, t))
            b = int(lerp(20, 50, t))
            pygame.draw.line(self.screen, (r, g, b), (0, y), (SCREEN_W, y))

        # 数据雨
        random.seed(42)
        for _ in range(120):
            sx = random.randint(0, SCREEN_W)
            sy = random.randint(0, SCREEN_H // 2)
            speed = random.randint(1, 3)
            animated_y = (sy + self.tick * speed) % (SCREEN_H // 2)
            c = random.choice([(0, 180, 150), (0, 255, 200), (0, 120, 100)])
            fade = max(30, 255 - animated_y * 2)
            self.screen.set_at((sx, animated_y), (c[0]*fade//255, c[1]*fade//255, c[2]*fade//255))
        random.seed()

        # 城市天际线
        for x in range(SCREEN_W):
            h = int(60 + math.sin(x * 0.015) * 30 + math.sin(x * 0.05) * 15)
            if x % 40 < 20:
                h += 30
            pygame.draw.line(self.screen, (15, 18, 35), (x, SCREEN_H - h), (x, SCREEN_H))
        # 霓虹窗户
        random.seed(99)
        for _ in range(60):
            wx = random.randint(0, SCREEN_W)
            wy = random.randint(SCREEN_H - 120, SCREEN_H - 20)
            c = random.choice([(0, 200, 180), (255, 50, 150), (180, 60, 255), (0, 255, 100)])
            pygame.draw.rect(self.screen, c, (wx, wy, 3, 2))
        random.seed()

        # 标题
        draw_text(self.screen, "赛博入侵", (SCREEN_W//2, 180), self.assets.font_title, C_NEON_CYAN, center=True)
        draw_text(self.screen, "Cyber Breach", (SCREEN_W//2, 230), self.assets.font_lg, C_NEON_PURPLE, center=True)

        # 菜单选项
        has_save = os.path.exists(SAVE_PATH)
        options = ["> 新连接", "> 读取存档"]
        for i, opt in enumerate(options):
            if i == 1 and not has_save:
                color = (40, 50, 60)
            elif i == self.title_index:
                color = C_NEON_CYAN
            else:
                color = C_WHITE
            prefix = ">> " if i == self.title_index else "   "
            draw_text(self.screen, prefix + opt, (SCREEN_W//2, 340 + i * 36), self.assets.font_md, color, center=True)

        # 操作说明
        draw_text(self.screen, "方向键/WASD: 移动  J: 确认/交互  X: 取消  ESC: 菜单",
                  (SCREEN_W//2, SCREEN_H - 60), self.assets.font_sm, (80, 100, 120), center=True)

    def _draw_explore(self):
        area = self.player.area
        cam_x, cam_y = int(self.camera_x), int(self.camera_y)

        # 天空渐变
        self._draw_sky(area)

        # 地图瓦片
        mdata = self.game_map.maps.get(area, [])
        start_tx = max(0, cam_x // TILE)
        start_ty = max(0, cam_y // TILE)
        end_tx = min(self.game_map.map_w.get(area, 0), (cam_x + SCREEN_W) // TILE + 2)
        end_ty = min(self.game_map.map_h.get(area, 0), (cam_y + SCREEN_H) // TILE + 2)

        water_frame = (self.tick // 15) % 4

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                sx = tx * TILE - cam_x
                sy = ty * TILE - cam_y
                tile = self.game_map.get_tile(area, tx, ty)

                if tile == 0:  # 金属地板
                    key = 'grass2' if (tx + ty) % 3 == 0 else 'grass'
                    self.screen.blit(self.assets.tiles[key], (sx, sy))
                elif tile == 1:  # 霓虹步道
                    self.screen.blit(self.assets.tiles['path'], (sx, sy))
                elif tile == 2:  # 数据流
                    self.screen.blit(self.assets.tiles[f'water_{water_frame}'], (sx, sy))
                    # 数据流闪光
                    if self.tick % 30 < 15 and random.random() < 0.02:
                        self.screen.set_at((sx + random.randint(0, TILE-1), sy + random.randint(0, TILE//2)),
                                           (0, 255, 220))
                elif tile == 3:  # 金属墙
                    self.screen.blit(self.assets.tiles['wall'], (sx, sy))
                elif tile == 4:  # 信号塔
                    self.screen.blit(self.assets.tiles['grass'], (sx, sy))
                    self.screen.blit(self.assets.tiles['tree'], (sx, sy))
                elif tile == 5:  # 电路板地板
                    self.screen.blit(self.assets.tiles['dungeon_floor'], (sx, sy))
                elif tile == 6:  # 霓虹灯
                    self.screen.blit(self.assets.tiles['grass'], (sx, sy))
                    self.screen.blit(self.assets.tiles['flower'], (sx, sy))
                elif tile == 7:  # 传送门
                    self.screen.blit(self.assets.tiles['door'], (sx, sy))
                elif tile == 8:  # 工厂地板
                    self.screen.blit(self.assets.tiles['factory_floor'], (sx, sy))
                elif tile == 9:  # 网络地板
                    self.screen.blit(self.assets.tiles['cyber_floor'], (sx, sy))
                elif tile == 10:  # 霓虹地砖
                    self.screen.blit(self.assets.tiles['neon_tile'], (sx, sy))
                elif tile == 11:  # 室内地板
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                elif tile == 12:  # 室内墙
                    self.screen.blit(self.assets.tiles['indoor_wall'], (sx, sy))
                elif tile == 13:  # 桌子
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                    self.screen.blit(self.assets.tiles['table'], (sx, sy))
                elif tile == 14:  # 终端机
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                    self.screen.blit(self.assets.tiles['terminal'], (sx, sy))
                elif tile == 15:  # 书架
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                    self.screen.blit(self.assets.tiles['bookshelf'], (sx, sy))
                elif tile == 16:  # 沙发
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                    self.screen.blit(self.assets.tiles['sofa'], (sx, sy))
                elif tile == 17:  # 地毯
                    self.screen.blit(self.assets.tiles['carpet'], (sx, sy))
                elif tile == 18:  # 吧台
                    self.screen.blit(self.assets.tiles['indoor_floor'], (sx, sy))
                    self.screen.blit(self.assets.tiles['bar_counter'], (sx, sy))
                elif tile == 19:  # 管道地板
                    self.screen.blit(self.assets.tiles['pipe_floor'], (sx, sy))
                elif tile == 20:  # 锈蚀墙
                    self.screen.blit(self.assets.tiles['rust_wall'], (sx, sy))

        # 宝箱
        for (a, cx, cy), (item_key, cnt) in self.chest_positions.items():
            if a == area and (a, cx, cy) not in self.chests_opened:
                sx = cx * TILE - cam_x
                sy = cy * TILE - cam_y
                self.screen.blit(self.assets.tiles['chest'], (sx, sy))

        # 建筑（数据港和霓虹街特有）
        if area in (AREA_VILLAGE, AREA_NEON_STREET):
            houses = [(12, 6), (26, 8), (30, 18)]
            for hx, hy in houses:
                sx = hx * TILE - cam_x
                sy = hy * TILE - cam_y
                self.screen.blit(self.assets.tiles['house'], (sx, sy))

        # NPC
        for npc in self.npcs:
            if npc.area == area:
                sx = npc.x * TILE - cam_x
                sy = npc.y * TILE - cam_y
                sprite = self.assets.npc_sprites.get(npc.sprite_key)
                if sprite:
                    # NPC 轻微浮动
                    bob = int(math.sin(self.tick * 0.05 + npc.x) * 2)
                    self.screen.blit(sprite, (sx, sy + bob))
                    # 名字
                    draw_text(self.screen, npc.name, (sx + TILE//2, sy - 8),
                              self.assets.font_sm, C_GOLD, center=True)
                    # 交互提示
                    dist = abs(self.player.tx - npc.x) + abs(self.player.ty - npc.y)
                    if dist <= 2:
                        if (self.tick // 20) % 2:
                            # 气泡背景
                            bw_hint = self.assets.font_sm.size("[J]")[0] + 8
                            bh_hint = 18
                            bx_hint = sx + TILE//2 - bw_hint//2
                            by_hint = sy - 28
                            pygame.draw.rect(self.screen, (30, 25, 50), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                            pygame.draw.rect(self.screen, (160, 140, 200), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                            draw_text(self.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                      self.assets.font_sm, C_YELLOW, center=True)

        # 幽灵商人（森林中，闪烁半透明效果）
        if area == AREA_FOREST:
            gx, gy = self.ghost_merchant_npc.x, self.ghost_merchant_npc.y
            sx = gx * TILE - cam_x
            sy = gy * TILE - cam_y
            # 闪烁：用 sin 控制可见度，部分 tick 不显示
            flicker = math.sin(self.tick * 0.08) * 0.5 + 0.5  # 0~1
            if flicker > 0.2:  # 80% 时间可见
                ghost_sprite = self.assets.npc_sprites.get('ghost_merchant')
                if ghost_sprite:
                    # 半透明效果
                    alpha = int(100 + flicker * 100)  # 100~200
                    temp = ghost_sprite.copy()
                    temp.set_alpha(alpha)
                    bob = int(math.sin(self.tick * 0.04 + gx) * 3)
                    self.screen.blit(temp, (sx, sy + bob))
                    # 名字（也半透明）
                    name_color = (180, 140, 255)
                    draw_text(self.screen, "???", (sx + TILE//2, sy - 8),
                              self.assets.font_sm, name_color, center=True)
                    # 交互提示
                    dist = abs(self.player.tx - gx) + abs(self.player.ty - gy)
                    if dist <= 2:
                        if (self.tick // 15) % 2:
                            bw_hint = self.assets.font_sm.size("[J]")[0] + 8
                            bh_hint = 18
                            bx_hint = sx + TILE//2 - bw_hint//2
                            by_hint = sy - 28
                            pygame.draw.rect(self.screen, (40, 20, 60), (bx_hint, by_hint, bw_hint, bh_hint), border_radius=4)
                            pygame.draw.rect(self.screen, (180, 140, 220), (bx_hint, by_hint, bw_hint, bh_hint), 1, border_radius=4)
                            draw_text(self.screen, "[J]", (sx + TILE//2, by_hint + 1),
                                      self.assets.font_sm, (200, 160, 255), center=True)

        # 玩家
        frames = self.assets.player_frames.get(self.player.direction, [])
        if frames:
            frame_idx = self.player.anim_frame if self.player.moving else 0
            psurf = frames[frame_idx % len(frames)]
            px = int(self.player.x) - cam_x
            py = int(self.player.y) - cam_y
            self.screen.blit(psurf, (px, py))

        # 粒子
        self.particles.draw(self.screen, cam_x, cam_y)

        # 对话框
        self.dialogue.draw(self.screen, self.player)

        # HUD
        self._draw_hud()

        # 小地图
        self._draw_minimap()

        # 消息
        if self.message_queue:
            msg, timer = self.message_queue[0]
            alpha = min(255, timer * 4)
            draw_text(self.screen, msg, (SCREEN_W//2, 80), self.assets.font_md, C_GOLD, center=True)

        # 区域名称（进入时短暂显示）
        if self.encounter_steps < 60:
            area_names = {AREA_VILLAGE: "数据港", AREA_FOREST: "废墟荒地", AREA_DUNGEON: "旧数据中心",
                          AREA_NEON_STREET: "霓虹商业街", AREA_FACTORY: "废弃工厂", AREA_CYBERSPACE: "网络空间",
                          AREA_TUNNEL: "地下通道", AREA_BLACK_MARKET: "黑市"}
            name = area_names.get(area, "")
            alpha = max(0, 60 - self.encounter_steps) / 60
            c = tuple(int(255 * alpha) for _ in range(3))
            draw_text(self.screen, name, (SCREEN_W//2, 50), self.assets.font_lg, c, center=True)

    def _draw_sky(self, area):
        if area == AREA_VILLAGE:
            # 数据港 - 深蓝夜空
            top = (5, 5, 20)
            bot = (15, 15, 35)
        elif area == AREA_FOREST:
            # 废墟荒地 - 暗绿
            top = (8, 15, 10)
            bot = (15, 25, 18)
        elif area == AREA_NEON_STREET:
            # 霓虹商业街 - 紫蓝
            top = (10, 5, 25)
            bot = (20, 12, 40)
        elif area == AREA_FACTORY:
            # 废弃工厂 - 暗橙
            top = (15, 10, 5)
            bot = (25, 18, 10)
        elif area == AREA_CYBERSPACE:
            # 网络空间 - 深蓝黑
            top = (2, 2, 12)
            bot = (8, 8, 25)
        elif area == AREA_TUNNEL:
            # 地下通道 - 暗棕
            top = (12, 8, 5)
            bot = (20, 15, 10)
        elif area == AREA_BLACK_MARKET:
            # 黑市 - 深紫
            top = (8, 3, 15)
            bot = (15, 8, 28)
        else:
            # 旧数据中心
            top = (8, 5, 15)
            bot = (15, 12, 25)

        for y in range(SCREEN_H):
            t = y / SCREEN_H
            c = lerp_color(top, bot, t)
            pygame.draw.line(self.screen, c, (0, y), (SCREEN_W, y))

    def _draw_hud(self):
        st = self.player.stats
        # 状态栏背景 - 赛博朋克风
        draw_pixel_rect(self.screen, (8, 10, 25), (8, 8, 220, 60), 2, (0, 150, 130))

        draw_text(self.screen, f"Lv.{st.level} 黑客", (16, 12), self.assets.font_sm, C_NEON_CYAN)
        draw_bar(self.screen, 16, 30, 140, 10, st.hp / st.max_hp, C_HP_BAR)
        draw_text(self.screen, f"HP {st.hp}/{st.max_hp}", (160, 28), self.assets.font_sm)
        draw_bar(self.screen, 16, 44, 140, 10, st.mp / st.max_mp, C_MP_BAR)
        draw_text(self.screen, f"EN {st.mp}/{st.max_mp}", (160, 42), self.assets.font_sm)
        draw_bar(self.screen, 16, 58, 140, 8, st.exp / max(1, st.exp_next), C_EXP_BAR)
        draw_text(self.screen, f"EXP {st.exp}/{st.exp_next}", (160, 55), self.assets.font_sm)

        # 信用点
        draw_text(self.screen, f"CR {st.gold}", (16, 74), self.assets.font_sm, C_NEON_CYAN)
        # 技能点
        if self.player.skill_points > 0:
            draw_text(self.screen, f"SP:{self.player.skill_points}", (100, 74), self.assets.font_sm, C_YELLOW)
        # 主线任务提示
        quest_hints = {
            0: "与城市管理员对话",
            1: "击败工厂Boss：失控监工",
            2: "通过地下通道到旧数据中心",
            3: "前往网络空间找AI先知",
            4: "击败量子霸主·真身",
            5: "通关！自由探索",
        }
        hint = quest_hints.get(self.player.quest_stage, "")
        if hint:
            draw_text(self.screen, f"[主线] {hint}", (SCREEN_W // 2, SCREEN_H - 16),
                      self.assets.font_sm, C_GOLD, center=True)

    def _draw_minimap(self):
        mm_w, mm_h = 120, 90
        mm_x, mm_y = SCREEN_W - mm_w - 10, 10
        mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm_surf.fill((0, 0, 0, 140))

        area = self.player.area
        mw = self.game_map.map_w.get(area, 1)
        mh = self.game_map.map_h.get(area, 1)
        sx = mm_w / mw
        sy = mm_h / mh

        mdata = self.game_map.maps.get(area, [])
        for ty, row in enumerate(mdata):
            for tx, tile in enumerate(row):
                px = int(tx * sx)
                py = int(ty * sy)
                pw = max(1, int(sx))
                ph = max(1, int(sy))
                if tile == 0 or tile == 6:
                    c = (30, 35, 45, 180)
                elif tile == 1:
                    c = (0, 150, 130, 180)
                elif tile == 2:
                    c = (0, 100, 180, 180)
                elif tile == 3:
                    c = (50, 55, 65, 180)
                elif tile == 4:
                    c = (80, 90, 110, 180)
                elif tile == 5:
                    c = (20, 25, 40, 180)
                elif tile == 7:
                    c = (0, 255, 200, 180)
                elif tile == 8:
                    c = (45, 40, 35, 180)
                elif tile == 9:
                    c = (10, 10, 30, 180)
                elif tile == 10:
                    c = (20, 15, 40, 180)
                elif tile == 19:
                    c = (25, 22, 18, 180)
                elif tile == 20:
                    c = (40, 30, 22, 180)
                else:
                    c = (15, 15, 25, 180)
                pygame.draw.rect(mm_surf, c, (px, py, pw, ph))

        # 玩家位置
        ppx = int(self.player.tx * sx)
        ppy = int(self.player.ty * sy)
        pygame.draw.rect(mm_surf, (0, 255, 200, 255), (ppx - 1, ppy - 1, 3, 3))

        # NPC位置
        for npc in self.npcs:
            if npc.area == area:
                npx = int(npc.x * sx)
                npy = int(npc.y * sy)
                pygame.draw.rect(mm_surf, (255, 220, 50, 255), (npx, npy, 2, 2))

        # 边框
        pygame.draw.rect(mm_surf, (140, 120, 180, 200), (0, 0, mm_w, mm_h), 2)

        self.screen.blit(mm_surf, (mm_x, mm_y))

    def _draw_menu(self):
        # 半透明遮罩
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        self.screen.blit(overlay, (0, 0))

        # 主面板
        pw, ph = 400, 420
        px = (SCREEN_W - pw) // 2
        py = (SCREEN_H - ph) // 2
        draw_pixel_rect(self.screen, C_PANEL, (px, py, pw, ph), 3, C_PANEL_BORDER)

        draw_text(self.screen, "【菜单】", (px + pw//2, py + 16), self.assets.font_lg, C_GOLD, center=True)

        st = self.player.stats

        # 角色信息
        info_y = py + 50
        draw_text(self.screen, f"Lv.{st.level} 黑客", (px + 20, info_y), self.assets.font_md, C_GOLD)
        draw_bar(self.screen, px + 20, info_y + 28, 200, 14, st.hp / st.max_hp, C_HP_BAR)
        draw_text(self.screen, f"HP {st.hp}/{st.max_hp}", (px + 230, info_y + 26), self.assets.font_sm)
        draw_bar(self.screen, px + 20, info_y + 48, 200, 14, st.mp / st.max_mp, C_MP_BAR)
        draw_text(self.screen, f"MP {st.mp}/{st.max_mp}", (px + 230, info_y + 46), self.assets.font_sm)

        draw_text(self.screen, f"攻击力: {self.player.get_total_atk()}", (px + 20, info_y + 72), self.assets.font_sm)
        draw_text(self.screen, f"防御力: {self.player.get_total_def()}", (px + 20, info_y + 92), self.assets.font_sm)
        draw_text(self.screen, f"信用点: {st.gold}", (px + 200, info_y + 72), self.assets.font_sm, C_GOLD)
        draw_text(self.screen, f"经验: {st.exp}/{st.exp_next}", (px + 200, info_y + 92), self.assets.font_sm)

        # 装备
        draw_text(self.screen, "【装备】", (px + 20, info_y + 120), self.assets.font_sm, C_GOLD)
        equip_names = {'weapon': '武器', 'armor': '防具', 'accessory': '饰品'}
        ey = info_y + 142
        for slot, label in equip_names.items():
            eq = self.player.equipped[slot]
            name = ITEMS_DB[eq].name if eq else "无"
            draw_text(self.screen, f"{label}: {name}", (px + 30, ey), self.assets.font_sm)
            ey += 20

        # 菜单选项
        if self.show_inventory:
            self._draw_inventory_panel(px + 20, info_y + 220, pw - 40)
        else:
            options = ["[I] 物品", "[S] 状态", "[T] 技能树", "[W] 保存", "[L] 读取", "[Q] 返回"]
            for i, opt in enumerate(options):
                color = C_YELLOW if i == self.menu_index else C_WHITE
                prefix = ">> " if i == self.menu_index else "   "
                draw_text(self.screen, prefix + opt, (px + 30, info_y + 220 + i * 26), self.assets.font_md, color)

    def _draw_inventory_panel(self, x, y, w):
        draw_text(self.screen, "【物品栏】(X返回)", (x, y), self.assets.font_sm, C_GOLD)
        items = self.player.inventory
        if not items:
            draw_text(self.screen, "空空如也...", (x + 10, y + 24), self.assets.font_sm)
            return
        for i, (key, cnt) in enumerate(items):
            item = ITEMS_DB.get(key)
            if not item:
                continue
            color = C_YELLOW if i == self.inv_index else C_WHITE
            prefix = ">> " if i == self.inv_index else "   "
            # 图标
            icon = self.assets.item_icons.get(key)
            iy = y + 24 + i * 26
            if icon:
                self.screen.blit(icon, (x + 4, iy))
            draw_text(self.screen, f"{prefix}{item.name} x{cnt}", (x + 30, iy + 2), self.assets.font_sm, color)
            # 选中时显示描述
            if i == self.inv_index:
                draw_text(self.screen, item.description, (x + 10, y + 24 + len(items) * 26 + 10),
                          self.assets.font_sm, (180, 180, 200))
                draw_text(self.screen, "J: 使用/装备", (x + 10, y + 24 + len(items) * 26 + 30),
                          self.assets.font_sm, (150, 150, 170))

    def _draw_game_over(self):
        self.screen.fill(C_BLACK)
        draw_text(self.screen, "SYSTEM OFFLINE", (SCREEN_W//2, SCREEN_H//2 - 40), self.assets.font_title, C_RED, center=True)
        draw_text(self.screen, "连接中断...", (SCREEN_W//2, SCREEN_H//2 + 20), self.assets.font_md, C_WHITE, center=True)
        if (self.tick // 30) % 2:
            draw_text(self.screen, "按 Enter 重新连接", (SCREEN_W//2, SCREEN_H//2 + 80), self.assets.font_md, C_NEON_CYAN, center=True)

    def _draw_skill_tree(self):
        self.screen.fill((8, 8, 18))
        draw_text(self.screen, "【技能树】(ESC返回)", (SCREEN_W//2, 20), self.assets.font_lg, C_GOLD, center=True)
        draw_text(self.screen, f"技能点: {self.player.skill_points}", (SCREEN_W//2, 50), self.assets.font_md, C_YELLOW, center=True)

        branches = [('attack', '攻击', C_RED), ('defense', '防御', C_NEON_CYAN), ('hack', '黑客', C_NEON_PURPLE)]
        bw = 180
        start_x = (SCREEN_W - bw * 3 - 40) // 2

        for bi, (branch, bname, bcolor) in enumerate(branches):
            bx = start_x + bi * (bw + 20)
            selected_branch = bi == self.skill_tree_branch
            # 分支标题
            title_color = bcolor if selected_branch else (80, 80, 80)
            draw_text(self.screen, bname, (bx + bw//2, 80), self.assets.font_md, title_color, center=True)
            # 技能节点
            for sid, node in SKILL_TREE.items():
                if node.branch != branch:
                    continue
                tier_idx = node.tier - 1
                ny = 110 + tier_idx * 70
                nx = bx + 10
                # 状态
                unlocked = sid in self.player.unlocked_skills
                selected = selected_branch and tier_idx == self.skill_tree_tier
                if unlocked:
                    bg = (20, 40, 30)
                    border = bcolor
                elif selected:
                    bg = (25, 25, 40)
                    border = C_YELLOW
                else:
                    bg = (15, 15, 25)
                    border = (50, 50, 60)
                draw_pixel_rect(self.screen, bg, (nx, ny, bw - 20, 55), 2, border)
                name_color = C_WHITE if unlocked else (140, 140, 140)
                draw_text(self.screen, f"{node.name} (Lv{node.tier})", (nx + 5, ny + 5), self.assets.font_sm, name_color)
                draw_text(self.screen, node.desc, (nx + 5, ny + 22), self.assets.font_sm, (120, 120, 140))
                cost_text = "已解锁" if unlocked else f"消耗: {node.cost}SP"
                draw_text(self.screen, cost_text, (nx + 5, ny + 38), self.assets.font_sm,
                          C_GREEN if unlocked else (100, 100, 120))

        # 操作提示
        draw_text(self.screen, "←→切换分支  ↑↓选择  Enter解锁", (SCREEN_W//2, SCREEN_H - 30),
                  self.assets.font_sm, (100, 100, 120), center=True)
        # 消息
        if self.message_queue:
            draw_text(self.screen, self.message_queue[0][0], (SCREEN_W//2, SCREEN_H - 55),
                      self.assets.font_sm, C_GOLD, center=True)

    def _draw_upgrade_shop(self):
        self.screen.fill((8, 8, 18))
        draw_text(self.screen, "【装备升级】(ESC返回)", (SCREEN_W//2, 30), self.assets.font_lg, C_GOLD, center=True)
        draw_text(self.screen, "消耗: 100信用点 + 1精密齿轮 → ATK/DEF+3", (SCREEN_W//2, 60),
                  self.assets.font_sm, (140, 140, 160), center=True)
        upgradeable = []
        for slot in ['weapon', 'armor']:
            item_key = self.player.equipped.get(slot)
            if item_key:
                upgradeable.append((slot, item_key))
        if not upgradeable:
            draw_text(self.screen, "没有已装备的武器/防具", (SCREEN_W//2, 120), self.assets.font_md, C_WHITE, center=True)
        else:
            for i, (slot, item_key) in enumerate(upgradeable):
                item = ITEMS_DB[item_key]
                color = C_YELLOW if i == self.upgrade_index else C_WHITE
                prefix = ">> " if i == self.upgrade_index else "   "
                slot_name = "武器" if slot == 'weapon' else "防具"
                draw_text(self.screen, f"{prefix}{slot_name}: {item.name} (ATK+{item.atk_bonus} DEF+{item.def_bonus})",
                          (100, 120 + i * 30), self.assets.font_md, color)

    def _draw_ending(self):
        self.screen.fill((5, 5, 15))
        self.ending_particles.draw(self.screen, 0, 0)
        # 渐入文字
        alpha = min(255, self.ending_timer * 3)
        if self.ending_timer > 30:
            draw_text(self.screen, "量子霸主被击败了...", (SCREEN_W//2, 100), self.assets.font_lg, C_NEON_CYAN, center=True)
        if self.ending_timer > 80:
            draw_text(self.screen, "网络空间恢复了秩序", (SCREEN_W//2, 160), self.assets.font_md, C_WHITE, center=True)
        if self.ending_timer > 130:
            draw_text(self.screen, "数据港重新连接了所有节点", (SCREEN_W//2, 210), self.assets.font_md, C_WHITE, center=True)
        if self.ending_timer > 180:
            draw_text(self.screen, "赛博入侵 - 通关", (SCREEN_W//2, 280), self.assets.font_title, C_GOLD, center=True)
            draw_text(self.screen, f"最终等级: Lv{self.player.stats.level}", (SCREEN_W//2, 330),
                      self.assets.font_md, C_NEON_PINK, center=True)
            if (self.tick // 30) % 2:
                draw_text(self.screen, "按 Enter 继续探索", (SCREEN_W//2, 400),
                          self.assets.font_md, C_NEON_CYAN, center=True)

# ============================================================
# 入口
# ============================================================
if __name__ == '__main__':
    game = Game()
    game.run()
