import pygame
import random
from random import randint

# Third-party Imports
from pygame.sprite import (
    Group,
    GroupSingle,
)  # Assuming GroupSingle might be needed later

# Local Application Imports (Ensure these paths are correct)
# It's better practice to have these at the top level of the module
try:
    from ..core.config import Config
    from ..entities.player import Player, Bullet, PowerBullet
    from ..entities.enemy import BasicEnemy, CircleEnemy, Boss
    from ..entities.bullet import EnemyBullet
    from ..managers.spawner import Spawner
    from ..managers.particle import HitParticle
    from ..entities.damage_text import DamageText
    from .game_over_scene import GameOverScene
    from ..entities.powerup import PowerUp
    from ..ui.hud import HUD  # Moved import

    # Assuming ParallaxLayer class is defined in this file or imported correctly
except ImportError as e:
    print(f"Error importing modules: {e}")
    # Handle import errors appropriately, maybe raise exception or exit


class GameScene:
    def __init__(self, game):  # game 参数用于访问全局对象如 score_manager
        self.game = game  # 保存游戏实例引用

        # --- 重置分数管理器 ---
        # 在场景初始化时重置分数和连击
        self.game.score_manager.reset()
        # ----------------------

        # 玩家相关
        self.player = Player((Config.WIDTH // 2, Config.HEIGHT - 80))
        # 使用 GroupSingle 更适合单个玩家精灵的管理和绘制
        self.player_group = GroupSingle(self.player)

        # 弹幕组
        self.bullets = Group()  # 玩家子弹
        self.enemy_bullets = Group()  # 敌人子弹

        # 敌机系统
        self.enemies = Group()
        self.spawner = Spawner()

        # 渲染组 (注意：原始代码的 all_sprites 使用方式效率不高)
        self.all_sprites = Group()  # 这个组在原始代码中管理方式需要优化
        self.all_sprites.add(self.player)  # 初始添加玩家

        # 效果组
        self.particles = Group()  # 粒子效果
        self.damage_numbers = pygame.sprite.Group()  # 伤害文字
        self.powerups = Group()  # 道具

        # 背景层
        self.background_layers = []
        # 检查配置项决定是否加载背景
        if Config.ENABLE_BACKGROUND:
            self.background_layers = [
                # 确保路径相对于项目根目录或资源目录正确
                ParallaxLayer("bg_layer1.png", 0.5),
                ParallaxLayer("bg_layer2.png", 0.8),
                ParallaxLayer("bg_layer3.png", 1.2),
            ]

        # 关卡/难度控制 (示例)
        self.current_wave = 0
        self.difficulty_curve = [
            {"enemy_count": 5, "enemy_type": "basic"},
            {"enemy_count": 8, "enemy_type": "circle"},
            {"boss_spawn": True},
        ]

        # 初始化HUD (需要访问 game.score_manager 来显示分数/连击)
        self.hud = HUD(self.game)  # HUD 可以从 self.game.score_manager 获取信息

    def handle_event(self, event):
        # 处理键盘按下/释放等离散事件
        # (原始代码中的连续检测已移至 update)
        # 如果需要处理特定按键事件（如暂停 P 键），可以在这里添加
        # self.player.handle_event(event) # 让玩家也处理事件（例如特殊技能触发）
        pass  # 保持和原始代码一致，主要处理在 update

    def update(self, dt):
        # 检查玩家是否存活
        if not self.player.alive():  # 使用 sprite.alive() 更标准
            self.game.score_manager.save_high_score("player0")
            # 重要：在切换场景前可以进行一些清理或状态保存
            self.game.change_scene(GameOverScene(self.game))  # 切换到结束场景
            return  # 玩家死亡，停止当前场景更新

        # --- 更新背景 ---
        if Config.ENABLE_BACKGROUND:
            for layer in self.background_layers:
                layer.update(dt)

        # --- 关卡进度控制 (示例，原始代码已注释) ---
        # if not self.spawner.active_boss:
        #     self._progress_difficulty()

        # --- 玩家输入与更新 ---
        keys = pygame.key.get_pressed()
        self.player.handle_movement_input(keys, dt)  # 处理移动等连续输入
        self.player.shoot(self.bullets)
        # 射击逻辑：原始代码在此处调用，但更适合放在 handle_input 或 Player.update 中
        # self.player.shoot(self.bullets) # 假设 Player.shoot 会将子弹添加到 self.bullets
        # 确保Player.shoot由某个机制（如按键、计时器）触发

        # --- 更新游戏对象 ---
        # self.player.update(dt) # GroupSingle.update 会调用其包含的 sprite 的 update
        self.player_group.update(dt)
        self.bullets.update(dt)

        # --- 敌机系统更新 ---
        self.spawner.update(dt, self.enemies)  # Spawner 添加敌人到 self.enemies
        # 敌人更新（移动、AI、射击），需要玩家位置信息
        self.enemies.update(dt, self.player.rect.center)  # 假设 Enemy.update 处理这些

        # --- 敌机射击 (原始方式，建议移入 Enemy.update) ---
        for enemy in self.enemies:
            # 假设 Enemy 有 shoot_pattern 方法，并将子弹加入 self.enemy_bullets
            enemy.shoot_pattern(self.enemy_bullets)
        self.enemy_bullets.update(dt)  # 更新所有敌方子弹

        # --- 渲染组管理 (原始方式，效率低) ---
        # 清空再添加效率很低，最好在对象创建/销毁时管理组
        try:
            self.all_sprites.empty()
        except KeyError:
            pass
        self.all_sprites.add(self.player)
        self.all_sprites.add(
            self.enemies, self.bullets, self.enemy_bullets, self.powerups
        )
        # ----------------------------------

        # --- 碰撞检测 ---
        self._check_collisions()  # 处理所有碰撞逻辑

        # --- 更新效果 ---
        self.damage_numbers.update(dt)  # 更新伤害文字动画
        self.particles.update(dt)  # 更新粒子动画

        # --- 清理死亡粒子 (原始方式，建议粒子自毁) ---
        # 假设粒子在 update 中判断是否结束生命并调用 self.kill()
        # for p in self.particles:
        #     if not p.alive():
        #         self.particles.remove(p) # Group 会自动处理 kill() 的精灵
        # ---------------------------------------

        # --- 更新道具 ---
        self.powerups.update(dt)

        # --- 更新HUD ---
        self.hud.update(dt)  # 更新HUD显示内容（分数、连击等）

    def _check_collisions(self):
        # --- 玩家被敌方子弹击中 ---
        # 假设 Player.take_damage 处理扣血、无敌帧等逻辑
        player_hits = pygame.sprite.spritecollide(
            self.player,
            self.enemy_bullets,
            True,  # 子弹碰撞后消失
            collided=pygame.sprite.collide_rect_ratio(0.7),
        )
        if player_hits and not self.player.invincible:  # 检查无敌状态
            # 传递伤害值，假设敌方子弹伤害为1
            self.player.take_damage(1)
            # 可能触发玩家受伤音效或特效

        # --- 玩家子弹击中敌机 ---
        # groupcollide 返回字典 {bullet: [enemy_list]}
        collisions = pygame.sprite.groupcollide(
            self.bullets,  # 玩家子弹组
            self.enemies,  # 敌机组
            True,  # 玩家子弹碰撞后消失
            False,  # 敌机碰撞后不消失 (由HP判断)
            collided=pygame.sprite.collide_rect,  # 或其他碰撞函数
        )

        # 处理击中效果
        for bullet, enemies_hit in collisions.items():
            for enemy in enemies_hit:
                if not enemy.alive():
                    continue  # 如果敌机在本帧已被标记为死亡则跳过

                damage = bullet.damage  # 获取子弹伤害
                enemy.take_damage(damage)  # 敌机处理伤害和HP

                # --- 生成伤害数字 ---
                is_critical = bullet.is_critical
                self.damage_numbers.add(
                    DamageText(enemy.rect.center, damage, is_critical)
                )

                # --- 生成击中粒子 ---
                for _ in range(5):  # 创建少量击中粒子
                    self.particles.add(
                        HitParticle(bullet.rect.center)
                    )  # 在子弹位置生成

                # --- 屏幕震动 (击中) ---
                # 使用 self.game 引用调用 Game 对象的震动方法
                self.game.apply_screen_shake(intensity=3, duration=0.1)

                # --- 检查敌机是否死亡 ---
                if not enemy.alive():  # 如果 take_damage 方法导致敌机死亡
                    self.player.killed_enemy_count += 1
                    # --- 增加分数 ---
                    # 使用 self.game.score_manager 增加分数
                    # enemy.score_value 是敌机应有的属性
                    if hasattr(enemy, "score_value"):
                        self.game.score_manager.add_score(enemy.score_value)
                    else:
                        print(
                            f"Warning: Enemy {type(enemy).__name__} missing score_value attribute."
                        )
                        self.game.score_manager.add_score(10)  # 默认分数
                    # ---------------

                    # --- 死亡特效 ---
                    # 大爆炸粒子
                    for _ in range(20):
                        self.particles.add(
                            HitParticle(enemy.rect.center, color=(255, 150, 0))
                        )
                    # 屏幕震动 (死亡)
                    self.game.apply_screen_shake(8, 0.3)

                    # --- 道具掉落 ---
                    # PowerUp.DROP_CHANCE 应在 PowerUp 类中定义
                    if random.random() < getattr(
                        PowerUp, "DROP_CHANCE", 0.1
                    ):  # 使用 getattr 提供默认值
                        self.powerups.add(
                            PowerUp(enemy.rect.center)
                        )  # 在敌机位置生成道具

                    # print(f"击破 {type(enemy).__name__} 获得分数") # 打印信息已包含在 score_manager 中

        # --- 敌机与玩家碰撞 ---
        enemy_player_hits = pygame.sprite.spritecollide(
            self.player,
            self.enemies,
            False,  # 玩家不消失
            collided=pygame.sprite.collide_rect_ratio(0.6),
        )
        if enemy_player_hits and not self.player.invincible:
            for enemy in enemy_player_hits:
                # 玩家承受碰撞伤害
                # enemy.collision_damage 应是敌机属性
                collision_dmg = getattr(enemy, "collision_damage", 2)  # 提供默认伤害
                self.player.take_damage(collision_dmg)

                # 特定类型敌机（如基础敌机）碰撞后自毁
                if isinstance(
                    enemy, BasicEnemy
                ):  # 或者检查敌机是否有 destroy_on_collision 标志
                    enemy.kill()  # 敌机自毁

                # 碰撞可能也触发屏幕震动
                self.game.apply_screen_shake(intensity=5, duration=0.15)
                # 避免一帧内因碰撞多次触发伤害，加短暂无敌或break
                break  # 假设一次碰撞只处理一个敌人

        # --- 玩家拾取道具 ---
        powerup_collected = pygame.sprite.spritecollide(
            self.player,
            self.powerups,
            True,  # 道具拾取后消失
            collided=pygame.sprite.collide_circle_ratio(0.8),  # 假设道具是圆形碰撞
        )
        for powerup in powerup_collected:
            # Player 类需要有 apply_powerup 方法
            # self.player.apply_powerup(powerup.type, 10)  # 应用道具效果
            powerup.apply_effect(self.player)  # 正确调用方式
            # 播放拾取音效/特效

    def render(self, surface):
        # 1. 渲染背景
        if Config.ENABLE_BACKGROUND:
            for layer in self.background_layers:
                layer.render(surface)

        # 2. 渲染所有游戏世界精灵 (使用原始的 all_sprites)
        self.all_sprites.draw(surface)

        # 3. 渲染非 sprite 组的 UI 元素或特效
        # 绘制血条 (应在对应对象的方法中实现)
        self.player.draw_health_bar(surface)
        for enemy in self.enemies:
            if isinstance(enemy, Boss):  # 只为 Boss 绘制血条
                enemy.draw_health_bar(surface)

        # 渲染粒子和伤害数字 (虽然是 Group，但可能需要在特定层级绘制)
        self.particles.draw(surface)
        self.damage_numbers.draw(surface)

        # 4. 渲染 HUD (最顶层)
        self.hud.draw(surface)  # HUD 绘制分数、连击、生命等信息

    def _progress_difficulty(self):
        """根据当前波次提升难度 (原始代码逻辑)"""
        # 确保 self.current_wave 不会超出 difficulty_curve 的索引范围
        wave_index = min(self.current_wave, len(self.difficulty_curve) - 1)
        wave_data = self.difficulty_curve[wave_index]

        # 假设 Spawner 有处理这些配置的方法
        if "boss_spawn" in wave_data and wave_data["boss_spawn"]:
            self.spawner.spawn_boss(self.enemies)  # 假设 spawner 有 spawn_boss 方法
        elif "enemy_count" in wave_data and "enemy_type" in wave_data:
            self.spawner.set_wave_config(
                wave_data["enemy_count"], wave_data["enemy_type"]
            )  # 假设 spawner 有此方法
        else:
            print(
                f"Warning: Invalid wave data format for wave {self.current_wave}: {wave_data}"
            )

        # 如果不是最后一波，或者需要循环/增加难度，则增加波次计数
        if self.current_wave < len(self.difficulty_curve):  # 或者其他逻辑判断是否结束
            self.current_wave += 1


class ParallaxLayer:
    """视差背景层 (已优化硬件加速)"""

    def __init__(self, image_path, speed_factor):
        try:
            # 1. 加载原始图像
            loaded_image = pygame.image.load(f"assets/backgrounds/{image_path}")
        except pygame.error as e:
            print(f"错误：无法加载图像 '{image_path}'. Pygame Error: {e}")
            # 创建一个占位符表面以避免崩溃
            loaded_image = pygame.Surface((Config.WIDTH, Config.HEIGHT))
            loaded_image.fill((128, 0, 128))  # 用紫色填充，表示错误

        # 2. 缩放图像以适应屏幕（或你想要的大小）
        scaled_image = pygame.transform.scale(
            loaded_image, (Config.WIDTH, Config.HEIGHT)
        )

        # --- 关键优化：转换为硬件加速格式 ---
        # 如果图像没有透明度 (e.g., JPG), 使用 convert()
        # 如果图像有透明度 (e.g., PNG with alpha channel), 使用 convert_alpha()
        # 根据你的图像文件类型选择
        try:
            # 尝试 convert_alpha()，因为它更通用，能处理带或不带 alpha 的图像
            self.image = scaled_image.convert_alpha()
            print(f"图像 '{image_path}' 已使用 convert_alpha() 优化。")
        except pygame.error:
            # 如果 convert_alpha() 失败（可能发生在没有 alpha 的表面上），回退到 convert()
            self.image = scaled_image.convert()
            print(f"图像 '{image_path}' 已使用 convert() 优化。")
        # -----------------------------------------

        self.speed_factor = speed_factor
        self.offset = 0.0  # 使用浮点数以获得更平滑的滚动
        self.tile_height = self.image.get_height()
        # 不再需要将 self.rect 作为移动状态存储

    def update(self, dt):
        """根据时间增量 (dt) 更新层的偏移量"""
        # 使用浮点数计算，乘以 dt 实现帧率无关的移动
        self.offset += 100.0 * dt * self.speed_factor
        # 使用取模运算 (%) 使偏移量在 [0, tile_height) 范围内循环
        self.offset %= self.tile_height

    def render(self, surface):
        """将层渲染（绘制）到目标表面上"""
        # 计算两个瓦片的位置以实现无缝滚动
        # 第一个瓦片的位置
        y1 = -self.offset
        # 第二个瓦片的位置，紧跟在第一个瓦片下方
        y2 = self.tile_height - self.offset

        # --- 优化：直接使用计算出的坐标进行 blit ---
        surface.blit(self.image, (0, y1))
        surface.blit(self.image, (0, y2))
        # ------------------------------------------
