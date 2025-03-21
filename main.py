import sys
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, 
                             QHBoxLayout, QVBoxLayout, QPushButton, 
                             QLabel, QGroupBox, QComboBox, QTextEdit, QTextBrowser)
from PySide6.QtCore import Qt, QTimer
import pygame
from faction import Faction
import random
import time
import re
from PySide6.QtGui import QTextCursor

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
    def __init__(self, game_widget, units_list):
        super().__init__()
        self.game_widget = game_widget
        self.units_list = units_list
        self.setup_ui()
        self.update_button_states()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Game state info
        state_group = QGroupBox("Game State")
        state_layout = QVBoxLayout()
        self.turn_label = QLabel("Current Turn: Player 1")
        self.state_label = QLabel("State: Setup")
        self.phase_label = QLabel("Phase: -")
        self.help_label = QLabel("Разместите юнитов в красной зоне,\nзатем нажмите 'Start Game'")
        self.help_label.setStyleSheet("color: #666;")
        self.resources_label = QLabel("Your Resources: 1000")
        self.enemy_resources_label = QLabel("Enemy Resources: 1000")
        self.start_game_btn = QPushButton("Start Game")
        self.start_game_btn.clicked.connect(self.handle_start_game)
        self.start_game_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; padding: 5px; }")
        state_layout.addWidget(self.turn_label)
        state_layout.addWidget(self.state_label)
        state_layout.addWidget(self.phase_label)
        state_layout.addWidget(self.help_label)
        state_layout.addWidget(self.resources_label)
        state_layout.addWidget(self.enemy_resources_label)
        state_layout.addWidget(self.start_game_btn)
        state_group.setLayout(state_layout)
        
        # Unit selection
        unit_group = QGroupBox("Unit Selection")
        unit_layout = QVBoxLayout()
        
        # Добавляем метку
        unit_layout.addWidget(QLabel("Select Unit Type:"))
        
        # Инициализируем комбобокс
        self.unit_combo = QComboBox()
        
        # Dynamically load unit types from game state's faction
        available_units = self.game_widget.game_state.current_faction.get_available_unit_types()
        for unit_data in available_units:
            unit_type = unit_data['type']
            cost = unit_data['cost']
            self.unit_combo.addItem(f"{unit_type.capitalize()} ({cost})")
        
        # Добавляем горизонтальный контейнер для комбобокса и кнопки выбора
        combo_layout = QHBoxLayout()
        combo_layout.addWidget(self.unit_combo, 3)  # соотношение 3:1
        
        # Кнопка для подтверждения выбора юнита
        self.select_unit_btn = QPushButton("Выбрать")
        self.select_unit_btn.clicked.connect(self.handle_select_unit)
        combo_layout.addWidget(self.select_unit_btn, 1)
        
        # Добавляем контейнер с комбобоксом и кнопкой
        unit_layout.addLayout(combo_layout)
        
        # Add unit description label
        self.unit_description = QLabel("Выберите тип юнита и нажмите 'Выбрать'")
        self.unit_description.setWordWrap(True)
        self.unit_description.setStyleSheet("color: #666; font-size: 10px;")
        unit_layout.addWidget(self.unit_description)
        
        unit_group.setLayout(unit_layout)
        
        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QVBoxLayout()
        self.move_btn = QPushButton("Move")
        self.attack_btn = QPushButton("Attack")
        self.end_turn_btn = QPushButton("End Turn")
        self.roll_dice_btn = QPushButton("Roll Dice")
        
        self.move_btn.clicked.connect(self.handle_move)
        self.attack_btn.clicked.connect(self.handle_attack)
        self.end_turn_btn.clicked.connect(self.handle_end_turn)
        self.roll_dice_btn.clicked.connect(self.handle_roll_dice)
        
        action_layout.addWidget(self.move_btn)
        action_layout.addWidget(self.attack_btn)
        action_layout.addWidget(self.roll_dice_btn)
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
        self.setFixedWidth(280)  # Немного увеличиваем ширину для сайдбара
    
    def update_button_states(self):
        game_state = self.game_widget.game_state
        
        # Update button states based on game state
        is_player_turn = game_state.state == "player1_turn"
        is_setup = game_state.state == "setup"
        is_game_over = game_state.state == "game_over"
        
        self.unit_combo.setEnabled(is_setup)
        self.select_unit_btn.setEnabled(is_setup)
        self.start_game_btn.setEnabled(is_setup)
        
        # Action buttons are only enabled during player's turn
        self.move_btn.setEnabled(is_player_turn and (game_state.selected_unit is not None) and (not game_state.selected_unit.is_moved))
        self.attack_btn.setEnabled(is_player_turn and (game_state.selected_unit is not None) and (not game_state.selected_unit.is_attacked))
        self.end_turn_btn.setEnabled(is_player_turn and not is_setup and not is_game_over)
        
        # Roll dice button is only enabled during player's turn and in the correct phase
        self.roll_dice_btn.setEnabled(is_player_turn and 
                                     game_state.current_phase is not None and 
                                     not game_state.phase_roll_complete)
    
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
    
    def handle_roll_dice(self):
        if self.game_widget and self.game_widget.game_state:
            self.game_widget.game_state.roll_dice_for_phase()
            self.game_widget.update()
            self.update_button_states()
            self.update_info()
            
            # Проверка, находимся ли мы в фазе Morale для игрока - если да, то сразу переходим к следующей фазе
            if (self.game_widget.game_state.current_phase == "Morale" and 
                self.game_widget.game_state.state == "player1_turn" and 
                self.game_widget.game_state.phase_roll_complete):
                # Задержка для показа результата броска кубика
                time.sleep(1)
                self.game_widget.game_state.proceed_to_next_phase()
                self.game_widget.update()
                self.update_button_states()
                self.update_info()
    
    def add_to_log(self, message):
        self.action_log.append(message)
        self.action_log.verticalScrollBar().setValue(
            self.action_log.verticalScrollBar().maximum()
        )
    
    def update_info(self):
        if self.game_widget and self.game_widget.game_state:
            game_state = self.game_widget.game_state
            
            # Update state info
            if game_state.state == "setup":
                state_text = "Setup"
            elif game_state.state == "player1_turn":
                state_text = "Player's Turn"
            elif game_state.state == "player2_turn":
                state_text = "Bot's Turn"
            elif game_state.state == "game_over":
                state_text = "Game Over"
            else:
                state_text = game_state.state
            
            self.state_label.setText(f"State: {state_text}")
            
            # Update phase info
            if game_state.current_phase:
                self.phase_label.setText(f"Phase: {game_state.current_phase}")
            else:
                self.phase_label.setText("Phase: -")
            
            # Update resources info
            player_resources = game_state.player_faction.resources
            bot_resources = game_state.bot_faction.resources
            self.resources_label.setText(f"Your Resources: {player_resources}")
            self.enemy_resources_label.setText(f"Enemy Resources: {bot_resources}")
            
            if game_state.selected_unit:
                unit = game_state.selected_unit
                info = f"Type: {unit.unit_type}\n"
                info += f"Health: {unit.health}\n"
                info += f"Attack: {unit.attack}\n"
                info += f"Defense: {unit.defense}"
                self.unit_info_label.setText(info)
            else:
                self.unit_info_label.setText("No unit selected")
            
            # Обновляем список юнитов
            self.update_units_list(game_state.player_faction.units)
        
        # Update button states
        self.update_button_states()
    
    def update_units_list(self, units):
        """Обновляет список юнитов игрока в сайдбаре"""
        self.units_list.clear()
        
        if not units:
            self.units_list.setHtml("<i>У вас нет юнитов</i>")
            return
        
        html = "<style>table {width: 100%; border-collapse: collapse;} td {padding: 2px;} .unit-row:hover {background-color: #f0f0f0; cursor: pointer;}</style>"
        # Группируем юниты по типу
        unit_types = {}
        for unit in units:
            if unit.unit_type not in unit_types:
                unit_types[unit.unit_type] = []
            unit_types[unit.unit_type].append(unit)
        
        # Отображаем юниты по типам
        for unit_type, unit_list in unit_types.items():
            html += f"<h3 style='margin: 5px 0px;'>{unit_type.capitalize()} ({len(unit_list)})</h3>"
            
            # Создаем таблицу для юнитов этого типа
            html += "<table>"
            for i, unit in enumerate(unit_list):
                # Добавляем класс для строки, чтобы подсветить при наведении
                row_class = " class='unit-row'"
                
                # Добавляем стиль для выбранного юнита
                selected_style = ""
                if unit.selected:
                    selected_style = " style='background-color: #ffffc0;'"
                
                if unit.health <= 0:
                    # Отображаем убитый юнит
                    html += f"<tr{row_class}{selected_style}><td>#{i+1}</td><td colspan='2'><span style='color:red; font-weight:bold'>УБИТ</span></td></tr>"
                else:
                    # Цвет для здоровья
                    health_color = self._get_health_color(unit.health)
                    # Индикатор статуса (ходил/атаковал)
                    status = []
                    if unit.is_moved:
                        status.append("<span style='color:orange'>◉ Ходил</span>")
                    if unit.is_attacked:
                        status.append("<span style='color:purple'>◉ Атаковал</span>")
                    
                    status_text = " ".join(status) if status else "<span style='color:green'>◉ Готов</span>"
                    
                    # Отображаем здоровье и атаку юнита
                    html += f"<tr{row_class}{selected_style}><td>#{i+1}</td><td><b>HP:</b> <span style='color:{health_color}'>{unit.health}</span></td>"
                    html += f"<td><b>ATK:</b> {unit.attack}</td></tr>"
                    
                    # Отображаем статус юнита
                    html += f"<tr{row_class}{selected_style}><td></td><td colspan='2'>{status_text}</td></tr>"
                    
                    # Добавляем пустую строку для разделения юнитов
                    html += f"<tr><td colspan='3'><hr style='border:none; height:1px; background-color:#eee'></td></tr>"
            
            html += "</table>"
        
        self.units_list.setHtml(html)
    
    def _get_health_color(self, health):
        """Возвращает цвет для отображения здоровья"""
        if health > 75:
            return "green"
        elif health > 50:
            return "yellowgreen"
        elif health > 25:
            return "orange"
        else:
            return "red"
    
    def handle_select_unit(self):
        """Обработчик нажатия кнопки выбора юнита"""
        if self.unit_combo.count() > 0:
            self.update_unit_description()
            self.add_to_log(f"Выбран тип юнита: {self.unit_combo.currentText()}")
    
    def update_unit_description(self):
        """Обновляет описание выбранного юнита"""
        if self.unit_combo.count() > 0:
            current_text = self.unit_combo.currentText()
            unit_type = current_text.split(" (")[0].lower()
            
            # Получаем данные о юните из фракции
            available_units = self.game_widget.game_state.current_faction.get_available_unit_types()
            for unit_data in available_units:
                if unit_data['type'].lower() == unit_type:
                    description = unit_data.get('description', 'Нет описания')
                    cost = unit_data.get('cost', 0)
                    health = unit_data.get('health', 100)
                    attack = unit_data.get('attack', 0)
                    defense = unit_data.get('defense', 0)
                    movement = unit_data.get('movement_range', 0)
                    attack_range = unit_data.get('attack_range', 0)
                    
                    # Форматируем описание юнита
                    formatted_desc = f"<b>{unit_type.capitalize()}</b> ({cost})<br>"
                    formatted_desc += f"HP: {health} | ATK: {attack} | DEF: {defense}<br>"
                    formatted_desc += f"Дальность: {movement} | Дист.атаки: {attack_range}"
                    
                    self.unit_description.setText(formatted_desc)
                    self.unit_description.setTextFormat(Qt.RichText)
                    return
            
            # Если данные не найдены
            self.unit_description.setText(f"Нет данных о типе {unit_type}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Warhammer 40k: Lite Edition")
        
        # Создаем главный виджет и лейаут
        main_widget = QWidget()
        main_layout = QHBoxLayout()  # Горизонтальный лейаут для всего интерфейса
        
        # Создаем левую панель для списка юнитов
        self.left_panel = QWidget()
        left_layout = QVBoxLayout()
        
        # Заголовок для левой панели
        left_layout.addWidget(QLabel("<h2>Ваши юниты</h2>"))
        
        # Создаем виджет для отображения списка юнитов
        self.units_list = QTextBrowser()
        self.units_list.setMinimumWidth(200)  # Устанавливаем фиксированную ширину
        self.units_list.setHtml("<i>У вас нет юнитов</i>")
        
        # Подключаем обработчик клика по списку юнитов
        self.units_list.mouseReleaseEvent = self.handle_units_list_click
        
        left_layout.addWidget(self.units_list)
        self.left_panel.setLayout(left_layout)
        
        # Добавляем левую панель в главный лейаут
        main_layout.addWidget(self.left_panel)
        
        # Создаем игровой виджет
        self.game_widget = GameWidget()
        main_layout.addWidget(self.game_widget, 1)  # 1 = растягивать по доступному пространству
        
        # Создаем меню действий и передаем ему список юнитов
        self.action_menu = ActionMenu(self.game_widget, self.units_list)
        main_layout.addWidget(self.action_menu)
        
        # Устанавливаем лейаут для главного виджета
        main_widget.setLayout(main_layout)
        self.setCentralWidget(main_widget)
        
        # Устанавливаем размер окна
        self.resize(1200, 800)
        
        # Связываем игровой виджет с меню действий
        self.game_widget.action_menu = self.action_menu
        # Связываем игровое состояние с меню действий
        self.game_widget.game_state.set_action_menu(self.action_menu)
        
        # Настраиваем таймер обновления
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_game)
        self.timer.start(1000 // 60)  # 60 FPS
    
    def handle_units_list_click(self, event):
        """Обрабатывает клик по списку юнитов"""
        # Получаем HTML под курсором
        cursor = self.units_list.cursorForPosition(event.pos())
        cursor.select(QTextCursor.LineUnderCursor)
        line = cursor.selectedText()
        
        # Находим номер юнита в строке (формат: #1, #2, и т.д.)
        match = re.search(r'#(\d+)', line)
        if match:
            unit_index = int(match.group(1)) - 1
            if 0 <= unit_index < len(self.game_widget.game_state.player_faction.units):
                # Сначала сбрасываем выделение у всех юнитов
                for unit in self.game_widget.game_state.player_faction.units:
                    unit.selected = False
                
                # Выделяем выбранный юнит
                unit = self.game_widget.game_state.player_faction.units[unit_index]
                if unit.health > 0:  # Только если юнит жив
                    unit.selected = True
                    self.game_widget.game_state.selected_unit = unit
                    self.action_menu.add_to_log(f"Выбран {unit.unit_type} #{unit_index + 1}")
                    
                    # Обновляем информацию в интерфейсе
                    self.action_menu.update_units_list(self.game_widget.game_state.player_faction.units)
                    self.action_menu.update_button_states()
                    self.game_widget.update()
        
        # Обрабатываем клик как обычно
        super(QTextBrowser, self.units_list).mouseReleaseEvent(event)

    def update_game(self):
        """Обновляет игровой интерфейс"""
        self.game_widget.update()
        self.action_menu.update_info()

class GameState:
    def __init__(self, surface):
        self.surface = surface
        self.player_faction = Faction("faction1")
        self.bot_faction = Faction("faction2")
        self.current_faction = self.player_faction
        self.other_faction = self.bot_faction
        self.state = "setup"  # setup, player1_turn, player2_turn, game_over
        self.selected_unit = None
        self.current_action = None  # move, attack
        self.action_menu = None
        self.grid_size = 32
        
        # Инициализация сетки
        self.grid = [[None for _ in range(surface.get_width() // self.grid_size)]
                    for _ in range(surface.get_height() // self.grid_size)]
        
        # Turn phases
        self.phases = ["Movement", "Attack", "Morale"]
        self.current_phase = None
        self.current_phase_index = -1
        self.phase_roll_complete = False
        self.dice_roll = None
        
        self.setup_zones = {
            "faction1": (0, self.surface.get_width() // self.grid_size // 3),
            "faction2": (2 * self.surface.get_width() // self.grid_size // 3, 
                        self.surface.get_width() // self.grid_size)
        }
    
    def set_action_menu(self, menu):
        self.action_menu = menu
    
    def set_action(self, action):
        self.current_action = action
        
        # Проверяем соответствие между действием и текущей фазой
        if action == "move" and self.current_phase != "Movement":
            if self.action_menu:
                self.action_menu.add_to_log("⚠️ В текущей фазе движение недоступно!")
            self.current_action = None
            return
            
        if action == "attack" and self.current_phase != "Attack":
            if self.action_menu:
                self.action_menu.add_to_log("⚠️ В текущей фазе атака недоступна!")
            self.current_action = None
            return
        
        # Если действие не соответствует текущей фазе, сбрасываем выбор юнита
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
            selected_text = self.action_menu.unit_combo.currentText().lower()
            # Извлекаем только имя юнита, отбрасывая стоимость в скобках
            unit_type = selected_text.split(" (")[0]
            
            unit = self.current_faction.add_unit(
                grid_x * self.grid_size,
                grid_y * self.grid_size,
                unit_type
            )
            if unit:
                self.grid[grid_y][grid_x] = unit
                if self.action_menu:
                    self.action_menu.add_to_log(f"Размещен {unit_type}")
                    # Обновляем список юнитов при размещении нового юнита
                    self.action_menu.update_units_list(self.player_faction.units)
    
    def handle_turn(self, grid_x, grid_y):
        # Check if we're selecting a unit
        clicked_unit = None
        
        # Проверяем, что игра находится в фазе хода игрока
        if self.state == "player1_turn":
            # Находим юнит по клику
            for unit in self.current_faction.units:
                if unit.rect.collidepoint(grid_x * self.grid_size, grid_y * self.grid_size):
                    clicked_unit = unit
                    break
            
            # Если мы собираемся двигать выбранный юнит
            if self.current_action == "move" and self.selected_unit and not self.selected_unit.is_moved and self.current_phase == "Movement" and self.phase_roll_complete:
                # Проверяем, что клик в пустую клетку
                if not clicked_unit:
                    # Calculate distance to make sure it's within movement range
                    dx = abs(grid_x * self.grid_size - self.selected_unit.rect.x) // self.grid_size
                    dy = abs(grid_y * self.grid_size - self.selected_unit.rect.y) // self.grid_size
                    distance = (dx ** 2 + dy ** 2) ** 0.5  # Euclidean distance
                    
                    if distance <= self.selected_unit.movement_range:
                        # Проверка на пустую клетку
                        if self.grid[grid_y][grid_x] is None:
                            # Move the unit
                            old_x = self.selected_unit.rect.x // self.grid_size
                            old_y = self.selected_unit.rect.y // self.grid_size
                            
                            # Обновляем позицию на игровом поле
                            move_successful = self.selected_unit.move(grid_x * self.grid_size, grid_y * self.grid_size)
                            if move_successful:
                                # Обновляем сетку
                                self.grid[old_y][old_x] = None
                                self.grid[grid_y][grid_x] = self.selected_unit
                                self.selected_unit.is_moved = True
                                self.current_action = None
                                
                                if self.action_menu:
                                    self.action_menu.add_to_log(f"Unit moved to ({grid_x}, {grid_y})")
                                    self.action_menu.update_button_states()
                                
                                # Переходим к следующей фазе автоматически
                                self.proceed_to_next_phase()
            
            # Если мы собираемся атаковать выбранным юнитом
            elif self.current_action == "attack" and self.selected_unit and not self.selected_unit.is_attacked and self.current_phase == "Attack" and self.phase_roll_complete:
                # Находим вражеский юнит для атаки
                enemy_unit = None
                for unit in self.other_faction.units:
                    if unit.rect.collidepoint(grid_x * self.grid_size, grid_y * self.grid_size):
                        enemy_unit = unit
                        break
                
                if enemy_unit:
                    # Calculate distance to check if in range
                    dx = abs(enemy_unit.rect.x - self.selected_unit.rect.x) // self.grid_size
                    dy = abs(enemy_unit.rect.y - self.selected_unit.rect.y) // self.grid_size
                    distance = dx + dy  # Manhattan distance
                    
                    if distance <= self.selected_unit.attack_range:
                        # Perform attack
                        damage = self.selected_unit.attack_unit(enemy_unit)
                        self.selected_unit.is_attacked = True
                        self.current_action = None
                        
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Атака нанесла {damage} урона!")
                            self.action_menu.update_button_states()
                        
                        # Check if target was destroyed
                        if enemy_unit.health <= 0:
                            # Очищаем клетку
                            enemy_grid_x = enemy_unit.rect.x // self.grid_size
                            enemy_grid_y = enemy_unit.rect.y // self.grid_size
                            self.grid[enemy_grid_y][enemy_grid_x] = None
                            
                            self.other_faction.remove_unit(enemy_unit)
                            if self.action_menu:
                                self.action_menu.add_to_log(f"❌ Юнит противника уничтожен!")
                                
                            # Check victory condition
                            if not self.other_faction.has_units():
                                self.state = "game_over"
                                if self.action_menu:
                                    self.action_menu.add_to_log("Игра окончена! Победитель: Player 1")
                                return
                                
                        # Переходим к следующей фазе автоматически
                        self.proceed_to_next_phase()
                        
                        # Обновляем список юнитов после атаки
                        if self.action_menu:
                            self.action_menu.update_units_list(self.player_faction.units)
            
            # Фаза Morale - игрок просто должен бросить кубик
            elif self.current_phase == "Morale" and self.phase_roll_complete:
                # Автоматически переходим к следующей фазе (конец хода)
                self.proceed_to_next_phase()
            
            # Если мы просто выбираем юнита (или отменяем выбор)
            elif clicked_unit:
                # Выбор/отмена выбора юнита
                if self.selected_unit:
                    self.selected_unit.selected = False
                
                if self.selected_unit == clicked_unit:
                    # Отменяем выбор того же юнита
                    self.selected_unit = None
                    self.current_action = None
                else:
                    # Выбираем нового юнита
                    self.selected_unit = clicked_unit
                    self.selected_unit.selected = True
                    self.current_action = None
                    
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Выбран юнит: {self.selected_unit.unit_type}")
                        self.action_menu.update_button_states()
    
    def end_turn(self):
        if self.state in ["player1_turn", "player2_turn"]:
            if self.selected_unit:
                self.selected_unit.selected = False
                self.selected_unit = None
            
            self.current_action = None
            self.current_phase = None
            self.current_phase_index = -1
            self.phase_roll_complete = False
            
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
                
                # Start phases for the new turn
                self.start_turn_phases()
                
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
                self.current_faction = self.player_faction
                self.other_faction = self.bot_faction
            else:
                self.state = "player2_turn"
                first_player = "Player 2 (Bot)"
                self.current_faction = self.bot_faction
                self.other_faction = self.player_faction
            
            # Финальное логирование результата
            if self.action_menu:
                self.action_menu.add_to_log(f"🏁 Первым ходит {first_player}!")
                self.action_menu.add_to_log(f"Результат: Player 1 ({p1_roll}) vs Player 2 ({p2_roll})")
                # Автоматическое размещение юнитов бота, если их ещё нет, с более рандомным размещением по полю
                if not self.bot_faction.units:
                    bot_resources = self.bot_faction.resources
                    unit_costs = {"warrior": 100, "archer": 150, "knight": 200}
                    desired_composition = [("warrior", 0.4), ("archer", 0.3), ("knight", 0.3)]
                    total_possible_units = bot_resources // min(unit_costs.values())
                    planned_units = []
                    for unit_type, ratio in desired_composition:
                        count = int(total_possible_units * ratio)
                        cost = count * unit_costs[unit_type]
                        while count > 0 and cost > bot_resources:
                            count -= 1
                            cost = count * unit_costs[unit_type]
                        for _ in range(count):
                            if bot_resources >= unit_costs[unit_type]:
                                planned_units.append(unit_type)
                                bot_resources -= unit_costs[unit_type]
                    zone = self.setup_zones["faction2"]
                    zone_start, zone_end = zone[0], zone[1]
                    rows = len(self.grid)
                    for unit_type in planned_units:
                        placed = False
                        attempts = 0
                        max_attempts = 100
                        while not placed and attempts < max_attempts:
                            rand_row = random.randint(0, rows - 1)
                            rand_col = random.randint(zone_start, zone_end - 1)
                            if self.grid[rand_row][rand_col] is None:
                                unit = self.bot_faction.add_unit(rand_col * self.grid_size, rand_row * self.grid_size, unit_type)
                                if unit:
                                    self.grid[rand_row][rand_col] = unit
                                    if self.action_menu:
                                        self.action_menu.add_to_log(f"Размещен бот: {unit_type} в ({rand_col}, {rand_row})")
                                    placed = True
                            attempts += 1
            
            # Start the first turn with phases
            self.start_turn_phases()
            
            # If bot goes first, make its move
            if self.state == "player2_turn":
                self.make_bot_move()
    
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
        # Bot's turn logic
        if self.state == "player2_turn":
            self.action_menu.add_to_log("Ход бота...")
            
            # Вначале бросаем кубик для фазы, если ещё не бросали
            if self.current_phase and not self.phase_roll_complete:
                self.action_menu.add_to_log(f"Бросаем кубик для фазы {self.current_phase}")
                self.roll_dice_for_phase()
                time.sleep(0.5)  # Небольшая пауза после броска
            
            # Bot only processes the current phase if roll is complete
            if self.current_phase and self.phase_roll_complete:
                # Get player units for targeting
                player_units = self.player_faction.units
                
                # Проверка, есть ли юниты у игрока
                if not player_units:
                    self.action_menu.add_to_log("У игрока нет юнитов. Пропускаем ход бота.")
                    self.proceed_to_next_phase()
                    return
                
                self.action_menu.add_to_log(f"Бот обрабатывает фазу: {self.current_phase}")
                
                # Find available units for the current phase
                if self.current_phase == "Movement":
                    available_units = [unit for unit in self.bot_faction.units if not unit.is_moved]
                    if self.action_menu:
                        if available_units:
                            self.action_menu.add_to_log(f"Доступно {len(available_units)} юнитов для движения")
                        else:
                            self.action_menu.add_to_log("Нет доступных юнитов для движения")
                elif self.current_phase == "Attack":
                    available_units = [unit for unit in self.bot_faction.units if not unit.is_attacked]
                    if self.action_menu:
                        if available_units:
                            self.action_menu.add_to_log(f"Доступно {len(available_units)} юнитов для атаки")
                            # Проверяем параметры атаки у юнитов
                            for unit in available_units:
                                self.action_menu.add_to_log(f"{unit.unit_type}: атака={unit.attack}, дальность={unit.attack_range}")
                        else:
                            self.action_menu.add_to_log("Нет доступных юнитов для атаки")
                else:  # Morale phase
                    available_units = self.bot_faction.units
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Фаза морали: {len(available_units)} юнитов")
                
                # Если есть доступные юниты для текущей фазы
                if available_units:
                    # Select the best unit for the current phase
                    if self.current_phase == "Movement":
                        bot_unit = max(available_units, key=lambda unit: unit.movement_range + (50 if unit.unit_type == "archer" else 0))
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Движение: выбран {bot_unit.unit_type} с рейтингом {bot_unit.movement_range}")
                    elif self.current_phase == "Attack":
                        bot_unit = max(available_units, key=lambda unit: unit.attack)
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Атака: выбран {bot_unit.unit_type} с атакой {bot_unit.attack}")
                    else:  # Morale phase
                        bot_unit = max(available_units, key=lambda unit: unit.defense)
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Мораль: выбран {bot_unit.unit_type} с защитой {bot_unit.defense}")
                    
                    # Select the unit
                    if self.selected_unit:
                        self.selected_unit.selected = False
                    self.selected_unit = bot_unit
                    self.selected_unit.selected = True
                    
                    # Process the phase
                    if self.current_phase == "Movement" and not bot_unit.is_moved:
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Вызываем процесс движения для {bot_unit.unit_type}")
                        # Показываем позицию юнита до перемещения
                        pos_x = bot_unit.rect.x // self.grid_size
                        pos_y = bot_unit.rect.y // self.grid_size
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Юнит находится в позиции ({pos_x}, {pos_y})")
                        
                        self.process_bot_movement(bot_unit, player_units)
                        
                        # Показываем, изменилась ли позиция юнита
                        new_x = bot_unit.rect.x // self.grid_size
                        new_y = bot_unit.rect.y // self.grid_size
                        if new_x != pos_x or new_y != pos_y:
                            if self.action_menu:
                                self.action_menu.add_to_log(f"Юнит переместился в новую позицию ({new_x}, {new_y})")
                        else:
                            if self.action_menu:
                                self.action_menu.add_to_log(f"Юнит остался на месте ({new_x}, {new_y})")
                    
                    elif self.current_phase == "Attack" and not bot_unit.is_attacked:
                        if self.action_menu:
                            self.action_menu.add_to_log(f"Вызываем процесс атаки для {bot_unit.unit_type}")
                            self.action_menu.add_to_log(f"Позиция атакующего: ({bot_unit.rect.x // self.grid_size}, {bot_unit.rect.y // self.grid_size})")
                            
                            # Проверяем расстояния до всех юнитов игрока
                            for target in player_units:
                                dx = abs(bot_unit.rect.x // self.grid_size - target.rect.x // self.grid_size)
                                dy = abs(bot_unit.rect.y // self.grid_size - target.rect.y // self.grid_size)
                                dist = dx + dy
                                self.action_menu.add_to_log(f"Расстояние до {target.unit_type}: {dist} (нужно ≤{bot_unit.attack_range})")
                        
                        self.process_bot_attack(bot_unit, player_units)
                    
                    elif self.current_phase == "Morale":
                        if self.action_menu:
                            self.action_menu.add_to_log("Фаза морали - просто переходим дальше")
                else:
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Нет доступных юнитов для фазы {self.current_phase}, пропускаем")
                
                # Wait a moment to show the action
                time.sleep(0.5)
                
                # Proceed to the next phase
                if self.action_menu:
                    self.action_menu.add_to_log("Переходим к следующей фазе")
                self.proceed_to_next_phase()
            
            # Update UI
            if self.action_menu:
                self.action_menu.update_button_states()
                self.action_menu.update_info()
    
    def process_bot_movement(self, bot_unit, player_units):
        """Processes bot movement during its turn."""
        if self.action_menu:
            self.action_menu.add_to_log(f"Бот выполняет движение {bot_unit.unit_type}")
            self.action_menu.add_to_log(f"Диапазон движения: {bot_unit.movement_range}")
        
        if not player_units:
            if self.action_menu:
                self.action_menu.add_to_log("Нет юнитов игрока для преследования")
            bot_unit.is_moved = True
            return

        current_x = bot_unit.rect.x // self.grid_size
        current_y = bot_unit.rect.y // self.grid_size

        closest_enemy = min(player_units, key=lambda target: 
            ((bot_unit.rect.x - target.rect.x) ** 2 + 
            (bot_unit.rect.y - target.rect.y) ** 2) ** 0.5)

        enemy_x = closest_enemy.rect.x // self.grid_size
        enemy_y = closest_enemy.rect.y // self.grid_size

        if self.action_menu:
            self.action_menu.add_to_log(f"Бот в позиции ({current_x}, {current_y}), противник в ({enemy_x}, {enemy_y})")

        # Гарантируем минимальный диапазон движения для бота
        bot_unit.movement_range = max(2, bot_unit.movement_range)
        
        # Ищем все доступные ходы в пределах диапазона движения
        valid_moves = []
        for dx in range(-bot_unit.movement_range, bot_unit.movement_range + 1):
            for dy in range(-bot_unit.movement_range, bot_unit.movement_range + 1):
                test_x = current_x + dx
                test_y = current_y + dy
                
                # Пропускаем текущую позицию
                if dx == 0 and dy == 0:
                    continue
                    
                # Проверяем, что расстояние находится в пределах диапазона движения
                distance = ((dx ** 2 + dy ** 2) ** 0.5)
                
                # Проверяем, что позиция в пределах поля и свободна
                if (distance <= bot_unit.movement_range and 
                    0 <= test_x < len(self.grid[0]) and 
                    0 <= test_y < len(self.grid) and 
                    self.grid[test_y][test_x] is None):
                    
                    # Вычисляем расстояние до противника с этой новой позиции
                    enemy_dist = ((test_x - enemy_x) ** 2 + (test_y - enemy_y) ** 2) ** 0.5
                    valid_moves.append((test_x, test_y, enemy_dist))
        
        if self.action_menu:
            self.action_menu.add_to_log(f"Найдено {len(valid_moves)} возможных ходов")
        
        # Сортируем ходы по расстоянию до противника (предпочитаем ближе)
        valid_moves.sort(key=lambda move: move[2])
        
        # Выбираем лучший ход
        new_x, new_y = current_x, current_y
        if valid_moves:
            new_x, new_y, _ = valid_moves[0]
            if self.action_menu:
                self.action_menu.add_to_log(f"Выбран ход в ({new_x}, {new_y})")
        else:
            if self.action_menu:
                self.action_menu.add_to_log("Нет доступных ходов!")

        # Перемещаем юнит, если найдена подходящая позиция
        if new_x != current_x or new_y != current_y:
            pixel_x = new_x * self.grid_size
            pixel_y = new_y * self.grid_size
            
            if self.action_menu:
                self.action_menu.add_to_log(f"Пытаемся переместить юнит в пиксели ({pixel_x}, {pixel_y})")
            
            # Перемещаем юнит
            # Обновляем позицию напрямую для отладки
            bot_unit.rect.x = pixel_x
            bot_unit.rect.y = pixel_y
            move_successful = True
            
            if move_successful:
                # Обновляем сетку
                self.grid[current_y][current_x] = None
                self.grid[new_y][new_x] = bot_unit
                bot_unit.is_moved = True
                
                if self.action_menu:
                    self.action_menu.add_to_log(f"Бот переместил {bot_unit.unit_type} из ({current_x}, {current_y}) в ({new_x}, {new_y})")
            else:
                bot_unit.is_moved = True
                if self.action_menu:
                    self.action_menu.add_to_log("Перемещение не удалось")
        else:
            bot_unit.is_moved = True
            if self.action_menu:
                self.action_menu.add_to_log("Юнит остался на месте - нет валидных ходов")

    def process_bot_attack(self, bot_unit, player_units):
        """Обрабатывает атаку выбранного юнита бота"""
        if self.action_menu:
            self.action_menu.add_to_log(f"Бот выполняет атаку {bot_unit.unit_type}")
            self.action_menu.add_to_log(f"Диапазон атаки: {bot_unit.attack_range}")
            bot_x = bot_unit.rect.x // self.grid_size
            bot_y = bot_unit.rect.y // self.grid_size
            self.action_menu.add_to_log(f"Позиция бота: ({bot_x}, {bot_y})")
        
        # Find enemy in range
        in_range_enemies = []
        for target in player_units:
            target_x = target.rect.x // self.grid_size
            target_y = target.rect.y // self.grid_size
            
            # Расстояние в клетках (не в пикселях)
            dx = abs(bot_x - target_x)
            dy = abs(bot_y - target_y)
            dist = dx + dy  # Manhattan distance
            
            if self.action_menu:
                self.action_menu.add_to_log(f"Проверяем {target.unit_type} в ({target_x}, {target_y}), расстояние: {dist}")
            
            if dist <= bot_unit.attack_range:
                in_range_enemies.append(target)
                if self.action_menu:
                    self.action_menu.add_to_log(f"✓ {target.unit_type} в зоне досягаемости!")
        
        if in_range_enemies:
            # Attack the weakest enemy in range
            target = min(in_range_enemies, key=lambda enemy: enemy.health)
            damage = bot_unit.attack_unit(target)
            bot_unit.is_attacked = True
            
            if self.action_menu:
                self.action_menu.add_to_log(f"Бот атаковал {target.unit_type} и нанес {damage} урона!")
                # Обновляем список юнитов игрока после атаки бота
                self.action_menu.update_units_list(self.player_faction.units)
            
            # Check if target was destroyed
            if target.health <= 0:
                grid_x = target.rect.x // self.grid_size
                grid_y = target.rect.y // self.grid_size
                self.grid[grid_y][grid_x] = None  # Очищаем клетку
                self.player_faction.remove_unit(target)
                if self.action_menu:
                    self.action_menu.add_to_log(f"❌ Юнит игрока {target.unit_type} уничтожен!")
                    # Обновляем список юнитов после уничтожения
                    self.action_menu.update_units_list(self.player_faction.units)
                    
                # Check victory condition
                if not self.player_faction.has_units():
                    self.state = "game_over"
                    if self.action_menu:
                        self.action_menu.add_to_log("Игра окончена! Победитель: Bot")
        else:
            if self.action_menu:
                self.action_menu.add_to_log("🤖 Нет целей в зоне досягаемости для атаки бота")
            bot_unit.is_attacked = True  # Skip attack if no targets
    
    def roll_dice_for_phase(self):
        if self.state in ["player1_turn", "player2_turn"] and self.current_phase is not None:
            # Roll a dice (1-6)
            self.dice_roll = random.randint(1, 6)
            
            if self.action_menu:
                self.action_menu.add_to_log(f"🎲 {self.current_faction.name} выбросил {self.dice_roll} на фазе {self.current_phase}")
            
            # Apply phase effects based on dice roll
            if self.current_phase == "Movement":
                self.apply_movement_effects(self.dice_roll)
            elif self.current_phase == "Attack":
                self.apply_attack_effects(self.dice_roll)
            elif self.current_phase == "Morale":
                self.apply_morale_effects(self.dice_roll)
            
            self.phase_roll_complete = True
            
            # Move to the next phase if it's bot's turn
            if self.state == "player2_turn":
                self.proceed_to_next_phase()
            
            self.update_action_menu()
    
    def apply_movement_effects(self, dice_roll):
        # Modifier based on dice roll
        movement_modifier = max(-1, (dice_roll - 3) / 3)  # -1 to +1 range
        
        for unit in self.current_faction.units:
            original_range = unit.movement_range
            unit.movement_range = max(1, int(original_range * (1 + movement_modifier)))
            
        if self.action_menu:
            if movement_modifier > 0:
                self.action_menu.add_to_log(f"Удача! Движение улучшено на {movement_modifier:.1f}x")
            elif movement_modifier < 0:
                self.action_menu.add_to_log(f"Неудача! Движение снижено на {abs(movement_modifier):.1f}x")
            else:
                self.action_menu.add_to_log("Нейтральный бросок. Движение без изменений.")
                
        # Если ход бота, вызываем функцию движения бота с модификатором
        if self.state == "player2_turn" and self.current_phase == "Movement":
            if self.action_menu:
                self.action_menu.add_to_log("Применяем модификатор движения для бота")
            
            # Находим доступные юниты для движения
            available_units = [unit for unit in self.bot_faction.units if not unit.is_moved]
            if available_units and len(self.player_faction.units) > 0:
                # Находим юнит противника, который ближе всего к любому из наших юнитов
                closest_enemy = None
                closest_unit = None
                min_distance = float('inf')
                
                for bot_unit in available_units:
                    for player_unit in self.player_faction.units:
                        distance = ((bot_unit.rect.x - player_unit.rect.x) ** 2 + 
                                    (bot_unit.rect.y - player_unit.rect.y) ** 2) ** 0.5
                        if distance < min_distance:
                            min_distance = distance
                            closest_enemy = player_unit
                            closest_unit = bot_unit
                
                if closest_unit and closest_enemy:
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Выбран {closest_unit.unit_type} для движения к {closest_enemy.unit_type}")
                    self.process_bot_movement(closest_unit, [closest_enemy])
    
    def apply_attack_effects(self, dice_roll):
        # Modifier based on dice roll
        attack_modifier = max(-0.5, (dice_roll - 3) / 6)  # -0.5 to +0.5 range
        
        for unit in self.current_faction.units:
            original_attack = unit.attack
            unit.attack = max(5, int(original_attack * (1 + attack_modifier)))
            
        if self.action_menu:
            if attack_modifier > 0:
                self.action_menu.add_to_log(f"Удача! Атака улучшена на {attack_modifier:.1f}x")
            elif attack_modifier < 0:
                self.action_menu.add_to_log(f"Неудача! Атака снижена на {abs(attack_modifier):.1f}x")
            else:
                self.action_menu.add_to_log("Нейтральный бросок. Атака без изменений.")
                
        # Если ход бота, вызываем функцию атаки бота с модификатором
        if self.state == "player2_turn" and self.current_phase == "Attack":
            if self.action_menu:
                self.action_menu.add_to_log("Применяем модификатор атаки для бота")
            
            # Находим доступные юниты для атаки
            available_units = [unit for unit in self.bot_faction.units if not unit.is_attacked]
            
            if available_units and len(self.player_faction.units) > 0:
                # Проверяем для каждого юнита, находится ли противник в зоне досягаемости
                units_in_range = []
                
                for bot_unit in available_units:
                    for player_unit in self.player_faction.units:
                        bot_x = bot_unit.rect.x // self.grid_size
                        bot_y = bot_unit.rect.y // self.grid_size
                        player_x = player_unit.rect.x // self.grid_size
                        player_y = player_unit.rect.y // self.grid_size
                        
                        # Расстояние в клетках (Манхэттенская метрика)
                        distance = abs(bot_x - player_x) + abs(bot_y - player_y)
                        
                        if distance <= bot_unit.attack_range:
                            units_in_range.append((bot_unit, player_unit, distance, bot_unit.attack))
                
                # Если есть юниты, которые могут атаковать
                if units_in_range:
                    # Сортируем по атаке (сначала наиболее сильные)
                    units_in_range.sort(key=lambda x: (-x[3], x[2]))  # -атака (чтобы сначала шли большие значения), затем расстояние
                    
                    best_attack_unit, target_unit, attack_distance, _ = units_in_range[0]
                    
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Выбран {best_attack_unit.unit_type} для атаки {target_unit.unit_type} с расстояния {attack_distance}")
                    
                    # Передаем конкретную цель для атаки
                    self.process_bot_attack(best_attack_unit, [target_unit])
                else:
                    # Если никто не может атаковать, выбираем юнит с наибольшей атакой
                    best_attack_unit = max(available_units, key=lambda unit: unit.attack)
                    
                    if self.action_menu:
                        self.action_menu.add_to_log(f"Выбран {best_attack_unit.unit_type} для атаки, но нет целей в досягаемости")
                    
                    # Передаем все юниты игрока для проверки атаки
                    self.process_bot_attack(best_attack_unit, self.player_faction.units)
    
    def apply_morale_effects(self, dice_roll):
        # Morale effects (for example, could affect defense)
        morale_modifier = max(-0.3, (dice_roll - 3) / 10)  # -0.3 to +0.3 range
        
        for unit in self.current_faction.units:
            original_defense = unit.defense
            unit.defense = max(5, int(original_defense * (1 + morale_modifier)))
            
        if self.action_menu:
            if morale_modifier > 0:
                self.action_menu.add_to_log(f"Высокий боевой дух! Защита улучшена на {morale_modifier:.1f}x")
            elif morale_modifier < 0:
                self.action_menu.add_to_log(f"Низкий боевой дух! Защита снижена на {abs(morale_modifier):.1f}x")
            else:
                self.action_menu.add_to_log("Нейтральный боевой дух. Защита без изменений.")
    
    def start_turn_phases(self):
        # Start with the first phase
        self.current_phase_index = 0
        if len(self.phases) > 0:
            self.current_phase = self.phases[0]
            self.phase_roll_complete = False
            
            if self.action_menu:
                self.action_menu.add_to_log(f"Начинается фаза: {self.current_phase}")
                self.action_menu.update_info()
            
            # If it's bot's turn, automatically roll dice
            if self.state == "player2_turn":
                self.roll_dice_for_phase()
    
    def proceed_to_next_phase(self):
        # Move to the next phase
        self.current_phase_index += 1
        
        # Check if we've gone through all phases
        if self.current_phase_index >= len(self.phases):
            # End of all phases, end the turn
            self.current_phase = None
            self.current_phase_index = -1
            
            if self.action_menu:
                self.action_menu.add_to_log("Все фазы завершены. Ход переходит к следующему игроку.")
            
            self.end_turn()
        else:
            # Move to the next phase
            self.current_phase = self.phases[self.current_phase_index]
            self.phase_roll_complete = False
            
            if self.action_menu:
                self.action_menu.add_to_log(f"Начинается фаза: {self.current_phase}")
                self.action_menu.update_info()
            
            # If it's bot's turn, automatically roll dice
            if self.state == "player2_turn":
                self.roll_dice_for_phase()
    
    def update_action_menu(self):
        if self.action_menu:
            self.action_menu.update_button_states()
            self.action_menu.update_info()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec()) 