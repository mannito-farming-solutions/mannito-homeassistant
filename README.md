<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="custom_components/mannito/brand/dark_logo.png">
    <img alt="Mannito" src="custom_components/mannito/brand/logo.png" width="320">
  </picture>
</p>

# Mannito for Home Assistant

Connects a Mannito board (the grow controller) to Home Assistant through the Mannito cloud. You see the climate,
irrigation and plants of each grow area, switch lights, fans, sockets and valves, and change climate control and
irrigation settings. The board keeps regulating on its own. Home Assistant reads along and steps in only when you tell it
to.

[![Open this repository in HACS](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=mannito-farming-solutions&repository=mannito-homeassistant&category=integration)

## Requirements

- Home Assistant 2026.9 or newer
- A Mannito board set up in the Mannito cloud
- An API token for that board

### Create an API token

1. In the Mannito cloud, open the page of your board.
2. In the **API-Zugänge** (API access) card, select **Token erstellen** (create token). Only organization admins see
   this card.
3. Give the token a name, for example `Home Assistant`, and pick its rights:

   | Right | What it allows |
   | --- | --- |
   | Read | Always included. All readings and states. |
   | Control | Switch devices by hand, hand them back to automatic, open valves briefly, record measurements and tank entries. |
   | Configure | Turn a grow area on or off, climate control, irrigation, phase targets, grow cycle, board firmware. |

4. Copy the token. It starts with `mnt_` and is shown only once.

A token works for one board only. It does not work for other boards or for the Mannito MCP server. The card shows when
each token was last used, and you can revoke a token there at any time.

## Install

### HACS

1. Select the button above, or in HACS open the menu, choose **Custom repositories** and add
   `https://github.com/mannito-farming-solutions/mannito-homeassistant` with the type **Integration**.
2. Download **Mannito**. HACS offers the latest release; older releases are available under **Redownload**.
3. Restart Home Assistant.

### Manual

1. Download the latest release and copy `custom_components/mannito` to `config/custom_components/mannito` of your Home
   Assistant installation, for example with the File editor or Samba add-on.
2. Restart Home Assistant.

## Set up

[![Add the Mannito integration](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=mannito)

Go to **Settings > Devices & services > Add integration > Mannito** and enter:

| Field | Value |
| --- | --- |
| Cloud address | Address of the Mannito cloud, usually `https://mannito.de` |
| API token | The token of the board (`mnt_...`) |

The token is checked right away. Each board becomes its own entry.

To change the cloud address or the token later, use **Reconfigure** on the entry. A new token entered there replaces the
old one, and the integration revokes the old token in the cloud. If a token is revoked or expires, Home Assistant asks
for a new one.

## What you get

The board is a device. Each grow area, each plant and each bus module (for example the VPD module) is a device of its
own below the board.

**Board**

- Online status, last contact, pending changes
- Every sensor of the board and its bus modules, with the name it has in the cloud
- Outputs, with the Control right: the lamp as a light (dimmable on a 0-10 V channel), fans with speed in percent,
  sockets and relays as switches, solenoid valves as valves
- Per output a **... automatic** button, which hands it back to the board, and a **... manual operation** diagnostic
  sensor
- Board firmware as an update entity. Installing needs the Configure right.

**Grow area**

- Climate: temperature, humidity, VPD, leaf temperature, CO₂ (if measured), intake air, and their targets
- Status (OK, attention, problem, paused), day or night, emergency mode
- Grow phase, day of grow, day of phase, and a **Grow phases** calendar with past, current and planned phases
- Irrigation: phase P0 to P3, substrate moisture and its daily peak, dryback, shots and water per pot today, last and
  next shot, field capacity, tank volume and level
- Open problems of the plantings
- With the Configure right:
  - Targets of the current phase: day and night temperature, day and night VPD (or humidity), light intensity,
    circulation, CO₂
  - **Lights on** as a time. The whole day of the grow cycle moves with it.
  - **Field capacity from current reading**: press it after soaking the pot and letting it drain
  - The **Control** switch, and selects for climate control (Fuzzy, Fuzzy + PI, MPC), irrigation (off, schedule,
    dryback) and dryback strategy
  - Number entities for every dryback value and the daily limits

**Plant**

Every plant in a grow area is a device, for example `Green Poison #3`, with its height (last measurement, in cm), when
it was last measured, its age in days, variety and location (pot or section and site).

**Keeping in step with the cloud**

When you switch an output, Home Assistant shows the new state at once; the board confirms it a few seconds later.

New outputs, sensors, grow areas, plants and bus modules appear on their own. What you delete or hide in the cloud
disappears again, and so do harvested plants. If a new token has fewer rights, the integration removes the switches and
settings it may no longer use. No entities are left behind as unavailable.

## The Mannito card

The integration ships a dashboard card and loads it for you; there is no resource to add. One card shows one grow area:

| Tab | Content |
| --- | --- |
| Overview | Phase timeline with today marked, climate against targets, substrate moisture on a scale with peak, field capacity, P2 trigger and emergency line, shots and water today, tank level, quick tank entries, a button to run the valves for 10 s |
| Plants | Each plant with height, age and last measurement. Record a height or an observation, optionally as a problem. |
| Devices | The devices of the area with a slider (dimmable lamp, fans), a switch, or **Open 10 s** for valves. A **Manual** badge and an automatic button per device. |
| Settings | Phase targets, lights-on time, control, climate control, irrigation, dryback strategy and values, field capacity, grow cycle (postpone, next phase, confirm phase), board firmware |

To add it, edit a dashboard, choose **Add card > Mannito grow area** and pick the grow area. In YAML:

```yaml
type: custom:mannito-card
device: <device ID of the grow area>
show_all_devices: false # true also shows board outputs not assigned to this area
```

The card hides what the token may not do. Without the Configure right there is no Settings tab. Without the Control
right the devices are shown but cannot be switched.

The card and all entities follow the language of Home Assistant. English and German are included.

## Actions

| Action | What it does |
| --- | --- |
| `mannito.open_valve` | Opens one valve for 1 to 60 seconds. It closes on its own. |
| `mannito.run_valves` | Opens all valves of a grow area one after another, either for a number of seconds (to measure the flow) or for an amount in ml per pot (test shot). Each valve opens for 60 seconds at most. |
| `mannito.grow_cycle_action` | Confirms a phase, starts the next phase, postpones it, sets the lights-on time, or turns CO₂ dosing on or off. |
| `mannito.record_measurement` | Records a measurement of a plant: height (cm), stem thickness, leaf size, weight, look, color. |
| `mannito.record_note` | Records an observation on a plant, optionally as an open problem. |
| `mannito.tank_entry` | Logs a tank event: mixed fresh, topped up, drawn off, level checked (liters). |
| `mannito.tank_reading` | Records EC, pH or temperature measured in the tank. |

Measurements and observations take a plant. A grow area with a single planting works too; the entry then applies to all
of its plants. Records need the Control right.

### Examples

The entity IDs below assume a board named `Tent` with a grow area named `Flower`. Replace them with yours.

Get a notification when the grow area goes into emergency mode:

```yaml
automation:
  - alias: "Tent in emergency mode"
    triggers:
      - trigger: state
        entity_id: binary_sensor.tent_flower_emergency_mode
        to: "on"
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "The tent is in emergency mode. Please check it."
```

Get a notification when the tank runs low:

```yaml
automation:
  - alias: "Refill the tank"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.tent_flower_tank_volume
        below: 2
    actions:
      - action: notify.mobile_app_phone
        data:
          message: "Only {{ states('sensor.tent_flower_tank_volume') }} l left in the tank."
```

Record a plant height:

```yaml
action: mannito.record_measurement
data:
  target: <device ID of the plant>
  measurement: height
  value: 42
```

## How fresh the data is

Home Assistant polls the cloud every 30 seconds, right after you change a setting, and a few seconds after a switch
command once the board has confirmed it. The board reports its readings to the cloud about once a minute, so a value can
be up to 90 seconds old.

## Limits

- A manual command takes the output out of automatic control until you press **... automatic**. The cloud behaves the
  same way.
- Valves opened from Home Assistant close after 60 seconds at most, so a faulty automation cannot flood the tent.
- Bus modules such as the VPD module get no firmware from Home Assistant. Update them in the cloud or over USB.
- A grow cycle cannot be ended from Home Assistant. End it on the page of the grow area in the cloud.
- During the protected night of a flowering grow area the board refuses to turn the lights on.
- Without internet the board keeps working, but Home Assistant no longer sees it.

## Troubleshooting

| Message | Cause and fix |
| --- | --- |
| The token is unknown, revoked or expired. | Create a new token in the cloud and enter it through the repair notice. |
| The API token does not have the right for this. | Create a token with the Control or Configure right and enter it with **Reconfigure**. |
| The Mannito cloud rejected the request: ... | The cloud gives the reason, for example that the board is offline or a valve time is over 60 s. |
| `rate limited, retry in ... s` in the log | A token may make 120 requests per minute. Installations that share a token share that limit, so give each one its own token. |
| A board sensor shows Unknown | Its last reading is older than 15 minutes. The probe is unplugged or the bus module is offline. |
| All entities are unavailable | The board is offline or the cloud cannot be reached. Check the online status of the board. |

When you report a problem, please attach the **diagnostics** of the entry. They do not contain the token.

## Remove

Go to **Settings > Devices & services > Mannito**, open the menu of the entry and select **Delete**. The integration
then:

- removes the devices and entities of the board,
- revokes its token in the cloud. If the cloud cannot be reached, the log says so; revoke the token in the **API-Zugänge**
  card yourself,
- stops loading the Mannito card once the last board is gone. Dashboards that still hold the card show an error there
  until you remove it.

Finally, remove the integration in HACS, or for a manual install delete `custom_components/mannito`, and restart Home
Assistant. To add the board again later, create a new token; the old one is revoked.

## Development

Home Assistant does not run on Windows, so the tests run in a Linux container:

```bash
sh script/test.sh                 # all tests in Docker
sh script/test.sh tests/test_card.py
```

All texts live in `script/translations.py`. After changing them, run
`python script/translations.py custom_components/mannito` to write `strings.json` and the translations.

Every push runs hassfest, the HACS checks and the tests. A release is a tag `vX.Y.Z` that matches `version` in
`manifest.json`.

## License

MIT, see [LICENSE](LICENSE). The Mannito name and logo are not covered by this license.
