#!/usr/bin/env python
"""
Copyright 2016 ARM Limited

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""
# pylint:disable=missing-docstring

import logging
import unittest
import time
import os
from test.test_helper import Helper
import serial
import six
from mbed_flasher.flash import Flash
from mbed_flasher.reset import Reset
import mbed_lstools


def verify_output_per_device(serial_port, command, output):
    # print 'Inspecting %s SERIAL device' % serial_port
    ser = serial.Serial(
        port=serial_port,
        baudrate=115200,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
        bytesize=serial.EIGHTBITS
    )
    if ser.isOpen():
        time.sleep(0.2)
        if six.PY2:
            ser.write('%s\n\r' % command)
        else:
            new_command = '%s\n\r' % command
            ser.write(new_command.encode('utf-8'))
        out = ''
        time.sleep(0.5)
        while ser.inWaiting() > 0:
            if six.PY2:
                out += ser.read(1)
            else:
                out += ser.read(1).decode('utf-8', "replace")
        if out.find(output) != -1:
            ser.close()
            return True
        ser.close()
        return False


def check_two_binaries_exist():
    count = 0
    for _, _, files in os.walk('test/'):
        for name in files:
            if str(name).endswith('.bin'):
                count += 1

    return bool(count == 2)


def find_second_binary():
    for root, _, files in os.walk('test/'):
        for name in files:
            if str(name).endswith('.bin') and str(name).find('helloworld') == -1:
                return str(os.path.join(root, name))
    return None

# this is not a const
# pylint: disable=invalid-name
mbed = mbed_lstools.create()


@unittest.skipIf(mbed.list_mbeds() == [], "no hardware attached")
class FlashVerifyTestCase(unittest.TestCase):
    """
    Flash verification with Hardware, three step verification for all attached devices:
    first flashes the helloworld binary to device and verifies that no response is seen
    second flashes found second binary to device and verifies that response is seen
    third flashes the helloworld binary to device and verifies that no response is seen
    """
    bin_path = os.path.join('test', 'helloworld.bin')

    def setUp(self):
        logging.disable(logging.CRITICAL)
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    def tearDown(self):
        Helper(platform_name='K64F', allowed_files=['DETAILS.TXT', 'MBED.HTM']).clear()

    @unittest.skipIf(check_two_binaries_exist() is False,
                     "binaries missing or too many binaries in test-folder")
    def test_verify_hw_flash(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        flasher = Flash()
        target_id = None
        serial_port = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'serial_port' and 'target_id' in target:
                    target_id = target['target_id']
                    serial_port = target['serial_port']
                    break
        if target_id and serial_port:
            ret = flasher.flash(build=self.bin_path,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=False,
                                method='simple')
            self.assertEqual(ret, 0)
            self.assertEqual(verify_output_per_device(serial_port, 'help', 'echo'), False)
            second_binary = find_second_binary()
            self.assertIsNotNone(second_binary, 'Second binary not found')
            ret = flasher.flash(build=second_binary,
                                target_id=target_id, platform_name='K64F',
                                device_mapping_table=False, method='simple')
            self.assertEqual(ret, 0)
            if not verify_output_per_device(serial_port, 'help', 'echo'):
                self.assertEqual(
                    verify_output_per_device(serial_port, 'help', 'echo'), True)
            ret = flasher.flash(build=self.bin_path,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=False,
                                method='simple')
            self.assertEqual(ret, 0)
            self.assertEqual(verify_output_per_device(serial_port, 'help', 'echo'), False)

    @unittest.skipIf(check_two_binaries_exist() is False,
                     "binaries missing or too many binaries in test-folder")
    def test_verify_hw_flash_no_reset(self):
        mbeds = mbed_lstools.create()
        targets = mbeds.list_mbeds()
        flasher = Flash()
        resetter = Reset()
        target_id = None
        serial_port = None
        for target in targets:
            if target['platform_name'] == 'K64F':
                if 'serial_port' and 'target_id' in target:
                    target_id = target['target_id']
                    serial_port = target['serial_port']
                    break
        if target_id and serial_port:
            second_binary = find_second_binary()
            self.assertIsNotNone(second_binary, 'Second binary not found')
            ret = flasher.flash(build=second_binary,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=False,
                                method='simple')
            self.assertEqual(ret, 0)
            if not verify_output_per_device(serial_port, 'help', 'echo'):
                self.assertEqual(
                    verify_output_per_device(serial_port, 'help', 'echo'), True)

            ret = flasher.flash(build=second_binary,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=False,
                                method='simple',
                                no_reset=True)
            self.assertEqual(ret, 0)
            self.assertEqual(verify_output_per_device(serial_port, 'help', 'echo'), False)
            ret = resetter.reset(target_id=target_id, method='simple')
            self.assertEqual(ret, 0)
            if not verify_output_per_device(serial_port, 'help', 'echo'):
                self.assertEqual(
                    verify_output_per_device(serial_port, 'help', 'echo'), True)
            ret = flasher.flash(build=self.bin_path,
                                target_id=target_id,
                                platform_name='K64F',
                                device_mapping_table=False,
                                method='simple')
            self.assertEqual(ret, 0)
            self.assertEqual(verify_output_per_device(serial_port, 'help', 'echo'), False)

if __name__ == '__main__':
    unittest.main()
