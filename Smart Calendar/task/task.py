
from datetime import datetime, date, time


class Data:
    def __init__(self, notes=None,command=None):
        self.messages = [] if notes is None else notes
        self.command = command

class Message:
    def __init__(self, note_type, date_time_obj, note):
        self.note_type = note_type
        self.date_time_obj = date_time_obj
        self.note = note

def sort_key(message):
    value = message.date_time_obj
    if isinstance(value, datetime):
        return value
    return datetime.combine(value, time.min)

def generate_reminder_notes(message):
    days, hours, minutes, secs = calc_note_notification(message.date_time_obj)
    return f"Note: \"{message.note}\". Remains: {days} day(s), {hours} hour(s), {minutes} minute(s)"

def generate_reminder_birthday(message):
    bday = message.date_time_obj
    age_turning, days = calc_birthday_age_and_days(bday)

    return f'Birthday: "{message.note} (turns {age_turning})" - {days} day(s)'

def process_command(command):
    command_handlers = {
        "add": handle_add,
        "view": handle_view,
        "delete": handle_delete,
        "exit": handle_exit
    }

    handler = command_handlers.get(command)
    if handler:
        return handler

def calc_birthday_age_and_days(bday: date):
    today = date.today()

    next_birthday = date(today.year, bday.month, bday.day)
    if next_birthday < today:
        next_birthday = date(today.year + 1, bday.month, bday.day)

    days_remaining = (next_birthday - today).days
    age_turning = next_birthday.year - bday.year

    return age_turning, days_remaining


def calc_note_notification(date_time_obj):
    now = datetime.now()
    delta = date_time_obj - now

    total_seconds = max(0, round(delta.total_seconds() + 59))

    days, remainder = divmod(total_seconds, 86400)
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60)

    return days, hours, minutes, seconds


def is_valid_date(date_time_obj):
    year = date_time_obj.year
    month = date_time_obj.month
    day = date_time_obj.day

    is_leap = False

    if year % 4 == 0 and year % 100 != 0:
        is_leap = True
    elif year % 400 == 0:
        is_leap = True

    cal_dic = {1: [1,31], 2: [1, 29 if is_leap else 28], 3: [1,31], 4: [1,30], 5: [1,31], 6: [1,30], 7: [1,31], 8: [1,31], 9: [1,30], 10: [1,31], 11: [1,30], 12: [1,31]}

    if month <= 0 and month > len(cal_dic):
        return False
    elif day not in range(cal_dic[month][0], cal_dic[month][1] + 1):
        return False
    else:
        return True


def validate_date_time(user_input, time_format):
    try:
        date_time_obj = datetime.strptime(user_input, time_format)
        if is_valid_date(date_time_obj):
            return date_time_obj
        else:
            return None
    except ValueError:
        return None

def handle_note_type():
    while True:
        note_type = input("Specify type (note, birthday): ")
        if note_type not in ["note", "birthday"]:
            print("Incorrect type")
            continue
        break
    return note_type

def handle_msg_count(note_type):
    while True:
        if note_type == "note":
            msg_count = input("How many notes would you like to add: ")
        elif note_type == "birthday":
            msg_count = input("How many dates of birth: ")

        if msg_count.isdigit() and int(msg_count) > 0:
            msg_count = int(msg_count)
            break
        else:
            print("Incorrect number")
    return msg_count

def handle_date_time(index, note_type):
    while True:
        if note_type == "note":
            date_time = input(f"{index + 1}. Enter datetime in \"YYYY-MM-DD HH:MM\" format: ")
            date_time_obj = validate_date_time(date_time, "%Y-%m-%d %H:%M")
        elif note_type == "birthday":
            date_time = input(f"{index + 1}. Enter datetime in \"YYYY-MM-DD\" format: ")
            date_time_obj = validate_date_time(date_time, "%Y-%m-%d")

        if date_time_obj:
            break
        else:
            print("Incorrect date or time values")
    return date_time_obj

def handle_add(data):
    note_type = handle_note_type()
    msg_count = handle_msg_count(note_type)


    for i in range(msg_count):
        if note_type == "note":
            date_time_obj = handle_date_time(i, note_type)
            note = input("Enter text: ")
            note_msg = Message(note_type, date_time_obj, note)
            data.messages.append(note_msg)
        elif note_type == "birthday":
            date_time_obj = handle_date_time(i, note_type)
            name = input("Enter name: ")
            bday_msg = Message(note_type, date_time_obj, name)
            data.messages.append(bday_msg)

    for message in data.messages:
        if note_type == "note" and message.note_type == "note":
            note_msg = generate_reminder_notes(message)
            print(note_msg)
        elif note_type == "birthday" and message.note_type == "birthday":
            bday_msg = generate_reminder_birthday(message)
            print(bday_msg)
    return start


def handle_view_all(data, note_type=None, sort=False, date_obj=None, text=None):
    formatters = {
        "birthday": generate_reminder_birthday,
        "note": generate_reminder_notes,
    }

    messages = data.messages

    if text:
        messages = [m for m in messages if text.lower() in m.note.lower()]

    if date_obj:
        messages = [m for m in messages if m.date_time_obj == date_obj]

    if sort:
        messages = sorted(messages, key=sort_key)

    if note_type:
        messages = [m for m in messages if m.note_type == note_type]

    for message in messages:
        formatter = formatters.get(message.note_type)
        if formatter:
            print(formatter(message))
def handle_view_date(data):
    while True:
        date = input("Enter date in \"YYYY-MM-DD\" format: ")
        date_obj = validate_date_time(date, "%Y-%m-%d").date()
        if date_obj:
            handle_view_all(data, sort=True, date_obj=date_obj)
            break
        else:
            print("Incorrect date")
            continue

def handle_view_text(data):
    while True:
        text = input("Enter text: ").strip()
        if text:
            handle_view_all(data, sort=True, text=text)
            break
        else:
            print("No text given")
            continue

def handle_view(data):
    while True:
        filter = input("Specify filter (all, date, text, birthdays, notes):")
        if filter not in ["all", "date", "text", "birthdays", "notes"]:
            print("Incorrect type")
            continue
        elif filter == "all":
            handle_view_all(data, sort=True)
        elif filter == "date":
            handle_view_date(data)
        elif filter == "text":
            handle_view_text(data)
        elif filter == "birthdays":
            handle_view_all(data, "birthday", sort=True)
        elif filter == "notes":
            handle_view_all(data, "note", sort=True)
        break
    return start

def handle_delete(data):
    print("Not implemented yet")
    return None

def handle_exit(data):
    print("Goodbye!")
    return None

def start(data):
    print("Current date and time:")
    now = datetime.now()
    print(now.strftime("%Y-%m-%d %H:%M"))


    while True:
        command = input("Enter the command (add, view, delete, exit):")

        if command not in ["add", "view", "delete", "exit"]:
            print("Incorrect command")
            continue
        break

    data.command = command

    return process_command(command)


def main():
    data = Data()

    handler = start(data)
    while handler:
        handler = handler(data)

if __name__ == "__main__":
    main()