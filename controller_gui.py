import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading

bot_process = None

def start_bot():
    global bot_process

    if bot_process is None:
        bot_process = subprocess.Popen(
            ["python", "bot_panini.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        status_label.config(text="🟢 Bot em execução", fg="green")

        # Thread para ler logs
        threading.Thread(target=read_logs, daemon=True).start()

    else:
        messagebox.showinfo("Info", "O bot já está a correr")

def stop_bot():
    global bot_process

    if bot_process is not None:
        bot_process.terminate()
        bot_process = None
        status_label.config(text="🔴 Bot parado", fg="red")
        log_box.insert(tk.END, "\n[INFO] Bot parado\n")
    else:
        messagebox.showinfo("Info", "O bot não está em execução")

def read_logs():
    global bot_process

    for line in bot_process.stdout:
        log_box.insert(tk.END, line)
        log_box.see(tk.END)  # auto scroll

def check_status():
    if bot_process is None:
        status_label.config(text="🔴 Bot parado", fg="red")
    else:
        status_label.config(text="🟢 Bot em execução", fg="green")

def on_close():
    stop_bot()
    root.destroy()

# -------- INTERFACE --------

root = tk.Tk()
root.title("Bot Panini Controller")
root.geometry("500x400")
root.resizable(False, False)

title = tk.Label(root, text="Controlo do Bot", font=("Arial", 14))
title.pack(pady=5)

status_label = tk.Label(root, text="🔴 Bot parado", font=("Arial", 12))
status_label.pack(pady=5)

btn_frame = tk.Frame(root)
btn_frame.pack(pady=5)

btn_start = tk.Button(btn_frame, text="▶ Iniciar", width=12, command=start_bot)
btn_start.grid(row=0, column=0, padx=5)

btn_stop = tk.Button(btn_frame, text="⏹ Parar", width=12, command=stop_bot)
btn_stop.grid(row=0, column=1, padx=5)

btn_status = tk.Button(btn_frame, text="🔄 Estado", width=12, command=check_status)
btn_status.grid(row=0, column=2, padx=5)

# Caixa de logs
log_box = scrolledtext.ScrolledText(root, width=60, height=15)
log_box.pack(pady=10)

root.protocol("WM_DELETE_WINDOW", on_close)

root.mainloop()