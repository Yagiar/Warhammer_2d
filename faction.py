import pygame
from unit import Unit, Squad
import random

class Faction:
    def __init__(self, name, resources=1000):
        self.name = name
        self.resources = resources
        self.units = []
        self.squads = []
        
        # Стоимость юнитов
        self.unit_costs = {
            "warrior": 100,
            "archer": 150,
            "knight": 200
        }
    
    def create_squad(self, name, unit_type, num_units=1):
        # Проверка ресурсов
        unit_cost = self.unit_costs.get(unit_type, 100)
        total_cost = unit_cost * num_units
        
        if total_cost <= self.resources:
            squad_units = []
            for _ in range(num_units):
                # Случайное размещение
                x = random.randint(0, 600)
                y = random.randint(0, 600)
                unit = Unit(x, y, unit_type, self.name)
                squad_units.append(unit)
                self.units.append(unit)
            
            squad = Squad(name, unit_type, squad_units, self)
            self.squads.append(squad)
            self.resources -= total_cost
            return squad
        return None
    
    def add_unit(self, x, y, unit_type):
        unit_cost = self.unit_costs.get(unit_type, 100)
        
        if unit_cost <= self.resources:
            unit = Unit(x, y, unit_type, self.name)
            self.units.append(unit)
            self.resources -= unit_cost
            return unit
        return None
    
    def remove_unit(self, unit):
        if unit in self.units:
            self.units.remove(unit)
        
        # Удаление юнита из отряда
        for squad in self.squads:
            if unit in squad.units:
                squad.remove_unit(unit)
                # Если отряд пустой, удаляем его
                if not squad.units:
                    self.squads.remove(squad)
    
    def has_units(self):
        return len(self.units) > 0
    
    def reset_turn(self):
        for unit in self.units:
            unit.is_moved = False
            unit.is_attacked = False
        
        for squad in self.squads:
            squad.reset_turn() 