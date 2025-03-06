import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QComboBox, QTextEdit)
from PySide6.QtCore import Qt, QTimer
import pygame
from faction import Faction
import random

class GameWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Initialize Pygame surface
        self.width = 600
        self.height = 600
        pygame.init()
        self.surface = pygame.Surface((self.width, self.height))
        self.game_state = GameState(self.surface)
        
        # Set fixed size for game area
        self.setFixedSize(self.width, self.height)
        
    def paintEvent(self, event):
        # Update Pygame surface
        self.game_state.draw()
        
        # Convert Pygame surface to QImage
        image = pygame.image.tostring(self.surface, 'RGB')
        from PySide6.QtGui import QImage, QPainter
        qimage = QImage(image, self.width, self.height, QImage.Format_RGB888)
        
        # Draw the image
        painter = QPainter(self)
        painter.drawImage(0, 0, qimage)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            x = event.position().x()
            y = event.position().y()
            self.game_state.handle_click(x, y)
            self.update()  # Trigger a repaint

class ActionMenu(QWidget):
    def __init__(self, game_widget):
        super().__init__()
        self.game_widget = game_widget
        self.setup_ui()
        self.update_button_states()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Game state info
        state_group = QGroupBox("Game State")
        state_layout = QVBoxLayout()
        self.turn_label = QLabel("Current Turn: Player 1")
        self.state_label = QLabel("State: Setup")
        self.help_label = QLabel("Разместите юнитов в красной зоне,\nзатем нажмите 'Start Game'")
        self.help_label.setStyleSheet("color: #666;")
        self.resources_label = QLabel("Your Resources: 1000")
        self.enemy_resources_label = QLabel("Enemy Resources: 1000")
        self.start_game_btn = QPushButton("Start Game")
        self.start_game_btn.clicked.connect(self.handle_start_game)
        self.start_game_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px; }")
        state_layout.addWidget(self.turn_label)
        state_layout.addWidget(self.state_label)
        state_layout.addWidget(self.help_label)
        state_layout.addWidget(self.resources_label)
        state_layout.addWidget(self.enemy_resources_label)
        state_layout.addWidget(self.start_game_btn)
        state_group.setLayout(state_layout)
        
        # Unit selection
        unit_group = QGroupBox("Unit Selection")
        unit_layout = QVBoxLayout()
        self.unit_combo = QComboBox()
        self.unit_combo.addItems(["Warrior", "Archer", "Knight"])
        unit_layout.addWidget(QLabel("Select Unit Type:"))
        unit_layout.addWidget(self.unit_combo)
        unit_group.setLayout(unit_layout)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        self.move_btn = QPushButton("Move")
        self.attack_btn = QPushButton("Attack")
        self.end_turn_btn = QPushButton("End Turn")
        
        self.move_btn.clicked.connect(self.handle_move)
        self.attack_btn.clicked.connect(self.handle_attack)
        self.end_turn_btn.clicked.connect(self.handle_end_turn)
        
        action_layout.addWidget(self.move_btn)
        action_layout.addWidget(self.attack_btn)
        action_layout.addWidget(self.end_turn_btn)
        action_group.setLayout(action_layout)
        
        # Unit info
        info_group = QGroupBox("Unit Info")
        info_layout = QVBoxLayout()
        self.unit_info_label = QLabel("No unit selected")
        info_layout.addWidget(self.unit_info_label)
        info_group.setLayout(info_layout)
        
        # Action log
        log_group = QGroupBox("Action Log")
        log_layout = QVBoxLayout()
        self.action_log = QTextEdit()
        self.action_log.setReadOnly(True)
        self.action_log.setMaximumHeight(150)
        log_layout.addWidget(self.action_log)
        log_group.setLayout(log_layout)
        
        # Add all groups to main layout
        layout.addWidget(state_group)
        layout.addWidget(unit_group)
        layout.addWidget(action_group)
        layout.addWidget(info_group)
        layout.addWidget(log_group)
        
        self.setLayout(layout)
        self.setFixedWidth(250)
    
    def update_button_states(self):
        game_state = self.game_widget.game_state
        is_setup = game_state.state == "setup"
        is_game_over = game_state.state == "game_over"
        
        # Enable/disable buttons based on game state
        self.move_btn.setEnabled(not is_setup and not is_game_over)
        self.attack_btn.setEnabled(not is_setup and not is_game_over)
        self.end_turn_btn.setEnabled(not is_setup and not is_game_over)
        self.start_game_btn.setEnabled(is_setup)
        self.unit_combo.setEnabled(is_setup)
    
    def handle_move(self):
        self.game_widget.game_state.set_action("move")
        self.game_widget.update()
    
    def handle_attack(self):
        self.game_widget.game_state.set_action("attack")
        self.game_widget.update()
    
    def handle_end_turn(self):
        self.game_widget.game_state.end_turn()
        self.add_to_log("Ход закончен")
        self.game_widget.update()
    
    def handle_start_game(self):
        self.game_widget.game_state.start_game()
        self.start_game_btn.setEnabled(False)
        self.add_to_log("Игра началась!")
        self.game_widget.update()
    
    def add_to_log(self, message):
        self.action_log.append(message)
        self.action_log.verticalScrollBar().setValue(
            self.action_log.verticalScrollBar().maximum()
        )
    
    def update_info(self):
        game_state = self.game_widget.game_state
        
        # Update turn indicator
        current_player = "Player 1" if game_state.current_faction.name == "faction1" else "Bot"
        self.turn_label.setText(f"Current Turn: {current_player}")
        
        # Update help text based on state
        if game_state.state == "setup":
            self.help_label.setText("Разместите юнитов в красной зоне,\nзатем нажмите 'Start Game'")
        elif game_state.state == "player1_turn":
            if not game_state.selected_unit and not game_state.current_action:
                self.help_label.setText("Выберите юнита для действия")
            elif game_state.selected_unit and not game_state.current_action:
                self.help_label.setText("Нажмите 'Move' для перемещения\nили 'Attack' для атаки")
            elif game_state.current_action == "move":
                self.help_label.setText("Кликните куда переместить юнита")
            elif game_state.current_action == "attack":
                self.help_label.setText("Кликните по вражескому юниту для атаки")
        else:
            self.help_label.setText("")
        
        # Update state and resources
        self.state_label.setText(f"State: {game_state.state}")
        self.resources_label.setText(f"Your Resources: {game_state.current_faction.resources}")
        self.enemy_resources_label.setText(f"Enemy Resources: {game_state.other_faction.resources}")
        
        if game_state.selected_unit:
            unit = game_state.selected_unit
            info = f"Type: {unit.unit_type}\n"
            info += f"Health: {unit.health}\n"
            info += f"Attack: {unit.attack}\n"
            info += f"Defense: {unit.defense}"
            self.unit_info_label.setText(info)
        else:
            self.unit_info_label.setText("No unit selected")
        
        # Update button states
        self.update_button_states()

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warhammer 2D")
        
        # Create main widget and layout
        main_widget = QWidget()
        layout = QHBoxLayout()
        
        # Create game widget and action menu
        self.game_widget = GameWidget()
        self.action_menu = ActionMenu(self.game_widget)
        
        # Connect game state with action menu
        self.game_widget.game_state.set_action_menu(self.action_menu)
        
        # Add widgets to layout
        layout.addWidget(self.game_widget)
        layout.addWidget(self.action_menu)
        
        # Set layout for main widget
        main_widget.setLayout(layout)
        self.setCentralWidget(main_widget)
        
        # Setup update timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000 // 60)  # 60 FPS
    
    def update_game(self):
        self.game_widget.update()
        self.action_menu.update_info()

