import json
from pathlib import Path
import pygame
import time


class ScoreManager:
    HIGH_SCORES_FILE = Path("data/highscores.json")

    def __init__(self):
        """初始化分数管理器"""
        self.current_score = 0
        self.combo = 0
        self.last_hit_time = 0.0  # 使用浮点数以便更精确地比较时间
        self.combo_timeout = 2.0  # 连击有效时间（秒）
        self.high_scores = self.load_high_scores()

    def reset(self):
        """
        重置当前游戏的分数和连击状态，准备开始新游戏。
        最高分记录不会被重置。
        """
        self.current_score = 0
        self.combo = 0
        # last_hit_time 设为 0 或一个足够早的时间，
        # 以确保游戏开始时的第一次得分能正确启动连击计数。
        self.last_hit_time = 0.0
        print("ScoreManager reset.")  # 添加打印信息方便调试

    def add_score(self, base_value):
        """根据基础分值增加分数，并处理连击"""
        # 获取当前时间（秒）
        # 确保 pygame.init() 已经被调用
        try:
            now = pygame.time.get_ticks() / 1000.0
        except pygame.error:
            # 如果 Pygame 尚未初始化（例如在测试环境中），
            # 可以使用 time 模块，但这在实际游戏中不推荐
            import time

            now = time.time()
            if (
                self.last_hit_time == 0.0 and self.current_score == 0
            ):  # 第一次调用 add_score
                self.last_hit_time = now  # 初始化 last_hit_time

        # 检查连击是否超时
        if (now - self.last_hit_time) < self.combo_timeout:
            self.combo += 1
        else:
            self.combo = 1  # 超时或第一次得分，连击重置为1

        # 计算最终得分并累加
        score_to_add = base_value * self.combo
        self.current_score += score_to_add

        print(f"Got score: {score_to_add} .")

        # 更新最后命中时间
        self.last_hit_time = now

        # 可以选择性地返回增加的分数和当前连击数，方便UI显示
        # return score_to_add, self.combo

    def save_high_score(self, name=str(time.time())):
        """如果当前分数是新的高分，则保存到高分榜"""
        # 检查是否是高分
        if (
            not self.high_scores
            or self.current_score > self.high_scores[-1]["score"]
            or len(self.high_scores) < 10
        ):
            # 清理并验证名字输入
            player_name = name.strip()[:15]  # 限制名字长度并去除首尾空格
            if not player_name:
                player_name = "匿名玩家"  # 提供默认名字

            self.high_scores.append({"name": player_name, "score": self.current_score})
            # 按分数降序排序
            self.high_scores.sort(key=lambda x: x["score"], reverse=True)
            # 只保留前10名
            self.high_scores = self.high_scores[:10]

            # 写入文件
            try:
                with open(self.HIGH_SCORES_FILE, "w", encoding="utf-8") as f:
                    json.dump(
                        self.high_scores, f, indent=4, ensure_ascii=False
                    )  # 使用 indent 美化输出, ensure_ascii=False 支持中文
                print(f"新高分 {self.current_score} 已由 {player_name} 保存。")
                return True  # 表示成功保存了新高分
            except IOError as e:
                print(f"错误：无法写入高分文件 {self.HIGH_SCORES_FILE}: {e}")
                return False  # 表示保存失败
        else:
            print("当前分数未进入高分榜。")
            return False  # 表示未达到高分

    @classmethod
    def load_high_scores(cls):
        """加载高分记录文件"""
        try:
            # 确保目录存在
            cls.HIGH_SCORES_FILE.parent.mkdir(parents=True, exist_ok=True)
            if not cls.HIGH_SCORES_FILE.exists():
                print(f"高分文件 {cls.HIGH_SCORES_FILE} 不存在，将创建空列表。")
                return []  # 文件不存在，返回空列表
            with open(cls.HIGH_SCORES_FILE, "r", encoding="utf-8") as f:
                try:
                    scores = json.load(f)
                    # 基本验证：确保加载的是列表，且列表内是字典
                    if isinstance(scores, list) and all(
                        isinstance(item, dict) for item in scores
                    ):
                        # 可以添加更严格的键值验证
                        print(f"成功加载 {len(scores)} 条高分记录。")
                        return scores
                    else:
                        print(
                            f"错误：高分文件格式不正确，应为字典列表。 文件内容：{scores}"
                        )
                        return []  # 格式错误，返回空列表
                except json.JSONDecodeError as e:
                    print(f"错误：解析高分文件失败 {cls.HIGH_SCORES_FILE}: {e}")
                    return []  # 解析失败，返回空列表
        except IOError as e:
            print(f"错误：无法读取高分文件 {cls.HIGH_SCORES_FILE}: {e}")
            return []  # 文件读取错误，返回空列表
        except Exception as e:  # 捕获其他潜在错误
            print(f"加载高分时发生未知错误: {e}")
            return []


# --- 使用示例 ---
# pygame.init() # 确保 Pygame 已初始化以使用 pygame.time.get_ticks()

# score_manager = ScoreManager()
# print("初始分数:", score_manager.current_score)
# print("初始连击:", score_manager.combo)

# # 模拟得分
# score_manager.add_score(100)
# print(f"得分后: score={score_manager.current_score}, combo={score_manager.combo}")
# pygame.time.wait(500) # 等待0.5秒 (小于 combo_timeout)
# score_manager.add_score(150)
# print(f"连击得分: score={score_manager.current_score}, combo={score_manager.combo}")
# pygame.time.wait(2500) # 等待2.5秒 (大于 combo_timeout)
# score_manager.add_score(50)
# print(f"连击超时后得分: score={score_manager.current_score}, combo={score_manager.combo}")

# # 尝试保存高分
# score_manager.save_high_score("玩家一")

# # 重置分数管理器
# score_manager.reset()
# print("重置后分数:", score_manager.current_score)
# print("重置后连击:", score_manager.combo)
# print("高分记录:", score_manager.high_scores) # 高分记录应保留

# pygame.quit()
