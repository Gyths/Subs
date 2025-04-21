import whisper
import keyboard
import sounddevice as sd
import numpy as np
import wave
import os

from colorama import Fore,init
import webrtcvad
import time
import tkinter as tk
# ADD VEC2VEC VAD for voice detection
    #DONE , test silero version later
# GUI with lang detection

#CMD Color test
init(autoreset=True)

AUDIO_ARCHIVO = "temp_audio.wav"

# 🔹 Configuración del micrófono
SAMPLERATE = 48000  # Frecuencia de muestreo, 16k es lo unico compatible con webrtcvad
CHANNELS = 1  # Mono
DEVICE = 2 # 1 = dispositivo por defecto del sistema

# Configuracion del detector de actividad de voz (VAD)
vad = webrtcvad.Vad(3) #1,2,3 va subiendo la sensibilidad al silencio, 3 es max
CHUNK_DURATION = 30 # Duracion de cada corte de audio -> 10,20 o 30 -> 30 parece funcionar mejor para no perder muchas palabras en whisper
CHUNK_SIZE = int(SAMPLERATE*(CHUNK_DURATION/1000)) #Tamaño de cada corte
BUFFER_TIMEOUT = 10000 #Milisegundos de maxima duracion del buffer
SILENCE_TIMEOUT = 120 #Milisegundos de silencio para cortar y mandar directamente a whisper
NEWLINE_TIMEOUT = 1000
# Usa GPU para acelerar (tiny, base, small, medium, large, turbo)
print('Cargando el modelo en la GPU...')
model = whisper.load_model("turbo").to("cuda")


# 🎙️ Función para grabar audio por deteccion de actividad de voz
def grabar_audio_VAD():

    #Inicializacion de microfono y buffer de audio
    stream = sd.InputStream(samplerate=SAMPLERATE, channels=CHANNELS, dtype= np.int16, blocksize= CHUNK_SIZE,device= DEVICE)
    stream.start()
    speech_buffer= []
    print("Escuchando....")
    print("Presiona 'Shift + `' para salir")
    
    last_speech = time.time()
    try:
        while True:
            audio_chunk,_ = stream.read(CHUNK_SIZE)
            audio_data = np.frombuffer(audio_chunk, dtype= np.int16)
            is_speech = vad.is_speech(audio_data.tobytes(),sample_rate= SAMPLERATE)
            
            #Si es dialogo y el buffer no ha llegado a su maxima capacidad (en este caso 10 segundos)
            if (is_speech and (len(speech_buffer)<=(BUFFER_TIMEOUT/CHUNK_DURATION))):
                speech_buffer.append(audio_data)
                last_speech = time.time()
            else:                
                last_speech_time = (time.time() - last_speech) * 1000
                #Si existe algo en el buffer y hay silencio por 120ms
                if((len(speech_buffer)>1) and last_speech_time>SILENCE_TIMEOUT):
                    audio_data = np.concatenate(speech_buffer)
                    with wave.open(AUDIO_ARCHIVO, "wb") as wf:
                        wf.setnchannels(CHANNELS)
                        wf.setsampwidth(2)
                        wf.setframerate(SAMPLERATE)
                        wf.writeframes(audio_data.tobytes())

                    transcribir_audio()
                    speech_buffer=[]
                
                if(last_speech_time>NEWLINE_TIMEOUT):
                        stream_newline()
            
            #Actualizacion de pantalla y cierre con teclado
            keyboard.add_hotkey("shift+`", lambda: os._exit(0))  # Cerrar con 'Shift + ~'``
            scrollbar_en.config(command=transcription_en.yview)
            scrollbar_es.config(command=transcription_es.yview)
            root.update()

    except Exception as e:
        print("Error al detectar audio")
    
    stream.stop()
    stream.close()

def stream_newline():
    if transcription_en.get("end-2c") != '\n':
        transcription_en.config(state='normal')
        transcription_en.insert('end','\n\n')
        transcription_en.config(state='disabled')
    if transcription_es.get("end-2c") != '\n':
        transcription_es.config(state='normal')
        transcription_es.insert('end','\n\n')
        transcription_es.config(state='disabled')

# 📜 Función para transcribir el audio con Whisper local
def transcribir_audio():
    #print("🔄 Transcribiendo...")
    result = model.transcribe(AUDIO_ARCHIVO)
    #print("📝 Transcripción: (", result["language"],") ", result["text"], end= ' ')
    if(result["language"]=='en'):
        transcription_en.config(state='normal')
        transcription_en.insert(tk.END,result["text"]+" ")
        transcription_en.see('end')
        transcription_en.config(state='disabled')
        print(Fore.BLUE + result["text"], end= ' ')
    elif(result["language"]=='es'):
        transcription_es.config(state='normal')
        transcription_es.insert(tk.END,result["text"]+" ")
        transcription_es.see('end')
        transcription_es.config(state='normal')
        print(Fore.GREEN + result["text"], end= ' ')
    else:
        print(result["text"], end= ' ')


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

#SIMPLE GUI SETUP
#Window
root = tk.Tk()
root.title("Gemas gratis de dragon city")
root.geometry("500x1200")

label = tk.Label(root,text="Cada dia menos chamba.com (no hay boton de acabar soy permanente)", font =("Helvetica",12))
label.pack(pady=20)

#Botones de inicio y fin
button = tk.Button(root,text="Empezar", command=grabar_audio_VAD)
button.pack()

end_button = tk.Button(root,text="Sicarear", command=end_transcription)
end_button.pack(side=tk.BOTTOM,pady=120)

clear_button_en= tk.Button(root,text="Clear EN",command=clearEN)
clear_button_en.pack(side=tk.BOTTOM)

clear_button_es= tk.Button(root,text="Clear ES",command=clearES)
clear_button_es.pack(side=tk.BOTTOM,pady=10)

#Frame que contiene todos los elementos graficos
main_frame = tk.Frame(root)
main_frame.pack(pady=20)

#Configuracion para cuadro de texto en ingles
en_frame = tk.LabelFrame(main_frame,text="El que te cobra 10k por mirarte a los ojos",padx=10,pady=10) #Frame que contiene los dos elementos cuadro de texto y barra
en_frame.pack(side=tk.TOP,pady=10)

scrollbar_en = tk.Scrollbar(en_frame) #barra deslizable
scrollbar_en.pack(side=tk.RIGHT, fill=tk.Y)

transcription_en = tk.Text(en_frame,wrap=tk.WORD,yscrollcommand=scrollbar_en.set,height=20,width=60,fg="#FFA500",state="disabled")# Cuadro de texto, solo lectura
transcription_en.pack(pady=20)

scrollbar_en.config(command=transcription_en.yview) #Funcionalidad de la barra / sin esto solo es un png que cuelga la ventana

#Configuracion cuadro de texto para español
es_frame = tk.LabelFrame(main_frame,text="Conchudo sin estudios",padx=10,pady=10)#Frame que contiene los dos elementos cuadro de texto y barra
es_frame.pack(side=tk.TOP,pady=10)

scrollbar_es = tk.Scrollbar(es_frame) #barra deslizable
scrollbar_es.pack(side=tk.RIGHT, fill=tk.Y)

transcription_es = tk.Text(es_frame,wrap=tk.WORD,yscrollcommand=scrollbar_es.set,height=20,width=60,fg="#008000",state='disabled')# Cuadro de texto, solo lectura
transcription_es.pack(pady=20)

scrollbar_es.config(command=transcription_es.yview) #Funcionalidad de la barra / sin esto solo es un png que cuelga la ventana

#Inicializa pantalla la 1ra vez
root.mainloop()

