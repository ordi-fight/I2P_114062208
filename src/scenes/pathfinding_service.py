from collections import deque
from src.utils import Position, GameSettings
from src.core import GameManager # 需要 GameManager 來存取地圖和碰撞檢測
import pygame as pg
import src.core.services as services
from src.core.services import scene_manager, sound_manager, input_manager

# ----------------------------------------------------
# 輔助類：用於 BFS 字典和集合中的鍵
# ----------------------------------------------------
# 為什麼要這樣做 (Why): 
# 1. 避免依賴 src.utils.Position 是否正確實現了 __hash__ 和 __eq__。
# 2. 簡化 BFS 邏輯，使用 (x, y) tuple 作為唯一的、可哈希的鍵。
TileCoord = tuple[int, int]

class PathfindingService:
    def __init__(self, game_manager: GameManager):
        self.game_manager = game_manager

    # ----------------------------------------------------
    # 核心方法：將像素座標轉換為格子座標
    # ----------------------------------------------------
    # 為什麼要這樣做 (Why):
    # 尋路必須在一個離散的網格上進行。遊戲中的 Position 是浮點數(像素)，
    # 必須轉換成整數網格座標 (x, y) 才能作為 BFS 的節點。
    @staticmethod
    def pixel_to_tile(position: Position) -> TileCoord:
        """將像素座標 Position(x, y) 轉換為格子座標 (x_tile, y_tile)"""
        # 使用 round 確保獲得最接近 Position 中心點的那個格子
        tile_x = round(position.x / GameSettings.TILE_SIZE)
        tile_y = round(position.y / GameSettings.TILE_SIZE)
        return (tile_x, tile_y)

    # ----------------------------------------------------
    # 輔助方法：檢查碰撞
    # ----------------------------------------------------
    # 為什麼要這樣做 (Why): 
    # 將碰撞檢查邏輯封裝起來，讓 BFS 主體保持乾淨。
    def _is_walkable(self, tile_coord: TileCoord) -> bool:
        """檢查一個格子座標 (x, y) 是否可通行 (無碰撞)"""
        tile_x, tile_y = tile_coord
        
        # 轉換格子座標為像素座標 (取格子的左上角，用於碰撞檢測)
        pixel_rect = pg.Rect(
            tile_x * GameSettings.TILE_SIZE, 
            tile_y * GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE, 
            GameSettings.TILE_SIZE
        )
        # 依賴 GameManager 的碰撞檢測方法
        return not self.game_manager.check_collision(pixel_rect) and not self.game_manager.check_bush_collision(pixel_rect)

    # ----------------------------------------------------
    # BFS 核心演算法
    # ----------------------------------------------------
    # 為什麼要這樣做 (Why):
    # 這是尋找最短路徑的標準 BFS 實現。使用 deque 和 parent 字典來保證最短路徑和可追溯性。
    def find_path_bfs(self, start_pixel_pos: Position, target_tile_pos: TileCoord) -> list[TileCoord]:
        """
        從起始像素座標找到目標格子座標的最短路徑。
        返回一個 TileCoord (x, y) tuple 列表。
        """
        # 1. 轉換起點為格子座標
        start_tile = self.pixel_to_tile(start_pixel_pos)

        if start_tile == target_tile_pos:
            return []

        queue = deque([start_tile])
        # parent: current_tile -> previous_tile，用於重建路徑
        parent: dict[TileCoord, TileCoord | None] = {start_tile: None}
        visited: set[TileCoord] = {start_tile}
        
        # 移動方向 (上下左右)
        directions: list[TileCoord] = [
            (0, -1), (0, 1), (1, 0), (-1, 0)
        ]

        # 2. 搜索
        while queue:
            current_tile = queue.popleft()

            if current_tile == target_tile_pos:
                break 

            for dx, dy in directions:
                next_x = current_tile[0] + dx
                next_y = current_tile[1] + dy
                next_tile = (next_x, next_y)
                
                # 檢查：未訪問 且 可通行
                if next_tile not in visited and self._is_walkable(next_tile):
                    visited.add(next_tile)
                    parent[next_tile] = current_tile
                    queue.append(next_tile)
        else:
            # 搜索結束但未找到目標
            return [] 

        # 3. 路徑重建
        path: list[TileCoord] = []
        current = target_tile_pos
        
        # 反向追溯，直到回到起點
        while current != start_tile:
            path.append(current) 
            current = parent.get(current)
            if current is None: break 
            
        path.reverse() # 順序變為：起點 -> 終點

        return path