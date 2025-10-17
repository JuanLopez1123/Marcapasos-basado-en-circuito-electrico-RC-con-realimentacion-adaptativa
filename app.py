# app.py
import streamlit as st
import plotly.graph_objects as go
import numpy as np
import pandas as pd
from model import simulate_multiple_beats
import time

st.set_page_config(page_title="Simulador de Marcapasos", layout="wide")
st.title("Simulador de Marcapasos con Múltiples Latidos y Arrhythmia")

# --- Sidebar ---
with st.sidebar:
    st.header("⚙️ Parámetros")
    V0_user = st.slider("Voltaje inicial V₀ (V)", 1.0, 10.0, 5.0, 0.1)
    R_base = st.slider("Resistencia base R (Ω)", 300, 1000, 500, 10)
    C_uF = st.slider("Capacitancia C (µF)", 10.0, 30.0, 20.0, 0.5)
    C = C_uF * 1e-6

    num_beats = st.slider("Número de latidos", 1, 20, 5)
    interval = st.slider("Intervalo entre latidos (s)", 0.5, 2.0, 1.0, 0.1)

    use_feedback = st.checkbox("✅ Realimentación adaptativa", value=True)
    V_min = st.slider("V_min (V)", 0.5, 3.0, 1.0, 0.1) if use_feedback else 1.0

    arrhythmia = st.checkbox("⚠️ Modo Arrhythmia (R variable)", value=False)

# --- Simulación ---
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

# --- Pestañas ---
tab1, tab2, tab3, tab4 = st.tabs(["📊 Gráfico", "💾 Datos", "▶️ Animación en Vivo", "🧮 Modelo Matemático"])

