import threading
import re
import dateutil
import dateutil.parser
import dateutil.tz
import datetime
from typing import Any, Dict

# The "advanced" regex has options for time and whether reminder is public or
# private. If the "advanced" regex doesn't match, the whole message sent to
# Reminder Bot is sent back after a delay.
REMINDER_ADVANCED_REGEX = re.compile(
    '"(?P<reminder>.+)"'
    '(( in (?P<delay>\d+) (?P<unit>(s|sec|secs|second|seconds|min|mins|minute|minutes)))|'
    '( at (?P<time>.+?)))?'
    '(?P<public> public)?'
    '$'
)

HELP_RESPONSE = '''
Reminder Bot can remind you of whatever you want. It has 2 modes: advanced \
and normal.

---

In **normal**, mode you can just send a message to Reminder Bot and have it \
remind you in 5 minutes.

 > @**Reminder Bot** Walk the dog.

…and then 5 minutes later in a private message from Reminder Bot…

 > Walk the dog.

---

In **advanced** mode you can control when to get the reminder and whether it \
should be public or private. You have to put your reminder in quotes.

For example,

 > @**Reminder Bot** "Water the plants." in 20 minutes

or

 > @**Reminder Bot** "Water the plants." in 20 seconds

or even

 > @**Reminder Bot** "Water the plants." at 6:13

…and then in a private message…

 > Water the plants.

You can also do

  > @**Reminder Bot** "Take out the trash." public

…and then, in the current stream for all subscribers to see…

 > Take out the trash.

Or, you can do both at once

 > @**Reminder Bot** "Make the bed." at 8:26 public

…and then, in the current stream 30 minutes later…

 > Make the bed.
'''

class ReminderHandler(object):
    def usage(self) -> str:
        return '''
        Reminder Bot can remind users of whatever they want. No setup is
        necessary. See `doc.md` for the very-simple usage instructions.
        '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        content = message['content']
        sender = message['sender_email']
        sender_name = message['sender_full_name']

        reminder_advanced_match = REMINDER_ADVANCED_REGEX.match(content)

        if content == 'help' or content == '':
            bot_handler.send_reply(message, HELP_RESPONSE)
        elif reminder_advanced_match:
            # The default delay is 5 minutes.
            delay = 5 * 60

            # If they listed a delay using the `in <delay> <unit>` syntax, use
            # it.
            if reminder_advanced_match.group('delay'):
                unconverted_delay = delay
                try:
                    unconverted_delay = int(reminder_advanced_match.group('delay'))
                except ValueError:
                    bot_handler.send_reply(message, 'Sorry, that time doesn\'t make sense.')
                    return

                is_minutes = (
                    (reminder_advanced_match.group('unit'))
                    in ["min", "mins", "minute", "minutes"]
                )
                delay = unconverted_delay * 60 if is_minutes else unconverted_delay
            # If they didn't, see if they listed an exact time.
            elif reminder_advanced_match.group('time'):
                time = datetime.datetime.now() + datetime.timedelta(seconds=delay)
                try:
                    time = dateutil.parser.parse(reminder_advanced_match.group('time'))
                except ValueError:
                    bot_handler.send_reply(message, 'Sorry, that time doesn\'t make sense.')
                    return

                now = datetime.datetime.now()
                difference = (time - now)
                if difference < datetime.timedelta(0):
                    bot_handler.send_reply(message, 'Sorry, the time can\'t be in the past.')
                    return

                delay = difference.total_seconds()

            # If it's "public" the reminder will be sent in the same stream as
            # the user who messaged Reminder Bot. If it's "private" it will
            # be sent in a private message to the user.
            is_public = bool(reminder_advanced_match.group('public'))

            reminder = reminder_advanced_match.group('reminder')

            def remind():
                if is_public:
                    mention = '@**' + sender_name + '** '
                    bot_handler.send_reply(message, mention + reminder)
                else:
                    bot_handler.send_message(dict(
                        type='private',
                        to=sender,
                        content=reminder
                    ))

            threading.Timer(delay, remind).start()
        else:
            # If the "advanced" mode doesn't match, just send back the whole
            # message that was sent to Reminder Bot.
            def remind():
                bot_handler.send_message(dict(
                    type='private',
                    to=sender,
                    content=content
                ))

            # The default delay is 5 minutes.
            threading.Timer(5 * 60, remind).start()

handler_class = ReminderHandler
