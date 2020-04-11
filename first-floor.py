#!/usr/bin/env python3
"""Demo file showing how to use the mitemp library."""

import argparse
import re
import datetime
import requests

from miio import chuangmi_plug
from btlewrap import available_backends, BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY


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
    heat_url = 'http://smart.levabd.pp.ua:2003/heat/key/27fbc501b51b47663e77c46816a'
    ac_heat = check_if_ac_heat()
    if ac_heat is not None:
        if not ac_heat:
            response = requests.get(heat_url)
            print(response.json())
    return


def turn_on_cool_ac():
    """Turn on AC on a first floor for a cooling if it was not."""
    cool_url = 'http://smart.levabd.pp.ua:2003/cool/key/27fbc501b51b47663e77c46816a'
    ac_cool = check_if_ac_cool()
    if ac_cool is not None:
        if not ac_cool:
            response = requests.get(cool_url)
            print(response.json())


def turn_off_ac():
    """Turn off AC on a first floor."""
    turn_url = 'http://smart.levabd.pp.ua:2003/power-off/key/27fbc501b51b47663e77c46816a'
    response = requests.get(turn_url)
    print(response.json())


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
    print(today.month)
    print(today.hour)
    if (temperature > 25.8) and (today.month < 10) and (today.month > 4):
        turn_on_cool_ac()
    if (temperature < 23) and (today.month < 10) and (today.month > 4):
        turn_off_ac()
    if (temperature < 20) and (today.month > 9) and (today.month < 5):
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


if __name__ == '__main__':
    main()
