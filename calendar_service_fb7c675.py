import requests
from icalendar import Calendar
import recurring_ical_events
from datetime import datetime, time, timedelta
import os

# Period timings as derived from Claire's calendar
PERIOD_TIMINGS = {
    1: (time(8, 40), time(9, 20)),
    2: (time(9, 20), time(10, 0)),
    3: (time(10, 0), time(10, 40)),
    4: (time(11, 0), time(11, 40)),
    5: (time(11, 40), time(12, 20)),
    6: (time(13, 10), time(13, 50)),
    7: (time(13, 50), time(14, 30)),
    8: (time(14, 30), time(15, 10)),
}

class CalendarService:
    @staticmethod
    def get_calendar_data(url_or_path):
        """Fetches ICS data from a URL or local path."""
        if url_or_path.startswith(('http://', 'https://')):
            try:
                response = requests.get(url_or_path, timeout=10)
                response.raise_for_status()
                return response.content
            except Exception as e:
                print(f"Error fetching calendar from URL: {e}")
                return None
        elif os.path.exists(url_or_path):
            try:
                with open(url_or_path, 'rb') as f:
                    return f.read()
            except Exception as e:
                print(f"Error reading local calendar file: {e}")
                return None
        return None

    @staticmethod
    def get_busy_periods(calendar_url, target_date):
        """
        Parses the calendar and returns a dictionary {period_num: summary}
        where the staff member is busy on the target_date.
        """
        data = CalendarService.get_calendar_data(calendar_url)
        if not data:
            return {}

        try:
            cal = Calendar.from_ical(data)
            # Handle recurring events for the specific day
            events = recurring_ical_events.of(cal).at(target_date)
            
            busy_map = {}
            
            for event in events:
                # X-MICROSOFT-CDO-BUSYSTATUS can be BUSY, TENTATIVE, FREE, OOF
                busy_status = str(event.get('X-MICROSOFT-CDO-BUSYSTATUS', 'BUSY')).upper()
                if busy_status == 'FREE':
                    continue

                summary = str(event.get('SUMMARY', 'Busy'))
                start = event.get('dtstart').dt
                end = event.get('dtend').dt

                # If it's a date object (all day event), treat as busy for all periods
                if not isinstance(start, datetime):
                    for p in PERIOD_TIMINGS.keys():
                        if p not in busy_map:
                            busy_map[p] = []
                        busy_map[p].append(summary)
                    continue

                # Ensure we are working with the time part
                event_start_time = start.time()
                event_end_time = end.time()

                for period, (p_start, p_end) in PERIOD_TIMINGS.items():
                    # Check for overlap: event starts before period ends AND event ends after period starts
                    if event_start_time < p_end and event_end_time > p_start:
                        if period not in busy_map:
                            busy_map[period] = []
                        busy_map[period].append(summary)
            
            # Combine multiple summaries for the same period
            result = {p: " & ".join(summaries) for p, summaries in busy_map.items()}
            return result
        except Exception as e:
            print(f"Error processing calendar: {e}")
            return {}

if __name__ == "__main__":
    # Test with local file
    service = CalendarService()
    test_date = datetime(2026, 1, 29).date()
    busy = service.get_busy_periods('reachcalendar.ics', test_date)
    print(f"Busy periods on {test_date}: {busy}")
