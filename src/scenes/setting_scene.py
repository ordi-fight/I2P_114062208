'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''

import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
from typing import override
from src.sprites import Sprite
import src.core.services as services
from src.core.managers.game_manager import GameManager

class SettingScene(Scene):
    # Background Image
    background: BackgroundSprite
    # Buttons
    play_button: Button
    back_button : Button
    game_manager: GameManager
    
    def __init__(self):
        super().__init__()

        self.back_button = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            0, 0, 100, 100,
            
            on_click = lambda: services.scene_manager.change_scene("menu")
        )
        self.load_button = Button( 
            "UI/button_load.png", "UI/button_load_hover.png", 
            0, 0, 100, 100,
            on_click = self.load_game
        )

        self.save_button = Button( 
            "UI/button_save.png", "UI/button_save_hover.png", 
            0, 0, 100, 100,
            on_click = self.save_game
        )
        self.button_x = Button( 
            "UI/button_x.png", "UI/button_x_hover.png", 
            0, 0, 100, 100,
            on_click = lambda: services.scene_manager.change_scene("game") 
        )
        self.is_muted = False
        self.mute_button = Button(
            "UI/raw/UI_Flat_ToggleOn03a.png", "UI/raw/UI_Flat_ToggleOn03a.png",
            350,300,20,30,
            on_click = self.mute
        )
        self.panel_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.panel_img = pg.transform.scale(self.panel_img, (800, 500))
        self.panel_rect = self.panel_img.get_rect()
        self.slider_img = pg.image.load("assets/images/UI/raw/UI_Flat_BarFill01f.png").convert_alpha()
        self.slider_img = pg.transform.scale(self.slider_img, (350, 15))
        self.slider_posi = (300,250)
        self.slider_object = pg.image.load("assets/images/UI/raw/UI_Flat_ToggleLeftOn01a.png").convert_alpha()
        self.slider_object= pg.transform.scale(self.slider_object, (50, 50))
        # slider handle rect
        self.slider_handle_rect = self.slider_object.get_rect()
        self.slider_handle_rect.center = (300, 250)   # 初始位置

        # slider dragging state
        self.slider_dragging = False

        # slider bar range
        self.slider_min_x = 275          # 左端
        self.slider_max_x = 275 + 350    # 右端（因為 slider_img 寬度 = 350）

        self.message = ""
        
    @override
    def enter(self) -> None:
        super().enter() 
        services.sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")

    @override
    def exit(self) -> None:
        super().exit() 

    @override
    def update(self, dt: float) -> None:
        if services.input_manager.key_pressed(pg.K_SPACE):
            services.scene_manager.change_scene("game")
            return
        self.back_button.update(dt)  #back_button have to do update to change the state in game scene
        self.load_button.update(dt)
        self.save_button.update(dt)
        self.button_x.update(dt)
        self.mute_button.update(dt)
        # dt is calculate in engine.py
        mouse_pos = pg.mouse.get_pos()
        mouse_pressed = pg.mouse.get_pressed()[0]   # 左鍵

    # --- check if mouse starts dragging the handle ---
        if mouse_pressed:
            if not self.slider_dragging:  
                if self.slider_handle_rect.collidepoint(mouse_pos):
                    self.slider_dragging = True
        # if dragging, move slider handle
            if self.slider_dragging:
        # Update slider position but clamp between min/max
                x = max(self.slider_min_x, min(mouse_pos[0], self.slider_max_x))
                self.slider_handle_rect.centerx = x
                v = (self.slider_handle_rect.centerx - self.slider_min_x) / (self.slider_max_x - self.slider_min_x)
                services.sound_manager.set_volume(v)
        else:
            # release mouse stops dragging
            self.slider_dragging = False
        # if mouse_pressed:
        #     if self.slider_handle_rect.collidepoint(mouse_pos):
        #         x = max(self.slider_min_x, min(mouse_pos[0], self.slider_max_x))
        #         self.slider_handle_rect.centerx = x
        #         v = (self.slider_handle_rect.centerx - self.slider_min_x) / (self.slider_max_x - self.slider_min_x)
        #         services.sound_manager.set_volume(v)
    @override
    def draw(self, screen: pg.Surface) -> None:

        overlay = pg.Surface(screen.get_size())
        overlay.fill((0, 0, 0))   # 填滿黑色
        overlay.set_alpha(120)    # 半透明
        screen.blit(overlay, (0, 0))   # 貼到畫面上
        self.panel_rect.center = screen.get_rect().center #拿我自己的中心點 去對齊 螢幕的中心點
        screen.blit(self.panel_img, self.panel_rect)
        # back_button
        self.back_button.hitbox.centerx = self.panel_rect.centerx - 50
        self.back_button.hitbox.centery = self.panel_rect.centery + 120
       
        self.back_button.img_button_default =  Sprite("UI/button_back.png", (80,100 ))
        self.back_button.img_button_hover =  Sprite("UI/button_back_hover.png", (80,100 ))

        self.back_button.hitbox.size  = (80,100)
        #必須同步改變圖片和rect(滑鼠點擊範圍)

        self.back_button.draw(screen) #back_button have to use function draw to present the state to scene

        #load_button
        self.load_button.hitbox.centerx = self.panel_rect.centerx - 150
        self.load_button.hitbox.centery = self.panel_rect.centery + 120
       
        self.load_button.img_button_default =  Sprite("UI/button_load.png", (80,100 ))
        self.load_button.img_button_hover =  Sprite("UI/button_load_hover.png", (80,100 ))
        # self.load_button.img_button = self.load_button.img_button_default
        # you have to add thhis because
        #_ = screen.blit(self.img_button.image, self.hitbox) is the function in draw()
        # however , self.load_button.img_button = self.load_button.img_button_default is in function update
        self.load_button.hitbox.size  = (80,100)
        
        self.load_button.draw(screen)

        #save_button

        self.save_button.hitbox.centerx = self.panel_rect.centerx - 250
        self.save_button.hitbox.centery = self.panel_rect.centery + 120
       
        self.save_button.img_button_default =  Sprite("UI/button_save.png", (80,100 ))
        self.save_button.img_button_hover =  Sprite("UI/button_save_hover.png", (80,100 ))
        
        self.save_button.hitbox.size  = (80,100)
        
        self.save_button.draw(screen)

        #button_x

        self.button_x.hitbox.centerx = self.panel_rect.centerx + 350
        self.button_x.hitbox.centery = self.panel_rect.centery - 200
       
        self.button_x.img_button_default =  Sprite("UI/button_x.png", (40,40))
        self.button_x.img_button_hover =  Sprite("UI/button_x_hover.png", (40,40))
        
        self.button_x.hitbox.size  = (40,40)
        
        self.button_x.draw(screen)
        # mute_button
        self.mute_button.draw(screen)

        #slider
        screen.blit(self.slider_img,self.slider_posi )
        #slider_object
        screen.blit(self.slider_object, self.slider_handle_rect)
        # 文字
        services.scene_manager.write(40,"Volume", screen, (0,0,0), (275,180))
        # services.scene_manager.write(40,"Settings", screen, (255, 255, 255),  (275,150))
        if self.message !="":
            services.scene_manager.write(40,self.message, screen, (0, 0, 0), (350,350))
        if self.message == "":
            services.scene_manager.write(40,"mute on", screen, (0, 0, 0), (350,350))
    def save_game(self):
        # services.game_manager.bag.add_item("Pokeball", 5)
        # services.game_manager.save("saves/game0.json")
        services.scene_manager._scenes["game"].game_manager .save("saves/game0.json")
        print("Game Saved")
    def load_game(self):
        loaded =  GameManager.load("saves/game0.json")
        if loaded:
            services.scene_manager._scenes["game"].game_manager = loaded   # ← 替換成新的遊戲狀態
            print(" Game Loaded & Applied")
        else:
            print("Load failed")

    def mute(self):
 
        if not self.is_muted :
            self.mute_button.img_button_hover = Sprite("UI/raw/UI_Flat_ToggleOff03a.png",(20, 30))
            self.mute_button.img_button_default = Sprite("UI/raw/UI_Flat_ToggleOff03a.png",(20, 30))
            self.message = "Mute off"
            services.sound_manager.mute()
            self.is_muted = True #改動按鈕

        else:
            self.mute_button.img_button_hover = Sprite("UI/raw/UI_Flat_ToggleOn03a.png", (20, 30))
            self.mute_button.img_button_default = Sprite("UI/raw/UI_Flat_ToggleOn03a.png", (20, 30))
            self.message = "Mute on"
            services.sound_manager.unmute()
            self.is_muted = False #改動按鈕

            





        