import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
import os
import re
import ttkbootstrap as tb
from ttkbootstrap.constants import *

# --- ЛОГИКА СЕТИ ---

def check_ping(ip_address, row_state):
    text_box = row_state["text_box"]
    status_label = row_state["status_label"]
    
    try:
        command = ["ping", "-t", ip_address]
        CREATE_NO_WINDOW = 0x08000000
        
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, creationflags=CREATE_NO_WINDOW)
        row_state["process"] = process
        
        success_count = 0
        fail_count = 0
        
        for line in iter(process.stdout.readline, b''):
            if not row_state["is_pinging"]:
                break
                
            try:
                output_line = line.decode('cp866').strip()
            except UnicodeDecodeError:
                output_line = line.decode('utf-8', errors='replace').strip()
                
            if output_line:
                # Пинг успешен, если есть ответ, байты и время
                is_reply = "Ответ от" in output_line or "Reply from" in output_line
                has_bytes = "байт" in output_line or "bytes" in output_line or "=" in output_line
                has_time = "мс" in output_line or "ms" in output_line or "TTL=" in output_line or "ttl=" in output_line
                
                if is_reply and has_bytes and has_time:
                    is_success = True
                else:
                    is_success = False
                
                if is_success:
                    success_count += 1
                    fail_count = 0
                    
                    if success_count >= 2:
                        def update_green(l=status_label):
                            l.config(bootstyle="success-inverse")
                        text_box.after(0, update_green)
                else:
                    fail_count += 1
                    success_count = 0
                    
                    def update_red(l=status_label):
                        l.config(bootstyle="danger-inverse")
                    text_box.after(0, update_red)
                
                # Выводим текст в лог
                def update_ui(l=output_line):
                    text_box.config(state=NORMAL)
                    text_box.insert(END, l + "\n")
                    
                    lines_count = int(text_box.index('end-1c').split('.')[0])
                    if lines_count > 30:
                        text_box.delete('1.0', f"{lines_count - 30}.0")
                        
                    text_box.see(END)
                    text_box.config(state=DISABLED)
                    
                text_box.after(0, update_ui)
                
    except Exception as e:
        def update_err():
            text_box.config(state=NORMAL)
            text_box.insert(END, f"\nКритическая ошибка:\n{e}\n")
            text_box.see(END)
            text_box.config(state=DISABLED)
            def set_error():
                status_label.config(bootstyle="danger-inverse")
            text_box.after(0, set_error)
        text_box.after(0, update_err)
    finally:
        if row_state["process"]:
            row_state["process"].terminate()
            row_state["process"] = None
        
        def reset_btn():
            row_state["btn"].config(text="▶ Пинг", bootstyle=PRIMARY)
            status_label.config(bootstyle="secondary-inverse")
        text_box.after(0, reset_btn)

def toggle_ping(base_ip, row_state):
    octet_entry = row_state["entry"]
    text_box = row_state["text_box"]
    btn = row_state["btn"]
    status_label = row_state["status_label"]
    
    if row_state["is_pinging"]:
        row_state["is_pinging"] = False
        btn.config(text="Останавливаем...", bootstyle=WARNING)
        return
        
    last_octet = octet_entry.get().strip()
    
    if not last_octet.isdigit() or not (0 <= int(last_octet) <= 255):
        messagebox.showwarning("Ошибка", "Введите корректное число от 0 до 255!")
        return

    full_ip = base_ip + last_octet
    
    text_box.config(state=NORMAL)
    text_box.delete(1.0, END)
    text_box.insert(END, f"Запуск непрерывного пинга: {full_ip}...\n")
    text_box.config(state=DISABLED)
    
    btn.config(text="⏹ Стоп", bootstyle=DANGER)
    row_state["is_pinging"] = True
    
    status_label.config(bootstyle="warning-inverse")
    
    thread = threading.Thread(target=check_ping, args=(full_ip, row_state))
    thread.daemon = True
    thread.start()

def start_all():
    for row in rows_data:
        if row["entry"].get().strip() and not row["is_pinging"]:
            toggle_ping(base_ip_global, row)

def stop_all():
    for row in rows_data:
        if row["is_pinging"]:
            toggle_ping(base_ip_global, row)

# --- ЛОГИКА ИНТЕРФЕЙСА ---

def go_to_second_screen():
    global base_ip_global
    
    pc_ip = ip_entry.get().strip()
    parts = pc_ip.split(".")
    
    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        messagebox.showerror("Ошибка", "Введите правильный IP-адрес (например: 192.168.1.55)")
        return
        
    base_ip_global = f"{parts[0]}.{parts[1]}.{parts[2]}."
    
    frame_step1.pack_forget()
    frame_step2.pack(fill=BOTH, expand=True, padx=10, pady=10)
    lbl_base_ip.config(text=f"Подсеть магазина: {base_ip_global}X")

