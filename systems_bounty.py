"""悬赏板系统"""
import random
import pygame
from constants import *
from entities import BOUNTY_POOL, ITEMS_DB


def refresh_bounty_board(game):
    """刷新赏金板（进入酒吧时或板空时）"""
    p = game.player
    if p.bounty_board and not all(bid in p.completed_bounties for bid in p.bounty_board):
        return  # 还有未完成的，不刷新
    available = [bid for bid in BOUNTY_POOL if bid not in p.completed_bounties]
    random.shuffle(available)
    p.bounty_board = available[:3]


def handle_bounty_event(game, event):
    if event.type != pygame.KEYDOWN:
        return
    p = game.player
    board = p.bounty_board
    if not board:
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            from game import GameState
            game.state = GameState.EXPLORE
        return
    if event.key in (pygame.K_ESCAPE, pygame.K_x):
        from game import GameState
        game.state = GameState.EXPLORE
    elif event.key == pygame.K_UP:
        game.bounty_index = (game.bounty_index - 1) % len(board)
    elif event.key == pygame.K_DOWN:
        game.bounty_index = (game.bounty_index + 1) % len(board)
    elif event.key in (pygame.K_j, pygame.K_RETURN):
        if game.bounty_index < len(board):
            bid = board[game.bounty_index]
            bdef = BOUNTY_POOL.get(bid)
            if not bdef:
                return
            # 检查是否已接取
            active_ids = [b['bounty_id'] for b in p.active_bounties]
            if bid in active_ids:
                # 检查是否完成
                ab = next(b for b in p.active_bounties if b['bounty_id'] == bid)
                if _is_bounty_complete(game, ab, bdef):
                    # 领取奖励
                    _claim_bounty_reward(game, ab, bdef)
                else:
                    game.message_queue.append(("任务尚未完成！", 90))
            elif bid in p.completed_bounties:
                game.message_queue.append(("已完成此任务！", 90))
            elif len(p.active_bounties) >= 3:
                game.message_queue.append(("最多同时接取3个赏金任务！", 90))
            else:
                # 接取
                p.active_bounties.append({'bounty_id': bid, 'progress': 0})
                game.message_queue.append((f"接取赏金任务：{bdef.name}！", 120))


def _is_bounty_complete(game, ab, bdef):
    if bdef.bounty_type == 'kill':
        return ab['progress'] >= bdef.target_count
    elif bdef.bounty_type == 'collect':
        return game.player.item_count(bdef.target) >= bdef.target_count
    elif bdef.bounty_type == 'survive':
        return ab['progress'] >= bdef.target_count
    return False


def _claim_bounty_reward(game, ab, bdef):
    p = game.player
    bid = ab['bounty_id']
    # 扣除collect类物品
    if bdef.bounty_type == 'collect':
        p.remove_item(bdef.target, bdef.target_count)
    # 发放奖励
    rewards = bdef.rewards
    p.stats.gold += rewards.get('gold', 0)
    for item_key, cnt in rewards.get('items', []):
        p.add_item(item_key, cnt)
    # 宠物经验
    pet_exp = rewards.get('pet_exp', 0)
    if pet_exp and p.active_pet:
        p.add_pet_exp(p.active_pet, pet_exp)
    # 标记完成
    p.active_bounties = [b for b in p.active_bounties if b['bounty_id'] != bid]
    p.completed_bounties.add(bid)
    reward_text = f"+{rewards.get('gold', 0)}G"
    for item_key, cnt in rewards.get('items', []):
        reward_text += f" +{ITEMS_DB[item_key].name}x{cnt}"
    game.message_queue.append((f"赏金完成：{bdef.name}！{reward_text}", 180))
    px = SCREEN_W // 2
    py = SCREEN_H // 2
    game.particles.emit(px, py, 20, C_GOLD, 3, 50, 4, 'magic')


