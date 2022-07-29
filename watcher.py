import os
import sys
import json
import time
import tinytuya
import argparse
import requests
import pygsheets
from datetime import datetime, timedelta

__sheet__ = 'https://docs.google.com/spreadsheets/d/{id}/edit?usp=sharing'
__path__ = os.path.dirname(os.path.realpath(__file__))
__line__ = 'curl -H "Authorization: Bearer {bearer}" -d "message={message}" https://notify-api.line.me/api/notify'

def notify(bearer, message):
    os.system(__line__.format(
        bearer=bearer,
        message=message
    ))

def outlet(auth, device, val):
    cloud = tinytuya.Cloud(
        apiRegion="us",
        apiKey=auth['key'],
        apiSecret=auth['secret'],
        apiDeviceID=auth['device_id'])

    commands = {
        'commands': [
            {
                'code': 'switch_1',
                'value': val
            },
            {
                'code': 'countdown_1',
                'value': 0
            }
        ]
    }

    result = cloud.sendcommand(device, commands)
    return result['success'] == True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('bearer', help='')
    parser.add_argument('--key', default=os.path.join(__path__, 'key.json'), help='')
    parser.add_argument('--sheet', default='1O34xZfhJdFeZd-s4M4bIOhdNhbyFw7M7y4nzoHyknwQ', help='')
    parser.add_argument('--tuya', nargs='+', help='')
    args = parser.parse_args()

    certificate = pygsheets.authorize(service_file=args.key)
    sht = certificate.open_by_url(__sheet__.format(id=args.sheet))
    wks_list = sht.worksheets()

    for wks in wks_list:
        data = wks.get_all_records(numericise_data=False)
        for worker in data:
            if worker['notify'] == '0':
                continue

            report = datetime.strptime(worker['time'], '%Y/%m/%d %H:%M:%S')
            current = datetime.now()
            time_delta = current - report

            if time_delta > timedelta(minutes=25):
                result = True

                if worker['outlet'] == '':
                    result = False
                else:
                    result &= outlet(
                        {
                            'key': args.tuya[0],
                            'secret': args.tuya[1],
                            'device_id': args.tuya[2]
                        },
                        worker['outlet'],
                        False
                    )
                    time.sleep(5)
                    result &= outlet(
                        {
                            'key': args.tuya[0],
                            'secret': args.tuya[1],
                            'device_id': args.tuya[2]
                        },
                        worker['outlet'],
                        True
                    )

                if result == False:
                    notify(args.bearer, '{farm}.{worker} is offline'.format(
                        farm=wks.title,
                        worker=worker['miner']
                    ))

if __name__ == '__main__':
    main()