import pygame
import math
from random import uniform
from pygame.math import Vector2
from ..core.config import Config
from .bullet import *
from random import randint


class Enemy(pygame.sprite.Sprite):
    def __init__(self, pos, hp=1, score_value=100):
        super().__init__()
        self.hp = hp
        self.max_hp = hp
        self.image = pygame.Surface((32, 32))
        self._create_visual()
        self.rect = self.image.get_rect(center=pos)
        self.hitbox = self.rect.inflate(-8, -8)
        self.shoot_timer = 0
        self.speed = Vector2(0, 100)
        self.score_value = score_value
        self.player_pos = None

    def _create_visual(self):
        self.image.fill((255, 0, 0))

    def update(self, dt, player_pos=None):
        self.player_pos = player_pos
        self.shoot_timer += dt
        self.rect.y += self.speed.y * dt

    def shoot_pattern(self, bullet_group):
        raise NotImplementedError("必须实现射击模式")

    # 新增核心方法：处理伤害
    def take_damage(self, damage):
        """基础伤害处理方法"""
        self.hp -= damage
        if self.hp <= 0:
            self.kill()


class BasicEnemy(Enemy):
    def __init__(self, pos, hp=1, score_value=100):
        super().__init__(pos, hp=hp, score_value=score_value)
        self.image.fill((100, 100, 100))
        self.hitbox = self.rect.inflate(-10, -10)
        self.speed = Vector2(0, 150)

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        if self.rect.top > Config.HEIGHT:
            self.kill()

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer >= 2.0:
            bullet = EnemyBullet(
                self.rect.center, Vector2(0, 1), speed=300, color=(100, 100, 100)
            )
            bullet_group.add(bullet)
            self.shoot_timer = 0


class CircleEnemy(BasicEnemy):
    def __init__(self, pos):
        super().__init__(pos, hp=2, score_value=200)
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (255, 150, 0), (16, 16), 12)
        self.speed = Vector2(0, 300)

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer > 1.5:
            self.shoot_timer = 0
            for angle in range(0, 360, 15):
                rad = math.radians(angle)
                direction = Vector2(math.cos(rad), math.sin(rad))
                bullet_group.add(EnemyBullet(self.rect.center, direction))

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        # 添加静止状态检测
        if self.speed.length() == 0:
            self.rect.centery += 100 * dt  # 添加默认下落逻辑
        if self.rect.top > Config.HEIGHT:
            self.kill()


class ZigzagEnemy(BasicEnemy):
    """锯齿移动敌机"""

    def __init__(self, pos):
        super().__init__(pos, hp=3, score_value=150)
        self.image = pygame.Surface((32, 32), pygame.SRCALPHA)
        pygame.draw.polygon(self.image, (0, 200, 100), [(16, 0), (0, 32), (32, 32)])
        self.speed = Vector2(0, 200)
        self.amplitude = 100  # 横向摆动幅度
        self.frequency = 2  # 摆动频率

    def update(self, dt, player_pos=None):
        self.rect.y += self.speed.y * dt
        # 横向锯齿运动
        self.rect.x += (
            math.sin(pygame.time.get_ticks() * 0.001 * self.frequency)
            * self.amplitude
            * dt
        )
        if self.rect.top > Config.HEIGHT:
            self.kill()

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer >= 1.2:
            # 三向散射
            for angle in [-15, 0, 15]:
                bullet = EnemyBullet(
                    self.rect.center,
                    Vector2(0, 1).rotate(angle),
                    speed=300,
                    color=(0, 200, 100),
                )
                bullet_group.add(bullet)
            self.shoot_timer = 0


class HomingDroneEnemy(Enemy):
    """跟踪无人机"""

    def __init__(self, pos, max_alive_time=7):
        super().__init__(pos, hp=5, score_value=300)
        self.image = pygame.Surface((36, 36), pygame.SRCALPHA)
        pygame.draw.circle(self.image, (150, 50, 200), (18, 18), 15)
        pygame.draw.circle(self.image, (200, 200, 200), (18, 18), 5)
        self.speed = Vector2(0, 50)
        self.turn_speed = 90  # 转向速度度/秒
        self.max_alive_time = max_alive_time
        self.timer = 0

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        self.timer += dt
        if player_pos:
            # 向玩家方向转向
            target_vector = Vector2(player_pos) - self.rect.center
            if target_vector.length() > 0:
                target_dir = target_vector.normalize()
                current_dir = self.speed.normalize()
                angle = current_dir.angle_to(target_dir)
                max_turn = self.turn_speed * dt
                angle = max(-max_turn, min(angle, max_turn))
                self.speed = current_dir.rotate(angle) * self.speed.length()

        self.rect.center += self.speed * dt
        if self.rect.top > Config.HEIGHT:
            self.kill()
        if self.timer > self.max_alive_time:
            self.kill()

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer >= 1.8:
            # 发射跟踪导弹
            bullet = HomingEnemyBullet(
                self.rect.center,
                Vector2(0, 1),
                speed=200,
                color=(200, 100, 200),
                player_pos_ref=lambda: self.player_pos,
            )
            bullet_group.add(bullet)
            self.shoot_timer = 0


