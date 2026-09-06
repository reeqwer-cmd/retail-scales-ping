"""
ping_scales.py - Утилита мониторинга сетевого статуса весов
Стилизовано под тему Catppuccin Mocha (theme.py)
"""

import os
import sys
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import ttk
import ttkbootstrap as tb
from theme import Theme

# --- ЛОГИКА СЕТИ ---

def check_ping(ip_address, row_state):
    text_box = row_state["text_box"]
    status_indicator = row_state["status_indicator"]

    try:
        if sys.platform == "win32":
            command = ["ping", "-t", ip_address]
            flags = 0x08000000
        else:
            command = ["ping", ip_address]
            flags = 0

        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            creationflags=flags
        )
        row_state["process"] = process

        success_count = 0
        fail_count = 0

        for line in iter(process.stdout.readline, b''):
            if not row_state["is_pinging"]:
                break

            try:
                output_line = line.decode('cp866' if sys.platform == "win32" else 'utf-8').strip()
            except UnicodeDecodeError:
                output_line = line.decode('utf-8', errors='replace').strip()

            if output_line:
                line_lower = output_line.lower()
                is_reply = any(k in line_lower for k in ["ответ от", "reply from", "bytes from"])
                has_bytes = any(k in line_lower for k in ["байт", "bytes", "="])
                has_time = any(k in line_lower for k in ["мс", "ms", "ttl="])

                is_success = is_reply and has_bytes and has_time

                if is_success:
                    success_count += 1
                    fail_count = 0
                    if success_count >= 2:
                        text_box.after(0, lambda: status_indicator.config(bg=Theme.SUCCESS))
                else:
                    fail_count += 1
                    success_count = 0
                    text_box.after(0, lambda: status_indicator.config(bg=Theme.DANGER))

                def update_ui(l=output_line):
                    text_box.config(state=tk.NORMAL)
                    text_box.insert(tk.END, l + "\n")
                    lines_count = int(text_box.index('end-1c').split('.')[0])
                    if lines_count > 30:
                        text_box.delete('1.0', f"{lines_count - 30}.0")
                    text_box.see(tk.END)
                    text_box.config(state=tk.DISABLED)

                text_box.after(0, update_ui)

    except Exception as e:
        def update_err():
            text_box.config(state=tk.NORMAL)
            text_box.insert(tk.END, f"\nОшибка: {e}\n")
            text_box.see(tk.END)
            text_box.config(state=tk.DISABLED)
            status_indicator.config(bg=Theme.DANGER)

        text_box.after(0, update_err)
    finally:
        if row_state["process"]:
            try:
                row_state["process"].terminate()
            except Exception:
                pass
            row_state["process"] = None

        def reset_btn():
            row_state["btn"].config(
                text="▶ Пинг",
                bg=Theme.ACCENT_BTN,
                fg=Theme.ACCENT_TEXT
            )
            status_indicator.config(bg=Theme.FG_DISABLED)

        text_box.after(0, reset_btn)


def toggle_ping(base_ip, row_state):
    octet_entry = row_state["entry"]
    text_box = row_state["text_box"]
    btn = row_state["btn"]
    status_indicator = row_state["status_indicator"]

    if row_state["is_pinging"]:
        row_state["is_pinging"] = False
        btn.config(text="Остановка...", bg=Theme.BG_HOVER, fg=Theme.WARNING)
        return

    last_octet = octet_entry.get().strip()
    if not last_octet.isdigit() or not (0 <= int(last_octet) <= 255):
        messagebox.showwarning("Ошибка", "Введите корректное число октета от 0 до 255!")
        return

    full_ip = base_ip + last_octet

    text_box.config(state=tk.NORMAL)
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, f"Запуск непрерывного пинга: {full_ip}...\n")
    text_box.config(state=tk.DISABLED)

    btn.config(text="⏹ Стоп", bg=Theme.DANGER, fg="#ffffff")
    row_state["is_pinging"] = True
    status_indicator.config(bg=Theme.WARNING)

    thread = threading.Thread(target=check_ping, args=(full_ip, row_state), daemon=True)
    thread.start()


def start_all():
    for row in rows_data:
        if row["entry"].get().strip() and not row["is_pinging"]:
            toggle_ping(base_ip_global, row)


