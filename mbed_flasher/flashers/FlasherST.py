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

import os
import re
import subprocess
import logging
import tempfile


class FlasherST(object):
    """
    Class FlasherST

    Target on flashing STM boards.
    """
    name = "stm"
    exe = None
    supported_targets = ["NUCLEO_F401RE", "NUCLEO_F411RE", "NUCLEO_F429ZI", "NUCLEO_L476RG", "NUCLEO_F767ZI", "UBLOX_EVK_ODIN_W2"]
    logger = logging

    def __init__(self, exe=None):
        FlasherST.set_st-link_cli_exe(exe)
        self.logger = logging.getLogger('mbed-flasher')

    @staticmethod
    def get_supported_targets():
        """
        :return: supported ST types
        """
        global supported_targets
        return supported_targets

    @staticmethod
    def set_st-link_cli_exe(exe):
        """
        :param exe: ST-LINK_CLI program
        :return:
        """
        if not FlasherST.exe:
            for ospath in os.environ['PATH'].split(os.pathsep):
                if ospath.find('STM32 ST-LINK Utility') != -1:
                    # assume that ST-LINK_CLI.exe is in path
                    FlasherAtmelAt.exe = "ST-LINK_CLI.exe"
                    break
            else:
                FlasherST.exe = exe

        #FlasherST.logger.debug("atprogram location: %s", FlasherST.exe)

    @staticmethod
    def get_available_devices():
        """
        :return: list of available devices
        """
        if not FlasherST.exe:
            return []
        FlasherST.set_st-link_cli_exe(FlasherST.exe)
        cmd = FlasherST.exe + " -List"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, _ = proc.communicate()
        connected_devices = []
        if proc.returncode == 0:
            lines = stdout.splitlines()
            for line in lines:
                if line.find("SN: ") != -1:
                    connected_devices.append({"target_id_usb_id":line.split("SN:")[1]})
        FlasherAtmelAt.logger.debug(
            "Connected atprogrammer supported devices: %s", connected_devices)
        return connected_devices

    # actual flash procedure
    def flash(self, source, target):
        """flash device
        :param sn: device serial number to be flashed
        :param binary: binary file to be flash
        :return: 0 when flashing success
        """
        
        cmd = self.exe \
              + " -c SN="\
              + target['target_id_usb_id']\
              + " -P "\
              + source\
              + "0x08000000 -V"
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = proc.communicate()
        FlasherST.logger.debug(stdout)
        FlasherST.logger.debug(stderr)
        return proc.returncode


    @staticmethod
    def find(line, lookup):
        """find with regexp
        :param line:
        :param lookup:
        :return:
        """
        match = re.search(lookup, line)
        if match:
            if match.group(1):
                return match.group(1)
        return False
