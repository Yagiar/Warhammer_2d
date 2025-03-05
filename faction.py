import pygame
from unit import Unit

class Faction:
    def __init__(self, name):
        self.name = name
        self.units = pygame.sprite.Group()
        self.available_unit_types = {
            "warrior": {
                "attack": (15, 25),
                "defense": (10, 15),
                "cost": 100
            },
            "archer": {
                "attack": (20, 30),
                "defense": (5, 10),
                "cost": 150
            },
            "knight": {
                "attack": (25, 35),
                "defense": (15, 20),
                "cost": 200
            }
        }
        self.resources = 1000  # Starting resources
        
    def can_afford(self, unit_type):
        return self.resources >= self.available_unit_types[unit_type]["cost"]
        
    def add_unit(self, x, y, unit_type):
        if self.can_afford(unit_type):
            unit = Unit(x, y, self.name, unit_type)
            self.units.add(unit)
            self.resources -= self.available_unit_types[unit_type]["cost"]
            return unit
        return None
        
    def remove_unit(self, unit):
        self.units.remove(unit)
        
    def reset_all_units(self):
        for unit in self.units:
            unit.reset_turn()
            
    def has_units(self):
        return len(self.units) > 0 