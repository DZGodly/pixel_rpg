"""宠物管理与烹饪系统"""
import math
import random
import pygame
from constants import *
from entities import PETS_DB, ITEMS_DB, MEALS_DB


def handle_pet_menu_event(game, event):
    """宠物管理界面"""
    if event.type != pygame.KEYDOWN:
        return
    p = game.player
    pets_list = list(PETS_DB.values())

    # 喂食子菜单
    if game.pet_feed_mode:
        feedable = [(k, c) for k, c in p.inventory
                    if k in ('hp_potion', 'mp_potion', 'data_sample', 'quantum_chip')]
        if not feedable:
            game.pet_feed_mode = False
            return
        if event.key in (pygame.K_ESCAPE, pygame.K_x):
            game.pet_feed_mode = False
        elif event.key == pygame.K_UP:
            game.pet_feed_index = (game.pet_feed_index - 1) % len(feedable)
        elif event.key == pygame.K_DOWN:
            game.pet_feed_index = (game.pet_feed_index + 1) % len(feedable)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            if game.pet_feed_index < len(feedable):
                item_key, cnt = feedable[game.pet_feed_index]
                pet_id = p.pets_owned[game.pet_menu_index]
                happiness_map = {'hp_potion': 10, 'mp_potion': 10, 'data_sample': 15, 'quantum_chip': 20}
                delta = happiness_map.get(item_key, 5)
                cur = p.pet_happiness.get(pet_id, 50)
                p.pet_happiness[pet_id] = min(100, cur + delta)
                p.remove_item(item_key)
                pet = PETS_DB[pet_id]
                game.message_queue.append((f"{pet.name}吃了{ITEMS_DB[item_key].name}！幸福度+{delta} ({p.pet_happiness[pet_id]}/100)", 120))
                game.pet_feed_mode = False
        return

    if game.pet_shop_mode:
        # 宠物商店
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            game.pet_shop_mode = False
        elif event.key == pygame.K_UP:
            game.pet_shop_index = (game.pet_shop_index - 1) % len(pets_list)
        elif event.key == pygame.K_DOWN:
            game.pet_shop_index = (game.pet_shop_index + 1) % len(pets_list)
        elif event.key in (pygame.K_RETURN, pygame.K_j):
            pet = pets_list[game.pet_shop_index]
            price = 200  # 统一价格
            if pet.pet_id in p.pets_owned:
                game.message_queue.append(("已经拥有这只宠物了！", 90))
            elif p.stats.gold >= price:
                p.stats.gold -= price
                p.pets_owned.append(pet.pet_id)
                p.pet_happiness[pet.pet_id] = 50
                game.message_queue.append((f"获得了 {pet.name}！(-{price}G)", 120))
            else:
                game.message_queue.append(("信用点不足！", 90))
    else:
        # 宠物管理
        if event.key == pygame.K_ESCAPE or event.key == pygame.K_x:
            from game import GameState
            game.state = GameState.EXPLORE
        elif event.key == pygame.K_TAB:
            game.pet_shop_mode = True
            game.pet_shop_index = 0
        elif p.pets_owned:
            if event.key == pygame.K_UP:
                game.pet_menu_index = (game.pet_menu_index - 1) % len(p.pets_owned)
            elif event.key == pygame.K_DOWN:
                game.pet_menu_index = (game.pet_menu_index + 1) % len(p.pets_owned)
            elif event.key in (pygame.K_RETURN, pygame.K_j):
                pet_id = p.pets_owned[game.pet_menu_index]
                if p.active_pet == pet_id:
                    p.active_pet = None
                    game.message_queue.append(("宠物已收回。", 90))
                else:
                    p.active_pet = pet_id
                    pet = PETS_DB[pet_id]
                    evo_name = pet.evolved_name if p.is_pet_evolved(pet_id) else pet.name
                    game.message_queue.append((f"{evo_name} 出战！", 90))
            elif event.key == pygame.K_f:
                # 喂食
                game.pet_feed_mode = True
                game.pet_feed_index = 0
            elif event.key == pygame.K_p:
                # 玩耍
                pet_id = p.pets_owned[game.pet_menu_index]
                cd = p.pet_play_cooldown.get(pet_id, 0)
                if cd > 0:
                    game.message_queue.append((f"玩耍冷却中...还需{cd}步", 90))
                else:
                    cur = p.pet_happiness.get(pet_id, 50)
                    p.pet_happiness[pet_id] = min(100, cur + 8)
                    p.pet_play_cooldown[pet_id] = 500
                    pet = PETS_DB[pet_id]
                    game.message_queue.append((f"和{pet.name}玩耍了！幸福度+8 ({p.pet_happiness[pet_id]}/100)", 120))
                    px = SCREEN_W // 2
                    py = SCREEN_H // 2
                    game.particles.emit(px, py, 15, (255, 200, 100), 2, 40, 3, 'firefly')
            elif event.key == pygame.K_e:
                # 探险
                pet_id = p.pets_owned[game.pet_menu_index]
                if p.expedition:
                    game.message_queue.append(("已有宠物在探险中！", 90))
                elif pet_id == p.active_pet:
                    game.message_queue.append(("出战中的宠物不能探险！", 90))
                else:
                    pet_level = p.get_pet_level(pet_id)
                    p.expedition = {'pet_id': pet_id, 'steps_left': 1000, 'reward_tier': pet_level}
                    pet = PETS_DB[pet_id]
                    game.message_queue.append((f"{pet.name}出发探险了！(1000步后返回)", 120))


