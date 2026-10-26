from google_calendar import get_calendar_service, sync_lessons
from wat_scraper import download_plan_html, parse_lessons


PLAN_URL = "https://planzajec.wcy.wat.edu.pl/pl/rozklad?grupa_id=WCY24IJ2S1"


def main() -> None:
    html = download_plan_html(PLAN_URL)
    lessons = parse_lessons(html)
    print("Lessons found:", len(lessons))

    service = get_calendar_service()
    sync_lessons(service, lessons)


if __name__ == "__main__":
    main()
