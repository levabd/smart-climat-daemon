#!/usr/bin/env python3
"""Demo file showing how to use the mitemp library."""

import os
import json
import argparse
import re
import datetime
import requests

from miio import chuangmi_plug
from btlewrap import available_backends, BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY

state = {}
state['triedTurnedOff'] = 0
state['wasTurnedOff'] = 0
state['triedTurnedCool'] = 0
state['wasTurnedCool'] = 0
state['triedTurnedHeat'] = 0
state['wasTurnedHeat'] = 0
with open('ac_state.json', 'w') as f:
    json.dump(state, f)

triedTurnedOff = int(os.environ["TRIEDTURNEDOFF"])
wasTurnedOff = int(os.environ["WASTURNEDOFF"])
triedTurnedCool = int(os.environ["TRIEDTURNEDCOOL"])
wasTurnedCool = int(os.environ["WASTURNEDCOOL"])
triedTurnedHeat = int(os.environ["TRIEDTURNEDHEAT"])
wasTurnedHeat = int(os.environ["WASTURNEDHEAT"])

def valid_mitemp_mac(mac, pat=re.compile(r"[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac addresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError(
            'The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac


def turn_on_humidifier():
    """Turn on humidifier on a first floor."""
    cP = chuangmi_plug.ChuangmiPlug(ip='192.168.19.59', token='56e74499dda17df9068e0a0cb00213f9', start_id=0, debug=0, lazy_discover=True, model='chuangmi.plug.m1')
    cP.on()


def turn_off_humidifier():
    """Turn off humidifier on a first floor."""
    cP = chuangmi_plug.ChuangmiPlug(ip='192.168.19.59', token='56e74499dda17df9068e0a0cb00213f9', start_id=0, debug=0, lazy_discover=True, model='chuangmi.plug.m1')
    cP.off()


def check_if_ac_off():
    """Check if AC is turned off."""
    status_url = 'http://smart.levabd.pp.ua:2003/status/key/27fbc501b51b47663e77c46816a'
    response = requests.get(status_url, timeout=(20, 30))
    if ('address' in response.json()) and ('name' in response.json()):
        if ((response.json()['name'] == "08bc20043df8") and (response.json()['address'] == "192.168.19.54")):
            if response.json()['props']['boot'] == 0:
                return True
            return False
    return None

def check_if_ac_cool():
    """Check if AC is turned for a automate cooling."""
    status_url = 'http://smart.levabd.pp.ua:2003/status/key/27fbc501b51b47663e77c46816a'
    response = requests.get(status_url, timeout=(20, 30))
    if ('address' in response.json()) and ('name' in response.json()):
        if ((response.json()['name'] == "08bc20043df8") and (response.json()['address'] == "192.168.19.54")):
            if not response.json()['props']['boot'] == 1:
                return False
            if not response.json()['props']['runMode'] == '001':
                return False
            if not response.json()['props']['healthy'] == 1:
                return False
            if not response.json()['props']['wdNumber'] == 25:
                return False
            if not response.json()['props']['windLevel'] == '001':
                return False
            return True
    return None


def check_if_ac_heat():
    """Check if AC is turned for a automate heating."""
    status_url = 'http://smart.levabd.pp.ua:2003/status/key/27fbc501b51b47663e77c46816a'
    response = requests.get(status_url, timeout=(20, 30))
    if ('address' in response.json()) and ('name' in response.json()):
        if ((response.json()['name'] == "08bc20043df8") and (response.json()['address'] == "192.168.19.54")):
            if not response.json()['props']['boot'] == 1:
                return False
            if not response.json()['props']['runMode'] == '100':
                return False
            if not response.json()['props']['healthy'] == 1:
                return False
            if not response.json()['props']['wdNumber'] == 23:
                return False
            if not response.json()['props']['windLevel'] == '001':
                return False
            return True
    return None


def turn_on_heat_ac():
    """Turn on AC on a first floor for a heating if it was not."""
    if (wasTurnedHeat == 1) and not (triedTurnedHeat == 1):
        return
    heat_url = 'http://smart.levabd.pp.ua:2003/heat/key/27fbc501b51b47663e77c46816a'
    ac_heat = check_if_ac_heat()
    if ac_heat is not None:
        if not ac_heat:
            os.environ["TRIEDTURNEDHEAT"] = "1"
            os.environ["WASTURNEDHEAT"] = "0"
            response = requests.get(heat_url)
            print(response.json())
        else:
            if (triedTurnedHeat == 1):
                os.environ["TRIEDTURNEDOFF"] = "0"
                os.environ["WASTURNEDOFF"] = "0"
                os.environ["TRIEDTURNEDCOOL"] = "0"
                os.environ["WASTURNEDCOOL"] = "0"
                os.environ["TRIEDTURNEDHEAT"] = "0"
                os.environ["WASTURNEDHEAT"] = "1"


def turn_on_cool_ac():
    """Turn on AC on a first floor for a cooling if it was not."""
    if (wasTurnedCool == 1) and not (triedTurnedCool == 1):
        return
    cool_url = 'http://smart.levabd.pp.ua:2003/cool/key/27fbc501b51b47663e77c46816a'
    ac_cool = check_if_ac_cool()
    if ac_cool is not None:
        if not ac_cool:
            os.environ["TRIEDTURNEDCOOL"] = "1"
            os.environ["WASTURNEDCOOL"] = "0"
            response = requests.get(cool_url)
            print(response.json())
        else:
            if (triedTurnedCool == 1):
                os.environ["TRIEDTURNEDOFF"] = "0"
                os.environ["WASTURNEDOFF"] = "1"
                os.environ["TRIEDTURNEDCOOL"] = "0"
                os.environ["WASTURNEDCOOL"] = "1"
                os.environ["TRIEDTURNEDHEAT"] = "0"
                os.environ["WASTURNEDHEAT"] = "0"


def turn_off_ac():
    """Turn off AC on a first floor."""
    if (wasTurnedOff == 1) and not (triedTurnedOff == 1):
        return
    turn_url = 'http://smart.levabd.pp.ua:2003/power-off/key/27fbc501b51b47663e77c46816a'
    ac_off = check_if_ac_off()
    if ac_off is not None:
        if not ac_off:
            os.environ["TRIEDTURNEDOFF"] = "1"
            os.environ["WASTURNEDOFF"] = "0"
            response = requests.get(turn_url)
            print(response.json())
        else:
            if (triedTurnedOff == 1):
                os.environ["TRIEDTURNEDOFF"] = "0"
                os.environ["WASTURNEDOFF"] = "1"
                os.environ["TRIEDTURNEDCOOL"] = "0"
                os.environ["WASTURNEDCOOL"] = "0"
                os.environ["TRIEDTURNEDHEAT"] = "0"
                os.environ["WASTURNEDHEAT"] = "0"


def poll_temp_humidity():
    """Poll data from the sensor."""
    today = datetime.datetime.today()
    backend = BluepyBackend
    poller = MiTempBtPoller('58:2d:34:38:c0:91', backend)
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

# def scan(args):
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
    """Main function.

    """
    # check_if_ac_cool()
    (today, temperature, humidity) = poll_temp_humidity()
    if (today.hour > -1) and (today.hour < 7):
        turn_off_ac()
    if (temperature > 25.8) and (today.month < 10) and (today.month > 4) and (today.hour < 24) and (today.hour > 6):
        turn_on_cool_ac()
    if (temperature < 23) and (today.month < 10) and (today.month > 4):
        turn_off_ac()
    if (temperature < 20) and (today.month > 9) and (today.month < 5) and (today.hour < 24) and (today.hour > 6):
        turn_on_heat_ac()
    if (temperature > 22) and (today.month > 9) and (today.month < 5):
        turn_off_ac()
    if (humidity > 49) and (today.month < 10) and (today.month > 4):
        turn_off_humidifier()
    if (humidity < 30) and (today.month < 10) and (today.month > 4):
        turn_on_humidifier()
    if (humidity < 23) and (today.month > 9) and (today.month < 5):
        turn_on_humidifier()
    if (humidity > 40) and (today.month > 9) and (today.month < 5):
        turn_off_humidifier()
    
    # clear env at night
    if (today.hour == 4):
        os.environ["TRIEDTURNEDOFF"] = "0"
        os.environ["WASTURNEDOFF"] = "0"
        os.environ["TRIEDTURNEDCOOL"] = "0"
        os.environ["WASTURNEDCOOL"] = "0"
        os.environ["TRIEDTURNEDHEAT"] = "0"
        os.environ["WASTURNEDHEAT"] = "0"


if __name__ == '__main__':
    main()
