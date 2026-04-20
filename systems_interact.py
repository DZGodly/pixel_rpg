"""NPC交互系统：对话、任务、恋爱、送礼"""

import pygame
from constants import TILE, C_GOLD
from game_map import AREA_FOREST, AREA_BLACK_MARKET, AREA_HOME
from entities import ITEMS_DB, ROMANCE_CHARS, FUSION_RECIPES
from combat import Combat
from data import GRAFFITI_POS, GRAFFITI_DB, GRAFFITI_SETS


def interact(g):
    """与面前的NPC/物体交互"""
    dx, dy = 0, 0
    if g.player.direction == 'up': dy = -1
    elif g.player.direction == 'down': dy = 1
    elif g.player.direction == 'left': dx = -1
    elif g.player.direction == 'right': dx = 1

    target_tx = g.player.tx + dx
    target_ty = g.player.ty + dy

    # 检查面前一格和当前站的格子
    check_positions = [(target_tx, target_ty), (g.player.tx, g.player.ty)]

    # 幽灵商人
    if g.player.area == AREA_FOREST:
        for cx, cy in check_positions:
            if g.ghost_merchant_npc.x == cx and g.ghost_merchant_npc.y == cy:
                # 芯片融合检测
                available_fusions = []
                for recipe in FUSION_RECIPES:
                    materials, product_key, product_name = recipe
                    can_fuse = all(g.player.item_count(k) >= v for k, v in materials.items())
                    if can_fuse:
                        available_fusions.append(recipe)
                if available_fusions:
                    # 显示融合选项
                    mat, prod_key, prod_name = available_fusions[0]
                    mat_text = '+'.join(f"{ITEMS_DB[k].name}x{v}" for k, v in mat.items())
                    g.ghost_merchant_npc.dialogues = [
                        "[!] 我感应到了什么...",
                        f"你的背包里有可以融合的材料！",
                        f"融合：{mat_text} → {prod_name}",
                        "（按J确认融合）",
                    ]
                    # 执行融合
                    for k, v in mat.items():
                        g.player.remove_item(k, v)
                    g.player.add_item(prod_key)
                    item = ITEMS_DB[prod_key]
                    g.message_queue.append((f"[!] 芯片融合成功！获得{item.name}！", 180))
                    px = g.player.x + TILE // 2
                    py = g.player.y + TILE // 2
                    g.particles.emit(px, py, 25, (180, 60, 255), 3, 50, 4, 'magic')
                    g.particles.emit(px, py, 15, (0, 255, 200), 2, 40, 3, 'firefly')
                g.dialogue.start(g.ghost_merchant_npc, g.player.quest_stage)
                return

    # 暗网守护者入口（黑市特定坐标交互）
    if (g.player.area == AREA_BLACK_MARKET and not g.player.darknet_cleared
            and g.player.quest_stage >= 5
            and g.player.item_count('encrypted_data') >= 3):
        # 黑市中心区域触发
        if 10 <= target_tx <= 16 and 10 <= target_ty <= 14:
            g.player.remove_item('encrypted_data', 3)
            g.darknet_phase = 1
            g.message_queue.append(("【暗网守护者】加密数据共鸣...暗网入口开启！", 180))
            g.message_queue.append(("三连Boss战开始！每场间恢复部分HP/EN。", 120))
            g.combat = Combat(g.player, 'firewall_guardian', g.assets)
            from game import GameState
            g.state = GameState.COMBAT
            return

    # NPC
    for npc in g.npcs:
        if npc.area == g.player.area:
            for cx, cy in check_positions:
                if npc.x == cx and npc.y == cy:
                    handle_npc_interact(g, npc)
                    return

    # 恋爱NPC
    for npc in g.romance_npcs:
        if npc.area == g.player.area:
            for cx, cy in check_positions:
                if npc.x == cx and npc.y == cy:
                    handle_romance_interact(g, npc)
                    return

    # 宝箱
    chest_key = (g.player.area, target_tx, target_ty)
    if chest_key in g.chest_positions and chest_key not in g.chests_opened:
        item_key, count = g.chest_positions[chest_key]
        g.player.add_item(item_key, count)
        g.chests_opened.add(chest_key)
        item = ITEMS_DB[item_key]
        g.message_queue.append((f"获得 {item.name} x{count}！", 120))
        g.particles.emit(target_tx * TILE + 16, target_ty * TILE + 16, 15, C_GOLD, 2, 40, 3, 'magic')
        return

    # 隐藏宝箱（检测玩家当前位置和面前位置）
    for check_key in [chest_key, (g.player.area, g.player.tx, g.player.ty)]:
        if check_key in g.hidden_chests and check_key not in g.hidden_chests_opened:
            item_key, count = g.hidden_chests[check_key]
            g.player.add_item(item_key, count)
            g.hidden_chests_opened.add(check_key)
            item = ITEMS_DB[item_key]
            g.message_queue.append((f"[!] 发现隐藏终端! 获得 {item.name} x{count}!", 150))
            px = check_key[1] * TILE + 16
            py = check_key[2] * TILE + 16
            g.particles.emit(px, py, 25, (255, 200, 100), 3, 50, 3, 'magic')
            g.particles.emit(px, py, 15, (0, 255, 200), 2, 40, 2, 'firefly')
            return

    # 赛博涂鸦检测（面前的墙壁瓦片）
    graffiti_key = (g.player.area, target_tx, target_ty)
    if graffiti_key in GRAFFITI_POS:
        gid = GRAFFITI_POS[graffiti_key]
        if gid not in g.player.graffiti_found:
            gdef = GRAFFITI_DB[gid]
            tile = g.game_map.get_tile(g.player.area, target_tx, target_ty)
            if tile in (3, 12, 20, 22):  # 墙壁类瓦片
                g.player.graffiti_found.add(gid)
                g.message_queue.append((f"[!] 发现赛博涂鸦：{gdef.name}", 150))
                g.message_queue.append((f"「{gdef.description}」", 120))
                # 霓虹粒子效果
                px = target_tx * TILE + TILE // 2
                py = target_ty * TILE + TILE // 2
                g.particles.emit(px, py, 30, (0, 255, 200), 3, 50, 4, 'magic')
                g.particles.emit(px, py, 20, (255, 50, 150), 2, 40, 3, 'firefly')
                # 首个涂鸦成就
                if len(g.player.graffiti_found) == 1 and 'graffiti_hunter' not in g.player.achievements:
                    g.player.achievements.add('graffiti_hunter')
                    g.message_queue.append(("【成就】涂鸦猎人 — ATK+2", 150))
                # 全部收集成就
                if len(g.player.graffiti_found) == len(GRAFFITI_DB) and 'graffiti_master' not in g.player.achievements:
                    g.player.achievements.add('graffiti_master')
                    g.message_queue.append(("【成就】涂鸦大师 — MAX_HP+10 ATK+3 DEF+3", 180))
                # 检查套装完成
                set_info = GRAFFITI_SETS.get(gdef.set_id)
                if set_info and gdef.set_id not in g.player.graffiti_sets_claimed:
                    if all(sid in g.player.graffiti_found for sid in set_info['ids']):
                        g.player.graffiti_sets_claimed.add(gdef.set_id)
                        bonus = set_info['bonus']
                        for attr, val in bonus.items():
                            setattr(g.player.stats, attr, getattr(g.player.stats, attr) + val)
                        if 'max_hp' in bonus:
                            g.player.stats.hp = min(g.player.stats.hp + bonus['max_hp'], g.player.stats.max_hp)
                        g.message_queue.append((f"【套装完成】{set_info['name']} — {set_info['desc']}", 180))
                        g.particles.emit(int(g.player.x) + TILE // 2, int(g.player.y) + TILE // 2,
                                         40, (255, 220, 50), 4, 60, 5, 'magic')
                return

    # 家园：农田交互
    if g.player.area == AREA_HOME:
        from game import GameState
        tile = g.game_map.get_tile(AREA_HOME, target_tx, target_ty)
        if tile == 21:  # 农田地块
            g.state = GameState.FARM
            # 确定是哪块地
            plot_idx = g._get_farm_plot_index(target_tx, target_ty)
            if plot_idx is not None:
                g.farm_index = plot_idx
            g.farm_mode = 0
            return
        # 宠物管理台（终端机位置）
        if target_tx == 17 and target_ty == 2:
            g.state = GameState.PET_MENU
            g.pet_menu_index = 0
            return
        # 家具/据点管理（书架位置）
        if target_tx == 5 and target_ty == 2:
            g.state = GameState.HOME_DECOR
            g.home_decor_index = 0
            return
        # 图鉴（沙发位置）
        if target_tx == 10 and target_ty == 2:
            g.state = GameState.CODEX
            g.codex_tab = 0
            g.codex_scroll = 0
            return


