from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite, Animation 
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera


@dataclass
class IdleMovement:
    def update(self, npc: "NPC", dt: float) -> None:
        return

class NPC(Entity):
    _movement: IdleMovement
    dialogue: str

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        facing: Direction = Direction.DOWN,
        dialogue: str = "Hello there!",
    ) -> None:
        # **載入 NPC 專屬的動畫 (覆蓋 Entity 繼承的 ow1.png)**
        self.animation = Animation(
            "character/ow6.png",
            ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        self.position = Position(x, y)
        self.game_manager = game_manager
        
        self.dialogue = dialogue
        self._movement = IdleMovement()
        self._set_direction(facing)
        self.warning_sign = Sprite("exclamation.png", (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2))
        self.warning_sign.update_pos(Position(x + GameSettings.TILE_SIZE // 4, y - GameSettings.TILE_SIZE // 2))
        self.detected = False
        
        self.animation.update_pos(self.position)
        # super().__init__(x, y, game_manager) # 因為我們手動初始化了動畫和位置，所以不調用 super().__init__

    @override
    def update(self, dt: float) -> None:
        self._movement.update(self, dt)
        self._has_los_to_player()
        # 互動邏輯
        if self.detected and input_manager.key_pressed(pygame.K_i):
           scene_manager.push_scene("buy")
            
        self.animation.update_pos(self.position)
        super().update(dt) 

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT:
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
            
    def _can_interact(self) -> bool:
        """檢查玩家是否在 NPC 面對的方向上的一個格子內"""
        player = self.game_manager.player
        if player is None:
            return False
            
        ts = GameSettings.TILE_SIZE
        # 創建一個與 NPC 面向方向延伸一格的矩形 (互動區域)
        if self.direction == Direction.UP:
            interaction_rect = pygame.Rect(self.position.x, self.position.y - ts, ts, ts)
        elif self.direction == Direction.DOWN:
            interaction_rect = pygame.Rect(self.position.x, self.position.y + ts, ts, ts)
        elif self.direction == Direction.LEFT:
            interaction_rect = pygame.Rect(self.position.x - ts, self.position.y, ts, ts)
        else: # Direction.RIGHT
            interaction_rect = pygame.Rect(self.position.x + ts, self.position.y, ts, ts)

        return interaction_rect
    def _has_los_to_player(self) -> None:
        player = self.game_manager.player
        rect = self._can_interact()
        if rect is None or player is None:
            self.detected = False
            return
        if rect.colliderect(player.animation.rect):
            self.detected = True
        else:
            self.detected = False
    

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "NPC":
        facing_val = data.get("facing")
        facing: Direction = Direction.DOWN
        if facing_val is not None and isinstance(facing_val, str):
            facing = Direction[facing_val]
                
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            facing,
            data.get("dialogue", "Hello there!"),
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["facing"] = self.direction.name
        base["dialogue"] = self.dialogue
        return base
    