class ShieldedEnemy(BasicEnemy):
    """护盾敌机"""

    def __init__(self, pos):
        super().__init__(pos, hp=5, score_value=250)
        self.base_image = pygame.Surface((40, 40), pygame.SRCALPHA)
        # 绘制护盾效果
        pygame.draw.circle(self.base_image, (100, 100, 255, 100), (20, 20), 18)
        pygame.draw.circle(self.base_image, (0, 0, 200), (20, 20), 12)
        self.image = self.base_image.copy()
        self.shield_active = True
        self.shield_recharge_time = 5.0
        self.shield_timer = 0.0
        self.speed = Vector2(0, 50)

    def take_damage(self, damage):
        if self.shield_active:
            # 护盾存在时免疫伤害
            self.image.fill((255, 255, 255, 200), special_flags=pygame.BLEND_RGBA_MULT)
            self.shield_active = False
            # print("Block damage.")
            return
        super().take_damage(damage)
        # print(f"Take damage:{str(damage)} .")

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        # 护盾恢复逻辑
        if not self.shield_active:
            self.shield_timer += dt
            if self.shield_timer >= self.shield_recharge_time:
                self.shield_active = True
                self.image = self.base_image.copy()
                self.shield_timer = 0.0


class SpiralEnemy(CircleEnemy):
    """螺旋弹幕敌机"""

    def __init__(self, pos):
        super().__init__(pos)
        self.image.fill((0, 0, 0, 0))
        pygame.draw.polygon(self.image, (255, 100, 0), [(16, 0), (32, 32), (0, 32)])
        self.rotate_speed = 180  # 度/秒

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer > 0.8:
            # 旋转发射
            base_angle = pygame.time.get_ticks() / 1000 * self.rotate_speed
            for i in range(0, 360, 45):
                angle = base_angle + i
                direction = Vector2(1, 0).rotate(angle)
                bullet = EnemyBullet(
                    self.rect.center, direction, speed=250, color=(255, 150, 0)
                )
                bullet_group.add(bullet)
            self.shoot_timer = 0


class CarrierEnemy(Enemy):
    """母舰敌机"""

    def __init__(self, pos):
        super().__init__(pos, hp=20, score_value=500)
        self.image = pygame.Surface((64, 32))
        self.image.fill((80, 80, 80))
        pygame.draw.rect(self.image, (100, 100, 100), (0, 12, 64, 8))
        self.speed = Vector2(0, 50)
        self.drone_spawn_interval = 3.0
        self.drone_timer = 0.0

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        self.drone_timer += dt
        # 定期释放小飞机
        if self.drone_timer >= self.drone_spawn_interval:
            self._release_drones()
            self.drone_timer = 0

    def _release_drones(self):
        for i in range(-1, 2):
            pos = (self.rect.centerx + i * 20, self.rect.centery + 20)
            drone = BasicEnemy(pos, hp=1, score_value=50)
            drone.speed = Vector2(0, 200)
            self.groups()[0].add(drone)

    def shoot_pattern(self, bullet_group):
        if self.shoot_timer >= 2.5:
            # 两侧齐射
            for side in [-1, 1]:
                pos = (self.rect.centerx + side * 24, self.rect.centery)
                bullet = EnemyBullet(
                    pos, Vector2(0, 1), speed=300, color=(100, 100, 100)
                )
                bullet_group.add(bullet)
            self.shoot_timer = 0


