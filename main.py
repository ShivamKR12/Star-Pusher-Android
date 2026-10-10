# main.py

"""
IMPROVEMENTS TO BE MADE: 

1. [FIXED] Sometimes, the game is crashing on screen orientation change. Debug and find the reason for the random, inconsistent and existing Bug/Issue.
2. [FIXED] When converting the game to an .apk, upon changing the orientation of the screen, the game resetting back to the main menu/screen. It is also sometimes just straight up crashing, which needs to be looked into as well !
3. [FIXED] Add a button on main menu/screen to Quit/Close the game.
"""

import random
import sys
import copy
import os
import json
import pygame
from pygame.locals import *

# Constants
FPS = 30
TILEWIDTH = 50
TILEHEIGHT = 85
TILEFLOORHEIGHT = 40
OUTSIDE_DECORATION_PCT = 20

BRIGHTBLUE = (0, 170, 255)
WHITE = (255, 255, 255)
GRAY = (100, 100, 100)
DARK_GRAY = (50, 50, 50)
BGCOLOR = BRIGHTBLUE
TEXTCOLOR = WHITE

UP = 'up'
DOWN = 'down'
LEFT = 'left'
RIGHT = 'right'

def resource_path(relative_path):
    """Get absolute path to resource."""
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, "assets", relative_path)

def get_save_path():
    """Returns a safe, writable path for saving data across desktop and mobile environments."""
    save_dir = os.path.join(os.path.expanduser("~"), ".starpusher")
    if not os.path.exists(save_dir):
        try:
            os.makedirs(save_dir)
        except OSError:
            save_dir = "." 
    return os.path.join(save_dir, "savegame.json")

