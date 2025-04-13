import pygame
from pygame.math import Vector2
from random import uniform
from ..core.config import Config

class HitParticle(pygame.sprite.Sprite):
    def __init__(self, pos, color=(255,0,0)):
        super().__init__()
        self.image = pygame.Surface((8,8), pygame.SRCALPHA)
        pygame.draw.circle(self.image, color, (4,4), 4)
        self.rect = self.image.get_rect(center=pos)
        self.lifetime = 0.3  # 秒
        self.age = 0
        self.velocity = Vector2(
            uniform(-100, 100),
            uniform(-100, 100)
        )

    def update(self, dt):
        self.age += dt
        self.rect.center += self.velocity * dt
        self.image.set_alpha(255 * (1 - self.age/self.lifetime))
        
        if self.age >= self.lifetime:
            self.kill()