# --- Gráfico ---
with tab1:
    st.subheader("📊 Simulación del Pulso de Descarga")

    fig = go.Figure()

    colors = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]

    # Dibujar cada latido con un color diferente, manteniendo continuidad temporal
    for i, (start, end) in enumerate(beat_boundaries):
        color = colors[i % len(colors)]
        fig.add_trace(go.Scatter(
            x=t[start:end],
            y=V[start:end],
            mode='lines',
            line=dict(width=2.5, color=color),
            name=f'Latido {i+1} (R={R_vals[start]:.0f} Ω)',
            showlegend=True
        ))

    if use_feedback:
        fig.add_hline(y=V_min, line_dash="dot", line_color="red", annotation_text="V_min")

    fig.update_layout(
        title="Pulso de Descarga del Marcapasos (Modelo RC)",
        xaxis_title="Tiempo (s)",
        yaxis_title="Voltaje (V)",
        height=500,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    st.plotly_chart(fig, use_container_width=True)

    # --- Análisis automático ---
    tau = R_base * C
    V_at_tau = V0_user * np.exp(-1)

    st.markdown("### 🔍 Análisis de la Simulación")

    if use_feedback:
        st.success(f"""
        ✅ **Realimentación adaptativa activa**: El sistema ajustó el voltaje inicial a **{V[0]:.2f} V** para garantizar que el voltaje en t = τ = {tau*1000:.1f} ms 
        no caiga por debajo de **{V_min} V**, asegurando una estimulación cardíaca efectiva.
        """)
    else:
        if V_at_tau >= V_min:
            st.success(f"""
            ✅ **Pulso efectivo**: Con V₀ = {V0_user} V, el voltaje en t = τ = {tau*1000:.1f} ms es **{V_at_tau:.2f} V**, 
            por encima del umbral mínimo ({V_min} V). La estimulación sería exitosa.
            """)
        else:
            st.warning(f"""
            ⚠️ **Riesgo de estimulación fallida**: Con V₀ = {V0_user} V, el voltaje en t = τ = {tau*1000:.1f} ms cae a **{V_at_tau:.2f} V**, 
            por debajo del umbral mínimo ({V_min} V). Se recomienda activar la realimentación adaptativa.
            """)

    st.markdown(f"""
    - **Duración del pulso**: La mayor parte de la energía se entrega en los primeros **{tau*1000:.1f} ms** (una constante de tiempo τ = RC).
    - **Forma del pulso**: Exponencial decreciente, característica de los circuitos RC en descarga.
    - **Aplicación clínica**: Este modelo simula cómo un marcapasos libera energía controlada para despolarizar el tejido cardíaco.
    """)

# --- Datos ---
with tab2:
    df = pd.DataFrame({
        'Tiempo (s)': t,
        'Voltaje (V)': V,
        'Resistencia (Ω)': R_vals,
        'V0 Usado (V)': V0_vals
    })
    st.dataframe(df, use_container_width=True)
    csv = df.to_csv(index=False).encode('utf-8')
    st.download_button("📥 Descargar CSV", csv, "marcapasos_datos.csv", "text/csv")

# --- Animación en Vivo ---
with tab3:
    st.subheader("▶️ Animación en Tiempo Real")
    
    fig_animated = go.Figure()
    fig_animated.add_trace(go.Scatter(x=[], y=[], mode='lines', line=dict(width=2), name='Voltaje'))
    if use_feedback:
        fig_animated.add_hline(y=V_min, line_dash="dot", line_color="red", annotation_text="V_min")
    fig_animated.update_layout(
        title="Animación en Tiempo Real - Pulso de Descarga",
        xaxis_title="Tiempo (s)",
        yaxis_title="Voltaje (V)",
        xaxis_range=[0, t[-1]],
        yaxis_range=[0, max(V)*1.1],
        template="plotly_white",
        height=500,
        xaxis=dict(fixedrange=True),
        yaxis=dict(fixedrange=True),
        uirevision="constant"
    )

    plot_placeholder = st.empty()
    plot_placeholder.plotly_chart(fig_animated, use_container_width=True)

    if st.button("▶️ Iniciar Animación"):
        with st.spinner("Iniciando animación..."):
            for i in range(1, len(t) + 1):
                fig_animated.data[0].x = t[:i]
                fig_animated.data[0].y = V[:i]
                plot_placeholder.plotly_chart(fig_animated, use_container_width=True)
                time.sleep(0.2)
            st.success("✅ Animación completada.")

# --- Modelo Matemático ---
with tab4:
    st.subheader("🧮 Resolución de la Ecuación Diferencial")

    st.markdown("""
    El marcapasos se modela como un **circuito RC en modo de descarga**, es decir, 
    el capacitor ya fue cargado previamente y ahora se descarga a través del tejido cardíaco 
    (representado por una resistencia \( R \)). **No hay fuente de voltaje activa** durante este proceso.
    """)

    st.markdown("### 📐 Ecuación diferencial del modelo")

    st.markdown("""
    Aplicando la **segunda ley de Kirchhoff** al lazo del circuito RC en descarga, 
    se obtiene la siguiente ecuación diferencial para la carga \( q(t) \) en el capacitor:
    """)

    st.latex(r'''
    \frac{dq}{dt} + \frac{1}{RC} q = 0
    ''')

    st.markdown("""
    - \( q(t) \): carga en el capacitor (culombios)  
    - \( R \): resistencia del tejido cardíaco + electrodo (Ω)  
    - \( C \): capacitancia del marcapasos (F)  
    - \( t \): tiempo (s)  

    Esta es una **ecuación diferencial ordinaria lineal, homogénea, de primer orden**.
    """)

    st.markdown("### Condición inicial")
    st.markdown("""
    Al inicio de la descarga (\( t = 0 \)), el capacitor tiene su carga máxima:
    """)
    st.latex(r'''
    q(0) = q_0 = C \cdot V_0
    ''')
    st.markdown(f"Donde \( V_0 = {V0_user}  \\text{{V}} \) es el voltaje inicial.")

    st.markdown("### Resolución paso a paso (método de separación de variables)")

    st.markdown("""
    **Paso 1:** Reescribimos la ecuación para aislar la derivada.
    """)
    st.latex(r'''
    \frac{dq}{dt} = -\frac{1}{RC} \, q
    ''')

    st.markdown("""
    **Paso 2:** Separamos las variables \( q \) y \( t \) en lados opuestos.
    """)
    st.latex(r'''
    \frac{dq}{q} = -\frac{1}{RC} \, dt
    ''')

    st.markdown("""
    **Paso 3:** Integramos ambos lados.  
    La integral de \( \\frac{1}{q} \) es \( \\ln|q| \), y la integral de una constante es lineal.
    """)
    st.latex(r'''
    \int \frac{dq}{q} = \int -\frac{1}{RC} \, dt \quad \Rightarrow \quad \ln|q| = -\frac{t}{RC} + C_1
    ''')
    st.markdown("Donde \( C_1 \) es la constante de integración.")

    st.markdown("""
    **Paso 4:** Eliminamos el logaritmo aplicando la exponencial.
    """)
    st.latex(r'''
    q(t) = e^{C_1} \cdot e^{-t/(RC)} = k \cdot e^{-t/(RC)}
    ''')
    st.markdown("Donde \( k = e^{C_1} \) es una nueva constante.")

    st.markdown("""
    **Paso 5:** Aplicamos la condición inicial \( q(0) = C V_0 \) para hallar \( k \).
    """)
    st.latex(r'''
    q(0) = k \cdot e^{0} = k = C V_0 \quad \Rightarrow \quad q(t) = C V_0 \, e^{-t/(RC)}
    ''')

    st.markdown("""
    **Paso 6:** Obtenemos el voltaje en el capacitor usando \( V_C(t) = \\dfrac{q(t)}{C} \).
    """)
    st.latex(r'''
    V_C(t) = V_0 \, e^{-t/(RC)}
    ''')

    st.markdown("###Solución final con tus parámetros")

    tau = R_base * C
    st.latex(rf'''
    V_C(t) = {V0_user} \cdot e^{{-t / {tau:.6f}}}
    ''')

    st.markdown(f"""
    - **Voltaje inicial**: $ V_0 = {V0_user}  \\text{{V}} $
    - **Resistencia**: $ R = {R_base}  \\Omega $
    - **Capacitancia**: $ C = {C_uF}  \\mu\\text{{F}} = {C:.2e}  \\text{{F}} $
    - **Constante de tiempo**: $ \\tau = RC = {tau*1000:.2f}  \\text{{ms}} $
    """)

    st.markdown("""
    ### 💡 ¿Qué significa esta solución?
    - El voltaje **decae exponencialmente** con el tiempo.
    - La **constante de tiempo \( \\tau = RC \)** indica cuánto tarda el voltaje en caer al **36.8%** de su valor inicial.
    - En **1τ**, se entrega la mayor parte de la energía útil del pulso.
    - Esta forma exponencial es **crítica para una estimulación cardíaca segura y eficaz**.
    """)

    st.info("✅ Esta solución analítica es la base de todas las simulaciones que ves en las otras pestañas. Cada gráfico que observas es la evaluación numérica de esta función.")