def handle_npc_interact(g, npc):
    """处理NPC交互，含任务逻辑"""
    p = g.player

    # 赏金终端 → 进入悬赏板
    if npc.name == '赏金终端':
        g._refresh_bounty_board()
        from game import GameState
        g.state = GameState.BOUNTY_BOARD
        g.bounty_index = 0
        return

    # 主线：城市管理员 - Stage 0 → 1
    if npc.name == '城市管理员' and p.quest_stage == 0:
        p.quest_stage = 1
        g.message_queue.append(("【主线】前往废弃工厂，击败失控监工！", 180))
    # 主线：AI先知 - Stage 3 → 4
    elif npc.name == 'AI先知' and p.quest_stage == 3:
        p.quest_stage = 4
        g.message_queue.append(("【主线】前往网络空间中央(20,20)，击败量子霸主·真身！", 180))

    # 支线：维修技师 - 零件收集
    if npc.name == '维修技师':
        sq = p.side_quests.get('gear_collect', 0)
        if sq == 0:
            p.side_quests['gear_collect'] = 1
            p.quest_counters['gear_collect'] = p.item_count('precision_gear')
            g.message_queue.append(("【支线】零件收集：收集3个精密齿轮", 150))
        elif sq == 1 and p.item_count('precision_gear') >= 3:
            p.remove_item('precision_gear', 3)
            p.side_quests['gear_collect'] = 2
            p.quest_flags['upgrade_unlocked'] = True
            g.message_queue.append(("【支线完成】零件收集！解锁装备升级服务！", 180))

    # 支线：数据分析师 - 数据采样
    if npc.name == '数据分析师':
        sq = p.side_quests.get('data_collect', 0)
        if sq == 0:
            p.side_quests['data_collect'] = 1
            g.message_queue.append(("【支线】数据采样：收集2个数据样本", 150))
        elif sq == 1 and p.item_count('data_sample') >= 2:
            p.remove_item('data_sample', 2)
            p.side_quests['data_collect'] = 2
            p.stats.exp += 80
            p.add_item('quantum_chip')
            g.message_queue.append(("【支线完成】数据采样！获得80EXP+量子芯片！", 180))

    # 支线：醉酒佣兵 - 佣兵委托
    if npc.name == '醉酒佣兵':
        sq = p.side_quests.get('merc_hunt', 0)
        if sq == 0:
            p.side_quests['merc_hunt'] = 1
            p.quest_counters['merc_hunt'] = 0
            g.message_queue.append(("【支线】佣兵委托：击败10个敌人", 150))
        elif sq == 1 and p.quest_counters.get('merc_hunt', 0) >= 10:
            p.side_quests['merc_hunt'] = 2
            p.stats.gold += 300
            g.message_queue.append(("【支线完成】佣兵委托！获得300信用点！", 180))

    # 支线：逃亡工人 - 失踪工人
    if npc.name == '逃亡工人':
        sq = p.side_quests.get('missing_worker', 0)
        if sq == 0:
            p.side_quests['missing_worker'] = 1
            g.message_queue.append(("【支线】失踪工人：在工厂找到工人证件", 150))
        elif sq == 1 and p.has_item('worker_id'):
            p.remove_item('worker_id')
            p.side_quests['missing_worker'] = 2
            p.stats.exp += 60
            p.add_item('hp_potion', 5)
            g.message_queue.append(("【支线完成】失踪工人！获得60EXP+纳米修复剂x5！", 180))

    # 支线：线人·影子 - 黑市通行证
    if npc.name == '线人·影子':
        sq = p.side_quests.get('black_market_pass', 0)
        if sq == 0:
            p.side_quests['black_market_pass'] = 1
            g.message_queue.append(("【支线】黑市通行证：收集3个加密数据", 150))
        elif sq == 1 and p.item_count('encrypted_data') >= 3:
            p.remove_item('encrypted_data', 3)
            p.side_quests['black_market_pass'] = 2
            p.quest_flags['black_market_open'] = True
            g.message_queue.append(("【支线完成】黑市通行证！霓虹街黑市入口已解锁！", 180))

    # v0.13 新NPC交互
    if npc.name == '竞技场管理员':
        g._start_arena()
        return
    if npc.name == '宠物训练师':
        if not p.active_pet:
            g.message_queue.append(("你需要先装备一只宠物！", 90))
        else:
            g._start_pet_battle()
            return
    if npc.name == '改造工匠':
        from game import GameState
        g.state = GameState.CRAFTING
        g.craft_index = 0
        return
    if npc.name == '每日挑战终端':
        g._start_daily_challenge()
        return
    if npc.name == '入侵终端':
        g._start_hacking()
        return
    if npc.name == '据点管理员':
        from game import GameState
        g.state = GameState.HOME_DECOR
        g.home_decor_index = 0
        return

    g.dialogue.start(npc, p.quest_stage)


