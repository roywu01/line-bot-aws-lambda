# -*- coding: utf-8 -*-
from botocore.vendored import requests
import json
import twstock
import datetime
from model import *
from services import *
import os


access_token = os.environ.get('api_access_token')
user_id = os.environ.get('target_user_id')

push_msg = 'https://api.line.me/v2/bot/message/push'
reply_msg = 'https://api.line.me/v2/bot/message/reply'


def lambda_handler(event, context):
    try:
        Session.commit()
    except:
        Session.rollback()

    if event.get('detail-type') == 'Scheduled Event':
        for source in event.get('resources'):
            if 'rule/CheckStock' in source:
                check_stock(event)
    else:
        for e in event.get('events'):
            if e.get('message').get('type') == 'text' and e.get('message').get('text').startswith('!'):
                print(e.get('message').get('text'))
                if '!weather' in e.get('message').get('text'):
                    send_weather_msg(e)
                if '!add' in e.get('message').get('text'):
                    add_stock(e)
                if '!remove' in e.get('message').get('text'):
                    remove_stock(e)
    return event


def send_weather_msg(e):
    params = {
        'to': e.get('source').get('groupId'),
        'messages': [
            {
                'type': 'text',
                'text': get_weather_description()
            }
        ]
    }

    r = requests.post(push_msg, headers={
        'Authorization': 'Bearer {access_token}'.format(access_token=access_token),
        'Content-Type': 'application/json'
    }, data=json.dumps(params))

    return r


def get_weather_description():
    weather = requests.get('https://works.ioa.tw/weather/api/weathers/3.json').json()
    result = '各位夥伴安安，今天天氣為{desc}，現在溫度為{temperature}度，體感溫度為{felt_air_temp}度，濕度為{humidity}%，日落時間為{sunset}。(資訊來源: Google Maps API)\n\n' \
        .format(desc=weather.get('desc'), temperature=weather.get('temperature'), felt_air_temp=weather.get('felt_air_temp'), humidity=weather.get('humidity'),
                sunset=weather.get('sunset'))
    result += '\n\n'.join(weather.get('specials'))
    return result


def check_stock(e):
    stock_ids = []

    tracking = Session.query(Tracking).all()
    for tracking in tracking:
        stock_ids.append(tracking.stock_id)

    r = twstock.realtime.get(stock_ids)

    for i in stock_ids:
        row = r.get(i)

        best = row.get('realtime').get('latest_trade_price')  # string

        low = row.get('realtime').get('low')
        high = row.get('realtime').get('high')

        stock_id = row.get('info').get('code')
        name = row.get('info').get('name')

        last_record = Session.query(Stock).filter(Stock.stock_id == stock_id).order_by(Stock.id.desc()).first()

        if last_record is not None and float(last_record.price) == float(best):
            continue

        stock = Stock(
            stock_id,
            datetime.datetime.utcnow().date(),
            best
        )

        Session.add(stock)
        Session.commit()

        d = '{name}({id}) : {price}, low: {low}, high: {high}. {ds}'
        ds = ''
        if best <= low:
            ds = 'LOWEST Today!'
        elif best >= high:
            ds = 'HIGHEST Today!'

        if d is not None:
            params = {
                'to': user_id,
                'messages': [
                    {
                        'type': 'text',
                        'text': d.format(name=name, id=stock_id, ds=ds, price=str(best), low=low, high=high)
                    }
                ]
            }

            requests.post(push_msg, headers={
                'Authorization': 'Bearer {access_token}'.format(access_token=access_token),
                'Content-Type': 'application/json'
            }, data=json.dumps(params))

    return {}


def add_stock(e):
    stock_id = e.get('message').get('text').split(' ')[1]
    try:
        tracking = Tracking(stock_id=stock_id)
        Session.add(tracking)
        Session.commit()
        response_text = 'Success to add stock[{}]'.format(stock_id)
    except Exception as error:
        response_text = str(error)

    params = {
        "replyToken": e.get('replyToken'),
        "messages": [
            {
                "type": "text",
                "text": str(response_text)
            },
        ]
    }

    r = requests.post(reply_msg, headers={
        'Authorization': 'Bearer {access_token}'.format(access_token=access_token),
        'Content-Type': 'application/json'
    }, data=json.dumps(params))


def remove_stock(e):
    stock_id = e.get('message').get('text').split(' ')[1]
    try:
        tracking = Session.query(Tracking).filter(Tracking.stock_id == stock_id).first()
        Session.delete(tracking)
        Session.commit()
        response_text = 'Success to remove stock[{}]'.format(stock_id)
    except Exception as error:
        response_text = str(error)

    params = {
        "replyToken": e.get('replyToken'),
        "messages": [
            {
                "type": "text",
                "text": str(response_text)
            },
        ]
    }

    r = requests.post(reply_msg, headers={
        'Authorization': 'Bearer {access_token}'.format(access_token=access_token),
        'Content-Type': 'application/json'
    }, data=json.dumps(params))

