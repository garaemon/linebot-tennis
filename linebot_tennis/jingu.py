#!/usr/bin/python

import asyncio
from datetime import (datetime, timedelta)
import io
import urllib
import urllib.request

from pyquery import PyQuery as pq
from flask import Response, make_response

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_agg import FigureCanvasAgg

JINGU_URL = 'http://www.meijijingugaien.jp/sports/futsal/reserve.php'
TENNIS_ONLY_COURT_SELECTOR = '#anc01'
TENNIS_FOOTSAL_COURT_SELECTOR = '#anc02'
TIME_TITLES = [
    '7:00-8:00', '8:00-9:00', '9:00-10:00', '10:00-11:00', '11:00-12:00',
    '12:00-13:00', '13:00-14:00', '14:00-15:00', '15:00-16:00', '16:00-17:00',
    '17:00-18:00', '18:00-19:00', '19:00-20:00', '20:00-21:00', '21:00-22:00',
    '22:00-23:00'
]
FREE_COLOR = (0.48, 0.75, 0.94)
RESERVED_COLOR = (0.93, 0.4, 0.4)


def parse_table(tds, skip_index):
    # Remove the first 2 tags
    # First <td> tag --> date
    # Second <td> tag --> name of the court
    index = 0
    reserved_info = []
    for td in tds.items():
        if index < skip_index:
            pass  # ignore
        else:
            if td.hasClass('reserved'):
                reserved_info.append('reserved')
            else:
                reserved_info.append('free')
        index = index + 1
    return reserved_info


def parse_tennis_only_court_table(table):
    return parse_table(table('td'), skip_index=2)


def parse_tennis_footsal_court_table(table):
    trs = table('tbody tr')
    tr_index = 0
    reserved_info_array = []
    for tr in trs.items():
        if tr_index == 0:
            reserved_info = parse_table(tr('td'), skip_index=2)
            reserved_info_array.append(reserved_info)
        else:
            reserved_info = parse_table(tr('td'), skip_index=1)
            reserved_info_array.append(reserved_info)
        tr_index = tr_index + 1
    reserved_info_result = []
    court_num = len(reserved_info_array)
    for time_index in range(len(TIME_TITLES)):
        reserved_info_of_time_index_array = [
            info[time_index] for info in reserved_info_array
        ]
        is_free = any(
            [info == 'free' for info in reserved_info_of_time_index_array])
        if is_free:
            reserved_info_result.append('free')
        else:
            reserved_info_result.append('reserved')
    return reserved_info_result


def url_for_the_date(date):
    return 'https://linebot-tennis.herokuapp.com/image/jingu/%d/%02d/%02d' % (
        date.year, date.month, date.day)


def url_for_html(date):
    return 'https://linebot-tennis.herokuapp.com/jingu/%d/%02d/%02d' % (
        date.year, date.month, date.day)


async def query_reservation_page(date, index):
    y = date.year
    m = date.month
    d = date.day
    url = '%s?y=%04d&m=%02d&d=%02d' % (JINGU_URL, y, m, d)
    print('Querying %s' % (url))
    with urllib.request.urlopen(url) as response:
        return (response.read(), index, url)
    # dom = pq(url)
    # return dom


def parse_reservation_page(page):
    dom = pq(page)
    tennis_only_court_table = dom(TENNIS_ONLY_COURT_SELECTOR).parent()('table')
    tennis_only_court_reserved_info = parse_tennis_only_court_table(
        tennis_only_court_table)
    tennis_only_court_color = convert_reserved_info_to_colors(
        tennis_only_court_reserved_info)
    tennis_footsal_court_table = dom(TENNIS_FOOTSAL_COURT_SELECTOR).parent()(
        'table')
    tennis_footsal_court_reserved_info = parse_tennis_footsal_court_table(
        tennis_footsal_court_table)
    tennis_footsal_court_color = convert_reserved_info_to_colors(
        tennis_footsal_court_reserved_info)
    return plt.table(
        colLabels=TIME_TITLES,
        rowLabels=['tennis', 'footsal'],
        cellText=[
            tennis_only_court_reserved_info, tennis_footsal_court_reserved_info
        ],
        cellColours=[tennis_only_court_color, tennis_footsal_court_color],
        loc='center')


def convert_reserved_info_to_colors(reserved_info):
    colors = []
    for info in reserved_info:
        if info == 'free':
            colors.append(FREE_COLOR)
        else:
            colors.append(RESERVED_COLOR)
    return colors


def demo():
    today = datetime.today()
    fig = plt.figure(figsize=(30, 8))

    with Pool(7) as p:
        contents_array = p.map(
            query_reservation_page,
            [today + timedelta(days=i) for i in range(7)])
    for i, content in zip(range(7), contents_array):
        target_day = today + timedelta(days=i)
        ax = plt.subplot(711 + i)
        ax.set_title('%d/%d(%s)' % (target_day.month, target_day.day,
                                    target_day.strftime('%a')))
        parse_reservation_page(content)
        ax.axis('off')
        ax.grid('off')
    plt.savefig('test.png')


def serve_image(year, month, day):
    start_day = datetime(year, month, day)
    fig = plt.figure(figsize=(30, 8))
    loop = asyncio.get_event_loop()
    print('start_day', start_day)
    tasks, _ = loop.run_until_complete(
        asyncio.wait([
            query_reservation_page(start_day + timedelta(days=i), i)
            for i in range(7)
        ]))
    contents_array = [task.result() for task in tasks]
    # contents_array is a list of (url, index, url)
    # sort contents_array by index because asyncio.wait may change the order of
    # range.
    sorted_contents = sorted(contents_array, key=lambda x: x[1])
    for i, content_tuple in zip(range(7), sorted_contents):
        (content, index, url) = content_tuple
        print(i, index, url)
        ax = plt.subplot(711 + i)
        target_day = start_day + timedelta(days=i)
        ax.set_title('%d/%d(%s)' % (target_day.month, target_day.day,
                                    target_day.strftime('%a')))
        parse_reservation_page(content)
        ax.axis('off')
        ax.grid('off')
    canvas = FigureCanvasAgg(fig)
    buf = io.BytesIO()
    canvas.print_png(buf)
    response = make_response(buf.getvalue())
    response.mimetype = 'image/png'
    return response


def serve_html(year, month, day):
    now_str = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    return '''<html>
    <head>
    <style>
    img {{
      max-width: 100%;
    }}
    </style>
    </head>
    <body>
    <h1>神宮球場前テニスコート予約状況</h1>
    <p>
    <strong>画像の取得には時間がかかることがあります</strong>
    </p>
    <p>
    <a href={image_url}><img src={image_url} alt-"画像取得中"></img></a>
    </p>
    <p>テニスコートの予約状況は<a href="{jingu_url}">jingu_url</a>から取得しています</p>
    <p>予約の電話番号は <a href="tel:03-3403-0923">03-3403-0923</a> です.</p>
    run at {now}
    </body>
    </html>
    '''.format(
        image_url=url_for_the_date(datetime.now()),
        jingu_url=JINGU_URL,
        now=now_str)


if __name__ == '__main__':
    demo()
