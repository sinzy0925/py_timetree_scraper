import os
import json
import requests # 追加
from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import re

# 既存のロジックは変更なし
load_dotenv()
TIMETREE_EMAIL = os.getenv("TIMETREE_EMAIL")
TIMETREE_PASSWORD = os.getenv("TIMETREE_PASSWORD")
CALENDAR_URL = os.getenv("TIMETREE_CALENDAR_URL")
GAS_WEBAPP_URL = os.getenv("GAS_WEBAPP_URL") # 追加

# 既存のスクレイピング関数は変更なし
def get_events_with_playwright_logic(page):
    """
    Playwrightの標準的なAPIを使用して、カレンダーのイベント情報を取得します。
    """
    events = []
    month_year = page.locator('time').get_attribute('datetime')
    event_elements = page.locator('.lndlxo5').all()
    for event_element in event_elements:
        style = event_element.get_attribute('style')
        if not style:
            continue
        day_of_month_match = re.search(r'--lndlxo3: (\d+)', style)
        if not day_of_month_match:
            continue
        day_of_month = int(day_of_month_match.group(1))
        button = event_element.locator('button')
        if button.count() > 0:
            title_element = button.locator('.lndlxo9')
            time_element = button.locator('._1r1c5vla')
            if title_element.count() > 0:
                title = title_element.inner_text()
            else:
                title = button.inner_text()
            if time_element.count() > 0:
                time = time_element.inner_text()
            else:
                time = None
            event = {
                'date': f"{month_year}-{str(day_of_month).zfill(2)}",
                'time': time,
                'title': title.strip()
            }
            events.append(event)
    return events

def main():
    with sync_playwright() as p:
        # 修正: GitHub Actionsで実行するためにheadless=Trueに変更
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        # 既存のログイン処理は変更なし
        page.goto(CALENDAR_URL, wait_until="networkidle")
        page.fill('input[type="email"]', TIMETREE_EMAIL)
        page.fill('input[type="password"]', TIMETREE_PASSWORD)
        page.click('button[type="submit"]')
        page.wait_for_timeout(5000)
        page.wait_for_selector('[data-test-id="calendar-main"]')

        # 既存のスクレイピング呼び出しは変更なし
        events = get_events_with_playwright_logic(page)

        print("--- Scraped Events ---")
        print(json.dumps(events, indent=2, ensure_ascii=False))

        # --- ここから追加したロジック ---
        if GAS_WEBAPP_URL:
            print("\n--- Sending data to Google Apps Script ---")
            try:
                headers = {'Content-Type': 'application/json'}
                response = requests.post(GAS_WEBAPP_URL, data=json.dumps(events), headers=headers)
                response.raise_for_status()  # ステータスコードが200番台でなければ例外を発生
                print(f"Successfully sent data. Status: {response.status_code}")
                print(f"Response from GAS: {response.text}")
            except requests.exceptions.RequestException as e:
                print(f"Error sending data to GAS: {e}")
        else:
            print("\nGAS_WEBAPP_URL is not set. Skipping sending data to GAS.")
        # --- ここまで追加したロジック ---

        browser.close()

if __name__ == "__main__":
    main()