def draw_bounty_board(game):
    """悬赏板界面"""
    game.screen.fill((10, 8, 20))
    p = game.player
    draw_text(game.screen, "【赏金任务板】", (SCREEN_W // 2, 20), game.assets.font_lg, C_GOLD, center=True)

    board = p.bounty_board
    if not board:
        draw_text(game.screen, "暂无可用任务", (SCREEN_W // 2, 120), game.assets.font_md, C_WHITE, center=True)
    else:
        active_ids = [b['bounty_id'] for b in p.active_bounties]
        for i, bid in enumerate(board):
            bdef = BOUNTY_POOL.get(bid)
            if not bdef:
                continue
            y = 70 + i * 160
            selected = i == game.bounty_index
            border_c = C_NEON_CYAN if selected else (60, 60, 80)
            draw_pixel_rect(game.screen, (15, 12, 30), (40, y, SCREEN_W - 80, 145), 2, border_c)

            # 名称
            color = C_YELLOW if selected else C_WHITE
            prefix = ">> " if selected else "   "
            draw_text(game.screen, f"{prefix}{bdef.name}", (60, y + 8), game.assets.font_md, color)

            # 类型标签
            type_labels = {'kill': '[击杀]', 'collect': '[收集]', 'survive': '[存活]'}
            type_colors = {'kill': C_RED, 'collect': C_GREEN, 'survive': C_NEON_CYAN}
            draw_text(game.screen, type_labels.get(bdef.bounty_type, ''),
                      (SCREEN_W - 120, y + 8), game.assets.font_sm,
                      type_colors.get(bdef.bounty_type, C_WHITE))

            # 描述
            draw_text(game.screen, bdef.description, (80, y + 32), game.assets.font_sm, (160, 160, 180))

            # 奖励
            rewards = bdef.rewards
            reward_parts = [f"{rewards.get('gold', 0)}G"]
            for item_key, cnt in rewards.get('items', []):
                if item_key in ITEMS_DB:
                    reward_parts.append(f"{ITEMS_DB[item_key].name}x{cnt}")
            draw_text(game.screen, f"奖励: {' '.join(reward_parts)}",
                      (80, y + 54), game.assets.font_sm, C_GOLD)

            # 状态/进度
            if bid in p.completed_bounties:
                draw_text(game.screen, "[已完成]", (80, y + 76), game.assets.font_sm, (100, 100, 100))
            elif bid in active_ids:
                ab = next(b for b in p.active_bounties if b['bounty_id'] == bid)
                if bdef.bounty_type == 'collect':
                    cur = p.item_count(bdef.target)
                    progress = min(cur, bdef.target_count)
                else:
                    progress = ab['progress']
                total = bdef.target_count
                done = progress >= total
                pct = min(1.0, progress / total) if total > 0 else 0
                draw_bar(game.screen, 80, y + 80, 200, 10, pct,
                         C_GREEN if done else C_NEON_CYAN)
                draw_text(game.screen, f"{progress}/{total}",
                          (290, y + 77), game.assets.font_sm, C_WHITE)
                if done:
                    draw_text(game.screen, "J:领取奖励", (400, y + 77),
                              game.assets.font_sm, C_YELLOW)
            else:
                draw_text(game.screen, "J:接取", (80, y + 76), game.assets.font_sm, C_NEON_CYAN)

            # 已接取数量
            draw_text(game.screen, f"已接取: {len(p.active_bounties)}/3",
                      (80, y + 100), game.assets.font_sm, (100, 120, 140))

    draw_text(game.screen, "↑↓选择  J:接取/领取  X:返回", (SCREEN_W // 2, SCREEN_H - 30),
              game.assets.font_sm, (80, 100, 120), center=True)

    # 消息
    if game.message_queue:
        msg, timer = game.message_queue[0]
        draw_text(game.screen, msg, (SCREEN_W // 2, SCREEN_H - 60), game.assets.font_md, C_GOLD, center=True)
