import pygame
from random import randint
from pygame.math import Vector2


class DamageText(pygame.sprite.Sprite):
    def __init__(self, pos, damage, is_critical=False):
        super().__init__()
        # 初始化位置属性（关键修正）
        self.pos = Vector2(pos)  # 将传入的pos转换为Vector2
        self.pos += Vector2(randint(-15, 15), randint(-10, 10))  # 随机偏移

        # 文字属性
        self._create_text_surface(damage, is_critical)

        # 运动参数
        self.velocity = Vector2(randint(-20, 20), -50 if is_critical else -30)
        self.lifetime = 1.0
        self.age = 0.0

    def _create_text_surface(self, damage, is_critical):
        """创建文字表面"""
        self.font_size = 32 if is_critical else 24
        self.color = (255, 255, 0) if is_critical else (255, 255, 255)
        self.font = pygame.font.SysFont("Arial", self.font_size, bold=True)

        text = f"{damage}!" if is_critical else str(damage)
        self.image = self.font.render(text, True, self.color)
        self.rect = self.image.get_rect(center=self.pos)  # 初始化rect位置

    def update(self, dt):
        """更新位置和生命周期"""
        self.age += dt
        # 运动计算
        self.velocity.y += 100 * dt  # 模拟重力
        self.pos += self.velocity * dt
        # 更新显示位置
        self.rect.center = self.pos

        # 透明度变化
        alpha = 255 * (1 - self.age / self.lifetime)
        self.image.set_alpha(int(alpha))

        # 自动销毁
        if self.age >= self.lifetime:
            self.kill()