class Game:
    def __init__(self):
        pygame.init()
        self.clock = pygame.time.Clock()
        
        self.screen = pygame.display.set_mode((800, 600), pygame.RESIZABLE | pygame.FULLSCREEN)
        self.width, self.height = self.screen.get_size()
            
        # Increased font scaling for better readability
        self.font = pygame.font.Font(None, 34)
        self.large_font = pygame.font.Font(None, 56)  
        self.load_assets()
        
        self.levels = self.read_levels_file(resource_path('starPusherLevels.txt'))
        self.current_level_index = 0
        
        # State tracking
        self.state = 'START_SCREEN'
        self.menu_open = False
        
        # Touch controls tracking state
        self.swipe_threshold = 0.05  
        self.finger_start_pos = None  
        self.finger_id = None
        self.ignore_swipe = False  
        self.swipe_enabled = True 
        
        # Virtual UI Buttons mapping state
        self.ui_buttons = {}
        self.dir_buttons = {}
        
        self.load_progress()

    def load_assets(self):
        def safe_load(path, size=(TILEWIDTH, TILEHEIGHT), color=(200, 200, 200)):
            try:
                return pygame.image.load(resource_path(path)).convert_alpha()
            except Exception:
                surf = pygame.Surface(size)
                surf.fill(color)
                return surf

        self.images = {
            'uncovered goal': safe_load('RedSelector.png', color=(255, 0, 0)),
            'covered goal': safe_load('Selector.png', color=(0, 255, 0)),
            'star': safe_load('Star.png', color=(255, 255, 0)),
            'corner': safe_load('Wall_Block_Tall.png', color=(139, 69, 19)),
            'wall': safe_load('Wood_Block_Tall.png', color=(205, 133, 63)),
            'inside floor': safe_load('Plain_Block.png', color=(220, 220, 220)),
            'outside floor': safe_load('Grass_Block.png', color=(34, 139, 34)),
            'title': safe_load('star_title.png', (300, 150), (0, 170, 255)),
            'solved': safe_load('star_solved.png', (200, 100), (0, 0, 0)),
            'princess': safe_load('princess.png', color=(255, 192, 203)),
            'boy': safe_load('boy.png', color=(30, 144, 255)),
            'catgirl': safe_load('catgirl.png', color=(218, 112, 214)),
            'horngirl': safe_load('horngirl.png', color=(255, 69, 0)),
            'pinkgirl': safe_load('pinkgirl.png', color=(255, 105, 180)),
            'rock': safe_load('Rock.png', color=(128, 128, 128)),
            'short tree': safe_load('Tree_Short.png', color=(0, 100, 0)),
            'tall tree': safe_load('Tree_Tall.png', color=(0, 128, 0)),
            'ugly tree': safe_load('Tree_Ugly.png', color=(85, 107, 47))
        }

        self.tile_mapping = {
            'x': self.images['corner'],
            '#': self.images['wall'],
            'o': self.images['inside floor'],
            ' ': self.images['outside floor']
        }
        self.outside_deco_mapping = {
            '1': self.images['rock'],
            '2': self.images['short tree'],
            '3': self.images['tall tree'],
            '4': self.images['ugly tree']
        }

        self.player_images = [
            self.images['princess'], self.images['boy'], 
            self.images['catgirl'], self.images['horngirl'], self.images['pinkgirl']
        ]
        self.current_image_idx = 0

    def load_progress(self):
        save_path = get_save_path()
        try:
            if os.path.exists(save_path):
                with open(save_path, 'r') as f:
                    data = json.load(f)
                
                self.current_level_index = data.get('level_index', 0)
                self.current_image_idx = data.get('char_index', 0)
                self.swipe_enabled = data.get('swipe_enabled', True)
                
                saved_game_state = data.get('game_state', None)
                self.load_level(saved_game_state)
            else:
                self.load_level()
        except Exception:
            self.load_level()

    def save_progress(self):
        save_path = get_save_path()
        data = {
            'level_index': self.current_level_index,
            'char_index': self.current_image_idx,
            'swipe_enabled': self.swipe_enabled,
            'game_state': self.game_state
        }
        try:
            with open(save_path, 'w') as f:
                json.dump(data, f)
        except Exception as e:
            print(f"Error saving progress: {e}")

    def load_level(self, saved_state=None):
        self.level_obj = self.levels[self.current_level_index]
        self.map_obj = self.decorate_map(self.level_obj['mapObj'], self.level_obj['startState']['player'])
        
        if saved_state:
            self.game_state = saved_state
            self.game_state['player'] = tuple(self.game_state['player'])
            self.game_state['stars'] = [tuple(s) for s in self.game_state['stars']]
        else:
            self.game_state = copy.deepcopy(self.level_obj['startState'])
            
        self.map_needs_redraw = True
        self.menu_open = False

    def run(self):
        while True:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_AC_BACK):
                self.terminate()
                
            elif event.type == VIDEORESIZE:
                self.width, self.height = event.w, event.h
                self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                self.map_needs_redraw = True

            elif event.type == FINGERDOWN:
                if self.finger_id is None:
                    self.finger_id = event.finger_id
                    self.finger_start_pos = (event.x, event.y)
                    self.ignore_swipe = False
                
                px_x = int(event.x * self.width)
                px_y = int(event.y * self.height)
                
                if self.check_ui_clicks((px_x, px_y)):
                    self.ignore_swipe = True
                    return

                if self.state == 'START_SCREEN':
                    self.state = 'PLAYING'
                    return

                if self.state == 'LEVEL_COMPLETE':
                    self.advance_level('solved')
                    self.state = 'PLAYING'
                    return

            elif event.type == FINGERMOTION:
                if self.swipe_enabled and self.state == 'PLAYING' and not self.ignore_swipe and not self.menu_open:
                    if self.finger_id == event.finger_id and self.finger_start_pos:
                        start_x, start_y = self.finger_start_pos
                        dx = event.x - start_x
                        dy = event.y - start_y
                        
                        if abs(dx) > self.swipe_threshold or abs(dy) > self.swipe_threshold:
                            if abs(dx) > abs(dy):
                                direction = RIGHT if dx > 0 else LEFT
                            else:
                                direction = DOWN if dy > 0 else UP
                                
                            self.move_player(direction)
                            self.finger_start_pos = (event.x, event.y)

            elif event.type == FINGERUP:
                if self.finger_id == event.finger_id:
                    self.finger_id = None
                    self.finger_start_pos = None
                    self.ignore_swipe = False

    def check_ui_clicks(self, pos):
        for label, rect in self.ui_buttons.items():
            if rect.collidepoint(pos):
                if label == "MENU": 
                    self.menu_open = not self.menu_open
                elif label == "RESET": 
                    self.load_level()
                    self.save_progress()
                elif label == "PREV": 
                    self.advance_level('back')
                elif label == "NEXT": 
                    self.advance_level('next')
                elif label == "QUIT": 
                    self.terminate()
                elif label in ("SWIPE ON", "SWIPE OFF"):
                    self.swipe_enabled = not self.swipe_enabled
                    self.save_progress()
                elif label == "CHANGE CHAR":
                    self.current_image_idx = (self.current_image_idx + 1) % len(self.player_images)
                    self.map_needs_redraw = True
                    self.save_progress()
                return True
                
        if not self.menu_open:
            for label, rect in self.dir_buttons.items():
                if rect.collidepoint(pos):
                    if label == '^': self.move_player(UP)
                    elif label == 'v': self.move_player(DOWN)
                    elif label == '<': self.move_player(LEFT)
                    elif label == '>': self.move_player(RIGHT)
                    return True
                
        return False

    def move_player(self, direction):
        player_x, player_y = self.game_state['player']
        stars = self.game_state['stars']

        x_offset, y_offset = 0, 0
        if direction == UP:    y_offset = -1
        elif direction == DOWN:  y_offset = 1
        elif direction == LEFT:  x_offset = -1
        elif direction == RIGHT: x_offset = 1

        if self.is_wall(player_x + x_offset, player_y + y_offset):
            return

        if (player_x + x_offset, player_y + y_offset) in stars:
            next_star_x = player_x + (x_offset * 2)
            next_star_y = player_y + (y_offset * 2)
            if not self.is_blocked(next_star_x, next_star_y):
                idx = stars.index((player_x + x_offset, player_y + y_offset))
                stars[idx] = (next_star_x, next_star_y)
            else:
                return

        self.game_state['player'] = (player_x + x_offset, player_y + y_offset)
        self.game_state['stepCounter'] += 1
        self.map_needs_redraw = True
        
        self.save_progress()

    def update(self):
        if self.state == 'PLAYING' and self.is_level_finished():
            self.state = 'LEVEL_COMPLETE'

    def draw(self):
        self.screen.fill(BGCOLOR)
        self.ui_buttons.clear()
        self.dir_buttons.clear()

        if self.state == 'START_SCREEN':
            # 1. Pushed title image substantially higher
            title_rect = self.images['title'].get_rect()
            title_rect.center = (self.width // 2, self.height // 2 - 260)
            self.screen.blit(self.images['title'], title_rect)
    
            # 2. Scaled up Character Showcase and moved lower
            orig_char = self.player_images[self.current_image_idx]
            char_img = pygame.transform.scale(orig_char, (orig_char.get_width() * 2, orig_char.get_height() * 2))
            char_rect = char_img.get_rect(center=(self.width // 2, self.height // 2 + 10))
            self.screen.blit(char_img, char_rect)
            
            # 3. Scaled up Change Character Button and dropped below the character image
            self.draw_btn('CHANGE CHAR', self.width // 2, self.height // 2 + 150, 220, 70, self.ui_buttons, self.font)

            # 4. Quit button
            self.draw_btn('QUIT', self.width // 2, self.height // 2 + 230, 220, 70, self.ui_buttons, self.font)

            instruct_surf = self.large_font.render("Tap anywhere else to start playing!", True, WHITE)
            instruct_rect = instruct_surf.get_rect(center=(self.width // 2, self.height - 60))
            self.screen.blit(instruct_surf, instruct_rect)
    
            pygame.display.update()
            return

        if self.map_needs_redraw or not hasattr(self, 'map_surf'):
            self.map_surf = self.render_map_surface()
            self.map_needs_redraw = False

        is_portrait = self.height > self.width

        if is_portrait:
            avail_w = self.width
            avail_h = int(self.height * 0.52) 
            map_center = (self.width // 2, int(self.height * 0.35))
        else:
            avail_w = int(self.width * 0.52)   
            avail_h = self.height - 40         
            map_center = (self.width // 2, self.height // 2)
        
        map_w, map_h = self.map_surf.get_size()
        scale = min(avail_w / map_w, avail_h / map_h)
        
        new_w = int(map_w * scale)
        new_h = int(map_h * scale)
        
        scaled_map = pygame.transform.smoothscale(self.map_surf, (new_w, new_h))
        map_rect = scaled_map.get_rect()
        map_rect.center = map_center
        self.screen.blit(scaled_map, map_rect)

        self.draw_ui(is_portrait)

        if self.state == 'LEVEL_COMPLETE':
            solved_rect = self.images['solved'].get_rect()
            solved_rect.center = map_center
            self.screen.blit(self.images['solved'], solved_rect)
            
            hint_surf = self.font.render("Tap screen to continue", True, WHITE)
            hint_rect = hint_surf.get_rect(center=(map_center[0], map_center[1] + (solved_rect.height // 2) + 20))
            self.screen.blit(hint_surf, hint_rect)

        pygame.display.update()

    def draw_btn(self, label, cx, cy, w, h, target_dict, font):
        rect = pygame.Rect(0, 0, w, h)
        rect.center = (cx, cy)
        target_dict[label] = rect

        surf = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(surf, (30, 30, 30, 190), surf.get_rect(), border_radius=12)
        pygame.draw.rect(surf, (100, 100, 100, 190), surf.get_rect().inflate(-4, -4), border_radius=10)

        lbl_surf = font.render(label, True, WHITE)
        lbl_rect = lbl_surf.get_rect(center=(w//2, h//2))
        surf.blit(lbl_surf, lbl_rect)
        self.screen.blit(surf, rect.topleft)

    def draw_ui(self, is_portrait):
        # 1. Scaled and Shifted Top Bar Information
        hud_str = f"Level {self.current_level_index + 1}/{len(self.levels)} \n  Steps: {self.game_state['stepCounter']}"
        hud_surf = self.large_font.render(hud_str, True, WHITE)
        # Shifted sufficiently right and down to avoid corner hardware
        self.screen.blit(hud_surf, (240, 60))

        # 2. Scaled and Shifted MENU Button
        btn_w, btn_h = 180, 100
        menu_x = 110  # Pushed right
        menu_y = 100  # Pushed down
        self.draw_btn('MENU', menu_x, menu_y, btn_w, btn_h, self.ui_buttons, self.font)

        # 3. Scaled Dropdown Menu Items
        if self.menu_open:
            dd_w, dd_h = 190, 85
            options = ['RESET', 'PREV', 'NEXT', "SWIPE ON" if self.swipe_enabled else "SWIPE OFF", 'QUIT']
            
            for i, option in enumerate(options):
                opt_y = menu_y + btn_h + 20 + (i * (dd_h + 30))
                self.draw_btn(option, menu_x + 90, opt_y, dd_w, dd_h, self.ui_buttons, self.font)
                
        # 4. Directional D-Pad 
        if is_portrait:
            dpad_size = 140
            dpad_space = 155
            bottom_cy = self.height * 0.76
            dpad_cx = self.width * 0.5
            
            self.draw_btn('^', dpad_cx, bottom_cy - dpad_space, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('v', dpad_cx, bottom_cy + dpad_space, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('<', dpad_cx - dpad_space, bottom_cy, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('>', dpad_cx + dpad_space, bottom_cy, dpad_size, dpad_size, self.dir_buttons, self.large_font)
        else:
            dpad_size = 125
            dpad_space = 130
            dpad_cx = self.width * 0.85
            dpad_cy = self.height // 2
            
            self.draw_btn('^', dpad_cx, dpad_cy - dpad_space, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('v', dpad_cx, dpad_cy + dpad_space, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('<', dpad_cx - dpad_space, dpad_cy, dpad_size, dpad_size, self.dir_buttons, self.large_font)
            self.draw_btn('>', dpad_cx + dpad_space, dpad_cy, dpad_size, dpad_size, self.dir_buttons, self.large_font)

    def render_map_surface(self):
        map_surf_w = len(self.map_obj) * TILEWIDTH
        map_surf_h = (len(self.map_obj[0]) - 1) * TILEFLOORHEIGHT + TILEHEIGHT
        surf = pygame.Surface((map_surf_w, map_surf_h))
        surf.fill(BGCOLOR)

        for x in range(len(self.map_obj)):
            for y in range(len(self.map_obj[x])):
                rect = pygame.Rect((x * TILEWIDTH, y * TILEFLOORHEIGHT, TILEWIDTH, TILEHEIGHT))
                base_tile = self.tile_mapping.get(self.map_obj[x][y], self.tile_mapping[' '])
                
                if self.map_obj[x][y] in self.outside_deco_mapping:
                    base_tile = self.tile_mapping[' ']

                surf.blit(base_tile, rect)

                if self.map_obj[x][y] in self.outside_deco_mapping:
                    surf.blit(self.outside_deco_mapping[self.map_obj[x][y]], rect)
                elif (x, y) in self.game_state['stars']:
                    if (x, y) in self.level_obj['goals']:
                        surf.blit(self.images['covered goal'], rect)
                    surf.blit(self.images['star'], rect)
                elif (x, y) in self.level_obj['goals']:
                    surf.blit(self.images['uncovered goal'], rect)

                if (x, y) == self.game_state['player']:
                    surf.blit(self.player_images[self.current_image_idx], rect)
        return surf

    def advance_level(self, outcome):
        if outcome in ('solved', 'next'):
            self.current_level_index = (self.current_level_index + 1) % len(self.levels)
        elif outcome == 'back':
            self.current_level_index = (self.current_level_index - 1) % len(self.levels)
        self.load_level()
        self.save_progress()

    def is_wall(self, x, y, map_obj=None):
        if map_obj is None:
            map_obj = self.map_obj
        if x < 0 or x >= len(map_obj) or y < 0 or y >= len(map_obj[x]):
            return False
        return map_obj[x][y] in ('#', 'x')

    def is_blocked(self, x, y):
        if self.is_wall(x, y): return True
        if x < 0 or x >= len(self.map_obj) or y < 0 or y >= len(self.map_obj[x]): return True
        if (x, y) in self.game_state['stars']: return True
        return False

    def is_level_finished(self):
        return all(goal in self.game_state['stars'] for goal in self.level_obj['goals'])

    def decorate_map(self, map_obj, start_xy):
        start_x, start_y = start_xy
        map_copy = copy.deepcopy(map_obj)

        for x in range(len(map_copy)):
            for y in range(len(map_copy[0])):
                if map_copy[x][y] in ('$', '.', '@', '+', '*'):
                    map_copy[x][y] = ' '

        self.flood_fill(map_copy, start_x, start_y, ' ', 'o')

        for x in range(len(map_copy)):
            for y in range(len(map_copy[0])):
                if map_copy[x][y] == '#':
                    if (self.is_wall(x, y-1, map_copy) and self.is_wall(x+1, y, map_copy)) or \
                       (self.is_wall(x+1, y, map_copy) and self.is_wall(x, y+1, map_copy)) or \
                       (self.is_wall(x, y+1, map_copy) and self.is_wall(x-1, y, map_copy)) or \
                       (self.is_wall(x-1, y, map_copy) and self.is_wall(x, y-1, map_copy)):
                        map_copy[x][y] = 'x'
                elif map_copy[x][y] == ' ' and random.randint(0, 99) < OUTSIDE_DECORATION_PCT:
                    map_copy[x][y] = random.choice(list(self.outside_deco_mapping.keys()))
        return map_copy

    def flood_fill(self, map_obj, x, y, old_char, new_char):
        stack = [(x, y)]
        while stack:
            cx, cy = stack.pop()
            if map_obj[cx][cy] == old_char:
                map_obj[cx][cy] = new_char
                if cx < len(map_obj) - 1: stack.append((cx + 1, cy))
                if cx > 0: stack.append((cx - 1, cy))
                if cy < len(map_obj[cx]) - 1: stack.append((cx, cy + 1))
                if cy > 0: stack.append((cx, cy - 1))

    def read_levels_file(self, filename):
        if not os.path.exists(filename):
            return [{'width': 5, 'height': 5, 'goals': [(3, 3)], 'mapObj': [['#','#','#','#','#'],['#',' ',' ',' ','#'],['#',' ','@',' ','#'],['#',' ',' ',' ','#'],['#','#','#','#','#']], 'startState': {'player': (2, 2), 'stepCounter': 0, 'stars': [(2, 3)]}}]
        
        with open(filename, 'r') as map_file:
            content = map_file.readlines() + ['\r\n']

        levels = []
        map_text_lines = []
        
        for line in content:
            line = line.rstrip('\r\n')
            if ';' in line:
                line = line[:line.find(';')]

            if line != '':
                map_text_lines.append(line)
            elif line == '' and map_text_lines:
                max_width = max(len(l) for l in map_text_lines)
                for i in range(len(map_text_lines)):
                    map_text_lines[i] += ' ' * (max_width - len(map_text_lines[i]))

                map_obj = [[map_text_lines[y][x] for y in range(len(map_text_lines))] for x in range(max_width)]
                
                start_x, start_y = None, None
                goals, stars = [], []
                
                for x in range(max_width):
                    for y in range(len(map_obj[x])):
                        if map_obj[x][y] in ('@', '+'):
                            start_x, start_y = x, y
                        if map_obj[x][y] in ('.', '+', '*'):
                            goals.append((x, y))
                        if map_obj[x][y] in ('$', '*'):
                            stars.append((x, y))

                game_state_obj = {'player': (start_x, start_y), 'stepCounter': 0, 'stars': stars}
                levels.append({
                    'width': max_width, 'height': len(map_obj),
                    'mapObj': map_obj, 'goals': goals, 'startState': game_state_obj
                })
                map_text_lines = []
        return levels

    def terminate(self):
        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()
