from datetime import (datetime, timedelta)

from linebot.models import (TextSendMessage, ImageSendMessage)

from .jingu import url_for_the_date as jingu_url_for_the_date
from .jingu import url_for_html as jingu_url_for_html


class Command(object):

    def help(self):
        pass

    def is_match(self, message):
        return False

    def reply(self, body, token, api):
        pass


class PingCommand(Command):

    def help(self):
        return 'ping -- return pong'

    def is_match(self, message):
        return message.startswith('ping')

    def reply(self, body, token, api):
        api.reply_message(token, TextSendMessage(text='pong'))


class JinguReservationStateThisWeek(Command):

    def help(self):
        return 'thisweek -- show this week reservation @ jingu tennis court'

    def is_match(self, message):
        return message.startswith('thisweek')

    def reply(self, body, token, api):
        today = datetime.today()
        image_url = jingu_url_for_the_date(today)
        api.reply_message(
            token, [
                ImageSendMessage(
                    original_content_url=image_url,
                    preview_image_url=
                    'https://linebot-tennis.herokuapp.com/image/nowloading.jpg'
                ),
                TextSendMessage(text='webからもこの結果を見ることができます {url}'.format(
                    jingu_url_for_html(today)))
            ])
