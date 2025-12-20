import pygame as pg
import threading
import time
import math
import random

from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.interface.components import Button
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import scene_manager, sound_manager, input_manager
from src.sprites import Animation
from src.sprites import Sprite,BackgroundSprite
from typing import override
from src.scenes.pathfinding_service import PathfindingService, TileCoord



class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
    
    def __init__(self):
        super().__init__()
        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
        #minimap
        self.minimap_surface: pg.Surface | None = None
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
        else:
            self.online_manager = None
        self.sprite_online = Animation(
            "character/ow1.png", ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        #TODO add a button to game secne on left top page
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            GameSettings.SCREEN_WIDTH - 100, 10 , 100, 100,
            lambda: scene_manager.push_scene("setting")
        )
        self.button_backpack = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            GameSettings.SCREEN_WIDTH - 200, 10 , 100, 100,
            lambda: scene_manager.push_scene("bag")
        )
        self.speedup_button = Button(
           "UI/raw/UI_Flat_Banner03a.png","UI/raw/UI_Flat_Bar01a.png",
                0, 0, 300, 100,            
                on_click= lambda :  self.speed_up()  
        )
        # nevagation
        self.pathfinding_service = PathfindingService(self.game_manager)
        self.current_path: list[TileCoord] = [] # 儲存計算出的路徑 (使用 TileCoord tuple)
        
        # 範例目的地列表 (現在使用 TileCoord tuple)
       
        
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.gym_button = Button( "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            GameSettings.SCREEN_WIDTH - 300, 10 , 80, 80,
            on_click=self.go_to_gym)
        self.battle_button = Button( "UI/raw/UI_Flat_Button02a_4.png", "UI/raw/UI_Flat_Button02a_2.png",
            GameSettings.SCREEN_WIDTH - 400, 10 , 80, 80,
            on_click=self.go_to_battle)
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.current_path = []
        self.move_index = 0
        self.move_P_index = 0
        self.timer = 0
        self.done = False
        self.is_starburst_active = False
        self.starburst_timer = 0.0
        self.starburst_duration = 0.8 
        self.num_rays = 6
        self.starburst_color = (0, 0, 0)
        self.move_to_path = [(34,17),(26,18),(23,23),(18,28),(12,32)]
        self.move_back_path = [(18,28),(23,23),(26,18),(45,14)]
        self.pokemonball_path = []
        self.pokemonball_sprite = Sprite("ingame_ui/ball.png",(32,32))
        self.is_catch = False
        self.barrar_img = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.barrar_img = pg.transform.scale(self.barrar_img, (300, 100))
        self.barrar_posi = (0,0)
        self._message = ""
        self._message_timer = 0
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        self.monster_collection = self.evolve()
        if self.monster_collection:
            self.trigger_starburst()

        self.monster_catch = []
        
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        self.gym_button.update(dt)
        self.battle_button.update(dt)
        self.speedup_button.update(dt)
        if self._message_timer > 0:
            self._message_timer -= dt
        if self._message_timer <= 0:
            self._message = "" # 計時結束，清空短暫訊息
            self._message_timer = 0
        # animation for change scene
        if self.is_starburst_active:
            self.starburst_timer += dt
            if self.starburst_timer >= self.starburst_duration:
                self.is_starburst_active = False
                self.starburst_timer = 0.0
                scene_manager.change_scene("evolution")
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
        
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
        for npc in self.game_manager.current_npcs():
            npc.update(dt)
            
        # Update others
        self.game_manager.bag.update(dt)
        
        if self.game_manager.player is not None and self.online_manager is not None:
            
            current_direction = self.game_manager.player.animation.cur_row

            _ = self.online_manager.update(
                self.game_manager.player.position.x, 
                self.game_manager.player.position.y,
                self.game_manager.current_map.path_name,
                current_direction
            )
        
        

        self.setting_button.update(dt)
        self.button_backpack.update(dt)
        if not self.current_path:
            if self.game_manager.check_move_collision(self.game_manager.player.animation.rect):
                self.current_path = self.move_to_path.copy()
                self.move_index = 0 # 重置索引
                self.timer = 0
            elif self.game_manager.check_move_back_collision(self.game_manager.player.animation.rect):
                self.current_path = self.move_back_path.copy()
                self.move_index = 0
                self.timer = 0
        
        if self.current_path and self.game_manager.player:
            if self.move_index < len(self.current_path):
                # print(self.current_path)  # 有在跑
                pos = self.current_path[self.move_index]
                x,y = pos
                x = x*GameSettings.TILE_SIZE
                y = y*GameSettings.TILE_SIZE
                
                if self.timer > 0 :
                    self.timer -= dt
                else:
                    if self.game_manager.player.position.x > x:
                        self.game_manager.player.animation.switch("left")
                    elif self.game_manager.player.position.x < x:
                        self.game_manager.player.animation.switch("right")
                    elif self.game_manager.player.position.y > y:
                        self.game_manager.player.animation.switch("up")
                    elif self.game_manager.player.position.y < y:
                        self.game_manager.player.animation.switch("down") 
                    self.game_manager.player.position = Position(x,y)
                    self.timer = 0.5
                    
                    self.move_index += 1
                    
                    
            else:
                self.done = True
                self.current_path = []
        # print(self.game_manager.check_move_collision(self.game_manager.player.animation.rect))
        # print(self.game_manager.player.position)
        # if self.game_manager.check_move_collision(self.game_manager.player.animation.rect):
        # the next frame the condition will be false and the player stop
        if self.game_manager.check_pokemonball_collision(self.game_manager.player.animation.rect) and input_manager.key_pressed(pg.K_SPACE):
            # print("hello")
            self.pokemonball_path = [(random.randint(41,61)* GameSettings.TILE_SIZE ,random.randint(1,36)* GameSettings.TILE_SIZE) for _ in range(40)]
            # print(self.pokemonball_path)
        if self.pokemonball_path :
            if self.move_P_index < len(self.pokemonball_path):
                # print(self.current_path)  # 有在跑
                if not self.game_manager.player.animation.rect.colliderect(self.pokemonball_sprite.rect):
                    pos = self.pokemonball_path[self.move_P_index]
                
                    if self.timer > 0 :
                        self.timer -= dt
                    else:
                        self.pokemonball_sprite.rect.topleft = pos
                        self.timer = 2
                        
                        self.move_P_index += 1
                else:
                    # print("yes")
                    for item in self.game_manager.bag._items_data:

                        if item["name"] == "Pokeball":

                            item["count"] += 1
                    catch_monster = random.choice([
      { "name": "Pikachu",   "hp": 85,  "max_hp": 100,"attack":10,"defense":10 ,"level": 12,"element": "grass","win_count" : 0, "sprite_path": "menu_sprites/menusprite1.png" },
      { "name": "evolved Charizard", "hp": 150, "max_hp": 200, "attack":50,"defense":50,"level": 36,"element": "grass", "win_count" : 0,"sprite_path": "sprites/sprite2_evolved.png" },
      { "name": "Blastoise", "hp": 120, "max_hp": 180, "attack":30,"defense":30,"level": 16,"element": "water", "win_count" : 0,"sprite_path": "menu_sprites/menusprite3.png" },
      { "name": "Venusaur",  "hp": 90,  "max_hp": 160, "attack":10,"defense":10,"level": 15,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite4.png" },
      { "name": "Gengar",    "hp": 110, "max_hp": 140, "attack":15,"defense":15,"level": 14,"element": "fire", "win_count" : 0,"sprite_path": "menu_sprites/menusprite5.png" },
      { "name": "evolved Dragonite", "hp": 200, "max_hp": 220, "attack":80,"defense":80,"level": 40, "element": "water","win_count" : 0,"sprite_path": "sprites/sprite6_evolved.png" }
    ])
                    
                    self.monster_catch.append(catch_monster)
                    self.game_manager.bag._monsters_data.append(catch_monster)
                    self.game_manager .save("saves/game0.json")
                    self.is_catch = True
                    self.pokemonball_path = []
            else:
                self.pokemonball_path = []
                self.move_P_index = 0
    

    def go_to_gym(self):
    
        self.DESTINATIONS: dict[str, TileCoord] = {
            "gym": (24, 24), 
            "battle": (24, 30)
    
        }
      
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.current_path = []
        self.move_index = 0
        self.timer = 0
        self.done = False
        self.is_go_to_gym = True
        self.start_navigation(self.DESTINATIONS["gym"])
    def go_to_battle(self):
        if self.game_manager.current_map.path_name == "map.tmx":
            self.DESTINATIONS: dict[str, TileCoord] = {
                "gym": (24, 24), 
                "battle": (24, 30)
        
            }
        elif self.game_manager.current_map.path_name == "beach_map.tmx":
              self.DESTINATIONS: dict[str, TileCoord] = {
                
                "battle": (54, 26)
        
            }
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.current_path = []
        self.move_index = 0
        self.timer = 0
        self.done = False

        self.is_go_to_battle = True
        # print(self.DESTINATIONS)
        self.start_navigation(self.DESTINATIONS["battle"])
       
    def trigger_starburst(self):
       
        self.is_starburst_active = True
        self.starburst_timer = 0.0
    def reset_minimap(self) -> None:
        """當地圖切換時，清除舊的 minimap 表面，強制重新渲染新地圖。"""
        self.minimap_surface = None
    def start_navigation(self, target_tile: TileCoord):
        """觸發路徑計算並設置目標"""
        if self.game_manager.player and (self.is_go_to_gym == True or self.is_go_to_battle == True) and not (self.is_go_to_gym == True and self.is_go_to_battle == True):
            player_pos = self.game_manager.player.position # 獲取玩家的像素座標 (Position)
            # print(player_pos)
            # 呼叫 PathfindingService 進行計算
            self.current_path = self.pathfinding_service.find_path_bfs(
                player_pos, 
                target_tile
            )
            
               
        else:
            self.current_path = []
    @override
    def draw(self, screen: pg.Surface):        
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
            
            camera = self.game_manager.player.camera
            '''
            
            #player is the position of player
            camera = self.game_manager.player.camera
            #camera = PositionCamera(16 * GameSettings.TILE_SIZE, 30 * GameSettings.TILE_SIZE)
            self.game_manager.current_map.draw(screen, camera)
            self.draw_navigation_path(screen)
            if self.done == True:
                self.game_manager.current_map.draw(screen, camera)
            # print(f"{repr(self.game_manager.current_map.path_name)}_______________")
            self.game_manager.player.draw(screen, camera)
           

        else:
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
        
        self.draw_minimap(screen)

        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)
        for npc in self.game_manager.current_npcs():
            npc.draw(screen, camera)

        self.game_manager.bag.draw(screen)
        
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            #                                                                                                                                                                                            
            for player in list_online:

                if player["map"] == self.game_manager.current_map.path_name:
                    cam = self.game_manager.player.camera
                    pos = cam.transform_position_as_position(Position(player["x"], player["y"]))
                    direction = player["direction"]
                    self.sprite_online.update_pos(pos)
                    self.sprite_online.switch(direction)
                    self.sprite_online.draw(screen)
        if self._message :
           
            self.draw_message(screen, self._message)
       
        
        # setting_button
        self.setting_button.img_button_default =  Sprite("UI/button_setting.png", (80,80))
        self.setting_button.img_button_hover =  Sprite("UI/button_setting_hover.png", (80,80 ))
        
        self.setting_button.hitbox.size  = (80,80)
        self.setting_button.draw(screen)

        # button_backpack

        self.button_backpack.img_button_default =  Sprite("UI/button_backpack.png", (80,80))
        self.button_backpack.img_button_hover =  Sprite("UI/button_backpack_hover.png", (80,80))
        
        self.button_backpack.hitbox.size  = (80,80)
        self.button_backpack.draw(screen)
        # draw gym_button
        self.gym_button.draw(screen)
        pg.draw.circle(screen, (0, 200, 255) , ( GameSettings.SCREEN_WIDTH - 260, 45), 25)
        scene_manager.write(35,"gym",screen,(0,0,0),( GameSettings.SCREEN_WIDTH - 280, 35))
        # draw battle_button
        self.battle_button.draw(screen)
        pg.draw.circle(screen,(255, 100, 0) , ( GameSettings.SCREEN_WIDTH - 360, 45), 25)
        scene_manager.write(35,"battle",screen,(0,0,0),( GameSettings.SCREEN_WIDTH - 400, 35))
        if self.is_starburst_active:
            self.draw_starburst_transition(screen)
        if self.pokemonball_path and self.game_manager.player:
            # 獲取目前的相機實例
            camera = self.game_manager.player.camera
            
            # 1. 取得球在世界中的位置 (像素)
            world_pos = Position(self.pokemonball_sprite.rect.x, self.pokemonball_sprite.rect.y)
            
            # 2. 透過相機轉換成螢幕上的座標
            screen_pos = camera.transform_position_as_position(world_pos)
            
            # 3. 建立一個臨時 rect 並繪製
            draw_rect = self.pokemonball_sprite.rect.copy()
            draw_rect.topleft = (int(screen_pos.x), int(screen_pos.y))
            
            # 直接用 screen.blit 繪製，確保它在地圖物件層之上
            screen.blit(self.pokemonball_sprite.image, draw_rect)
        x = 900
        y = 100
        if self.is_catch and self.game_manager.current_map.path_name == "beach_map.tmx":

            if not self.monster_catch:
                return

            font = pg.font.SysFont(None, 28)

            x = 900
            y = 100
            spacing = 110   # 每隻怪獸的縱向間距

            for mon in self.monster_catch:

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
                
        if self.game_manager.current_map.path_name == "beach_map.tmx":
            self.speedup_button.hitbox.top = y
            self.speedup_button.hitbox.left = x
            self.speedup_button.draw(screen)
            font = pg.font.Font("assets/fonts/Pokemon Solid.ttf", 30)

            # show message
            message_page = font.render("speed up", True, (0,0,0))
            message_page_rect = message_page.get_rect()
            message_page_rect.center = self.speedup_button.hitbox.center
            screen.blit(message_page, message_page_rect)


        
       
    def draw_minimap(self, screen: pg.Surface) -> None:
        if self.game_manager.player is None:
            return

        # --- Minimap 參數設定 ---
        MINIMAP_SIZE = 200      # Minimap 繪製的最大尺寸 (固定邊長)
        MINIMAP_MARGIN = 10     # 距離畫面邊緣的距離
        RED_DOT_RADIUS = 3
        
        current_map = self.game_manager.current_map
        TILE_SIZE = GameSettings.TILE_SIZE
        
        # 1. 載入/預渲染地圖 (只在 self.minimap_surface 為 None 時執行)
        if self.minimap_surface is None:
            
            # 取得地圖的實際世界尺寸 (像素)
            # 依賴 map.py 中的 tmxdata 屬性來獲得瓦片寬高
            World_W = current_map.tmxdata.width * TILE_SIZE
            World_H = current_map.tmxdata.height * TILE_SIZE
            
            # 決定縮放比例 (以長邊為準，確保整個地圖能放進 200x200 框)
            scale_factor = MINIMAP_SIZE / max(World_W, World_H)
            Minimap_W = int(World_W * scale_factor)
            Minimap_H = int(World_H * scale_factor)

            # 創建 World 尺寸的 Surface 繪製整個地圖
            minimap_unscaled_surface = pg.Surface((World_W, World_H))
            minimap_unscaled_surface.fill((30, 30, 30)) 
            
            # 使用 (0, 0) 鏡頭繪製整個地圖和靜態實體
            global_camera = PositionCamera(0, 0)
            current_map.draw(minimap_unscaled_surface, global_camera)
            
            # 繪製靜態實體 (Enemy/NPC) 到 Minimap 背景上
            for enemy in self.game_manager.current_enemy_trainers:
                enemy.draw(minimap_unscaled_surface, global_camera)
            for npc in self.game_manager.current_npcs():
                npc.draw(minimap_unscaled_surface, global_camera)

            # 縮放並儲存結果，同時儲存世界尺寸和比例供紅點計算使用
            self.minimap_surface = pg.transform.scale(minimap_unscaled_surface, (Minimap_W, Minimap_H))
            self.minimap_world_w = World_W
            self.minimap_world_h = World_H
            
        # 2. Blit 預渲染的 Minimap 背景 (左上角貼圖)
        scaled_minimap = self.minimap_surface
        
        # 最終貼圖位置 (左上角貼圖，只使用邊距)
        final_blit_pos = (MINIMAP_MARGIN, MINIMAP_MARGIN)
        screen.blit(scaled_minimap, final_blit_pos)
        
        # 3. 繪製玩家紅點 (利用相對座標實現動態追蹤)
        player_pos = self.game_manager.player.position
        
        # 相對座標 (0 到 1 之間): 玩家世界坐標 / 世界總寬高
        relative_x = player_pos.x / self.minimap_world_w
        relative_y = player_pos.y / self.minimap_world_h
        
        # 紅點在縮小地圖上的絕對坐標 = 相對座標 * 縮小地圖的寬高
        dot_x = int(relative_x * scaled_minimap.get_width())
        dot_y = int(relative_y * scaled_minimap.get_height())
        
        # 紅點在主畫面上的最終坐標 (加上 Minimap 貼圖的左上角位置)
        red_dot_screen_x = MINIMAP_MARGIN + dot_x
        red_dot_screen_y = MINIMAP_MARGIN + dot_y
        
        # 繪製紅點
        pg.draw.circle(screen, (255, 0, 0), (red_dot_screen_x, red_dot_screen_y), RED_DOT_RADIUS)
        
        # 繪製 Minimap 邊框
        pg.draw.rect(screen, (255, 255, 255), 
                     (MINIMAP_MARGIN, MINIMAP_MARGIN, scaled_minimap.get_width(), scaled_minimap.get_height()), 
                     2)
    def draw_navigation_path(self, screen: pg.Surface):
        """在螢幕上繪製計算出的路徑指引"""
        if not self.current_path or not self.game_manager.player:
            return
        
        camera = self.game_manager.player.camera
        
        # 迭代並繪製路徑上的所有格子
        for i, (tile_x, tile_y) in enumerate(self.current_path):
            
            # 1. 計算該格子的中心像素座標 (世界座標)
            center_x = tile_x * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
            center_y = tile_y * GameSettings.TILE_SIZE + GameSettings.TILE_SIZE // 2
            world_pos = Position(center_x, center_y)
            # 2. 轉換為螢幕座標 (考慮鏡頭位移)
            screen_pos = camera.transform_position_as_position(world_pos)
            
            # 3. 繪製路徑標記 (例如：藍色圓點)
            color = (0, 200, 255) if i < len(self.current_path) - 1 else (255, 100, 0) # 終點用橘色
            radius = 4
            pg.draw.circle(screen, color, (int(screen_pos.x), int(screen_pos.y)), radius)
    def evolve(self):

        evolution_info = {
  "Pikachu":   { "name": "evolved Pikachu",   "hp": 150, "max_hp": 220, "attack": 60, "defense": 35, "level": 25, "element": "grass", "win_count": 0, "sprite_path": "sprites/sprite1_evolved.png" },
  "Charizard": { "name": "evolved Charizard", "hp": 190, "max_hp": 280, "attack": 80, "defense": 50, "level": 36, "element": "grass", "win_count": 0, "sprite_path": "sprites/sprite2_evolved.png" },
  "Blastoise": { "name": "evolved Blastoise", "hp": 210, "max_hp": 300, "attack": 85, "defense": 60, "level": 32, "element": "water", "win_count": 0, "sprite_path": "sprites/sprite3_evolved.png" },
  "Venusaur":  { "name": "evolved Venusaur",  "hp": 180, "max_hp": 250, "attack": 70, "defense": 45, "level": 30, "element": "fire",  "win_count": 0, "sprite_path": "sprites/sprite4_evolved.png" },
  "Gengar":    { "name": "evolved Gengar",    "hp": 170, "max_hp": 240, "attack": 75, "defense": 45, "level": 28, "element": "fire",  "win_count": 0, "sprite_path": "sprites/sprite5_evolved.png" },
  "Dragonite": { "name": "evolved Dragonite", "hp": 250, "max_hp": 350, "attack": 100, "defense": 80, "level": 40, "element": "water", "win_count": 0, "sprite_path": "sprites/sprite6_evolved.png" }
}
        monster_collection = []
        for monster in self.game_manager.bag._monsters_data:
           
            if monster["win_count"] > 0 and "evolved" not in monster["name"] :
                name = monster["name"]
                monster["name"] =  (evolution_info[name])["name"]
                monster["hp"] =  (evolution_info[name])["hp"]
                monster["max_hp"] =  (evolution_info[name])["max_hp"]
                monster["attack"] =  (evolution_info[name])["attack"]
                monster["defense"] =  (evolution_info[name])["defense"]
                monster["level"] =  (evolution_info[name])["level"]
                monster["win_count"] =  (evolution_info[name])["win_count"]
                monster["sprite_path"] =  (evolution_info[name])["sprite_path"]
                monster_collection.append(monster)
        self.game_manager .save("saves/game0.json")
       
        return monster_collection
    def draw_starburst_transition(self, screen: pg.Surface):
        center_x = GameSettings.SCREEN_WIDTH // 2
        center_y = GameSettings.SCREEN_HEIGHT // 2
        screen_center = (center_x, center_y)

        progress = self.starburst_timer / self.starburst_duration
        max_radius = pg.Vector2(center_x, center_y).length()
        current_radius = max_radius * progress 
        
        # --- 修正後的參數 ---
        self.num_rays = 6             # 光芒數量
        RAY_WIDTH_DEG = 10             # 每個光芒的寬度 (度)
        
        angle_step = 360 / self.num_rays # 每個光芒的中心線間隔 (60 度)

        for i in range(self.num_rays):
            # 1. 計算該光芒的中心角度
            center_angle = i * angle_step
            
            # 2. 定義光芒的起始角和結束角 (創造空隙)
            start_angle = center_angle - RAY_WIDTH_DEG / 2
            end_angle = center_angle + RAY_WIDTH_DEG / 2
            
            # 3. 轉換為弧度
            start_rad = math.radians(start_angle) 
            end_rad = math.radians(end_angle)
            
            # 頂點 1：中心點
            point1 = screen_center
            
            # 頂點 2: 沿著 start_rad 的邊緣點
            point2 = (
                center_x + current_radius * math.cos(start_rad),
                center_y - current_radius * math.sin(start_rad)
            )
            # 頂點 3: 沿著 end_rad 的邊緣點
            point3 = (
                center_x + current_radius * math.cos(end_rad),
                center_y - current_radius * math.sin(end_rad)
            )

            # 繪製三角形
            pg.draw.polygon(screen, self.starburst_color, [point1, point2, point3])
    def speed_up(self):

        for item in self.game_manager.bag._items_data:

            if item["name"] == "Coins":
                if item["count"] > 5:
                    item["count"] -= 5
                    self._message = "Coins - 5 speed up 200"
                    self._message_timer = 2
                    self.game_manager.player.speed += 200
                else:
                    self._message = "insufficient coins, more battle to earn coins"
                    self._message_timer = 2

      
    def draw_message(self, screen: pg.Surface, message: str):

        font = pg.font.Font("assets/fonts/Minecraft.ttf", 30)

        # show message
        message_page = font.render(message, True, (255,255,255))
        message_page_rect = message_page.get_rect()
        message_page_rect.top = screen.get_rect().top
        message_page_rect.left = 230

        screen.blit(message_page, message_page_rect)
            



                


            
            
        