from playwright.sync_api import sync_playwright

url = "https://planzajec.wcy.wat.edu.pl/pl/rozklad?grupa_id=WCY24IJ2S1"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    page.goto(url, wait_until="networkidle")

    print("Title:", page.title())
    print("Status page loaded")
    print(page.locator(".roklad_container").inner_text()[:1000])

    browser.close()