def handle_cooking_event(game, event):
    """烹饪界面"""
    if event.type != pygame.KEYDOWN:
        return
    meals = list(MEALS_DB.values())
    if event.key in (pygame.K_ESCAPE, pygame.K_x):
        from game import GameState
        game.state = GameState.MENU
    elif event.key == pygame.K_UP:
        game.cooking_index = (game.cooking_index - 1) % len(meals)
    elif event.key == pygame.K_DOWN:
        game.cooking_index = (game.cooking_index + 1) % len(meals)
    elif event.key in (pygame.K_RETURN, pygame.K_j):
        meal = meals[game.cooking_index]
        # 检查材料
        can_cook = all(game.player.item_count(k) >= v for k, v in meal.materials.items())
        if not can_cook:
            game.message_queue.append(("材料不足！", 90))
        else:
            for k, v in meal.materials.items():
                game.player.remove_item(k, v)
            game.player.active_meal = meal.meal_id
            game.player.meal_buff_turns = meal.buff_turns
            game.player.codex_recipes.add(meal.meal_id)
            buff_desc = {'atk': f'ATK+{meal.buff_value}', 'def': f'DEF+{meal.buff_value}',
                         'hp_regen': f'HP回复{meal.buff_value}/回合', 'all': f'全属性+{meal.buff_value}',
                         'atk_def': f'ATK+{meal.buff_value} DEF+5'}
            game.message_queue.append((f"烹饪了{meal.name}！{buff_desc.get(meal.buff_type, '')} {meal.buff_turns}回合", 150))


def complete_expedition(game):
    """探险完成，发放奖励"""
    p = game.player
    exp = p.expedition
    if not exp:
        return
    pet_id = exp['pet_id']
    tier = exp['reward_tier']
    pet = PETS_DB.get(pet_id)
    pet_name = pet.name if pet else pet_id

    rewards = []
    if tier <= 2:
        item = random.choice(['hp_potion', 'mp_potion'])
        count = random.randint(1, 2)
        gold = random.randint(20, 50)
    elif tier <= 4:
        item = random.choice(['data_sample', 'precision_gear'])
        count = 1
        gold = random.randint(50, 100)
    else:
        item = random.choice(['quantum_chip', 'encrypted_data'])
        count = 1
        gold = random.randint(100, 200)
        # 稀有物品概率
        if random.random() < 0.3:
            p.add_item('elixir')
            rewards.append('系统重启')

    p.add_item(item, count)
    p.stats.gold += gold
    rewards.insert(0, f"{ITEMS_DB[item].name}x{count} +{gold}G")
    reward_text = ' '.join(rewards)
    game.message_queue.append((f"{pet_name}探险归来！获得{reward_text}", 180))
    px = SCREEN_W // 2
    py = SCREEN_H // 2
    game.particles.emit(px, py, 20, (0, 255, 200), 3, 50, 4, 'magic')
    p.expedition = None


