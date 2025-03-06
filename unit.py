import pygame
from pygame.locals import *
import random

class Unit(pygame.sprite.Sprite):
    def __init__(self, x, y, unit_type, faction):
        super().__init__()
        self.rect = pygame.Rect(x, y, 32, 32)
        self.unit_type = unit_type
        self.faction = faction
        self.selected = False
        self.is_moved = False
        self.is_attacked = False
        
        # Базовые характеристики по типу юнита
        unit_stats = {
            "warrior": {"health": 100, "attack": 20, "defense": 15, "movement_range": 2},
            "archer": {"health": 80, "attack": 15, "defense": 10, "movement_range": 3},
            "knight": {"health": 120, "attack": 25, "defense": 20, "movement_range": 1}
        }
        
        stats = unit_stats.get(unit_type, {})
        self.health = stats.get("health", 100)
        self.attack = stats.get("attack", 20)
        self.defense = stats.get("defense", 15)
        self.movement_range = stats.get("movement_range", 2)
        self.attack_range = 1  # Базовая дальность атаки
        
        # Different colors for different factions
        self.color = (255, 0, 0) if faction == "faction1" else (0, 0, 255)
        self.image = pygame.Surface((30, 30))
        self.image.fill(self.color)
        
    def draw(self, surface):
        # Простая отрисовка юнита
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
        
    def move(self, new_x, new_y):
        # Проверка дистанции перемещения
        dx = abs(new_x - self.rect.x) // 32
        dy = abs(new_y - self.rect.y) // 32
        
        if dx * dx + dy * dy <= self.movement_range * self.movement_range:
            self.rect.x = new_x
            self.rect.y = new_y
            return True
        return False
    
    def attack_unit(self, target):
        # Расчет урона с учетом защиты
        damage = max(0, self.attack - target.defense // 2)
        target.health = max(0, target.health - damage)
        return damage
    
    def is_alive(self):
        return self.health > 0

class Squad:
    def __init__(self, name, unit_type, units, faction):
        self.name = name
        self.unit_type = unit_type
        self.units = units
        self.faction = faction
        self.is_moved = False
        self.is_attacked = False
    
    def add_unit(self, unit):
        if unit.unit_type == self.unit_type:
            self.units.append(unit)
    
    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)
    
    def is_alive(self):
        return any(unit.is_alive() for unit in self.units)
    
    def get_total_health(self):
        return sum(unit.health for unit in self.units)
    
    def get_total_attack(self):
        return sum(unit.attack for unit in self.units)
    
    def get_total_defense(self):
        return sum(unit.defense for unit in self.units)

    def reset_turn(self):
        self.is_moved = False
        self.is_attacked = False
        
    def draw(self, surface):
        for unit in self.units:
            unit.draw(surface) 