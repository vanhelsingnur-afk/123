
"""Parse orders data from https://web.roapp.io/orders/table using Playwright."""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from pathlib import Path
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from playwright.sync_api import Page

BASE_URL = "https://web.roapp.io"
ORDERS_URL = f"{BASE_URL}/orders/table"
LOGIN_URL = f"{BASE_URL}/login"


def _env_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_bool(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def _dedupe_headers(headers: Iterable[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: list[str] = []
    for idx, header in enumerate(headers, start=1):
        name = header.strip() or f"column_{idx}"
        counts[name] = counts.get(name, 0)  +1
        if counts[name] > 1:
            name = f"{name}_{counts[name]}"
        result.append(name)
    return result


def save_rows(rows: list[dict], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.suffix.lower() == ".json":
        output_path.write_text(json.dumps(rows, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    fieldnames: list[str] = sorted({key for row in rows for key in row.keys()})
    if not fieldnames:
        fieldnames = ["empty"]
        rows = [{"empty": ""}]

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def _is_login_page(page: "Page") -> bool:
    is_login_url = "/login" in page.url
    password_fields = page.locator('input#password, input[type="password"], input[name*="password" i]').count()
    login_fields = page.locator('input#login, input[type="email"], input[name*="email" i], input[name*="login" i]').count()
    table_visible = page.locator("table").count() > 0
    return (is_login_url or (password_fields > 0 and login_fields > 0)) and not table_visible


def _try_login(page: "Page", email: str, password: str) -> None:
    page.goto(LOGIN_URL, wait_until="domcontentloaded")
    page.fill("#login", email)
    page.fill("#password", password)
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")


def _wait_manual_login(page: "Page", timeout_ms: int) -> bool:
    deadline = time.time()  (timeout_ms / 1000)
    while time.time() < deadline:
        if page.locator("table").count() > 0 and not _is_login_page(page):
            return True
        page.wait_for_timeout(1000)
    return False


def parse_orders(
    email: str,
    password: str,
    output: Path,
    headless: bool,
    timeout_ms: int,
    storage_state: Path | None,
    manual_login: bool,
) -> int:
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
    from playwright.sync_api import sync_playwright

    context_kwargs: dict = {"locale": "ru-RU"}
    if storage_state and storage_state.exists():
        context_kwargs["storage_state"] = str(storage_state)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.set_default_timeout(timeout_ms)

        try:
            if email and password:
                _try_login(page, email, password)

            page.goto(ORDERS_URL, wait_until="domcontentloaded")

            if _is_login_page(page):
                if email and password:
                    _try_login(page, email, password)
                elif manual_login and not headless:
                    print("Manual login mode: complete login/2FA in opened browser window...", file=sys.stderr)
                    if not _wait_manual_login(page, timeout_ms):
                        print("Manual login timeout reached before orders table became visible.", file=sys.stderr)
                        return 4
                else:
                    print(
                        "Detected login page, but credentials are missing. "
                        "Provide --email/--password, --storage-state, or --manual-login with --headless false.",
                        file=sys.stderr,
                    )
                    return 1

            page.goto(ORDERS_URL, wait_until="networkidle")

            if _is_login_page(page):
                print("Login failed or requires 2FA/captcha/manual verification.", file=sys.stderr)
                return 3

            table = page.locator("table").first
            table.wait_for(state="visible")

            headers = [h.inner_text().strip() for h in table.locator("thead th").all()]
            if not headers:
                first_row_cells = table.locator("tr").nth(0).locator("th,td").all()
                headers = [c.inner_text().strip() for c in first_row_cells]
            headers = _dedupe_headers(headers)

            rows: list[dict] = []
            body_rows = table.locator("tbody tr")
            total_rows = body_rows.count()

            for i in range(total_rows):
                cells = body_rows.nth(i).locator("td").all()
                values = [c.inner_text().strip() for c in cells]
                if not any(values):
                    continue

                row_data: dict[str, str] = {}
                for j, value in enumerate(values):
                    key = headers[j] if j < len(headers) else f"column_{j1}"
                    row_data[key] = value
                rows.append(row_data)

            if storage_state:
                context.storage_state(path=str(storage_state))

            save_rows(rows, output)
            print(f"Saved {len(rows)} rows to {output}")
            return 0

        except PlaywrightTimeoutError as exc:
            print(f"Timeout while parsing orders table: {exc}", file=sys.stderr)
            return 2
        finally:
            context.close()
            browser.close()


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ROAPP orders table parser")
    parser.add_argument("--email", default=os.getenv("ROAPP_EMAIL", "").strip())
    parser.add_argument("--password", default=os.getenv("ROAPP_PASSWORD", "").strip())
    parser.add_argument("--output", default=os.getenv("ROAPP_OUTPUT", "orders.csv"))
    parser.add_argument("--headless", default=os.getenv("ROAPP_HEADLESS", "true"))
    parser.add_argument("--manual-login", action="store_true", default=_env_bool("ROAPP_MANUAL_LOGIN", False))
    parser.add_argument("--timeout-ms", type=int, default=int(os.getenv("ROAPP_TIMEOUT_MS", "45000")))
    parser.add_argument("--storage-state", default=os.getenv("ROAPP_STORAGE_STATE", "").strip())
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    output = Path(args.output)
    headless = _parse_bool(str(args.headless))
    storage_state = Path(args.storage_state) if args.storage_state else None

    return parse_orders(
        email=args.email,
        password=args.password,
        output=output,
        headless=headless,
        timeout_ms=args.timeout_ms,
        storage_state=storage_state,
        manual_login=args.manual_login,
    )


if __name__ == "__main__":
    raise SystemExit(main())
