#!/usr/bin/env python

import os
import sys

from flask import (Flask, request)

# add load path to ../linebot-tennis
if __name__ == '__main__':
    libdir = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
    if os.path.exists(os.path.join(libdir, 'linebot_tennis')):
        sys.path.insert(0, libdir)

from linebot_tennis import Bot, jingu

app = Flask(__name__)
bot = Bot()

@app.route('/callback', methods=['GET', 'POST'])
def app_callback():
    print('/callback')
    return bot.handle_request(request)

@app.route('/image/jingu/<year>/<month>/<day>')
def jingu_image(year, month, day):
    print('/image/jingu')
    return jingu.serve_image(int(year), int(month), int(day))

if __name__ == '__main__':
    app.run()
