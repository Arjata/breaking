import pygame
from pygame.locals import *
from ..core.config import Config


class GameOverScene:
    def __init__(self, game):
        self.game = game
        self.font = pygame.font.Font(None, 72)  # 主标题字体
        self.info_font = pygame.font.Font(None, 36)  # 分数信息字体

    def handle_event(self, event):
        if event.type == KEYDOWN:
            if event.key == K_r:  # R键重启
                from .game_scene import GameScene

                self.game.change_scene(GameScene(self.game))
            elif event.key == K_ESCAPE:  # ESC退出
                self.game.running = False

    def update(self, dt):
        pass

    def render(self, surface):
        surface.fill((0, 0, 0))

        # 获取分数数据
        score_manager = self.game.score_manager
        current_score = score_manager.current_score
        high_scores = score_manager.high_scores
        high_score = high_scores[0]["score"] if high_scores else 0

        # 主标题
        title_text = self.font.render("GAME OVER", True, (255, 0, 0))
        title_rect = title_text.get_rect(
            center=(Config.WIDTH // 2, Config.HEIGHT // 2 - 80)
        )
        surface.blit(title_text, title_rect)

        # 当前分数
        current_text = self.info_font.render(
            f"Current Score: {current_score}", True, (255, 255, 255)
        )
        current_rect = current_text.get_rect(
            center=(Config.WIDTH // 2, Config.HEIGHT // 2 - 20)
        )
        surface.blit(current_text, current_rect)

        # 历史最高分
        high_text = self.info_font.render(
            f"High Score: {high_score}", True, (255, 255, 255)
        )
        high_rect = high_text.get_rect(
            center=(Config.WIDTH // 2, Config.HEIGHT // 2 + 20)
        )
        surface.blit(high_text, high_rect)

        # 操作提示
        prompt_text = self.info_font.render(
            "Press R to Restart | ESC to Quit", True, (200, 200, 200)
        )
        prompt_rect = prompt_text.get_rect(
            center=(Config.WIDTH // 2, Config.HEIGHT // 2 + 80)
        )
        surface.blit(prompt_text, prompt_rect)
