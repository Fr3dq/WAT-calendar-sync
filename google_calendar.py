from datetime import datetime
from pathlib import Path

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


SCOPES = ["https://www.googleapis.com/auth/calendar"]
CALENDAR_ID = "primary"
TIME_ZONE = "Europe/Warsaw"
SOURCE = "wat-calendar-sync"
CREDENTIALS_FILE = Path(__file__).parent / "credentials.json"
TOKEN_FILE = Path(__file__).parent / "token.json"


def get_calendar_service() -> Resource:
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    if credentials and credentials.expired and credentials.refresh_token:
        try:
            credentials.refresh(Request())
        except RefreshError:
            credentials = None

    if not credentials or not credentials.valid:
        flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
        credentials = flow.run_local_server(port=0)

    TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")
    return build("calendar", "v3", credentials=credentials)


def build_event(lesson: dict) -> dict:
    start = lesson["start"].isoformat()
    end = lesson["end"].isoformat()
    key = f"{start} {end} {lesson['summary']} {lesson['room']} {lesson['teacher_code']}"

    return {
        "summary": lesson["summary"],
        "location": lesson["room"],
        "description": f"Teacher code: {lesson['teacher_code']}",
        "start": {"dateTime": start, "timeZone": TIME_ZONE},
        "end": {"dateTime": end, "timeZone": TIME_ZONE},
        "extendedProperties": {"private": {"source": SOURCE, "key": key}},
    }


def get_key(event: dict) -> str:
    return event["extendedProperties"]["private"]["key"]


def sync_lessons(service: Resource, lessons: list[dict]) -> None:
    now = datetime.now()

    old_events = service.events().list(
        calendarId=CALENDAR_ID,
        privateExtendedProperty=f"source={SOURCE}",
        timeMin=now.astimezone().isoformat(),
        maxResults=2500,
    ).execute().get("items", [])

    new_events = [build_event(lesson) for lesson in lessons if lesson["end"] > now]

    old_keys = {get_key(event) for event in old_events}
    new_keys = {get_key(event) for event in new_events}

    events_to_delete = [event for event in old_events if get_key(event) not in new_keys]
    events_to_create = [event for event in new_events if get_key(event) not in old_keys]

    for event in events_to_delete:
        service.events().delete(calendarId=CALENDAR_ID, eventId=event["id"]).execute()

    for event in events_to_create:
        service.events().insert(calendarId=CALENDAR_ID, body=event).execute()

    print("Deleted events:", len(events_to_delete))
    print("Created events:", len(events_to_create))
