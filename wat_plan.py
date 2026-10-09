from google_calendar import (
    build_google_event,
    get_google_calendar_service,
)
from wat_scraper import download_plan_html, parse_lessons


PLAN_URL = (
    "https://planzajec.wcy.wat.edu.pl/"
    "pl/rozklad?grupa_id=WCY24IJ2S1"
)


def main() -> None:
    html = download_plan_html(PLAN_URL)
    lessons = parse_lessons(html)

    print("Lessons found:", len(lessons))

    google_events = [build_google_event(lesson) for lesson in lessons]

    service = get_google_calendar_service()
    calendar = service.calendars().get(
        calendarId="primary",
    ).execute()

    print("Connected to calendar:", calendar["summary"])

    if not google_events:
        raise RuntimeError("No Google Calendar events were generated")

    created_event = service.events().insert(
        calendarId="primary",
        body=google_events[0],
    ).execute()

    print("Created event:", created_event["htmlLink"])


if __name__ == "__main__":
    main()
