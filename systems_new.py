"""v0.15 新系统 — 黑客入侵 / 装备合成 / 任务链 / 竞技场 / 每日挑战 / 宠物对战 / 家园装饰 / NG+"""

import pygame
import random
import math
import datetime
from constants import (SCREEN_W, SCREEN_H, TILE, C_WHITE, C_YELLOW, C_RED, C_GREEN,
                       C_GOLD, C_PANEL, C_PANEL_BORDER, C_HP_BAR, C_MP_BAR,
                       C_NEON_CYAN, C_NEON_PINK, C_NEON_PURPLE,
                       draw_pixel_rect, draw_text, draw_bar)
from entities import (ITEMS_DB, HACK_WORDS, CRAFT_RECIPES, AFFIXES,
                      QUEST_CHAINS, ARENA_WAVES, DAILY_MODIFIERS,
                      PET_BATTLE_MOVES, PET_BATTLE_NPCS, FURNITURE_DB,
                      ENEMY_DEFS, ENCOUNTER_TABLE)
from combat import Combat, CombatState


# ============================================================
# 1. 黑客入侵小游戏 (Wordle风格终端解谜)
# ============================================================

def start_hacking(g):
    """初始化黑客入侵小游戏"""
    g.hack_word = random.choice(HACK_WORDS)
    g.hack_guess = ''
    g.hack_attempts = 4
    g.hack_feedback = []
    # 随机奖励
    rewards = [
        ('gold', random.randint(50, 150)),
        ('data_sample', random.randint(1, 3)),
        ('encrypted_data', 1),
        ('quantum_chip', 1),
    ]
    g.hack_reward = random.choice(rewards)
    from game import GameState
    g.state = GameState.HACKING


def handle_hacking_event(g, event):
    """处理黑客入侵输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return

    if event.key == pygame.K_ESCAPE:
        g.state = GameState.EXPLORE
        return

    # 已经结束（成功或失败后按任意键退出）
    if g.hack_attempts <= 0 or (g.hack_feedback and g.hack_feedback[-1][1] == 'GGGGGG'):
        if event.key in (pygame.K_RETURN, pygame.K_j):
            g.state = GameState.EXPLORE
        return

    # 输入字母
    if event.key == pygame.K_BACKSPACE:
        g.hack_guess = g.hack_guess[:-1]
    elif event.key == pygame.K_RETURN or event.key == pygame.K_j:
        if len(g.hack_guess) == len(g.hack_word):
            _check_hack_guess(g)
    elif len(g.hack_guess) < len(g.hack_word):
        ch = event.unicode.upper()
        if ch.isalpha():
            g.hack_guess += ch


def _check_hack_guess(g):
    """检查猜测结果"""
    word = g.hack_word
    guess = g.hack_guess
    result = ''
    # G=正确位置(绿), Y=存在但位置错(黄), X=不存在(灰)
    word_chars = list(word)
    # 第一遍：标记完全匹配
    temp = ['X'] * len(word)
    used = [False] * len(word)
    for i in range(len(word)):
        if guess[i] == word[i]:
            temp[i] = 'G'
            used[i] = True
    # 第二遍：标记存在但位置错
    for i in range(len(word)):
        if temp[i] == 'G':
            continue
        for j in range(len(word)):
            if not used[j] and guess[i] == word[j]:
                temp[i] = 'Y'
                used[j] = True
                break
    result = ''.join(temp)
    g.hack_feedback.append((guess, result))
    g.hack_guess = ''

    if result == 'G' * len(word):
        # 成功！给予奖励
        reward_key, reward_val = g.hack_reward
        if reward_key == 'gold':
            g.player.stats.gold += reward_val
            g.message_queue.append((f"入侵成功！获得 {reward_val} 信用点！", 120))
        else:
            g.player.add_item(reward_key, reward_val)
            name = ITEMS_DB[reward_key].name if reward_key in ITEMS_DB else reward_key
            g.message_queue.append((f"入侵成功！获得 {name} x{reward_val}！", 120))
    else:
        g.hack_attempts -= 1
        if g.hack_attempts <= 0:
            g.message_queue.append((f"入侵失败...正确答案是 {g.hack_word}", 120))


def draw_hacking(g):
    """绘制黑客入侵界面"""
    g.screen.fill((5, 8, 15))

    # 终端框
    pw, ph = 420, 400
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, (8, 15, 25), (px, py, pw, ph), 3, (0, 255, 100))

    # 标题
    draw_text(g.screen, "[ 终端入侵 ]", (SCREEN_W // 2, py + 16), g.assets.font_lg, (0, 255, 100), center=True)
    draw_text(g.screen, f"破解 {len(g.hack_word)} 位密码  剩余尝试: {g.hack_attempts}",
              (SCREEN_W // 2, py + 46), g.assets.font_sm, (0, 200, 80), center=True)

    # 已有猜测反馈
    fy = py + 75
    for guess, result in g.hack_feedback:
        _draw_hack_row(g, px + 30, fy, guess, result)
        fy += 36

    # 当前输入行
    if g.hack_attempts > 0 and not (g.hack_feedback and g.hack_feedback[-1][1] == 'G' * len(g.hack_word)):
        _draw_hack_input(g, px + 30, fy)
        fy += 50
        draw_text(g.screen, "输入字母后按 Enter 确认",
                  (SCREEN_W // 2, fy), g.assets.font_sm, (0, 150, 60), center=True)
    else:
        # 结果
        fy += 10
        if g.hack_feedback and g.hack_feedback[-1][1] == 'G' * len(g.hack_word):
            draw_text(g.screen, ">> ACCESS GRANTED <<",
                      (SCREEN_W // 2, fy), g.assets.font_lg, (0, 255, 100), center=True)
            fy += 30
            rk, rv = g.hack_reward
            if rk == 'gold':
                draw_text(g.screen, f"奖励: {rv} 信用点",
                          (SCREEN_W // 2, fy), g.assets.font_md, C_GOLD, center=True)
            else:
                name = ITEMS_DB[rk].name if rk in ITEMS_DB else rk
                draw_text(g.screen, f"奖励: {name} x{rv}",
                          (SCREEN_W // 2, fy), g.assets.font_md, C_GOLD, center=True)
        else:
            draw_text(g.screen, ">> ACCESS DENIED <<",
                      (SCREEN_W // 2, fy), g.assets.font_lg, C_RED, center=True)
            fy += 30
            draw_text(g.screen, f"密码: {g.hack_word}",
                      (SCREEN_W // 2, fy), g.assets.font_md, (200, 60, 60), center=True)
        fy += 30
        draw_text(g.screen, "[Enter] 离开",
                  (SCREEN_W // 2, fy), g.assets.font_sm, (0, 150, 60), center=True)

    # 扫描线效果
    t = pygame.time.get_ticks()
    scan_y = (t // 8) % SCREEN_H
    pygame.draw.line(g.screen, (0, 255, 100, 15), (0, scan_y), (SCREEN_W, scan_y))


def _draw_hack_row(g, x, y, guess, result):
    """绘制一行猜测结果"""
    for i, (ch, r) in enumerate(zip(guess, result)):
        bx = x + i * 56
        if r == 'G':
            color = (0, 200, 80)
            bg = (0, 60, 20)
        elif r == 'Y':
            color = (255, 220, 50)
            bg = (60, 50, 0)
        else:
            color = (100, 100, 100)
            bg = (25, 25, 30)
        draw_pixel_rect(g.screen, bg, (bx, y, 48, 30), 2, color)
        draw_text(g.screen, ch, (bx + 24, y + 5), g.assets.font_md, color, center=True)


def _draw_hack_input(g, x, y):
    """绘制当前输入行"""
    word_len = len(g.hack_word)
    for i in range(word_len):
        bx = x + i * 56
        ch = g.hack_guess[i] if i < len(g.hack_guess) else '_'
        blink = (pygame.time.get_ticks() // 400) % 2 == 0
        border_c = (0, 255, 100) if (i == len(g.hack_guess) and blink) else (0, 100, 50)
        draw_pixel_rect(g.screen, (10, 20, 15), (bx, y, 48, 30), 2, border_c)
        draw_text(g.screen, ch, (bx + 24, y + 5), g.assets.font_md, (0, 255, 100), center=True)


# ============================================================
# 2. 装备合成系统
# ============================================================

def handle_crafting_event(g, event):
    """处理装备合成输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return
    recipes = list(CRAFT_RECIPES.values())
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
        g.state = GameState.EXPLORE
    elif event.key == pygame.K_UP:
        g.craft_index = (g.craft_index - 1) % len(recipes)
    elif event.key == pygame.K_DOWN:
        g.craft_index = (g.craft_index + 1) % len(recipes)
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        _do_craft(g, recipes[g.craft_index])


