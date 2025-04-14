import pygame
import math
from random import uniform, randint
from pygame.math import Vector2
from ..core.config import Config
from ..entities.player import Player, Bullet
from threading import Timer


class EnemyBullet(pygame.sprite.Sprite):
    def __init__(self, pos, direction, speed=400, color=(255, 0, 0)):
        super().__init__()
        self.image = pygame.Surface((8, 8))
        self.image.fill(color)
        self.rect = self.image.get_rect(center=pos)
        self.color = color

        # 统一使用velocity控制移动
        if direction.length() == 0:
            direction = Vector2(0, 1)
        self.velocity = direction.normalize() * speed

    def update(self, dt):
        self.rect.center += self.velocity * dt
        # 边界检查
        if not (0 - 100 < self.rect.x < Config.WIDTH + 100) or not (
            0 - 100 < self.rect.y < Config.HEIGHT + 100
        ):
            self.kill()


class HomingEnemyBullet(EnemyBullet):
    def __init__(self, pos, direction, speed, color, player_pos_ref, max_alive_time=3):
        super().__init__(pos, direction, speed, color)
        self.player_pos_ref = player_pos_ref
        self.turn_rate = 120  # 每秒转向角度
        self.max_alive_time = max_alive_time
        self.timer = 0

    def update(self, dt):
        self.timer += dt
        # 基础移动
        self.rect.center += self.velocity * dt

        # 跟踪逻辑
        player_pos = self.player_pos_ref()
        if player_pos:
            current_pos = Vector2(self.rect.center)
            target_vector = player_pos - current_pos
            if target_vector.length() > 10:
                target_dir = target_vector.normalize()
                current_dir = self.velocity.normalize()
                angle = current_dir.angle_to(target_dir)
                max_turn = self.turn_rate * dt
                angle = max(-max_turn, min(angle, max_turn))
                # 更新velocity方向
                self.velocity = (
                    current_dir.rotate(angle).normalize() * self.velocity.length()
                )

        # 边界检查
        if not (0 - 100 < self.rect.x < Config.WIDTH + 100) or not (
            0 - 100 < self.rect.y < Config.HEIGHT + 100
        ):
            self.kill()
        if self.timer > self.max_alive_time:
            self.kill()


class BounceEnemyBullet(EnemyBullet):
    def __init__(self, pos, direction, speed=300, color=(0, 0, 255)):
        super().__init__(pos, direction, speed, color)
        self.bounce_count = 0
        self.max_bounce = 3

    def update(self, dt):
        old_center = self.rect.center
        self.rect.center += self.velocity * dt

        # 水平反弹
        if self.rect.left < 0 or self.rect.right > Config.WIDTH:
            self.velocity.x *= -1
            self.bounce_count += 1
            self.rect.center = old_center  # 防止卡墙

        # 垂直反弹
        if self.rect.top < 0 or self.rect.bottom > Config.HEIGHT:
            self.velocity.y *= -1
            self.bounce_count += 1
            self.rect.center = old_center

        if self.bounce_count >= self.max_bounce:
            self.kill()


