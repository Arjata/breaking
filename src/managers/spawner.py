# src/managers/spawner.py
import pygame
import random
import math
from pygame.math import Vector2
from ..core.config import Config
from ..entities.enemy import *


class Spawner:
    def __init__(self):
        self.wave = 0  # 当前波次（从0开始计数）
        self.boss_wave_interval = 5  # 每5波生成BOSS
        self.spawn_timer = 0.0
        self.base_spawn_interval = 10.0
        self.active_boss = None  # 当前活跃的BOSS

        # 难度曲线参数
        self.difficulty_curve = {
            "base_enemies": 5,  # 基础敌机数量
            "enemy_hp_growth": 0.05,  # 每波血量增长10%
            "speed_growth": 0.03,  # 每波速度增长3%
            "phase_multiplier": 1.5,  # 每阶段难度倍率
        }

    def get_current_phase(self):
        """计算当前阶段（每5波为一个阶段）"""
        return math.floor(self.wave / self.boss_wave_interval) + 1

    def update(self, dt, enemy_group):
        """更新生成逻辑"""
        self.spawn_timer += dt

        # BOSS存活期间暂停生成普通敌机
        if self.active_boss and self.active_boss.alive():
            return

        current_phase = self.get_current_phase()

        # BOSS波次处理
        if self.wave % self.boss_wave_interval == 0 and self.wave > 0:
            if not self.active_boss:
                self._spawn_boss(enemy_group, current_phase)
        else:
            # 动态调整普通波次生成间隔
            spawn_interval = self.base_spawn_interval / math.log(current_phase + 1)
            if self.spawn_timer >= spawn_interval:
                self._spawn_wave(enemy_group, current_phase)
                self.spawn_timer = 0.0
                self.wave += 1

        if (
            self.wave % self.boss_wave_interval == 0
            and self.wave > 0
            and isinstance(self.active_boss, Boss)
            and not self.active_boss.alive()
        ):
            self.wave += 1
            self.active_boss = None

    def _spawn_wave(self, enemy_group, phase):
        """生成普通敌机波次"""
        wave_config = self._generate_wave_config(phase)

        for _ in range(wave_config["count"]):
            enemy = self._create_enemy(wave_config)
            enemy_group.add(enemy)

    def _generate_wave_config(self, phase):
        """生成波次配置"""
        base = self.difficulty_curve["base_enemies"]
        return {
            "count": math.floor(
                base * (phase ** self.difficulty_curve["phase_multiplier"])
            ),
            "enemy_types": self._get_available_enemies(phase),
            "hp_multiplier": (1 + self.difficulty_curve["enemy_hp_growth"])
            ** self.wave,
            "speed_multiplier": (1 + self.difficulty_curve["speed_growth"])
            ** self.wave,
        }

    def _get_available_enemies(self, phase):
        """根据阶段解锁敌机类型"""
        types = [BasicEnemy, ShieldedEnemy]
        if phase >= 2:
            types.extend([ZigzagEnemy])
        if phase >= 3:
            types.extend([HomingDroneEnemy, SpiralEnemy, CarrierEnemy])
        if phase >= 4:
            types.extend([CircleEnemy, StealthEnemy])
        # phase >=4 可添加新敌机类型
        return types

    def _create_enemy(self, wave_config):
        """创建敌机实例并应用难度增强"""
        EnemyClass = random.choice(wave_config["enemy_types"])
        pos = Vector2(
            random.randint(50, Config.WIDTH - 50),
            random.randint(-300, -100),  # 更高的生成位置
        )

        enemy = EnemyClass(pos)
        enemy.hp *= wave_config["hp_multiplier"]
        enemy.speed *= wave_config["speed_multiplier"]
        enemy.score_value = int(enemy.score_value * (1.1**self.wave))
        return enemy

    def _spawn_boss(self, enemy_group, phase):
        """生成阶段BOSS"""
        self.active_boss = Boss()
        self.active_boss.set_enemies_group(enemy_group)

        # BOSS强化参数
        boss_multiplier = phase**1.3
        self.active_boss.max_hp *= boss_multiplier * 5
        self.active_boss.hp = self.active_boss.max_hp
        self.active_boss.attack_speed /= math.sqrt(phase)
        self.active_boss.score_value *= phase
        self.active_boss.attack_patterns = [self.active_boss._spiral_attack]

        # 添加阶段专属攻击模式
        if phase >= 2:
            self.active_boss.attack_patterns.extend([self.active_boss._spread_attack])
            self.active_boss.add_phase_callback(
                2,
                lambda p: self.active_boss.attack_patterns.extend(
                    [self.active_boss._ring_attack]
                ),
            )
        if phase >= 3:
            self.active_boss.attack_patterns.extend([self.active_boss._homing_attack])
            self.active_boss.add_phase_callback(
                2,
                lambda p: self.active_boss.attack_patterns.extend(
                    [self.active_boss._bounce_attack]
                ),
            )
        if phase >= 4:
            self.active_boss.attack_patterns.extend(
                [
                    self.active_boss._minefield_attack,  # 新增地雷阵
                ]
            )
            self.active_boss.add_phase_callback(
                3,
                lambda p: self.active_boss.attack_patterns.extend(
                    [
                        self.active_boss._cross_lasers_attack,  # 新增交叉激光
                    ]
                ),
            )
            self.active_boss.add_phase_callback(
                4,
                lambda p: self.active_boss.attack_patterns.extend(
                    [
                        self.active_boss._matrix_attack,  # 新增矩阵弹幕
                        self.active_boss._homing_ring,
                    ]
                ),
            )

        enemy_group.add(self.active_boss)
        print(f"⚡ 第{phase}阶段BOSS登场！当前波次：{self.wave}")

    def reset(self):
        """重置生成器状态"""
        self.wave = 0
        self.spawn_timer = 0.0
        self.active_boss = None