def _do_craft(g, recipe):
    """执行合成"""
    # 检查材料
    for mat_key, mat_count in recipe.materials.items():
        have = sum(c for k, c in g.player.inventory if k == mat_key)
        if have < mat_count:
            name = ITEMS_DB[mat_key].name if mat_key in ITEMS_DB else mat_key
            g.message_queue.append((f"材料不足: {name} 需要{mat_count}个", 90))
            return
    # 扣除材料
    for mat_key, mat_count in recipe.materials.items():
        g.player.remove_item(mat_key, mat_count)
    # 生成装备
    g.player.add_item(recipe.result_key, 1)
    result_name = ITEMS_DB[recipe.result_key].name if recipe.result_key in ITEMS_DB else recipe.result_key
    # 随机词缀
    if recipe.has_random_affix:
        prefix_name, prefix_bonus = random.choice(AFFIXES['prefix'])
        suffix_name, suffix_bonus = random.choice(AFFIXES['suffix'])
        total_bonus = {}
        for k, v in prefix_bonus.items():
            total_bonus[k] = total_bonus.get(k, 0) + v
        for k, v in suffix_bonus.items():
            total_bonus[k] = total_bonus.get(k, 0) + v
        affix_name = f"{prefix_name}{result_name}{suffix_name}"
        g.player.crafted_affixes[recipe.result_key] = {
            'prefix': prefix_name, 'suffix': suffix_name,
            'display_name': affix_name,
            'bonus_atk': total_bonus.get('atk_bonus', 0),
            'bonus_def': total_bonus.get('def_bonus', 0),
            'bonus_hp': total_bonus.get('hp_restore', 0),
        }
        g.message_queue.append((f"合成成功！{affix_name} (ATK+{total_bonus.get('atk_bonus', 0)} DEF+{total_bonus.get('def_bonus', 0)})", 120))
    else:
        g.message_queue.append((f"合成成功！获得 {result_name}！", 120))


