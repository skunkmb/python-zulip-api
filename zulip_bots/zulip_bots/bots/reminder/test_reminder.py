from zulip_bots.test_lib import BotTestCase
from typing import Callable
from mock import patch

class TestReminderBot(BotTestCase):
    bot_name = "reminder"

    # 'Foo Test User' must be used because it's the name used in
    # `make_request_message` in `test_lib`.
    sender_name = 'Foo Test User'
    sender_mention = '@**' + sender_name + '** '

    def _test(self, request: str, response: str):
        with patch('threading.Timer') as timer:
            # This is similar to `verify_reply` in `BotTestCase`, but with a
            # break in the middle for the timer's function call.
            bot, bot_handler = self._get_handlers()
            message = self.make_request_message(request)
            bot_handler.reset_transcript()
            bot.handle_message(message, bot_handler)

            # Call the function specified in for the Timer immediately so that
            # the tests don't take too long.
            if timer.call_args:
                timer.call_args[0][1]()

            # `verify_reply` uses `unique_reply`, but `unique_response`
            # allows for private messages, making it more useful here.
            reply = bot_handler.unique_response()

            self.assertEqual(response, reply['content'])

    def test_normal_mode(self):
        self._test('Walk the dog.', 'Walk the dog.')

    def test_advanced_mode(self):
        self._test('"Walk the dog."', 'Walk the dog.')

    def test_advanced_mode_delay(self):
        self._test('"Walk the dog." in 6 minutes', 'Walk the dog.')

    def test_advanced_mode_time(self):
        self._test('"Walk the dog." at 11:59 p.m.', 'Walk the dog.')

    def test_advanced_mode_public(self):
        self._test('"Walk the dog." public', self.sender_mention + 'Walk the dog.')

    def test_advanced_mode_delay_public(self):
        self._test('"Walk the dog." in 8 minutes public', self.sender_mention + 'Walk the dog.')

    def test_advanced_mode_time_public(self):
        self._test('"Walk the dog." at 11:59 p.m. public', self.sender_mention + 'Walk the dog.')

    def test_bad_time(self):
        self._test('"Walk the dog." at 13:64 p.m.', 'Sorry, that time doesn\'t make sense.')

    def test_past_time(self):
        self._test('"Walk the dog." at 12:00 a.m.', 'Sorry, the time can\'t be in the past.')
