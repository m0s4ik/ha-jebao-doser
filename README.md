# Jebao Doser for Home Assistant — local, no cloud (HACS)

[![HACS](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://hacs.xyz/docs/faq/custom_repositories)
[![Release](https://img.shields.io/github/v/release/m0s4ik/ha-jebao-doser)](https://github.com/m0s4ik/ha-jebao-doser/releases)
[![Validate](https://github.com/m0s4ik/ha-jebao-doser/actions/workflows/validate.yml/badge.svg)](https://github.com/m0s4ik/ha-jebao-doser/actions/workflows/validate.yml)
[![Home Assistant](https://img.shields.io/badge/Home%20Assistant-2025.2%2B-41BDF5?logo=homeassistant)](https://www.home-assistant.io/)
[![License: MIT](https://img.shields.io/github/license/m0s4ik/ha-jebao-doser)](LICENSE)

Home Assistant custom integration for **Jebao WiFi aquarium dosing pumps**: Jebao **DOSER 3.4** (tested) and other Gizwits based Jebao dosers (**DOSER 3.1**, **DOSER 3.2**, **MD 4.4**). It talks to the pump over the **local network** (local push), with no Jebao/Gizwits cloud and no account.

See in Home Assistant when each head doses, the dosing schedule (times, ml per day, interval in days), the last dose of every head and the pump alarms, and use them in automations: for example a notification if a scheduled dose did not run, or if the pump goes offline.

Built on the **[jebao-doser](https://github.com/m0s4ik/jebao-doser)** Python library (also usable on its own, from the command line).

## Entities

Per head (`N` = 1…4):

| Entity | |
|---|---|
| `binary_sensor` Head N dosing | the head is running right now |
| `sensor` Head N schedule | dose times; attribute `doses` = list of `{time, amount}` |
| `sensor` Head N amount per day | ml per dosing day |
| `sensor` Head N interval | days between dosing days |
| `sensor` Head N last dose | timestamp of the last dose, attribute `duration` (s); kept across restarts |

Pump: local connection, power, open circuit alarm, Wi-Fi module fault. Translations: English, Italian.

Doses are pushed by the pump the moment they happen, whether scheduled, started from the app or from the buttons on the pump.

## Install

The [jebao-doser](https://github.com/m0s4ik/jebao-doser) library is bundled in `custom_components/jebao_doser/vendor/` until it is published on PyPI: nothing else to install.

**HACS**: *HACS → ⋮ → Custom repositories* → `https://github.com/m0s4ik/ha-jebao-doser`, category *Integration* → install → restart Home Assistant.

**Manual**: copy `custom_components/jebao_doser` into your `config/custom_components/` and restart.

Then *Settings → Devices & services → Add integration → **Jebao Doser (local)*** and enter the pump's IP address. Model and number of heads are read from the pump. Give the pump a fixed IP (DHCP reservation).

## Notes

- Read only for now: a write sends every writable byte at once and a mistake wipes the schedules, so manual dosing and schedule editing are not exposed yet.
- The vendor app keeps working: the pump stays connected to its cloud.
- Security: anyone who can reach the pump on TCP 12416 can control it. Keep it on an isolated IoT network and allow that port only from Home Assistant.

Not affiliated with Jebao or Gizwits. MIT license.
