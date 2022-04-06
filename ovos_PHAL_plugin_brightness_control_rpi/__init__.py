# Copyright 2021 Aditya Mehra <aix.m@outlook.com>.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

import subprocess

from ovos_utils.log import LOG
from mycroft_bus_client import Message
from ovos_plugin_manager.phal import PHALPlugin


class BrightnessControlRPIPlugin(PHALPlugin):
    def __init__(self, bus=None, config=None):
        super().__init__(bus=bus, name="ovos-PHAL-plugin-brightness-control-rpi", config=config)
        self.bus = bus
        self.device_interface = None
        self.ddcutil_detected_bus = None
        self.ddcutil_brightness_code = None

        self.discover()

        self.bus.on("phal.brightness.control.get",
                    self.query_current_brightness)
        self.bus.on("phal.brightness.control.set", self.set_brightness)

    # Discover the brightness control device interface (HDMI / DSI) on the Raspberry PI
    def discover(self):
        LOG.info("Discovering brightness control device interface")
        proc = subprocess.Popen(["/opt/vc/bin/vcgencmd",
                                "get_config", "display_default_lcd"], stdout=subprocess.PIPE)
        if proc.stdout.read().decode("utf-8").strip() == "1":
            self.device_interface = "DSI"
        else:
            self.device_interface = "HDMI"
        LOG.info("Brightness control device interface is {}".format(
            self.device_interface))

        if self.device_interface == "HDMI":
            proc_detect = subprocess.Popen(
                ["/usr/bin/ddcutil", "detect"], stdout=subprocess.PIPE)

            ddcutil_detected_output = proc_detect.stdout.read().decode("utf-8")
            if "I2C bus:" in ddcutil_detected_output:
                bus_code = ddcutil_detected_output.split(
                    "I2C bus: ")[1].strip().split("\n")[0]
                self.ddcutil_detected_bus = bus_code.split("-")[1].strip()
            else:
                ddcutil_detected_bus = None
                LOG.error("Display is not detected by DDCUTIL")

            if self.ddcutil_detected_bus:
                proc_fetch_vcp = subprocess.Popen(
                    ["/usr/bin/ddcutil", "getvcp", "known", "--bus", self.ddcutil_detected_bus], stdout=subprocess.PIPE)
                # check the vcp output for the Brightness string and get its VCP code
                for line in proc_fetch_vcp.stdout:
                    if "Brightness" in line.decode("utf-8"):
                        self.ddcutil_brightness_code = line.decode(
                            "utf-8").split(" ")[2].strip()

    # Get the current brightness level
    def get_brightness(self):
        LOG.info("Getting current brightness level")
        if self.device_interface == "HDMI":
            proc_fetch_vcp = subprocess.Popen(
                ["/usr/bin/ddcutil", "getvcp", self.ddcutil_brightness_code, "--bus", self.ddcutil_detected_bus], stdout=subprocess.PIPE)
            for line in proc_fetch_vcp.stdout:
                if "current value" in line.decode("utf-8"):
                    brightness_level = line.decode(
                        "utf-8").split("current value = ")[1].split(",")[0].strip()
                    return int(brightness_level)

        if self.device_interface == "DSI":
            proc_fetch_vcp = subprocess.Popen(
                ["cat", "/sys/class/backlight/rpi_backlight/actual_brightness"], stdout=subprocess.PIPE)
            for line in proc_fetch_vcp:
                brightness_level = line.decode("utf-8").strip()
                return int(brightness_level)

    def query_current_brightness(self, message):
        current_brightness = self.get_brightness()
        if self.device_interface == "HDMI":
            self.bus.emit(message.response(
                data={"brightness": current_brightness}))
        elif self.device_interface == "DSI":
            brightness_percentage = int((current_brightness / 255) * 100)
            self.bus.emit(message.response(
                data={"brightness": brightness_percentage}))

    # Set the brightness level
    def set_brightness(self, level):
        LOG.info("Setting brightness level")
        if self.device_interface == "HDMI":
            subprocess.Popen(["/usr/bin/ddcutil", "setvcp", self.ddcutil_brightness_code,
                             "--bus", self.ddcutil_detected_bus, "--value", str(level)])
        elif self.device_interface == "DSI":
            subprocess.Popen(
                ["echo", str(level), ">", "/sys/class/backlight/rpi_backlight/brightness"])

        self.bus.emit(
            Message("phal.brightness.control.changed", {"brightness": level}))
        LOG.info("Brightness level set to {}".format(level))

    def set_brightness_from_bus(self, message):
        LOG.info("Setting brightness level from bus")
        level = message.data["brightness"]
        if self.device_interface == "HDMI":
            if level < 0:
                level = 0
            elif level > 100:
                level = 100
            else:
                level = round(level / 10) * 10

            self.set_brightness(level)

        if self.device_interface == "DSI":
            if level < 0:
                level = 0
            elif level > 255:
                level = 255
            else:
                # round the level to the nearest 10
                level = round(level / 10) * 10

            self.set_brightness(level)