def draw_pet_menu(game):
    """宠物管理界面"""
    game.screen.fill((10, 10, 20))
    p = game.player

    draw_text(game.screen, "【宠物管理】", (SCREEN_W//2, 20), game.assets.font_lg, C_NEON_CYAN, center=True)
    draw_text(game.screen, f"信用点: {p.stats.gold}", (SCREEN_W - 120, 20), game.assets.font_sm, C_GOLD)

    if game.pet_shop_mode:
        # 宠物商店
        draw_text(game.screen, "【宠物商店】(X返回)", (SCREEN_W//2, 60), game.assets.font_md, C_GOLD, center=True)
        pets_list = list(PETS_DB.values())
        for i, pet in enumerate(pets_list):
            color = C_YELLOW if i == game.pet_shop_index else C_WHITE
            owned = pet.pet_id in p.pets_owned
            prefix = ">> " if i == game.pet_shop_index else "   "
            status = " [已拥有]" if owned else f" (200G)"
            draw_text(game.screen, f"{prefix}{pet.name}{status}",
                      (80, 100 + i * 50), game.assets.font_md, color)
            draw_text(game.screen, pet.description, (100, 125 + i * 50), game.assets.font_sm, (140, 140, 160))
            # 被动效果
            passive = pet.passive
            eff_text = ""
            if passive.get('type') == 'hp_regen': eff_text = f"被动: 每秒回复{passive['value']}HP"
            elif passive.get('type') == 'gold_boost': eff_text = f"被动: 金币+{passive['value']}%"
            elif passive.get('type') == 'exp_boost': eff_text = f"被动: 经验+{passive['value']}%"
            elif passive.get('type') == 'atk_boost': eff_text = f"被动: ATK+{passive['value']}"
            elif passive.get('type') == 'def_boost': eff_text = f"被动: DEF+{passive['value']}"
            draw_text(game.screen, eff_text, (100, 140 + i * 50), game.assets.font_sm, C_NEON_CYAN)
            # 精灵
            sprite = game.assets.npc_sprites.get(pet.sprite_key)
            if sprite:
                game.screen.blit(sprite, (50, 100 + i * 50))
    elif game.pet_feed_mode and p.pets_owned:
        # 喂食子菜单
        pet_id = p.pets_owned[game.pet_menu_index]
        pet = PETS_DB.get(pet_id)
        pet_name = pet.evolved_name if pet and p.is_pet_evolved(pet_id) else (pet.name if pet else pet_id)
        draw_text(game.screen, f"喂食 {pet_name} (X返回)", (SCREEN_W//2, 60), game.assets.font_md, C_GOLD, center=True)
        feedable = [(k, c) for k, c in p.inventory
                    if k in ('hp_potion', 'mp_potion', 'data_sample', 'quantum_chip')]
        if not feedable:
            draw_text(game.screen, "没有可喂食的物品！", (SCREEN_W//2, 120), game.assets.font_md, (150, 150, 150), center=True)
        else:
            happiness_map = {'hp_potion': 10, 'mp_potion': 10, 'data_sample': 15, 'quantum_chip': 20}
            for i, (key, cnt) in enumerate(feedable):
                color = C_YELLOW if i == game.pet_feed_index else C_WHITE
                prefix = ">> " if i == game.pet_feed_index else "   "
                delta = happiness_map.get(key, 5)
                draw_text(game.screen, f"{prefix}{ITEMS_DB[key].name} x{cnt} (幸福度+{delta})",
                          (80, 100 + i * 28), game.assets.font_sm, color)
    else:
        # 我的宠物
        if not p.pets_owned:
            draw_text(game.screen, "还没有宠物。按TAB打开宠物商店。", (SCREEN_W//2, SCREEN_H//2),
                      game.assets.font_md, (100, 100, 120), center=True)
        else:
            draw_text(game.screen, "我的宠物 (TAB:商店)", (SCREEN_W//2, 60), game.assets.font_md, C_GOLD, center=True)
            for i, pet_id in enumerate(p.pets_owned):
                pet = PETS_DB.get(pet_id)
                if not pet:
                    continue
                color = C_YELLOW if i == game.pet_menu_index else C_WHITE
                prefix = ">> " if i == game.pet_menu_index else "   "
                active = " ★出战中" if p.active_pet == pet_id else ""
                evolved = p.is_pet_evolved(pet_id)
                display_name = pet.evolved_name if evolved else pet.name
                level = p.get_pet_level(pet_id)
                on_expedition = p.expedition and p.expedition['pet_id'] == pet_id

                y_base = 90 + i * 80
                draw_text(game.screen, f"{prefix}{display_name} Lv{level}{active}",
                          (80, y_base), game.assets.font_md, color)
                if evolved:
                    draw_text(game.screen, "[进化]", (350, y_base), game.assets.font_sm, (255, 200, 50))

                desc = pet.evolved_description if evolved else pet.description
                draw_text(game.screen, desc, (100, y_base + 20), game.assets.font_sm, (140, 140, 160))

                # 经验条
                exp = p.pet_exp.get(pet_id, 0)
                exp_next = level * 50
                exp_pct = exp / exp_next if exp_next > 0 else 0
                draw_bar(game.screen, 100, y_base + 36, 120, 6, min(1.0, exp_pct), (100, 200, 255))
                draw_text(game.screen, f"EXP:{exp}/{exp_next}", (225, y_base + 33), game.assets.font_sm, (120, 160, 200))

                # 幸福度
                happiness = p.pet_happiness.get(pet_id, 50)
                h_color = (80, 200, 80) if happiness > 80 else ((200, 200, 80) if happiness > 20 else (200, 80, 80))
                face = "♥" if happiness > 80 else ("~" if happiness > 20 else "...")
                draw_bar(game.screen, 310, y_base + 36, 80, 6, happiness / 100, h_color)
                draw_text(game.screen, f"{face}{happiness}", (395, y_base + 33), game.assets.font_sm, h_color)

                # 战斗技能
                if evolved and pet.evolved_combat_skill:
                    skill_name, skill_val = pet.evolved_combat_skill
                    draw_text(game.screen, f"技能: {skill_name}({skill_val})",
                              (100, y_base + 50), game.assets.font_sm, (100, 200, 180))
                elif pet.combat_skill:
                    draw_text(game.screen, f"技能: {pet.combat_skill[0]}({pet.combat_skill[1]})",
                              (100, y_base + 50), game.assets.font_sm, (100, 200, 180))

                # 探险状态
                if on_expedition:
                    steps_left = p.expedition['steps_left']
                    draw_text(game.screen, f"[探险中 剩余{steps_left}步]",
                              (300, y_base + 50), game.assets.font_sm, (255, 180, 80))

                # 精灵
                sprite_key = pet.evolved_sprite_key if evolved else pet.sprite_key
                sprite = game.assets.npc_sprites.get(sprite_key)
                if not sprite:
                    sprite = game.assets.npc_sprites.get(pet.sprite_key)
                if sprite:
                    bob = int(math.sin(game.tick * 0.06 + i) * 2)
                    game.screen.blit(sprite, (50, y_base + bob))

    # 操作提示
    draw_text(game.screen, "↑↓选择  J:出战/收回  F:喂食  P:玩耍  E:探险  TAB:商店  X:返回", (SCREEN_W//2, SCREEN_H - 30),
              game.assets.font_sm, (80, 100, 120), center=True)

    # 消息
    if game.message_queue:
        msg, timer = game.message_queue[0]
        draw_text(game.screen, msg, (SCREEN_W//2, SCREEN_H - 60), game.assets.font_md, C_GOLD, center=True)


def draw_cooking(game):
    """烹饪界面"""
    game.screen.fill((15, 10, 10))
    p = game.player

    draw_text(game.screen, "【烹饪】", (SCREEN_W//2, 20), game.assets.font_lg, C_GOLD, center=True)

    # 当前buff状态
    if p.active_meal:
        meal = MEALS_DB.get(p.active_meal)
        if meal:
            draw_text(game.screen, f"当前buff: {meal.name} (剩余{p.meal_buff_turns}回合)",
                      (SCREEN_W//2, 50), game.assets.font_sm, C_NEON_CYAN, center=True)

    meals = list(MEALS_DB.values())
    for i, meal in enumerate(meals):
        y = 80 + i * 70
        selected = i == game.cooking_index
        color = C_YELLOW if selected else C_WHITE
        prefix = ">> " if selected else "   "

        # 检查材料
        can_cook = all(p.item_count(k) >= v for k, v in meal.materials.items())
        if not can_cook:
            color = (100, 100, 100)

        draw_text(game.screen, f"{prefix}{meal.name}", (60, y), game.assets.font_md, color)

        # 材料列表
        mat_parts = []
        for k, v in meal.materials.items():
            have = p.item_count(k)
            item_name = ITEMS_DB[k].name if k in ITEMS_DB else k
            c = "✓" if have >= v else "✗"
            mat_parts.append(f"{item_name}x{v}({c})")
        draw_text(game.screen, "材料: " + " + ".join(mat_parts), (80, y + 22), game.assets.font_sm, (140, 140, 160))

        # buff预览
        buff_desc = {'atk': f'ATK+{meal.buff_value}', 'def': f'DEF+{meal.buff_value}',
                     'hp_regen': f'HP回复{meal.buff_value}/回合', 'all': f'全属性+{meal.buff_value}',
                     'atk_def': f'ATK+{meal.buff_value} DEF+5'}
        draw_text(game.screen, f"效果: {buff_desc.get(meal.buff_type, '')} ({meal.buff_turns}回合)",
                  (80, y + 40), game.assets.font_sm, (100, 200, 180))

    # 操作提示
    draw_text(game.screen, "↑↓选择  J:烹饪  X:返回", (SCREEN_W//2, SCREEN_H - 30),
              game.assets.font_sm, (120, 100, 100), center=True)

    # 消息
    if game.message_queue:
        msg, timer = game.message_queue[0]
        draw_text(game.screen, msg, (SCREEN_W//2, SCREEN_H - 60), game.assets.font_md, C_GOLD, center=True)
