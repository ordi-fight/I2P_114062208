
import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
import src.core.services as services
from typing import override
from src.sprites import Sprite

class BagScene(Scene):
    # Buttons
    play_button: Button
    back_button : Button
    
    def __init__(self):
        super().__init__()
        self.button_x = Button( 
            "UI/button_x.png", "UI/button_x_hover.png", 
            0, 0, 100, 100,
            on_click = lambda: services.scene_manager.change_scene("game") 
        )
        self.panel_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.panel_img = pg.transform.scale(self.panel_img, (800, 500))
        self.panel_rect = self.panel_img.get_rect()
        self.barrar_img = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.barrar_img = pg.transform.scale(self.barrar_img, (300, 100))
        self.barrar_posi = (0,0)
       
       
    @override
    def enter(self) -> None:
        services.sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
         # 資料儲存，每次進入bagacene都會更新一次
        self.bag = services.scene_manager._scenes["game"].game_manager.bag
        self.monsters = self.bag._monsters_data

    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        if services.input_manager.key_pressed(pg.K_SPACE):
            services.scene_manager.change_scene("game")
            return
        self.button_x.update(dt)
        # dt is calculate in engine.py
    def draw_items(self, screen: pg.Surface):

        font = pg.font.SysFont(None, 32)

        x = 700     # icon 起始位置
        y = 150
        spacing = 60     # 每個 item 間距

        for item in self.bag._items_data:

            name = item.get("name", "Unknown")
            amt  = item.get("amount", item.get("count", 0))

            # 1. load icon
            icon_path = "assets/images/" + item.get("sprite_path", "")
            icon = pg.image.load(icon_path).convert_alpha()
            icon = pg.transform.scale(icon, (40, 40))
            screen.blit(icon, (x, y))

            # 2. 顯示名稱
            name_text = font.render(name, True, (0,0,0))
            screen.blit(name_text, (x + 60, y + 5))

            # 3. 顯示數量
            count_text = font.render(f"x{amt}", True, (0,0,0))
            screen.blit(count_text, (x + 200, y + 5))

            y += spacing
    def draw_monsters(self, screen: pg.Surface):

        if not self.monsters:
            return

        font = pg.font.SysFont(None, 28)

        x = 300
        y = 150
        spacing = 110   # 每隻怪獸的縱向間距

        for mon in self.monsters:

            name = mon.get("name", "Unknown")
            level = mon.get("level", 1)
            hp = mon.get("hp", 1)
            max_hp = mon.get("max_hp", 1)

            sprite_path = "assets/images/" + mon.get("sprite_path")
            sprite = pg.image.load(sprite_path).convert_alpha()
            sprite = pg.transform.scale(sprite, (90, 90))
             # ---white background----
            self.barrar_posi = (x,y)
            screen.blit(self.barrar_img, self.barrar_posi)

            # --- Draw sprite ---
            screen.blit(sprite, (x, y))

            # --- Draw name ---
            name_text = font.render(f"{name}", True, (0, 0, 0))
            screen.blit(name_text, (x + 110, y + 10))

            # --- Draw HP bar ---
            # HP 百分比
            hp_ratio = hp / max_hp
            bar_width = 150
            bar_height = 12

            # 背景條（灰色）
            pg.draw.rect(screen, (80, 80, 80), (x + 110, y + 40, bar_width, bar_height))

            # 綠色血條
            pg.draw.rect(screen, (0, 200, 0), (x + 110, y + 40, bar_width * hp_ratio, bar_height))

            # --- Draw level ---
            lvl_text = font.render(f"Lv {level}", True, (0, 0, 0))
            screen.blit(lvl_text, (x + 110, y + 40))

            # --- HP Text ---
            hp_text = font.render(f"{hp}/{max_hp}", True, (0, 0, 0))
            screen.blit(hp_text, (x + 110, y + 60))

            y += spacing
    @override
    def draw(self, screen: pg.Surface) -> None:

        overlay = pg.Surface(screen.get_size())
        overlay.fill((0, 0, 0))   # 填滿黑色
        overlay.set_alpha(120)    # 半透明
        screen.blit(overlay, (0, 0))   # 貼到畫面上
        self.panel_rect.center = screen.get_rect().center #拿我自己的中心點 去對齊 螢幕的中心點
        screen.blit(self.panel_img, self.panel_rect)

        #button_x

        self.button_x.hitbox.centerx = self.panel_rect.centerx + 350
        self.button_x.hitbox.centery = self.panel_rect.centery - 200
       
        self.button_x.img_button_default =  Sprite("UI/button_x.png", (40,40))
        self.button_x.img_button_hover =  Sprite("UI/button_x_hover.png", (40,40))
        
        self.button_x.hitbox.size  = (40,40)
        
        self.button_x.draw(screen)

        #同步資料

        self.draw_items(screen)
        self.draw_monsters(screen)
