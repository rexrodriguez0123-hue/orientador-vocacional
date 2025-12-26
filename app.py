import streamlit as st
import os
import plotly.express as px
import pandas as pd
from utils import extract_text_from_pdf
from ai_logic import configure_genai, generate_questions_from_report, get_career_recommendations

# Configuración de la página
st.set_page_config(
    page_title="Orientador Vocacional IA",
    page_icon="🎓",
    layout="centered"
)

# Estilos CSS personalizados
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        margin-top: 20px;
    }
    .report-view {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        max-height: 200px;
        overflow-y: scroll;
        font-size: 0.8em;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🎓 Orientador Vocacional con IA")
st.write("Descubre tu futuro profesional analizando tus notas y preferencias.")

# --- Configuración de API Key ---
# Intentamos obtenerla de las variables de entorno (para Render/Local .env)
api_key = os.environ.get("GOOGLE_API_KEY")

# Si no está en el entorno, la pedimos en el sidebar
with st.sidebar:
    st.header("Configuración")
    if not api_key:
        api_key_input = st.text_input("Ingresa tu Gemini API Key", type="password")
        if api_key_input:
            api_key = api_key_input
            os.environ["GOOGLE_API_KEY"] = api_key_input
        st.info("Necesitas una API Key de Google Gemini. [Consíguela aquí](https://aistudio.google.com/app/apikey).")
    else:
        st.success("API Key detectada ✅")

    if st.button("Reiniciar Aplicación"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

# Validar que tengamos API Key antes de continuar
if not api_key:
    st.warning("👈 Por favor, ingresa tu API Key en la barra lateral para comenzar.")
    st.stop()

configure_genai(api_key)

# --- Estado de la Sesión ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'report_text' not in st.session_state:
    st.session_state.report_text = ""
if 'questions' not in st.session_state:
    st.session_state.questions = []
if 'answers' not in st.session_state:
    st.session_state.answers = {}
if 'recommendations' not in st.session_state:
    st.session_state.recommendations = []

# ==========================================
# PASO 1: SUBIR BOLETÍN
# ==========================================
if st.session_state.step == 1:
    st.header("1. Sube tu Boletín de Notas")
    st.write("Sube el PDF de tu último año escolar.")
    
    uploaded_file = st.file_uploader("Elige un archivo PDF", type="pdf")
    
    if uploaded_file is not None:
        if st.button("Analizar Boletín y Continuar"):
            with st.spinner("Leyendo PDF y analizando tu perfil académico..."):
                text = extract_text_from_pdf(uploaded_file)
                if len(text) < 50:
                    st.error("No se pudo extraer suficiente texto del PDF. Asegúrate de que no sea una imagen escaneada.")
                else:
                    st.session_state.report_text = text
                    # Generar preguntas con IA
                    questions = generate_questions_from_report(text)
                    if not questions:
                        st.error("No se pudieron generar las preguntas. Intenta de nuevo.")
                    else:
                        st.session_state.questions = questions
                        st.session_state.step = 2
                        st.rerun()

# ==========================================
# PASO 2: CUESTIONARIO
# ==========================================
elif st.session_state.step == 2:
    st.header("2. Conociéndote mejor")
    st.write("La IA ha generado estas preguntas basándose en tus notas para afinar la recomendación.")
    
    with st.expander("Ver texto extraído del boletín (para depuración)"):
        st.markdown(f'<div class="report-view">{st.session_state.report_text}</div>', unsafe_allow_html=True)

    with st.form("questions_form"):
        answers = []
        for i, q in enumerate(st.session_state.questions):
            ans = st.text_area(f"{i+1}. {q}", key=f"q_{i}")
            answers.append(ans)
        
        submitted = st.form_submit_button("Obtener mis Carreras Ideales")
        
        if submitted:
            # Validar que haya respondido algo (opcional, pero recomendado)
            if any(len(a.strip()) < 2 for a in answers):
                st.warning("Por favor, responde todas las preguntas con un poco más de detalle.")
            else:
                st.session_state.answers = answers
                with st.spinner("La IA está cruzando tus datos para encontrar tu vocación..."):
                    recs = get_career_recommendations(
                        st.session_state.report_text, 
                        st.session_state.questions, 
                        answers
                    )
                    st.session_state.recommendations = recs
                    st.session_state.step = 3
                    st.rerun()

# ==========================================
# PASO 3: RESULTADOS
# ==========================================
elif st.session_state.step == 3:
    st.header("3. Tus Carreras Ideales")
    st.success("¡Análisis completado!")
    
    recs = st.session_state.recommendations
    
    # Verificamos si hubo un error en la respuesta (si contiene la clave 'error')
    error_found = False
    if recs and isinstance(recs, list) and len(recs) > 0 and 'error' in recs[0]:
        error_found = True
        error_msg = recs[0]['error']
        raw_resp = recs[0].get('raw_response', 'N/A')
    
    if not recs or error_found:
        st.error("Hubo un problema generando las recomendaciones.")
        if error_found:
            st.warning(f"Detalle del error: {error_msg}")
            with st.expander("Ver respuesta cruda de la IA (para depuración)"):
                st.code(raw_resp)
        
        if st.button("Volver atrás e intentar de nuevo"):
            st.session_state.step = 2
            st.rerun()
    else:
        # Preparar datos para el gráfico
        df = pd.DataFrame(recs)
        
        # Gráfico de Barras Horizontales
        fig = px.bar(
            df, 
            x='porcentaje', 
            y='carrera', 
            orientation='h',
            text='porcentaje',
            title='Top 5 Carreras Sugeridas (% de Afinidad)',
            labels={'porcentaje': 'Afinidad (%)', 'carrera': 'Carrera'},
            color='porcentaje',
            color_continuous_scale='Viridis'
        )
        fig.update_traces(texttemplate='%{text}%', textposition='outside')
        fig.update_layout(yaxis={'categoryorder':'total ascending'}) # Ordenar de mayor a menor
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.subheader("Detalle de las Sugerencias")
        for rec in recs:
            with st.expander(f"**{rec['carrera']}** - {rec['porcentaje']}%"):
                st.write(rec['razon'])
        
        if st.button("Comenzar de nuevo"):
            st.session_state.step = 1
            st.session_state.report_text = ""
            st.session_state.questions = []
            st.session_state.recommendations = []
            st.rerun()
