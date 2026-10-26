from datetime import datetime

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def download_plan_html(url: str) -> str:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False)
        page = browser.new_page()
        page.goto(url)
        page.wait_for_selector(".lesson", state="attached")
        html = page.content()
        browser.close()

    return html


def parse_block_times(soup: BeautifulSoup) -> dict[str, tuple[str, str]]:
    block_times = {}

    for block in soup.select(".block_nr"):
        start = block.select_one(".hr1")
        end = block.select_one(".hr2")
        if start is None or end is None:
            continue

        times = (start.get_text(strip=True), end.get_text(strip=True))
        for class_name in block["class"]:
            if class_name.startswith("block") and class_name != "block_nr":
                block_times[class_name] = times

    return block_times


def parse_lessons(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    block_times = parse_block_times(soup)
    lessons = []

    for lesson in soup.select(".lesson"):
        date_element = lesson.select_one(".date")
        block_element = lesson.select_one(".block_id")
        name_element = lesson.select_one(".name")

        if date_element is None or block_element is None or name_element is None:
            print("Skipping incomplete lesson")
            continue

        date = date_element.get_text(strip=True)
        block_id = block_element.get_text(strip=True)

        if block_id not in block_times:
            print("Skipping lesson with unknown block:", block_id)
            continue

        start, end = block_times[block_id]
        lines = name_element.get_text("\n", strip=True).splitlines()
        short_name, class_type, room, teacher_code = (lines + ["", "", "", ""])[:4]

        lessons.append(
            {
                "summary": f"{short_name} {class_type}".strip(),
                "room": room,
                "teacher_code": teacher_code,
                "start": datetime.strptime(f"{date} {start}", "%Y_%m_%d %H:%M"),
                "end": datetime.strptime(f"{date} {end}", "%Y_%m_%d %H:%M"),
            }
        )

    if not lessons:
        raise RuntimeError("No lessons found in the WAT plan")

    return lessons