def draw_crafting(g):
    """绘制装备合成界面"""
    g.screen.fill(C_PANEL)
    pw, ph = 440, 380
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, C_PANEL, (px, py, pw, ph), 3, C_PANEL_BORDER)

    draw_text(g.screen, "【装备合成】", (SCREEN_W // 2, py + 16), g.assets.font_lg, C_GOLD, center=True)
    draw_text(g.screen, "[ESC]返回  [↑↓]选择  [Enter]合成",
              (SCREEN_W // 2, py + 46), g.assets.font_sm, (120, 120, 140), center=True)

    recipes = list(CRAFT_RECIPES.values())
    ry = py + 70
    for i, recipe in enumerate(recipes):
        selected = (i == g.craft_index)
        color = C_YELLOW if selected else C_WHITE
        prefix = ">> " if selected else "   "
        draw_text(g.screen, f"{prefix}{recipe.name}", (px + 20, ry), g.assets.font_md, color)

        # 材料列表
        mat_strs = []
        for mat_key, mat_count in recipe.materials.items():
            have = sum(c for k, c in g.player.inventory if k == mat_key)
            name = ITEMS_DB[mat_key].name if mat_key in ITEMS_DB else mat_key
            c = C_GREEN if have >= mat_count else C_RED
            mat_strs.append((f"{name}:{have}/{mat_count}", c))

        mx = px + 40
        for ms, mc in mat_strs:
            draw_text(g.screen, ms, (mx, ry + 22), g.assets.font_sm, mc)
            mx += 130

        # 已有词缀显示
        if recipe.result_key in g.player.crafted_affixes:
            affix = g.player.crafted_affixes[recipe.result_key]
            draw_text(g.screen, f"已有: {affix['display_name']}",
                      (px + 40, ry + 40), g.assets.font_sm, C_NEON_CYAN)

        ry += 62


# ============================================================
# 3. 竞技场系统
# ============================================================

def start_arena(g):
    """开始竞技场挑战"""
    from game import GameState
    g.arena_wave = 1
    g.arena_active = True
    g.arena_hp_saved = g.player.stats.hp
    g.arena_mp_saved = g.player.stats.mp
    _start_arena_wave(g)


def _start_arena_wave(g):
    """开始竞技场当前波次"""
    from game import GameState
    wave_enemies = ARENA_WAVES.get(g.arena_wave)
    if not wave_enemies:
        _arena_victory(g)
        return
    enemy_key = random.choice(wave_enemies)
    g.combat = Combat(g.player, enemy_key, g.assets)
    g.state = GameState.ARENA


def on_arena_combat_end(g):
    """竞技场战斗结束回调"""
    from game import GameState
    if not g.combat:
        g.state = GameState.EXPLORE
        g.arena_active = False
        return

    if g.combat.state == CombatState.VICTORY:
        # 波次奖励
        wave_gold = 20 + g.arena_wave * 15
        g.player.stats.gold += wave_gold
        g.message_queue.append((f"Wave {g.arena_wave} 通过！+{wave_gold}G", 90))

        # 每波回复少量HP/MP
        g.player.stats.hp = min(g.player.stats.max_hp,
                                g.player.stats.hp + g.player.stats.max_hp // 10)
        g.player.stats.mp = min(g.player.stats.max_mp,
                                g.player.stats.mp + g.player.stats.max_mp // 5)

        g.arena_wave += 1
        if g.arena_wave > len(ARENA_WAVES):
            _arena_victory(g)
        else:
            _start_arena_wave(g)
    elif g.combat.state == CombatState.DEFEAT:
        _arena_defeat(g)
    else:
        # 逃跑
        _arena_defeat(g)


def _arena_victory(g):
    """竞技场全部通关"""
    from game import GameState
    g.arena_active = False
    g.combat = None
    bonus_gold = 300
    g.player.stats.gold += bonus_gold
    if g.arena_wave - 1 > g.player.arena_best_wave:
        g.player.arena_best_wave = g.arena_wave - 1
    g.message_queue.append((f"竞技场全部通关！奖励 {bonus_gold}G！", 150))
    g.message_queue.append((f"最佳记录: Wave {g.player.arena_best_wave}", 120))
    g.state = GameState.EXPLORE


def _arena_defeat(g):
    """竞技场失败"""
    from game import GameState
    g.arena_active = False
    reached = g.arena_wave
    if reached > g.player.arena_best_wave:
        g.player.arena_best_wave = reached
    # 恢复进场时的HP/MP（不惩罚）
    g.player.stats.hp = max(1, g.arena_hp_saved)
    g.player.stats.mp = g.arena_mp_saved
    g.combat = None
    g.message_queue.append((f"竞技场结束！到达 Wave {reached}", 120))
    g.message_queue.append((f"最佳记录: Wave {g.player.arena_best_wave}", 90))
    g.state = GameState.EXPLORE


# ============================================================
# 4. 每日挑战系统
# ============================================================

def start_daily_challenge(g):
    """开始每日挑战"""
    from game import GameState
    today = datetime.date.today().isoformat()
    if g.player.daily_completed_date == today:
        g.message_queue.append(("今天的挑战已完成，明天再来！", 90))
        return

    g.daily_modifier = random.choice(DAILY_MODIFIERS)
    g.daily_active = True

    # 选择敌人（根据玩家等级）
    lv = g.player.stats.level
    if lv < 5:
        enemy_key = random.choice(['slime', 'bat', 'skeleton'])
    elif lv < 10:
        enemy_key = random.choice(['glitch_bot', 'cyber_virus', 'factory_guard'])
    else:
        enemy_key = random.choice(['data_ghost', 'darknet_guard', 'security_drone'])

    g.combat = Combat(g.player, enemy_key, g.assets)

    # 应用修饰符效果
    mod = g.daily_modifier
    eff = mod.effect
    if 'hp_set' in eff:
        g.combat.player.stats.hp = eff['hp_set']
    if 'atk_mult' in eff:
        g.combat.player.stats.atk = int(g.combat.player.stats.atk * eff['atk_mult'])
    if 'enemy_hp_mult' in eff:
        g.combat.enemy_hp = int(g.combat.enemy_hp * eff['enemy_hp_mult'])
        g.combat.enemy_max_hp = g.combat.enemy_hp
    if 'enemy_atk_mult' in eff:
        g.combat.enemy_atk = int(g.combat.enemy_atk * eff['enemy_atk_mult'])

    g.state = GameState.DAILY_CHALLENGE
    g.message_queue.append((f"每日挑战: {mod.name} — {mod.description}", 120))


def on_daily_combat_end(g):
    """每日挑战战斗结束"""
    from game import GameState
    if not g.combat:
        g.state = GameState.EXPLORE
        g.daily_active = False
        return

    today = datetime.date.today().isoformat()
    if g.combat.state == CombatState.VICTORY:
        g.player.daily_completed_date = today
        g.player.daily_streak += 1
        if g.player.daily_streak > g.player.daily_best_streak:
            g.player.daily_best_streak = g.player.daily_streak
        # 奖励
        reward_gold = 100 + g.player.daily_streak * 20
        g.player.stats.gold += reward_gold
        g.player.add_item('data_sample', 2)
        g.message_queue.append((f"每日挑战完成！+{reward_gold}G +数据样本x2", 120))
        g.message_queue.append((f"连胜: {g.player.daily_streak} 最佳: {g.player.daily_best_streak}", 90))
    else:
        g.player.daily_streak = 0
        g.message_queue.append(("每日挑战失败...", 90))

    g.daily_active = False
    g.combat = None
    g.state = GameState.EXPLORE


# ============================================================
# 5. NPC任务链系统
# ============================================================

def handle_quest_chain_event(g, event):
    """处理任务链界面输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return
    chains = list(QUEST_CHAINS.values())
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
        g.state = GameState.MENU
    elif event.key == pygame.K_UP:
        idx = _get_chain_index(g)
        idx = (idx - 1) % (len(chains) + 1)  # +1 for "back"
        _set_chain_index(g, idx, chains)
    elif event.key == pygame.K_DOWN:
        idx = _get_chain_index(g)
        idx = (idx + 1) % (len(chains) + 1)
        _set_chain_index(g, idx, chains)
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        idx = _get_chain_index(g)
        if idx < len(chains):
            chain = chains[idx]
            _try_accept_or_advance_chain(g, chain)


def _get_chain_index(g):
    if not hasattr(g, '_quest_chain_idx'):
        g._quest_chain_idx = 0
    return g._quest_chain_idx


def _set_chain_index(g, idx, chains):
    g._quest_chain_idx = idx
    if idx < len(chains):
        g.quest_chain_id = chains[idx].chain_id
    else:
        g.quest_chain_id = ''


def _try_accept_or_advance_chain(g, chain):
    """尝试接受或推进任务链"""
    p = g.player
    aff = p.get_affection(chain.char_id)
    if aff < chain.required_affection:
        from entities import ROMANCE_CHARS
        rc = ROMANCE_CHARS.get(chain.char_id)
        name = rc.name if rc else chain.char_id
        g.message_queue.append((f"需要与{name}好感度≥{chain.required_affection}（当前:{aff}）", 120))
        return

    chain_state = p.quest_chains.get(chain.chain_id)
    if chain_state and chain_state.get('done'):
        g.message_queue.append(("该任务链已完成！", 90))
        return

    if not chain_state:
        # 接受任务链
        p.quest_chains[chain.chain_id] = {'step': 0, 'progress': 0, 'done': False}
        step = chain.steps[0]
        g.message_queue.append((f"接受任务: {chain.name}", 120))
        g.message_queue.append((f"目标: {step.description}", 120))
    else:
        # 检查当前步骤是否完成
        step_idx = chain_state['step']
        if step_idx >= len(chain.steps):
            return
        step = chain.steps[step_idx]
        progress = chain_state['progress']
        if step.objective_type == 'collect':
            have = sum(c for k, c in p.inventory if k == step.target)
            progress = have
            chain_state['progress'] = progress
        elif step.objective_type == 'visit':
            if p.area == step.target:
                progress = 1
                chain_state['progress'] = 1

        if progress >= step.target_count:
            # 完成当前步骤
            if step.objective_type == 'collect':
                p.remove_item(step.target, step.target_count)
            chain_state['step'] += 1
            chain_state['progress'] = 0
            if chain_state['step'] >= len(chain.steps):
                # 任务链完成！
                chain_state['done'] = True
                rewards = chain.rewards
                if 'gold' in rewards:
                    p.stats.gold += rewards['gold']
                if 'exp' in rewards:
                    p.stats.exp += rewards['exp']
                if 'item' in rewards:
                    item_key, count = rewards['item']
                    p.add_item(item_key, count)
                    name = ITEMS_DB[item_key].name if item_key in ITEMS_DB else item_key
                    g.message_queue.append((f"任务链完成！获得 {name}！", 150))
                g.message_queue.append((f"{chain.name} 全部完成！", 120))
            else:
                next_step = chain.steps[chain_state['step']]
                g.message_queue.append((f"步骤完成！下一步: {next_step.description}", 120))
        else:
            g.message_queue.append((f"进度: {progress}/{step.target_count}", 90))


def draw_quest_chain(g):
    """绘制任务链界面"""
    g.screen.fill(C_PANEL)
    pw, ph = 460, 420
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, C_PANEL, (px, py, pw, ph), 3, C_PANEL_BORDER)

    draw_text(g.screen, "【角色任务链】", (SCREEN_W // 2, py + 16), g.assets.font_lg, C_GOLD, center=True)
    draw_text(g.screen, "[ESC]返回  [↑↓]选择  [Enter]接受/推进",
              (SCREEN_W // 2, py + 44), g.assets.font_sm, (120, 120, 140), center=True)

    chains = list(QUEST_CHAINS.values())
    idx = _get_chain_index(g)
    ry = py + 70

    for i, chain in enumerate(chains):
        selected = (i == idx)
        from entities import ROMANCE_CHARS
        rc = ROMANCE_CHARS.get(chain.char_id)
        char_name = rc.name if rc else chain.char_id

        # 状态
        chain_state = g.player.quest_chains.get(chain.chain_id)
        aff = g.player.get_affection(chain.char_id)

        if chain_state and chain_state.get('done'):
            status = "✓ 已完成"
            status_c = C_GREEN
        elif chain_state:
            step_idx = chain_state['step']
            step = chain.steps[step_idx] if step_idx < len(chain.steps) else None
            status = f"进行中 ({step_idx + 1}/{len(chain.steps)})"
            status_c = C_NEON_CYAN
        elif aff >= chain.required_affection:
            status = "可接受"
            status_c = C_YELLOW
        else:
            status = f"需好感≥{chain.required_affection} (当前:{aff})"
            status_c = (100, 100, 100)

        color = C_YELLOW if selected else C_WHITE
        prefix = ">> " if selected else "   "
        draw_text(g.screen, f"{prefix}{char_name}: {chain.name}", (px + 20, ry), g.assets.font_md, color)
        draw_text(g.screen, status, (px + 40, ry + 22), g.assets.font_sm, status_c)

        # 当前步骤详情
        if selected and chain_state and not chain_state.get('done'):
            step_idx = chain_state['step']
            if step_idx < len(chain.steps):
                step = chain.steps[step_idx]
                progress = chain_state['progress']
                if step.objective_type == 'collect':
                    have = sum(c for k, c in g.player.inventory if k == step.target)
                    progress = have
                draw_text(g.screen, f"  → {step.description} [{progress}/{step.target_count}]",
                          (px + 40, ry + 40), g.assets.font_sm, C_NEON_PINK)

        ry += 65


# ============================================================
# 6. 宠物对战系统
# ============================================================

def start_pet_battle(g):
    """开始宠物对战"""
    from game import GameState
    if not g.player.active_pet:
        g.message_queue.append(("你需要先装备一只宠物！", 90))
        return
    g.pet_battle_npc_idx = 0
    g.pet_battle_state = 'choose'
    g.pet_battle_move_idx = 0
    g.pet_battle_msg = ''
    g.pet_battle_turn = 'player'
    g.state = GameState.PET_BATTLE


def handle_pet_battle_event(g, event):
    """处理宠物对战输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return

    if event.key == pygame.K_ESCAPE:
        if g.pet_battle_state == 'choose':
            g.state = GameState.EXPLORE
        elif g.pet_battle_state == 'result':
            g.state = GameState.EXPLORE
        return

    if g.pet_battle_state == 'choose':
        npcs = PET_BATTLE_NPCS
        if event.key == pygame.K_UP:
            g.pet_battle_npc_idx = (g.pet_battle_npc_idx - 1) % len(npcs)
        elif event.key == pygame.K_DOWN:
            g.pet_battle_npc_idx = (g.pet_battle_npc_idx + 1) % len(npcs)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            _init_pet_fight(g)

    elif g.pet_battle_state == 'fight':
        if g.pet_battle_turn != 'player':
            return
        from entities import PET_BATTLE_MOVES, PETS_DB
        pet_id = g.player.active_pet
        moves = PET_BATTLE_MOVES.get(pet_id, [])
        if not moves:
            g.message_queue.append(("该宠物没有战斗技能！", 90))
            g.pet_battle_state = 'result'
            return

        if event.key == pygame.K_UP:
            g.pet_battle_move_idx = (g.pet_battle_move_idx - 1) % len(moves)
        elif event.key == pygame.K_DOWN:
            g.pet_battle_move_idx = (g.pet_battle_move_idx + 1) % len(moves)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            _execute_pet_move(g, moves[g.pet_battle_move_idx])

    elif g.pet_battle_state == 'result':
        if event.key in (pygame.K_RETURN, pygame.K_j):
            g.state = GameState.EXPLORE


def _init_pet_fight(g):
    """初始化宠物战斗"""
    from entities import PETS_DB
    npc = PET_BATTLE_NPCS[g.pet_battle_npc_idx]
    pet_id = g.player.active_pet
    pet = PETS_DB.get(pet_id)
    if not pet:
        return

    pet_level = g.player.pet_levels.get(pet_id, 1)
    g.pet_battle_pet_max_hp = 30 + pet_level * 10
    g.pet_battle_pet_hp = g.pet_battle_pet_max_hp
    g.pet_battle_enemy_hp = npc.hp
    g.pet_battle_enemy_max_hp = npc.hp
    g.pet_battle_state = 'fight'
    g.pet_battle_turn = 'player'
    g.pet_battle_move_idx = 0
    g.pet_battle_msg = f"对战 {npc.npc_name} 的 {npc.pet_name}！"


def _execute_pet_move(g, move):
    """执行宠物技能"""
    npc = PET_BATTLE_NPCS[g.pet_battle_npc_idx]
    pet_level = g.player.pet_levels.get(g.player.active_pet, 1)
    level_bonus = pet_level * 2

    if move.move_type == 'attack':
        dmg = max(1, move.power + level_bonus - npc.defense)
        g.pet_battle_enemy_hp -= dmg
        g.pet_battle_msg = f"使用 {move.name}！造成 {dmg} 伤害！"
    elif move.move_type == 'heal':
        heal = move.power + level_bonus
        g.pet_battle_pet_hp = min(g.pet_battle_pet_max_hp, g.pet_battle_pet_hp + heal)
        g.pet_battle_msg = f"使用 {move.name}！回复 {heal} HP！"
    elif move.move_type == 'buff':
        level_bonus += move.power
        g.pet_battle_msg = f"使用 {move.name}！攻击力提升！"
    elif move.move_type == 'debuff':
        npc_atk_reduce = move.power
        g.pet_battle_msg = f"使用 {move.name}！降低敌方攻击！"

    # 检查敌方是否倒下
    if g.pet_battle_enemy_hp <= 0:
        g.pet_battle_enemy_hp = 0
        _pet_battle_victory(g)
        return

    # 敌方回合
    g.pet_battle_turn = 'enemy'
    _enemy_pet_turn(g)


def _enemy_pet_turn(g):
    """敌方宠物回合"""
    npc = PET_BATTLE_NPCS[g.pet_battle_npc_idx]
    move = random.choice(npc.moves)

    if move.move_type == 'attack':
        dmg = max(1, move.power)
        g.pet_battle_pet_hp -= dmg
        g.pet_battle_msg += f"\n对方 {move.name}！受到 {dmg} 伤害！"
    elif move.move_type == 'heal':
        heal = move.power
        g.pet_battle_enemy_hp = min(g.pet_battle_enemy_max_hp, g.pet_battle_enemy_hp + heal)
        g.pet_battle_msg += f"\n对方 {move.name}！回复 {heal} HP！"
    elif move.move_type == 'buff':
        g.pet_battle_msg += f"\n对方 {move.name}！"

    # 检查我方是否倒下
    if g.pet_battle_pet_hp <= 0:
        g.pet_battle_pet_hp = 0
        _pet_battle_defeat(g)
        return

    g.pet_battle_turn = 'player'


def _pet_battle_victory(g):
    """宠物对战胜利"""
    npc = PET_BATTLE_NPCS[g.pet_battle_npc_idx]
    g.pet_battle_state = 'result'
    g.player.pet_battle_wins += 1
    g.player.pet_battle_defeated.add(npc.npc_name)
    g.player.stats.gold += npc.reward_gold
    # 宠物经验
    pet_id = g.player.active_pet
    g.player.pet_exp[pet_id] = g.player.pet_exp.get(pet_id, 0) + 20
    # 检查升级
    pet_lv = g.player.pet_levels.get(pet_id, 1)
    if g.player.pet_exp.get(pet_id, 0) >= pet_lv * 30:
        g.player.pet_exp[pet_id] -= pet_lv * 30
        g.player.pet_levels[pet_id] = pet_lv + 1
        g.pet_battle_msg = f"胜利！+{npc.reward_gold}G 宠物升级到 Lv{pet_lv + 1}！"
    else:
        g.pet_battle_msg = f"胜利！+{npc.reward_gold}G +20宠物EXP"
    if npc.reward_item:
        item_key, count = npc.reward_item
        g.player.add_item(item_key, count)
        name = ITEMS_DB[item_key].name if item_key in ITEMS_DB else item_key
        g.pet_battle_msg += f" +{name}x{count}"


def _pet_battle_defeat(g):
    """宠物对战失败"""
    g.pet_battle_state = 'result'
    g.pet_battle_msg = "宠物倒下了...对战失败"


def draw_pet_battle(g):
    """绘制宠物对战界面"""
    g.screen.fill(C_PANEL)
    pw, ph = 460, 400
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, C_PANEL, (px, py, pw, ph), 3, C_NEON_CYAN)

    draw_text(g.screen, "【宠物对战】", (SCREEN_W // 2, py + 16), g.assets.font_lg, C_NEON_CYAN, center=True)

    if g.pet_battle_state == 'choose':
        draw_text(g.screen, "[ESC]返回  [↑↓]选择  [Enter]挑战",
                  (SCREEN_W // 2, py + 44), g.assets.font_sm, (120, 120, 140), center=True)
        ry = py + 70
        for i, npc in enumerate(PET_BATTLE_NPCS):
            selected = (i == g.pet_battle_npc_idx)
            color = C_YELLOW if selected else C_WHITE
            prefix = ">> " if selected else "   "
            defeated = "✓" if npc.npc_name in g.player.pet_battle_defeated else " "
            draw_text(g.screen, f"{prefix}{defeated} {npc.npc_name} ({npc.pet_name})",
                      (px + 20, ry), g.assets.font_md, color)
            draw_text(g.screen, f"   HP:{npc.hp} ATK:{npc.atk} DEF:{npc.defense}  奖励:{npc.reward_gold}G",
                      (px + 40, ry + 22), g.assets.font_sm, (140, 140, 160))
            ry += 50

    elif g.pet_battle_state == 'fight':
        from entities import PETS_DB, PET_BATTLE_MOVES
        npc = PET_BATTLE_NPCS[g.pet_battle_npc_idx]
        pet = PETS_DB.get(g.player.active_pet)
        pet_name = pet.name if pet else '???'

        # 敌方信息
        ey = py + 55
        draw_text(g.screen, f"{npc.pet_name} (HP: {g.pet_battle_enemy_hp}/{g.pet_battle_enemy_max_hp})",
                  (px + 30, ey), g.assets.font_md, C_RED)
        draw_bar(g.screen, px + 30, ey + 24, 200, 12,
                 g.pet_battle_enemy_hp / max(1, g.pet_battle_enemy_max_hp), C_HP_BAR)

        # 我方信息
        my = py + 120
        draw_text(g.screen, f"{pet_name} (HP: {g.pet_battle_pet_hp}/{g.pet_battle_pet_max_hp})",
                  (px + 30, my), g.assets.font_md, C_NEON_CYAN)
        draw_bar(g.screen, px + 30, my + 24, 200, 12,
                 g.pet_battle_pet_hp / max(1, g.pet_battle_pet_max_hp), C_MP_BAR)

        # 消息
        msg_y = py + 180
        for line in g.pet_battle_msg.split('\n'):
            draw_text(g.screen, line, (px + 30, msg_y), g.assets.font_sm, C_WHITE)
            msg_y += 20

        # 技能选择
        if g.pet_battle_turn == 'player':
            moves = PET_BATTLE_MOVES.get(g.player.active_pet, [])
            sy = py + 250
            draw_text(g.screen, "选择技能:", (px + 30, sy), g.assets.font_sm, C_GOLD)
            sy += 22
            for i, m in enumerate(moves):
                selected = (i == g.pet_battle_move_idx)
                color = C_YELLOW if selected else C_WHITE
                prefix = ">> " if selected else "   "
                type_label = {'attack': '攻击', 'heal': '回复', 'buff': '增益', 'debuff': '减益'}.get(m.move_type, m.move_type)
                draw_text(g.screen, f"{prefix}{m.name} ({type_label} 威力:{m.power})",
                          (px + 30, sy), g.assets.font_sm, color)
                sy += 22

    elif g.pet_battle_state == 'result':
        ry = py + 100
        for line in g.pet_battle_msg.split('\n'):
            draw_text(g.screen, line, (SCREEN_W // 2, ry), g.assets.font_md, C_GOLD, center=True)
            ry += 28
        draw_text(g.screen, "[Enter] 离开", (SCREEN_W // 2, ry + 20), g.assets.font_sm, (120, 120, 140), center=True)


# ============================================================
# 7. 家园装饰系统
# ============================================================

def handle_home_decor_event(g, event):
    """处理家园装饰输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return
    furns = list(FURNITURE_DB.values())
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
        g.state = GameState.EXPLORE
    elif event.key == pygame.K_UP:
        g.home_decor_index = (g.home_decor_index - 1) % len(furns)
    elif event.key == pygame.K_DOWN:
        g.home_decor_index = (g.home_decor_index + 1) % len(furns)
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        furn = furns[g.home_decor_index]
        _buy_furniture(g, furn)


def _buy_furniture(g, furn):
    """购买家具"""
    if furn.furn_id in g.player.furniture:
        g.message_queue.append(("已经拥有该家具！", 90))
        return
    if g.player.stats.gold < furn.cost:
        g.message_queue.append((f"信用点不足！需要 {furn.cost}G", 90))
        return
    g.player.stats.gold -= furn.cost
    g.player.furniture.add(furn.furn_id)
    g.message_queue.append((f"购买了 {furn.name}！{furn.description}", 120))


def get_furniture_bonuses(player):
    """计算家具被动加成总和"""
    bonuses = {}
    for furn_id in player.furniture:
        furn = FURNITURE_DB.get(furn_id)
        if furn:
            for k, v in furn.passive.items():
                bonuses[k] = bonuses.get(k, 0) + v
    return bonuses


def draw_home_decor(g):
    """绘制家园装饰界面"""
    g.screen.fill(C_PANEL)
    pw, ph = 460, 420
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, C_PANEL, (px, py, pw, ph), 3, C_NEON_PINK)

    draw_text(g.screen, "【据点装饰】", (SCREEN_W // 2, py + 16), g.assets.font_lg, C_NEON_PINK, center=True)
    draw_text(g.screen, f"信用点: {g.player.stats.gold}G  [ESC]返回  [Enter]购买",
              (SCREEN_W // 2, py + 44), g.assets.font_sm, C_GOLD, center=True)

    furns = list(FURNITURE_DB.values())
    ry = py + 70
    for i, furn in enumerate(furns):
        selected = (i == g.home_decor_index)
        owned = furn.furn_id in g.player.furniture
        color = C_GREEN if owned else (C_YELLOW if selected else C_WHITE)
        prefix = ">> " if selected else "   "
        owned_mark = " ✓" if owned else ""
        draw_text(g.screen, f"{prefix}{furn.name} ({furn.cost}G){owned_mark}",
                  (px + 20, ry), g.assets.font_md, color)
        draw_text(g.screen, f"   {furn.description}",
                  (px + 40, ry + 22), g.assets.font_sm, (140, 140, 160))
        ry += 50

    # 当前加成总览
    bonuses = get_furniture_bonuses(g.player)
    if bonuses:
        by = py + ph - 50
        bonus_str = "  ".join(f"{k}+{v}" for k, v in bonuses.items())
        draw_text(g.screen, f"当前加成: {bonus_str}", (px + 20, by), g.assets.font_sm, C_NEON_CYAN)


# ============================================================
# 8. New Game+ 系统
# ============================================================

def handle_ng_plus_event(g, event):
    """处理NG+确认输入"""
    from game import GameState
    if event.type != pygame.KEYDOWN:
        return
    if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
        g.state = GameState.EXPLORE
        g.ng_plus_pending = False
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        if g.ng_plus_pending:
            _execute_ng_plus(g)


def _execute_ng_plus(g):
    """执行New Game+"""
    from game import GameState
    p = g.player
    ng_level = p.ng_plus + 1

    # 保留的数据
    kept_skills = set(p.unlocked_skills)
    kept_gold = p.stats.gold // 2  # 保留一半金币
    kept_pets = list(p.pets_owned)
    kept_pet_levels = dict(p.pet_levels)
    kept_furniture = set(p.furniture)
    kept_achievements = set(p.achievements)
    kept_crafted = dict(p.crafted_affixes)
    kept_fish = dict(p.fish_caught)
    kept_graffiti = set(p.graffiti_found)
    kept_arena = p.arena_best_wave
    kept_daily_streak = p.daily_best_streak

    # 重置玩家
    from game_map import AREA_VILLAGE
    p.__init__(20, 16)

    # 恢复保留数据
    p.ng_plus = ng_level
    p.unlocked_skills = kept_skills
    p.stats.gold = kept_gold
    p.pets_owned = kept_pets
    p.pet_levels = kept_pet_levels
    p.furniture = kept_furniture
    p.achievements = kept_achievements
    p.crafted_affixes = kept_crafted
    p.fish_caught = kept_fish
    p.graffiti_found = kept_graffiti
    p.arena_best_wave = kept_arena
    p.daily_best_streak = kept_daily_streak

    # NG+加成：敌人更强但经验更多
    p.stats.atk += ng_level * 2
    p.stats.defense += ng_level * 2
    p.stats.max_hp += ng_level * 20
    p.stats.hp = p.stats.max_hp
    p.stats.max_mp += ng_level * 10
    p.stats.mp = p.stats.max_mp

    # 重置游戏状态
    g.chests_opened = set()
    g.hidden_chests_opened = set()
    g.darknet_phase = 0
    g.combat = None
    g.ng_plus_pending = False
    g.state = GameState.EXPLORE

    g.message_queue.append((f"New Game+ {ng_level} 开始！", 150))
    g.message_queue.append(("保留了技能、宠物、家具、成就", 120))
    g.message_queue.append(("敌人变强了，但你也更强了！", 120))


def trigger_ng_plus(g):
    """触发NG+确认（通关后调用）"""
    from game import GameState
    g.ng_plus_pending = True
    g.state = GameState.NG_PLUS_CONFIRM


def draw_ng_plus_confirm(g):
    """绘制NG+确认界面"""
    g.screen.fill(C_PANEL)
    pw, ph = 400, 300
    px = (SCREEN_W - pw) // 2
    py = (SCREEN_H - ph) // 2
    draw_pixel_rect(g.screen, C_PANEL, (px, py, pw, ph), 3, C_GOLD)

    ng_level = g.player.ng_plus + 1
    draw_text(g.screen, f"【New Game+ {ng_level}】",
              (SCREEN_W // 2, py + 20), g.assets.font_lg, C_GOLD, center=True)

    info = [
        "开始新的轮回？",
        "",
        "保留: 技能、宠物、家具、成就、涂鸦",
        f"保留: {g.player.stats.gold // 2}G (当前一半)",
        f"加成: ATK+{ng_level * 2} DEF+{ng_level * 2} HP+{ng_level * 20}",
        "",
        "重置: 主线进度、装备、物品、好感度",
        "",
        "[Enter] 确认开始",
        "[ESC] 取消",
    ]
    iy = py + 60
    for line in info:
        c = C_WHITE
        if line.startswith("保留"):
            c = C_GREEN
        elif line.startswith("加成"):
            c = C_NEON_CYAN
        elif line.startswith("重置"):
            c = C_RED
        draw_text(g.screen, line, (SCREEN_W // 2, iy), g.assets.font_sm, c, center=True)
        iy += 22


# ============================================================
# 任务链击杀/收集进度追踪（在战斗结束时调用）
# ============================================================

def update_quest_chain_kill(player, enemy_key):
    """战斗胜利后更新任务链击杀进度"""
    for chain_id, state in player.quest_chains.items():
        if state.get('done'):
            continue
        chain = QUEST_CHAINS.get(chain_id)
        if not chain:
            continue
        step_idx = state['step']
        if step_idx >= len(chain.steps):
            continue
        step = chain.steps[step_idx]
        if step.objective_type == 'kill' and step.target == enemy_key:
            state['progress'] = state.get('progress', 0) + 1
