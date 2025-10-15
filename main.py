import os
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from yt_dlp import YoutubeDL
from pydub import AudioSegment

# ------------------------------------------------------------
# CONFIGURACIÓN BASE
# ------------------------------------------------------------
os.makedirs("downloads", exist_ok=True)

links = []  # Lista de canciones (url + título)

# ------------------------------------------------------------
# FUNCIONES PRINCIPALES
# ------------------------------------------------------------

def actualizar_estado(texto):
    lbl_estado.config(text=texto)

def mostrar_titulo(texto):
    lbl_titulo.config(text=texto)

def obtener_titulo_youtube(url):
    """Obtiene el título del video sin descargarlo."""
    try:
        opciones = {'quiet': True, 'skip_download': True}
        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(url, download=False)
            return info.get('title', 'Título no encontrado')
    except Exception as e:
        print(f"Error al obtener título: {e}")
        return "Título no disponible"

def agregar_enlace():
    enlace = entry_url.get().strip()
    if not enlace:
        messagebox.showwarning("Atención", "Por favor ingresa un enlace de YouTube.")
        return

    def tarea_titulo():
        btn_agregar.config(state="disabled")
        actualizar_estado("Obteniendo título del video...")
        titulo = obtener_titulo_youtube(enlace)
        lista_canciones.insert("end", titulo)
        links.append({"url": enlace, "titulo": titulo})
        entry_url.delete(0, "end")
        actualizar_estado("Canción agregada.")
        btn_agregar.config(state="normal")

    threading.Thread(target=tarea_titulo).start()

def eliminar_seleccion():
    seleccion = lista_canciones.curselection()
    if not seleccion:
        messagebox.showwarning("Atención", "Selecciona una canción para eliminar.")
        return

    index = seleccion[0]
    lista_canciones.delete(index)
    links.pop(index)
    actualizar_estado("Canción eliminada.")

def descargar_y_convertir(url, titulo, indice, total):
    """Descarga y convierte una canción de YouTube a MP3."""
    try:
        opciones = {
            'format': 'bestaudio/best',
            'outtmpl': f"downloads/{titulo}.%(ext)s",
            'quiet': True,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192'
            }],
        }

        with YoutubeDL(opciones) as ydl:
            ydl.download([url])

        progress["value"] = indice
        mostrar_titulo(f"Descargado: {titulo}")
    except Exception as e:
        print(f"Error descargando {titulo}: {e}")

def unir_audios(carpeta_origen, archivo_salida):
    """Une todos los MP3 en un solo archivo."""
    archivos_mp3 = [f for f in os.listdir(carpeta_origen) if f.endswith(".mp3")]
    if not archivos_mp3:
        return False

    combinado = AudioSegment.empty()
    for archivo in archivos_mp3:
        ruta = os.path.join(carpeta_origen, archivo)
        combinado += AudioSegment.from_mp3(ruta)

    combinado.export(archivo_salida, format="mp3")
    return True

def generar_recopilatorio():
    if not links:
        messagebox.showwarning("Atención", "Agrega al menos una canción antes de generar el recopilatorio.")
        return

    threading.Thread(target=proceso_recopilatorio).start()

def proceso_recopilatorio():
    total = len(links)
    progress["maximum"] = total
    progress["value"] = 0

    for i, data in enumerate(links, start=1):
        actualizar_estado(f"Descargando {i}/{total}...")
        mostrar_titulo(data["titulo"])
        descargar_y_convertir(data["url"], data["titulo"], i, total)

    # 🧠 Ejecutar guardado en el hilo principal
    def guardar_recopilatorio():
        nombre_final = filedialog.asksaveasfilename(
            title="Guardar recopilatorio como...",
            defaultextension=".mp3",
            filetypes=[("Archivo MP3", "*.mp3")],
            initialdir="recopilatorios"
        )

        if nombre_final:
            actualizar_estado("Unificando canciones...")
            exito = unir_audios("downloads", nombre_final)
            if exito:
                messagebox.showinfo("Completado", "Recopilatorio generado exitosamente 🎶")
                actualizar_estado("Listo.")
                mostrar_titulo("Tu recopilatorio está completo.")
            else:
                messagebox.showerror("Error", "No se encontraron archivos MP3 para unir.")
                actualizar_estado("Error en la unión de archivos.")
        else:
            actualizar_estado("Cancelado por el usuario.")
            mostrar_titulo("")

        # Limpieza de temporales
        for f in os.listdir("downloads"):
            os.remove(os.path.join("downloads", f))

        progress["value"] = 0

    root.after(0, guardar_recopilatorio)

# ------------------------------------------------------------
# INTERFAZ TKINTER
# ------------------------------------------------------------

root = tk.Tk()
root.title("🎵 Recopilador YouTube MP3 🎵")
root.geometry("640x500")
root.config(bg="#1E1E1E")

# Entrada de enlace
frame_input = tk.Frame(root, bg="#1E1E1E")
frame_input.pack(pady=10)
entry_url = tk.Entry(frame_input, width=60, font=("Segoe UI", 10))
entry_url.pack(side="left", padx=5)
btn_agregar = tk.Button(frame_input, text="Agregar", command=agregar_enlace, bg="#0078D7", fg="white", font=("Segoe UI", 9, "bold"))
btn_agregar.pack(side="left", padx=5)

# Lista de canciones
frame_lista = tk.Frame(root, bg="#1E1E1E")
frame_lista.pack(pady=10, fill="both", expand=True)
scroll = tk.Scrollbar(frame_lista)
scroll.pack(side="right", fill="y")
lista_canciones = tk.Listbox(
    frame_lista, 
    width=80, 
    height=12, 
    yscrollcommand=scroll.set,
    bg="#2D2D30", 
    fg="white",
    selectbackground="#0078D7",
    font=("Segoe UI", 10)
)
lista_canciones.pack(padx=10, pady=5, fill="both", expand=True)
scroll.config(command=lista_canciones.yview)

# Botones de acción
frame_botones = tk.Frame(root, bg="#1E1E1E")
frame_botones.pack(pady=10)
btn_eliminar = tk.Button(frame_botones, text="Eliminar canción", command=eliminar_seleccion, bg="#D83B01", fg="white", font=("Segoe UI", 9, "bold"))
btn_eliminar.pack(side="left", padx=5)
btn_recopilar = tk.Button(frame_botones, text="Generar recopilatorio", command=generar_recopilatorio, bg="#107C10", fg="white", font=("Segoe UI", 9, "bold"))
btn_recopilar.pack(side="left", padx=5)

# Barra de progreso
progress = ttk.Progressbar(root, orient="horizontal", length=500, mode="determinate", maximum=100)
progress.pack(pady=10)
style = ttk.Style()
style.theme_use('default')
style.configure("TProgressbar", troughcolor="#3C3C3C", background="#22C55E", thickness=20)

# Estado y título
lbl_titulo = tk.Label(root, text="", bg="#1E1E1E", fg="#FFD700", font=("Segoe UI", 10, "bold"))
lbl_titulo.pack(pady=5)
lbl_estado = tk.Label(root, text="Listo.", bg="#1E1E1E", fg="white", font=("Segoe UI", 9))
lbl_estado.pack(pady=5)

root.mainloop()