#
#       pyBlocks, a simple blocks game written with python and pygame.
#
#       Licensed under GPLv3
#       Contact author at pyblocks@gmail.com
#
#       Project pyblocks at sourceforge.net
#       Project pyblocks at pygame.org
#
#       The "Default" tile graphics had a base that I didn't create myself, but I worked them enough in GIMP 
#       that I doubt the originals could still be recognized from them. I have no idea whatsoever if they were free to use.
#       The "Shiny" tileset graphics I created from scratch.
#       The "Animals" and "Doom" tilesets use graphics from some website that I found by searching for "free animal icons" 
#       and claimed they are free to use in non-profit works. You can guess if I hold the copyright to Doom IP or not, but
#       I'd venture that this qualifies as fair use.
#       Fontin Sans is a free font found on some page that was indexed by Google, by searching for its name.
#
#       Known bugs:
#               Some visual problems with the floating texts.
#
#       New in alpha-5:
#               Renamed tilesets to Stringname_t0 to Stringname_t6 to avoid some of the messiness involved.
#               The collapse and scoring routines have been reworked, now the combo favoring really starts to show. I don't like
#                       how you can destroy 5-6 blocks at once and they'll be reverted to 3 and 4 block collapses for the scoring,
#                       but at least it works. More enhancing is on the way for this one later.
#               Score texts float up from their collapse positions now. There are some problems with it, but they're of the visual
#                       sort and they'll get fixed as a side-product as the animation system progresses. Easiest way to see the
#                       flaws in action is to remove an x-shaped or cross-shaped pile of blocks at once, and the floating texts
#                       will be piled so that only the top one remains visible. Or just erase a vertical shape from the rightmost
#                       or leftmost column.
#               A new panic text to have some kind of idea how fast the blocks are moving.
#
#       Planned features:
#               A small time window to work with the tile even after it has touched down.
#               Two player game, cooperative and deathmatch. Possibly through an Internet connection,
#                       but the relevant libraries are still completely unfamiliar to me.
#               In-game musics and sound effects are underway.
#               Explosion animations for removed blocks and animated effects for scores.
#               A high scores list, once the scoring is more or less settled.
#               Transparency support for tiles.
#
#       Fifth released alpha version, April 17th, 2010
#

import pygame, random, os, sys, copy
from pygame.locals import *
from vector2 import Vector2
from imgload import load_image
from textclasses import *

block_size = 32
TIMER = 26
block_speed = 75.
textcolor = (50, 100, 200)
textsize = 20

font1 = "Fontin_Sans_SC_45b.otf"
font2 = "slkscr.ttf"

font2_color = (50, 100, 200)
font2_speed = 75.
font2_timer = 1
font2_size = 25

random.seed()
pygame.init()
screen = pygame.display.set_mode((800,600), 0, 32)
pygame.display.set_caption("PyBlocks alpha-5")
clock = pygame.time.Clock()
pygame.time.set_timer(TIMER, 5000)

background = pygame.Surface(screen.get_size())
background = background.convert()
background.fill((0,0,0))

class Dummy:
    pass

Leveldata = Dummy()
Leveldata.level = block_speed-74

class Player_Entity:
    def __init__(self):
        self.score = 0

Plr = Player_Entity()

Texts_strings = ["<- -> Move block", "LSHIFT, LCTRL: Rotate block", "Down arrow: Accelerate", "Up arrow: Rotate block", "P: Pause/unpause game", "+/- : Select tileset", "ESC: Quit"]
Texts = [Simpletext((500, 50+i*(textsize+2)), text, textcolor, textsize, font1) for i, text in enumerate(Texts_strings)]
score_text_loc = 50+(len(Texts)+1)*(textsize+2)
Texts.append(Variabletext((500, score_text_loc), "Score: %d", Plr, textcolor, textsize, font1, "score"))
Texts.append(Variabletext((45, 50), "PANIC: %d", Leveldata, textcolor, textsize, font1, "level"))

score_text_loc += textsize+2

