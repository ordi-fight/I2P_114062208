
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


class BattleScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    
    def __init__(self):
        super().__init__()

        self.background =  BackgroundSprite("backgrounds/background1.png") 
        self._message: str = ""
        # possible states: start, player_turn, enemy_turn, ended
        self.cage_image = pg.image.load("assets/images/UI/—Pngtree—animal cage_8426636.png").convert_alpha()
        self.cage_image = pg.transform.scale(self.cage_image, (500, 300))
        self.cage_image_rect = self.cage_image.get_rect()
        self.banner_image = pg.image.load("assets/images/UI/raw/UI_Flat_Frame01a.png").convert_alpha()
        self.banner_image = pg.transform.scale(self.banner_image, (500, 100))
        self.banner_image_rect = self.banner_image.get_rect()
        self.cage_drop_active = False
        self.cage_drop_y = -400              # Start above the screen
        self.cage_drop_speed = 250          # Fall speed (px per second)
        self.cage_drop_target_y = 0          # Target Y (set when animation starts)
        self._animation_timer = 0.0
        self.tool_button  = Button(
            "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            0,0 , 200, 50,
            on_click = self.overlay_change
        )
        self.portion_button = Button(
            "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            300,200 , 200, 50,
            on_click = self.portion_used
        )
        self.buff_button = Button(
            "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            300,300 , 200, 50,
            on_click = self.buff_change
        )
        self.monster_button = Button(
            "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            300,400 , 200, 50,
            on_click = self.monster_change
        )
        self.button_x = Button( 
            "UI/button_x.png", "UI/button_x_hover.png", 
            950, 150, 20, 20,
            on_click = self.overlay_unchange
        )
        self.panel_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.panel_img = pg.transform.scale(self.panel_img, (800, 500))
        self.panel_rect = self.panel_img.get_rect()
        
        
    @override    
    def enter(self):
        self.game_manager = scene_manager._scenes["game"].game_manager 
        if self.game_manager.bag._monsters_data:
            self.player_mon = (self.game_manager.bag._monsters_data[0]).copy()

        else:
            self.player_mon =  {
            "name": "Pikachu",
            "hp": 85,
            "max_hp": 100,
            "defense": 5,
            "attack":10,
            "level": 25,
            "element":"grass",
            "win_count" : 0,
            "sprite_path": "menu_sprites/menusprite1.png"
            }

        # --- Enemy monster (simple fixed monster) ---
        self.enemy_mon = random.choice([
      { "name": "dangerous dolpin",   "hp": 85,  "max_hp": 100,"attack":5.0,"defense":5.0,"level": 12,"element":"water" ,"sprite_path": "sprites/sprite14_attack.png" },
      { "name": "fire dragon", "hp": 150, "max_hp": 200, "attack":25.0,"defense":5.0,"level": 18,"element":"fire", "sprite_path": "sprites/sprite9_attack.png" },
      { "name": "little seed", "hp": 120, "max_hp": 180, "attack":30.0,"defense":5.0,"level": 16, "element":"grass","sprite_path": "sprites/sprite16_attack.png" },
      { "name": "Venusaur",  "hp": 90,  "max_hp": 160, "attack":10.0,"defense":10.0,"level": 15, "element":"grass","sprite_path": "sprites/sprite4_attack.png" },
      { "name": "Gengar",    "hp": 110, "max_hp": 140, "attack":15.0,"defense":15.0,"level": 14, "element":"fire","sprite_path": "sprites/sprite5_attack.png" },
      { "name": "Dragonite", "hp": 180, "max_hp": 220, "attack":40.0,"defense":5.0,"level": 20, "element":"water","sprite_path": "sprites/sprite6_attack.png" }
    ])
        
        self.state = "player_turn" 
        self.is_cage_image = False
        self.enemy_fixed_position = True
        self.bag = scene_manager._scenes["game"].game_manager.bag
        self.monsters = self.bag._monsters_data
        self.items = self.bag._items_data
        self.monsters = self.bag._monsters_data
        self.item_shop_buttons = self._create_item_buttons(self.items)
        self.monster_buttons =  self._create_monster_buttons(self.monsters)
        self.is_overlay = False
        self.is_buff = False
        self.is_monster = False
        self.heal_amount = 25
        self.damage = 0
        self.enemy_mon_ani = Animation(self.enemy_mon["sprite_path"], ["attack"], 4,(250,250))
        self._message = ""
        self._message_timer = 0
    def _create_item_buttons(self, items):
        buttons = []
        for index, item in enumerate(items):
            item_name = item.get("name")
            on_click_func = lambda name=item_name: self.shop(name)
            
            button = Button(
                "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
                0, 0, 250, 50,
                on_click=on_click_func
            )
            buttons.append(button)
        return buttons
    def _create_monster_buttons(self,monsters):
        buttons = []
        for monster in monsters:

            button = Button(
                "UI/raw/UI_Flat_Banner03a.png","UI/raw/UI_Flat_Bar01a.png",
                0, 0, 300, 100,            
                on_click= lambda monster = monster:  self.switch_monster(monster)           
                            )
            buttons.append(button)
        return buttons
    
    def overlay_change(self):
        self.is_overlay = True
        self.is_buff = False
        self.is_monster = False
    def overlay_unchange(self):
        self.is_overlay = False
    def buff_change(self):
        self.is_buff = True
        self.is_monster = False
    def monster_change(self):
        self.is_monster = True
        self.is_buff = False
    def take_damage(self,attacked,attack):
        self.check_element(attack)
        attacked["hp"] = max(0, min(attacked["hp"],attacked["hp"] - (attack["attack"]+self.damage) + attacked["defense"]))
        self.damage = 0
    def is_alive(self,monster):
        return monster["hp"] > 0
    def end_battle(self,victor):
        Logger.info(f"Battle ended. victor={victor}")
        self._message = f"{victor} wins"
        self._message_timer = 2
        

    @override
    def update(self, dt: float):
        
        self.tool_button.update(dt)
        self.button_x.update(dt)
        self.enemy_mon_ani.update(dt)
        if self._message_timer > 0:
            self._message_timer -= dt
        if self._message_timer <= 0:
            if "wins" in self._message:
                scene_manager.change_scene("game")
            else:
                self._message = "" # 計時結束，清空短暫訊息
                self._message_timer = 0
            
        # 2. 只有在沒有短暫訊息時，才顯示回合提示
        if self._message == "": # 檢查是否有正在顯示的短暫訊息
            if self.state == "player_turn" :
                self._message = "Player turn! Press RIGHT/D to Attack or DOWN/S to Run"
               
            elif self.state == "enemy_turn":
                self._message = "Enermy turn! Press LEFT/A to Attack or Up/w Run"
               
       
        # self.is_cage_image = False
        if self.state == "player_turn":
          
            
            Logger.info(f"Player turn - HP { self.player_mon ["hp"]} | Enemy HP {self.enemy_mon["hp"]}  (1:Attack  2:Run)")
            # self.state = "player_turn"
            Logger.info(f"{input_manager.key_pressed(pg.K_RIGHT)} {input_manager.key_pressed(pg.K_d)}")
            if  input_manager.key_pressed(pg.K_RIGHT) or input_manager.key_pressed(pg.K_d):
                self.take_damage(self.enemy_mon,self.player_mon)
                # Logger.info(f"Player attacks! Enemy HP is now {self.enemy_mon['hp']}")
                if not self.is_alive(self.enemy_mon):
                    for item in scene_manager._scenes["game"].game_manager.bag._items_data:
                        if item["name"] == "Potion":
                            item["count"] += 2
                        if item["name"] == "Coins":
                            item["count"] += 2  
                    for monster in scene_manager._scenes["game"].game_manager.bag._monsters_data:
                        if monster["name"] == self.player_mon["name"]:
                            monster["win_count"] += 1
                    #add_item function has a return
                            
                    Logger.info(f"{scene_manager._scenes["game"].game_manager.bag._items_data}")
                    scene_manager._scenes["game"].game_manager .save("saves/game0.json")
                   
                    self.end_battle(victor=self.player_mon["name"])
                  
      
                self.state = "enemy_turn"
                self.enemy_timer = 0.0
                self.enemy_mon["hp/ratio"] = self.enemy_mon["hp"]/self.enemy_mon["max_hp"]
                
            elif input_manager.key_pressed(pg.K_DOWN) or input_manager.key_pressed(pg.K_s):
                # Logger.info("You fled the battle!")
                scene_manager.change_scene("game")
                
                
        elif self.state == "enemy_turn" :
    
            
            # if self.enemy_timer >= self.enemy_delay:
            if input_manager.key_pressed(pg.K_LEFT) or input_manager.key_pressed(pg.K_a):
                self.take_damage(self.player_mon,self.enemy_mon)
                # Logger.info(f"Enemy attacks! Player HP is now {self.player_mon['hp']}")
                
                if not self.is_alive(self.player_mon):
                    
                    self.end_battle(victor=self.enemy_mon["name"])
                 
                
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
        
        if self.is_overlay  and not self.is_buff and not self.is_monster:
            self.buff_button.update(dt)
            self.monster_button.update(dt)
            self.portion_button.update(dt)
        elif self.is_overlay and self.is_buff and not self.is_monster:
            for button in self.item_shop_buttons:

                button.update(dt)
        elif self.is_overlay and  not self.is_buff and  self.is_monster:
            for button in self.monster_buttons:

                button.update(dt)
        self.player_mon_hp_ratio = self.player_mon["hp"]/self.player_mon["max_hp"]
        self.enemy_mon_hp_ratio = self.enemy_mon["hp"]/self.enemy_mon["max_hp"]
    @override
    def draw(self,screen):
        self.background.draw(screen)
        # draw player monster (left bottom)
        player_mon = Sprite(self.player_mon["sprite_path"], (150,150))
        player_mon.rect.topleft = (100, GameSettings.SCREEN_HEIGHT -350)
        player_mon.draw(screen)
        element_path_dict = {
            "fire": "element/42697fire_98982.png",
            "water":"element/water_drop_icon_175805.png",
            "grass" : "element/2998140-eco-garden-grass_99847.png"
        }
        element = Sprite(element_path_dict[self.player_mon["element"]],(30,30))
        element.rect.left = player_mon.rect.right + 50
        element.rect.top =  player_mon.rect.top + 60
        pg.draw.circle(screen,(0,0,0),element.rect.center,20,True)
        element.draw(screen)
        # draw enemy monster (right top)
        
        self.enemy_mon_ani.rect.topleft = (GameSettings.SCREEN_WIDTH - 350, 100)
        # if not self.cage_drop_active and not self.is_cage_image:
        
        self.enemy_mon_ani.draw(screen)
        element = Sprite(element_path_dict[self.enemy_mon["element"]],(30,30))
        element.rect.topright = self.enemy_mon_ani.rect.bottomleft
        pg.draw.circle(screen,(0,0,0),element.rect.center,20,True)
        element.draw(screen)
        if self.if_check_element(self.player_mon) :
            monster = self.if_check_element(self.player_mon)
            damage = (monster["attack"])//2
            text_content = f"player's monster attack : {self.player_mon['attack']}+{damage} \n" \
               f"player's monster defense : {self.player_mon['defense']}\n" \
               f"enemy's monster attack : {self.enemy_mon['attack']} \n" \
               f"enemy's monster defense : {self.enemy_mon['defense']}"
        elif self.if_check_element(self.enemy_mon):
            monster = self.if_check_element(self.enemy_mon)
            damage = monster["attack"]//2
            text_content = f"player's monster attack : {self.player_mon['attack']}\n" \
               f"player's monster defense : {self.player_mon['defense']}\n" \
               f"enemy's monster attack : {self.enemy_mon['attack']}+{damage} \n" \
               f"enemy's monster defense : {self.enemy_mon['defense']}" 
        else:
            text_content = f"player's monster attack : {self.player_mon['attack']}\n" \
               f"player's monster defense : {self.player_mon['defense']}\n" \
               f"enemy's monster attack : {self.enemy_mon['attack']} \n" \
               f"enemy's monster defense : {self.enemy_mon['defense']}" 
        
            
        font_1 = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        

        # 2. 將字串按換行符號分割成行
        lines = text_content.split('\n')

        # 3. 定義起始繪製位置和行高間距
        x_start = 50  # 假設的起始 X 座標
        y_start = 50  # 假設的起始 Y 座標
        line_height = font_1.get_linesize() # 獲取字體的高度作為行高

        # 4. 在 draw 函式中，迴圈渲染每一行
        current_y = y_start

        for line in lines:
            # 對每一行單獨渲染成 Surface
            line_surface = font_1.render(line, True, (255, 255, 255))
            
            # 繪製到螢幕上 (假設 screen 是您的 Pygame 螢幕物件)
            screen.blit(line_surface, (x_start, current_y))
            
            # 更新下一行的 Y 座標
            current_y += line_height  
       # 畫面訊息：由 draw 每幀負責繪製，避免被後續繪圖蓋掉
    
        if self._message :
            print(f"self.state = {self.state}")
            if self._message_timer > 0:
                # 短暫訊息 (例如：使用藥水、屬性相剋)，使用紅字高亮
                self.draw_message_color(screen, self._message)
            elif self._message_timer <= 0 and "wins" not in self._message:
                # 回合提示訊息 (self._message_timer 已經清空，但 self._message 剛被 update 設為回合提示)
                self.draw_message(screen, self._message)
       

        pg.draw.rect(screen, (80, 80, 80), (150, GameSettings.SCREEN_HEIGHT - 150, self.player_mon["max_hp"] , 10))
        pg.draw.rect(screen, (0, 200, 0), (150, GameSettings.SCREEN_HEIGHT - 150, self.player_mon["max_hp"] * self.player_mon_hp_ratio ,10))
        
        font = pg.font.SysFont(None, 20)
        hp_repr = font.render(f"hp of player monster {self.player_mon["hp"]}", True, (0,0,0))
        screen.blit(hp_repr, (150, GameSettings.SCREEN_HEIGHT - 180))

        #the HP bars of enemy_mon
        pg.draw.rect(screen, (80, 80, 80), (GameSettings.SCREEN_WIDTH - 250, 100, self.enemy_mon["max_hp"] , 10))
        pg.draw.rect(screen, (0, 200, 0), (GameSettings.SCREEN_WIDTH - 250, 100,self.enemy_mon["max_hp"] * self.enemy_mon_hp_ratio ,10))
        
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
            mon_rect = self.enemy_mon_ani.rect.copy()
            mon_rect.centerx = cage_rect.centerx - 30
            mon_rect.centery = cage_rect.centery - 30
            # 文字位置
            font = pg.font.SysFont(None, 40)
            message = font.render("the monster is caught", True, (128, 0, 32))
            message_rect = message.get_rect()
            message_rect.midbottom = (cage_rect.centerx,cage_rect.top)
            self.banner_image_rect.center = message_rect.center
            # 繪製怪獸（籠子裡）
            enemy_mon_caught = Animation(self.enemy_mon["sprite_path"], ["attack"], 4,(150,150))
            enemy_mon_caught.rect = mon_rect
            
            enemy_mon_caught.draw(screen)
            # 繪製籠子（蓋在怪獸上面）
            screen.blit(self.cage_image, cage_rect)
            #the monster is caught
            screen.blit(self.banner_image, self.banner_image_rect)
            screen.blit(message, message_rect)
        
        if self.is_overlay :
            #overlay
            overlay = pg.Surface(screen.get_size())
            overlay.fill((0, 0, 0))   # 填滿黑色
            overlay.set_alpha(120)    # 半透明
            screen.blit(overlay, (0, 0))   # 貼到畫面上
            self.panel_rect.center = screen.get_rect().center #拿我自己的中心點 去對齊 螢幕的中心點
            screen.blit(self.panel_img, self.panel_rect)
            #draw x_button
            self.button_x.draw(screen)
            if  not self.is_buff and not self.is_monster:
              
                # draw portion button
                self.portion_button.draw(screen)
                
                # draw buff button
                self.buff_button.draw(screen)
                scene_manager.write(30,"use buff",screen,(0,0,0),(330,315))
                #draw monster button
                self.monster_button.draw(screen)
                scene_manager.write(30,"switch monster",screen,(0,0,0),(315,415))
                # draw portion text
                font = pg.font.SysFont(None, 30)
                portion_text = font.render("Use Portion", True, (0,0,0))
                portion_text_rect = portion_text.get_rect()     
                portion_text_rect.center = self.portion_button.hitbox.center
                screen.blit(portion_text, portion_text_rect)
            elif self.is_buff and not self.is_monster:
                x = 300     # icon 起始位置
                y = 250
                spacing = 110
                for index, item in enumerate(self.bag._items_data):
                    name = item.get("name", "Unknown")
                    if (name == "defence_buff") or  (name == "attack_buff") or (name == "heal_buff"):
                        button = self.item_shop_buttons[index] # 取得這個 item 專屬的 Button 實例
                        
                        amt  = item.get("amount", item.get("count", 0))
                        # shop_button (使用獨立按鈕)
                        button.hitbox.centerx = x + 100
                        button.hitbox.centery = y + 20
                        button.draw(screen) # 繪製獨立按鈕
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

                        

                        y += spacing
            elif self.is_monster and not self.is_buff:
               
                font = pg.font.SysFont(None, 28)

                x = 300
                y = 150
                spacing = 110   # 每隻怪獸的縱向間距
                if not self.bag._monsters_data:
                    
                    return
                for index,mon in enumerate(self.bag._monsters_data):
                    print("this print monster")
                    name = mon.get("name", "Unknown")
                    level = mon.get("level", 1)
                    hp = mon.get("hp", 1)
                    max_hp = mon.get("max_hp", 1)

                    sprite_path = "assets/images/" + mon.get("sprite_path")
                    sprite = pg.image.load(sprite_path).convert_alpha()
                    sprite = pg.transform.scale(sprite, (90, 90))
                    # # ---white background----
                    button = self.monster_buttons[index]
                    button.hitbox.centerx = x + 120
                    button.hitbox.centery = y  + 50
                    button.draw(screen) # 繪製獨立按鈕

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
        if not  self.is_overlay :
            self.tool_button.hitbox.centerx = screen.get_rect().centerx
            self.tool_button.hitbox.bottom = GameSettings.SCREEN_HEIGHT -150
            self.tool_button.draw(screen)
            font = pg.font.SysFont(None, 30)
            tool_text = font.render("change monster", True, (0,0,0))
            tool_text_rect = tool_text.get_rect()     
            tool_text_rect.center = self.tool_button.hitbox.center
            screen.blit(tool_text, tool_text_rect)
       
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
        self.player_mon["hp"] = min(self.player_mon["max_hp"], self.player_mon["hp"] + self.heal_amount)
        self.player_mon_hp_ratio= self.player_mon["hp"]/self.player_mon["max_hp"]
        # Decrease portion count in the bag
        for item in scene_manager._scenes["game"].game_manager.bag._items_data:
            if item["name"] == "Potion":
                item["count"] -= 1
                break
        self._message = f"Used a portion! Healed {self.heal_amount} HP."
        self._message_timer = 2.0


    def shop(self,item_name):
      
        for item in scene_manager._scenes["game"].game_manager.bag._items_data:
            if item["count"] > 1:
                item["count"] -= 1
            else:
                self._message = "insufficient items"
                self.message_timer = 2
            if item["name"] == "defence_buff":
               
                self.player_mon["defense"] += 20
            if item["name"] == "attack_buff":

                self.player_mon["attack"] += 20
            if item["name"] == "heal_buff":
               self.heal_amount += 10
        self.is_buff = False
    def switch_monster(self,monster):
        self.player_mon = monster
    def check_element(self,monster):
        
        element_dict = {"water":"fire","fire":"grass","grass":"water"}
       
        print(f"DEBUG: Player Element: {self.player_mon['element']}, Enemy Element: {self.enemy_mon['element']}")
        if monster == self.player_mon:
            if element_dict[self.player_mon["element"]] == self.enemy_mon["element"]:
                
                self._message = f"{self.player_mon["name"]} attak increases 50%"
                self._message_timer = 2 
                self.damage = self.player_mon["attack"]//2
        elif monster == self.enemy_mon:
             if element_dict[self.enemy_mon["element"]] == self.player_mon["element"]:
                
                self._message = f"{self.enemy_mon["name"]} attak increases 50%"
                self._message_timer = 1.0
                self.damage = self.enemy_mon["attack"]//2
    def if_check_element(self,monster):
        element_dict = {"water":"fire","fire":"grass","grass":"water"}
        
        print(f"DEBUG: Player Element: {self.player_mon['element']}, Enemy Element: {self.enemy_mon['element']}")
        if monster == self.player_mon:
            if element_dict[self.player_mon["element"]] == self.enemy_mon["element"]:
                
                return self.player_mon
        elif monster == self.enemy_mon:
             if element_dict[self.enemy_mon["element"]] == self.player_mon["element"]:
                
                return self.enemy_mon
            
       

            