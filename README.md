# Aqua Illumination for Home Assistant (2026 Modernized)

A modernized, all-in-one Home Assistant integration for **Aqua Illumination (AI)** lights, updated for **HA 2026.3+** and **Python 3.14+**.

## 🤝 Credits & History
This integration is built on the incredible reverse-engineering work of the original community:
* **Original HA Component:** Initially written by **@zonyl** (based on work by **@mcclown**).
* **Core Library:** Powered by a vendored version of the **`AquaIPy`** module by **@chkuendig / @mcclown**.

*This module is in no way endorsed by AquaIllumination. Use it at your own risk. It likely invalidates your warranty.*

## 🚀 2026 Modernization Fixes
* **Vendored Library:** The `aquaipy` logic is now bundled inside `custom_components` to bypass Python 3.14 installation errors on Home Assistant Green/Yellow.
* **Entity Compliance:** Updated to use `ColorMode` and `SensorDeviceClass`, replacing legacy constants removed in HA 2026.3.
* **Relative Imports:** Re-architected to run locally without external pip dependencies.

A brief rundown of features/caveats:

* This component implements 3 different types of platforms, for each light. A schedule enabled switch, a light for each channel and a sensor for each channel.
* Each individual light channel appears as a different light entity.
* Each individual light channel also has a corresponding sensor entity, with the brightness level. This is useful for graphing the light channel levels.
* It is possible to turn off the "scheduled mode" for the light but if it isn't turned off, then light brightness changes will appear for a few seconds then change back to the normal schedule.
* Support is only for the HD range of lights. No support for earlier models yet.
* No support for setting more than one channel at once.
* No support for increasing the channels to over 100% (the HD range). Although a schedule can still set values over 100%.

## 🛠 Installation
1. Copy the `custom_components/aqua_illumination` folder to your `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Add via **Settings > Devices & Services > Add Integration**.


A sample configuration is shown below. This adds a light entity for each of the colour channels called <name>_<channel name>.

Add this to your configuration.yaml. OBS! If you have patent/child light, you can only ad the parent light, if you try to ad the child as well the integration won't work.

```YAML
aqua_illumination:
  - host: 192.168.1.100
    name: sump ai
  - host: 192.168.1.101
    name: dt ai
```