class Block_images:
    def __init__(self):
        self.data = {}
        self.current_set_num = 0
        load_on_startup = ""
        
        try:
            f = open("blocks.cfg", 'r')
            for line in f:
                if line.startswith('#'):
                    continue

                line = line.rstrip().lstrip()
                
                if line.startswith('Tilesets:'):
                    self.keys = line[9:].lstrip().split('; ')
                elif line.startswith('Load on startup:'):
                    load_on_startup = line[16:].lstrip()
                    
            f.close()
            if not self.keys:
                print "Error in configuration file blocks.cfg", 
            else:
                for index, item in enumerate(self.keys[:]):
                    data = item.split(':')
                    data[1] = int(data[1])
                    self.keys[index] = tuple(data)
                    
        except IOError:
            print "Configuration file blocks.cfg missing.",
        
        if not self.keys:
            print "Reverting to default blockset."
            self.keys = [("Default", 32)]
        
        if load_on_startup:    
            for index, (name, size) in enumerate(self.keys):
                if load_on_startup == name:
                    self.current_set_num = self.keys.index((name, size))
                    self.current_set = self.keys[self.current_set_num][0]
                    
        self.load_sets()
        
    def next_tileset(self, dir):
        self.current_set_num += dir
        if self.current_set_num < 0:
            self.current_set_num = len(self.keys)-1
        elif self.current_set_num == len(self.keys):
            self.current_set_num = 0
        
        self.current_set = self.keys[self.current_set_num][0]
        return self.keys[self.current_set_num][1]
        
    def load_sets(self):
        extensions = ['.png', '.jpg', '.gif']

        for (name, size) in self.keys:
            print "Loading tileset:", name
            self.data[name] = []
            
            for i in range(0,7):
                for ext in extensions:
                    file = name + "_" + "t" + str(i) + ext
                    if os.path.isfile(os.path.join('images', file)):
                        self.data[name].append(load_image(file))
                        break
                else:
                    if size == block_size:
                        print "Using default tile for color number", i
                        self.data[name].append(load_image("Default" + "_" + "t" + str(i) + ".png"))
                    else:
                        print "Cannot replace block size:", size, "with a default block size: 32"
                        print "Press enter to quit."
                        raw_input()
                        exit()
                    
    
class Block(pygame.sprite.Sprite):
    def __init__(self, images, area, speed, active=False):
        pygame.sprite.Sprite.__init__(self)
        
        self.images = images
        self.active = active
        self.sprite = pygame.Surface((block_size, block_size*3), 0, 8)
        self.rect = self.sprite.get_rect()
        
        self.colors = [random.randint(1, 6),random.randint(1, 6),random.randint(1, 6)]
        #self.colors = [1,1,2]
        self.update_sprite()
        
        self.locations = [block_size * x + 200 for x in range(0,6)]
        self.xpos = 2
        
        self.pos = Vector2((self.locations[self.xpos], block_size))
        self.dir = Vector2((0,1))
                
        self.speed = speed
        self.speedup = False
        
        self.area = area
        self.target = Vector2(self.pos.x, self.area.get_bottom(self.xpos))
        
        self.terminate = False
        
    def reset_pos(self):
        self.xpos = 2
        self.pos = Vector2((self.locations[self.xpos], -block_size))
        self.dir = Vector2((0,1))
        self.target = Vector2(self.pos.x, self.area.get_bottom(self.xpos))
        
    def update_sprite(self):
        for offset, color in enumerate(self.colors):
            img, rect = self.images.data[self.images.current_set][color]
            self.sprite.blit(img, (0, offset*block_size))
            
    def rotate(self, dir):
        if dir == 'LSHIFT':
            temp = self.colors.pop(0)
            self.colors.append(temp)
        elif dir == 'LCTRL':
            temp = self.colors.pop()
            self.colors.insert(0,temp)
            
        self.update_sprite()
        
    def update(self, screen, time):
        
        if self.active:
            if self.speed > 0:
                dest_vec = self.target - self.pos
                dest_dist = dest_vec.get_length()
                travel_dist = min(dest_dist, time * (self.speed + self.speedup * 250))
                
                if travel_dist < 0.5:
                    self.pos = self.target
                    self.speed = 0
                    self.terminate = True
                else:
                    self.pos += self.dir * travel_dist
                    
            self.rect.topleft = self.pos
            self.speedup = False
            
            draw_pos = (self.pos.x, self.pos.y-2*block_size)
            screen.blit(self.sprite, draw_pos)
        else:
            screen.blit(self.sprite, (400, 50))
        
    
    def move(self, dir):
        if block.terminate:
            return
        
        x,y = self.pos
        
        if dir == 1:
            if self.xpos > 0:
                a,b = area.find_loc((self.locations[self.xpos-1], self.pos.y))
                if area.data[b][a] == 0:
                    self.xpos -= 1
            else:
                return
            
        elif dir == 2:
            if self.xpos < 5:
                a,b = area.find_loc((self.locations[self.xpos+1], self.pos.y))
                if area.data[b][a] == 0:
                    self.xpos += 1
            else:
                return
        
        self.target = Vector2(self.locations[self.xpos], self.area.get_bottom(self.xpos))
        self.pos = Vector2((self.locations[self.xpos], y))
                
