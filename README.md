diff --git a/README.md b/README.md
index 6c96afafc9ddf6fc3c253055fae5e09556fb042d..13f3652c2761cc46efa797e12a2eb6476112b71d 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,77 @@
-# 123
\ No newline at end of file
+# ROAPP orders parser
+
+Скрипт для парсинга таблицы заказов со страницы `https://web.roapp.io/orders/table`.
+
+## Где это запускать
+
+Запускай **у себя на компьютере** (macOS/Linux/Windows) или на сервере, где есть:
+
+- Python 3.10+
+- доступ в интернет к `web.roapp.io`
+- возможность установить Playwright и Chromium
+
+> В этом чате я не могу войти в твой аккаунт на сайте за тебя, поэтому реальный запуск нужно делать в твоем окружении.
+
+## Быстрый старт (macOS / Linux)
+
+```bash
+python3 -m venv .venv
+source .venv/bin/activate
+pip install -r requirements.txt
+python -m playwright install chromium
+
+ROAPP_EMAIL='you@example.com' \
+ROAPP_PASSWORD='your_password' \
+ROAPP_OUTPUT='orders.csv' \
+python parser_roapp_orders.py
+```
+
+После выполнения рядом появится `orders.csv` (или файл, который укажешь в `ROAPP_OUTPUT`).
+
+## Быстрый старт (Windows PowerShell)
+
+```powershell
+py -m venv .venv
+.\.venv\Scripts\Activate.ps1
+pip install -r requirements.txt
+python -m playwright install chromium
+
+$env:ROAPP_EMAIL="you@example.com"
+$env:ROAPP_PASSWORD="your_password"
+$env:ROAPP_OUTPUT="orders.csv"
+python parser_roapp_orders.py
+```
+
+## Запуск в видимом браузере (для отладки)
+
+Если хочешь видеть, что делает скрипт:
+
+```bash
+ROAPP_HEADLESS=false ROAPP_EMAIL='you@example.com' ROAPP_PASSWORD='your_password' python parser_roapp_orders.py
+```
+
+## Переменные окружения
+
+- `ROAPP_EMAIL` — email для входа.
+- `ROAPP_PASSWORD` — пароль.
+- `ROAPP_OUTPUT` — путь к выходному файлу (`.csv` или `.json`, по умолчанию `orders.csv`).
+- `ROAPP_HEADLESS` — `true/false`, запуск браузера в headless-режиме (по умолчанию `true`).
+- `ROAPP_TIMEOUT_MS` — таймаут в миллисекундах (по умолчанию `45000`).
+
+## Что делает скрипт
+
+1. Открывает страницу заказов.
+2. Если отображается форма логина — вводит email/пароль и выполняет вход.
+3. Повторно открывает страницу заказов.
+4. Считывает заголовки и строки первой HTML-таблицы.
+5. Сохраняет данные в CSV/JSON.
+
+## Если не запускается
+
+- Ошибка `No module named playwright`:
+  - активируй venv
+  - выполни `pip install -r requirements.txt`
+- Ошибка про браузер:
+  - выполни `python -m playwright install chromium`
+- Если у тебя 2FA/капча:
+  - возможно, потребуется ручной вход и доработка сценария.