def handle_romance_interact(g, npc):
    """处理恋爱NPC交互"""
    p = g.player
    # 找到对应的RomanceChar
    rc = None
    for char_id, rchar in ROMANCE_CHARS.items():
        if rchar.name == npc.name:
            rc = rchar
            break
    if not rc:
        return

    char_id = rc.char_id
    aff = p.get_affection(char_id)

    # 已有伴侣且不是这个角色
    if p.partner and p.partner != char_id:
        npc.dialogues = ["你已经有伴侣了...祝你们幸福。"]
        g.dialogue.start(npc, 0)
        return

    # 已是伴侣 - 显示对话+送礼选项
    if p.partner == char_id:
        # 设置对话
        best_aff = -1
        best_lines = rc.affection_dialogues.get(0, ["..."])
        for threshold, lines in sorted(rc.affection_dialogues.items()):
            if threshold <= p.get_affection(char_id) and threshold > best_aff:
                best_aff = threshold
                best_lines = lines
        npc.dialogues = best_lines + ["（按G送礼）"]
        g.gift_char_id = char_id
        g.dialogue.start(npc, 0)
        return

    # 增加好感度（每次交互+5）
    new_aff = p.add_affection(char_id, 5)
    if new_aff != aff:
        g.message_queue.append((f"♥ {rc.name} 好感度 +5 ({new_aff}/100)", 90))

    # 检查剧情事件
    event = p.check_romance_event(char_id)
    if event:
        threshold, desc, reward_type = event
        p.mark_romance_event(char_id, threshold)
        g.message_queue.append((f"【剧情】{desc}", 180))
        # 给奖励
        if reward_type == 'exp':
            p.stats.exp += 50
            g.message_queue.append(("获得 50 EXP！", 90))
        elif reward_type == 'item':
            p.add_item('hp_potion', 3)
            g.message_queue.append(("获得 纳米修复剂 x3！", 90))
        elif reward_type == 'stat':
            p.stats.max_hp += 10
            p.stats.hp += 10
            g.message_queue.append(("最大HP +10！", 90))
        elif reward_type == 'skill':
            p.skill_points += 1
            g.message_queue.append(("获得 1 技能点！", 90))

    # 好感度达到80，触发告白选择
    if new_aff >= 80 and not p.partner:
        g.romance_choice_active = True
        g.romance_choice_char = char_id
        g.romance_choice_index = 0

    # 设置对话
    best_aff = -1
    best_lines = rc.affection_dialogues.get(0, ["..."])
    for threshold, lines in sorted(rc.affection_dialogues.items()):
        if threshold <= new_aff and threshold > best_aff:
            best_aff = threshold
            best_lines = lines
    npc.dialogues = best_lines + ["（按G送礼）"]
    g.gift_char_id = char_id
    g.dialogue.start(npc, 0)


