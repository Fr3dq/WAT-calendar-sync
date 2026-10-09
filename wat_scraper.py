from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


def download_plan_html(url: str) -> str:
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

    return html


def parse_lessons(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")

    blocks = soup.select(".block_nr")
    if not blocks:
        raise RuntimeError("No time blocks found in the WAT plan")

    block_times: dict[str, dict[str, str]] = {}

    for block in blocks:
        classes = block.get("class", [])
        block_id = next(
            (
                class_name
                for class_name in classes
                if class_name.startswith("block")
                and class_name != "block_nr"
            ),
            None,
        )

        start_element = block.select_one(".hr1")
        end_element = block.select_one(".hr2")

        if block_id is None or start_element is None or end_element is None:
            continue

        block_times[block_id] = {
            "start": start_element.get_text(strip=True),
            "end": end_element.get_text(strip=True),
        }

    lessons: list[dict[str, str]] = []
    lesson_elements = soup.select(".lesson")

    if not lesson_elements:
        raise RuntimeError("No lessons found in the WAT plan")

    for lesson in lesson_elements:
        date_element = lesson.select_one(".date")
        block_id_element = lesson.select_one(".block_id")
        name_element = lesson.select_one(".name")

        if (
            date_element is None
            or block_id_element is None
            or name_element is None
        ):
            print("Skipping incomplete lesson")
            continue

        date = date_element.get_text(strip=True)
        block_id = block_id_element.get_text(strip=True)
        name_lines = name_element.get_text("\n", strip=True).splitlines()

        if block_id not in block_times:
            print(f"Skipping lesson with unknown block: {block_id}")
            continue

        lessons.append(
            {
                "date": date,
                "block_id": block_id,
                "start": block_times[block_id]["start"],
                "end": block_times[block_id]["end"],
                "short_name": name_lines[0] if len(name_lines) > 0 else "",
                "class_type": name_lines[1] if len(name_lines) > 1 else "",
                "room": name_lines[2] if len(name_lines) > 2 else "",
                "teacher_code": (
                    name_lines[3] if len(name_lines) > 3 else ""
                ),
            }
        )

    return lessons
