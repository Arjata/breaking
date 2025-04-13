from src.core.game import Game
from src.scenes.game_scene import GameScene

if __name__ == "__main__":
    game = Game()
    game.change_scene(GameScene(game))  # 传递game实例
    game.run()