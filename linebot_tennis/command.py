from datetime import (datetime, timedelta)

from linebot.models import (
    TextSendMessage, ImageSendMessage
)

from .jingu import url_for_the_date as jingu_url_for_the_date


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


class JinguReservationStateThisWeak(Command):
    def help(self):
        return 'thisweek -- show this weak reservation @ jingu tennis court'

    def is_match(self, message):
        return message.startswith('thisweek')

    def reply(self, body, token, api):
        today = datetime.today()
        image_url = jingu_url_for_the_date(today)
        api.reply_message(token, ImageSendMessage(original_content_url=image_url,
                          preview_image_url=image_url))