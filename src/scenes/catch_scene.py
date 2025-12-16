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


class CatchScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    
    def __init__(self):
        super().__init__()

        self.background =  BackgroundSprite("backgrounds/background1.png") 
        self._message: str = ""
        self.cage_image = pg.image.load("assets/images/UI/—Pngtree—animal cage_8426636.png").convert_alpha()
        self.cage_image = pg.transform.scale(self.cage_image, (500, 300))
        self.cage_image_rect = self.cage_image.get_rect()
        self.banner_image = pg.image.load("assets/images/UI/raw/UI_Flat_Frame01a.png").convert_alpha()
        self.banner_image = pg.transform.scale(self.banner_image, (500, 100))
        self.banner_image_rect = self.banner_image.get_rect()
        self.cage_drop_active = False
        self.cage_drop_y = -400             
        self.cage_drop_speed = 250          
        self.cage_drop_target_y = 0         
        self._message = ""
        self._message_timer = 0
        self._animation_timer = 0.0
        self.portion_button = Button(
            "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            0,0 , 250, 100,
            on_click = self.portion_used
        )

    @override    
    def enter(self):
        self.game_manager = scene_manager._scenes["game"].game_manager 
        if self.game_manager.bag._monsters_data:
            self.player_mon = self.game_manager.bag._monsters_data[0].copy()
            self.player_mon =  {
            "name": "Pikachu",
            "hp": 85,
            "max_hp": 100,
            "hp/ratio":1.0,
            "level": 25,
            "win_count" : 0,
            "sprite_path": "menu_sprites/menusprite1.png"
            }
        else:
            self.player_mon =  {
            "name": "Pikachu",
            "hp": 85,
            "max_hp": 100,
            "hp/ratio":1.0,
            "level": 25,
            "win_count": 0,
            "sprite_path": "menu_sprites/menusprite1.png"
            }

        # --- Enemy monster (simple fixed monster) ---
        self.enemy_mon = random.choice([
      { "name": "Pikachu",   "hp": 85,  "max_hp": 100,"attack":10,"defense":10 ,"level": 12,"element": "grass","win_count" : 0, "sprite_path": "menu_sprites/menusprite1.png" },
      { "name": "Charizard", "hp": 150, "max_hp": 200, "attack":25,"defense":25,"level": 18,"element": "grass", "win_count" : 0,"sprite_path": "menu_sprites/menusprite2.png" },
      { "name": "Blastoise", "hp": 120, "max_hp": 180, "attack":30,"defense":30,"level": 16,"element": "water", "win_count" : 0,"sprite_path": "menu_sprites/menusprite3.png" },
      { "name": "Venusaur",  "hp": 90,  "max_hp": 160, "attack":10,"defense":10,"level": 15,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite4.png" },
      { "name": "Gengar",    "hp": 110, "max_hp": 140, "attack":15,"defense":15,"level": 14,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite5.png" },
      { "name": "Dragonite", "hp": 180, "max_hp": 220, "attack":40,"defense":40,"level": 20, "element": "water","win_count" : 0,"sprite_path": "menu_sprites/menusprite6.png" }
    ])
        self.enemy_mon_copy = self.enemy_mon.copy()
        self.player_mon_sprite = Sprite(self.player_mon["sprite_path"], (150,150))
        self.enemy_mon_sprite  = Sprite(self.enemy_mon["sprite_path"],  (150,150))
        self.state = "player_turn" 
        self.is_cage_image = False
        self.enemy_fixed_position = True
    def take_damage(self,monster,damage):
        monster["hp"] = max(0, monster["hp"] - damage)
    def is_alive(self,monster):
        return monster["hp"] > 0
    def end_battle(self,victor):
        self.state = "ended"
        Logger.info(f"Battle ended. victor={victor}")
        scene_manager.change_scene("game")

    @override
    def update(self, dt: float):
        self.portion_button.update(dt)
        # self.is_cage_image = False
        if self.state == "player_turn" :
            if self._message == "" and self._animation_timer == 0.0:
                self._message = "Player turn! Press RIGHT/D to Attack or DOWN/S to Run"
            Logger.info(f"Player turn - HP { self.player_mon ["hp"]} | Enemy HP {self.enemy_mon["hp"]}  (1:Attack  2:Run)")
            # self.state = "player_turn"
            Logger.info(f"{input_manager.key_pressed(pg.K_RIGHT)} {input_manager.key_pressed(pg.K_d)}")
            if  input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                self.take_damage(self.enemy_mon,120)
                # Logger.info(f"Player attacks! Enemy HP is now {self.enemy_mon['hp']}")
                if not self.is_alive(self.enemy_mon):
                        # Logger.info("You were defeated! Game Over!")
        
                    scene_manager._scenes["game"].game_manager.bag._monsters_data.append(self.enemy_mon_copy)
                    for item in scene_manager._scenes["game"].game_manager.bag._items_data:
                        if item["name"] == "Pokeball":
                            item["count"] -= 2
                        if item["name"] == "Coins":
                            item["count"] += 2  
                    #add_item function has a return
                    Logger.info(f"{scene_manager._scenes["game"].game_manager.bag._items_data}")
                    scene_manager._scenes["game"].game_manager .save("saves/game0.json")
                    # print(f"self.state is {self.state}")
                    self.end_battle(victor=self.player_mon["name"])
                    return
      
                self.state = "enemy_turn"
                self.enemy_timer = 0.0
                self.enemy_mon["hp/ratio"] = self.enemy_mon["hp"]/self.enemy_mon["max_hp"]
                
            elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                # Logger.info("You fled the battle!")
                self.end_battle(victor=self.player_mon["name"])
                return
        elif self.state == "enemy_turn":
            if self._message == "" and self._animation_timer == 0.0:
                self._message = "Enermy turn! Press LEFT/A to Attack or Up/w Run"
            
            # if self.enemy_timer >= self.enemy_delay:
            if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                self.take_damage(self.player_mon,10)
                # Logger.info(f"Enemy attacks! Player HP is now {self.player_mon['hp']}")
                
                if not self.is_alive(self.player_mon):
                    # Logger.info("Enemy defeated! You win!")
                    
                    # scene_manager._scenes["game"].game_manager.bag.add_item("Pokeball", -2)
                    for item in scene_manager._scenes["game"].game_manager.bag._items_data:
                        if item["name"] == "Pokeball":
                            item["count"] -= 2
                        
                    scene_manager._scenes["game"].game_manager .save("saves/game0.json")
                    self.end_battle(victor=self.enemy_mon["name"])
                    return
                
                self.state = "player_turn"
                self.player_mon["hp/ratio"] = self.player_mon["hp"]/self.player_mon["max_hp"]
            elif input_manager.key_pressed(pg.K_UP) or input_manager.key_pressed(pg.K_w):
                self._message = "Enermy run!!! hurry to get him back"
                self._message_timer = 0.4
                # self.enemy_timer += dt
                    # Logger.info("Enemy tried to flee, but can't!")
                self.state = "intermediate_turn"  
                
                self.cage_drop_active = True
                self.cage_drop_y = -300
                self.cage_drop_target_y = 250   # 掉到畫面中央附近
                self._animation_timer = 3.0
                
        if self._message_timer > 0:
            self._message_timer -= dt
        if self._message_timer <= 0:
            self._message = "" 
        if self.cage_drop_active:
            self.cage_drop_y += self.cage_drop_speed * dt

        if self.cage_drop_y >= self.cage_drop_target_y:
            self.cage_drop_y = self.cage_drop_target_y
            self.cage_drop_active = False
        if self._animation_timer > 0:
            self._animation_timer -= dt
        if self._animation_timer < 0:
            self.state = "player_turn"
            self._animation_timer = 0.0
        self.player_mon_hp_ratio = self.player_mon["hp"]/self.player_mon["max_hp"]
        self.enemy_mon_hp_ratio = self.enemy_mon["hp"]/self.enemy_mon["max_hp"]
            
    @override
    def draw(self,screen):
        self.background.draw(screen)
        # draw player monster (left bottom)
        self.player_mon_sprite.rect.topleft = (100, GameSettings.SCREEN_HEIGHT -350)
        self.player_mon_sprite.draw(screen)
        # draw enemy monster (right top)
        self.enemy_mon_sprite.rect.topleft = (GameSettings.SCREEN_WIDTH - 350, 100)
        # if not self.cage_drop_active and not self.is_cage_image:
            
        self.enemy_mon_sprite.draw(screen)
        
       # 畫面訊息：由 draw 每幀負責繪製，避免被後續繪圖蓋掉
        #print(f"{self._message_timer} {self._message}")
        if self._message == ""and self.state != "intermediate_turn":
            if self.state == "player_turn":
                text = "Player turn! Press RIGHT/D or DOWN/S"
            elif self.state == "enemy_turn":
                text = "Enemy turn! Press LEFT/A or UP/W"
            self.draw_message(screen, text)
        elif self.state != "ended" :
    # # 畫高優先訊息
            self.draw_message_color(screen, self._message)

        #the HP bars of player_mon
        pg.draw.rect(screen, (80, 80, 80), (150, GameSettings.SCREEN_HEIGHT - 150, self.player_mon["max_hp"] , 10))
        pg.draw.rect(screen, (0, 200, 0), (150, GameSettings.SCREEN_HEIGHT - 150, self.player_mon["max_hp"] * self.player_mon_hp_ratio ,10))
        
        font = pg.font.SysFont(None, 20)
        hp_repr = font.render(f"hp of player monster {self.player_mon["hp"]}", True, (0,0,0))
        screen.blit(hp_repr, (150, GameSettings.SCREEN_HEIGHT - 180))

        #the HP bars of enemy_mon
        pg.draw.rect(screen, (80, 80, 80), (GameSettings.SCREEN_WIDTH - 250, 100, self.enemy_mon["max_hp"], 10))
        pg.draw.rect(screen, (0, 200, 0), (GameSettings.SCREEN_WIDTH - 250, 100, self.enemy_mon["max_hp"] * self.enemy_mon_hp_ratio,10))
        
        font = pg.font.SysFont(None, 20)
        hp_repr = font.render(f"hp of enermy monster {self.enemy_mon["hp"]}", True, (0,0,0))
        screen.blit(hp_repr, (GameSettings.SCREEN_WIDTH - 250,70))
        # --- Draw cage dropping animation ---
        if self.cage_drop_active:

            # 籠子位置（水平置中）
            cage_rect = self.cage_image.get_rect()
            cage_rect.centerx = GameSettings.SCREEN_WIDTH // 2
            cage_rect.top = self.cage_drop_y

            # 怪獸位置（對齊籠子中心）
            mon_rect = self.enemy_mon_sprite.rect.copy()
            mon_rect.center = cage_rect.center
            # 文字位置
            font = pg.font.SysFont(None, 40)
            message = font.render("the monster is caught", True, (128, 0, 32))
            message_rect = message.get_rect()
            message_rect.midbottom = (cage_rect.centerx,cage_rect.top)
            self.banner_image_rect.center = message_rect.center
            # 繪製怪獸（籠子裡）
            screen.blit(self.enemy_mon_sprite.image, mon_rect)

            # 繪製籠子（蓋在怪獸上面）
            screen.blit(self.cage_image, cage_rect)
            #the monster is caught
            screen.blit(self.banner_image, self.banner_image_rect)
            screen.blit(message, message_rect)
        # draw portion button
        self.portion_button.hitbox.centerx = screen.get_rect().centerx
        self.portion_button.hitbox.bottom = GameSettings.SCREEN_HEIGHT -150
        self.portion_button.draw(screen)
        # draw portion text
        font = pg.font.SysFont(None, 30)
        portion_text = font.render("Use Portion", True, (0,0,0))
        portion_text_rect = portion_text.get_rect()     
        portion_text_rect.center = self.portion_button.hitbox.center
        screen.blit(portion_text, portion_text_rect)
    def draw_message(self, screen: pg.Surface, message: str):

        font = pg.font.SysFont(None, 40)

        # show message
        message_page = font.render(message, True, (0,0,0))
        message_page_rect = message_page.get_rect()
        message_page_rect.center = screen.get_rect().center
        screen.blit(message_page, message_page_rect)
    def draw_message_color(self, screen: pg.Surface, message: str):

        font = pg.font.SysFont(None, 60)

        # show message
        message_page = font.render(message, True, (255, 0, 0))
        message_page_rect = message_page.get_rect()
        message_page_rect.center = screen.get_rect().center
        screen.blit(message_page, message_page_rect)
    def portion_used(self):
        if self.state != "player_turn":
            return
        # Check if there are portions in the bag
        portion_count = 0
        for item in scene_manager._scenes["game"].game_manager.bag._items_data:
            if item["name"] == "Potion":
                portion_count = item["count"]
                break
        if portion_count <= 0:
            self._message = "No portions left!"
            self._message_timer = 2.0
            return
        # Use a portion to heal the player's monster
        heal_amount = 25
        self.player_mon["hp"] = min(self.player_mon["max_hp"], self.player_mon["hp"] + heal_amount)
        self.player_mon["hp/ratio"] = self.player_mon["hp"]/self.player_mon["max_hp"]
        # Decrease portion count in the bag
        for item in scene_manager._scenes["game"].game_manager.bag._items_data:
            if item["name"] == "Potion":
                item["count"] -= 1
                break
        self._message = f"Used a portion! Healed {heal_amount} HP."
        self._message_timer = 2.0
    
            