def stop_all():
    for row in rows_data:
        if row["is_pinging"]:
            toggle_ping(base_ip_global, row)


def go_to_second_screen():
    global base_ip_global

    pc_ip = ip_entry.get().strip()
    parts = pc_ip.split(".")

    if len(parts) != 4 or not all(p.isdigit() for p in parts):
        messagebox.showerror("Ошибка", "Введите корректный IP-адрес (например: 192.168.1.55)")
        return

    base_ip_global = f"{parts[0]}.{parts[1]}.{parts[2]}."

    frame_step1.pack_forget()
    frame_step2.pack(fill=tk.BOTH, expand=True, padx=12, pady=10)
    lbl_base_ip.config(text=f"Подсеть магазина: {base_ip_global}X")


# === ОСНОВНОЕ ОКНО ===
root = tb.Window(themename="darkly")
root.title("Мониторинг пинга весов")
root.geometry("980x860")
root.minsize(860, 700)
root.configure(bg=Theme.BG_BASE)

base_ip_global = ""
rows_data = []

# --- ЭКРАН 1: Ввод IP ---
frame_step1 = tk.Frame(root, bg=Theme.BG_BASE)
frame_step1.pack(fill=tk.BOTH, expand=True, padx=40, pady=60)

card_step1 = tk.Frame(frame_step1, bg=Theme.BG_CARD, padx=30, pady=30)
card_step1.pack(expand=True, fill=tk.X)

tk.Label(
    card_step1,
    text="Введите IP-адрес любого ПК или устройства в магазине:",
    bg=Theme.BG_CARD,
    fg=Theme.FG_MAIN,
    font=("Segoe UI", 12, "bold")
).pack(pady=(0, 15))

ip_entry = tk.Entry(
    card_step1,
    font=("Segoe UI", 14),
    justify="center",
    bg=Theme.BG_INPUT,
    fg=Theme.FG_MAIN,
    insertbackground=Theme.FG_MAIN,
    relief="flat",
    highlightthickness=1,
    highlightbackground=Theme.BG_HOVER,
    highlightcolor=Theme.ACCENT_BTN
)
ip_entry.pack(pady=10, fill=tk.X, ipady=6)
ip_entry.insert(0, "192.168.1.100")
ip_entry.bind("<Return>", lambda e: go_to_second_screen())

btn_next = tk.Button(
    card_step1,
    text="Перейти к списку весов →",
    bg=Theme.ACCENT_BTN,
    fg=Theme.ACCENT_TEXT,
    activebackground=Theme.ACCENT_HOVER,
    activeforeground=Theme.ACCENT_TEXT,
    font=("Segoe UI", 10, "bold"),
    relief="flat",
    cursor="hand2",
    pady=8,
    command=go_to_second_screen
)
btn_next.pack(pady=(15, 0), fill=tk.X)

# --- ЭКРАН 2: Список весов ---
frame_step2 = tk.Frame(root, bg=Theme.BG_BASE)

top_info_frame = tk.Frame(frame_step2, bg=Theme.BG_BASE)
top_info_frame.pack(fill=tk.X, pady=(0, 8))

lbl_base_ip = tk.Label(
    top_info_frame,
    text="",
    bg=Theme.BG_BASE,
    fg=Theme.ACCENT_BTN,
    font=("Segoe UI", 11, "bold")
)
lbl_base_ip.pack(side=tk.LEFT)