def handle_gift_input(g, event):
    """送礼界面输入处理"""
    if event.type != pygame.KEYDOWN:
        return
    giftable = [(k, c) for k, c in g.player.inventory
                 if ITEMS_DB[k].item_type == 'material']
    if not giftable:
        g.gift_mode = False
        return
    if event.key in (pygame.K_ESCAPE, pygame.K_x):
        g.gift_mode = False
    elif event.key == pygame.K_UP:
        g.gift_index = (g.gift_index - 1) % len(giftable)
    elif event.key == pygame.K_DOWN:
        g.gift_index = (g.gift_index + 1) % len(giftable)
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        if g.gift_index < len(giftable):
            item_key, cnt = giftable[g.gift_index]
            char_id = g.gift_char_id
            rc = ROMANCE_CHARS.get(char_id)
            if rc:
                delta, reaction = g.player.gift_to_partner_char(char_id, item_key)
                item_name = ITEMS_DB[item_key].name
                aff = g.player.get_affection(char_id)
                if reaction == 'liked':
                    g.message_queue.append((f"♥ {rc.name}非常喜欢{item_name}！好感度+{delta} ({aff}/100)", 120))
                elif reaction == 'disliked':
                    g.message_queue.append((f"♥ {rc.name}不太喜欢{item_name}... 好感度{delta} ({aff}/100)", 120))
                else:
                    g.message_queue.append((f"♥ {rc.name}收下了{item_name}。好感度+{delta} ({aff}/100)", 120))
                # 检查剧情事件
                event_data = g.player.check_romance_event(char_id)
                if event_data:
                    threshold, desc, reward_type = event_data
                    g.player.mark_romance_event(char_id, threshold)
                    g.message_queue.append((f"【剧情】{desc}", 180))
                # 检查告白
                if aff >= 80 and not g.player.partner:
                    g.romance_choice_active = True
                    g.romance_choice_char = char_id
                    g.romance_choice_index = 0
            g.gift_mode = False
            g.gift_char_id = None
