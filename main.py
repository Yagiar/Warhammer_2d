import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QComboBox)
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
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Game state info
        state_group = QGroupBox("Game State")
        state_layout = QVBoxLayout()
        self.state_label = QLabel("State: Setup")
        self.resources_label = QLabel("Resources: 1000")
        state_layout.addWidget(self.state_label)
        state_layout.addWidget(self.resources_label)
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
        
        # Add all groups to main layout
        layout.addWidget(state_group)
        layout.addWidget(unit_group)
        layout.addWidget(action_group)
        layout.addWidget(info_group)
        layout.addStretch()
        
        self.setLayout(layout)
        self.setFixedWidth(200)
    
    def handle_move(self):
        self.game_widget.game_state.set_action("move")
        self.game_widget.update()
    
    def handle_attack(self):
        self.game_widget.game_state.set_action("attack")
        self.game_widget.update()
    
    def handle_end_turn(self):
        self.game_widget.game_state.end_turn()
        self.game_widget.update()
    
    def update_info(self):
        game_state = self.game_widget.game_state
        self.state_label.setText(f"State: {game_state.state}")
        self.resources_label.setText(f"Resources: {game_state.current_faction.resources}")
        
        if game_state.selected_unit:
            unit = game_state.selected_unit
            info = f"Type: {unit.unit_type}\n"
            info += f"Health: {unit.health}\n"
            info += f"Attack: {unit.attack}\n"
            info += f"Defense: {unit.defense}"
            self.unit_info_label.setText(info)
        else:
            self.unit_info_label.setText("No unit selected")

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
            unit = self.current_faction.add_unit(
                grid_x * self.grid_size,
                grid_y * self.grid_size,
                "warrior"  # This will be replaced by the selected unit type from UI
            )
            if unit:
                self.grid[grid_y][grid_x] = unit
    
    def handle_turn(self, grid_x, grid_y):
        clicked_unit = self.grid[grid_y][grid_x]
        
        # If no action is selected, select unit
        if not self.current_action:
            if clicked_unit and clicked_unit in self.current_faction.units:
                if self.selected_unit:
                    self.selected_unit.selected = False
                self.selected_unit = clicked_unit
                clicked_unit.selected = True
        
        # Handle move action
        elif self.current_action == "move" and self.selected_unit:
            if not clicked_unit:  # Moving to empty space
                if self.selected_unit.move(grid_x * self.grid_size, 
                                         grid_y * self.grid_size):
                    old_x = self.selected_unit.rect.x // self.grid_size
                    old_y = self.selected_unit.rect.y // self.grid_size
                    self.grid[old_y][old_x] = None
                    self.grid[grid_y][grid_x] = self.selected_unit
                    self.current_action = None
                    self.selected_unit.selected = False
                    self.selected_unit = None
        
        # Handle attack action
        elif self.current_action == "attack" and self.selected_unit:
            if clicked_unit and clicked_unit in self.other_faction.units:
                damage = self.selected_unit.attack_unit(clicked_unit)
                if damage > 0:
                    if not clicked_unit.is_alive():
                        self.grid[grid_y][grid_x] = None
                        clicked_unit.faction.remove_unit(clicked_unit)
                    self.current_action = None
                    self.selected_unit.selected = False
                    self.selected_unit = None
    
    def end_turn(self):
        if self.state in ["player1_turn", "player2_turn"]:
            if self.selected_unit:
                self.selected_unit.selected = False
                self.selected_unit = None
            
            self.current_action = None
            self.current_faction, self.other_faction = self.other_faction, self.current_faction
            self.current_faction.reset_all_units()
            
            # Check victory conditions
            if not self.other_faction.has_units():
                self.state = "game_over"
            else:
                self.state = "player2_turn" if self.state == "player1_turn" else "player1_turn"
    
    def start_game(self):
        if self.state == "setup":
            self.state = "player1_turn"
    
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
        
        # Draw units
        for faction in [self.current_faction, self.other_faction]:
            for unit in faction.units:
                unit.draw(self.surface)
        
        # Draw action indicators
        if self.selected_unit and self.current_action == "move":
            self.draw_movement_range()
        elif self.selected_unit and self.current_action == "attack":
            self.draw_attack_range()
    
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
                            pygame.draw.rect(self.surface, range_color, rect, 1)
    
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
                            pygame.draw.rect(self.surface, range_color, rect, 1)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 