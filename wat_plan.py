from datetime import datetime
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright
import os.path

#Google Auth imports
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/calendar"]

url = "https://planzajec.wcy.wat.edu.pl/pl/rozklad?grupa_id=WCY24IJ2S1"
block_times = {}
lessons = []
TIME_ZONE = "Europe/Warsaw"


def build_google_event(lesson):
    start = datetime.strptime(
        f"{lesson['date']} {lesson['start']}",
        "%Y_%m_%d %H:%M",
    )
    end = datetime.strptime(
        f"{lesson['date']} {lesson['end']}",
        "%Y_%m_%d %H:%M",
    )

    summary = f"{lesson['short_name']} {lesson['class_type']}".strip()

    return {
        "summary": summary,
        "location": lesson["room"],
        "description": f"Teacher code: {lesson['teacher_code']}",
        "start": {
            "dateTime": start.isoformat(),
            "timeZone": TIME_ZONE,
        },
        "end": {
            "dateTime": end.isoformat(),
            "timeZone": TIME_ZONE,
        },
    }

def get_google_calendar_service():
    credentials = None

    if os.path.exists("token.json"):
        credentials = Credentials.from_authorized_user_file(
            "token.json",
            SCOPES,
        )

    if credentials is None or not credentials.valid:
        if credentials is not None and credentials.expired:
            if credentials.refresh_token:
                credentials.refresh(Request())
            else:
                credentials = None

        if credentials is None:
            flow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json",
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        with open("token.json", "w", encoding="utf-8") as token_file:
            token_file.write(credentials.to_json())

    return build("calendar", "v3", credentials=credentials)

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

for block in soup.select(".block_nr"):
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

    if (block_id is None or start_element is None or end_element is None):
        continue

    block_times[block_id] = {
        "start": start_element.get_text(strip=True),
        "end": end_element.get_text(strip=True),
    }

for lesson in soup.select(".lesson"):
    date_element = lesson.select_one(".date")
    block_id_element = lesson.select_one(".block_id")
    name_element = lesson.select_one(".name")

    if (
        date_element is None
        or block_id_element is None
        or name_element is None
    ):
        print("Skipping incomplete lesson", date_element, block_id_element)
        continue

    date = date_element.get_text(strip=True)
    block_id = block_id_element.get_text(strip=True)
    name_lines = name_element.get_text("\n", strip=True).splitlines()

    if block_id not in block_times:
        print(f"Skipping lesson with unknown block: {block_id}")
        continue

    lesson_data = {
        "date": date,
        "block_id": block_id,
        "start": block_times[block_id]["start"],
        "end": block_times[block_id]["end"],
        "short_name": name_lines[0] if len(name_lines) > 0 else "",
        "class_type": name_lines[1] if len(name_lines) > 1 else "",
        "room": name_lines[2] if len(name_lines) > 2 else "",
        "teacher_code": name_lines[3] if len(name_lines) > 3 else "",
    }

    lessons.append(lesson_data)

print("Lessons found:", len(lessons))

google_events = [build_google_event(lesson) for lesson in lessons]

service = get_google_calendar_service()

calendar = service.calendars().get(
    calendarId="primary",
).execute()

print("Connected to calendar:", calendar["summary"])