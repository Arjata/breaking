from enum import Enum
import random
import pygame
from pygame.math import Vector2
from ..core.config import Config


class PowerUpType(Enum):
    HEALTH = 1
    SHIELD = 2
    FIREPOWER = 3


class PowerUp(pygame.sprite.Sprite):
    DROP_CHANCE = 0.3  # 30%掉落率

    def __init__(self, enemy_pos):
        super().__init__()
        self.type = random.choice(list(PowerUpType))
        colors = {
            PowerUpType.HEALTH: (0, 255, 0),
            PowerUpType.SHIELD: (0, 0, 255),
            PowerUpType.FIREPOWER: (255, 165, 0),
        }
        self.image = pygame.Surface((20, 20))
        self.image.fill(colors[self.type])
        self.rect = self.image.get_rect(center=enemy_pos)
        self.speed = Vector2(0, 100)  # 向下飘落

    def update(self, dt):
        self.rect.y += self.speed.y * dt
        if self.rect.top > Config.HEIGHT:
            self.kill()

    def apply_effect(self, player):
        player.apply_powerup(self.type)
