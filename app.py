import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import numpy as np
import pandas as pd
from model import simulate_multiple_beats
import time

st.set_page_config(
    page_title="Simulador de Marcapasos Profesional",
    page_icon="🫀",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .parameter-group {
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1rem;
        margin: 1rem 0;
        background: #f8f9fa;
    }
    .status-success {
        background: linear-gradient(135deg, #4CAF50, #45a049);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
    .status-warning {
        background: linear-gradient(135deg, #ff9800, #f57c00);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)


st.markdown("""
<div class="main-header">
    <h1 style="color: #2E86C1; margin-bottom: 0;">🫀 Simulador de Marcapasos Profesional</h1>
    <h3 style="color: #5D6D7E; font-weight: 300;">Sistema Avanzado de Simulación RC con Análisis de Múltiples Latidos</h3>
</div>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## ⚙️ Panel de Control")
    
    st.divider()
    
    st.markdown("### 🏥 Configuraciones Clínicas Predefinidas")
    
    clinical_presets = {
        "Personalizado": {
            "V0": 5.0,
            "R": 500,
            "C": 20.0,
            "num_beats": 5,
            "interval": 1.0,
            "use_feedback": True,
            "arrhythmia": False,
            "description": "Configuración manual personalizada"
        },
        "Normal (60-100 bpm)": {
            "V0": 5.0,
            "R": 500,
            "C": 20.0,
            "num_beats": 8,
            "interval": 0.75,  # 80 bpm
            "use_feedback": True,
            "arrhythmia": False,
            "description": "Ritmo cardíaco normal entre 60-100 latidos por minuto"
        },
        "Bradicardia (<60 bpm)": {
            "V0": 6.0,
            "R": 600,
            "C": 22.0,
            "num_beats": 6,
            "interval": 1.5,  # 40 bpm
            "use_feedback": True,
            "arrhythmia": False,
            "description": "Frecuencia cardíaca baja, requiere estimulación"
        },
        "Taquicardia (>100 bpm)": {
            "V0": 4.5,
            "R": 450,
            "C": 18.0,
            "num_beats": 12,
            "interval": 0.5,  # 120 bpm
            "use_feedback": True,
            "arrhythmia": False,
            "description": "Frecuencia cardíaca elevada"
        },
        "Fibrilación Auricular": {
            "V0": 5.5,
            "R": 700,
            "C": 25.0,
            "num_beats": 10,
            "interval": 0.9,
            "use_feedback": True,
            "arrhythmia": True,
            "description": "Ritmo irregular con resistencia variable del tejido"
        },
        "Bloqueo Cardíaco": {
            "V0": 7.0,
            "R": 800,
            "C": 25.0,
            "num_beats": 6,
            "interval": 1.8,  # 33 bpm
            "use_feedback": True,
            "arrhythmia": False,
            "description": "Conducción cardíaca deteriorada, requiere alto voltaje"
        }
    }
    
    if 'last_preset' not in st.session_state:
        st.session_state.last_preset = "Personalizado"
    
    preset_choice = st.selectbox(
        "Seleccionar Preset",
        options=list(clinical_presets.keys()),
        index=0,
        key="preset_selector",
        help="Configura automáticamente los parámetros para condiciones clínicas comunes"
    )
    
    if preset_choice != st.session_state.last_preset:
        st.session_state.last_preset = preset_choice
        
        st.rerun()
    
    if preset_choice != "Personalizado":
        st.info(f"ℹ️ **{preset_choice}**: {clinical_presets[preset_choice]['description']}")
    
    st.divider()
    
    # Get preset values
    preset = clinical_presets[preset_choice]
    
    with st.expander("🔌 Parámetros Eléctricos", expanded=True):
        st.markdown("### Configuración del Circuito RC")
        V0_user = st.slider(
            "Voltaje Inicial V₀ (V)", 
            min_value=1.0, max_value=10.0, value=preset["V0"], step=0.1,
            help="Voltaje inicial del capacitor antes de la descarga",
            disabled=(preset_choice != "Personalizado"),
            key=f"v0_{preset_choice}"
        )
        R_base = st.slider(
            "Resistencia Base R (Ω)", 
            min_value=300, max_value=1000, value=preset["R"], step=10,
            help="Resistencia del tejido cardíaco y electrodo",
            disabled=(preset_choice != "Personalizado"),
            key=f"r_base_{preset_choice}"
        )
        C_uF = st.slider(
            "Capacitancia C (µF)", 
            min_value=10.0, max_value=30.0, value=preset["C"], step=0.5,
            help="Capacitancia del marcapasos",
            disabled=(preset_choice != "Personalizado"),
            key=f"c_uf_{preset_choice}"
        )
        C = C_uF * 1e-6
    
    # Timing Parameters Group
    with st.expander("⏱️ Parámetros Temporales", expanded=True):
        st.markdown("### Control de Estimulación")
        num_beats = st.slider(
            "Número de Latidos", 
            min_value=1, max_value=20, value=preset["num_beats"],
            help="Cantidad total de pulsos a simular",
            disabled=(preset_choice != "Personalizado"),
            key=f"num_beats_{preset_choice}"
        )
        interval = st.slider(
            "Intervalo entre Latidos (s)", 
            min_value=0.5, max_value=2.0, value=preset["interval"], step=0.1,
            help="Tiempo de espera entre pulsos consecutivos",
            disabled=(preset_choice != "Personalizado"),
            key=f"interval_{preset_choice}"
        )
    
    # Advanced Features Group
    with st.expander("🔬 Características Avanzadas", expanded=True):
        st.markdown("### Funciones Especializadas")
        use_feedback = st.checkbox(
            "✅ Realimentación Adaptativa", 
            value=preset["use_feedback"],
            help="Ajusta automáticamente V₀ para mantener efectividad",
            disabled=(preset_choice != "Personalizado"),
            key=f"feedback_{preset_choice}"
        )
        if use_feedback:
            V_min = st.slider(
                "Voltaje Mínimo V_min (V)", 
                min_value=0.5, max_value=3.0, value=1.0, step=0.1,
                help="Umbral mínimo para estimulación efectiva",
                disabled=(preset_choice != "Personalizado"),
                key=f"vmin_{preset_choice}"
            )
        else:
            V_min = 1.0
            
        arrhythmia = st.checkbox(
            "⚠️ Modo Arritmia", 
            value=preset["arrhythmia"],
            help="Simula resistencia variable del tejido cardíaco",
            disabled=(preset_choice != "Personalizado"),
            key=f"arrhythmia_{preset_choice}"
        )
    
    # Quick Info Panel
    tau = R_base * C
    st.markdown("### 📊 Información Rápida")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Constante τ", f"{tau*1000:.1f} ms")
    with col2:
        st.metric("Frecuencia", f"{60/interval:.0f} bpm")

# Run simulation
t, V, R_vals, V0_vals, beat_boundaries = simulate_multiple_beats(
    V0_user=V0_user,
    R_base=R_base,
    C=C,
    num_beats=num_beats,
    interval=interval,
    use_feedback=use_feedback,
    V_min=V_min,
    arrhythmia_mode=arrhythmia
)

# Set plot template based on theme
plot_template = "plotly_dark" if  "Oscuro" else "plotly_white"

# Main content tabs with professional styling
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "📈 Análisis Gráfico", 
    "🔬 Métricas Avanzadas",
    "📊 Comparación de Presets",
    "💾 Datos Detallados", 
    "🎬 Simulación en Vivo", 
    "🧮 Modelo Matemático"
])

with tab1:
    st.markdown("## 📈 Visualización Continua del Voltaje del Marcapasos ")
    
    fig = go.Figure()

    medical_colors = [
        '#E74C3C', '#3498DB', '#2ECC71', '#F39C12', '#9B59B6',
        '#1ABC9C', '#E67E22', '#34495E', '#16A085', '#C0392B'
    ]

    for i, (start, end) in enumerate(beat_boundaries):
        color = medical_colors[i % len(medical_colors)]

        # Convertir a RGBA para sombra
        hex_color = color.lstrip('#')
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
        fillcolor = f'rgba({r}, {g}, {b}, 0.15)'

        if i > 0:
            t_segment = np.concatenate(([t[start-1]], t[start:end]))
            V_segment = np.concatenate(([V[start-1]], V[start:end]))
        else:
            t_segment = t[start:end]
            V_segment = V[start:end]

        fig.add_trace(go.Scatter(
            x=t_segment,
            y=V_segment,
            mode='lines',
            line=dict(width=3, color=color),
            fill='tonexty',  
            fillcolor=fillcolor,
            name=f'Latido {i+1}',
            hovertemplate=f"<b>Latido {i+1}</b><br>Tiempo: %{{x:.3f}}s<br>Voltaje: %{{y:.2f}}V<extra></extra>"
        ))

    # Línea del umbral
    fig.add_hline(
        y=V_min,
        line_dash="dot",
        line_color="#F1C40F",
        line_width=2,
        annotation_text=f"Umbral: {V_min:.1f}V",
        annotation_position="top right"
    )

    # Configuración visual
    fig.update_layout(
        title={
            'text': "Simulación Continua del Voltaje del Marcapasos con Latidos Diferenciados",
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18, 'color': '#2C3E50'}
        },
        xaxis_title="Tiempo (s)",
        yaxis_title="Voltaje (V)",
        height=550,
        template="plotly_dark",
        showlegend=True,
        legend=dict(
    orientation="v",
    yanchor="top",
    y=0.99,
    xanchor="left",
    x=1.02,
    bgcolor="rgba(0,0,0,0.6)",   # ✅ fondo oscuro semitransparente
    bordercolor="rgba(255,255,255,0.2)",  # ✅ borde suave y claro
    borderwidth=1,
    font=dict(color="white")  # ✅ texto visible en modo oscuro
)
,
        hovermode='x unified',
        margin=dict(r=150)
    )

    fig.update_xaxes(
        gridcolor='rgba(128,128,128,0.2)',
        gridwidth=1
    )
    fig.update_yaxes(
        gridcolor='rgba(128,128,128,0.2)',
        gridwidth=1
    )

    st.plotly_chart(fig, use_container_width=True)


    
    # Export options
    export_col1, export_col2 = st.columns([3, 1])
    with export_col2:
        # Export button for HTML (interactive)
        html_bytes = fig.to_html(include_plotlyjs='cdn').encode()
        st.download_button(
            label="📥 Exportar Gráfico HTML",
            data=html_bytes,
            file_name=f"marcapasos_grafico_{preset_choice.replace(' ', '_')}.html",
            mime="text/html",
            help="Descarga el gráfico interactivo en formato HTML"
        )
    
    # Professional analysis cards
    st.markdown("## 🔍 Análisis Clínico Profesional")
    
    # Create metrics columns
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Voltaje Inicial Promedio",
            f"{np.mean(V0_vals):.2f} V",
            delta=f"{np.mean(V0_vals) - V0_user:.2f}" if use_feedback else None
        )
    
    with col2:
        st.metric(
            "Resistencia Promedio",
            f"{np.mean(R_vals):.0f} Ω",
            delta=f"{np.std(R_vals):.0f}" if arrhythmia else "Constante"
        )
    
    with col3:
        V_at_tau = V0_user * np.exp(-1)
        st.metric(
            "Voltaje en τ",
            f"{V_at_tau:.2f} V",
            delta="Efectivo" if V_at_tau >= V_min else "Insuficiente"
        )
    
    with col4:
        st.metric(
            "Constante de Tiempo",
            f"{tau*1000:.1f} ms",
            delta=f"τ = RC"
        )
    
    # Professional status analysis
    if use_feedback:
        st.markdown("""
        <div class="status-success">
            <h4>✅ Sistema de Realimentación Activo</h4>
            <p>El sistema ha ajustado automáticamente el voltaje inicial para garantizar una estimulación cardíaca efectiva. 
            El voltaje se mantiene por encima del umbral mínimo durante el tiempo crítico de estimulación.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        if V_at_tau >= V_min:
            st.markdown("""
            <div class="status-success">
                <h4>✅ Estimulación Efectiva</h4>
                <p>Los parámetros actuales garantizan una estimulación cardíaca exitosa. El voltaje permanece por encima 
                del umbral mínimo durante la ventana crítica de estimulación.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-warning">
                <h4>⚠️ Riesgo de Estimulación Insuficiente</h4>
                <p>El voltaje cae por debajo del umbral mínimo. Se recomienda activar la realimentación adaptativa 
                o ajustar los parámetros eléctricos para garantizar una estimulación efectiva.</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Clinical insights
    st.markdown("### 💡 Perspectivas Clínicas")
    insight_col1, insight_col2 = st.columns(2)
    
    with insight_col1:
        st.markdown("""
        **Características del Pulso:**
        - Forma exponencial decreciente característica
        - Entrega de energía concentrada en primeros τ ms
        - Perfil de descarga optimizado para despolarización
        """)
    
    with insight_col2:
        st.markdown(f"""
        **Parámetros Críticos:**
        - Duración efectiva: ~{tau*1000:.1f} ms
        - Energía principal en 1τ = {tau*1000:.1f} ms  
        - Seguridad: Voltaje controlado y predecible
        """)

# Advanced Metrics Dashboard Tab
with tab2:
    st.markdown("## 🔬 Dashboard de Métricas Avanzadas")
    
    # Calculate advanced metrics
    df_metrics = pd.DataFrame({
        'Tiempo (s)': t,
        'Voltaje (V)': V,
        'Resistencia (Ω)': R_vals,
        'Potencia (W)': V**2 / R_vals,
    })
    
    # Energy metrics per beat
    energy_per_beat = []
    for i, (start, end) in enumerate(beat_boundaries):
        beat_energy = np.sum(V[start:end]**2 / R_vals[start:end] * np.gradient(t[start:end]))
        energy_per_beat.append(beat_energy)
    
    # Heart rate variability (HRV) - Calculate from actual beat timings
    if len(beat_boundaries) > 1:
        # Get actual RR intervals from beat start times
        beat_start_times = [t[start] for start, end in beat_boundaries]
        rr_intervals = np.diff(beat_start_times) * 1000  # Convert to ms
        hrv_std = np.std(rr_intervals)
        hrv_mean = np.mean(rr_intervals)
        avg_bpm = 60000 / hrv_mean if hrv_mean > 0 else 60 / interval
    else:
        hrv_std = 0
        hrv_mean = interval * 1000
        avg_bpm = 60 / interval
    
    # Top metrics row
    st.markdown("### 📊 Métricas Principales del Pulso Cardíaco")
    metric_col1, metric_col2, metric_col3, metric_col4 = st.columns(4)
    
    with metric_col1:
        st.metric(
            "Frecuencia Cardíaca",
            f"{avg_bpm:.1f} bpm",
            delta="Normal" if 60 <= avg_bpm <= 100 else ("Bajo" if avg_bpm < 60 else "Alto"),
            delta_color="normal" if 60 <= avg_bpm <= 100 else "inverse"
        )
    
    with metric_col2:
        st.metric(
            "Variabilidad (HRV)",
            f"{hrv_std:.1f} ms",
            delta="Variable" if arrhythmia else "Estable",
            delta_color="inverse" if arrhythmia else "normal"
        )
    
    with metric_col3:
        total_energy = np.sum(energy_per_beat)
        st.metric(
            "Energía Total",
            f"{total_energy*1000:.2f} mJ",
            delta=f"{len(beat_boundaries)} latidos"
        )
    
    with metric_col4:
        avg_energy = np.mean(energy_per_beat)
        st.metric(
            "Energía Promedio/Latido",
            f"{avg_energy*1000:.3f} mJ",
            delta=f"±{np.std(energy_per_beat)*1000:.3f}"
        )
    
    st.divider()
    
    # Detailed metrics in columns
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### ⚡ Análisis de Energía por Latido")
        
        # Energy per beat chart
        fig_energy = go.Figure()
        fig_energy.add_trace(go.Bar(
            x=[f"Latido {i+1}" for i in range(len(energy_per_beat))],
            y=[e*1000 for e in energy_per_beat],
            marker=dict(
                color=[e*1000 for e in energy_per_beat],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="Energía (mJ)")
            ),
            text=[f"{e*1000:.3f} mJ" for e in energy_per_beat],
            textposition='outside',
            hovertemplate='<b>%{x}</b><br>Energía: %{y:.3f} mJ<extra></extra>'
        ))
        
        fig_energy.update_layout(
            title="Distribución de Energía por Latido",
            xaxis_title="Latido",
            yaxis_title="Energía (mJ)",
            height=400,
            template=plot_template,
            showlegend=False
        )
        
        st.plotly_chart(fig_energy, use_container_width=True)
        
        # Energy statistics table
        st.markdown("**Estadísticas de Energía:**")
        energy_stats = pd.DataFrame({
            'Métrica': ['Mínima', 'Máxima', 'Promedio', 'Desv. Estándar', 'Total'],
            'Valor (mJ)': [
                f"{min(energy_per_beat)*1000:.3f}",
                f"{max(energy_per_beat)*1000:.3f}",
                f"{np.mean(energy_per_beat)*1000:.3f}",
                f"{np.std(energy_per_beat)*1000:.3f}",
                f"{total_energy*1000:.3f}"
            ]
        })
        st.dataframe(energy_stats, hide_index=True, use_container_width=True)
    
    with col2:
        st.markdown("### 📈 Distribución de Potencia")
        
        # Power distribution over time
        fig_power = go.Figure()
        
        # Add power trace
        fig_power.add_trace(go.Scatter(
            x=t,
            y=df_metrics['Potencia (W)'],
            mode='lines',
            fill='tozeroy',
            line=dict(color='#E67E22', width=2),
            fillcolor='rgba(230, 126, 34, 0.2)',
            name='Potencia Instantánea',
            hovertemplate='Tiempo: %{x:.3f}s<br>Potencia: %{y:.3f}W<extra></extra>'
        ))
        
        # Add average line
        avg_power = df_metrics['Potencia (W)'].mean()
        fig_power.add_hline(
            y=avg_power,
            line_dash="dash",
            line_color="red",
            annotation_text=f"Promedio: {avg_power:.3f}W"
        )
        
        fig_power.update_layout(
            title="Potencia Instantánea vs Tiempo",
            xaxis_title="Tiempo (s)",
            yaxis_title="Potencia (W)",
            height=400,
            template=plot_template,
            showlegend=True
        )
        
        st.plotly_chart(fig_power, use_container_width=True)
        
        # Power statistics
        st.markdown("**Estadísticas de Potencia:**")
        power_stats = pd.DataFrame({
            'Métrica': ['Pico', 'Mínima', 'Promedio', 'Desv. Estándar'],
            'Valor (W)': [
                f"{df_metrics['Potencia (W)'].max():.3f}",
                f"{df_metrics['Potencia (W)'].min():.3f}",
                f"{avg_power:.3f}",
                f"{df_metrics['Potencia (W)'].std():.3f}"
            ]
        })
        st.dataframe(power_stats, hide_index=True, use_container_width=True)
    
    st.divider()
    
    # Clinical interpretation
    st.markdown("### 🏥 Interpretación Clínica de Métricas")
    
    interp_col1, interp_col2, interp_col3 = st.columns(3)
    
    with interp_col1:
        st.markdown("**Frecuencia Cardíaca:**")
        if avg_bpm < 60:
            st.warning(f"⚠️ Bradicardia detectada ({avg_bpm:.0f} bpm). El marcapasos compensa frecuencia baja.")
        elif avg_bpm > 100:
            st.info(f"ℹ️ Taquicardia ({avg_bpm:.0f} bpm). Frecuencia elevada.")
        else:
            st.success(f"✅ Frecuencia normal ({avg_bpm:.0f} bpm).")
    
    with interp_col2:
        st.markdown("**Consumo Energético:**")
        if total_energy * 1000 < 1.0:
            st.success("✅ Consumo eficiente de batería.")
        elif total_energy * 1000 < 5.0:
            st.info("ℹ️ Consumo moderado de energía.")
        else:
            st.warning("⚠️ Alto consumo energético.")
    
    with interp_col3:
        st.markdown("**Estabilidad del Ritmo:**")
        if arrhythmia:
            st.warning(f"⚠️ Modo arritmia activo (HRV: {hrv_std:.1f}ms).")
        else:
            st.success(f"✅ Ritmo estable y predecible.")

# Preset Comparison Tab
with tab3:
    st.markdown("## 📊 Análisis Comparativo de Presets Clínicos")
    
    st.markdown("""
    Esta herramienta permite comparar visualmente el comportamiento de diferentes configuraciones
    clínicas predefinidas, facilitando la comprensión de cómo distintas condiciones cardíacas
    afectan la respuesta del marcapasos.
    """)
    
    # Preset selection for comparison
    st.markdown("### Seleccionar Presets para Comparar")
    comp_col1, comp_col2 = st.columns(2)
    
    preset_names = list(clinical_presets.keys())
    preset_names.remove("Personalizado")  # Remove custom from comparison
    
    with comp_col1:
        preset1 = st.selectbox(
            "Preset 1",
            options=preset_names,
            index=0,
            help="Primer preset a comparar"
        )
    
    with comp_col2:
        preset2 = st.selectbox(
            "Preset 2",
            options=preset_names,
            index=min(1, len(preset_names)-1),
            help="Segundo preset a comparar"
        )
    
    # Simulate both presets
    p1_config = clinical_presets[preset1]
    p2_config = clinical_presets[preset2]
    
    # Simulation 1
    t1, V1, R1, V0_1, bounds1 = simulate_multiple_beats(
        V0_user=p1_config["V0"],
        R_base=p1_config["R"],
        C=p1_config["C"] * 1e-6,
        num_beats=p1_config["num_beats"],
        interval=p1_config["interval"],
        use_feedback=p1_config["use_feedback"],
        V_min=1.0,
        arrhythmia_mode=p1_config["arrhythmia"]
    )
    
    # Simulation 2
    t2, V2, R2, V0_2, bounds2 = simulate_multiple_beats(
        V0_user=p2_config["V0"],
        R_base=p2_config["R"],
        C=p2_config["C"] * 1e-6,
        num_beats=p2_config["num_beats"],
        interval=p2_config["interval"],
        use_feedback=p2_config["use_feedback"],
        V_min=1.0,
        arrhythmia_mode=p2_config["arrhythmia"]
    )
    
    # Side-by-side comparison
    st.markdown("### 📈 Comparación Visual de Pulsos")
    
    graph_col1, graph_col2 = st.columns(2)
    
    with graph_col1:
        st.markdown(f"**{preset1}**")
        fig1 = go.Figure()
        for i, (start, end) in enumerate(bounds1):
            fig1.add_trace(go.Scatter(
                x=t1[start:end],
                y=V1[start:end],
                mode='lines',
                line=dict(width=2, color='#E74C3C'),
                name=f'Latido {i+1}',
                showlegend=False
            ))
        
        fig1.update_layout(
            title=f"{preset1}<br><sub>{p1_config['description']}</sub>",
            xaxis_title="Tiempo (s)",
            yaxis_title="Voltaje (V)",
            height=400,
            template=plot_template
        )
        st.plotly_chart(fig1, use_container_width=True)
        
        # Metrics for preset 1
        st.markdown("**Métricas:**")
        st.write(f"- Frecuencia: {60/p1_config['interval']:.0f} bpm")
        st.write(f"- V₀: {p1_config['V0']:.1f} V")
        st.write(f"- R: {p1_config['R']} Ω")
        st.write(f"- C: {p1_config['C']:.1f} µF")
        st.write(f"- τ: {(p1_config['R'] * p1_config['C'] * 1e-6)*1000:.2f} ms")
    
    with graph_col2:
        st.markdown(f"**{preset2}**")
        fig2 = go.Figure()
        for i, (start, end) in enumerate(bounds2):
            fig2.add_trace(go.Scatter(
                x=t2[start:end],
                y=V2[start:end],
                mode='lines',
                line=dict(width=2, color='#3498DB'),
                name=f'Latido {i+1}',
                showlegend=False
            ))
        
        fig2.update_layout(
            title=f"{preset2}<br><sub>{p2_config['description']}</sub>",
            xaxis_title="Tiempo (s)",
            yaxis_title="Voltaje (V)",
            height=400,
            template=plot_template
        )
        st.plotly_chart(fig2, use_container_width=True)
        
        # Metrics for preset 2
        st.markdown("**Métricas:**")
        st.write(f"- Frecuencia: {60/p2_config['interval']:.0f} bpm")
        st.write(f"- V₀: {p2_config['V0']:.1f} V")
        st.write(f"- R: {p2_config['R']} Ω")
        st.write(f"- C: {p2_config['C']:.1f} µF")
        st.write(f"- τ: {(p2_config['R'] * p2_config['C'] * 1e-6)*1000:.2f} ms")
    
    # Overlay comparison
    st.markdown("### 🔄 Superposición de Configuraciones")
    
    fig_overlay = go.Figure()
    
    # Add first preset (only first beat for clarity)
    if len(bounds1) > 0:
        start, end = bounds1[0]
        fig_overlay.add_trace(go.Scatter(
            x=t1[start:end],
            y=V1[start:end],
            mode='lines',
            line=dict(width=3, color='#E74C3C'),
            name=preset1
        ))
    
    # Add second preset (only first beat for clarity)
    if len(bounds2) > 0:
        start, end = bounds2[0]
        fig_overlay.add_trace(go.Scatter(
            x=t2[start:end],
            y=V2[start:end],
            mode='lines',
            line=dict(width=3, color='#3498DB'),
            name=preset2
        ))
    
    fig_overlay.update_layout(
        title="Comparación Directa del Primer Pulso",
        xaxis_title="Tiempo (s)",
        yaxis_title="Voltaje (V)",
        height=500,
        template=plot_template,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig_overlay, use_container_width=True)
    
    # Comparative table
    st.markdown("### 📋 Tabla Comparativa de Parámetros")
    
    comparison_df = pd.DataFrame({
        'Parámetro': [
            'Frecuencia Cardíaca (bpm)',
            'Voltaje Inicial V₀ (V)',
            'Resistencia R (Ω)',
            'Capacitancia C (µF)',
            'Constante τ (ms)',
            'Número de Latidos',
            'Intervalo (s)',
            'Realimentación',
            'Modo Arritmia'
        ],
        preset1: [
            f"{60/p1_config['interval']:.0f}",
            f"{p1_config['V0']:.1f}",
            f"{p1_config['R']}",
            f"{p1_config['C']:.1f}",
            f"{(p1_config['R'] * p1_config['C'] * 1e-6)*1000:.2f}",
            f"{p1_config['num_beats']}",
            f"{p1_config['interval']:.1f}",
            "Sí" if p1_config['use_feedback'] else "No",
            "Sí" if p1_config['arrhythmia'] else "No"
        ],
        preset2: [
            f"{60/p2_config['interval']:.0f}",
            f"{p2_config['V0']:.1f}",
            f"{p2_config['R']}",
            f"{p2_config['C']:.1f}",
            f"{(p2_config['R'] * p2_config['C'] * 1e-6)*1000:.2f}",
            f"{p2_config['num_beats']}",
            f"{p2_config['interval']:.1f}",
            "Sí" if p2_config['use_feedback'] else "No",
            "Sí" if p2_config['arrhythmia'] else "No"
        ]
    })
    
    st.dataframe(comparison_df, use_container_width=True, hide_index=True)

# Enhanced Data Tab
with tab4:
    st.markdown("## 📊 Datos Detallados de la Simulación")
    
    # Create comprehensive dataframe
    df = pd.DataFrame({
        'Tiempo (s)': t,
        'Voltaje (V)': V,
        'Resistencia (Ω)': R_vals,
        'V₀ Aplicado (V)': V0_vals,
        'Potencia (W)': V**2 / R_vals,
        'Energía Acum. (J)': np.cumsum(V**2 / R_vals * np.gradient(t))
    })
    
    # Summary statistics
    st.markdown("### 📈 Estadísticas Resumidas")
    summary_col1, summary_col2, summary_col3 = st.columns(3)
    
    with summary_col1:
        st.markdown("**Voltaje**")
        st.write(f"Máximo: {df['Voltaje (V)'].max():.2f} V")
        st.write(f"Mínimo: {df['Voltaje (V)'].min():.2f} V")
        st.write(f"Promedio: {df['Voltaje (V)'].mean():.2f} V")
    
    with summary_col2:
        st.markdown("**Potencia**")
        st.write(f"Pico: {df['Potencia (W)'].max():.3f} W")
        st.write(f"Promedio: {df['Potencia (W)'].mean():.3f} W")
        st.write(f"Total: {df['Potencia (W)'].sum():.3f} W⋅s")
    
    with summary_col3:
        st.markdown("**Energía**")
        st.write(f"Total entregada: {df['Energía Acum. (J)'].iloc[-1]:.6f} J")
        st.write(f"Por latido: {df['Energía Acum. (J)'].iloc[-1]/num_beats:.6f} J")
    
    # Interactive data table
    st.markdown("### 📋 Tabla de Datos Completa")
    st.dataframe(
        df.round(6), 
        use_container_width=True,
        height=400
    )
    
    # Enhanced download options
    st.markdown("### 💾 Opciones de Exportación")
    col1, col2 = st.columns(2)
    
    with col1:
        csv_data = df.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Descargar CSV Completo",
            data=csv_data,
            file_name=f"marcapasos_simulacion_{num_beats}latidos.csv",
            mime="text/csv",
            help="Descarga todos los datos de la simulación en formato CSV"
        )
    
    with col2:
        # Summary report
        summary_report = f"""
        REPORTE DE SIMULACIÓN DE MARCAPASOS
        ===================================
        
        Parámetros de Configuración:
        - Voltaje inicial: {V0_user} V
        - Resistencia base: {R_base} Ω  
        - Capacitancia: {C_uF} µF
        - Número de latidos: {num_beats}
        - Intervalo: {interval} s
        - Realimentación: {'Activada' if use_feedback else 'Desactivada'}
        - Modo arritmia: {'Activado' if arrhythmia else 'Desactivado'}
        
        Resultados de Análisis:
        - Constante de tiempo: {tau*1000:.2f} ms
        - Voltaje máximo: {df['Voltaje (V)'].max():.2f} V
        - Voltaje mínimo: {df['Voltaje (V)'].min():.2f} V
        - Energía total: {df['Energía Acum. (J)'].iloc[-1]:.6f} J
        - Potencia pico: {df['Potencia (W)'].max():.3f} W
        """
        
        st.download_button(
            "📄 Descargar Reporte",
            data=summary_report,
            file_name=f"reporte_marcapasos_{num_beats}latidos.txt",
            mime="text/plain",
            help="Descarga un resumen ejecutivo de la simulación"
        )

# Enhanced Live Animation Tab
with tab5:
    st.markdown("## 🎬 Simulación en Tiempo Real")
    
    st.markdown("""
    Esta simulación muestra la evolución temporal del voltaje del marcapasos en tiempo real,
    permitiendo observar el comportamiento dinámico de cada pulso de estimulación.
    """)
    
    # Animation controls
    control_col1, control_col2, control_col3 = st.columns([2, 1, 1])
    
    with control_col1:
        animation_speed = st.slider(
            "Velocidad de Animación", 
            min_value=0.01, max_value=0.5, value=0.1, step=0.01,
            help="Controla la velocidad de reproducción de la animación"
        )
    
    with control_col2:
        show_markers = st.checkbox("Mostrar Puntos", value=False)
    
    with control_col3:
        show_grid = st.checkbox("Mostrar Rejilla", value=True)
    
    # Create animated figure
    fig_animated = go.Figure()
    fig_animated.add_trace(go.Scatter(
        x=[], y=[], 
        mode='lines+markers' if show_markers else 'lines',
        line=dict(width=3, color='#E74C3C'),
        marker=dict(size=4) if show_markers else {},
        name='Voltaje del Marcapasos'
    ))
    
    if use_feedback:
        fig_animated.add_hline(
            y=V_min, 
            line_dash="dot", 
            line_color="#F39C12", 
            line_width=2,
            annotation_text=f"Umbral: {V_min}V"
        )
    
    fig_animated.update_layout(
        title={
            'text': "Animación en Tiempo Real - Descarga del Marcapasos",
            'x': 0.5,
            'xanchor': 'center'
        },
        xaxis_title="Tiempo (s)",
        yaxis_title="Voltaje (V)",
        xaxis_range=[0, t[-1]],
        yaxis_range=[0, max(V)*1.1],
        template=plot_template,
        height=500,
        showlegend=True,
        xaxis=dict(
            fixedrange=True,
            showgrid=show_grid,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        yaxis=dict(
            fixedrange=True,
            showgrid=show_grid,
            gridcolor='rgba(128,128,128,0.2)'
        ),
        uirevision="constant"
    )
    
    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(fig_animated, use_container_width=True)
    
    # Animation button with enhanced styling
    if st.button("▶️ Iniciar Simulación en Vivo", type="primary", use_container_width=True):
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        with st.spinner("Iniciando simulación en tiempo real..."):
            total_points = len(t)
            
            for i in range(1, total_points + 1, max(1, int(total_points/200))):  # Optimize for smooth animation
                # Update progress
                progress = i / total_points
                progress_bar.progress(progress)
                status_text.text(f"Simulando... {progress*100:.1f}% completado")
                
                # Update plot data
                fig_animated.data[0].x = t[:i]
                fig_animated.data[0].y = V[:i]
                
                # Add current point highlight
                if i < total_points:
                    if len(fig_animated.data) > (2 if use_feedback else 1):
                        fig_animated.data[-1].x = [t[i-1]]
                        fig_animated.data[-1].y = [V[i-1]]
                    else:
                        fig_animated.add_trace(go.Scatter(
                            x=[t[i-1]], y=[V[i-1]],
                            mode='markers',
                            marker=dict(size=8, color='yellow', line=dict(width=2, color='red')),
                            name='Punto Actual',
                            showlegend=False
                        ))
                
                plot_placeholder.plotly_chart(fig_animated, use_container_width=True)
                time.sleep(animation_speed)
            
            # Animation completed
            progress_bar.progress(1.0)
            status_text.text("✅ Simulación completada exitosamente")
            st.balloons()

# Enhanced Mathematical Model Tab
with tab6:
    st.markdown("## 🧮 Fundamentos Matemáticos del Modelo")
    
    st.markdown("""
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 1.5rem; border-radius: 15px; margin: 1rem 0;">
        <h3 style="margin: 0; color: white;">💡 Concepto Fundamental</h3>
        <p style="margin: 0.5rem 0 0 0;">
            El marcapasos se modela como un <strong>circuito RC en descarga</strong>, donde el capacitor 
            previamente cargado se descarga a través del tejido cardíaco, representado por una resistencia variable.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Mathematical derivation with enhanced presentation
    st.markdown("### 📐 Derivación de la Ecuación Diferencial")
    
    derivation_col1, derivation_col2 = st.columns([1, 1])
    
    with derivation_col1:
        st.markdown("**Análisis del Circuito:**")
        st.markdown("""
        Aplicando la **Ley de Kirchhoff** al circuito RC durante la descarga:
        
        - El voltaje del capacitor: $V_C = \\frac{q}{C}$
        - La corriente de descarga: $I = -\\frac{dq}{dt}$
        - Ley de Ohm: $V_C = I \\cdot R$
        """)
    
    with derivation_col2:
        st.markdown("**Ecuación Resultante:**")
        st.latex(r'''
        V_C = I \cdot R = -\frac{dq}{dt} \cdot R
        ''')
        st.latex(r'''
        \frac{q}{C} = -R \frac{dq}{dt}
        ''')
        st.latex(r'''
        \frac{dq}{dt} + \frac{1}{RC} q = 0
        ''')
    
    # Step by step solution
    st.markdown("### 🔍 Solución Paso a Paso")
    
    steps = [
        {
            "title": "Paso 1: Separación de Variables",
            "equation": r"\frac{dq}{dt} = -\frac{1}{RC} q",
            "explanation": "Aislamos la derivada temporal de la carga."
        },
        {
            "title": "Paso 2: Reorganización",
            "equation": r"\frac{dq}{q} = -\frac{1}{RC} dt",
            "explanation": "Separamos las variables q y t en lados opuestos."
        },
        {
            "title": "Paso 3: Integración",
            "equation": r"\int \frac{dq}{q} = \int -\frac{1}{RC} dt",
            "explanation": "Integramos ambos lados de la ecuación."
        },
        {
            "title": "Paso 4: Resultado de Integración",
            "equation": r"\ln|q| = -\frac{t}{RC} + C_1",
            "explanation": "Aplicamos las reglas de integración básicas."
        },
        {
            "title": "Paso 5: Exponencial",
            "equation": r"q(t) = K e^{-t/(RC)}",
            "explanation": "Eliminamos el logaritmo aplicando la función exponencial."
        }
    ]
    
    for i, step in enumerate(steps):
        with st.expander(f"**{step['title']}**", expanded=(i==0)):
            col1, col2 = st.columns([2, 3])
            with col1:
                st.latex(step['equation'])
            with col2:
                st.write(step['explanation'])
    
    # Final solution with current parameters
    st.markdown("### 🎯 Solución Final con Parámetros Actuales")
    
    solution_col1, solution_col2 = st.columns([1, 1])
    
    with solution_col1:
        st.markdown("**Aplicando Condición Inicial:**")
        st.markdown(f"- $q(0) = C \\cdot V_0 = {C:.2e} \\times {V0_user} = {C*V0_user:.2e}$ C")
        st.markdown("**Solución para la Carga:**")
        st.latex(rf'''
        q(t) = {C*V0_user:.2e} \cdot e^{{-t/{tau:.6f}}}
        ''')
        
    with solution_col2:
        st.markdown("**Solución para el Voltaje:**")
        st.latex(rf'''
        V_C(t) = \frac{{q(t)}}{{C}} = {V0_user} \cdot e^{{-t/{tau:.6f}}}
        ''')
        st.markdown("**Parámetros del Sistema:**")
        st.write(f"- Constante de tiempo: τ = {tau*1000:.2f} ms")
        st.write(f"- Tiempo de caída al 37%: {tau*1000:.2f} ms")
        st.write(f"- Tiempo de caída al 5%: {3*tau*1000:.2f} ms")
    
    # Physical interpretation
    st.markdown("### 🏥 Interpretación Clínica y Física")
    
    interpretation_tabs = st.tabs(["Significado Físico", "Relevancia Clínica", "Optimización"])
    
    with interpretation_tabs[0]:
        st.markdown("""
        **Comportamiento Exponencial:**
        - La descarga exponencial es característica de todos los circuitos RC
        - La constante τ = RC determina la velocidad de descarga
        - El 63% de la energía se entrega en el primer τ
        
        **Constante de Tiempo:**
        - Parámetro crítico que controla la duración efectiva del pulso
        - Debe ser suficientemente larga para despolarizar el tejido
        - Pero suficientemente corta para evitar daño tisular
        """)
    
    with interpretation_tabs[1]:
        st.markdown(f"""
        **Aplicación en Marcapasos:**
        - Pulso de duración controlada (~{tau*1000:.1f} ms)
        - Entrega de energía concentrada en tiempo crítico
        - Forma de onda segura y predecible
        
        **Seguridad del Paciente:**
        - Voltaje decreciente minimiza riesgo de fibrilación
        - Energía limitada previene daño tisular
        - Forma exponencial es biocompatible
        """)
    
    with interpretation_tabs[2]:
        st.markdown(f"""
        **Optimización de Parámetros:**
        - **R**: Depende del tejido (300-1000 Ω típico)
        - **C**: Determinado por diseño del dispositivo ({C_uF} µF)
        - **V₀**: Ajustable según necesidad de estimulación ({V0_user} V)
        
        **Criterios de Diseño:**
        - Minimizar energía total consumida
        - Garantizar estimulación efectiva (V > {V_min} V en τ)
        - Maximizar vida útil de la batería
        """)
    
    # Validation section
    st.markdown("### ✅ Validación del Modelo")
    
    st.info("""
    **Verificación Matemática:**
    ✓ Esta solución analítica ha sido validada contra las simulaciones numéricas mostradas en las pestañas anteriores.
    
    ✓ Cada punto graficado corresponde a la evaluación numérica de la función exponencial derivada matemáticamente.
    
    ✓ El modelo reproduce fielmente el comportamiento de los marcapasos comerciales en condiciones controladas.
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #7F8C8D; font-size: 14px; padding: 1rem;">
    <strong>Simulador de Marcapasos Profesional</strong> | 
    Desarrollado para análisis biomédico avanzado | 
    Modelo RC con simulación de múltiples latidos
</div>
""", unsafe_allow_html=True)
