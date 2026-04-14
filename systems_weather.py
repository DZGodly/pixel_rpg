"""天气/时间系统"""
import random
import pygame
from constants import *
from game_map import (AREA_VILLAGE, AREA_FOREST, AREA_NEON_STREET, AREA_FACTORY,
                      AREA_CYBERSPACE, AREA_TUNNEL, AREA_BLACK_MARKET, AREA_HOME)


def get_time_phase(game):
    t = game.player.world_time % 10800
    if t < 1800:
        return 'dawn'
    elif t < 5400:
        return 'day'
    elif t < 7200:
        return 'dusk'
    else:
        return 'night'


def update_weather_time(game):
    """每tick更新天气和时间"""
    p = game.player
    p.world_time += 1
    if p.world_time >= 10800:
        p.world_time = 0
    # 天气切换
    p.weather_timer -= 1
    if p.weather_timer <= 0:
        roll = random.random()
        if roll < 0.40:
            p.weather = 'clear'
        elif roll < 0.65:
            p.weather = 'rain'
        elif roll < 0.85:
            p.weather = 'fog'
        else:
            p.weather = 'storm'
        p.weather_timer = random.randint(10800, 18000)


def draw_weather_overlay(game):
    """天气/时间视觉叠加层"""
    phase = game._get_time_phase()
    weather = game.player.weather

    # 时间叠加
    overlay = None
    if phase == 'night':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((0, 0, 40, 80))
    elif phase == 'dusk':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((40, 20, 0, 40))
    elif phase == 'dawn':
        overlay = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        overlay.fill((40, 30, 10, 30))
    if overlay:
        game.screen.blit(overlay, (0, 0))

    # 雾
    if weather == 'fog':
        fog = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        fog.fill((80, 80, 80, 60))
        game.screen.blit(fog, (0, 0))

    # 雨
    if weather in ('rain', 'storm'):
        for _ in range(30):
            rx = random.randint(0, SCREEN_W)
            ry = random.randint(0, SCREEN_H)
            pygame.draw.line(game.screen, (100, 150, 220, 120),
                             (rx, ry), (rx - 3, ry + 10))

    # 闪电 (storm)
    if weather == 'storm':
        if game.lightning_timer > 0:
            flash = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
            flash.fill((255, 255, 255, min(100, game.lightning_timer * 30)))
            game.screen.blit(flash, (0, 0))
            game.lightning_timer -= 1
        elif random.random() < 0.02:
            game.lightning_timer = 3


def draw_sky(game, area):
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
    elif area == AREA_HOME:
        # 家园 - 暖色调
        top = (15, 12, 8)
        bot = (25, 20, 15)
    else:
        # 旧数据中心
        top = (8, 5, 15)
        bot = (15, 12, 25)

    for y in range(SCREEN_H):
        t = y / SCREEN_H
        c = lerp_color(top, bot, t)
        pygame.draw.line(game.screen, c, (0, y), (SCREEN_W, y))
