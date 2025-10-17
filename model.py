# model.py
import numpy as np
import pandas as pd

def single_pulse(V0, R, C, t_max=0.05, num_points=200):
    """Simula un solo pulso de descarga."""
    tau = R * C
    t = np.linspace(0, t_max, num_points)
    Vc = V0 * np.exp(-t / tau)
    return t, Vc

def adaptive_feedback(V0_target, R, C, V_min=1.0):
    """Ajusta V0 para garantizar Vc(tau) >= V_min."""
    return max(V0_target, V_min * np.exp(1))

def simulate_multiple_beats(
    V0_user, R_base, C, 
    num_beats=5, 
    interval=1.0,
    use_feedback=False,
    V_min=1.0,
    arrhythmia_mode=False,
    R_min=300,
    R_max=1000
):
    """
    Simula múltiples latidos con opción de arrhythmia.
    Retorna: tiempo, voltaje, resistencias, V0 usados, y límites de cada latido.
    """
    t_global = []
    V_global = []
    R_values = []
    V0_used = []
    beat_boundaries = []  # ← NUEVO: índices de inicio/fin de cada latido

    t_offset = 0.0
    total_index = 0

    for beat in range(num_beats):
        # Modo arrhythmia: R varía aleatoriamente
        if arrhythmia_mode:
            R_current = np.random.uniform(R_min, R_max)
        else:
            R_current = R_base

        # Realimentación adaptativa
        if use_feedback:
            V0_current = adaptive_feedback(V0_user, R_current, C, V_min)
        else:
            V0_current = V0_user

        # Simular pulso
        t_pulse, V_pulse = single_pulse(V0_current, R_current, C)

        # Añadir offset de tiempo
        t_pulse_shifted = t_pulse + t_offset

        t_global.append(t_pulse_shifted)
        V_global.append(V_pulse)
        R_values.extend([R_current] * len(t_pulse))
        V0_used.extend([V0_current] * len(t_pulse))

        # Guardar los límites de este latido
        start_idx = total_index
        end_idx = total_index + len(t_pulse)
        beat_boundaries.append((start_idx, end_idx))
        total_index = end_idx

        # Actualizar offset (intervalo entre latidos)
        t_offset += interval

    # Aplanar listas
    t_total = np.concatenate(t_global)
    V_total = np.concatenate(V_global)

    return t_total, V_total, np.array(R_values), np.array(V0_used), beat_boundaries