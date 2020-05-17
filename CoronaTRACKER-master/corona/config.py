import re,datetime

LAST_UPDATED_DATE_STR="2020-03-27"
match = re.search('\d{4}-\d{2}-\d{2}', LAST_UPDATED_DATE_STR)
LAST_UPDATED_DATE = datetime.datetime.strptime(match.group(), '%Y-%m-%d').date()
