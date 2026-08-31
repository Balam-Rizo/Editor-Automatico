import streamlit as st
import os
from xml_generator import generar_xml_premiere
from ai_director import transcribir_y_mapear

# 1. Configuración de la página
st.set_page_config(page_title="Director AI", page_icon="🎬", layout="wide")

# 2. Asegurar que las carpetas existan
os.makedirs("media_input", exist_ok=True)
os.makedirs("media_output", exist_ok=True)

st.title("🎬 Orquestador de Edición AI")

# Creamos dos pestañas en la interfaz
tab1, tab2 = st.tabs(["✂️ 1. Limpieza de Silencios (XML)", "🧠 2. Análisis de Director (JSON)"])

# ==========================================
# PESTAÑA 1: LIMPIEZA DE SILENCIOS (XML)
# ==========================================
with tab1:
    st.write("Sube tu archivo bruto para limpiar silencios y generar el XML.")
    
    col1, col2 = st.columns([1, 2])

    with col1:
        st.subheader("⚙️ Parámetros de Corte")
        
        silence_thresh = st.slider(
            "Umbral de Silencio (dBFS)", 
            min_value=-60, max_value=-10, value=-36, step=1,
            help="Si el volumen baja de este nivel, se considera silencio."
        )
        
        # Ajustes actualizados: 1000ms para mantener un ritmo humano en la voz
        min_silence_len = st.slider(
            "Duración Mínima (milisegundos)", 
            min_value=100, max_value=2000, value=1000, step=100,
            help="Tiempo mínimo que debe durar el silencio para ser cortado."
        )
        
        # Ajustes actualizados: 300ms para dejar "aire" alrededor de los cortes
        keep_silence = st.slider(
            "Margen de Seguridad (milisegundos)", 
            min_value=50, max_value=800, value=300, step=10,
            help="Añade unos milisegundos de silencio antes y después de cada corte."
        )

    with col2:
        st.subheader("📁 Archivo de Video")
        uploaded_file = st.file_uploader("Arrastra tu gameplay (.mp4, .mov)", type=['mp4', 'mov'])
        
        if uploaded_file is not None:
            st.info(f"Archivo cargado: {uploaded_file.name} ({(uploaded_file.size / (1024*1024)):.2f} MB)")
            
            if st.button("🚀 Procesar Video y Generar XML", use_container_width=True, type="primary"):
                ruta_video = os.path.join("media_input", uploaded_file.name)
                
                with st.spinner('Guardando archivo en el disco...'):
                    with open(ruta_video, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                        
                st.success(f"¡Video guardado en {ruta_video}!")
                st.info("Analizando audio y calculando cortes... (Esto puede tardar un poco dependiendo del video)")
                
                nombre_sin_ext = os.path.splitext(uploaded_file.name)[0]
                ruta_xml = os.path.join("media_output", f"{nombre_sin_ext}_cortado.xml")
                
                try:
                    # Llamamos a nuestro motor con OpenCV
                    total_cortes = generar_xml_premiere(
                        ruta_video=ruta_video,
                        umbral_db=silence_thresh,
                        min_silencio_ms=min_silence_len,
                        padding_ms=keep_silence,
                        ruta_salida_xml=ruta_xml
                    )
                    
                    st.success(f"¡Éxito! Se eliminaron los silencios y se generaron {total_cortes} clips de video.")
                    
                    with open(ruta_xml, "r", encoding="utf-8") as f:
                        xml_data = f.read()
                        
                    st.download_button(
                        label="⬇️ Descargar Archivo XML para Premiere",
                        data=xml_data,
                        file_name=f"{nombre_sin_ext}_cortado.xml",
                        mime="application/xml",
                        type="primary"
                    )
                    
                except Exception as e:
                    st.error(f"Ocurrió un error al procesar el audio o video: {e}")

# ==========================================
# PESTAÑA 2: ANÁLISIS DE DIRECTOR (JSON)
# ==========================================
with tab2:
    st.header("🎙️ Dictado de Director en Vivo")
    st.write("Sube la pista donde dictaste los comandos. El sistema buscará palabras clave (ej. 'zoom 1', 'risa') y generará el mapa de efectos.")
    
    audio_file = st.file_uploader("Sube tu pista de comandos (.wav, .mp3)", type=['wav', 'mp3'])
    
    if audio_file is not None:
        if st.button("Analizar Comandos y Generar JSON", type="primary"):
            
            ruta_audio = os.path.join("media_input", audio_file.name)
            with open(ruta_audio, "wb") as f:
                f.write(audio_file.getbuffer())
                
            nombre_sin_ext = os.path.splitext(audio_file.name)[0]
            ruta_json = os.path.join("media_output", f"{nombre_sin_ext}_comandos.json")
            
            with st.spinner("Escuchando comandos y cruzando con el diccionario..."):
                try:
                    eventos = transcribir_y_mapear(ruta_audio, ruta_json)
                    
                    if len(eventos) > 0:
                        st.success(f"¡Se detectaron {len(eventos)} comandos en tu audio!")
                        st.json(eventos) # Mostramos el resultado en pantalla para que lo veas rápido
                        
                        with open(ruta_json, "r", encoding="utf-8") as f:
                            st.download_button(
                                "⬇️ Descargar Mapa de Comandos (JSON)",
                                f.read(),
                                file_name=f"{nombre_sin_ext}_comandos.json",
                                mime="application/json"
                            )
                    else:
                        st.warning("Se transcribió el audio, pero no se encontró ninguna palabra clave del diccionario.")
                        
                except Exception as e:
                    st.error(f"Error procesando el audio: {e}")