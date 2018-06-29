#!/usr/bin/env python

import os
import sys
import wsgiref.simple_server

from flask import Response

from linebot import (LineBotApi, WebhookParser)
from linebot.exceptions import (InvalidSignatureError)
from linebot.models import (MessageEvent, TextMessage, TextSendMessage)
from linebot.utils import PY3

from .command import (PingCommand, JinguReservationStateThisWeak)


class Bot(object):
    COMMAND_PREFIX = '@bot'

    def __init__(self):
        secret, access_token = self.check_required_environmental_variables()
        self.commands = [PingCommand(), JinguReservationStateThisWeak()]
        self.line_bot_api = LineBotApi(access_token)
        self.parser = WebhookParser(secret)

    def check_required_environmental_variables(self):
        channel_secret = os.getenv('LINEBOT_TENNIS_LINE_CHANNEL_SECRET', None)
        channel_access_token = os.getenv(
            'LINEBOT_TENNIS_LINE_CHANNEL_ACCESS_TOKEN', None)
        if channel_secret is None:
            raise Exception(
                'Specify LINEBOT_TENNIS_LINE_CHANNEL_SECRET as environment variable.'
            )
        if channel_access_token is None:
            raise Exception(
                'Specify LINEBOT_TENNIS_LINE_CHANNEL_ACCESS_TOKEN as environment variable.'
            )
        return (channel_secret, channel_access_token)

    def handle_request(self, request):
        if request.method != 'POST':
            return Response('404', status=404)
        signature = request.headers.get('X_LINE_SIGNATURE')
        wsgi_input = request.headers.get('wsgi.input')
        content_length = int(request.headers.get('CONTENT_LENGTH'))
        #body = wsgi_input.read(content_length).decode('utf-8')
        body = request.stream.read().decode('utf-8')

        try:
            events = self.parser.parse(body, signature)
        except InvalidSignatureError:
            return Response('Bad request', status=400)

        for event in events:
            if self.is_event_for_connection_test(event):
                print('Ignore the message because it is connection test')
            elif event.type == 'message' and event.message.type == 'text':
                self.handle_message(event.message.text, event.reply_token)

        return Response('OK', status=200)

    def send_help_string(self, reply_token):
        help_string = 'Available commands:\n' + '\n'.join(
            [c.help() for c in self.commands])
        self.line_bot_api.reply_message(
            reply_token, TextSendMessage(text=help_string))

    def is_event_for_connection_test(self, event):
        return (event.type == 'message' and
                (event.message.id == '100001' or event.message.id == '100002'))

    def handle_message(self, message_text, reply_token):
        if message_text.startswith(self.COMMAND_PREFIX):
            message_body = message_text[len(self.COMMAND_PREFIX):].strip()
            for command in self.commands:
                if command.is_match(message_body):
                    command.reply(message_body, reply_token, self.line_bot_api)
                    return
            self.send_help_string(reply_token)


if __name__ == '__main__':
    test_bot = Bot()
