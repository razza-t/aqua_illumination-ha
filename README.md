# 🌊 Aqua Illumination for Home Assistant (2026 Modernized)

A modernized, high-performance Home Assistant integration for **Aqua Illumination (AI)** lights. Re-engineered to support **HA 2026.3+** and **Python 3.14+**.



## 🛠 2026 Modernization Fixes
* **UI-Based Configuration:** Full support for **Config Flow**. No more editing `configuration.yaml`—add your lights directly through the Home Assistant interface.
* **Zero Dependency Errors:** The `aquaipy` logic is now "vendored" (bundled) inside the component, fixing installation failures on Home Assistant Green, Yellow, and Raspberry Pi OS.
* **Native Entity Grouping:** All color channels (Deep Blue, UV, Cool White, etc.) are automatically grouped under a single Device for a cleaner, more organized UI.
* **Modern Entity Compliance:** Updated with 2026 `ColorMode` and `SensorDeviceClass` standards to ensure long-term stability.

---

## ⚠️ Important: Parent/Child Setup
If you have multiple AI lights paired together in a **Parent/Child (Master/Slave)** configuration:
* **ONLY add the IP address of the Parent light.**
* The Parent light manages the communication for all paired children. 
* **Do NOT** attempt to add the IP addresses of Child lights individually; the integration will fail to connect or create duplicate entities.

---

## ✨ Features
* **Individual Channel Control:** Every LED color channel (Deep Blue, Royal Blue, Cool White, UV, etc.) appears as a dimmable light entity.
* **Brightness Sensors:** Real-time percentage sensors for every channel—perfect for History Graphs and Energy dashboards.
* **Scheduled Mode Switch:** A dedicated toggle to switch between the light's **Internal AI Schedule** and **Manual HA Control**.
* **Diagnostics:** Track Firmware versions and connection stability directly from the device page.

---

## 🚀 Installation

### Option 1: HACS (Recommended)
1.  Open **HACS** in your Home Assistant sidebar.
2.  Click the **three dots** (top-right) and select **Custom repositories**.
3.  Paste your GitHub URL: `https://github.com/YOUR_USERNAME/YOUR_REPO_NAME`
4.  Select **Integration** as the category and click **Add**.
5.  Find **Aqua Illumination (2026 Fix)** and click **Download**.
6.  **Restart Home Assistant.**

### Option 2: Manual Installation
1.  Download the `aqua_illumination` folder from this repository.
2.  Copy it into your Home Assistant `/config/custom_components/` directory.
3.  **Restart Home Assistant.**

---

## ⚙️ How to Setup
1.  Navigate to **Settings > Devices & Services**.
2.  Click **+ Add Integration** in the bottom right.
3.  Search for **Aqua Illumination**.
4.  Enter the **IP Address** of your **Parent** light.
5.  Give it a name (e.g., "Main Reef") and click **Submit**.

---

## 📉 Known Caveats
* **Compatibility:** Tested only with Hydra 26HD. Likely also works with Prime HD, Hydra 26HD, 52HD, 32HD, 64HD.
* **Network Latency:** Since commands are sent per-channel, adjusting multiple sliders simultaneously may result in a very slight stagger.
* **HD Overdrive:** This integration supports 0-100% brightness. Values above 100% (the "HD" boost) are currently best managed via the internal AI schedule.

---

## 📜 Credits
* **Original Integration:** Created by **@zonyl** and **@mcclown**.
* **Core API Library:** Powered by **`AquaIPy`** by **@chkuendig**.
* **2026 Modernization:** Updated for modern HA standards by the community.

*Disclaimer: This module is not officially endorsed by or affiliated with AquaIllumination. Use at your own risk.*
