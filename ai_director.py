import whisper
import json
import os
import re

# ==========================================
# EL DICCIONARIO DE DIRECTOR (VERSIÓN BÁSICA)
# ==========================================
DICCIONARIO_COMANDOS = {
    "zoom 1": {"accion": "zoom_in", "escala": 125, "tipo": "video"},
    "zoom épico": {"accion": "zoom_in", "escala": 180, "tipo": "video"},
    "boom": {"accion": "efecto_sonido", "archivo": "boom.wav", "tipo": "audio"},
    "grillo": {"accion": "efecto_sonido", "archivo": "grillos.wav", "tipo": "audio"},
    "censura": {"accion": "filtro", "efecto": "blanco_y_negro", "tipo": "video"}
}

def limpiar_texto(texto):
    """Quita puntos, comas y pasa todo a minúsculas para encontrar las palabras exactas."""
    return re.sub(r'[^\w\s]', '', texto.lower())

def transcribir_y_mapear(ruta_audio, ruta_salida_json, modelo_tamano="base"):
    """
    Transcribe el audio y busca frases del diccionario para asignar efectos.
    """
    print(f"Cargando modelo Whisper ({modelo_tamano})...")
    modelo = whisper.load_model(modelo_tamano)
    
    print("Transcribiendo y buscando comandos de dirección...")
    resultado = modelo.transcribe(ruta_audio, language="es", fp16=False)
    
    mapa_eventos = []
    
    for segmento in resultado["segments"]:
        texto_original = segmento["text"].strip()
        texto_limpio = limpiar_texto(texto_original)
        
        # Escanear el diccionario en busca de coincidencias
        comandos_detectados = []
        for frase_clave, instruccion in DICCIONARIO_COMANDOS.items():
            if frase_clave in texto_limpio:
                comandos_detectados.append(instruccion)
        
        # Solo guardamos el evento si detectó un comando (para mantener el JSON limpio)
        if len(comandos_detectados) > 0:
            evento = {
                "inicio_seg": round(segmento["start"], 2),
                "fin_seg": round(segmento["end"], 2),
                "lo_que_dijiste": texto_original,
                "efectos_a_aplicar": comandos_detectados
            }
            mapa_eventos.append(evento)
            
    with open(ruta_salida_json, "w", encoding="utf-8") as f:
        json.dump(mapa_eventos, f, indent=4, ensure_ascii=False)
        
    return mapa_eventos