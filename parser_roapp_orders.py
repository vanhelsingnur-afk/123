from __future__ import annotations
import csv
import json
import os
import sys
from pathlib import Path
from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

BASE_URL = "https://web.roapp.io"
LOGIN_URL = f"{BASE_URL}/login"
ORDERS_URL = f"{BASE_URL}/orders/table"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def save_rows(rows: List[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    fieldnames: List[str] = sorted({key for row in rows for key in row.keys()})
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def parse_orders(email: str, password: str, output: Path, headless: bool, timeout_ms: int) -> int:
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(locale="ru-RU")
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            # Перейти на страницу логина
            page.goto(LOGIN_URL, wait_until="domcontentloaded")

            # Ждем поля email
            email_field = page.locator('input[type="email"], input[name*="email" i]').first
            password_field = page.locator('input[type="password"], input[name*="password" i]').first

            email_field.wait_for(state="visible")
            password_field.wait_for(state="visible")

            email_field.fill(email)
            password_field.fill(password)

            # Нажимаем Enter вместо клика
            password_field.press("Enter")

            # Ждем, пока таблица заказов загрузится
            page.goto(ORDERS_URL, wait_until="networkidle")
            table = page.locator("table").first
            table.wait_for(state="visible", timeout=timeout_ms)

            # Делаем скриншот для проверки, что залогинились
            page.screenshot(path="roapp_after_login.png")

            # Собираем заголовки
            headers = [h.inner_text().strip() for h in table.locator("thead th").all()]
            if not headers:
                first_row_cells = table.locator("tr").nth(0).locator("th,td").all()
                headers = [c.inner_text().strip() or f"column_{idx}" for idx, c in enumerate(first_row_cells)]

            rows: List[dict] = []
            body_rows = table.locator("tbody tr")
            total_rows = body_rows.count()

            for i in range(total_rows):
                cells = body_rows.nth(i).locator("td").all()
                values = [c.inner_text().strip() for c in cells]
                if not any(values):
                    continue

                row_data = {}
                for j, value in enumerate(values):
                    key = headers[j] if j < len(headers) and headers[j] else f"column_{j}"
                    row_data[key] = value
                rows.append(row_data)

            save_rows(rows, output)
            print(f"Saved {len(rows)} rows to {output}")
            return 0

        except PlaywrightTimeoutError as exc:
            print(f"Timeout while parsing orders table: {exc}", file=sys.stderr)
            page.screenshot(path="roapp_timeout.png")  # для отладки
            return 2
        finally:
            context.close()
            browser.close()


def main() -> int:
    email = os.getenv("ROAPP_EMAIL", "").strip()
    password = os.getenv("ROAPP_PASSWORD", "").strip()
    if not email or not password:
        print("Set ROAPP_EMAIL and ROAPP_PASSWORD environment variables.", file=sys.stderr)
        return 1

    output = Path(os.getenv("ROAPP_OUTPUT", "orders.csv"))
    headless = _env_bool("ROAPP_HEADLESS", True)
    timeout_ms = int(os.getenv("ROAPP_TIMEOUT_MS", "45000"))

    return parse_orders(
        email=email,
        password=password,
        output=output,
        headless=headless,
        timeout_ms=timeout_ms,
    )


if __name__ == "__main__":
    raise SystemExit(main())
