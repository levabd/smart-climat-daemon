#!/usr/bin/env python3

import json
import argparse
import re
import datetime
import paramiko
import requests

# cmd  ['ssh', 'smart',
#        'mkdir -p /home/levabd/smart-home-temp-humidity-monitor;
#         cat - > /home/levabd/smart-home-temp-humidity-monitor/lr.json']

from btlewrap import available_backends, BluepyBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

br_state = {}
cb_state = {}
f = open('/home/pi/smart-climat-daemon/ac_br_state.json')
br_state = json.load(f)
f = open('/home/pi/smart-climat-daemon/ac_cb_state.json')
cb_state = json.load(f)

dummy_ac_url = 'http://smart.levabd.pp.ua:2002'

def valid_mitemp_mac(mac, pat=re.compile(r"[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac addresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError(
            'The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac

#  turn_on_humidifier():
#     """Turn on humidifier on a first floor."""
#     hummidifier_plug = chuangmi_plug.ChuangmiPlug(
#         ip='192.168.19.61',
#         token='14f5b868a58ef4ffaef6fece61c65b16',
#         start_id=0,
#         debug=1,
#         lazy_discover=True,
#         model='chuangmi.plug.m1')
#     hummidifier_plug.on()
#
#
# def turn_off_humidifier():
#     """Turn off humidifier on a first floor."""
#     hummidifier_plug = chuangmi_plug.ChuangmiPlug(
#         ip='192.168.19.61',
#         token='14f5b868a58ef4ffaef6fece61c65b16',
#         start_id=0,
#         debug=1,
#         lazy_discover=True,
#         model='chuangmi.plug.m1')
#     hummidifier_plug.off()

def check_if_ac_off(room):
    """Check if AC is turned off."""
    status_url = dummy_ac_url
    if room == 'br':
        status_url = 'http://smart.levabd.pp.ua:2002/status-bedroom?key=27fbc501b51b47663e77c46816a'
    elif room == 'cb':
        status_url = 'http://smart.levabd.pp.ua:2002/status-office?key=27fbc501b51b47663e77c46816a'
    response = requests.get(status_url, timeout=(20, 30))
    if 'Pow' in response.json():
        print(response.json()['Pow'])
        if response.json()['Pow'] == "ON":
            return False
        return True
    return None

def check_if_ac_cool(room):
    """Check if AC is turned for a automate cooling."""
    status_url = dummy_ac_url
    if room == 'br':
        status_url = 'http://smart.levabd.pp.ua:2002/status-bedroom?key=27fbc501b51b47663e77c46816a'
    elif room == 'cb':
        status_url = 'http://smart.levabd.pp.ua:2002/status-office?key=27fbc501b51b47663e77c46816a'
    response = requests.get(status_url, timeout=(20, 30))
    print(response.json())
    if 'Pow' in response.json():
        if (response.json()['Pow'] == "ON") and (response.json()['Mod'] == "COOL"):
            return True
        return False
    return None

def set_cool_temp_ac(room, temp):
    """Set AC temerature of cooling if AC already turned cool."""
    state = {}
    state = br_state if room == 'br' else cb_state # 'cb'
    if not state['wasTurnedCool'] == 1 and check_if_ac_cool(room):
        return
    temp_url = dummy_ac_url
    if room == 'br':
        temp_url = 'http://smart.levabd.pp.ua:2002/setTemp-bedroom?key=27fbc501b51b47663e77c46816a&temp='
    elif room == 'cb':
        temp_url = 'http://smart.levabd.pp.ua:2002/setTemp-office?key=27fbc501b51b47663e77c46816a&temp='

    response = requests.get(temp_url + temp)
    print(response)


def turn_on_cool_ac(room):
    """Turn on AC for a cooling if it was not."""
    state = {}
    state = br_state if room == 'br' else cb_state # 'cb'
    ac_cool = check_if_ac_cool(room)
    if ((state['wasTurnedCool'] == 1) and not state['triedTurnedCool'] == 1) or (ac_cool is None):
        return
    if ac_cool and (state['triedTurnedCool'] == 1):
        if room == 'br':
            br_state['triedTurnedOff'] = 0
            br_state['wasTurnedOff'] = 0
            br_state['triedTurnedCool'] = 0
            br_state['wasTurnedCool'] = 1
            br_state['triedTurnedHeat'] = 0
            br_state['wasTurnedHeat'] = 0
            with open('/home/pi/smart-climat-daemon/ac_br_state.json', 'w') as file:
                json.dump(br_state, file)
        elif room == 'cb':
            cb_state['triedTurnedOff'] = 0
            cb_state['wasTurnedOff'] = 0
            cb_state['triedTurnedCool'] = 0
            cb_state['wasTurnedCool'] = 1
            cb_state['triedTurnedHeat'] = 0
            cb_state['wasTurnedHeat'] = 0
            with open('/home/pi/smart-climat-daemon/ac_cb_state.json', 'w') as file:
                json.dump(cb_state, file)
        return
    cool_url = dummy_ac_url
    turn_on_url = dummy_ac_url
    temp_url = dummy_ac_url
    if room == 'br':
        turn_on_url = 'http://smart.levabd.pp.ua:2002/powerOn-bedroom?key=27fbc501b51b47663e77c46816a'
        cool_url = 'http://smart.levabd.pp.ua:2002/cool-bedroom?autoFan=false&key=27fbc501b51b47663e77c46816a'
        temp_url = 'http://smart.levabd.pp.ua:2002/setTemp-bedroom?key=27fbc501b51b47663e77c46816a&temp=26'
    elif room == 'cb':
        turn_on_url = 'http://smart.levabd.pp.ua:2002/powerOn-office?key=27fbc501b51b47663e77c46816a'
        cool_url = 'http://smart.levabd.pp.ua:2002/cool-office?autoFan=false&key=27fbc501b51b47663e77c46816a'
        temp_url = 'http://smart.levabd.pp.ua:2002/setTemp-office?key=27fbc501b51b47663e77c46816a&temp=26'
    if room == 'br':
        br_state['triedTurnedCool'] = 1
        br_state['wasTurnedCool'] = 0
        with open('/home/pi/smart-climat-daemon/ac_br_state.json', 'w') as file:
            json.dump(br_state, file)
    elif room == 'cb':
        cb_state['triedTurnedCool'] = 1
        cb_state['wasTurnedCool'] = 0
        with open('/home/pi/smart-climat-daemon/ac_cb_state.json', 'w') as file:
            json.dump(cb_state, file)
    response = requests.get(temp_url)
    print(response)
    response = requests.get(cool_url)
    print(response)
    response = requests.get(turn_on_url)
    print(response)


def turn_off_ac(room):
    """Turn off AC ."""
    state = {}
    state = br_state if room == 'br' else cb_state # 'cb'
    ac_off = check_if_ac_off(room)
    if ((state['wasTurnedOff'] == 1) and not state['triedTurnedOff'] == 1) or (ac_off is None):
        return
    if ac_off and (state['triedTurnedCool'] == 1):
        if room == 'br':
            br_state['triedTurnedOff'] = 0
            br_state['wasTurnedOff'] = 1
            br_state['triedTurnedCool'] = 0
            br_state['wasTurnedCool'] = 0
            br_state['triedTurnedHeat'] = 0
            br_state['wasTurnedHeat'] = 0
            with open('/home/pi/smart-climat-daemon/ac_br_state.json', 'w') as file:
                json.dump(br_state, file)
        elif room == 'cb':
            cb_state['triedTurnedOff'] = 0
            cb_state['wasTurnedOff'] = 1
            cb_state['triedTurnedCool'] = 0
            cb_state['wasTurnedCool'] = 0
            cb_state['triedTurnedHeat'] = 0
            cb_state['wasTurnedHeat'] = 0
            with open('/home/pi/smart-climat-daemon/ac_cb_state.json', 'w') as file:
                json.dump(cb_state, file)
    turn_url = dummy_ac_url
    if room == 'br':
        turn_url = 'http://smart.levabd.pp.ua:2002/powerOff-bedroom?key=27fbc501b51b47663e77c46816a'
    elif room == 'cb':
        turn_url = 'http://smart.levabd.pp.ua:2002/powerOff-office?key=27fbc501b51b47663e77c46816a'
    if room == 'br':
        br_state['triedTurnedOff'] = 1
        br_state['wasTurnedOff'] = 0
        with open('/home/pi/smart-climat-daemon/ac_br_state.json', 'w') as file:
            json.dump(br_state, file)
    elif room == 'cb':
        cb_state['triedTurnedOff'] = 1
        cb_state['wasTurnedOff'] = 0  
        with open('/home/pi/smart-climat-daemon/ac_cb_state.json', 'w') as file:
            json.dump(cb_state, file)
            
    response = requests.get(turn_url)
    print(response)

def record_temp_humid(temperature, humidity, room):
    """Record temperature and humidity data for web interface monitor"""
    dicty = {
        "temperature": temperature,
        "humidity": humidity
        }

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect('smart.levabd.pp.ua', port = 2001, username='levabd', password='vapipu280.')
    sftp = ssh.open_sftp()

    with sftp.open('smart-home-temp-humidity-monitor/' + room + '.json', 'w') as outfile:
        json.dump(dicty, outfile)

    ssh.close()


def poll_temp_humidity(room):
    """Poll data frstate['triedTurnedOff']om the sensor."""
    today = datetime.datetime.today()
    backend = BluepyBackend
    mac = '58:2d:34:38:be:2e' if room == 'br' else '58:2d:34:39:27:4e' # 'cb'
    poller = MiTempBtPoller(mac, backend)
    temperature = poller.parameter_value(MI_TEMPERATURE)
    humidity = poller.parameter_value(MI_HUMIDITY)
    print("Month: {}".format(today.month))
    print("Getting data from Mi Temperature and Humidity Sensor")
    print("FW: {}".format(poller.firmware_version()))
    print("Name: {}".format(poller.name()))
    print("Battery: {}".format(poller.parameter_value(MI_BATTERY)))
    print("Temperature: {}".format(poller.parameter_value(MI_TEMPERATURE)))
    print("Humidity: {}".format(poller.parameter_value(MI_HUMIDITY)))
    return (today, temperature, humidity)

#  scan(args):
#     """Scan for sensors."""
#     backend = _get_backend(args)
#     print('Scanning for 10 seconds...')
#     devices = mitemp_scanner.scan(backend, 10)
#     devices = []
#     print('Found {} devices:'.format(len(devices)))
#     for device in devices:
#         print('  {}'.format(device))


def list_backends(_):
    """List all available backends."""
    backends = [b.__name__ for b in available_backends()]
    print('\n'.join(backends))


def main():
    """Main function."""

    # check bedroom
    (today, temperature, humidity) = poll_temp_humidity('br')
    # if (humidity > 49) and (today.month < 10) and (today.month > 4):
    #     turn_off_humidifier()
    # if (humidity < 31) and (today.month < 10) and (today.month > 4):
    #     turn_on_humidifier()
    # if (humidity < 31) and ((today.month > 9) or (today.month < 5)):
    #     turn_on_humidifier()
    # if (humidity > 49) and ((today.month > 9) or (today.month < 5)):
    #     turn_off_humidifier()
    #
    # Prevent Sleep of Xiaomi Smart Plug
    # hummidifier_plug = chuangmi_plug.ChuangmiPlug(
    #   ip='192.168.19.59',
    #     token='14f5b868a58ef4ffaef6fece61c65b16',
    #     start_id=0,
    #     debug=0,
    #     lazy_discover=True,
    #     model='chuangmi.plug.m1')
    # print(hummidifier_plug.status())

    # Record temperature and humidity for monitor
    record_temp_humid(temperature, humidity, 'br')

    # clear env at night
    if today.hour == 3:
        br_state['triedTurnedOff'] = 0
        br_state['wasTurnedOff'] = 0
        br_state['triedTurnedCool'] = 0
        br_state['wasTurnedCool'] = 0
        br_state['triedTurnedHeat'] = 0
        br_state['wasTurnedHeat'] = 0
        cb_state['triedTurnedOff'] = 0
        cb_state['wasTurnedOff'] = 0
        cb_state['triedTurnedCool'] = 0
        cb_state['wasTurnedCool'] = 0
        cb_state['triedTurnedHeat'] = 0
        cb_state['wasTurnedHeat'] = 0
        with open('/home/pi/smart-climat-daemon/ac_br_state.json', 'w') as file:
            json.dump(br_state, file)
        with open('/home/pi/smart-climat-daemon/ac_cb_state.json', 'w') as file:
            json.dump(cb_state, file)

    # if (temperature > 24.0) and (today.month < 6) and (today.month > 3) and (today.hour < 11) and (today.hour > 3):
    #    turn_on_cool_ac('br')
    if (temperature > 32) and (today.hour < 24) and (today.hour > 7):
        turn_on_cool_ac('br')
    if (temperature > 25.3) and (today.month < 11) and (today.month > 4) and (today.hour < 8) and (today.hour > 4):
        turn_on_cool_ac('br')
    if (temperature < 23.3) and (today.hour < 8) and (today.hour > 4):
        turn_off_ac('br')
    if (temperature < 19) and (today.hour < 24) and (today.hour > 8):
        turn_off_ac('br')
    # _if (temperature < 20) and ((today.month > 9) or (today.month < 5)) and (today.hour < 24) and (today.hour > 9):
    #     turn_on_heat_ac()
    # if (temperature > 22) and ((today.month > 9) or (today.month < 5)):
    #     turn_off_ac()

    # record the office room numbers
    (_, temperature, humidity) = poll_temp_humidity('cb')
    record_temp_humid(temperature, humidity, 'cb')


if __name__ == '__main__':
    main()