class GameState:
    def __init__(self, surface):
        self.surface = surface
        self.state = "setup"
        self.current_faction = Faction("faction1")
        self.other_faction = Faction("faction2")
        self.selected_unit = None
        self.current_action = None
        self.grid_size = 32
        self.grid = [[None for _ in range(surface.get_width() // self.grid_size)]
                    for _ in range(surface.get_height() // self.grid_size)]
        self.setup_zones = {
            "faction1": (0, self.surface.get_width() // self.grid_size // 3),
            "faction2": (2 * self.surface.get_width() // self.grid_size // 3, 
                        self.surface.get_width() // self.grid_size)
        }
        self.action_menu = None  # Will be set from outside
    
    def set_action_menu(self, menu):
        self.action_menu = menu
    
    def set_action(self, action):
        self.current_action = action
        if action != "move" and action != "attack":
            self.selected_unit = None
    
    def is_valid_setup_position(self, faction, grid_x, grid_y):
        zone = self.setup_zones[faction]
        return (zone[0] <= grid_x < zone[1] and 
                0 <= grid_y < len(self.grid) and 
                self.grid[grid_y][grid_x] is None)
    
    def handle_click(self, x, y):
        grid_x = int(x) // self.grid_size
        grid_y = int(y) // self.grid_size
        
        if not (0 <= grid_x < len(self.grid[0]) and 0 <= grid_y < len(self.grid)):
            return
        
        if self.state == "setup":
            self.handle_setup(grid_x, grid_y)
        elif self.state in ["player1_turn", "player2_turn"]:
            self.handle_turn(grid_x, grid_y)
    
    def handle_setup(self, grid_x, grid_y):
        if self.is_valid_setup_position(self.current_faction.name, grid_x, grid_y):
            # Get selected unit type from UI
            unit_type = self.action_menu.unit_combo.currentText().lower()
            unit = self.current_faction.add_unit(
                grid_x * self.grid_size,
                grid_y * self.grid_size,
                unit_type
            )
            if unit:
                self.grid[grid_y][grid_x] = unit
                if self.action_menu:
                    self.action_menu.add_to_log(f"Размещен {unit_type}")
    
    def handle_turn(self, grid_x, grid_y):
        clicked_unit = self.grid[grid_y][grid_x]
        current_player = "Player 1" if self.current_faction.name == "faction1" else "Bot"
        
        # If no action is selected, select unit
        if not self.current_action:
            if clicked_unit and clicked_unit in self.current_faction.units:
                if self.selected_unit:
                    self.selected_unit.selected = False
                self.selected_unit = clicked_unit
                clicked_unit.selected = True
                if self.action_menu:
                    self.action_menu.add_to_log(f"{current_player} выбрал {clicked_unit.unit_type}")
                    # Update button states based on unit's action flags
                    self.action_menu.move_btn.setEnabled(not clicked_unit.is_moved)
                    self.action_menu.attack_btn.setEnabled(not clicked_unit.is_attacked)
        
        # Handle move action
        elif self.current_action == "move" and self.selected_unit and not self.selected_unit.is_moved:
            if not clicked_unit:  # Moving to empty space
                if self.selected_unit.move(grid_x * self.grid_size, 
                                         grid_y * self.grid_size):
                    old_x = self.selected_unit.rect.x // self.grid_size
                    old_y = self.selected_unit.rect.y // self.grid_size
                    self.grid[old_y][old_x] = None
                    self.grid[grid_y][grid_x] = self.selected_unit
                    if self.action_menu:
                        self.action_menu.add_to_log(f"{current_player} переместил {self.selected_unit.unit_type}")
                    self.current_action = None
                    self.selected_unit.is_moved = True
                    # Update button states
                    self.action_menu.move_btn.setEnabled(False)
        
        # Handle attack action
        elif self.current_action == "attack" and self.selected_unit and not self.selected_unit.is_attacked:
            if clicked_unit and clicked_unit in self.other_faction.units:
                damage = self.selected_unit.attack_unit(clicked_unit)
                if damage > 0:
                    if self.action_menu:
                        self.action_menu.add_to_log(
                            f"{current_player} атаковал {clicked_unit.unit_type} и нанес {damage} урона"
                        )
                    if not clicked_unit.is_alive():
                        self.grid[grid_y][grid_x] = None
                        clicked_unit.faction.remove_unit(clicked_unit)
                        if self.action_menu:
                            self.action_menu.add_to_log(f"{clicked_unit.unit_type} был уничтожен")
                    self.current_action = None
                    self.selected_unit.is_attacked = True
                    # Update button states
                    self.action_menu.attack_btn.setEnabled(False)
    
    def end_turn(self):
        if self.state in ["player1_turn", "player2_turn"]:
            if self.selected_unit:
                self.selected_unit.selected = False
                self.selected_unit = None
            
            self.current_action = None
            self.current_faction, self.other_faction = self.other_faction, self.current_faction
            
            # Reset all action flags for the new current faction's units
            for unit in self.current_faction.units:
                unit.is_moved = False
                unit.is_attacked = False
            
            # Check victory conditions
            if not self.other_faction.has_units():
                self.state = "game_over"
                if self.action_menu:
                    winner = "Player 1" if self.current_faction.name == "faction1" else "Bot"
                    self.action_menu.add_to_log(f"Игра окончена! Победитель: {winner}")
            else:
                self.state = "player2_turn" if self.state == "player1_turn" else "player1_turn"
                if self.action_menu:
                    next_player = "Bot" if self.state == "player2_turn" else "Player 1"
                    self.action_menu.add_to_log(f"Ход перешел к {next_player}")
                    
                # If it's bot's turn, make a move
                if self.state == "player2_turn":
                    self.make_bot_move()
    
    def start_game(self):
        if self.state == "setup":
            # Бросок кубика для Player 1
            p1_roll = random.randint(1, 6)
            
            # Бросок кубика для Player 2 (Bot)
            p2_roll = random.randint(1, 6)
            
            # Логирование результатов броска
            if self.action_menu:
                self.action_menu.add_to_log("🎲 Определение первого хода:")
                self.action_menu.add_to_log(f"Player 1 бросает кубик: {p1_roll}")
                self.action_menu.add_to_log(f"Player 2 (Bot) бросает кубик: {p2_roll}")
            
            # Обработка ничьей - повторный бросок
            while p1_roll == p2_roll:
                if self.action_menu:
                    self.action_menu.add_to_log("🔄 Ничья! Перебрасываем кубики.")
                
                p1_roll = random.randint(1, 6)
                p2_roll = random.randint(1, 6)
                
                if self.action_menu:
                    self.action_menu.add_to_log(f"Player 1 перебрасывает: {p1_roll}")
                    self.action_menu.add_to_log(f"Player 2 (Bot) перебрасывает: {p2_roll}")
            
            # Определение первого хода
            if p1_roll > p2_roll:
                self.state = "player1_turn"
                first_player = "Player 1"
            else:
                self.state = "player2_turn"
                first_player = "Player 2 (Bot)"
            
            # Финальное логирование результата
            if self.action_menu:
                self.action_menu.add_to_log(f"🏁 Первым ходит {first_player}!")
                self.action_menu.add_to_log(f"Результат: Player 1 ({p1_roll}) vs Player 2 ({p2_roll})")
            
            # Стратегическое размещение юнитов бота
            bot_resources = self.other_faction.resources
            unit_costs = {
                "warrior": 100,
                "archer": 150,
                "knight": 200
            }
            
            # Стратегическая композиция отрядов
            desired_composition = [
                ("warrior", 0.4),  # 40% warriors
                ("archer", 0.3),   # 30% archers
                ("knight", 0.3)    # 30% knights
            ]
            
            # Расчет максимального количества юнитов
            total_possible_units = bot_resources // min(unit_costs.values())
            planned_units = []
            
            for unit_type, ratio in desired_composition:
                count = int(total_possible_units * ratio)
                cost = count * unit_costs[unit_type]
                
                while cost > bot_resources:
                    count -= 1
                    cost = count * unit_costs[unit_type]
                
                for _ in range(count):
                    if bot_resources >= unit_costs[unit_type]:
                        planned_units.append(unit_type)
                        bot_resources -= unit_costs[unit_type]
            
            # Размещение юнитов в зоне бота
            zone = self.setup_zones["faction2"]
            zone_width = zone[1] - zone[0]
            zone_height = len(self.grid)
            
            # Стратегические позиции для разных типов юнитов
            positions = {
                "warrior": [(x, y) for x in range(zone[0], zone[0] + 2) 
                          for y in range(zone_height)],  # Передний край
                "archer": [(x, y) for x in range(zone[0] + 2, zone[1]) 
                          for y in range(zone_height)],  # Задний край
                "knight": [(x, y) for x in range(zone[0], zone[1]) 
                          for y in range(zone_height)]   # Гибкое размещение
            }
            
            # Размещение каждого запланированного юнита
            for unit_type in planned_units:
                preferred_positions = positions[unit_type]
                random.shuffle(preferred_positions)  # Рандомизация позиций
                
                for grid_x, grid_y in preferred_positions:
                    if self.is_valid_setup_position("faction2", grid_x, grid_y):
                        unit = self.other_faction.add_unit(
                            grid_x * self.grid_size,
                            grid_y * self.grid_size,
                            unit_type
                        )
                        if unit:
                            self.grid[grid_y][grid_x] = unit
                            if self.action_menu:
                                self.action_menu.add_to_log(f"Bot разместил {unit_type}")
                            break
            
            # Запуск фаз хода
            self.run_turn_phases()
    
    def draw(self):
        # Fill background
        self.surface.fill((0, 0, 0))
        
        # Draw grid
        for x in range(0, self.surface.get_width(), self.grid_size):
            pygame.draw.line(self.surface, (128, 128, 128), (x, 0), 
                           (x, self.surface.get_height()))
        for y in range(0, self.surface.get_height(), self.grid_size):
            pygame.draw.line(self.surface, (128, 128, 128), (0, y), 
                           (self.surface.get_width(), y))
        
        # Draw setup zones
        if self.state == "setup":
            for faction, (start, end) in self.setup_zones.items():
                color = (64, 0, 0) if faction == "faction1" else (0, 0, 64)
                rect = pygame.Rect(start * self.grid_size, 0,
                                 (end - start) * self.grid_size,
                                 self.surface.get_height())
                pygame.draw.rect(self.surface, color, rect)
        
        # Draw movement or attack range if action is selected
        if self.selected_unit:
            if self.current_action == "move" and not self.selected_unit.is_moved:
                self.draw_movement_range()
            elif self.current_action == "attack" and not self.selected_unit.is_attacked:
                self.draw_attack_range()
        
        # Draw units
        for faction in [self.current_faction, self.other_faction]:
            for unit in faction.units:
                # Draw unit background
                bg_color = (200, 0, 0) if faction.name == "faction1" else (0, 0, 200)
                bg_rect = pygame.Rect(unit.rect.x, unit.rect.y, self.grid_size, self.grid_size)
                pygame.draw.rect(self.surface, bg_color, bg_rect)
                
                # Draw unit
                unit.draw(self.surface)
                
                # Draw health bar
                health_width = (self.grid_size - 4) * (unit.health / 100)
                health_rect = pygame.Rect(unit.rect.x + 2, unit.rect.y - 5, 
                                        health_width, 3)
                pygame.draw.rect(self.surface, (0, 255, 0), health_rect)
                
                # Draw action indicators for player units
                if faction.name == "faction1":
                    if unit.is_moved and unit.is_attacked:
                        # Draw red border for units that used all actions
                        pygame.draw.rect(self.surface, (255, 0, 0), unit.rect, 2)
                    elif unit.is_moved:
                        # Draw orange border for units that moved
                        pygame.draw.rect(self.surface, (255, 165, 0), unit.rect, 2)
                    elif unit.is_attacked:
                        # Draw purple border for units that attacked
                        pygame.draw.rect(self.surface, (255, 0, 255), unit.rect, 2)
                
                # Draw selection highlight
                if unit.selected:
                    # Draw yellow corners for selected unit
                    rect = unit.rect
                    corner_length = 8
                    # Top-left corner
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.left, rect.top), 
                                   (rect.left + corner_length, rect.top), 3)
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.left, rect.top), 
                                   (rect.left, rect.top + corner_length), 3)
                    # Top-right corner
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.right, rect.top), 
                                   (rect.right - corner_length, rect.top), 3)
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.right, rect.top), 
                                   (rect.right, rect.top + corner_length), 3)
                    # Bottom-left corner
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.left, rect.bottom), 
                                   (rect.left + corner_length, rect.bottom), 3)
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.left, rect.bottom), 
                                   (rect.left, rect.bottom - corner_length), 3)
                    # Bottom-right corner
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.right, rect.bottom), 
                                   (rect.right - corner_length, rect.bottom), 3)
                    pygame.draw.line(self.surface, (255, 255, 0), (rect.right, rect.bottom), 
                                   (rect.right, rect.bottom - corner_length), 3)

    def draw_movement_range(self):
        if self.selected_unit:
            x = self.selected_unit.rect.x // self.grid_size
            y = self.selected_unit.rect.y // self.grid_size
            range_color = (0, 255, 255, 128)
            
            for dx in range(-self.selected_unit.movement_range, 
                          self.selected_unit.movement_range + 1):
                for dy in range(-self.selected_unit.movement_range, 
                              self.selected_unit.movement_range + 1):
                    if (dx * dx + dy * dy) <= self.selected_unit.movement_range * self.selected_unit.movement_range:
                        new_x = x + dx
                        new_y = y + dy
                        if (0 <= new_x < len(self.grid[0]) and 
                            0 <= new_y < len(self.grid) and 
                            not self.grid[new_y][new_x]):
                            rect = pygame.Rect(new_x * self.grid_size,
                                            new_y * self.grid_size,
                                            self.grid_size, self.grid_size)
                            # Fill with semi-transparent color
                            s = pygame.Surface((self.grid_size, self.grid_size))
                            s.set_alpha(128)
                            s.fill((0, 255, 255))
                            self.surface.blit(s, rect)
                            # Draw border
                            pygame.draw.rect(self.surface, (0, 255, 255), rect, 2)

    def draw_attack_range(self):
        if self.selected_unit:
            x = self.selected_unit.rect.x // self.grid_size
            y = self.selected_unit.rect.y // self.grid_size
            range_color = (255, 0, 0, 128)
            attack_range = getattr(self.selected_unit, 'attack_range', 1)
            
            for dx in range(-attack_range, attack_range + 1):
                for dy in range(-attack_range, attack_range + 1):
                    if (dx * dx + dy * dy) <= attack_range * attack_range:
                        new_x = x + dx
                        new_y = y + dy
                        if (0 <= new_x < len(self.grid[0]) and 
                            0 <= new_y < len(self.grid)):
                            rect = pygame.Rect(new_x * self.grid_size,
                                            new_y * self.grid_size,
                                            self.grid_size, self.grid_size)
                            # Fill with semi-transparent color
                            s = pygame.Surface((self.grid_size, self.grid_size))
                            s.set_alpha(128)
                            s.fill((255, 0, 0))
                            self.surface.blit(s, rect)
                            # Draw border
                            pygame.draw.rect(self.surface, (255, 0, 0), rect, 2)

    def make_bot_move(self):
        # Analyze game state
        bot_units = self.current_faction.units
        enemy_units = self.other_faction.units
        
        # Calculate unit type counts and health status
        bot_unit_types = {}
        bot_total_health = 0
        for unit in bot_units:
            bot_unit_types[unit.unit_type] = bot_unit_types.get(unit.unit_type, 0) + 1
            bot_total_health += unit.health
        
        enemy_unit_types = {}
        enemy_total_health = 0
        for unit in enemy_units:
            enemy_unit_types[unit.unit_type] = enemy_unit_types.get(unit.unit_type, 0) + 1
            enemy_total_health += unit.health
        
        # Determine battle strategy based on analysis
        aggressive = bot_total_health > enemy_total_health
        has_ranged = bot_unit_types.get("archer", 0) > 0
        
        # Process each bot unit with strategic priorities
        for bot_unit in self.current_faction.units:
            bot_unit.selected = False
            
            # Analyze potential targets
            targets = []
            for enemy_unit in enemy_units:
                dx = (enemy_unit.rect.x - bot_unit.rect.x) // self.grid_size
                dy = (enemy_unit.rect.y - bot_unit.rect.y) // self.grid_size
                distance = dx * dx + dy * dy
                
                # Calculate target priority based on multiple factors
                priority = 0
                # Prioritize low health targets
                priority += (100 - enemy_unit.health) * 0.5
                # Prioritize threatening units
                if enemy_unit.unit_type == "archer" and bot_unit.unit_type == "warrior":
                    priority += 30
                elif enemy_unit.unit_type == "knight":
                    priority += 20
                # Distance factor (closer targets get higher priority)
                priority += 100 / (distance + 1)
                
                targets.append((enemy_unit, distance, priority))
            
            # Sort targets by priority
            targets.sort(key=lambda x: x[2], reverse=True)
            
            if targets:
                target, distance, _ = targets[0]
                attack_range = getattr(bot_unit, 'attack_range', 1)
                
                # If target is in attack range, attack
                if distance <= attack_range * attack_range:
                    damage = bot_unit.attack_unit(target)
                    if damage > 0:
                        if self.action_menu:
                            self.action_menu.add_to_log(
                                f"Bot атаковал {target.unit_type} (HP: {target.health}) и нанес {damage} урона"
                            )
                        if not target.is_alive():
                            grid_x = target.rect.x // self.grid_size
                            grid_y = target.rect.y // self.grid_size
                            self.grid[grid_y][grid_x] = None
                            self.other_faction.remove_unit(target)
                            if self.action_menu:
                                self.action_menu.add_to_log(f"{target.unit_type} был уничтожен")
                
                # If target is not in range and unit hasn't moved, plan movement
                elif not bot_unit.is_moved:
                    current_x = bot_unit.rect.x // self.grid_size
                    current_y = bot_unit.rect.y // self.grid_size
                    target_x = target.rect.x // self.grid_size
                    target_y = target.rect.y // self.grid_size
                    
                    # Calculate optimal movement based on unit type and strategy
                    best_move = None
                    best_score = float('-inf')
                    
                    for dx in range(-bot_unit.movement_range, bot_unit.movement_range + 1):
                        for dy in range(-bot_unit.movement_range, bot_unit.movement_range + 1):
                            if dx * dx + dy * dy <= bot_unit.movement_range * bot_unit.movement_range:
                                new_x = current_x + dx
                                new_y = current_y + dy
                                
                                if (0 <= new_x < len(self.grid[0]) and 
                                    0 <= new_y < len(self.grid) and 
                                    not self.grid[new_y][new_x]):
                                    
                                    # Calculate move score based on multiple factors
                                    score = 0
                                    new_distance = (new_x - target_x) ** 2 + (new_y - target_y) ** 2
                                    
                                    # Distance factor
                                    score -= new_distance
                                    
                                    # Strategic positioning
                                    if bot_unit.unit_type == "archer":
                                        # Archers prefer to keep distance
                                        if new_distance >= 4:  # Minimum safe distance
                                            score += 50
                                    elif bot_unit.unit_type == "warrior":
                                        # Warriors want to get close
                                        if new_distance <= 2:
                                            score += 50
                                    elif bot_unit.unit_type == "knight":
                                        # Knights are flexible but prefer medium range
                                        if 2 <= new_distance <= 4:
                                            score += 30
                                    
                                    # Avoid clustering with friendly units
                                    for friendly in bot_units:
                                        if friendly != bot_unit:
                                            fx = friendly.rect.x // self.grid_size
                                            fy = friendly.rect.y // self.grid_size
                                            if abs(new_x - fx) + abs(new_y - fy) <= 1:
                                                score -= 20
                                    
                                    if score > best_score:
                                        best_score = score
                                        best_move = (new_x, new_y)
                    
                    # Execute the best move
                    if best_move:
                        new_x, new_y = best_move
                        if bot_unit.move(new_x * self.grid_size, new_y * self.grid_size):
                            old_x = current_x
                            old_y = current_y
                            self.grid[old_y][old_x] = None
                            self.grid[new_y][new_x] = bot_unit
                            if self.action_menu:
                                self.action_menu.add_to_log(
                                    f"Bot переместил {bot_unit.unit_type} в стратегическую позицию"
                                )
        
        # End bot's turn
        self.end_turn()

    def run_turn_phases(self):
        # 6 фаз хода с броском кубика
        phases = [
            "Движение", 
            "Магия", 
            "Стрельба", 
            "Ближний бой", 
            "Морал", 
            "Командование"
        ]
        
        for phase_index, phase_name in enumerate(phases, 1):
            # Бросок кубика для определения характеристик фазы
            dice_roll = random.randint(1, 6)
            
            # Модификаторы для каждой фазы
            phase_modifiers = {
                1: self.modify_movement,     # Движение
                2: self.modify_magic,        # Магия
                3: self.modify_shooting,     # Стрельба
                4: self.modify_melee_combat, # Ближний бой
                5: self.modify_morale,       # Морал
                6: self.modify_command       # Командование
            }
            
            # Применение модификатора фазы
            modifier_func = phase_modifiers.get(phase_index, lambda x: x)
            modified_roll = modifier_func(dice_roll)
            
            # Логирование результатов
            if self.action_menu:
                self.action_menu.add_to_log(
                    f"Фаза {phase_index} ({phase_name}): "
                    f"Бросок кубика = {dice_roll}, "
                    f"Модифицированный бросок = {modified_roll}"
                )
    
    def modify_movement(self, dice_roll):
        # Влияние броска на движение юнитов
        movement_bonus = {
            1: -1,  # Замедление
            2: -0.5,
            3: 0,   # Без изменений
            4: 0.5, # Небольшое ускорение
            5: 1,   # Значительное ускорение
            6: 1.5  # Максимальное ускорение
        }
        
        for unit in self.current_faction.units:
            unit.movement_range = max(1, int(unit.movement_range * (1 + movement_bonus.get(dice_roll, 0))))
        
        return dice_roll
    
    def modify_magic(self, dice_roll):
        # Влияние броска на магические способности
        magic_bonus = {
            1: 0,   # Нет магии
            2: 0.2, # Слабая магия
            3: 0.4,
            4: 0.6,
            5: 0.8,
            6: 1.0  # Полная магическая мощь
        }
        
        # Здесь можно добавить логику магических способностей
        return dice_roll
    
    def modify_shooting(self, dice_roll):
        # Влияние броска на стрельбу
        shooting_bonus = {
            1: 0,   # Промах
            2: 0.2, # Слабая точность
            3: 0.4,
            4: 0.6,
            5: 0.8,
            6: 1.0  # Идеальная точность
        }
        
        for unit in self.current_faction.units:
            if unit.unit_type == "archer":
                unit.attack *= (1 + shooting_bonus.get(dice_roll, 0))
        
        return dice_roll
    
    def modify_melee_combat(self, dice_roll):
        # Влияние броска на ближний бой
        melee_bonus = {
            1: 0,   # Полный провал
            2: 0.2, # Слабая атака
            3: 0.4,
            4: 0.6,
            5: 0.8,
            6: 1.0  # Мощная атака
        }
        
        for unit in self.current_faction.units:
            if unit.unit_type in ["warrior", "knight"]:
                unit.attack *= (1 + melee_bonus.get(dice_roll, 0))
        
        return dice_roll
    
    def modify_morale(self, dice_roll):
        # Влияние броска на мораль
        morale_bonus = {
            1: -1.0,  # Полный упадок духа
            2: -0.5,
            3: 0,     # Без изменений
            4: 0.5,   # Небольшой подъем духа
            5: 0.75,
            6: 1.0    # Максимальный боевой дух
        }
        
        # Здесь можно добавить логику влияния на боевой дух
        return dice_roll
    
    def modify_command(self, dice_roll):
        # Влияние броска на командование
        command_bonus = {
            1: 0,   # Полный хаос
            2: 0.2, # Слабое управление
            3: 0.4,
            4: 0.6,
            5: 0.8,
            6: 1.0  # Идеальное управление
        }
        
        # Здесь можно добавить логику влияния на командование
        return dice_roll

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 