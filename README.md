# ⚖️ Multithreaded Retail Scales Diagnostics

Специализированная десктопная утилита для параллельной сетевой диагностики парка электронных торговых весов в розничной сети. Позволяет оперативно локализовать сетевые сбои на кассовых и торговых узлах. В целом можно пинговать не только весы но и все оборудование что будет иметь одинаковые первые три октета IP адреса. 

![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python&logoColor=white)
![GUI](https://img.shields.io/badge/GUI-ttkbootstrap-blue)
![Architecture](https://img.shields.io/badge/Concurrency-threading-success)

---

## ✨ Возможности

* **Параллельный мониторинг:** опрос до 10 весовых комплексов одновременно в независимых фоновых потоках (`threading`).
* **Отзывчивый UI:** сетевые операции через `subprocess.Popen` не блокируют интерфейс и плавно обновляют логи через буфер `tkinter.after()`.
* **Анализ ответов:** парсинг вывода системной утилиты `ping` (поддержка CP866 и UTF-8) с валидацией успешных пакетов и времени отклика.
* **Цветовая индикация:** наглядный статус узла в реальном времени (зеленый — доступен, красный — сбой, желтый — идет проверка, серый — не активен).
* **Групповые действия:** массовый запуск и мгновенная остановка тестирования всех заполненных позиций в один клик.

---

## 🛠️ Стек технологий

* **Язык:** Python 3.10+
* **Интерфейс:** `tkinter`, `ttkbootstrap` (Darkly Theme)
* **Асинхронность и сеть:** `threading`, `subprocess`, `re`

---

## 🚀 Быстрый старт

### 1. Клонирование и зависимости
```bash
git clone [https://github.com/reeqwer-cmd/retail-scales-ping.git](https://github.com/reeqwer-cmd/retail-scales-ping.git)
cd retail-scales-ping
pip install -r requirements.txt