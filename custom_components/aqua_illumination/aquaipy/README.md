# Aqua Illumination for Home Assistant (2026 Modernized)

This is a modernized fork of the original `aqua_illumination` integration. It has been updated to support **Home Assistant 2026.3+** and **Python 3.14+**.

## 🚀 Improvements in this Fork
* **Vendored Library:** The `aquaipy` library is now included directly in the integration to prevent Python version installation errors on Home Assistant Green.
* **Modern Entity Support:** Updated to use `ColorMode` and `SensorDeviceClass` to comply with 2026 structural requirements.
* **Relative Imports:** Re-architected to run as a standalone custom component without external pip dependencies.

## 🤝 Credits
* **Original Integration:** Based on the work by **@zonyl** (GitHub: [zonyl/aqua_illumination](https://github.com/zonyl/aqua_illumination)).
* **Library Foundation:** Uses the `aquaipy` library originally developed by **@chkuendig** (and/or other contributors).

## 🛠 Installation
1. Copy the `custom_components/aqua_illumination` folder to your HA `/config/custom_components/` directory.
2. Restart Home Assistant.
3. Add the integration via **Settings > Devices & Services**.