# === ОСНОВНОЕ ОКНО ===
root = tb.Window(themename="darkly") 
root.title("Живой Пинг Весов v4 (Dark Edition)")
root.geometry("900x820")
root.option_add("*Font", "Arial 10") # ИЗМЕНЕНО НА ARIAL

base_ip_global = ""
rows_data = []

# --- ЭКРАН 1: Ввод IP ---
frame_step1 = tb.Frame(root)
frame_step1.pack(fill=BOTH, expand=True, padx=20, pady=50)

tb.Label(frame_step1, text="Введите IP-адрес ПК в магазине:", font=("Arial", 12)).pack(pady=10)
ip_entry = tb.Entry(frame_step1, font=("Arial", 14), justify="center")
ip_entry.pack(pady=10, fill=X)
ip_entry.insert(0, "192.168.1.100")

tb.Button(frame_step1, text="Далее ->", bootstyle=INFO, width=20, 
          command=go_to_second_screen).pack(pady=20)

# --- ЭКРАН 2: Список весов ---
frame_step2 = tb.Frame(root)
lbl_base_ip = tb.Label(frame_step2, text="", font=("Arial", 12, "bold"))
lbl_base_ip.pack(pady=(0, 10))

# Создаем заголовок таблицы
header_frame = tb.Frame(frame_step2)
header_frame.pack(fill=X, pady=(0, 5))
tb.Label(header_frame, text="Статус", width=8, anchor="w", font=("Arial", 9, "bold")).pack(side=LEFT, padx=(10, 0))
tb.Label(header_frame, text="Весы", width=8, anchor="w", font=("Arial", 9, "bold")).pack(side=LEFT)
tb.Label(header_frame, text="IP (последний октет)", width=20, anchor="w", font=("Arial", 9, "bold")).pack(side=LEFT, padx=5)
tb.Label(header_frame, text="Лог пинга (Терминал)", width=50, anchor="w", font=("Arial", 9, "bold")).pack(side=RIGHT, padx=5)

# Рисуем 10 строк
for i in range(1, 11):
    row_frame = tb.Frame(frame_step2)
    row_frame.pack(fill=X, pady=3)
    
    controls_frame = tb.Frame(row_frame)
    controls_frame.pack(side=LEFT, fill=Y, padx=5)
    
    # ЛАМПОЧКА (индикатор)
    status_label = tb.Label(controls_frame, text="   ", width=3, bootstyle="secondary-inverse")
    status_label.pack(side=LEFT, padx=(0, 15))
    
    tb.Label(controls_frame, text=f"Весы {i}:", width=6, anchor="w").pack(side=LEFT)
    octet_entry = tb.Entry(controls_frame, width=6, justify="center")
    octet_entry.pack(side=LEFT, padx=5)
    
    # Терминал (темно-серый фон, зеленый шрифт)
    text_output = tk.Text(row_frame, height=3, width=60, bg="#1e1e1e", fg="#00ff00", font=("Consolas", 9), relief="flat")
    text_output.pack(side=RIGHT, padx=5, fill=X, expand=True)
    text_output.insert(END, "Готово к проверке...")
    text_output.config(state=DISABLED)
    
    btn_ping = tb.Button(controls_frame, text="▶ Пинг", width=10, bootstyle=PRIMARY)
    btn_ping.pack(side=LEFT, padx=5)
    
    row_state = {
        "entry": octet_entry,
        "text_box": text_output,
        "btn": btn_ping,
        "is_pinging": False,
        "process": None,
        "status_label": status_label
    }
    
    btn_ping.config(command=lambda rs=row_state: toggle_ping(base_ip_global, rs))
    rows_data.append(row_state)

# Панель массового управления внизу
bottom_frame = tb.Frame(frame_step2)
bottom_frame.pack(side=BOTTOM, fill=X, pady=15)

tb.Button(bottom_frame, text="▶ Запустить все заполненные", bootstyle=SUCCESS, 
          command=start_all).pack(side=LEFT, expand=True, fill=X, padx=5)

tb.Button(bottom_frame, text="⏹ Остановить все", bootstyle=DANGER, 
          command=stop_all).pack(side=RIGHT, expand=True, fill=X, padx=5)

# Легенда цветов
legend_frame = tb.Frame(frame_step2)
legend_frame.pack(side=BOTTOM, fill=X, pady=5)

tb.Label(legend_frame, text="🟢 Работает", bootstyle=SUCCESS).pack(side=LEFT, padx=10)
tb.Label(legend_frame, text="🔴 Ошибка", bootstyle=DANGER).pack(side=LEFT, padx=10)
tb.Label(legend_frame, text="🟡 Проверка", bootstyle=WARNING).pack(side=LEFT, padx=10)
tb.Label(legend_frame, text="⚪ Не активен", bootstyle=SECONDARY).pack(side=LEFT, padx=10)

root.mainloop()
