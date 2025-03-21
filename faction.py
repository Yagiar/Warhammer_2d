import pygame
from unit import Unit, Squad, SQUAD_DATA
import random
import json

class Faction:
    def __init__(self, name, resources=1000):
        self.name = name
        self.resources = resources
        self.units = []
        self.squads = []
        
        # Загружаем стоимость юнитов из внешнего файла
        self.unit_costs = {}
        for unit_type, data in SQUAD_DATA.items():
            self.unit_costs[unit_type] = data.get('cost', 100)
    
    def create_squad(self, name, unit_type, num_units=1):
        # Проверяем, существует ли такой тип юнита
        if unit_type not in SQUAD_DATA:
            print(f"Ошибка: тип юнита '{unit_type}' не найден в squads.json")
            return None
            
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
        # Проверяем, существует ли такой тип юнита
        if unit_type not in SQUAD_DATA:
            print(f"Ошибка: тип юнита '{unit_type}' не найден в squads.json")
            return None
            
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
            
    def get_available_unit_types(self):
        """Возвращает список доступных типов юнитов с их стоимостью"""
        available_units = []
        for unit_type, cost in self.unit_costs.items():
            if cost <= self.resources:
                unit_data = SQUAD_DATA.get(unit_type, {})
                description = unit_data.get('description', '')
                available_units.append({
                    'type': unit_type,
                    'cost': cost,
                    'description': description
                })
        return available_units 