from icalendar import Calendar
import recurring_ical_events

def analyze_ics(file_path):
    with open(file_path, 'rb') as f:
        gcal = Calendar.from_ical(f.read())
        
    times = set()
    for component in gcal.walk():
        if component.name == "VEVENT":
            start = component.get('dtstart').dt
            end = component.get('dtend').dt
            summary = component.get('summary')
            # Extract time part if it's a datetime
            if hasattr(start, 'time'):
                times.add((start.strftime('%H:%M'), end.strftime('%H:%M'), summary))
    
    for s, e, summ in sorted(list(times)):
        print(f"{s} - {e}: {summ}")

if __name__ == "__main__":
    analyze_ics('reachcalendar.ics')
