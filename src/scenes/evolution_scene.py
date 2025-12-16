import pygame as pg
import threading
import time
import random

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.interface.components import Button
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import scene_manager, sound_manager, input_manager
from src.sprites import Sprite,BackgroundSprite
from typing import override
from src.data.bag import Bag
from src.sprites import Animation


class EvolutionScene(Scene):
    
    def __init__(self):
        super().__init__()
        
        
       

    @override    
    def enter(self):
       
        self.monster_collection = scene_manager._scenes["game"].monster_collection
        self.monster_aimations =[]
        for monster in self.monster_collection:
            if monster["name"] == "evolved Pikachu":
                animation = Animation("sprites/sprite1.png",["turnround"],2,(600,600))
            elif monster["name"] == "evolved Charizard":
                animation = Animation("sprites/sprite2.png",["turnround"],2,(600,600))
            elif monster["name"] == "evolved Blastoise":
                animation = Animation("sprites/sprite3.png",["turnround"],2,(600,600))
            elif monster["name"] == "evolved Venusaur":
                animation = Animation("sprites/sprite4.png",["turnround"],2,(600,600))
            elif monster["name"] == "evolved Gengar":
                animation = Animation("sprites/sprite5.png",["turnround"],2,(600,600))
            elif monster["name"] == "evolved Dragonite":
                animation = Animation("sprites/sprite6.png",["turnround"],2,(600,600))
            self.monster_aimations.append(animation)
        self.timer = 4
    @override
    def update(self, dt: float):
        if self.monster_aimations:
            for monster in self.monster_aimations:
                monster.update(dt)
        if self.timer > 0:
            self.timer -= dt
        if self.timer <= 0:
            scene_manager.change_scene("game")
    @override
    def draw(self,screen):
       
        for index,monster in enumerate(self.monster_collection):
            
            if monster["element"] == "water":
                background =  BackgroundSprite("backgrounds/background3.png") 
                background.draw(screen)
            elif monster["element"] == "fire":
                background =  BackgroundSprite("backgrounds/background2.png") 
                background.draw(screen)
            elif monster["element"] == "grass":
                background =  BackgroundSprite("backgrounds/background1.png") 
                background.draw(screen)
            monster_animation = self.monster_aimations[index]
            monster_animation.rect.centerx= screen.get_rect().centerx -500
            monster_animation.rect.centery= screen.get_rect().centery - 300
            monster_animation.draw(screen)

            dict = {
                "evolved Pikachu":
                { "name": "Pikachu",   "hp": 85,  "max_hp": 100,"attack":10,"defense":10 ,"level": 12,"element": "grass","win_count" : 0, "sprite_path": "menu_sprites/menusprite1.png" },
                "evolved Charizard":
                { "name": "Charizard", "hp": 150, "max_hp": 200, "attack":25,"defense":25,"level": 18,"element": "grass", "win_count" : 0,"sprite_path": "menu_sprites/menusprite2.png" },
                "evolved Blastoise":
                { "name": "Blastoise", "hp": 120, "max_hp": 180, "attack":30,"defense":30,"level": 16,"element": "water", "win_count" : 0,"sprite_path": "menu_sprites/menusprite3.png" },
                "evolved Venusaur":
                { "name": "Venusaur",  "hp": 90,  "max_hp": 160, "attack":10,"defense":10,"level": 15,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite4.png" },
                "evolved Gengar":
                { "name": "Gengar",    "hp": 110, "max_hp": 140, "attack":15,"defense":15,"level": 14,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite5.png" },
                "evolved Dragonite":
                { "name": "Dragonite", "hp": 180, "max_hp": 220, "attack":40,"defense":40,"level": 20, "element": "water","win_count" : 0,"sprite_path": "menu_sprites/menusprite6.png" }
                }
            
            text_content = f"""
                name : {dict[monster["name"]]["name"]} ----> {monster["name"]}\n
                hp : {dict[monster["name"]]["hp"]} ----> {monster["hp"]} \n
                max_hp : {dict[monster["name"]]["max_hp"]} ----> {monster["max_hp"]} \n
                attack : {dict[monster["name"]]["attack"]} ----> {monster["attack"]} \n
                defense : {dict[monster["name"]]["defense"]} ----> {monster["defense"]} \n
                level : {dict[monster["name"]]["level"]} ----> {monster["level"]}""" 

            
            font_1 = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
            

            # 2. 將字串按換行符號分割成行
            lines = text_content.split('\n')
            # 3. 定義起始繪製位置和行高間距
            x_start = 600 # 假設的起始 X 座標
            y_start = 200 # 假設的起始 Y 座標
            line_height = font_1.get_linesize() # 獲取字體的高度作為行高

        
            current_y = y_start

            for line in lines:
            
                line_surface = font_1.render(line, True, (255, 255, 255))
                
                screen.blit(line_surface, (x_start, current_y))
                
                current_y += line_height  
       
            
            