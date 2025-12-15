
import pygame as pg

from src.utils import GameSettings
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.interface.components import Button
import src.core.services as services
from typing import override
from src.sprites import Sprite
import random

class BuyScene(Scene):
    # Buttons
    play_button: Button
    back_button : Button

    monster_shop_buttons: list[Button]
    item_shop_buttons: list[Button] # 為了 draw_items 保持結構完整，但我們只關注怪獸部分

    def __init__(self):
        super().__init__()
        self.mode : str = "sell"
        self.button_x = Button( 
            "UI/button_x.png", "UI/button_x_hover.png", 
            0, 0, 100, 100,
            on_click = lambda: services.scene_manager.change_scene("game") 
        )
        self.button_sell = Button(
            "UI/raw/UI_Flat_Button02a_2.png","UI/raw/UI_Flat_Button02a_4.png",
            0,0,100,50,
            on_click = self.change_mode_sell
        )
        self.button_buy = Button(
            "UI/raw/UI_Flat_Button02a_2.png","UI/raw/UI_Flat_Button02a_4.png",
            0,0,100,50,
            on_click = self.change_mode_buy
        )

        self.item_shop_buttons = []

        self.panel_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.panel_img = pg.transform.scale(self.panel_img, (800, 500))
        self.panel_rect = self.panel_img.get_rect()
        self.barrar_img = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.barrar_img = pg.transform.scale(self.barrar_img, (250, 60))
        self.barrar_posi = (0,0)
        self.message = None
        self.message_timer = 0
    def change_mode_sell(self):
        self.mode = "sell"
    def change_mode_buy(self):
        self.mode = "buy"
    def _create_item_buttons(self, items):
        buttons = []
        for index, item in enumerate(items):
            item_name = item.get("name")
            on_click_func = lambda name=item_name: self.shop(name)
            
            button = Button(
                "UI/button_shop.png", "UI/button_shop_hover.png",
                0, 0, 50, 50,
                on_click=on_click_func
            )
            buttons.append(button)
        return buttons
        
    @override
    def enter(self) -> None:
        services.sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
         # 資料儲存，每次進入都會更新一次
        self.bag = services.scene_manager._scenes["game"].game_manager.bag
        self.monsters = self.bag._monsters_data
        self.items = self.bag._items_data
        
        # 動態創建按鈕列表
        self.item_shop_buttons = self._create_item_buttons(self.items)
        self.random_count = [random.Random().randint(1,10) for _ in range(6)]


    @override
    def exit(self) -> None:
        pass

    @override
    def update(self, dt: float) -> None:
        self.button_x.update(dt)
        # dt is calculate in engine.py
        self.button_sell.update(dt)
        self.button_buy.update(dt)
        
        for button in self.item_shop_buttons:
            button.update(dt)
        if self.message_timer > 0:
            self.message_timer -= dt
        else:
            self.message = None
        
    def draw_items(self, screen: pg.Surface):

        font = pg.font.SysFont(None, 18)
        for index, item in enumerate(self.bag._items_data):
            name = item.get("name", "Unknown")
            if    (name == "Coins"):
                x = 750
                y = 250
                amt  = item.get("amount", item.get("count", 0))
                
                # 1. load icon
                icon_path = "assets/images/" + item.get("sprite_path", "")
                icon = pg.image.load(icon_path).convert_alpha()
                icon = pg.transform.scale(icon, (25, 25))
                screen.blit(icon, (x, y))

                # 2. 顯示名稱
                name_text = font.render(name, True, (0,0,0))
                screen.blit(name_text, (x + 60, y + 5))
                if self.message :
                    services.scene_manager.write(40,self.message,screen,(0,255,0),(750,300))

                # 3. 顯示數量
                count_text = font.render(f"x{amt}", True, (0,0,0))
                screen.blit(count_text, (x + 200, y + 5))
        x = 300     # icon 起始位置
        y = 250
        spacing = 60 
        if self.mode == "sell":
            for index, item in enumerate(self.bag._items_data):
                name = item.get("name", "Unknown")
                if (name == "defence_buff") or  (name == "attack_buff") or (name == "heal_buff"):
                    button = self.item_shop_buttons[index] # 取得這個 item 專屬的 Button 實例
                    
                    amt  = item.get("amount", item.get("count", 0))
                    tag  = item.get("tag", 0)
                    # 1. load icon
                    icon_path = "assets/images/" + item.get("sprite_path", "")
                    icon = pg.image.load(icon_path).convert_alpha()
                    icon = pg.transform.scale(icon, (25, 25))
                    screen.blit(icon, (x, y))

                    # 2. 顯示名稱
                    name_text = font.render(name, True, (0,0,0))
                    screen.blit(name_text, (x + 60, y + 5))

                    # 3. 顯示數量
                    count_text = font.render(f"x{amt}", True, (0,0,0))
                    screen.blit(count_text, (x + 200, y + 5))
                    # 4. price
                    count_text = font.render(f"price {tag}", True, (255,0,0))
                    screen.blit(count_text, (x + 350, y + 5))
                    # shop_button (使用獨立按鈕)
                    button.hitbox.centerx = x + 275
                    button.hitbox.centery = y + 25
                    button.draw(screen) # 繪製獨立按鈕

                    y += spacing
                    
        elif self.mode == "buy":

            for index, item in enumerate(self.bag._items_data):
                name = item.get("name", "Unknown")
                if name != "Coins":
                    button = self.item_shop_buttons[index] # 取得這個 item 專屬的 Button 實例
                        
                    amt  = self.random_count[index]
                    tag  = item.get("tag", 0)
                    # 1. load icon
                    icon_path = "assets/images/" + item.get("sprite_path", "")
                    icon = pg.image.load(icon_path).convert_alpha()
                    icon = pg.transform.scale(icon, (25, 25))
                    screen.blit(icon, (x, y))

                    # 2. 顯示名稱
                    name_text = font.render(name, True, (0,0,0))
                    screen.blit(name_text, (x + 60, y + 5))

                    # 3. 顯示數量
                    count_text = font.render(f"x{amt}", True, (0,0,0))
                    screen.blit(count_text, (x + 200, y + 5))
                    # 4. price
                    count_text = font.render(f"price {tag}", True, (255,0,0))
                    screen.blit(count_text, (x + 350, y + 5))
                    # shop_button (使用獨立按鈕)
                    button.hitbox.centerx = x + 275
                    button.hitbox.centery = y + 25
                    button.draw(screen) # 繪製獨立按鈕

                    y += spacing

            
                  
    @override
    def draw(self, screen: pg.Surface) -> None:

        overlay = pg.Surface(screen.get_size())
        overlay.fill((0, 0, 0))   # 填滿黑色
        overlay.set_alpha(120)    # 半透明
        screen.blit(overlay, (0, 0))    # 貼到畫面上
        self.panel_rect.center = screen.get_rect().center #拿我自己的中心點 去對齊 螢幕的中心點
        screen.blit(self.panel_img, self.panel_rect)

        #button_x

        self.button_x.hitbox.centerx = self.panel_rect.centerx + 350
        self.button_x.hitbox.centery = self.panel_rect.centery - 200
        
        self.button_x.img_button_default =   Sprite("UI/button_x.png", (40,40))
        self.button_x.img_button_hover =   Sprite("UI/button_x_hover.png", (40,40))
        
        self.button_x.hitbox.size   = (40,40)
        
        self.button_x.draw(screen)

        #button_sell
        self.button_buy.hitbox.centerx = self.panel_rect.centerx - 200
        self.button_buy.hitbox.centery = self.panel_rect.centery - 200
        
        self.button_buy.draw(screen)
        #button_buy
        self.button_sell.hitbox.centerx = self.panel_rect.centerx - 300
        self.button_sell.hitbox.centery = self.panel_rect.centery - 200
        
        self.button_sell.draw(screen)
        
        #同步資料

        self.draw_items(screen)


        services.scene_manager.write(30,"sell",screen, (0,0,0) ,(320,150))
        services.scene_manager.write(30,"buy",screen, (0,0,0) ,(420,150))

    def shop(self,item_name):
        for item in services.scene_manager._scenes["game"].game_manager.bag._items_data:
            if item["name"] == item_name:
                tag = item["tag"]
        if self.mode == "sell":
            for item in services.scene_manager._scenes["game"].game_manager.bag._items_data:
                if item["name"] == "Coins":
                    item["count"] += tag 
                    self.message = f"+ {tag}"
                    self.message_timer = 2
                if item["name"] == item_name:
                    if item["count"] > 1:
                        item["count"] -= 1
                    else:
                        self.message = "insufficient items"
                        self.message_timer = 2
                        
                #add_item function has a return
                services.scene_manager._scenes["game"].game_manager .save("saves/game0.json")
        elif self.mode == "buy":
            for item in services.scene_manager._scenes["game"].game_manager.bag._items_data:
                if item["name"] == "Coins":
                    if item["count"] > 0:
                        item["count"] -= tag 
                        self.message = f"- {tag}"
                        self.message_timer = 2
                    else:
                        self.message = "insufficient coins"
                        self.message_timer = 2
                if item["name"] == item_name:

                    item["count"] += 1
                        
                #add_item function has a return
                services.scene_manager._scenes["game"].game_manager .save("saves/game0.json")



