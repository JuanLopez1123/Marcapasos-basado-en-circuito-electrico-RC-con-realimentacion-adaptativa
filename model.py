# model.py
import numpy as np
import pandas as pd

def single_pulse(V0, R, C, t_max=0.05, num_points=200):
    """
    Simula un solo pulso de descarga del marcapasos.
    
    Parámetros:
    -----------
    V0 : float
        Voltaje inicial del capacitor (V)
    R : float
        Resistencia del tejido cardíaco (Ω)
    C : float
        Capacitancia del marcapasos (F)
    t_max : float
        Tiempo máximo de simulación (s)
    num_points : int
        Número de puntos de la simulación
        
    Retorna:
    --------
    t : array
        Vector de tiempo
    Vc : array
        Voltaje del capacitor en función del tiempo
    """
    tau = R * C  # Constante de tiempo del circuito RC
    t = np.linspace(0, t_max, num_points)
    Vc = V0 * np.exp(-t / tau)  # Solución analítica de la ecuación diferencial
    return t, Vc

def adaptive_feedback(V0_target, R, C, V_min=1.0):
    """
    Sistema de realimentación adaptativa para ajustar el voltaje inicial.
    
    Garantiza que el voltaje en t = τ sea mayor o igual a V_min.
    En t = τ, V(τ) = V0 * e^(-1) = V0 * 0.368
    
    Para que V(τ) >= V_min:
    V0 * 0.368 >= V_min
    V0 >= V_min / 0.368 = V_min * e
    
    Parámetros:
    -----------
    V0_target : float
        Voltaje inicial deseado por el usuario
    R : float
        Resistencia actual del tejido
    C : float
        Capacitancia del sistema
    V_min : float
        Voltaje mínimo requerido para estimulación efectiva
        
    Retorna:
    --------
    float
        Voltaje inicial ajustado para garantizar estimulación efectiva
    """
    V0_min_required = V_min * np.exp(1)  # V0 mínimo para cumplir criterio
    return max(V0_target, V0_min_required)

def simulate_multiple_beats(
    V0_user, 
    R_base, 
    C, 
    num_beats=5, 
    interval=1.0,
    use_feedback=False,
    V_min=1.0,
    arrhythmia_mode=False,
    R_min=300,
    R_max=1000
):
    """
    Simula múltiples latidos del marcapasos con opciones avanzadas.
    
    Características:
    - Modo arritmia: Variación aleatoria de la resistencia del tejido
    - Realimentación adaptativa: Ajuste automático de V0 para efectividad
    - Simulación continua con intervalos configurables
    
    Parámetros:
    -----------
    V0_user : float
        Voltaje inicial deseado por el usuario (V)
    R_base : float
        Resistencia base del tejido cardíaco (Ω)
    C : float
        Capacitancia del marcapasos (F)
    num_beats : int
        Número total de latidos a simular
    interval : float
        Tiempo entre latidos consecutivos (s)
    use_feedback : bool
        Activar sistema de realimentación adaptativa
    V_min : float
        Voltaje mínimo para estimulación efectiva (V)
    arrhythmia_mode : bool
        Activar simulación de arritmia (resistencia variable)
    R_min, R_max : float
        Rango de resistencia para modo arritmia (Ω)
        
    Retorna:
    --------
    t_total : array
        Vector de tiempo completo de la simulación
    V_total : array
        Voltaje del marcapasos a lo largo del tiempo
    R_values : array
        Valores de resistencia utilizados
    V0_used : array
        Valores de V0 aplicados en cada punto
    beat_boundaries : list
        Lista de tuplas (inicio, fin) para cada latido
    """
    
    # Inicialización de arrays de resultados
    t_global = []
    V_global = []
    R_values = []
    V0_used = []
    beat_boundaries = []  # Límites temporales de cada latido
    
    t_offset = 0.0  # Offset temporal acumulativo
    total_index = 0  # Índice total para beat_boundaries
    
    # Simulación latido por latido
    for beat in range(num_beats):
        # Modo arritmia: resistencia variable por patología cardíaca
        if arrhythmia_mode:
            # Simula variabilidad del tejido cardíaco en condiciones patológicas
            R_current = np.random.uniform(R_min, R_max)
        else:
            # Tejido cardíaco saludable con resistencia constante
            R_current = R_base
        
        # Sistema de realimentación adaptativa
        if use_feedback:
            # Ajuste automático de V0 para garantizar estimulación efectiva
            V0_current = adaptive_feedback(V0_user, R_current, C, V_min)
        else:
            # Usar voltaje especificado por el usuario sin ajustes
            V0_current = V0_user
        
        # Simular el pulso individual
        t_pulse, V_pulse = single_pulse(V0_current, R_current, C)
        
        # Aplicar offset temporal para continuidad de la simulación
        t_pulse_shifted = t_pulse + t_offset
        
        # Agregar datos del pulso actual a los arrays globales
        t_global.append(t_pulse_shifted)
        V_global.append(V_pulse)
        
        # Extender arrays de parámetros para cada punto temporal
        pulse_length = len(t_pulse)
        R_values.extend([R_current] * pulse_length)
        V0_used.extend([V0_current] * pulse_length)
        
        # Registrar límites del latido actual para análisis posterior
        start_idx = total_index
        end_idx = total_index + pulse_length
        beat_boundaries.append((start_idx, end_idx))
        total_index = end_idx
        
        # Actualizar offset temporal para el siguiente latido
        t_offset += interval
    
    # Consolidar todos los arrays en vectores continuos
    t_total = np.concatenate(t_global)
    V_total = np.concatenate(V_global)
    R_values = np.array(R_values)
    V0_used = np.array(V0_used)
    
    return t_total, V_total, R_values, V0_used, beat_boundaries

