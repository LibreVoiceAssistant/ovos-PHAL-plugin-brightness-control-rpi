# DEPRECATED - OVOS PHAL BRIGHTNESS CONTROL PLUGIN FOR RPI


This repository is no longer maintained by OpenVoiceOS, use https://github.com/OpenVoiceOS/ovos-gui-plugin-shell-companion instead

___________________________
This plugin provides a brightness control interface for the Raspberry PI, it supports DSI and **HDMI screens

** HDMI Screens: Screens supported and detected by DDCUTILS only

# Requirements
- Requires ddcutils for HDMI: https://github.com/rockowitz/ddcutil (install location: "/usr/bin/ddcutil")
- Requires vcgencmd for DSI: https://github.com/raspberrypi/userland (install location: "/opt/vc/bin/vcgencmd")

# Install

`pip install ovos-PHAL-plugin-brightness-control-rpi`

# Event Details:

##### Brightness GET and Brightness SET

Plugin provides methods to set and get brightness based on the detected screen type method.

```python
        self.bus.on("phal.brightness.control.get", self.query_current_brightness)
        self.bus.on("phal.brightness.control.set", self.set_brightness_from_bus)
```

##### Auto Dim and Nightmode

Plugin provides auto dim and nightmode activation and deactivation.

```python
        self.bus.on("speaker.extension.display.auto.dim.changed", self.is_auto_dim_enabled)
        self.bus.on("speaker.extension.display.auto.nightmode.changed", self.is_auto_night_mode_enabled)
```