class LaserBeam(pygame.sprite.Sprite):
    def __init__(self, pos, direction, duration=1.5, width=10, color=(255, 0, 0)):
        super().__init__()
        self.pos = Vector2(pos)
        self.direction = direction.normalize()
        self.duration = duration
        self.width = width
        self.color = color
        self.timer = 0.0

        # 创建基础激光图像
        length = max(Config.WIDTH, Config.HEIGHT) * 2
        self.base_image = pygame.Surface((length, width), pygame.SRCALPHA)
        pygame.draw.line(
            self.base_image, color, (0, width // 2), (length, width // 2), width
        )

        # 初始旋转
        self.image = pygame.transform.rotate(
            self.base_image, self.direction.angle_to((1, 0))
        )
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.duration:
            self.kill()


class RotatingLaser(LaserBeam):
    def __init__(self, pos, direction, rotation_speed=45, **kwargs):
        super().__init__(pos, direction, **kwargs)
        self.rotation_speed = rotation_speed
        self.current_angle = self.direction.angle_to((1, 0))

    def update(self, dt):
        super().update(dt)

        # 更新旋转角度
        self.current_angle += self.rotation_speed * dt
        self.image = pygame.transform.rotate(self.base_image, -self.current_angle)
        self.rect = self.image.get_rect(center=self.rect.center)
        self.direction = Vector2(1, 0).rotate(self.current_angle)
        self.mask = pygame.mask.from_surface(self.image)


class MineBullet(EnemyBullet):
    def __init__(self, pos, delay=2.0, color=(255, 255, 0)):
        super().__init__(pos, Vector2(0, 1), speed=0, color=color)
        self.delay = delay
        self.timer = 0.0
        self.exploded = False

    def update(self, dt):
        self.timer += dt
        if self.timer >= self.delay and not self.exploded:
            self._explode()
            self.exploded = True
            # 在 _explode 里已经把自己从组里移除，或在这里调用
            self.kill()

    def _explode(self):
        # 先把自己要从组里移除的操作留到外面 kill()
        # 遍历自己当前所属的所有组，将新子弹加进去
        groups = list(self.groups())
        for angle in range(0, 360, 30):
            direction = Vector2(1, 0).rotate(angle)
            new_bullet = EnemyBullet(
                self.rect.center, direction, speed=350, color=self.color
            )
            for group in groups:
                group.add(new_bullet)


class BlackHole(pygame.sprite.Sprite):
    def __init__(self, pos):
        super().__init__()
        self.pos = Vector2(pos)
        self.radius = 0
        self.max_radius = 300
        self.duration = 4.0
        self.timer = 0.0
        self.pull_force = 800
        self.image = pygame.Surface((8, 8))
        self.image.fill((118, 59, 191))
        self.rect = self.image.get_rect(center=pos)

    def update(self, dt):
        self.timer += dt
        self.radius = self.max_radius * (self.timer / self.duration)

        # 引力作用
        for sprite in self.groups()[0]:
            vec = self.pos - Vector2(sprite.rect.center)
            distance = vec.length()

            # 添加安全距离检查
            if distance == 0:
                continue  # 完全重合时跳过

            # 影响玩家
            # if isinstance(sprite, Player) and distance < self.radius + 50:
            #     force = self.pull_force * (1 - distance / (self.radius + 50))
            #     if vec.length() > 0:  # 安全规范化
            #         sprite.velocity += vec.normalize() * force * dt

            # 影响子弹（直接修改位置）
            elif (
                isinstance(sprite, EnemyBullet) or isinstance(sprite, Bullet)
            ) and distance < self.radius + 50:
                force = self.pull_force * (1 - distance / (self.radius + 50)) * 0.5
                if vec.length() > 0:  # 安全规范化
                    sprite.rect.center += vec.normalize() * force * dt

        if self.timer >= self.duration:
            self.kill()


class Shockwave(EnemyBullet):
    def __init__(self, pos, speed, width, color):
        super().__init__(pos, Vector2(0, 1), speed, color)
        self.image = pygame.Surface((width, 30), pygame.SRCALPHA)
        pygame.draw.rect(self.image, (*color, 100), (0, 0, width, 30))
        self.rect = self.image.get_rect(center=pos)
        self.mask = pygame.mask.from_surface(self.image)

    def update(self, dt):
        self.rect.y += self.velocity.y * dt
        if self.rect.top > Config.HEIGHT:
            self.kill()


class MirrorBullet(EnemyBullet):
    def __init__(self, pos, direction, bounce=3, **kwargs):
        super().__init__(pos, direction, **kwargs)
        self.max_bounce = bounce
        self.bounce_count = 0

    def update(self, dt):
        old_center = self.rect.center
        self.rect.center += self.velocity * dt

        # 水平反弹
        if self.rect.left < 0 or self.rect.right > Config.WIDTH:
            self.velocity.x *= -1
            self.bounce_count += 1
            self.rect.center = old_center

        # 垂直反弹
        if self.rect.top < 0 or self.rect.bottom > Config.HEIGHT:
            self.velocity.y *= -1
            self.bounce_count += 1
            self.rect.center = old_center

        if self.bounce_count >= self.max_bounce:
            self.kill()
