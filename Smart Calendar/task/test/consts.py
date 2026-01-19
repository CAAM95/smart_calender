from datetime import datetime, timedelta

STAGE = 3

DATE_TIME_FORMAT = "%Y-%m-%d %H:%M"
DATE_TIME_FORMAT_SHOW = "\"YYYY-MM-DD HH:MM\""
DATE_FORMAT = "%Y-%m-%d"
DATE_FORMAT_SHOW = "\"YYYY-MM-DD\""

NOTE_PATTERN = r'note: "(.*?)"[^\d]+(-?\d+)[^\d]+(-?\d+)[^\d]+(-?\d+)'
BIRTHDAY_PATTERN = r'birthday: "(.*?) \(turns (-?\d+)\)"[^\d]+(-?\d+)'
ANY_TEXT_PATTERN = r'(birthday: "(.*?) \(turns -?\d+\)"[^\d]+-?\d+)|(note: "(.*?)"[^\d]+-?\d+[^\d]+-?\d+[^\d]+-?\d+)'

YEARDATES = [(datetime.now() + timedelta(days=i)).strftime(DATE_FORMAT) for i in range(365)]

LIST_NOTES = [
    "Visit a doctor",
    "Buy groceries",
    "Call mom",
    "Finish the report",
    "Exercise for an hour",
    "Pay bills",
    "Plan a weekend getaway",
    "Read a book",
    "Learn a new recipe",
    "Clean the house",
    "Attend a friend's party",
    "Write in your journal",
    "Organize your closet",
    "Watch a documentary",
    "Take a walk in the park",
    "Schedule a dentist appointment",
    "Start a new hobby",
    "Send a thank-you letter",
    "Practice meditation",
    "Visit a museum",
    "Visit the library",
    "Go for a bike ride",
    "Call a friend you haven't spoken to in a while",
    "Set up a budget for the month",
    "Volunteer for a local charity",
    "Try a new restaurant in town",
    "Take a yoga class",
    "Create a bucket list",
    "Visit a farmer's market",
    "Research a topic of interest",
    "Plan a surprise for someone special",
    "Explore a nearby hiking trail",
    "Visit a historical landmark",
    "Take a day trip to a neighboring city",
    "Start a journal of gratitude",
    "Join a book club",
    "Practice a musical instrument",
    "Try a new workout routine",
    "Learn a new language",
    "Visit an art gallery",
    "Plant a garden",
    "Cook a three-course meal",
    "Go stargazing",
    "Write a poem",
    "Take a photography walk",
    "Try a new type of tea or coffee",
    "Create a vision board",
    "Explore a new genre of music",
    "Take a self-care day"
]

LIST_NAMES = [
    "Aiden Smith",
    "Aria Johnson",
    "Aubrey Brown",
    "Ava Davis",
    "Benjamin Wilson",
    "Chloe Anderson",
    "Christopher Hall",
    "Daniel Miller",
    "David Lewis",
    "Eleanor Lee",
    "Ella Robinson",
    "Eli Turner",
    "Elizabeth Turner",
    "Emma Lee",
    "Ethan Parker",
    "Evelyn Baker",
    "Grace King",
    "Harper Clark",
    "Henry Martin",
    "Isabella Taylor",
    "Jackson Harris",
    "James Wilson",
    "Leo White",
    "Liam Davis",
    "Lily Baker",
    "Lucas Anderson",
    "Madeline Turner",
    "Madison Harris",
    "Matthew Turner",
    "Mia Brown",
    "Michael Johnson",
    "Natalie Clark",
    "Noah Turner",
    "Oliver Wright",
    "Olivia Baker",
    "Samuel Moore",
    "Sarah Johnson",
    "Scarlett Martin",
    "Sebastian Baker",
    "Sophia Turner",
    "Sophie Lewis",
    "Samantha Turner",
    "Thomas King",
    "Victoria White",
    "William Martin",
    "Zoe Davis"
]