class Playing_area:
    def __init__(self, images, player, score_text_loc):
        
        random.seed()
        self.x_edge, self.y_edge = 6, 18
        self.images = images
        self.offset = 200
        self.collapse_delay_timer = 350
        
        self.image = pygame.Surface((block_size * self.x_edge, block_size * self.y_edge))
        self.paused_image = pygame.Surface((block_size * self.x_edge, block_size * self.y_edge))
        
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.offset,0)
        
        img, dummy = self.images.data[self.images.current_set][0]
        self.data = []
        self.player = player
        self.game_over_flag = False
        
        for i in range(self.y_edge):
            self.data.append([0]*6)
            
            for j in range(self.x_edge):
                self.image.blit(img, (j*block_size, i*block_size))
                self.paused_image.blit(img, (j*block_size, i*block_size))
                
        pauselogo, pause_rect = load_image('paused.png', -1)
        
        self.paused_image.blit(pauselogo, (10,280))
        
        self.data.append([100]*6)
        self.bottom = self.image.get_height() - block_size * 3
        
        self.score_xbase, self.score_ybase = 480, score_text_loc
        self.scoretexts = []
        self.little_scoretexts = []
        
        self.collapse_locations = []
        
        self.reset_scores()
        self.collapse_delay = False
        self.debug_counter = 0
    
    def update_pause_image(self):
        img, dummy = self.images.data[self.images.current_set][0]
        self.paused_image = pygame.Surface((block_size * self.x_edge, block_size * self.y_edge))
        for i in range(self.y_edge):
            for j in range(self.x_edge):
                self.paused_image.blit(img, (j*block_size, i*block_size))
        
        pauselogo, pause_rect = load_image('paused.png', -1)
        self.paused_image.blit(pauselogo, (10,280))
        
    def get_bottom(self, xpos):
        for pos, row in enumerate(self.data):
            if row[xpos] != 0:
                return pos * block_size - 3 * block_size
    
    def update(self, screen, time, clock, paused=False):
        if not paused:
            if not self.collapse_delay:
                screen.blit(self.image,(self.offset,-2*block_size))
            else:
                self.collapse_delay = False
                time_elapsed = 0
                while time_elapsed < self.collapse_delay_timer:
                    time = clock.tick(40)
                    time_elapsed += time
                    screen.blit(self.image,(self.offset,-2*block_size))
                    self.update_texts(screen, time_passed_secs, self.little_scoretexts)
                    pygame.display.update()
                    
            if self.data[2][2] != 0:
                self.game_over()

        else:
            screen.blit(self.paused_image,(self.offset,-2*block_size))
    
    def update_collapsing_blocks(self):
        def random_palette():
            return (random.randint(0,255), random.randint(0,255), random.randint(0,255))
        
        self.destroying_sprite = pygame.sprite.Sprite()
        self.destroying_sprite.set_palette([random_palette()]*255)

    def update_score_texts(self):
        for offset, text in enumerate(self.scoretexts):
            text.y = self.score_ybase+offset*(textsize+2)
    
    def update_texts(self, screen, time, texts):
        if not texts:
            return
        
        for text in texts[:]:
            if not text.timeout:
                text.update(screen, time)
            else:
                texts.remove(text)
                
    def find_loc(self, (_x, _y)):
        _x = int(_x)
        _y = int(_y)
        
        x = (_x - self.offset) / block_size
        y = (_y + 3*block_size) / block_size
        
        return x,y
    
    def blit_loc(self, x, y, color):
        x *= block_size
        y *= block_size
        
        try:
            img, rect = self.images.data[self.images.current_set][color]
        except KeyError:
            print "KeyError in Area.blit_loc()"
            print "Key =", color
            print "x:", x, "y:", y
            print
            print self.data
            exit()
            
        self.image.blit(img, (x,y))
        
    def add_blocks(self, block):
        #self.debug_counter += 1
        #print "Block", self.debug_counter, "landed."
        x,y = self.find_loc(block.pos)
        for i in range(0, 3):
                        
            self.data[y-i-1][x] = block.colors[2-i]
            self.blit_loc(x,y-i-1,block.colors[2-i])
        
        #print self.data
    
    def update_block_grid(self):            
        for row_index, row in enumerate(self.data[:-1]):
            for block_index, block in enumerate(row):
                self.blit_loc(block_index, row_index, block)
                        
    def reset_scores(self):
        self.lastscores = []
        self.combo = 0
        
    def add_block(self, x, y, color):
        self.data[y][x] = color
        
    def remove_block(self, x, y):
        if self.data[y][x] not in [0, 100]:
            self.data[y][x] = 0
    
    def drop_block(self, x, y):
        if self.data[y][x] == 100:
            return
        
        _y = y + 1
        temp = self.data[y][x]
        if self.data[_y][x] == 0:
            self.remove_block(x, y)
            try:
                while self.data[_y+1][x] == 0:
                    _y += 1
            except IndexError:
                print "_y:", _y, "x:", x
                print "y limit:", len(self.data), "x limit:", len(self.data[0])
                exit()
                
            self.add_block(x, _y, temp)
                
    def game_over(self):
        print "GAME OVER! Final score:", self.player.score
        exit()
    
    def check_collapse(self):
        #print "Starting collapse check."
        collapse = False
        self.collapsemap = []
        for i in range(self.y_edge):
            self.collapsemap.append([0]*6)
                            
        for row_index, row in enumerate(self.data):
            if row == [0]*6 or row == [100]*6:
                continue
                        
            for xpos in range(len(row)):
                if row[xpos] != 0:
                    
                    for collapse_dir in [[0,1], [-1,1], [1,1], [1,0]]:
                                                                        
                        currentx = xpos
                        currenty = row_index
                        target = row[xpos]
                        count = 1
                        
                        running = True
                        while running:

                            if len(row) > currentx+collapse_dir[0] and currentx+collapse_dir[0] >= 0 and len(self.data) > currenty+collapse_dir[1] and currenty+collapse_dir[1] >= 0:
                                if self.data[currenty+collapse_dir[1]][currentx+collapse_dir[0]] == target:
                                    count += 1
                                    currentx += collapse_dir[0]
                                    currenty += collapse_dir[1]
                                else:
                                    running = False
                            else:
                                running = False
                                
                        if count >= 3:
                            collapse = True
                            self.collapse_locations.append(((xpos, row_index), collapse_dir, count))
                            #print "Found a collapse at", (xpos, row_index), "dir:", collapse_dir, "len:", count
        
        
        def prune_collapse_list():
            for index1, ((x1,y1), dir1, count1) in enumerate(self.collapse_locations[:]):
                for index2, ((x2,y2), dir2, count2) in enumerate(self.collapse_locations[:]):
                    
                    if ((x1,y1), dir1, count1) == ((x2,y2), dir2, count2):
                        continue
                    
                    _x, _y = x1, y1
                    for i in range(count1):
                        if (_x,_y) == (x2,y2) and dir1 == dir2:
                            if count1 > count2:
                                pos = index2
                            else:
                                pos = index1
                                
                            del self.collapse_locations[pos]
                            return False
                        
                        _x += dir1[0]
                        _y += dir1[1]
            else:
                return True
            
        if len(self.collapse_locations) > 1:
            done = False
            while not done:
                done = prune_collapse_list()
                                    
        return collapse
    
    def do_collapse(self):
        #print "do_collapse()"
        #marked_spots = []
        
        def add_score(count, (x,y)):
            score = int((300 * (count - 2)) * ((self.combo+1) ** 2))
            score = int(round(score / 10.0) * 10)

            self.player.score += score
            self.collapse_delay = True
            
            if self.combo > 0:
                string = str(self.combo+1) + " combo! +" + str(score)
            else:
                string = "          " + "+" + str(score)
                
            x *= block_size
            y *= block_size
            
            y -= 2*block_size
            
            self.lastscores.append(string)            
            self.little_scoretexts.append(Movingtext((x+self.offset,y), score, font2_color, font2_size, font1, Vector2((0,-1)), font2_speed, font2_timer))
        
        from math import floor
        
        for ((x,y), dir, count) in self.collapse_locations:
            center = floor(count/2.0)
            center_x, center_y = x + center*dir[0], y + center*dir[1]
            add_score(count, (center_x, center_y))
                        
            for i in range(count):
                self.remove_block(x, y)
                x += dir[0]
                y += dir[1]

        
        self.collapse_locations = []
        self.combo += 1
        
        for row_index_rev, row in enumerate(reversed(self.data)):
            if row == [100]*6 or row == [0]*6:
                continue
            for block_index, block in enumerate(row):
                if 1 <= block <= 6:
                    if self.data[self.y_edge-row_index_rev+1][block_index] == 0:
                        self.drop_block(block_index, self.y_edge-row_index_rev)

        self.update_block_grid()
        
    def build_score_texts(self):
        if self.lastscores:
            for score in self.lastscores:
                self.scoretexts.append(Vanishingtext((self.score_xbase, self.score_ybase+len(self.scoretexts)*(textsize+2)), score, textcolor, textsize, font1, 3))
                    
