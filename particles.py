"""粒子系统"""

import random
import pygame
from typing import List
from constants import SCREEN_W, SCREEN_H


class Particle:
    __slots__ = ['x', 'y', 'vx', 'vy', 'life', 'max_life', 'color', 'size', 'kind']
    def __init__(self, x, y, vx, vy, life, color, size=2, kind='default'):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.kind = kind


class ParticleSystem:
    def __init__(self):
        self.particles: List[Particle] = []

    def emit(self, x, y, count=1, color=(255,255,200), spread=1.0, life=60, size=2, kind='default'):
        for _ in range(count):
            vx = random.uniform(-spread, spread)
            vy = random.uniform(-spread, spread)
            self.particles.append(Particle(x + random.uniform(-4,4), y + random.uniform(-4,4),
                                           vx, vy, life + random.randint(-10,10), color, size, kind))

    def update(self):
        for p in self.particles:
            p.x += p.vx
            p.y += p.vy
            p.life -= 1
            if p.kind == 'firefly':
                p.vx += random.uniform(-0.1, 0.1)
                p.vy += random.uniform(-0.1, 0.1)
            elif p.kind == 'magic':
                p.vy -= 0.02
            elif p.kind == 'dust':
                p.vy += 0.01
        self.particles = [p for p in self.particles if p.life > 0]

    def draw(self, surf, cam_x, cam_y):
        for p in self.particles:
            alpha = p.life / p.max_life
            sx = int(p.x - cam_x)
            sy = int(p.y - cam_y)
            if 0 <= sx < SCREEN_W and 0 <= sy < SCREEN_H:
                c = tuple(int(p.color[i] * alpha) for i in range(3))
                sz = max(1, int(p.size * alpha))
                if p.kind == 'firefly':
                    glow = pygame.Surface((sz*4, sz*4), pygame.SRCALPHA)
                    a = int(120 * alpha)
                    pygame.draw.circle(glow, (*p.color, a), (sz*2, sz*2), sz*2)
                    surf.blit(glow, (sx - sz*2, sy - sz*2))
                else:
                    pygame.draw.rect(surf, c, (sx, sy, sz, sz))
