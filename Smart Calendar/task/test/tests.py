import os
import random
import re
from enum import Enum

from hstest import StageTest, TestedProgram, dynamic_test, CheckResult, \
    WrongAnswer
from datetime import datetime, timedelta
from .consts import *


def run_for_stages(*stage_numbers: int):
    def decorator(function):
        def wrapper(self, *args, **kwargs):
            if STAGE in stage_numbers:
                return function(self, *args, **kwargs)
            else:
                print("Not applicable for this stage, skipped.")
                return CheckResult.correct()

        return wrapper

    return decorator


class Type(Enum):
    NOTE = 'note',
    BIRTHDAY = 'birthday',

    def __str__(self):
        return str(self.value[0])


class Notification:
    def __init__(self, notification_type, text, days, hours, minutes, years=0,
                 user=False):
        self.user = user
        self.text = text
        self.days = days
        self.hours = hours
        self.minutes = minutes
        self.type = notification_type
        self.date = datetime.now() + timedelta(days=days, hours=hours,
                                               minutes=minutes)
        # Birthday calculation
        self.years = years
        if notification_type == Type.BIRTHDAY and not self.user:
            try:
                birth_date = datetime(datetime.now().year, self.date.month,
                                      self.date.day)
                if datetime.now() > birth_date:
                    birth_date = datetime(datetime.now().year + 1,
                                          self.date.month,
                                          self.date.day)
                    self.years = years + 1
                self.days = abs((datetime.now() - birth_date).days)
            except ValueError:
                print(f"ValueError: {self.date}")
    @classmethod
    def from_match(cls, notification_type, m):
        if notification_type == Type.NOTE:
            for i in range(1, 4):
                if not m[i].isdigit() and not (m[i][0] == '-' and m[i][1:].isdigit()):
                    raise WrongAnswer(f"Invalid format number: {m[i]} should be integer.")
            return cls(notification_type, m[0], int(m[1]), int(m[2]),
                       int(m[3]), 0, True)
        else:
            for i in range(1, 3):
                if not m[i].isdigit() and not (m[i][0] == '-' and m[i][1:].isdigit()):
                    raise WrongAnswer(f"Invalid format number: {m[i]} should be integer.")
            return cls(notification_type, m[0], int(m[2]), 0, 0, int(m[1]),
                       True)

    @classmethod
    def random_note(cls, dhm=None, text=None):
        if dhm is not None:
            dt = datetime.now() + timedelta(days=dhm[0], hours=dhm[1],
                                            minutes=dhm[2])
        else:
            values = [random.randint(0, 1000) for _ in range(3)]
            dt = datetime.now() + timedelta(days=values[0], hours=values[1],
                                            minutes=values[2])
        delta = dt - datetime.now()
        return cls(Type.NOTE,
                   random.choice(LIST_NOTES) if text is None else text,
                   delta.days,
                   delta.seconds // 60 // 60, delta.seconds // 60 % 60)

    @classmethod
    def random_birthday(cls, wd=None, text=None):
        if wd is not None:
            values = wd
            dt = datetime.now() + timedelta(weeks=wd[0], days=wd[1])
        else:
            while True:
                values = [random.randint(-5000, -1000) for _ in range(2)]
                dt = datetime.now() + timedelta(weeks=values[0],
                                                days=values[1])
                if not (dt.month == 2 and dt.day > 27):
                    break
        return cls(Type.BIRTHDAY,
                   random.choice(LIST_NAMES) if text is None else text,
                   values[1] + values[0] * 7, 0, 0,
                   datetime.now().year - dt.year)

    def input(self):
        return self.date.strftime(
            DATE_TIME_FORMAT if self.type == Type.NOTE else DATE_FORMAT), self.text

    def is_on_date(self, date):
        return self.date.day == date.day and self.date.month == date.month and (
                self.date.year == date.year or self.type == Type.BIRTHDAY)

    def __eq__(self, other):
        if type(self) != type(other) or self.type != other.type:
            return False
        if self.type == Type.NOTE:
            return (self.text.lower() == other.text.lower() and
                    self.days == other.days and
                    self.hours == other.hours and
                    self.minutes == other.minutes)
        else:
            return (self.text.lower() == other.text.lower() and
                    self.years == other.years and
                    self.days == other.days)

    def __str__(self):
        if self.type == Type.NOTE:
            return f'\"Note: {self.text}. Remains: {self.days} day(s), {self.hours} hour(s), {self.minutes} minute(s)\"'
        else:
            return (f'\"Birthday: {self.text} (turns {self.years}). '
                    f'Remains: {self.days} day(s)\"')


def get_minutes_remaining(notification):
    return notification.days * 24 * 60 + notification.hours * 60 + notification.minutes


def get_lines(output):
    return [line.strip() for line in
            re.split(r"[\r\n]+", output.lower().strip())]


def check_tokens(s, lst):
    return all([token.lower().strip() in s.lower().strip() for token in lst])


def generate_random_dhms_wds_dates():
    custom_dhms = []
    custom_wds = []
    for __ in range(12):
        values = [random.randint(-5000, -1000) for _ in range(2)]
        dt = datetime.now() + timedelta(weeks=values[0], days=values[1])
        if not (dt.month == 2 and dt.day > 27):
            custom_wds.append(values)
            days = (datetime(year=datetime.now().year + 1, month=dt.month,
                             day=dt.day) - datetime.now()).days
            custom_dhms.append(
                [days, random.randint(0, 5), random.randint(0, 20)])

    custom_dates = list(dict.fromkeys(
        [(datetime.now() + timedelta(days=dhm[0], hours=dhm[1],
                                     minutes=dhm[2])).replace(
            year=datetime.now().year + 1) for dhm in custom_dhms] +
        [datetime.now() + timedelta(weeks=wd[0], days=wd[1]) for wd in
         custom_wds]))
    return custom_dhms, custom_wds, custom_dates


class CalendarTest(StageTest):
    def __init__(self, source=''):
        super().__init__()
        self.notes = []
        self.birthdays = []
        self.yeardates = [
            (datetime.now() + timedelta(days=i)).strftime(DATE_FORMAT) for i in
            range(365)]

    def reload(self):
        self.notes = []
        self.birthdays = []
        data_path = 'data.txt'
        feedback = 'An error occurred while tests were attempting to remove file: '
        if data_path in os.listdir('.'):
            try:
                os.remove(data_path)
            except FileNotFoundError:
                raise WrongAnswer(feedback + f"File {data_path} not found")
            except PermissionError:
                raise WrongAnswer(
                    feedback + f"Permission denied to remove file {data_path}")
            except OSError as e:
                raise WrongAnswer(feedback + f"{e}")

    def check_notifications(self, output, action, elements, sorting=None):
        elements_notes = list(
            filter(lambda el: el.type == Type.NOTE, elements))
        elements_birthdays = list(
            filter(lambda el: el.type == Type.BIRTHDAY, elements))
        note_matches = re.findall(NOTE_PATTERN, output)
        birthday_matches = re.findall(BIRTHDAY_PATTERN, output)
        if len(note_matches) != len(elements_notes):
            raise WrongAnswer(
                f"Incorrect number of notes found in your output after {action}. "
                f"Expected: {len(elements_notes)}. Got: {len(note_matches)}")
        if len(birthday_matches) != len(elements_birthdays):
            raise WrongAnswer(
                f"Incorrect number of birthday reminders found in your output after {action}. "
                f"Expected: {len(elements_birthdays)}. Got: {len(birthday_matches)}")

        notes = [Notification.from_match(Type.NOTE, m) for m in note_matches]
        birthdays = [Notification.from_match(Type.BIRTHDAY, m) for m in
                     birthday_matches]

        for expected_note in elements_notes:
            if not any(expected_note == users_note for users_note in notes):
                raise WrongAnswer(
                    f"Expected element {expected_note} not found in your output after {action}.")
        for expected_birthday in elements_birthdays:
            if not any(
                    expected_birthday == users_birthday for users_birthday in
                    birthdays):
                raise WrongAnswer(
                    f"Expected element {expected_birthday} not found in your output after {action}.")

        if sorting is None:
            return
        user_texts_order = [m[3] + m[0] for m in
                            re.findall(ANY_TEXT_PATTERN, output)]
        elements = sorted(elements,
                          key=lambda x: (get_minutes_remaining(x), x.text),
                          reverse=(sorting == 'descending'))
        for i, el in enumerate(elements):
            if el.text.lower() not in user_texts_order[i]:
                raise WrongAnswer(
                    f"Order of elements in the output of your program on {sorting} sorting is incorrect.")

    def check_views(self, pr, action, custom_dates):
        custom_texts = list(
            dict.fromkeys(
                [subs.strip() for no in self.birthdays + self.notes for subs in
                 no.text.split(' ')]))
        for prompt in ([['all'], ['birthdays'], ['notes']] +
                       [['date', date.strftime(DATE_FORMAT)] for date in
                        custom_dates] +
                       [['text', subs.strip()] for subs in custom_texts] +
                       ([['sorted', 'ascending'],
                         ['sorted', 'descending']] if STAGE >= 6 else [])):
            output = self.view_content(pr, prompt).lower().strip()
            # calculate expected
            if prompt[0] == 'all':
                expected = self.notes + self.birthdays
            elif prompt[0] == 'birthdays':
                expected = self.birthdays
            elif prompt[0] == 'notes':
                expected = self.notes
            elif prompt[0] == 'date':
                expected = list(filter(lambda x: x.is_on_date(
                    datetime.strptime(prompt[1], DATE_FORMAT)),
                                       self.notes + self.birthdays))
            elif prompt[0] == 'text':
                expected = list(
                    filter(lambda x: prompt[1].lower() in x.input()[1].lower(),
                           self.notes + self.birthdays))
            elif prompt[0] == 'sorted' and STAGE >= 6:
                expected = self.notes + self.birthdays
            else:
                expected = []
            # for t in expected:
            #     print(t)
            self.check_notifications(output,
                                     f'user viewed list of notifications filtered '
                                     f'by "{" ".join(prompt)}" after {action}',
                                     expected,
                                     sorting=prompt[1] if prompt[
                                                              0] == 'sorted' else None)

    def add_content(self, pr, elements):
        n_type = elements[0].type
        output = pr.execute("add").strip().lower()
        if STAGE > 2:
            if 'type' not in output.lower():
                raise WrongAnswer(
                    f"'Specify type' message not found in your output "
                    f"after 'add' option was selected")
            for tp in ['note', 'birthday']:
                if tp not in output:
                    raise WrongAnswer(
                        f"Possible '{tp}' type not found in your output "
                        f"after 'add' option was selected")
            output = pr.execute(str(n_type))
            if not check_tokens(output, ['how', 'many'] + (
                    ['notes'] if n_type == Type.NOTE else ['date', 'birth'])):
                raise WrongAnswer(
                    f"'How many {'notes' if n_type == Type.NOTE else 'dates of birth'}' message "
                    f"not found in your output after type of added notifications is specified")
            output = pr.execute(str(len(elements)))
        for i, el in enumerate(elements):
            tokens = ['Enter', 'datetime'] if n_type == Type.NOTE else [
                'Enter', 'date']
            if not check_tokens(output, tokens):
                raise WrongAnswer(
                    f"'{' '.join(tokens)}' message not found in your output "
                    f"when adding a {n_type}")
            f = DATE_TIME_FORMAT_SHOW if n_type == Type.NOTE else DATE_FORMAT_SHOW
            if f.lower() not in output.lower():
                raise WrongAnswer(
                    f"Format of expected datetime input not found in your output "
                    f"when adding a {n_type}. Expected: \"{f}\"")
            if len(elements) > 1 and str(i + 1) not in output.lower():
                raise WrongAnswer(
                    f"There should be a number of a {n_type} in your output "
                    f"when adding multiple {n_type}s. Expected: \"{i + 1}\"")
            if not pr.is_waiting_input():
                raise WrongAnswer(
                    f"Program should request the datetime when adding a {n_type}")

            output = pr.execute(el.input()[0]).lower().strip()

            tokens = ['Enter', 'text'] if n_type == Type.NOTE else ['Enter',
                                                                    'name']
            if not check_tokens(output, tokens):
                raise WrongAnswer(
                    f"'{' '.join(tokens)}' message not found in your output "
                    f"after datetime for a {n_type} was provided")
            if not pr.is_waiting_input():
                raise WrongAnswer(
                    f"Program should request the {tokens[1]} for a "
                    f"{n_type} after datetime was provided")

            output = pr.execute(el.input()[1]).lower().strip()
            if n_type == Type.NOTE:
                self.notes.append(el)
            else:
                self.birthdays.append(el)
        return output

    def delete_content(self, pr, elements):
        output = pr.execute("delete").strip().lower()
        lines = get_lines(output)
        feedback = (
                "Your program should print all notifications with indexes in {id}.{notification} format " +
                f"on separate lines when 'delete' option selected. ")
        len_notifies = len(self.notes + self.birthdays)
        if len(lines) != len_notifies + 1:
            raise WrongAnswer(
                feedback + f"Expected {len_notifies + 1} lines ({len_notifies} for notifications and "
                           f"one extra with 'Enter ids' message). Got {len(lines)}")
        for k in range(len(lines) - 1):
            if not lines[k].strip().startswith(str(k + 1)):
                raise WrongAnswer(
                    feedback + f"Line {k + 1} should start with '{k + 1}' index when 'delete' option "
                               f"selected, but was not: {lines[k]}")
        self.check_notifications(output, "'delete' option selected",
                                 self.notes + self.birthdays)
        if not check_tokens(lines[-1], ['enter', 'ids']):
            raise WrongAnswer(
                feedback + f"Last line of 'delete' option output should contain 'Enter ids' message. "
                           f"Got : {lines[-1]}")
        indices = []
        for el in elements:
            for i, line in enumerate(lines):
                if el.text.lower() in line.lower():
                    indices.append(str(i + 1))
                    break
        indices_str = ",".join(indices)
        output = pr.execute(indices_str).strip().lower()
        for note in filter(lambda x: x.type == Type.NOTE, elements):
            self.notes.remove(note)
        for birthday in filter(lambda x: x.type == Type.BIRTHDAY, elements):
            self.birthdays.remove(birthday)
        return output

    def view_content(self, pr, prompt):
        output = pr.execute("view").strip().lower()
        if 'filter' not in output.lower():
            raise WrongAnswer(
                f"'Specify filter' message not found in your output "
                f"after 'view' option was selected")
        for filt in ['all', 'date', 'text', 'birthdays', 'notes'] + (
                ['sorted'] if STAGE >= 6 else []):
            if filt not in output:
                raise WrongAnswer(
                    f"Possible '{filt}' filter not found in your output "
                    f"after 'view' option was selected")
        output = pr.execute(prompt[0]).lower().strip()
        if prompt[0] in ['date', 'text']:
            if not check_tokens(output, ['Enter', prompt[0]] + (
                    [DATE_FORMAT_SHOW] if prompt[0] == 'date' else [])):
                raise WrongAnswer(
                    f"'Enter {prompt[0]}' message not found in your "
                    f"output after '{prompt[0]}' filter is specified")
            output = pr.execute(prompt[1]).lower().strip()
        if prompt[0] == 'sorted' and STAGE >= 6:
            if 'way' not in output.lower():
                raise WrongAnswer(
                    f"'Specify way' message not found in your output "
                    f"after 'sorted' filter is specified")
            for way in ['ascending', 'descending']:
                if way not in output:
                    raise WrongAnswer(
                        f"Possible '{way}' way not found in your output "
                        f"after 'sorted' filter was selected")
            output = pr.execute(prompt[1]).lower().strip()
        return output

    @dynamic_test
    @run_for_stages(1, 2, 3, 4, 5, 6, 7)
    def test_start(self):
        pr = TestedProgram()
        lines = get_lines(pr.start().lower())

        if len(lines) < 3:
            return CheckResult.wrong(
                f"Your program should print 3 non-empty lines. Found: {len(lines)}")
        if not check_tokens(lines[0], ['current', 'date', 'time']):
            return CheckResult.wrong(
                f"'Current date and time' message not found in the first line of initial output.")

        try:
            user_datetime = datetime.strptime(lines[1], DATE_TIME_FORMAT)
        except ValueError:
            return CheckResult.wrong(
                f"Can't parse printed datetime object from the second line. Found: '{lines[1]}'. "
                f"Make sure that it is formatted as follows: {DATE_TIME_FORMAT}")
        if abs((datetime.now() - user_datetime).seconds) > 60:
            return CheckResult.wrong(
                f"Incorrect date and time found in the second line of initial output.")

        if 'command' not in lines[2]:
            return CheckResult.wrong(
                f"'Enter the command' message not found in the third line of initial output.")
        for option in ['add', 'view', 'delete', 'exit']:
            if option not in lines[2]:
                return CheckResult.wrong(
                    f"'{option}' option not found in the third line of initial output.")

        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(2, 3, 4, 5, 6, 7)
    def test_exit(self):
        pr = TestedProgram()
        pr.start()
        if not pr.is_waiting_input():
            return CheckResult.wrong(
                "Your program should request an option when the program just started")
        if not check_tokens(pr.execute('exit').lower(),
                            ['bye']) or not pr.is_finished():
            return CheckResult.wrong(
                "If the user chooses 'exit' option the program should print "
                "goodbye message and finish it's execution")
        return CheckResult.correct()

    @dynamic_test(data=['view', 'delete'])
    @run_for_stages(2, 3, 4)
    def test_not_implemented(self, opt):
        pr = TestedProgram()
        pr.start()
        if not pr.is_waiting_input():
            return CheckResult.wrong(
                "Your program should request an option when the program just started")
        if not check_tokens(pr.execute(opt).lower(),
                            ['not', 'implemented']) or not pr.is_finished():
            return CheckResult.wrong(
                "If the user chooses not yet implemented option the program should print "
                "'Not implemented' message and finish it's execution")
        return CheckResult.correct()

    @dynamic_test(repeat=10)
    @run_for_stages(2, 3, 4, 5, 6, 7)
    def test_add_note(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        random_note = Notification.random_note()
        output = self.add_content(pr, [random_note])
        self.check_notifications(output, 'a new note added', [random_note])
        return CheckResult.correct()

    @dynamic_test(repeat=10)
    @run_for_stages(3, 4, 5, 6, 7)
    def test_add_multiple_notes(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        random_notes = [Notification.random_note() for _ in
                        range(random.randint(2, 10))]
        output = self.add_content(pr, random_notes)
        self.check_notifications(output, 'multiple notes were added',
                                 random_notes)
        return CheckResult.correct()

    @dynamic_test(repeat=10)
    @run_for_stages(3, 4, 5, 6, 7)
    def test_add_birthday(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        random_birthday = Notification.random_birthday()
        output = self.add_content(pr, [random_birthday])
        self.check_notifications(output, 'a new birthday added',
                                 [random_birthday])
        return CheckResult.correct()

    @dynamic_test(repeat=10)
    @run_for_stages(3, 4, 5, 6, 7)
    def test_add_multiple_birthdays(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        random_birthdays = [Notification.random_birthday() for _ in
                            range(random.randint(2, 10))]
        output = self.add_content(pr, random_birthdays)
        self.check_notifications(output, 'multiple birthdays were added',
                                 random_birthdays)
        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(5, 6, 7)
    def test_action_loop(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        for _ in range(10):
            if random.randint(0, 1) == 0:
                output = self.add_content(pr,
                                          [Notification.random_note() for _ in
                                           range(random.randint(1, 3))])
            else:
                output = self.add_content(pr,
                                          [Notification.random_birthday() for _
                                           in range(random.randint(1, 3))])
            if not pr.is_waiting_input() or pr.is_finished():
                return CheckResult.wrong(
                    "The program should continue it's execution until 'exit' command is provided")
            if 'command' not in output:
                return CheckResult.wrong(
                    f"'Enter the command' message not found after any action was performed. "
                    f"Program should return back to start.")
            for option in ['add', 'view', 'delete', 'exit']:
                if option not in output:
                    return CheckResult.wrong(
                        f"'{option}' option not found after any action was performed. "
                        f"Program should return back to start.")
        pr.execute("exit")
        if pr.is_waiting_input() or not pr.is_finished():
            return CheckResult.wrong(
                "The program should finish it's execution when 'exit' command is provided")
        return CheckResult.correct()

    @dynamic_test(data=[
        [['all']], [['birthdays']], [['notes']],
        [['date', datetime.now().strftime(DATE_FORMAT)]],
        [['text', random.choice(LIST_NOTES)]]
    ])
    @run_for_stages(5, 6, 7)
    def test_view_empty(self, prompt):
        self.reload()
        pr = TestedProgram()
        pr.start()
        output = self.view_content(pr, prompt)
        self.check_notifications(output,
                                 f'user viewed empty list of notifications filtered by "{" ".join(prompt)}"',
                                 [])
        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(5, 6, 7)
    def test_add_view(self):
        self.reload()

        pr = TestedProgram()
        pr.start()

        custom_dhms, custom_wds, custom_dates = generate_random_dhms_wds_dates()

        for __ in range(4):
            random_notes = [
                Notification.random_note(random.choice(custom_dhms)) for _ in
                range(20)]
            output = self.add_content(pr, random_notes)
            self.check_notifications(output,
                                     'additional multiple notes were added',
                                     random_notes)
            random_birthdays = [
                Notification.random_birthday(random.choice(custom_wds)) for _
                in range(20)]
            output = self.add_content(pr, random_birthdays)
            self.check_notifications(output,
                                     'additional multiple birthdays were added',
                                     random_birthdays)
            self.check_views(pr, 'additional notifications were added',
                             custom_dates)
        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(6, 7)
    def test_delete_empty(self):
        self.reload()
        pr = TestedProgram()
        pr.start()
        output = self.delete_content(pr, [])
        if not pr.is_waiting_input() or pr.is_finished():
            return CheckResult.wrong(
                "The program should continue it's execution until 'exit' command is provided")
        if 'command' not in output:
            return CheckResult.wrong(
                f"'Enter the command' message not found after any action was performed. "
                f"Program should return back to start.")
        for option in ['add', 'view', 'delete', 'exit']:
            if option not in output:
                return CheckResult.wrong(
                    f"'{option}' option not found after any action was performed. "
                    f"Program should return back to start.")
        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(6, 7)
    def test_delete(self):
        self.reload()

        pr = TestedProgram()
        pr.start()

        custom_dhms, custom_wds, custom_dates = generate_random_dhms_wds_dates()

        notes = [Notification.random_note(dhm=random.choice(custom_dhms),
                                          text=f"note{i}") for i in range(8)]
        birthdays = [Notification.random_birthday(wd=random.choice(custom_wds),
                                                  text=f"birthday{i}") for i in
                     range(8)]
        self.add_content(pr, notes)
        self.add_content(pr, birthdays)
        self.check_views(pr, 'some notifications were added', custom_dates)
        for _ in range(3):
            self.delete_content(pr,
                                random.sample(self.notes + self.birthdays, 3))
            self.check_views(pr, 'some notifications were deleted',
                             custom_dates)

        return CheckResult.correct()

    @dynamic_test
    @run_for_stages(7)
    def test_saving_and_loading(self):
        self.reload()

        custom_dhms, custom_wds, custom_dates = generate_random_dhms_wds_dates()

        def hx(number):
            if 0 <= number <= 9:
                return str(number)
            elif 10 <= number <= 15:
                return chr(ord('A') + number - 10)

        notes = [Notification.random_note(dhm=random.choice(custom_dhms),
                                          text=f"note{hx(i)}") for i in
                 range(16)]
        birthdays = [Notification.random_birthday(wd=random.choice(custom_wds),
                                                  text=f"bday{hx(i)}") for i in
                     range(16)]

        reloaded = ''

        for _ in range(3):

            pr = TestedProgram()
            pr.start()

            notes_added = random.sample(notes, 3)
            birthdays_added = random.sample(birthdays, 3)
            notes = [x for x in notes if x not in notes_added]
            birthdays = [x for x in birthdays if x not in birthdays_added]

            self.add_content(pr, notes_added)
            self.add_content(pr, birthdays_added)
            self.check_views(pr, 'some notifications were added' + reloaded,
                             custom_dates)
            self.delete_content(pr, random.sample(self.notes + self.birthdays,
                                                  random.randint(1, 3)))
            self.check_views(pr, 'some notifications were deleted' + reloaded,
                             custom_dates)

            pr.execute('exit')
            if not pr.is_finished():
                return CheckResult.wrong(
                    "The program should finish it's execution when 'exit' command is provided")
            reloaded = ' (program reloaded)'
            print("Program reloaded!")

        return CheckResult.correct()

    @dynamic_test(data=wrong_cases)
    @run_for_stages(4, 5, 6, 7)
    def test_incorrect_input(self, inp, expected, mistake):
        self.reload()
        pr = TestedProgram()
        pr.start()
        output = pr.execute(inp)
        if not check_tokens(output, expected.split(' ')):
            return CheckResult.wrong(
                f'Your program should handle incorrect inputs properly. '
                f'Expected "{expected}" message when the user inputted {mistake}')
        return CheckResult.correct()

    @dynamic_test(
        data=[[2096, True], [2097, False], [2098, False], [2099, False],
              [2100, False], [2104, True]])
    @run_for_stages(4, 5, 6, 7)
    def test_leap_years(self, year, correct):
        self.reload()
        for tp in ['note', 'birthday']:
            pr = TestedProgram()
            pr.start()
            dt = f'{year}-02-29' + (' 12:00' if tp == 'note' else '')
            output = pr.execute(f'add\n{tp}\n1\n{dt}')
            if correct and check_tokens(output,
                                        'Incorrect date or time values'.split(
                                            ' ')):
                return CheckResult.wrong(
                    f'{year} is a leap year, so "{dt}" should be valid')
            if not correct and not check_tokens(output,
                                                'Incorrect date or time values'.split(
                                                    ' ')):
                return CheckResult.wrong(
                    f'{year} is not a leap year, so "{dt}" should be invalid')
            pr.stop()
        return CheckResult.correct()

    def after_all_tests(self):
        self.reload()


if __name__ == "__main__":
    CalendarTest().run_tests()
