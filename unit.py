import pygame
from pygame.locals import *
import random

class Unit(pygame.sprite.Sprite):
    def __init__(self, x, y, faction, unit_type):
        super().__init__()
        self.image = pygame.Surface((30, 30))
        self.faction = faction
        # Different colors for different factions
        self.color = (255, 0, 0) if faction == "faction1" else (0, 0, 255)
        self.image.fill(self.color)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        
        # Unit characteristics based on type
        self.unit_type = unit_type
        self.health = 100
        
        if unit_type == "warrior":
            self.attack = random.randint(15, 25)
            self.defense = random.randint(10, 15)
            self.movement_range = 4
        elif unit_type == "archer":
            self.attack = random.randint(20, 30)
            self.defense = random.randint(5, 10)
            self.movement_range = 3
            self.attack_range = 4
        else:  # knight
            self.attack = random.randint(25, 35)
            self.defense = random.randint(15, 20)
            self.movement_range = 5
        
        # State flags
        self.selected = False
        self.moved = False
        self.attacked = False
        
    def move(self, target_x, target_y):
        if not self.moved:
            dx = target_x - self.rect.x
            dy = target_y - self.rect.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            if distance <= self.movement_range * 32:  # 32 pixels per tile
                self.rect.x = target_x
                self.rect.y = target_y
                self.moved = True
                return True
        return False
        
    def attack_unit(self, target):
        if not self.attacked and not self.moved:
            # Calculate distance
            dx = target.rect.x - self.rect.x
            dy = target.rect.y - self.rect.y
            distance = (dx ** 2 + dy ** 2) ** 0.5
            
            # Check if target is in range
            attack_range = getattr(self, 'attack_range', 1) * 32
            if distance <= attack_range:
                damage = max(0, self.attack - target.defense)
                target.health -= damage
                self.attacked = True
                return damage
        return 0
        
    def reset_turn(self):
        self.moved = False
        self.attacked = False
        
    def is_alive(self):
        return self.health > 0
        
    def draw(self, surface):
        # Draw unit
        pygame.draw.rect(surface, self.color, self.rect)
        
        # Draw selection highlight
        if self.selected:
            pygame.draw.rect(surface, (255, 255, 0), self.rect, 2)
        
        # Draw health bar
        health_rect = pygame.Rect(self.rect.x, self.rect.y - 5, 30 * (self.health / 100), 3)
        pygame.draw.rect(surface, (0, 255, 0), health_rect)
        
        # Draw unit type indicator
        type_colors = {
            "warrior": (200, 200, 200),
            "archer": (0, 255, 0),
            "knight": (255, 215, 0)
        }
        type_rect = pygame.Rect(self.rect.x + 12, self.rect.y + 12, 6, 6)
        pygame.draw.rect(surface, type_colors[self.unit_type], type_rect) 