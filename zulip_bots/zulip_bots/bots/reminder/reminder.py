import threading
import re
from typing import Any, Dict

# The "advanced" regex has options for time and whether reminder is public or
# private. If the "advanced" regex doesn't match, the whole message sent to
# Reminder Bot is sent back after a delay.
REMINDER_ADVANCED_REGEX = re.compile(
    '"(?P<reminder>.+)"'
    '( in (?P<time>\d+) (?P<unit>(s|sec|secs|second|seconds|min|mins|minute|minutes)))?'
    '(?P<public> public)?'
    '$'
)

class ReminderHandler(object):
    def usage(self) -> str:
        return '''
        Reminder Bot can remind users of whatever they want. No setup is
        necessary. See `doc.md` for the very-simple usage instructions.
        '''

    def handle_message(self, message: Dict[str, str], bot_handler: Any) -> None:
        content = message['content']
        sender = message['sender_email']

        reminder_advanced_match = REMINDER_ADVANCED_REGEX.match(content)

        if reminder_advanced_match:
            # The default time is 5 minutes.
            unconverted_time = int(reminder_advanced_match.group('time') or 5)
            is_minutes = (
                (reminder_advanced_match.group('unit') or 'minutes')
                in ["min", "mins", "minute", "minutes"]
            )
            time = unconverted_time * 60 if is_minutes else unconverted_time

            # If it's "public" the reminder will be sent in the same stream as
            # the user who messaged Reminder Bot. If it's "private" it will
            # be sent in a private message to the user.
            is_public = bool(reminder_advanced_match.group('public'))

            reminder = reminder_advanced_match.group('reminder')

            def remind():
                if is_public:
                    bot_handler.send_reply(message, reminder)
                else:
                    bot_handler.send_message(dict(
                        type='private',
                        to=sender,
                        content=reminder
                    ))

            threading.Timer(time, remind).start()
        else:
            # If the "advanced" mode doesn't match, just send back the whole
            # message that was sent to Reminder Bot.
            def remind():
                bot_handler.send_message(dict(
                    type='private',
                    to=sender,
                    content=content
                ))

            # The default time is 5 minutes.
            threading.Timer(5 * 60, remind).start()

handler_class = ReminderHandler
