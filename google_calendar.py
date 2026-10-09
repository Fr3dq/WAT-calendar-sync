from datetime import datetime
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import Resource, build


SCOPES = ["https://www.googleapis.com/auth/calendar"]
TIME_ZONE = "Europe/Warsaw"
CREDENTIALS_FILE = Path("credentials.json")
TOKEN_FILE = Path("token.json")


def build_google_event(lesson: dict[str, str]) -> dict:
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


def get_google_calendar_service() -> Resource:
    credentials = None

    if TOKEN_FILE.exists():
        credentials = Credentials.from_authorized_user_file(
            str(TOKEN_FILE),
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
                str(CREDENTIALS_FILE),
                SCOPES,
            )
            credentials = flow.run_local_server(port=0)

        TOKEN_FILE.write_text(credentials.to_json(), encoding="utf-8")

    return build("calendar", "v3", credentials=credentials)
