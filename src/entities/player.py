from __future__ import annotations
import pygame 
from .entity import Entity
from src.core.services import input_manager,scene_manager
from src.utils import Position, PositionCamera, GameSettings, Logger
from src.core import GameManager
import math
from typing import override

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager

    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self.speed = 200
    @override
    
    def update(self, dt: float) -> None:
        dis = Position(0, 0)
        
        if input_manager.key_down(pygame.K_LEFT) or input_manager.key_down(pygame.K_a):
            dis.x -= 1
            self.animation.switch("left")
        if input_manager.key_down(pygame.K_RIGHT) or input_manager.key_down(pygame.K_d):
            dis.x += 1
            self.animation.switch("right")
        if input_manager.key_down(pygame.K_UP) or input_manager.key_down(pygame.K_w):
            dis.y -= 1
            self.animation.switch("up")
        if input_manager.key_down(pygame.K_DOWN) or input_manager.key_down(pygame.K_s):
            dis.y += 1
            self.animation.switch("down")
        length = (dis.x**2 + dis.y**2)**0.5
        if length != 0:
            dis.x /= length
            dis.y /= length

        self.position.x += dis.x*self.speed*dt

        if self.game_manager.check_collision(pygame.Rect(self.position.x, self.position.y,GameSettings.TILE_SIZE ,GameSettings.TILE_SIZE )):
            self.position.x = self._snap_to_grid(self.position.x)
        self.position.y += dis.y*self.speed*dt
        if self.game_manager.check_collision(pygame.Rect(self.position.x, self.position.y,GameSettings.TILE_SIZE ,GameSettings.TILE_SIZE )):
            self.position.y = self._snap_to_grid(self.position.y)
        if self.game_manager.check_bush_collision(pygame.Rect(self.position.x, self.position.y,GameSettings.TILE_SIZE ,GameSettings.TILE_SIZE )) :
            # print("In the bush")
            self.position.x = self._snap_to_grid(self.position.x)
            self.position.y = self._snap_to_grid(self.position.y)
            if input_manager.key_pressed(pygame.K_SPACE):
                scene_manager.change_scene("Catch")
        # Check teleportation
        tp = self.game_manager.current_map.check_teleport(self.position)
        if tp:
            dest = tp.destination
            
            self.game_manager.switch_map(dest)


                
        super().update(dt)
    def enter(self):

        pass

    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

