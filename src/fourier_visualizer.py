import pygame
import json
import os
import math
from typing import List, Tuple
from fourier_math import FourierSeries, Epicycle


class Slider:  
    def __init__(self, x: float, y: float, width: float, min_val: int, 
                 max_val: int, initial_val: int, label: str = ""):
        self.x = x
        self.y = y
        self.width = width
        self.min_val = min_val
        self.max_val = max_val
        self.value = initial_val
        self.label = label
        self.dragging = False
        self.height = 10
        self.knob_radius = 8
        
    def draw(self, screen: pygame.Surface, config: dict) -> None:
        pygame.draw.rect(screen, config['colors']['ui_border'], 
                        (self.x, self.y, self.width, self.height))
        ratio = (self.value - self.min_val) / (self.max_val - self.min_val)
        knob_x = self.x + ratio * self.width
        pygame.draw.circle(screen, config['colors']['epicycle'], 
                          (int(knob_x), int(self.y + self.height // 2)), 
                          self.knob_radius)
        font = pygame.font.Font(None, config['fonts']['label_size'])
        text = font.render(f"{self.label}: {self.value}", True, 
                          config['colors']['text'])
        screen.blit(text, (self.x, self.y - 25))
    
    def handle_mouse(self, pos: Tuple[int, int], pressed: bool) -> bool:
        mouse_x, mouse_y = pos
        
        if pressed:
            if abs(mouse_y - (self.y + self.height // 2)) < self.knob_radius + 5:
                if self.x <= mouse_x <= self.x + self.width:
                    self.dragging = True
        else:
            self.dragging = False
        
        if self.dragging:
            ratio = (mouse_x - self.x) / self.width
            ratio = max(0, min(1, ratio))  
            new_value = int(self.min_val + ratio * (self.max_val - self.min_val))
            
            if new_value != self.value:
                self.value = new_value
                return True
        
        return False


class Button:
    def __init__(self, x: float, y: float, width: float, height: float, 
                 label: str = ""):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.label = label
        self.hovered = False
        
    def draw(self, screen: pygame.Surface, config: dict) -> None:
        color = config['colors']['epicycle'] if self.hovered else config['colors']['ui_border']
        pygame.draw.rect(screen, color, (self.x, self.y, self.width, self.height))
        
        font = pygame.font.Font(None, config['fonts']['label_size'])
        text = font.render(self.label, True, config['colors']['text'])
        text_rect = text.get_rect(center=(self.x + self.width // 2, 
                                         self.y + self.height // 2))
        screen.blit(text, text_rect)
    
    def is_clicked(self, pos: Tuple[int, int]) -> bool:
        mouse_x, mouse_y = pos
        return (self.x <= mouse_x <= self.x + self.width and 
                self.y <= mouse_y <= self.y + self.height)
    
    def update_hover(self, pos: Tuple[int, int]) -> None:
        mouse_x, mouse_y = pos
        self.hovered = (self.x <= mouse_x <= self.x + self.width and 
                       self.y <= mouse_y <= self.y + self.height)


class FourierVisualizer:
    def __init__(self, config_path: str = "config/config.json"):
        with open(config_path, 'r') as f:
            self.config = json.load(f)
        pygame.init()
        self.screen = pygame.display.set_mode(
            (self.config['window']['width'], self.config['window']['height'])
        )
        pygame.display.set_caption(self.config['window']['title'])
        self.clock = pygame.time.Clock()
        self.running = True
        self.fourier = FourierSeries("rectangular")
        self.fourier.calculate_rectangular(self.config['fourier']['default_terms'])
        self.time = 0.0
        self.animation_speed = self.config['visualization']['animation_speed']
        self.paused = False
        self.trace_points: List[Tuple[float, float]] = []
        self.max_trace_length = self.config['visualization']['trace_length']
        self._init_ui_components()
        
    def _init_ui_components(self) -> None:
        self.slider_terms = Slider(
            x=50, y=50, width=200,
            min_val=self.config['fourier']['min_terms'],
            max_val=self.config['fourier']['max_terms'],
            initial_val=self.config['fourier']['default_terms'],
            label="Terms"
        )
        
        self.slider_speed = Slider(
            x=50, y=120, width=200,
            min_val=1, max_val=100,
            initial_val=50,
            label="Speed"
        )
        
        self.btn_rectangular = Button(50, 190, 90, 30, "Rectangular")
        self.btn_sawtooth = Button(150, 190, 90, 30, "Sawtooth")

        self.btn_pause = Button(50, 260, 90, 30, "Pause")
        self.btn_reset = Button(150, 260, 90, 30, "Reset")
        
    def handle_events(self) -> None:
        mouse_pos = pygame.mouse.get_pos()
        mouse_pressed = pygame.mouse.get_pressed()[0]

        self.btn_rectangular.update_hover(mouse_pos)
        self.btn_sawtooth.update_hover(mouse_pos)
        self.btn_pause.update_hover(mouse_pos)
        self.btn_reset.update_hover(mouse_pos)
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if self.slider_terms.handle_mouse(mouse_pos, True):
                    self._update_terms(self.slider_terms.value)
                
                if self.slider_speed.handle_mouse(mouse_pos, True):
                    self._update_speed(self.slider_speed.value)

                if self.btn_rectangular.is_clicked(mouse_pos):
                    self._switch_function("rectangular")
                
                if self.btn_sawtooth.is_clicked(mouse_pos):
                    self._switch_function("sawtooth")
                
                if self.btn_pause.is_clicked(mouse_pos):
                    self.paused = not self.paused
                
                if self.btn_reset.is_clicked(mouse_pos):
                    self._reset_animation()
            
            elif event.type == pygame.MOUSEBUTTONUP:
                self.slider_terms.handle_mouse(mouse_pos, False)
                self.slider_speed.handle_mouse(mouse_pos, False)
            
            elif event.type == pygame.MOUSEMOTION:
                if self.slider_terms.dragging:
                    if self.slider_terms.handle_mouse(mouse_pos, True):
                        self._update_terms(self.slider_terms.value)
                
                if self.slider_speed.dragging:
                    if self.slider_speed.handle_mouse(mouse_pos, True):
                        self._update_speed(self.slider_speed.value)
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self._reset_animation()
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def _update_terms(self, num_terms: int) -> None:
        if self.fourier.function_type == "rectangular":
            self.fourier.calculate_rectangular(num_terms)
        else:
            self.fourier.calculate_sawtooth(num_terms)
    
    def _update_speed(self, speed_value: int) -> None:
        self.animation_speed = speed_value / 2500.0
    
    def _switch_function(self, func_type: str) -> None:
        self.fourier.set_function_type(func_type)
        self._reset_animation()
    
    def _reset_animation(self) -> None:
        self.time = 0.0
        self.trace_points = []
        self.paused = False
    
    def update(self) -> None:
        if not self.paused:
            self.time += self.animation_speed
            
            if self.time >= 2 * math.pi:
                self.time -= 2 * math.pi
                self.trace_points = []  
            
            self.fourier.update(self.time)
            
            center_x = self.config['window']['width'] // 2
            center_y = self.config['window']['height'] // 2
            scale = self.config['visualization']['epicycle_scale']
            
            final_point = self.fourier.get_final_point(center_x, center_y, scale)
            self.trace_points.append(final_point)
            
            # Limit trace length
            if len(self.trace_points) > self.max_trace_length:
                self.trace_points.pop(0)
    
    def draw(self) -> None:
        self.screen.fill(self.config['colors']['background'])

        if self.config['visualization']['grid_enabled']:
            self._draw_grid()
        
        self._draw_epicycles()
        self._draw_trace()
        self._draw_function_comparison()
        
        self._draw_ui()

        pygame.display.flip()
    
    def _draw_grid(self) -> None:
        grid_spacing = 50
        width = self.config['window']['width']
        height = self.config['window']['height']
        
        for x in range(0, width, grid_spacing):
            pygame.draw.line(self.screen, self.config['colors']['grid'], 
                           (x, 0), (x, height), 1)
        
        for y in range(0, height, grid_spacing):
            pygame.draw.line(self.screen, self.config['colors']['grid'], 
                           (0, y), (width, y), 1)
    
    def _draw_epicycles(self) -> None:
        center_x = self.config['window']['width'] // 2
        center_y = self.config['window']['height'] // 2
        scale = self.config['visualization']['epicycle_scale']
        
        points = self.fourier.get_epicycle_points(center_x, center_y, scale)
        
        for i in range(len(points) - 1):
            x1, y1 = points[i]
            x2, y2 = points[i + 1]
            
            radius = self.fourier.epicycles[i].amplitude * scale
            pygame.draw.circle(self.screen, self.config['colors']['epicycle'], 
                             (int(x1), int(y1)), int(radius), 1)
            
            pygame.draw.line(self.screen, self.config['colors']['epicycle'], 
                           (int(x1), int(y1)), (int(x2), int(y2)), 2)
        
        final_x, final_y = points[-1]
        pygame.draw.circle(self.screen, self.config['colors']['trace'], 
                         (int(final_x), int(final_y)), 5)
    
    def _draw_trace(self) -> None:
        if len(self.trace_points) > 1:
            for i in range(len(self.trace_points) - 1):
                x1, y1 = self.trace_points[i]
                x2, y2 = self.trace_points[i + 1]
                pygame.draw.line(self.screen, self.config['colors']['trace'], 
                               (int(x1), int(y1)), (int(x2), int(y2)), 2)
    
    def _draw_function_comparison(self) -> None:
        font = pygame.font.Font(None, self.config['fonts']['value_size'])
        
        approx_val = self.fourier.get_approximation_value()
        true_val = self.fourier.get_true_value()
        error = self.fourier.get_error()

        info_texts = [
            f"Function: {self.fourier.function_type.capitalize()}",
            f"Terms: {self.fourier.max_terms}",
            f"Time: {self.time:.2f}",
            f"Approx: {approx_val:.3f}",
            f"True: {true_val:.3f}",
            f"Error: {error:.6f}",
            f"Status: {'PAUSED' if self.paused else 'PLAYING'}"
        ]
        
        y_offset = self.config['window']['height'] - 200
        for i, text in enumerate(info_texts):
            rendered = font.render(text, True, self.config['colors']['text'])
            self.screen.blit(rendered, (20, y_offset + i * 25))
    
    def _draw_ui(self) -> None:
        self.slider_terms.draw(self.screen, self.config)
        self.slider_speed.draw(self.screen, self.config)
        
        self.btn_rectangular.draw(self.screen, self.config)
        self.btn_sawtooth.draw(self.screen, self.config)
        
        self.btn_pause.draw(self.screen, self.config)
        self.btn_reset.draw(self.screen, self.config)
        
        font = pygame.font.Font(None, self.config['fonts']['label_size'])
        help_text = font.render("SPACE: Pause/Play | R: Reset | ESC: Exit", True, 
                               self.config['colors']['text'])
        self.screen.blit(help_text, (50, self.config['window']['height'] - 30))
    
    def run(self) -> None:
        while self.running:
            self.handle_events()
            self.update()
            self.draw()
            self.clock.tick(self.config['window']['fps'])
        
        pygame.quit()


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(os.path.dirname(script_dir))
    
    visualizer = FourierVisualizer()
    visualizer.run()


if __name__ == "__main__":
    main()