NewBlock = Block
images = Block_images()
area = Playing_area(images, Plr, score_text_loc)
block = NewBlock(images, area, block_speed, active=True)
nextblock = NewBlock(images, area, block_speed)
paused = False

while True:
    time_passed = clock.tick(40)
    time_passed_secs = time_passed / 1000.0
        
    
    if not paused:
        x,y = area.find_loc(block.pos)
        if block.terminate:
            area.add_blocks(block)
            area.reset_scores()
            while area.check_collapse():
                area.do_collapse()
                time_passed = clock.tick(40)
                time_passed_secs = time_passed / 1000.0
                area.update(screen, time_passed_secs, clock)
                
            area.build_score_texts()
            block = copy.copy(nextblock)
            block.active = True
            block.reset_pos()
            
            nextblock = NewBlock(images, area, block_speed)
        
        screen.blit(background,(0,0))
        area.update(screen, time_passed_secs, clock)
        block.update(screen, time_passed_secs)
        nextblock.update(screen, time_passed_secs)
        for text in Texts:
            text.update(screen)
        
        for texts in [area.scoretexts, area.little_scoretexts]:
            area.update_texts(screen, time_passed_secs, texts)
        
        keys = pygame.key.get_pressed()
        if keys:
            if keys[K_DOWN]:
                block.speedup = True
    else:
        screen.blit(background,(0,0))
        for text in Texts:
            text.update(screen)
        area.update(screen, time_passed_secs, clock, paused=True)
    
    pygame.display.update()
        
    for event in pygame.event.get():
        if not paused:
            if event.type == QUIT:
                exit()
            elif event.type == TIMER:
                block_speed += 1
                Leveldata.level = block_speed-74
        if event.type == KEYDOWN:
            if event.key == K_p:
                paused = not paused
            elif event.key == K_ESCAPE:
                exit()

            if not paused:
                if event.key == K_LCTRL:
                    block.rotate('LCTRL')
                elif event.key == K_LSHIFT or event.key == K_UP:
                    block.rotate('LSHIFT')
                elif event.key == K_LEFT:
                    block.move(1)
                elif event.key == K_RIGHT:
                    block.move(2)
                elif event.key == K_PLUS or event.key == K_MINUS:
                    block_size = images.next_tileset([-1,1][event.key == K_KP_PLUS])
                    block.update_sprite()
                    nextblock.update_sprite()
                    area.update_block_grid()
                    area.update_pause_image()
                #else:
                    #print "Unknown keyboard event key:", event.key