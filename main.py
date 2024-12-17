import pygame
from enum import Enum
from typing import List, Tuple

WINDOW_WIDTH = 1400
WINDOW_HEIGHT = 800
GRID_SIZE = 50
INFO_PANEL_WIDTH = 400

BACKGROUND = (255, 255, 255)  # Белый фон
GRID_COLOR = (200, 200, 200)  # Серый для сетки
AXIS_COLOR = (0, 0, 0)  # Черный для осей
WINDOW_COLOR = (200, 200, 255)  # Светло-голубой для окна отсечения
SHAPE_COLOR = (255, 165, 0)  # Оранжевый для рисуемых фигур
POLYGON_COLOR = (147, 112, 219)  # Светло-фиолетовый для многоугольников
CLIPPED_COLOR = (0, 255, 127)  # Зеленый для отсеченных фигур
TEXT_COLOR = (0, 0, 0)  # Черный для текста

class Mode(Enum):
    LINE = 1
    POLYGON = 2


class State(Enum):
    DRAWING = 1
    WINDOW_CREATION = 2


class App:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Алгоритм средней точки")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)

        self.mode = Mode.LINE
        self.state = State.DRAWING
        self.temp_point = None
        self.current_line = []
        self.current_polygon = []
        self.shapes = []
        self.clipping_window = None
        self.window_start = None
        self.clipped_shapes = []
        self.show_grid = True
        self.creating_window = False
        self.window_mode = False

    def draw_grid(self):
        if not self.show_grid:
            return

        for x in range(0, WINDOW_WIDTH - INFO_PANEL_WIDTH, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (x, 0), (x, WINDOW_HEIGHT))
        for y in range(0, WINDOW_HEIGHT, GRID_SIZE):
            pygame.draw.line(self.screen, GRID_COLOR, (0, y), (WINDOW_WIDTH - INFO_PANEL_WIDTH, y))

        mid_x = (WINDOW_WIDTH - INFO_PANEL_WIDTH) // 2
        mid_y = WINDOW_HEIGHT // 2
        pygame.draw.line(self.screen, AXIS_COLOR, (0, mid_y), (WINDOW_WIDTH - INFO_PANEL_WIDTH, mid_y), 3)
        pygame.draw.line(self.screen, AXIS_COLOR, (mid_x, 0), (mid_x, WINDOW_HEIGHT), 3)

        for i in range(-10, 11):
            if i != 0:
                x_pos = mid_x + (i * GRID_SIZE)
                label = self.font.render(str(i), True, TEXT_COLOR)
                self.screen.blit(label, (x_pos - 10, mid_y + 10))

                y_pos = mid_y - (i * GRID_SIZE)
                label = self.font.render(str(i), True, TEXT_COLOR)
                self.screen.blit(label, (mid_x + 10, y_pos - 10))

    def draw_info_panel(self):
        panel_rect = pygame.Rect(WINDOW_WIDTH - INFO_PANEL_WIDTH, 0, INFO_PANEL_WIDTH, WINDOW_HEIGHT)
        pygame.draw.rect(self.screen, (230, 230, 250), panel_rect)  # Светло-фиолетовый фон
        pygame.draw.line(self.screen, (180, 180, 180), (WINDOW_WIDTH - INFO_PANEL_WIDTH, 0),
                         (WINDOW_WIDTH - INFO_PANEL_WIDTH, WINDOW_HEIGHT), 3)  # Граница панели

        # Заголовок
        header_font = pygame.font.Font(None, 32)  # Больший шрифт
        subheader_font = pygame.font.Font(None, 28)  # Чуть больше, чем обычный текст
        label_font = pygame.font.Font(None, 24)  # Стандартный текст

        header_text = header_font.render("ИНФОРМАЦИЯ", True, (0, 0, 0))
        self.screen.blit(header_text, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 20, 10))

        # Секция режима
        mode_surface = subheader_font.render("Режим:", True, (0, 0, 0))
        self.screen.blit(mode_surface, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 20, 60))

        mode_value = f" {'Многоугольник' if self.mode == Mode.POLYGON else 'Линия'}"
        mode_text = label_font.render(mode_value, True, (50, 50, 150))
        self.screen.blit(mode_text, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 120, 60))

        # Секция состояния
        state_surface = subheader_font.render("Состояние:", True, (0, 0, 0))
        self.screen.blit(state_surface, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 20, 100))

        state_value = f" {'Рисование' if self.state == State.DRAWING else 'Создание окна'}"
        state_text = label_font.render(state_value, True, (50, 50, 150))
        self.screen.blit(state_text, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 140, 100))

        # Секция управления
        controls_title = subheader_font.render("Управление:", True, (0, 0, 0))
        self.screen.blit(controls_title, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 20, 150))

        controls = [
            ("M", "Сменить режим"),
            ("W", "Вкл/выкл режим окна"),
            ("Enter", "Произвести отсечение"),
            ("Backspace", "Удалить последнюю точку"),
            ("Delete", "Удалить последнюю фигуру"),
            ("C", "Убрать окно отсечения"),
            ("ESC", "Очистить всё"),
        ]

        y_offset = 200  # Стартовая позиция для управления
        for key, description in controls:
            key_surface = label_font.render(f"{key}:", True, (0, 0, 0))
            description_surface = label_font.render(description, True, (60, 60, 60))
            self.screen.blit(key_surface, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 20, y_offset))
            self.screen.blit(description_surface, (WINDOW_WIDTH - INFO_PANEL_WIDTH + 80, y_offset))
            y_offset += 40  # Увеличенный шаг между строками

    def draw_line(self, x1: int, y1: int, x2: int, y2: int):
        """
        Алгоритм Брезенхэма для рисования прямой линии.
        """
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy

        while True:
            pygame.draw.circle(self.screen, SHAPE_COLOR, (x1, y1), 1)
            if x1 == x2 and y1 == y2:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def handle_mouse_click(self, pos):
        x, y = pos
        if x >= WINDOW_WIDTH - INFO_PANEL_WIDTH:
            return

        if self.window_mode and not self.creating_window:
            self.window_start = pos
            self.creating_window = True
            self.state = State.WINDOW_CREATION
            return

        if self.state == State.DRAWING:
            if self.mode == Mode.LINE:
                if not self.current_line:
                    self.current_line = [pos]
                else:
                    self.current_line.append(pos)
                    self.shapes.append(self.current_line)
                    self.current_line = []
            else:
                self.current_polygon.append(pos)

    def handle_mouse_up(self, pos):
        if self.creating_window and self.window_start:
            x, y = pos
            x1, y1 = self.window_start
            if x < WINDOW_WIDTH - INFO_PANEL_WIDTH:
                self.clipping_window = (min(x1, x), min(y1, y), max(x1, x), max(y1, y))
                self.clipped_shapes = []
                self.creating_window = False
                self.window_start = None

    def run(self):
        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_m and self.state == State.DRAWING:
                        self.mode = Mode.POLYGON if self.mode == Mode.LINE else Mode.LINE
                        self.current_line = []
                        self.current_polygon = []
                    elif event.key == pygame.K_w:
                        self.window_mode = not self.window_mode
                        if not self.window_mode:
                            self.creating_window = False
                            self.window_start = None
                            self.state = State.DRAWING
                    elif event.key == pygame.K_SPACE and self.mode == Mode.POLYGON:
                        if len(self.current_polygon) == 2:
                            self.shapes.append(self.current_polygon)
                            self.current_polygon = []
                        elif len(self.current_polygon) > 2:
                            self.shapes.append(self.current_polygon)
                            self.current_polygon = []
                    elif event.key == pygame.K_RETURN and self.clipping_window:
                        self.clip_shapes()
                    elif event.key == pygame.K_BACKSPACE:
                        if self.current_polygon:
                            self.current_polygon.pop()
                    elif event.key == pygame.K_DELETE:
                        if self.shapes:
                            self.shapes.pop()
                    elif event.key == pygame.K_c:
                        self.clipping_window = None
                        self.clipped_shapes = []
                        self.state = State.DRAWING
                    elif event.key == pygame.K_g:
                        self.show_grid = not self.show_grid
                    elif event.key == pygame.K_ESCAPE:
                        self.shapes = []
                        self.current_line = []
                        self.current_polygon = []
                        self.clipped_shapes = []
                        self.clipping_window = None
                        self.state = State.DRAWING
                        self.creating_window = False
                        self.window_mode = False
                        self.window_start = None

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        self.handle_mouse_click(event.pos)

                elif event.type == pygame.MOUSEBUTTONUP:
                    if event.button == 1:
                        self.handle_mouse_up(event.pos)

            self.screen.fill(BACKGROUND)
            self.draw_grid()

            if self.clipping_window:
                x, y, w, h = self.clipping_window
                window_rect = pygame.Rect(x, y, w - x, h - y)
                pygame.draw.rect(self.screen, WINDOW_COLOR, window_rect)
                pygame.draw.rect(self.screen, AXIS_COLOR, window_rect, 3)

            if self.creating_window and self.window_start:
                mouse_pos = pygame.mouse.get_pos()
                if mouse_pos[0] < WINDOW_WIDTH - INFO_PANEL_WIDTH:
                    x1, y1 = self.window_start
                    x2, y2 = mouse_pos
                    rect = pygame.Rect(
                        min(x1, x2),
                        min(y1, y2),
                        abs(x2 - x1),
                        abs(y2 - y1)
                    )
                    pygame.draw.rect(self.screen, WINDOW_COLOR, rect)
                    pygame.draw.rect(self.screen, AXIS_COLOR, rect, 3)

            for shape in self.shapes:
                color = POLYGON_COLOR if len(shape) > 2 else SHAPE_COLOR
                pygame.draw.lines(self.screen, color,
                                  len(shape) > 2, shape, 4)

            if self.current_line:
                self.draw_line(self.current_line[0][0], self.current_line[0][1],
                               pygame.mouse.get_pos()[0], pygame.mouse.get_pos()[1])

            if self.current_polygon:
                points = self.current_polygon + [pygame.mouse.get_pos()]
                pygame.draw.lines(self.screen, POLYGON_COLOR, False,
                                  points, 4)
                for point in self.current_polygon:
                    pygame.draw.circle(self.screen, POLYGON_COLOR, point, 4)

            for shape in self.clipped_shapes:
                pygame.draw.lines(self.screen, CLIPPED_COLOR,
                                  len(shape) > 2, shape, 4)

            self.draw_info_panel()
            pygame.display.flip()
            self.clock.tick(60)

        pygame.quit()


if __name__ == "__main__":
    app = App()
    app.run()
