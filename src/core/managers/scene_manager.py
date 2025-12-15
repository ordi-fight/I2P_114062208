import pygame as pg

from src.scenes.scene import Scene
from src.utils import Logger

class SceneManager:
    
    _scenes: dict[str, Scene]
    _current_scene: Scene | None = None
    _next_scene: str | None = None
    
    def __init__(self):
        Logger.info("Initializing SceneManager")
        self._scenes = {}
        self._scene_stack = []
        # self.game_manager = None
    def register_scene(self, name: str, scene: Scene) -> None:
        self._scenes[name] = scene
        
    def change_scene(self, scene_name: str) -> None:
        if scene_name in self._scenes:
            Logger.info(f"Changing scene to '{scene_name}'")
            self._next_scene = scene_name
        else:
            raise ValueError(f"Scene '{scene_name}' not found")
            
    def update(self, dt: float) -> None:
        # Handle scene transition
        if self._next_scene is not None:
            self._perform_scene_switch()
            
        # Update current scene
        if self._scene_stack:
            self._scene_stack[-1].update(dt)
            
    def draw(self, screen: pg.Surface) -> None:
        for scene in self._scene_stack:
            scene.draw(screen)
            
    def _perform_scene_switch(self) -> None:
        if self._next_scene is None:
            return
            
        # Exit current scene
        if self._current_scene:
            self._current_scene.exit()
        
        new_scene = self._scenes[self._next_scene]
        self._scene_stack = [new_scene]   # <-- 初始化 stack ，放入第一個場景
        #在同一次遊戲執行中，不同場景重複堆疊在 stack 裡而不清乾淨
        #藉由change scene 就初始化讓場景不會重複堆疊
        #所以change_scene ->[menu_scene]; change_scene -> [game_scene] ; push_scene -> [game_scene,setting_scene]
        
        # Enter new scene
        if self._scene_stack:
            Logger.info(f"Entering {self._next_scene} scene")
            new_scene.enter()
            
        # Clear the transition request
        self._next_scene = None
    def push_scene(self, scene_name: str) -> None:
        if scene_name not in self._scenes:
            raise ValueError(f"Scene '{scene_name}' not found")

        Logger.info(f"Pushing scene '{scene_name}'")

        new_scene = self._scenes[scene_name]
        self._scene_stack.append(new_scene)
        new_scene.enter()
    def write(self,size:int,text, screen: pg.Surface, color: tuple[int, int, int], position: tuple[int, int]) -> None:
        font = pg.font.SysFont(None, size)
        text = font.render(text, True, color)
        text_rect = text.get_rect()
        text_rect.topleft = position
        screen.blit(text, text_rect)
        # print(text)
        
        