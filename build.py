import re
import requests
from datetime import datetime
from bs4 import BeautifulSoup
from ics import Calendar, Event

BIGCAL_URL = 'https://registrar.osu.edu/staff/bigcal.asp'

def parse_date(date_str: str, year: int) -> list:
  """Convert a varied-formatted human-written date string to something machine translatable.

  Args:
    date (str): Date in the form `Mar 14-18 (M-F)`, `TBA`, `March 15 (W)`, `Apr 26-May 2 (W-T)`
    year (str): Year, e.g. `2023`

  Returns:
    Pair of `datetime` values as a list, or an empty list for an unparsable date
  """
  months = {'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
            'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12}
  try:
    month_day = re.findall(r'\w+\s+\d+', date_str.lower())
    start_month = months[month_day[0][:3]]
    start_day = int(month_day[0].split(' ')[1])
    if len(month_day) == 2:
      end_month = months[month_day[1][:3]]
      end_day = int(month_day[1].split(' ')[1])
    else:
      end_month = start_month
      day_range = re.findall(r'\d+\s*-\s*\d+', date_str)
      if day_range:
        start_day, end_day = map(int, day_range[0].split('-'))
      else:
        end_day = start_day

    start_date = datetime(year, start_month, start_day)
    end_date = datetime(year, end_month, end_day)

    return [start_date, end_date]
  except ValueError as e:
    # Error parsing Feb 28-29 (M-T) 2027: day is out of range for month
    # In some cases, the dates may be typo'd, such as above. We just ignore
    # these and hope they fix their issue at some point on a re-scan.
    print('Error parsing {} {}: {}'.format(date_str, year, e))
    return []
  except:
    return []

def normalize(str: str) -> str:
  """Normalize poorly formatted strings from DOM parsing"""
  return ' '.join(str.split()).strip()

def is_offices_closed(event: str) -> bool:
  """Check if the event description specifies office closure."""
  return event.lower().find('offices clos') != -1

def scrape_table():
  page = requests.get(BIGCAL_URL)
  soup = BeautifulSoup(page.content, 'html.parser')
  tables = soup.find_all('table')

  transformed = []

  # Note this table's DOM isn't built to be accessible so
  # the way I scrape this is a bit awkward due to the lack
  # of proper headings. It's just styled to look like it has
  # subsections and headings.
  for table in tables:
    try:
      rows = table.find_all('tr')
      for row in rows:
        transformed.append([
          normalize(x.get_text()) for x in row.find_all('td')
        ])

      # Table we're interested in has an ACADEMIC YEAR as the first td value
      if transformed[0][0].lower() == 'academic year':
        return transformed
    except:
      pass

  raise RuntimeError('Table not found')

def parse_events(years, row):
  """
  Args:
    years (list): In the form `['2021-2022', '2022-2023', ...]`
    row (list): In the form `['initial fee due date', 'aug 17 (t)', 'aug 16 (t)', ...]`

  Returns:
    Generator of `{ summary, dtstart, dtend }` for valid events
  """
  event = row.pop(0)

  for i in range(len(years)):
    year = int(years[i][0:4])
    dates = parse_date(row[i], year)
    if len(dates) != 2:
      print('No valid date range for event: ' + event, row[i])
      continue

    yield {
      'summary': event,
      'dtstart': dates[0],
      'dtend': dates[1]
    }


def generate_ical():
  """
  Construct two .ics files, one for the full academic calendar and one
    for just events that staff would care about (offices closed)
  """
  transformed = scrape_table()

  # row 0: ['academic year', '2021-2022', '2022-2023', ...]
  # row 1: ['autumn semester', 'au21', 'au22', 'au23', 'au24', ...]
  # row 2 (full colspan): ['this calendar was last updated...']
  # row 3: ['initial fee due date', 'aug 17 (t)', 'aug 16 (t)', ...]

  years = transformed.pop(0)
  columns = len(years)
  years.pop(0)

  semester_headings = [
    'spring semester',
    'autumn semester',
    'summer semester',
    'spring term',
    'autumn term',
    'summer term'
  ]

  academic = Calendar()
  staff = Calendar()

  for row in transformed:
    # Skip headings and anything misaligned (e.g. colspan labels).
    if row[0].lower() in semester_headings or len(row) != columns:
      continue

    for event in parse_events(years, row):
      e = Event()
      e.name = event['summary']
      e.begin = event['dtstart']
      e.end = event['dtend']

      e.make_all_day()
      academic.events.add(e)

      if is_offices_closed(e.name):
        staff.events.add(e)

  with open('staff.ics', 'w') as f:
    f.write(staff.serialize())

  with open('academic.ics', 'w') as f:
    f.write(academic.serialize())

if __name__ == '__main__':
  generate_ical()
