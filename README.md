# Stromer Custom Component for Home Assistant

> Looking for Homey instead of Home Assistant and/or if you need more detailed information on how to get your credentials, @wdool created [Stromer for Homey](https://github.com/wdool/stromer_homey) using information in this repo but has extensive information on how to connect. Very nice that Homey users can now also track and automate their favorite bike(s).

**:warning::warning::warning: Read the [release notes](https://github.com/CoMPaTech/stromer/releases) before upgrading, in case there are BREAKING changes! :warning::warning::warning:**

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/CoMPaTech/stromer/)
[![CodeFactor](https://www.codefactor.io/repository/github/CoMPaTech/stromer/badge)](https://www.codefactor.io/repository/github/CoMPaTech/stromer)
[![HASSfest](https://github.com/CoMPaTech/stromer/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/CoMPaTech/stromer/actions)
[![Generic badge](https://img.shields.io/github/v/release/CoMPaTech/stromer)](https://github.com/CoMPaTech/stromer)

[![CodeRabbit.ai is Awesome](https://img.shields.io/badge/AI-orange?label=CodeRabbit&color=orange&link=https%3A%2F%2Fcoderabbit.ai)](https://coderabbit.ai)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)

## Requirements

Home Assistant 2026.10 or newer. If you are on an older Home Assistant version, use [v0.4.3](https://github.com/CoMPaTech/stromer/releases/tag/v0.4.3) or earlier.

A Stromer bike that has "Mobile phone network" connectivity. This *excludes* the standard ST1 without the "Upgrade" (see [Stromer Connectivity](https://www.stromerbike.com/en/swiss-technology-connectivity-omni)). ST2, ST3, ST5 and ST7 come standard with the required connectivity.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CoMPaTech&repository=stromer&category=integrations)

See [How to install?](#how-to-install) below if you prefer to add the repository manually.

## Configuration

The setup flow asks for:

- Your Stromer username (i.e. the e-mail address you use in the Stromer app)
- Your Stromer password
- The **Client ID** of the Stromer app
- The **Client Secret** of the Stromer app, *optional*: only needed for older (APIv3) client IDs, leave it empty if your client ID starts with `4P`

### Why do I need a Client ID (and MITM)?

Stromer does not offer a public API or a way to request API credentials. The official Stromer app logs in using its own (app-specific) Client ID, and this integration has to present that same Client ID to talk to the Stromer API. It is not shown anywhere in the app or on the Stromer website.

The way to retrieve it is to intercept the traffic between the Stromer app on your phone and the Stromer API using a man-in-the-middle (MITM) proxy such as [mitmproxy](https://mitmproxy.org) and read the Client ID (and Secret, if present) from the app's login/authorization requests. If you don't know how to do this or what it implies, ask someone who can help you with it or do not use this integration. [Stromer for Homey](https://github.com/wdool/stromer_homey) has a detailed walkthrough, and helpful users can be found on [the Dutch Stromer forum](https://www.speedpedelecreview.com/forum/viewtopic.php?f=8&t=1445).

## What it provides

In the current state it retrieves `bike`, `status` and `position` from the API every 10 minutes.

There is an early implementation on toggling data on your bike, `light` and `lock` can be adjusted.
Do note that the switches do not immediately reflect the status (i.e. they will when you toggle them, but switch back quickly).
After your 'switch' command we do request an API update to check on the status, pending that update the switch might toggle back-n-forth some time.
Depending on your bike type the `Light` switch will switch on/off or between 'dim and bright'.

As with the `switch` implementation a `button` is added to reset your trip_data.

Multi-bike support (see #81 / #82 for details). The config-flow will detect if you have one or multiple bikes. If you have one, you can only select it (obviously). When multiple bikes are in the same account, repeat the 'add integration' for each bike, selecting the other bike(s) on each iteration.

## If you want more frequent updates

Basically you'll have to trigger (through automations) the updates yourself. But it's the correct way to learn Home Assistant and the method shown below also saves some API calls to Stromer. Basically this will determine if the bike is **unlocked** and if so start frequent updates. The example will also show you how to add a button to immediately start the more frequent updates. And yes, I'm aware we can make blueprints of this, but I'll leave that for now until we have a broader user base and properly tested integration.

- [![Open your helpers.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)
- Create a `switch` (i.e. input-boolean) named `Stromer Frequent Updates` (i.e. becoming `input_boolean.stromer_frequent_updates`. Feel free to name it otherwise, but this is what will be referred to below.

- [![Open your automations.](https://my.home-assistant.io/badges/automations.svg)](https://my.home-assistant.io/redirect/automations/)
- Create a new automation, click on the right-top three dots and select 'Edit as YAML'. Don't worry, most of it you will be able to use the visual editor for, it's just that pasting is much easier this way. Do note that you'll have to change the `stromer` part of the bike (or after pasting, select the three dots, go back to visual editor and pick the correct entity).

```automation.yml
alias: Stromer cancel updates when locked
description: ''
triggers:
  - trigger: state
    entity_id: binary_sensor.stromer_bike_lock
    to: 'on'
  - trigger: template
    value_template: >-
      {{ has_value('sensor.stromer_last_status_push') and now().timestamp() - as_timestamp(states('sensor.stromer_last_status_push')) > 600 }}
conditions: []
actions:
  - action: homeassistant.turn_off
    data: {}
    target:
      entity_id: input_boolean.stromer_frequent_updates
mode: single
```

- Create another automation, same process as above

```automation.yml
alias: Stromer start updates when unlocked
description: ''
triggers:
  - trigger: state
    entity_id: binary_sensor.stromer_bike_lock
    to: 'off'
  - trigger: template
    value_template: >-
      {{ has_value('sensor.stromer_last_status_push') and now().timestamp() - as_timestamp(states('sensor.stromer_last_status_push')) > 600 }}
conditions: []
actions:
  - action: homeassistant.turn_on
    data: {}
    target:
      entity_id: input_boolean.stromer_frequent_updates
mode: single
```

- And the final one, actually calling the updates (example every 30 seconds). We'll only point to bike speed, but it will update the other sensors

```automation.yml
alias: Stromer update sensors
description: ''
triggers:
  - trigger: time_pattern
    seconds: /30
conditions:
  - condition: state
    entity_id: input_boolean.stromer_frequent_updates
    state: 'on'
actions:
  - action: homeassistant.update_entity
    data: {}
    target:
      entity_id: sensor.stromer_bike_speed
mode: single
```

- Final step is adding a button to your dashboard if you want to trigger updates right now. Do note that your bike must be **unlocked** before triggering, otherwise it will 'cancel itself' :) In a dashboard, click the three buttons right top, and add a `button`-card, through `view code editor` paste, switch back to visual editor and customize the below to your taste. Again pointing at bike speed but it will refresh if the bike is unlocked and trigger the updates helper.

```lovelace.yml
show_name: true
show_icon: true
type: button
tap_action:
  action: perform-action
  perform_action: homeassistant.update_entity
  data: {}
  target:
    entity_id: sensor.stromer_bike_speed
entity: ''
hold_action:
  action: none
name: Start Stromer updates
icon: mdi:bike
show_state: false
```

## State: BETA

Even though available does not mean it's stable yet, the HA part is solid but the class used to interact with the API is in need of improvement (e.g. better overall handling). This might also warrant having the class available as a module from pypi.

## What does it support?

- Location
  - It inherits zones, but you could also plot your location on a map
- Sensors
  - Like motor and battery temperature
  - Two speed sensors: `Bike speed` (reported by the bike) and `GPS speed` (derived from the position, so it may show small values while parked)
- Binary Sensors
  - Light-status and Omni-lock status and theft status

## How to install?

- Use [HACS](https://hacs.xyz)
- Navigate to the `Integrations` page and use the three-dots icon on the top right to add a custom repository.
- Use the link to this page as the URL and select 'Integrations' as the category.
- Look for `Stromer` in `Integrations` and install it!

### How to add the integration to HA Core

For each bike you will have to add it as an integration. Do note that you first have to retrieve your Client ID (see [Why do I need a Client ID (and MITM)?](#why-do-i-need-a-client-id-and-mitm)).

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=stromer)

- [ ] In Home Assistant go to `Settings` -> `Devices & services`
- [ ] Hit the `Add integration` button in the right lower corner
- [ ] Search or browse for 'Stromer e-bike' and click it
- [ ] Enter your e-mail address, password and the Client ID (and Secret, if needed)

### Changing your credentials

If you change your Stromer e-mail address, password or client ID/Secret, use `Reconfigure` from the three-dots menu of the integration entry. If the Stromer API rejects your credentials, Home Assistant will ask you to re-authenticate.

## Frequently Asked Questions (FAQ)

### I don't like the name of the sensor or the icon

You can adjust these in `Settings` -> `Devices & services` -> `Entities` (e.g. `https://{Your HA address}/config/entities`)

Just click on the device and adjust accordingly!

Please note that you can also click the cogwheel right top corner to rename all entities of a device at once.

### It doesn't work

I'm on Discord and used to frequent the Dutch Stromer forum more often, but feel free to add a Bug through the Issues tab on [Github](https://github.com/CoMPaTech/stromer).

### Is it tested?

It works on my bike and Home Assistant installation :) Let me know if it works on yours!

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-black.svg)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)

And [Home-Assistant Hassfest](https://github.com/home-assistant/actions) and [HACS validation](https://github.com/hacs/action)
