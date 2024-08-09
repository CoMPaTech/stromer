# Stromer Custom Component for Home Assistant

**:warning::warning::warning:Read the [release notes](https://github.com/CoMPaTech/stromer/releases) before upgrading, in case there are BREAKING changes!:warning::warning::warning:**

[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/CoMPaTech/stomer/)
[![CodeFactor](https://www.codefactor.io/repository/github/CoMPaTech/stromer/badge)](https://www.codefactor.io/repository/github/CoMPaTech/stromer)
[![HASSfest](https://github.com/CoMPaTech/stromer/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/CoMPaTech/stromer/actions)
[![Generic badge](https://img.shields.io/github/v/release/CoMPaTech/stromer)](https://github.com/CoMPaTech/stromer)

[![CodeRabbit.ai is Awesome](https://img.shields.io/badge/AI-orange?label=CodeRabbit&color=orange&link=https%3A%2F%2Fcoderabbit.ai)](https://coderabbit.ai)
[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)
[![Technical Debt](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=sqale_index)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)
[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=CoMPaTech_stromer&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)

## Requirements

A Stromer bike that has "Mobile phone network" connectivity. This *excludes* the standard ST1 without the "Upgrade" (see [Stromer Connectivity](https://www.stromerbike.com/en/swiss-technology-connectivity-omni)). ST2, ST3, ST5 and ST7 come standard with the required connectivity.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=CoMPaTech&repository=stromer&category=integrations)

## Configuration

Configure this integration the usual way, before starting you will need to retrieve your

- [ ] Client ID
- [x] Client Secret `*) only if you already have this or require APIv3`

For the API using a tool like MITM-proxy so you can intercept traffic between the app on your phone and the Stromer API.

Additional the setup flow will ask you for your username (i.e. e-mail address) and password for the Stromer API and the secrets retrieved through MITM-proxy.

## What it provides

In the current state it retrieves `bike`, `status` and `position` from the API every 10 minutes.

**BETA** There is an early implementation on toggling data on your bike, `light` and `lock` can be adjusted.
Do note that the switches do not immediately reflect the status (i.e. they will when you toggle them, but switch back quickly).
After your 'switch' command we do request an API update to check on the status, pending that update the switch might toggle back-n-forth some time.
The light-switch is called 'Light mode' as depending on your bike type it will switch on/off or between 'dim and bright'.

**BETA** As with the `switch` implementation a `button` is added to reset your trip_data.

**ALPHA** Multi-bike support (see #81 / #82 for details and progress). Currently seems working with a few glitches (v0.4.0a2), hoping to provide more stability (and migration from v0.3) (v0.4.0a4 and upwards). Basically the config-flow will now detect if you have one or multiple bikes. If you have one, you can only select it (obviously). When multiple bikes are in the same account repeat the 'add integration' for each bike, selecting the other bike(s) on each iteration.

## If you want more frequent updates

Basically you'll have to trigger (through automations) the updates yourself. But it's the correct way to learn Home Assistant and the method shown below also saves some API calls to Stromer. Basically this will determine if the bike is **unlocked** and if so start frequent updates. The example will also show you how to add a button to immediately start the more frequent updates. And yes, I'm aware we can make blueprints of this, but I'll leave that for now until we have a broader user base and properly tested integration.

- [![Open your helpers.](https://my.home-assistant.io/badges/helpers.svg)](https://my.home-assistant.io/redirect/helpers/)
- Create a `switch` (i.e. input-boolean) named `Stromer Frequent Updates` (i.e. becoming `input_boolean.stromer_frequent_updates`. Feel free to name it otherwise, but this is what will be referred to below.

- [![Open your automations.](https://my.home-assistant.io/badges/automations.svg)](https://my.home-assistant.io/redirect/automations/)
- Create a new automation, click on the right-top three dots and select 'Edit as YAML'. Don't worry, most of it you will be able to use the visual editor for, it's just that pasting is much easier this way. Do note that you'll have to change the `stromer` part of the bike (or after pasting, select the three dots, go back to visual editor and pick the correct entity).

```automation.yml
alias: Stromer cancel updates when locked
description: ''
trigger:
  - platform: state
    entity_id: binary_sensor.stromer_bike_lock
    to: 'on'
  - platform: template
    value_template: >-
      {{ now().timestamp() - as_timestamp(states.sensor.stromer_last_status_push.state) > 600 }}
condition: []
action:
  - service: homeassistant.turn_off
    data: {}
    target:
      entity_id: input_boolean.stromer_frequent_updates
mode: single
```

- Create another automation, same process as above

```automation.yml
alias: Stromer start updates when unlocked
description: ''
trigger:
  - platform: state
    entity_id: binary_sensor.stromer_bike_lock
    to: 'off'
  - platform: template
    value_template: >-
      {{ now().timestamp() - as_timestamp(states.sensor.stromer_last_status_push.state) > 600 }}
condition: []
action:
  - service: homeassistant.turn_on
    data: {}
    target:
      entity_id: input_boolean.stromer_frequent_updates
mode: single
```

- And the final one, actually calling the updates (example every 30 seconds). We'll only point to speed, but it will update the other sensors

```automation.yml
alias: Stromer update sensors
description: ''
trigger:
  - platform: time_pattern
    seconds: /30
condition:
  - condition: state
    entity_id: input_boolean.stromer_frequent_updates
    state: 'on'
action:
  - service: homeassistant.update_entity
    data: {}
    target:
      entity_id: sensor.stromer_speed
mode: single
```

- Final step is adding a button to your dashboard if you want to trigger updates right now. Do note that your bike must be **unlocked** before triggering, otherwise it will 'cancel itself' :) In a dashboard, click the three buttons right top, and add a `button`-card, through `view code editor` paste, switch back to visual editor and customize the below to your taste. Again pointing at speed but it will refresh if the bike is unlocked and trigger the updates helper.

```lovelace.yml
show_name: true
show_icon: true
type: button
tap_action:
  action: call-service
  service: homeassistant.update_entity
  service_data: {}
  target:
    entity_id: sensor.stromer_speed
entity: ''
hold_action:
  action: none
name: Start Stromer updates
icon: mdi:bike
show_state: false
```

## State: ALPHA

Even though available does not mean it's stable yet, the HA part is solid but the class used to interact with the API is in need of improvement (e.g. better overall handling). This might also warrant having the class available as a module from pypi.

## What does it support?

- Location
  - It inherits zones, but you could also plot your location on a map
- Sensors
  - Like motor and battery temperature
- Binary Sensors
  - Light-status and Omni-lock status and theft status

## How to install?

- Use [HACS](https://hacs.xyz)
- Navigate to the `Integrations` page and use the three-dots icon on the top right to add a custom repository.
- Use the link to this page as the URL and select 'Integrations' as the category.
- Look for `Stromer` in `Integrations` and install it!

### How to add the integration to HA Core

For each bike (i.e. api-user) you will have to add it as an integration. Do note that you first have to retrieve your client ID and Secret using some tool like [mitmproxy](https://mitmproxy.org) to fetch these. If you don't know how to do this or what this implies; search from someone who can eloborate on this or do not use this integration. For more details and/or helpful users see [the Dutch Stromer forum](https://www.speedpedelecreview.com/forum/viewtopic.php?f=8&t=1445)

- [ ] In Home Assistant click on `Configuration`
- [ ] Click on `Integrations`
- [ ] Hit the `+` button in the right lower corner
- [ ] Search or browse for 'Stromer e-bike' and click it
- [ ] Enter your e-mail address, password and the client ID and Secret

## Frequently Asked Questions (FAQ)

### I don't like the name of the sensor or the icon

You can adjust these in `Configuration`, `Integration` -> `Entities` (e.g. `https://{Your HA address}/config/entities`)

Just click on the device and adjust accordingly!

Please note that you can also click the cogwheel right top corner to rename all entities of a device at once.

### It doesn't work

I'm on Discord and used to frequent the Dutch Stromer forum more often, but feel free to add a Bug through the Issues tab on [Github](https://github.com/CoMPaTech/stromer).

### Is it tested?

It works on my bike and Home Assistant installation :) Let me know if it works on yours!

[![SonarCloud](https://sonarcloud.io/images/project_badges/sonarcloud-black.svg)](https://sonarcloud.io/summary/new_code?id=CoMPaTech_stromer)

And [Home-Assistant Hassfest](https://github.com/home-assistant/actions) and [HACS validation](https://github.com/hacs/action)
