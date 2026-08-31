import os
import cv2  # NUEVO: Para extraer propiedades de imagen
from urllib.parse import quote # NUEVO: Para generar URLs perfectas
from pydub import AudioSegment
from pydub.silence import detect_nonsilent

def generar_xml_premiere(ruta_video, umbral_db, min_silencio_ms, padding_ms, ruta_salida_xml):
    # 1. DETECTAR PROPIEDADES REALES DEL VIDEO
    print("Analizando propiedades del video...")
    cap = cv2.VideoCapture(ruta_video)
    if not cap.isOpened():
        print("Error: No se pudo leer el video. Verifica la ruta.")
        return 0
        
    fps_real = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()
    
    # Premiere necesita saber si el video usa formato NTSC (con decimales)
    if abs(fps_real - 29.97) < 0.2:
        TIMEBASE = 30
        ntsc = "TRUE"
    elif abs(fps_real - 59.94) < 0.2:
        TIMEBASE = 60
        ntsc = "TRUE"
    elif abs(fps_real - 23.976) < 0.2:
        TIMEBASE = 24
        ntsc = "TRUE"
    else:
        TIMEBASE = int(round(fps_real))
        ntsc = "FALSE"
        
    print(f"Propiedades de Video: {width}x{height} a {fps_real:.2f} FPS (Timebase: {TIMEBASE}, NTSC: {ntsc})")

    # 2. CARGAR AUDIO Y DETECTAR SILENCIOS
    print("Cargando audio del video...")
    audio = AudioSegment.from_file(ruta_video)
    
    # Extraemos también las propiedades reales del audio
    canales_audio = audio.channels
    sample_rate_audio = audio.frame_rate
    print(f"Propiedades de Audio: {canales_audio} canal(es), {sample_rate_audio} Hz")
    
    print("Analizando silencios...")
    chunks_con_voz = detect_nonsilent(
        audio, 
        min_silence_len=min_silencio_ms,
        silence_thresh=umbral_db
    )
    
    # 3. CONSTRUIR RUTA PERFECTA (Estándar FCP XML)
    nombre_archivo = os.path.basename(ruta_video)
    ruta_absoluta = os.path.abspath(ruta_video).replace('\\', '/')
    
    # Asegurarnos de que empiece con / para localhost
    if not ruta_absoluta.startswith('/'):
        ruta_absoluta = '/' + ruta_absoluta
        
    # quote() convierte espacios en %20 y maneja acentos, pero mantiene las barras '/' intactas
    ruta_encodeada = quote(ruta_absoluta, safe='/')
    pathurl = f"file://localhost{ruta_encodeada}"
    
    duration_total_frames = int((len(audio) / 1000.0) * TIMEBASE)
    
    # 4. GENERAR EL ENCABEZADO DEL XML
    xml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE xmeml>
<xmeml version="4">
    <project>
        <name>Director AI - Secuencia Limpia</name>
        <children>
            <sequence id="sequence-1">
                <name>Secuencia Autocortada</name>
                <duration>{duration_total_frames}</duration>
                <rate>
                    <timebase>{TIMEBASE}</timebase>
                    <ntsc>{ntsc}</ntsc>
                </rate>
                <media>
                    <video>
                        <format>
                            <samplecharacteristics>
                                <width>{width}</width>
                                <height>{height}</height>
                                <rate>
                                    <timebase>{TIMEBASE}</timebase>
                                    <ntsc>{ntsc}</ntsc>
                                </rate>
                            </samplecharacteristics>
                        </format>
                        <track>
"""
    
    clips_video = ""
    clips_audio = ""
    timeline_in = 0
    
    # 5. GENERAR LOS CORTES
    for i, (inicio_ms, fin_ms) in enumerate(chunks_con_voz):
        inicio_real_ms = max(0, inicio_ms - padding_ms)
        fin_real_ms = min(len(audio), fin_ms + padding_ms)
        
        start_frame = int((inicio_real_ms / 1000.0) * TIMEBASE)
        end_frame = int((fin_real_ms / 1000.0) * TIMEBASE)
        clip_duration = end_frame - start_frame
        
        timeline_out = timeline_in + clip_duration
        
        file_node = ""
        if i == 0:
            file_node = f"""
                                    <file id="file-1">
                                        <name>{nombre_archivo}</name>
                                        <pathurl>{pathurl}</pathurl>
                                        <rate>
                                            <timebase>{TIMEBASE}</timebase>
                                            <ntsc>{ntsc}</ntsc>
                                        </rate>
                                        <duration>{duration_total_frames}</duration>
                                        <media>
                                            <video>
                                                <samplecharacteristics>
                                                    <width>{width}</width>
                                                    <height>{height}</height>
                                                </samplecharacteristics>
                                            </video>
                                            <audio>
                                                <channelcount>{canales_audio}</channelcount>
                                                <samplecharacteristics>
                                                    <depth>16</depth>
                                                    <samplerate>{sample_rate_audio}</samplerate>
                                                </samplecharacteristics>
                                            </audio>
                                        </media>
                                    </file>"""
        else:
            file_node = f"""<file id="file-1"/>"""
            
        clips_video += f"""
                                <clipitem id="clipitem-V-{i}">
                                    <name>{nombre_archivo}</name>
                                    <enabled>TRUE</enabled>
                                    <duration>{duration_total_frames}</duration>
                                    <rate>
                                        <timebase>{TIMEBASE}</timebase>
                                        <ntsc>{ntsc}</ntsc>
                                    </rate>
                                    <start>{timeline_in}</start>
                                    <end>{timeline_out}</end>
                                    <in>{start_frame}</in>
                                    <out>{end_frame}</out>{file_node}
                                    <sourcetrack>
                                        <mediatype>video</mediatype>
                                        <trackindex>1</trackindex>
                                    </sourcetrack>
                                </clipitem>"""
        
        clips_audio += f"""
                                <clipitem id="clipitem-A-{i}">
                                    <name>{nombre_archivo}</name>
                                    <enabled>TRUE</enabled>
                                    <duration>{duration_total_frames}</duration>
                                    <rate>
                                        <timebase>{TIMEBASE}</timebase>
                                        <ntsc>{ntsc}</ntsc>
                                    </rate>
                                    <start>{timeline_in}</start>
                                    <end>{timeline_out}</end>
                                    <in>{start_frame}</in>
                                    <out>{end_frame}</out>
                                    <file id="file-1"/>
                                    <sourcetrack>
                                        <mediatype>audio</mediatype>
                                        <trackindex>1</trackindex>
                                    </sourcetrack>
                                </clipitem>"""
                                
        timeline_in = timeline_out
        
    xml_content += clips_video
    xml_content += f"""
                        </track>
                    </video>
                    <audio>
                        <format>
                            <samplecharacteristics>
                                <depth>16</depth>
                                <samplerate>{sample_rate_audio}</samplerate>
                            </samplecharacteristics>
                        </format>
                        <track>
"""
    xml_content += clips_audio
    xml_content += """
                        </track>
                    </audio>
                </media>
            </sequence>
        </children>
    </project>
</xmeml>
"""
    
    with open(ruta_salida_xml, "w", encoding="utf-8") as f:
        f.write(xml_content)
        
    return len(chunks_con_voz)