# Заголовок таблицы
header_frame = tk.Frame(frame_step2, bg=Theme.BG_BASE)
header_frame.pack(fill=tk.X, pady=(0, 4))
tk.Label(header_frame, text="Статус", width=6, anchor="center", bg=Theme.BG_BASE, fg=Theme.FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=(6, 4))
tk.Label(header_frame, text="Весы", width=9, anchor="w", bg=Theme.BG_BASE, fg=Theme.FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
tk.Label(header_frame, text="Октет", width=8, anchor="center", bg=Theme.BG_BASE, fg=Theme.FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
tk.Label(header_frame, text="Действие", width=12, anchor="center", bg=Theme.BG_BASE, fg=Theme.FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=5)
tk.Label(header_frame, text="Терминал ответов ping", anchor="w", bg=Theme.BG_BASE, fg=Theme.FG_MUTED, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT, padx=12)

# 10 строк весов
for i in range(1, 11):
    row_frame = tk.Frame(frame_step2, bg=Theme.BG_CARD, padx=8, pady=4)
    row_frame.pack(fill=tk.X, pady=2)

    # Индикатор
    indicator = tk.Label(row_frame, text="", width=2, height=1, bg=Theme.FG_DISABLED, relief="flat")
    indicator.pack(side=tk.LEFT, padx=(4, 10))

    # Номер весов
    tk.Label(row_frame, text=f"Весы {i:02d}", width=8, anchor="w", bg=Theme.BG_CARD, fg=Theme.FG_MAIN, font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)

    # Октет
    octet_entry = tk.Entry(
        row_frame,
        width=6,
        justify="center",
        bg=Theme.BG_INPUT,
        fg=Theme.FG_MAIN,
        insertbackground=Theme.FG_MAIN,
        relief="flat",
        highlightthickness=1,
        highlightbackground=Theme.BG_HOVER,
        highlightcolor=Theme.ACCENT_BTN,
        font=("Segoe UI", 9)
    )
    octet_entry.pack(side=tk.LEFT, padx=5, ipady=3)

    # Кнопка Пинг
    btn_ping = tk.Button(
        row_frame,
        text="▶ Пинг",
        width=10,
        bg=Theme.ACCENT_BTN,
        fg=Theme.ACCENT_TEXT,
        activebackground=Theme.ACCENT_HOVER,
        activeforeground=Theme.ACCENT_TEXT,
        relief="flat",
        font=("Segoe UI", 8, "bold"),
        cursor="hand2",
        pady=3
    )
    btn_ping.pack(side=tk.LEFT, padx=5)

    # Терминал лога
    text_output = tk.Text(
        row_frame,
        height=2,
        bg=Theme.BG_INPUT,
        fg=Theme.SUCCESS,
        insertbackground=Theme.FG_MAIN,
        relief="flat",
        font=("Consolas", 9),
        padx=6,
        pady=3
    )
    text_output.pack(side=tk.LEFT, padx=(8, 4), fill=tk.X, expand=True)
    text_output.insert(tk.END, "Готово к проверке...")
    text_output.config(state=tk.DISABLED)

    row_state = {
        "entry": octet_entry,
        "text_box": text_output,
        "btn": btn_ping,
        "is_pinging": False,
        "process": None,
        "status_indicator": indicator
    }

    btn_ping.config(command=lambda rs=row_state: toggle_ping(base_ip_global, rs))
    rows_data.append(row_state)

# Панель массового управления внизу
bottom_frame = tk.Frame(frame_step2, bg=Theme.BG_BASE)
bottom_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(8, 2))

btn_start_all = tk.Button(
    bottom_frame,
    text="▶ Запустить все заполненные",
    bg=Theme.BG_CARD,
    fg=Theme.SUCCESS,
    activebackground=Theme.BG_HOVER,
    activeforeground=Theme.SUCCESS,
    font=("Segoe UI", 9, "bold"),
    relief="flat",
    cursor="hand2",
    pady=6,
    command=start_all
)
btn_start_all.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

btn_stop_all = tk.Button(
    bottom_frame,
    text="⏹ Остановить все",
    bg=Theme.BG_CARD,
    fg=Theme.DANGER,
    activebackground=Theme.BG_HOVER,
    activeforeground=Theme.DANGER,
    font=("Segoe UI", 9, "bold"),
    relief="flat",
    cursor="hand2",
    pady=6,
    command=stop_all
)
btn_stop_all.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

# Легенда цветов
legend_frame = tk.Frame(frame_step2, bg=Theme.BG_SIDEBAR, padx=10, pady=4)
legend_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=(10, 4))

tk.Label(legend_frame, text="● Доступен", bg=Theme.BG_SIDEBAR, fg=Theme.SUCCESS, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
tk.Label(legend_frame, text="● Недоступен", bg=Theme.BG_SIDEBAR, fg=Theme.DANGER, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
tk.Label(legend_frame, text="● Проверка...", bg=Theme.BG_SIDEBAR, fg=Theme.WARNING, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)
tk.Label(legend_frame, text="● Ожидание", bg=Theme.BG_SIDEBAR, fg=Theme.FG_DISABLED, font=("Segoe UI", 9)).pack(side=tk.LEFT, padx=10)

root.mainloop()