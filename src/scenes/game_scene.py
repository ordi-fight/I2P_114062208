import pygame as pg
import threading
import time
import math

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
        # nevagation
        self.pathfinding_service = PathfindingService(self.game_manager)
        self.current_path: list[TileCoord] = [] # 儲存計算出的路徑 (使用 TileCoord tuple)
        
        # 範例目的地列表 (現在使用 TileCoord tuple)
        self.DESTINATIONS: dict[str, TileCoord] = {
            "gym": (24, 24), 
            "battle": (24, 30),
    
        }
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
        self.timer = 0
        self.done = False
        self.is_starburst_active = False
        self.starburst_timer = 0.0
        self.starburst_duration = 0.8 
        self.num_rays = 6
        self.starburst_color = (0, 0, 0)
      
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        if self.online_manager:
            self.online_manager.enter()
        self.monster_collection = self.evolve()
        if self.monster_collection:
            self.trigger_starburst()
    @override
    def exit(self) -> None:
        if self.online_manager:
            self.online_manager.exit()
        
    @override
    def update(self, dt: float):
        self.gym_button.update(dt)
        self.battle_button.update(dt)
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
                


                

    def go_to_gym(self):
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.current_path = []
        self.move_index = 0
        self.timer = 0
        self.done = False

        self.is_go_to_gym = True
        self.start_navigation(self.DESTINATIONS["gym"])
    def go_to_battle(self):
        self.is_go_to_gym = False
        self.is_go_to_battle = False
        self.current_path = []
        self.move_index = 0
        self.timer = 0
        self.done = False

        self.is_go_to_battle = True
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
            
            # for pos in self.current_path:
            #     x,y = pos
            #     x = x* GameSettings.TILE_SIZE
            #     y = y* GameSettings.TILE_SIZE
                
            #     self.game_manager.player.position = Position(x,y)
            
            
            # Logger.info(f"Path {self.current_path}")
            # Logger.info(f"Path calculated with {len(self.current_path)} steps.")
            # if self.is_go_to_gym == False and self.is_go_to_battle == True:
            #     self.is_go_to_battle = False
            # if self.is_go_to_gym == True and self.is_go_to_battle == False:
            #     self.is_go_to_gym = False
               
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
            "Pikachu":
        { "name": "evolved Pikachu",   "hp": 100,  "max_hp": 150,"attack":20,"defense":20 ,"level": 25,"element": "grass","win_count" : 0, "sprite_path": "sprites/sprite1_evolved.png" },
        "Charizard":
        { "name": "evolved Charizard", "hp": 150, "max_hp": 200, "attack":50,"defense":50,"level": 36,"element": "grass", "win_count" : 0,"sprite_path": "sprites/sprite2_evolved.png" },
        "Blastoise":
        { "name": "evolved Blastoise", "hp": 160, "max_hp": 180, "attack":60,"defense":60,"level": 32,"element": "water", "win_count" : 0,"sprite_path": "sprites/sprite3_evolved.png" },
        "Venusaur" :
        { "name": "evolved Venusaur",  "hp": 150,  "max_hp": 160, "attack":20,"defense":20,"level": 30,"element": "fire", "win_count" : 0,"sprite_path": "sprites/sprite4_evolved.png" },
        "Gengar":
        { "name": "evolved Gengar",    "hp": 130, "max_hp": 140, "attack":30,"defense":30,"level": 28,"element": "fire", "win_count" : 0,"sprite_path": "sprites/sprite5_evolved.png" },
        "Dragonite":
        { "name": "evolved Dragonite", "hp": 200, "max_hp": 220, "attack":80,"defense":80,"level": 40, "element": "water","win_count" : 0,"sprite_path": "sprites/sprite6_evolved.png" }
            }
        monster_collection = []
        for monster in self.game_manager.bag._monsters_data:
            print(monster)
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
        print(monster_collection)
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
            



                


            
            
        