def calculate_energy_metrics(t, V, R_values):
    """
    Calcula métricas energéticas del sistema de marcapasos.
    
    Parámetros:
    -----------
    t : array
        Vector de tiempo
    V : array
        Vector de voltaje
    R_values : array
        Vector de resistencias
        
    Retorna:
    --------
    dict
        Diccionario con métricas energéticas calculadas
    """
    # Potencia instantánea: P = V²/R
    power = V**2 / R_values
    
    # Energía acumulada por integración numérica
    dt = np.gradient(t)
    energy_cumulative = np.cumsum(power * dt)
    
    # Métricas de resumen
    total_energy = energy_cumulative[-1]
    peak_power = np.max(power)
    average_power = np.mean(power)
    
    return {
        'power': power,
        'energy_cumulative': energy_cumulative,
        'total_energy': total_energy,
        'peak_power': peak_power,
        'average_power': average_power
    }

def validate_parameters(V0, R, C, V_min):
    """
    Valida los parámetros del sistema para operación segura.
    
    Parámetros:
    -----------
    V0 : float
        Voltaje inicial
    R : float
        Resistencia del tejido
    C : float
        Capacitancia
    V_min : float
        Voltaje mínimo requerido
        
    Retorna:
    --------
    dict
        Diccionario con resultados de validación
    """
    # Cálculos de validación
    tau = R * C
    V_at_tau = V0 * np.exp(-1)
    
    # Criterios de seguridad y efectividad
    is_effective = V_at_tau >= V_min
    is_safe = V0 <= 15.0  # Límite de seguridad típico para marcapasos
    pulse_duration = 3 * tau * 1000  # 95% de la descarga en 3τ
    is_duration_ok = 0.5 <= pulse_duration <= 2.0  # Duración típica 0.5-2 ms
    
    return {
        'tau_ms': tau * 1000,
        'V_at_tau': V_at_tau,
        'is_effective': is_effective,
        'is_safe': is_safe,
        'pulse_duration_ms': pulse_duration,
        'is_duration_ok': is_duration_ok,
        'overall_valid': is_effective and is_safe and is_duration_ok
    }
