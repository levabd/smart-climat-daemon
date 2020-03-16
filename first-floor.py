#!/usr/bin/env python3
"""Demo file showing how to use the mitemp library."""

import argparse
import re
import logging
import sys

from btlewrap import available_backends, BluepyBackend, GatttoolBackend, PygattBackend
from mitemp_bt.mitemp_bt_poller import MiTempBtPoller, \
    MI_TEMPERATURE, MI_HUMIDITY, MI_BATTERY


def valid_mitemp_mac(mac, pat=re.compile(r"[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}:[0-9A-F]{2}")):
    """Check for valid mac adresses."""
    if not pat.match(mac.upper()):
        raise argparse.ArgumentTypeError('The MAC address "{}" seems to be in the wrong format'.format(mac))
    return mac


def pollTempHumidity():
    """Poll data from the sensor."""
    backend = BluepyBackend
    poller = MiTempBtPoller('58:2d:34:38:c0:91', backend)
    print("Getting data from Mi Temperature and Humidity Sensor")
    print("FW: {}".format(poller.firmware_version()))
    print("Name: {}".format(poller.name()))
    print("Battery: {}".format(poller.parameter_value(MI_BATTERY)))
    print("Temperature: {}".format(poller.parameter_value(MI_TEMPERATURE)))
    print("Humidity: {}".format(poller.parameter_value(MI_HUMIDITY)))


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
    pollTempHumidity()


if __name__ == '__main__':
    main()
