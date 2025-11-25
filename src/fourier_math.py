import math
from typing import List, Tuple
from dataclasses import dataclass


@dataclass
class Epicycle:
    frequency: int
    amplitude: float
    phase: float = 0.0
    angle: float = 0.0


class FourierSeries:  
    def __init__(self, function_type: str = "rectangular"):
        self.function_type = function_type
        self.epicycles: List[Epicycle] = []
        self.time = 0.0
        self.max_terms = 10
        
    def calculate_rectangular(self, num_terms: int) -> List[Epicycle]:
        epicycles = []
        for n in range(1, num_terms + 1):
            harmonic = 2 * n - 1 
            amplitude = (4.0 / math.pi) * (1.0 / harmonic)
            
            epicycles.append(Epicycle(
                frequency=harmonic,
                amplitude=amplitude,
                phase=0.0
            ))
        
        self.epicycles = epicycles
        self.max_terms = num_terms
        return epicycles
    
    def calculate_sawtooth(self, num_terms: int) -> List[Epicycle]:
        epicycles = []
        for n in range(1, num_terms + 1):
            sign = 1 if (n % 2 == 1) else -1
            amplitude = abs((2.0 / math.pi) * sign * (1.0 / n))
            phase = 0.0 if sign > 0 else math.pi
            
            epicycles.append(Epicycle(
                frequency=n,
                amplitude=amplitude,
                phase=phase
            ))
        
        self.epicycles = epicycles
        self.max_terms = num_terms
        return epicycles
    
    def update(self, time: float) -> None:
        self.time = time
        for epicycle in self.epicycles:
            epicycle.angle = epicycle.frequency * time + epicycle.phase
    
    def get_epicycle_points(self, center_x: float, center_y: float, 
                           scale: float = 1.0) -> List[Tuple[float, float]]:
        points = [(center_x, center_y)]
        current_x = center_x
        current_y = center_y
        
        for epicycle in self.epicycles:
            radius = epicycle.amplitude * scale
            current_x += radius * math.cos(epicycle.angle)
            current_y += radius * math.sin(epicycle.angle)
            points.append((current_x, current_y))
        
        return points
    
    def get_final_point(self, center_x: float, center_y: float, 
                       scale: float = 1.0) -> Tuple[float, float]:
        points = self.get_epicycle_points(center_x, center_y, scale)
        return points[-1]
    
    def get_approximation_value(self) -> float:
        total = 0.0
        for epicycle in self.epicycles:
            total += epicycle.amplitude * math.sin(epicycle.angle)
        return total
    
    def get_true_value(self) -> float:
        if self.function_type == "rectangular":
            return self._rectangular_wave(self.time)
        elif self.function_type == "sawtooth":
            return self._sawtooth_wave(self.time)
        return 0.0
    
    @staticmethod
    def _rectangular_wave(t: float) -> float:
        normalized = ((t % (2 * math.pi)) + 2 * math.pi) % (2 * math.pi)
        return 1.0 if normalized < math.pi else -1.0
    
    @staticmethod
    def _sawtooth_wave(t: float) -> float:
        normalized = ((t % (2 * math.pi)) + 2 * math.pi) % (2 * math.pi)
        return -1.0 + (2.0 * normalized) / (2 * math.pi)
    
    def get_error(self) -> float:
        true_val = self.get_true_value()
        approx_val = self.get_approximation_value()
        return (true_val - approx_val) ** 2
    
    def set_function_type(self, function_type: str) -> None:
        self.function_type = function_type
        if function_type == "rectangular":
            self.calculate_rectangular(self.max_terms)
        elif function_type == "sawtooth":
            self.calculate_sawtooth(self.max_terms)
