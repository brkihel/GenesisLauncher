import tkinter as tk
from tkinter import messagebox, ttk
from PIL import Image, ImageTk
from updater import update_files, download_all_files,  CLIENT_DIRECTORY, fetch_server_file_list, check_for_updates, download_files, read_local_file_list, generate_local_file_list
import os
import sys
import logging
import subprocess
import threading
import random
import time

def resource_path(relative_path):
    """Obter o caminho absoluto para recursos, funciona para dev e para PyInstaller."""
    try:
        # PyInstaller cria uma pasta temporária e armazena o caminho em _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def create_gui():
    """Cria a interface gráfica do launcher."""
    root = tk.Tk()
    root.title("Genesis Project Launcher")
    root.geometry("854x480")
    root.minsize(854, 480)
    root.overrideredirect(True)

    # Centralizar a janela na tela
    screen_width = root.winfo_screenwidth()
    screen_height = root.winfo_screenheight()
    x = (screen_width // 2) - (854 // 2)
    y = (screen_height // 2) - (480 // 2)
    root.geometry(f'{854}x{480}+{x}+{y}')

    # Variáveis para armazenar as posições do mouse e da janela
    def start_move(event):
        global offset_x, offset_y
        offset_x = event.x
        offset_y = event.y

    def move_window(event):
        x = root.winfo_x() + (event.x - offset_x)
        y = root.winfo_y() + (event.y - offset_y)
        root.geometry(f"+{x}+{y}")

    # Fechar a janela
    def close_window():
        root.destroy()

    # Lista de caminhos para os arquivos de imagem de background
    bg_images = [
        resource_path('assets/images/1.jpg'),
        resource_path('assets/images/2.jpg'),
        resource_path('assets/images/3.jpg'),
        resource_path('assets/images/5.jpg')
    ]

    # Caminho para os arquivos de imagem
    bg_image_path = random.choice(bg_images)
    logo_image_path = resource_path('assets\\images\\logo.png')
    btn_idle_img_path = resource_path('assets\\images\\PLAY1.png')
    btn_press_img_path = resource_path('assets\\images\\PLAY2.png')
    btn_close_idle_img_path = resource_path('assets\\images\\CLOSE.png')
    btn_close_press_img_path = resource_path('assets\\images\\CLOSE2.png')

    # Adicionar logs para verificar os caminhos dos arquivos de imagem
    logging.info(f"bg_image_path: {bg_image_path}")
    logging.info(f"logo_image_path: {logo_image_path}")
    logging.info(f"btn_idle_img_path: {btn_idle_img_path}")
    logging.info(f"btn_press_img_path: {btn_press_img_path}")
    logging.info(f"btn_close_idle_img_path: {btn_close_idle_img_path}")
    logging.info(f"btn_close_press_img_path: {btn_close_press_img_path}")

    # Configuração do plano de fundo
    bg_image = Image.open(bg_image_path).resize((854, 480), Image.Resampling.LANCZOS)
    bg_photo = ImageTk.PhotoImage(bg_image)
    canvas = tk.Canvas(root, width=854, height=480, highlightthickness=0)
    canvas.pack(fill="both", expand=True)
    canvas.create_image(0, 0, image=bg_photo, anchor="nw")

    # Sistema de partículas
    particles = []

    def create_particle():
        """Cria uma nova partícula."""
        x = random.randint(0, 854)
        y = random.randint(0, 480)
        size = random.randint(1, 3)
        speed = random.uniform(0.5, 1.5)
        direction = random.uniform(-0.5, 0.5)
        particle = {
            'id': canvas.create_oval(x, y, x + size, y + size, fill='cyan', outline=''),
            'x': x,
            'y': y,
            'size': size,
            'speed': speed,
            'direction': direction
        }
        particles.append(particle)
        if len(particles) < 20:  # Limitar o número de partículas
            root.after(500, create_particle)  # Criar uma nova partícula a cada 500ms

    def animate_particles():
        """Anima as partículas."""
        for particle in particles:
            particle['y'] -= particle['speed']
            particle['x'] += particle['direction']
            if particle['y'] < 0:
                particle['y'] = 480
            if particle['x'] < 0 or particle['x'] > 854:
                particle['x'] = random.randint(0, 854)
            canvas.coords(particle['id'], particle['x'], particle['y'], particle['x'] + particle['size'], particle['y'] + particle['size'])
        root.after(50, animate_particles)

    # Iniciar a criação e animação das partículas
    create_particle()
    animate_particles()

    # Configuração do logo
    logo_image = Image.open(logo_image_path).resize((300, 210), Image.Resampling.LANCZOS)
    logo_photo = ImageTk.PhotoImage(logo_image)
    canvas.create_image(427, 240, image=logo_photo, anchor="center")

    # Configuração do botão Play
    btn_idle_img = ImageTk.PhotoImage(Image.open(btn_idle_img_path).resize((175, 80), Image.Resampling.LANCZOS))
    btn_press_img = ImageTk.PhotoImage(Image.open(btn_press_img_path).resize((175, 80), Image.Resampling.LANCZOS))

    # Barra de progresso personalizada
    progress_canvas = tk.Canvas(root, width=200, height=30, bg='#252a34', bd=0, highlightthickness=2, relief='ridge')
    progress_canvas.place(x=327, y=380)
    progress_bar = progress_canvas.create_rectangle(0, 0, 0, 30, fill='#cd5e0f', width=0)
    progress_text = progress_canvas.create_text(100, 15, text="0%", fill="white", font=('Helvetica', 12, 'bold'))

    # Rótulo para exibir o nome do arquivo e o tempo estimado de download
    download_label = tk.Label(root, text="", bg='#252a34', fg="white", font=('Helvetica', 8, 'bold'))
    download_label.place(x=287, y=350)

    def update_progress_bar(value, maximum):
        """Atualiza a barra de progresso e o texto de progresso."""
        progress_canvas.coords(progress_bar, 0, 0, (value / maximum) * 200, 30)
        progress_canvas.itemconfig(progress_text, text=f"{int((value / maximum) * 100)}%")
        root.update_idletasks()

    def update_download_label(filename, estimated_time):
        """Atualiza o rótulo com o nome do arquivo e o tempo estimado de download."""
        file_name = os.path.basename(filename)
        download_label.config(text=f"Updating: {file_name} : estimated download time {estimated_time}")
        root.update_idletasks()

    def on_button_press():
        """Inicia o cliente do jogo e fecha o launcher."""
        try:
            # Caminho completo para o executável
            executable_path = os.path.join(CLIENT_DIRECTORY, "genesisproject_gl_x64.exe")
            subprocess.Popen([executable_path], shell=True)
            print("Iniciando o cliente do jogo...")
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao iniciar o cliente: {e}")
            return

        # Fecha o launcher
        sys.exit(0)

    def on_button_down(event):
        canvas.itemconfig(play_button, image=btn_press_img)

    def on_button_release(event):
        canvas.itemconfig(play_button, image=btn_idle_img)
        on_button_press()

    play_button = canvas.create_image(427, 380, image=btn_idle_img, anchor="center")
    canvas.tag_bind(play_button, "<ButtonPress-1>", on_button_down)
    canvas.tag_bind(play_button, "<ButtonRelease-1>", on_button_release)

    # Botão para fechar o launcher
    btn_close_idle_img = ImageTk.PhotoImage(Image.open(btn_close_idle_img_path).resize((65, 56), Image.Resampling.LANCZOS))
    btn_close_press_img = ImageTk.PhotoImage(Image.open(btn_close_press_img_path).resize((65, 56), Image.Resampling.LANCZOS))

    def on_close_button_down(event):
        canvas.itemconfig(close_button, image=btn_close_press_img)

    def on_close_button_release(event):
        canvas.itemconfig(close_button, image=btn_close_idle_img)
        close_window()

    close_button = canvas.create_image(810, 30, image=btn_close_idle_img, anchor="ne")
    canvas.tag_bind(close_button, "<ButtonPress-1>", on_close_button_down)
    canvas.tag_bind(close_button, "<ButtonRelease-1>", on_close_button_release)

    # Áreas clicáveis para arrastar a janela
    drag_areas = [
        canvas.create_rectangle(0, 0, 8, 480, outline="", fill=""),  # Lateral esquerda
        canvas.create_rectangle(846, 0, 854, 480, outline="", fill=""),  # Lateral direita
        canvas.create_rectangle(0, 0, 854, 8, outline="", fill=""),  # Parte superior
        canvas.create_rectangle(0, 472, 854, 480, outline="", fill="")  # Parte inferior
    ]

    for area in drag_areas:
        canvas.tag_bind(area, "<ButtonPress-1>", start_move)
        canvas.tag_bind(area, "<B1-Motion>", move_window)

    def update_files_with_progress():
        """Atualiza os arquivos e atualiza a barra de progresso."""
        try:
            # Esconder o botão de play
            canvas.itemconfig(play_button, state='hidden')

            # Gerar local_file_list.json
            generate_local_file_list()

            # Ler listas do servidor e local
            server_file_list = fetch_server_file_list()
            if not server_file_list:
                logging.error("Não foi possível obter a lista de arquivos do servidor.")
                return False

            local_file_list = read_local_file_list()
            if local_file_list is None or not local_file_list:
                logging.info("Lista de arquivos locais está vazia. Baixando todos os arquivos do servidor.")
                download_all_files(server_file_list, update_progress_bar)
                return

            # Verificar atualizações
            files_to_update = check_for_updates(server_file_list, local_file_list)
            if not files_to_update:
                logging.info("Todos os arquivos estão atualizados. Nenhuma ação necessária.")
                return False

            logging.info(f"Atualizações necessárias para {len(files_to_update)} arquivo(s).")
            for i, file in enumerate(files_to_update):
                start_time = time.time()
                download_files([file], update_progress_bar)
                elapsed_time = time.time() - start_time
                estimated_time = time.strftime("%M:%S", time.gmtime(elapsed_time))
                update_download_label(file[0], estimated_time)
                update_progress_bar(i + 1, len(files_to_update))
            logging.info("Atualização concluída.")
            return True
        except Exception as e:
            logging.error(f"Erro no processo de atualização: {e}")
            return False
        finally:
            progress_canvas.place_forget()
            download_label.place_forget()
            canvas.itemconfig(play_button, state='normal')
            canvas.itemconfig(play_button, image=btn_idle_img)

    # Iniciar a verificação de atualizações em uma thread separada
    threading.Thread(target=update_files_with_progress).start()

    root.mainloop()