import json
import google.generativeai as genai
import os

def enriquecer_mapa_con_gemini(ruta_json_entrada, ruta_json_salida, api_key):
    """
    Lee la transcripción, usa Gemini para analizar el contexto y añade comandos de edición.
    """
    print("Conectando con el cerebro de Gemini...")
    genai.configure(api_key=api_key)
    
    # Usamos el modelo Flash porque es extremadamente rápido y perfecto para leer JSON
    modelo = genai.GenerativeModel('gemini-1.5-flash') 
    
    # Abrimos tu JSON crudo
    with open(ruta_json_entrada, 'r', encoding='utf-8') as f:
        eventos = json.load(f)
        
    PROMPT_SISTEMA = """
    Eres un Director de Edición experto. Tu trabajo es leer una transcripción de un gameplay (JSON) y decidir qué efectos visuales y sonoros aplicar en cada momento para maximizar la retención.
    
    REGLAS DE EDICIÓN:
    1. COMANDOS DIRECTOS: Si el texto dice "COMANDO:" o algo similar (ej. "pon un zoom", "mete un meme"), obedece esa instrucción exactamente.
    2. AVATARES: Tienes dos personajes disponibles: 'tiburashi' y 'gatoñin'. 
       - Si el texto denota risa o burla, asigna el avatar: "tiburashi_riendo.png".
       - Si el texto denota enojo, frustración o gritos, asigna: "gatoñin_enojado.png".
       - Si el texto es neutral o explicativo, asigna: "tiburashi_hablando.png".
    3. EFECTOS (SFX): Si detectas una muerte (kill), un susto o un chiste, añade un efecto de sonido (ej. "boom.wav", "grillo.wav", "punch.wav").
    4. ZOOM: Aplica un zoom progresivo (escala: 120 o 150) en momentos de tensión.
    
    Devuelve ÚNICAMENTE un archivo JSON válido. Por cada segmento del JSON original, añade una clave "edicion" que contenga tus decisiones. No uses bloques de código ```json en tu respuesta, devuelve el texto plano.
    """
    
    # Convertimos los datos a texto para que Gemini los lea
    texto_a_analizar = json.dumps(eventos, indent=2, ensure_ascii=False)
    prompt_completo = f"{PROMPT_SISTEMA}\n\nAnaliza este JSON y devuélvelo enriquecido:\n{texto_a_analizar}"
    
    print("Analizando contexto y tomando decisiones creativas...")
    respuesta = modelo.generate_content(prompt_completo)
    
    # Limpiamos la respuesta por si la IA añade formato Markdown
    json_respuesta = respuesta.text.replace("```json", "").replace("```", "").strip()
    
    try:
        eventos_enriquecidos = json.loads(json_respuesta)
        # Guardamos el mapa final
        with open(ruta_json_salida, 'w', encoding='utf-8') as f:
            json.dump(eventos_enriquecidos, f, indent=4, ensure_ascii=False)
        return eventos_enriquecidos
    except json.JSONDecodeError:
        raise ValueError("Gemini no devolvió un JSON válido. Intenta de nuevo.")