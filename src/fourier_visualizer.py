import pygame
import math
import random
import json
import os

class Button:
    def __init__(self, x, y, width, height, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.hovered = False

    def draw(self, screen):
        color = (180, 180, 230) if self.hovered else (80, 80, 130)
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        font = pygame.font.SysFont("Arial", 28)
        txt = font.render(self.label, True, (255,255,255))
        screen.blit(txt, (self.x + 15, self.y + 5))

    def is_clicked(self, pos):
        x, y = pos
        return self.x <= x <= self.x + self.width and self.y <= y <= self.y + self.height

    def update_hover(self, pos):
        self.hovered = self.is_clicked(pos)

class Slider:
    def __init__(self, x, y, width, min_val, max_val, initial_val, label=""):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False

    def draw(self, screen):
        font = pygame.font.SysFont("Arial", 24)
        txt = font.render(f"{self.label}: {int(self.value)}", True, (255,255,255))
        screen.blit(txt, (self.x, self.y - 30))
        pygame.draw.rect(screen, (60, 60, 90), (self.x, self.y, self.width, 8))
        pos = self.x + int((self.value - self.min_val) / (self.max_val - self.min_val) * self.width)
        pygame.draw.circle(screen, (230, 230, 255), (pos, self.y + 4), 12)

    def handle_mouse(self, pos, pressed):
        if pressed and self.x <= pos[0] <= self.x + self.width and self.y <= pos[1] <= self.y + 16:
            self.dragging = True
        if not pressed:
            self.dragging = False
        if self.dragging:
            rel = max(0, min(pos[0]-self.x, self.width))
            val = self.min_val + (rel / self.width) * (self.max_val - self.min_val)
            self.value = round(val)

class FourierSeries:
    def __init__(self, func_type="rectangular"):
        self.func_type = func_type
        self.epicycles = []
        self.time = 0

    def calculate_rectangular(self, num_terms):
        self.epicycles = []
        for n in range(1, num_terms+1):
            harmonic = 2*n - 1
            amplitude = (4.0 / math.pi) * (1.0 / harmonic)
            self.epicycles.append({"frequency": harmonic, "amplitude": amplitude, "phase": 0.0, "angle": 0.0})

    def calculate_sawtooth(self, num_terms):
        self.epicycles = []
        for n in range(1, num_terms+1):
            sign = 1 if (n%2 == 1) else -1
            amplitude = abs((2.0 / math.pi) * sign * (1.0 / n))
            phase = 0.0 if sign > 0 else math.pi
            self.epicycles.append({"frequency": n, "amplitude": amplitude, "phase": phase, "angle": 0.0})

    def update(self, time):
        self.time = time
        for epi in self.epicycles:
            epi["angle"] = epi["frequency"] * time + epi["phase"]

    def get_epicycle_points(self, center_x, center_y, scale=1.0):
        points = [(center_x, center_y)]
        x, y = center_x, center_y
        for epi in self.epicycles:
            radius = epi["amplitude"] * scale
            x += radius * math.cos(epi["angle"])
            y += radius * math.sin(epi["angle"])
            points.append((x, y))
        return points

    def get_final_point(self, center_x, center_y, scale=1.0):
        pts = self.get_epicycle_points(center_x, center_y, scale)
        return pts[-1]

class FourierVisualizer:
    def __init__(self, config_path="config/config.json"):
        if not os.path.exists(config_path):
            raise RuntimeError("config.json not found!")
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = json.load(f)

        win_cfg = self.config['window']
        pygame.init()
        pygame.display.set_caption(win_cfg.get('title', "Fourier Series Visualization"))
        self.screen = pygame.display.set_mode((win_cfg['width'], win_cfg['height']))
        self.clock = pygame.time.Clock()
        self.running = True
        self.paused = False
        self.time = 0
        self.trace_points = []
        self.function_type = "rectangular"
        self.fourier = FourierSeries(self.function_type)
        self.fourier.calculate_rectangular(self.config['fourier']['default_terms'])

        self.slider_terms = Slider(
            30, win_cfg['height'] - 150, 300,
            self.config['fourier']['min_terms'], self.config['fourier']['max_terms'],
            self.config['fourier']['default_terms'], label="Terms"
        )
        self.slider_speed = Slider(
            30, win_cfg['height'] - 90, 300,
            1, 100, int(self.config['visualization']['animation_speed'] * 1000),
            label="Speed"
        )
        self.btn_rectangular = Button(370, win_cfg['height'] - 150, 170, 48, "Rectangular")
        self.btn_sawtooth = Button(560, win_cfg['height'] - 150, 170, 48, "Sawtooth")
        self.btn_pause = Button(760, win_cfg['height'] - 150, 100, 48, "Pause")
        self.btn_reset = Button(880, win_cfg['height'] - 150, 110, 48, "Reset")

    def _switch_function(self, func):
        self.function_type = func
        if func == "rectangular":
            self.fourier.calculate_rectangular(int(self.slider_terms.value))
        elif func == "sawtooth":
            self.fourier.calculate_sawtooth(int(self.slider_terms.value))

    def _reset_animation(self):
        self.time = 0
        self.trace_points = []

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                if self.btn_rectangular.is_clicked(pos):
                    self._switch_function("rectangular")
                if self.btn_sawtooth.is_clicked(pos):
                    self._switch_function("sawtooth")
                if self.btn_pause.is_clicked(pos):
                    self.paused = not self.paused
                if self.btn_reset.is_clicked(pos):
                    self._reset_animation()
                self.slider_terms.handle_mouse(pos, True)
                self.slider_speed.handle_mouse(pos, True)
            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                self.slider_terms.handle_mouse(pos, False)
                self.slider_speed.handle_mouse(pos, False)
            elif event.type == pygame.MOUSEMOTION:
                pos = pygame.mouse.get_pos()
                self.btn_rectangular.update_hover(pos)
                self.btn_sawtooth.update_hover(pos)
                self.btn_pause.update_hover(pos)
                self.btn_reset.update_hover(pos)
                self.slider_terms.handle_mouse(pos, pygame.mouse.get_pressed()[0])
                self.slider_speed.handle_mouse(pos, pygame.mouse.get_pressed()[0])
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self._reset_animation()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False

    def update(self):
        if not self.paused:
            self.time += self.slider_speed.value * 0.001
            self.fourier.update(self.time)
            final_point = self.fourier.get_final_point(
                self.config['window']['width'] // 3, self.config['window']['height'] // 2,
                self.config['visualization']['epicycle_scale'])
            if len(self.trace_points) < self.config['visualization']['trace_length']:
                self.trace_points.append(final_point)
            else:
                self.trace_points.pop(0)
                self.trace_points.append(final_point)
            if self.time >= 2 * math.pi:
                self.time = 0
                self.trace_points = []

    def _draw_grid(self):
        grid_color = (40,40,60)
        for x in range(0, self.config['window']['width'], 50):
            pygame.draw.line(self.screen, grid_color, (x,0), (x,self.config['window']['height']), 1)
        for y in range(0, self.config['window']['height'], 50):
            pygame.draw.line(self.screen, grid_color, (0,y), (self.config['window']['width'], y), 1)

    def _draw_epicycles(self):
        pts = self.fourier.get_epicycle_points(
            self.config['window']['width'] // 3,
            self.config['window']['height'] // 2,
            self.config['visualization']['epicycle_scale'])
        color = tuple(self.config['colors']['epicycle'])
        for i in range(len(pts)-1):
            x1, y1 = pts[i]
            x2, y2 = pts[i+1]
            radius = self.fourier.epicycles[i]["amplitude"] * self.config['visualization']['epicycle_scale']
            pygame.draw.circle(self.screen, color, (int(x1), int(y1)), int(radius), 1)
            pygame.draw.line(self.screen, color, (int(x1), int(y1)), (int(x2), int(y2)), 2)

    def _draw_trace(self):
        trace_color = tuple(self.config['colors']['trace'])
        if len(self.trace_points) > 1:
            for i in range(len(self.trace_points)-1):
                pygame.draw.line(self.screen, trace_color, self.trace_points[i], self.trace_points[i+1], 2)

    def _draw_ui(self):
        text_color = tuple(self.config['colors']['text'])
        self.slider_terms.draw(self.screen)
        self.slider_speed.draw(self.screen)
        self.btn_rectangular.draw(self.screen)
        self.btn_sawtooth.draw(self.screen)
        self.btn_pause.draw(self.screen)
        self.btn_reset.draw(self.screen)
        font = pygame.font.SysFont("Arial", 28)
        info = f"Function: {self.function_type}  |  t: {self.time:.2f} rad  |  Terms: {int(self.slider_terms.value)}"
        txt = font.render(info, True, text_color)
        self.screen.blit(txt, (30, 30))

    def _draw_ecg(self):
        win_cfg = self.config['window']
        start_x = win_cfg['width'] - 480
        start_y = win_cfg['height']//2 + 220
        points = []
        amplitude = 35
        length = 430
        step = 5
        x = start_x
        for i in range(0, length, step):
            if 30 < i < 50:
                y = start_y - amplitude * 0.25 - random.randint(0,5)
            elif 90 < i < 130:
                y = start_y - amplitude * 0.7 - random.randint(0,10)
            elif 145 < i < 170:
                y = start_y + amplitude * 0.7 + random.randint(0,10)
            elif 210 < i < 235:
                y = start_y - amplitude * 0.5 - random.randint(0,5)
            else:
                y = start_y + random.randint(-7, 7)
            points.append((x + i, y))
        for i in range(len(points) - 1):
            pygame.draw.line(self.screen, (0,235,60), points[i], points[i+1], 3)
        font = pygame.font.SysFont("Arial", 22)
        txt = font.render("ECG (кардиограмма)", True, (80,255,140))
        self.screen.blit(txt, (start_x, start_y - 56))

    def draw(self):
        self.screen.fill(tuple(self.config['colors']['background']))
        if self.config['visualization']['grid_enabled']:
            self._draw_grid()
        self._draw_epicycles()
        self._draw_trace()
        self._draw_ui()
        self._draw_ecg()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            if int(self.slider_terms.value) != len(self.fourier.epicycles):
                if self.function_type == "rectangular":
                    self.fourier.calculate_rectangular(int(self.slider_terms.value))
                else:
                    self.fourier.calculate_sawtooth(int(self.slider_terms.value))
            self.update()
            self.draw()
            self.clock.tick(self.config['window'].get('fps', 60))  # 60 FPS или из json
        pygame.quit()

if __name__ == "__main__":
    FourierVisualizer().run()
