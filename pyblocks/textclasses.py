# Helper classes created by the author of pyblocks, licensed under GPLv3

import pygame
from pygame.locals import *
from vector2 import Vector2

class Text(pygame.sprite.Sprite, object):
    def __init__(self, coords, color, size, font):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(font, size)
        self.x, self.y = coords
        self.color = color

        self.image = self.font.render(self.as_string(), 1, self.color)
        self.rect = self.image.get_rect()
        self.rect.topleft = (self.x,self.y)

    def update(self, screen):
        screen.blit(self.image, self.rect)
        
    def as_string(self):
        return str(self.phrase)
    
class Variabletext(Text):
    def __init__(self, coords, string, item, color, size, font, *args):
        self.string = string
        self.item = item
        self.variables = ["self.item." + variable for variable in args]
        Text.__init__(self, coords, color, size, font)
        
    def as_string(self):
        return self.string % (tuple(map(eval, self.variables)))
    
    def update(self, screen):
        self.image = self.font.render(self.as_string(), 1, self.color)
        screen.blit(self.image, self.rect)

class Simpletext(Text):
    def __init__(self, coords, phrase, color, size, font):
        self.phrase = phrase    
        Text.__init__(self, coords, color, size, font)

class Vanishingtext(Text):
    def __init__(self, coords, phrase, color, size, font, time):
        self.phrase = phrase    
        self.visible_time = time
        self.elapsed_time = 0
        self.timeout = False
        Text.__init__(self, coords, color, size, font)
        
    def update(self, screen, time):
        self.elapsed_time += time
        if self.elapsed_time < self.visible_time:
            self.image = self.font.render(self.as_string(), 1, self.color)
            self.rect = self.image.get_rect()
            self.rect.topleft = (self.x,self.y)
            screen.blit(self.image, self.rect)
        else:
            self.timeout = True

class Movingtext(pygame.sprite.Sprite, object):
    def __init__(self, coords, phrase, color, size, font, heading, speed, time):
        pygame.sprite.Sprite.__init__(self)
        self.font = pygame.font.Font(font, size)
        
        self.color = color
        self.phrase = str(phrase)
        self.heading = heading
        self.speed = speed
        self.pos = Vector2(coords)
        
        #self.dropshadow = self.font.render(self.phrase, 1, (1,1,1))
        self.text = self.font.render(self.phrase, 1, self.color)
        
        self.image = pygame.surface.Surface(self.text.get_size())
        self.rect = self.image.get_rect()
        
        colorkey = self.image.get_at((0,0))
        self.image.set_colorkey(colorkey, RLEACCEL)
        
        #self.image.blit(self.dropshadow, (3,3))
        self.image.blit(self.text, (0,0))

        self.elapsed_time = 0
        
        if time != -1:
            self.visible_time = time
            self.timeout = False
            self.usetimer = True
        else:
            self.visible_time = 1
            self.usetimer = False
            
    def update(self, screen, time=0):
        if self.usetimer:
            self.elapsed_time += time
            
        if self.elapsed_time < self.visible_time:
            
            self.pos += self.heading * self.speed * time
            self.rect.topleft = self.pos.as_tuple()
            screen.blit(self.image, self.rect)
            
        else:
            self.timeout = True
            