class StealthEnemy(BasicEnemy):
    """隐形敌机"""

    def __init__(self, pos):
        super().__init__(pos, hp=2, score_value=200)
        self.alpha = 0
        self.fade_speed = 200  # 透明度变化速度（alpha/秒）
        self.is_visible = False

    def update(self, dt, player_pos=None):
        # 接近玩家时显形
        if player_pos:
            distance = Vector2(player_pos).distance_to(self.rect.center)
            if distance < 300:
                self.alpha = min(self.alpha + self.fade_speed * dt, 255)
                self.is_visible = True
            else:
                self.alpha = max(self.alpha - self.fade_speed * dt, 0)
                self.is_visible = False

            self.image.set_alpha(self.alpha)

        super().update(dt, player_pos)

    def shoot_pattern(self, bullet_group):
        if self.is_visible and self.shoot_timer >= 1.0:
            # 瞬发三向弹
            for angle in [-5, 0, 5]:
                bullet = EnemyBullet(
                    self.rect.center,
                    Vector2(0, 1).rotate(angle),
                    speed=400,
                    color=(100, 100, 100, self.alpha),
                )
                bullet_group.add(bullet)
            self.shoot_timer = 0


class Boss(Enemy):
    def __init__(self):
        super().__init__((Config.WIDTH // 2, 100), hp=50, score_value=1000)
        self.image = pygame.Surface((128, 64))
        self.image.fill((200, 50, 200))
        self.rect = self.image.get_rect(center=(Config.WIDTH // 2, 100))
        self.phase = 1
        self.move_speed = 150
        self.move_range = 300
        self.base_y = 100
        self.direction = 1
        self.attack_speed = 0.8  # 初始攻击间隔
        self.attack_timer = 0.0
        self.attack_patterns = []
        self.bullets_groups = []

        # 激光相关属性
        self.laser_duration = 1.5
        self.laser_cooldown = 5.0
        self.laser_timer = 0.0
        self.attack_patterns = []
        # 新增属性
        self.minion_spawn_timer = 0.0
        # self.minion_spawn_interval = 8.0
        self.blackhole_timer = 0.0
        self.blackhole_cooldown = 15.0
        self.max_phase = 4
        self.phase_callback = {}
        for i in range(1, self.max_phase + 1):
            self.phase_callback[i] = []
        # 新增敌人组引用
        self.enemies_group = None  # 将在初始化时注入
        # 调整召唤间隔为更合理的值
        self.minion_spawn_interval = 5.0  # 5秒召唤一次

    def add_phase_callback(self, phase: int, callback: any):
        self.phase_callback[self.phase].append(callback)

    def take_damage(self, damage):  # 重写Boss的伤害处理
        super().take_damage(damage)
        if (
            self.hp <= self.max_hp * 0.5
            and self.hp > self.max_hp * 0.3
            and self.phase != 2
        ):
            self.phase = 2
            self.image.fill((150, 0, 200))
            for _phase_callback in self.phase_callback[self.phase]:
                _phase_callback()
        elif (
            self.hp <= self.max_hp * 0.3
            and self.hp > self.max_hp * 0.1
            and self.phase != 3
        ):
            self.phase = 3
            self.image.fill((255, 255, 150))
            for _phase_callback in self.phase_callback[self.phase]:
                _phase_callback()
        elif self.hp <= self.max_hp * 0.1 and self.phase != 4:
            self.phase = 4
            self.image.fill((255, 0, 100))
            for _phase_callback in self.phase_callback[self.phase]:
                _phase_callback()

    def update(self, dt, player_pos=None):
        super().update(dt, player_pos)
        self._handle_movement(dt)
        self.attack_timer += dt
        self.laser_timer += dt

        # 处理激光攻击
        if self.phase == 2 and self.laser_timer >= self.laser_cooldown:
            self._laser_attack(self.bullets_groups[0])
            self.laser_timer = 0.0

        # 常规攻击模式
        if self.attack_timer >= self.attack_speed:
            self.shoot(self.bullets_groups)
            self.attack_timer = 0

        # 新增子系统计时器
        self.minion_spawn_timer += dt
        self.blackhole_timer += dt

        # 修改召唤条件判断
        if self.phase >= 2 and self.enemies_group:
            if self.minion_spawn_timer >= self.minion_spawn_interval:
                self._summon_minions()
                self.minion_spawn_timer = 0.0

        # 黑洞攻击系统
        if self.phase >= 3 and self.blackhole_timer >= self.blackhole_cooldown:
            self._blackhole_attack(self.bullets_groups[0])
            self.blackhole_timer = 0.0

    def _handle_movement(self, dt):
        move_amount = self.move_speed * self.direction * dt
        new_x = self.rect.centerx + move_amount
        left_bound = Config.WIDTH // 2 - self.move_range // 2
        right_bound = Config.WIDTH // 2 + self.move_range // 2

        if new_x < left_bound:
            new_x = left_bound
            self.direction = 1
        elif new_x > right_bound:
            new_x = right_bound
            self.direction = -1

        self.rect.centerx = new_x
        self.rect.centery = self.base_y + 20 * math.sin(pygame.time.get_ticks() / 300)

    def _spread_attack(self, bullet_group):
        if self.player_pos:
            direction = Vector2(self.player_pos) - self.rect.center
            if direction.length() > 0:
                direction = direction.normalize()
                for angle in [-15, 0, 15]:
                    rotated = direction.rotate(angle)
                    bullet_group.add(
                        EnemyBullet(self.rect.center, rotated, color=(255, 0, 200))
                    )

    def _spiral_attack(self, bullet_group):
        angle = pygame.time.get_ticks() % 360 * 3
        rad = math.radians(angle)
        direction = Vector2(math.cos(rad), math.sin(rad))
        bullet_group.add(
            EnemyBullet(self.rect.center, direction, speed=350, color=(50, 200, 255))
        )

    def shoot_pattern(self, bullet_group):
        if len(self.bullets_groups) >= 3:
            self.bullets_groups.clear()
        self.bullets_groups.append(bullet_group)

    def shoot(self, bullets_groups):
        for attack_pattern in self.attack_patterns:
            for bullets_group in bullets_groups:
                attack_pattern(bullets_group)

    def draw_health_bar(self, surface):
        """在屏幕顶部绘制Boss血条"""
        bar_width = 400
        bar_height = 20
        pos = (Config.WIDTH // 2 - bar_width // 2, 20)

        # 背景
        pygame.draw.rect(surface, (80, 0, 0), (*pos, bar_width, bar_height))
        # 当前血量
        fill_width = bar_width * (self.hp / self.max_hp)
        pygame.draw.rect(surface, (200, 50, 200), (*pos, fill_width, bar_height))

    def _ring_attack(self, bullet_group):
        """环形弹幕攻击"""
        num_bullets = 24
        for angle in range(0, 360, 360 // num_bullets):
            rad = math.radians(angle)
            direction = Vector2(math.cos(rad), math.sin(rad))
            bullet = EnemyBullet(
                self.rect.center, direction, speed=250, color=(255, 150, 0)
            )
            bullet_group.add(bullet)

    def _homing_attack(self, bullet_group):
        """跟踪导弹攻击"""
        if self.player_pos:
            initial_dir = Vector2(0, 1)  # 初始向下
            bullet = HomingEnemyBullet(
                self.rect.center,
                initial_dir,
                speed=200,
                color=(255, 0, 150),
                player_pos_ref=lambda: self.player_pos,
            )
            bullet_group.add(bullet)

    def _bounce_attack(self, bullet_group):
        """弹跳子弹攻击"""
        angle = uniform(-45, 45)
        direction = Vector2(1, 0).rotate(angle)  # 随机水平方向
        bullet = BounceEnemyBullet(
            self.rect.center, direction, speed=300, color=(0, 0, 255)
        )
        bullet_group.add(bullet)

    def _shotgun_attack(self, bullet_group):
        """散弹枪式扇形攻击"""
        if self.player_pos:
            base_dir = (Vector2(self.player_pos) - self.rect.center).normalize()
            for angle in range(-60, 61, 15):
                spread_dir = base_dir.rotate(angle)
                bullet = EnemyBullet(
                    self.rect.center,
                    spread_dir,
                    speed=400 + randint(-50, 50),
                    color=(randint(100, 255), 0, 0),
                )
                bullet_group.add(bullet)

    def _laser_attack(self, bullet_group):
        """激光束攻击"""
        if self.player_pos:
            direction = (Vector2(self.player_pos) - self.rect.center).normalize()
            laser = LaserBeam(
                self.rect.center,
                direction,
                duration=self.laser_duration,
                width=15,
                color=(255, 50, 50),
            )
            bullet_group.add(laser)

    def _minefield_attack(self, bullet_group):
        """地雷阵攻击"""
        for _ in range(3):
            pos = (
                self.rect.centerx + randint(-200, 200),
                self.rect.centery + randint(50, 150),
            )
            mine = MineBullet(pos, delay=1.5 + uniform(0, 1.5), color=(255, 255, 0))
            bullet_group.add(mine)

    def _cross_lasers_attack(self, bullet_group):
        """十字交叉激光"""
        for angle in [0, 90, 180, 270]:
            direction = Vector2(1, 0).rotate(angle)
            laser = RotatingLaser(
                self.rect.center,
                direction,
                rotation_speed=45 if self.phase == 1 else 90,
                duration=2.0,
                color=(255, 100, 200),
            )
            bullet_group.add(laser)

    def _matrix_attack(self, bullet_group):
        """矩阵弹幕"""
        cols = 5
        rows = 3
        spacing = 80
        offset = pygame.time.get_ticks() % 2000 / 2000 * spacing

        for x in range(cols):
            for y in range(rows):
                pos = (x * spacing + offset - 200, y * spacing + offset + 50)
                direction = Vector2(0, 1).rotate(uniform(-5, 5))
                bullet = EnemyBullet(
                    (pos[0] + self.rect.centerx - 200, pos[1]),
                    direction,
                    speed=250,
                    color=(x * 50, y * 80, 150),
                )
                bullet_group.add(bullet)

    def _summon_minions(self):
        """召唤护卫机（修正组引用）"""
        for side in [-1, 1]:
            pos = (self.rect.centerx + side * 150, self.rect.centery + 80)
            minion = CircleEnemy(pos)
            minion.speed = Vector2(0, 0)
            minion.hp = 3
            self.enemies_group.add(minion)  # 添加到正确的敌人组

    def _blackhole_attack(self, bullet_group):
        """黑洞引力攻击"""
        blackhole_pos = (
            self.rect.centerx + randint(-200, 200),
            self.rect.centery + 150,
        )
        bullet_group.add(BlackHole(blackhole_pos))

    def _time_bomb_attack(self, bullet_group):
        """定时爆破弹"""
        bomb = TimeBombBullet(
            self.rect.center, delay=2.0, sub_bullets=8, color=(200, 0, 200)
        )
        bullet_group.add(bomb)

    def _rotating_shield(self, bullet_group):
        """旋转护盾弹幕"""
        radius = 80
        angle = pygame.time.get_ticks() % 360 * 2
        for _ in range(8):
            pos = self.rect.center + Vector2(
                radius * math.cos(math.radians(angle)),
                radius * math.sin(math.radians(angle)),
            )
            bullet = EnemyBullet(pos, Vector2(0, 1), speed=200, color=(0, 200, 200))
            bullet_group.add(bullet)
            angle += 45

    def _homing_ring(self, bullet_group):
        """追踪环形弹"""
        num = 12
        base_angle = pygame.time.get_ticks() % 360 * 0.5
        for i in range(num):
            angle = base_angle + i * (360 / num)
            direction = Vector2(1, 0).rotate(angle)
            bullet = HomingEnemyBullet(
                self.rect.center,
                direction,
                speed=180,
                color=(255, 150, 0),
                player_pos_ref=lambda: self.player_pos,
                delay=1.0,  # 1秒后开始追踪
            )
            bullet_group.add(bullet)

    def _shockwave_attack(self, bullet_group):
        """全屏震荡波"""
        wave = Shockwave(
            self.rect.center, speed=200, width=Config.WIDTH, color=(150, 150, 255)
        )
        bullet_group.add(wave)

    def _mirror_attack(self, bullet_group):
        """镜像反射弹"""
        if self.player_pos:
            mirror_count = 3
            for i in range(mirror_count):
                offset = (i - mirror_count // 2) * 50
                pos = (self.rect.centerx + offset, self.rect.centery)
                direction = (Vector2(self.player_pos) - pos).normalize()
                bullet = MirrorBullet(
                    pos, direction, bounce=3, color=(200, 200, 0)  # 最大反弹次数
                )
                bullet_group.add(bullet)

    def _dna_attack(self, bullet_group):
        """DNA螺旋弹幕"""
        num = 30
        for i in range(num):
            angle = i * 137.5  # 黄金角度
            radius = i * 3
            x = radius * math.cos(math.radians(angle))
            y = radius * math.sin(math.radians(angle))
            pos = self.rect.center + Vector2(x, y)
            direction = Vector2(
                math.cos(math.radians(angle + 90)), math.sin(math.radians(angle + 90))
            ).normalize()
            bullet = EnemyBullet(
                pos, direction, speed=250 + i * 2, color=(i * 8, 150 - i * 5, 200)
            )
            bullet_group.add(bullet)

    def set_enemies_group(self, group):
        """设置敌人组的引用"""
        self.enemies_group = group