wrong_cases = (  # Stage 4
                      [[f'{command}', 'Incorrect command',
                        'incorrect command (everything besides "add", "view", "delete" or "exit")']
                       for command in ['command', 'smile', 'addadd']] +
                      [[f'add\n{tp}', 'Incorrect type', 'incorrect type (everything besides "note" or "birthday")']
                       for tp in ['event', 'not', 'birth']] +
                      [[f'add\n{tp}\n{n}', 'Incorrect number',
                        'a number of notifications that is equal to 0 or not numeric']
                       for tp in ['note', 'birthday'] for n in ['eight', 'two', '10e2'] + list(range(0, -10, -1))] +

                      [[f'add\nnote\n1\n{n}', 'Incorrect format',
                        f'the datetime for a note that can\'t be parsed by {DATE_TIME_FORMAT_SHOW} format']
                       for n in
                       ['tomorrow at 5', '2025-12-0418:36', '2025:12:04 18-36', '2025+12+04 18:36', '2025-12-04']] +
                      [[f'add\nbirthday\n1\n{n}', 'Incorrect format',
                        f'the date for a birthday that can\'t be parsed by {DATE_FORMAT_SHOW} format']
                       for n in
                       ['tomorrow', 'Feb 15', '1011', '20251204', '12.04.2025', '2025+12+04', '2025-12-04 18:36']] +

                      [[f'add\n{tp}\n1\n{datetime.now().year + 1}-{n}-10{" 12:00" if tp == "note" else ""}',
                        'Incorrect date or time values',
                        f'{"date" if tp == "birthday" else "datetime"} for a {tp} that contains incorrect number of months']
                       for tp in ['note', 'birthday'] for n in range(13, 20)] +
                      [[f'add\n{tp}\n1\n{datetime.now().year + 1}-10-{n}{" 12:00" if tp == "note" else ""}',
                        'Incorrect date or time values',
                        f'{"date" if tp == "birthday" else "datetime"} for a {tp} that contains incorrect number of days']
                       for tp in ['note', 'birthday'] for n in range(32, 40)] +

                      [[f'add\nnote\n1\n{datetime.now().year + 1}-{datetime.now().month}-{datetime.now().day} {n}:30',
                        'Incorrect date or time values',
                        f'the datetime for a note that contains incorrect number of hours'] for n in range(24, 40)] +
                      [[f'add\nnote\n1\n{datetime.now().year + 1}-{datetime.now().month}-{datetime.now().day} 12:{n}',
                        'Incorrect date or time values',
                        f'the datetime for a note that contains incorrect number of minutes'] for n in range(60, 70)]
              ) + (
                  (  # Stage 5
                          [[f'view\n{filt}', 'Incorrect filter',
                            'incorrect filter (everything besides "all", "date", "text", "notes" or "birthdays")']
                           for filt in ['data', 'up', 'down']] +
                          [[f'view\ndate\n{n}', 'Incorrect format',
                            f'the date for a "date" filter that can\'t be parsed by {DATE_FORMAT_SHOW} format']
                           for n in
                           ['tomorrow', 'Feb 15', '1011', '20251204', '12.04.2025', '2025+12+04',
                            '2025-12-04 18:36']] +
                          [[f'view\ndate\n{datetime.now().year + 1}-{n}-10', 'Incorrect date or time values',
                            f'date for a "date" filter that contains incorrect number of months']
                           for n in range(13, 20)] +
                          [[f'view\ndate\n{datetime.now().year + 1}-10-{n}', 'Incorrect date or time values',
                            f'date for a "date" filter that contains incorrect number of days']
                           for n in range(32, 40)]
                  ) if STAGE >= 5 else []
              ) + (
                  (  # Stage 6
                      [[f'view\nsorted\n{way}', 'Incorrect way',
                        'incorrect way (everything besides "ascending", "descending")']
                       for way in ['up', 'down', '+', '-']]
                  ) if STAGE >= 6 else [])
