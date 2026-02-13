import whisper
import keyboard
import sounddevice as sd
import numpy as np
import wave
import os
import threading

from colorama import Fore,init
import webrtcvad
import time
import tkinter as tk
from transformers import pipeline


#CMD test
init(autoreset=True)

AUDIO_ARCHIVO = "temp_audio.wav"

# 🔹 Configuración del micrófono
SAMPLERATE = 48000  # Frecuencia de muestreo, 16k es lo unico compatible con webrtcvad
CHANNELS = 1  # Mono
DEVICE = 2 # 1 = dispositivo por defecto del sistema, 2 cable de audio virtual

# Configuracion del detector de actividad de voz (VAD)
vad = webrtcvad.Vad(3) #1,2,3 va subiendo la sensibilidad al silencio, 3 es max
CHUNK_DURATION = 30 # Duracion de cada corte de audio -> 10,20 o 30 -> 30 parece funcionar mejor para no perder muchas palabras en whisper
CHUNK_SIZE = int(SAMPLERATE*(CHUNK_DURATION/1000)) #Tamaño de cada corte
BUFFER_TIMEOUT = 10000 #Milisegundos de maxima duracion del buffer
SILENCE_TIMEOUT = 120 #Milisegundos de silencio para cortar y mandar directamente a whisper
NEWLINE_TIMEOUT = 1000
# Carga de modelo a la gpu, Turbo es el mejor para bidireccionalidad en idioma por ahora
print('Cargando el modelo en la GPU...')
model = whisper.load_model("turbo").to("cuda")

# Modelo basico de traduccion texto a texto (Pruebas)
translator_en_es = pipeline("translation", model="Helsinki-NLP/opus-mt-en-es")
translator_es_en = pipeline("translation", model="Helsinki-NLP/opus-mt-es-en")


def grabar_audio_VAD():
    stream = sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype=np.int16,
                            blocksize=CHUNK_SIZE, device=DEVICE)
    stream.start()
    speech_buffer = []
    print("Escuchando....")
    last_speech = time.time()

    while True:
        try:
            audio_chunk, _ = stream.read(CHUNK_SIZE)
            audio_data = np.frombuffer(audio_chunk, dtype=np.int16)
            is_speech = vad.is_speech(audio_data.tobytes(), sample_rate=SAMPLERATE)

            if is_speech and (len(speech_buffer) <= (BUFFER_TIMEOUT / CHUNK_DURATION)):
                speech_buffer.append(audio_data)
                last_speech = time.time()
            else:
                last_speech_time = (time.time() - last_speech) * 1000
                if (len(speech_buffer) > 1) and (last_speech_time > SILENCE_TIMEOUT):
                    audio_data = np.concatenate(speech_buffer)
                    with wave.open(AUDIO_ARCHIVO, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLERATE)
                        wf.writeframes(audio_data.tobytes())

                    try:
                        transcribir_audio()
                    except Exception as e:
                        print("[DEBUG]: Transcription error:", e)
                    speech_buffer = []

                if last_speech_time > NEWLINE_TIMEOUT:
                    stream_newline()

            # Actualiza GUI 
            scrollbar_en.config(command=transcription_en.yview)
            scrollbar_es.config(command=transcription_es.yview)
            root.update()

        except Exception as e:
            # Saltar el segmento y seguir grabando
            print("[DEBUG]: Audio capture error:", e)
            continue


def stream_newline():
    if transcription_en.get("end-2c") != '\n':
        transcription_en.config(state='normal')
        transcription_en.insert('end','\n\n')
        transcription_en.config(state='disabled')
    if transcription_es.get("end-2c") != '\n':
        transcription_es.config(state='normal')
        transcription_es.insert('end','\n\n')
        transcription_es.config(state='disabled')

