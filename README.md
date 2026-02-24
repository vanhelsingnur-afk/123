diff --git a/README.md b/README.md
index 6c96afafc9ddf6fc3c253055fae5e09556fb042d..8d59f7763a0816afead8727e9a6d5a6513da9f32 100644
--- a/README.md
+++ b/README.md
@@ -1 +1,39 @@
-# 123
\ No newline at end of file
+# ROAPP orders parser
+
+Скрипт для парсинга таблицы заказов со страницы `https://web.roapp.io/orders/table`.
+
+## Установка
+
+```bash
+python -m venv .venv
+source .venv/bin/activate
+pip install -r requirements.txt
+python -m playwright install chromium
+```
+
+## Запуск
+
+```bash
+ROAPP_EMAIL='you@example.com' \
+ROAPP_PASSWORD='your_password' \
+ROAPP_OUTPUT='orders.csv' \
+python parser_roapp_orders.py
+```
+
+Переменные окружения:
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
+> Если у аккаунта включена 2FA/капча или другая сложная авторизация — потребуется доработка под конкретный сценарий.
