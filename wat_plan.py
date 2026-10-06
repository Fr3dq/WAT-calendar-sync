from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

url = "https://planzajec.wcy.wat.edu.pl/pl/rozklad?grupa_id=WCY24IJ2S1"

with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=False)
    page = browser.new_page()

    response = page.goto(url, wait_until="domcontentloaded")

    if response is not None:
        print("HTTP status:", response.status)

    page.wait_for_timeout(5000)

    print("Final URL:", page.url)
    print("Title:", page.title())

    html = page.content()
    browser.close()

#Parse the HTML string into object that I can work with
soup = BeautifulSoup(html, "html.parser")

if soup is None:
    raise RuntimeError("Failed to parse HTML content")