# Transcribe el audio con whisper local
def transcribir_audio():
    try:
        result = model.transcribe(AUDIO_ARCHIVO, temperature=0, no_speech_threshold=0.6)
    except Exception as e:
        print("[DEBUG]: Transcription failed:", e)
        return
    noise_flag = False
    print(result.values())
    #Intento de reducir la cantidad de ruido de fondo clasificado como segmento, se requiere cierto grado de confianza para mostrar
    for segment in result["segments"]:
        if segment["avg_logprob"]< -0.85:
            noise_flag = True
        elif segment["end"] >= 29.98:
            noise_flag = True
            

    if noise_flag == False:
        text = result["text"]

    if result["language"] == "en":
        # Original EN
        transcription_en.config(state='normal')
        transcription_en.insert(tk.END, text + " ")
        transcription_en.see('end')
        transcription_en.config(state='disabled')

        # Traduccion ES
        translated = translator_en_es(text)[0]["translation_text"]

        transcription_es.config(state='normal')
        transcription_es.insert(tk.END, translated + " ")
        transcription_es.see('end')
        transcription_es.config(state='disabled')

        print(Fore.BLUE + text, end=' ')

    elif result["language"] == "es":
        # Original ES
        transcription_es.config(state='normal')
        transcription_es.insert(tk.END, text + " ")
        transcription_es.see('end')
        transcription_es.config(state='disabled')

        # Traduccion EN
        translated = translator_es_en(text)[0]["translation_text"]

        transcription_en.config(state='normal')
        transcription_en.insert(tk.END, translated + " ")
        transcription_en.see('end')
        transcription_en.config(state='disabled')

        print(Fore.GREEN + text, end=' ')

    else:
        print(text, end=' ')

def start_vad_thread():
    # Inicia un daemon_thread para detectar audio continuamente
    vad_thread = threading.Thread(target=grabar_audio_VAD, daemon=True)
    vad_thread.start()

def end_transcription():
    os._exit(0)

def clearEN():
        transcription_en.config(state='normal')
        transcription_en.delete('1.0','end')
        transcription_en.config(state='disabled')

def clearES():
        transcription_es.config(state='normal')
        transcription_es.delete('1.0','end')
        transcription_es.config(state='disabled')

#GUI
#Window (resolucion fija, arreglar)
root = tk.Tk()
root.title("Call Log")
root.geometry("500x1200")

label = tk.Label(root,text="Transcipcion de audio en vivo", font =("Helvetica",12))
label.pack(pady=20)

#Botones de inicio y fin
button = tk.Button(root,text="Start", command=start_vad_thread)
button.pack()

end_button = tk.Button(root,text="Quit", command=end_transcription)
end_button.pack(side=tk.BOTTOM,pady=120)

clear_button_en= tk.Button(root,text="Clear EN",command=clearEN)
clear_button_en.pack(side=tk.BOTTOM)

clear_button_es= tk.Button(root,text="Clear ES",command=clearES)
clear_button_es.pack(side=tk.BOTTOM,pady=10)

#Frame
main_frame = tk.Frame(root)
main_frame.pack(pady=20)

#Cuadro de texto en ingles
en_frame = tk.LabelFrame(main_frame,text="Texto en Ingles",padx=10,pady=10)
en_frame.pack(side=tk.TOP,pady=10)

scrollbar_en = tk.Scrollbar(en_frame) #barra deslizable
scrollbar_en.pack(side=tk.RIGHT, fill=tk.Y)

transcription_en = tk.Text(en_frame,wrap=tk.WORD,yscrollcommand=scrollbar_en.set,height=20,width=60,fg="#FFA500",state="disabled")# Solo lectura
transcription_en.pack(pady=20)

scrollbar_en.config(command=transcription_en.yview)

#Cuadro de texto para español
es_frame = tk.LabelFrame(main_frame,text="Texto en español",padx=10,pady=10)
es_frame.pack(side=tk.TOP,pady=10)

scrollbar_es = tk.Scrollbar(es_frame) #barra deslizable
scrollbar_es.pack(side=tk.RIGHT, fill=tk.Y)

transcription_es = tk.Text(es_frame,wrap=tk.WORD,yscrollcommand=scrollbar_es.set,height=20,width=60,fg="#008000",state='disabled')# Cuadro de texto, solo lectura
transcription_es.pack(pady=20)

scrollbar_es.config(command=transcription_es.yview)


#PARA TRANSCRIBIR ARCHIVOS DE AUDIO Y NO EN VIVO DESCOMENTAR Y CAMBIAR EL NOMBRE DE ARCHIVO
#transcribir_audio()

root.mainloop()


