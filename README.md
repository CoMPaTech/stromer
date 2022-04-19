**:warning::warning::warning:Read the [release notes](<https://github.com/CoMPaTech/stromer/releases>) before upgrading, in case there are BREAKING changes!:warning::warning::warning:**

# Stromer Custom Component for Home Assistant

 [![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/CoMPaTech/stomer/)
 [![CodeFactor](https://www.codefactor.io/repository/github/CoMPaTech/stromer/badge)](https://www.codefactor.io/repository/github/CoMPaTech/stromer)
 [![HASSfest](https://github.com/CoMPaTech/stromer/workflows/Validate%20with%20hassfest/badge.svg)](https://github.com/CoMPaTech/stromer/actions)
 [![Generic badge](https://img.shields.io/github/v/release/CoMPaTech/stromer)](https://github.com/CoMPaTech/stromer)

[![Open your Home Assistant instance and show your integrations.](https://my.home-assistant.io/badges/integrations.svg)](https://my.home-assistant.io/redirect/integrations/) 

## Configuration

Configure this integration the usual way, before starting you will need to retrieve your 

- [ ] Client ID
- [ ] Client Secret

For the API using a tool like MITM-proxy so you can intercept traffic between the app on your phone and the Stromer API.

Additional the setup flow will ask you for your username (i.e. e-mail address) and password for the Stromer API

## What it provides

In the current state it retrieves `bike`, `status` and `position` from the API every 10 minutes. It does not (yet?) provide any means of sending data to the API or your bike.

## State: ALPHA

Even though available does not mean it's stable yet, the HA part is solid but the class used to interact with the API is in need of improvement (e.g. better overall handling). This might also warrant having the class available as a module from pypi.

# Changelog

## APR 2022 [0.0.7]
  - Fix sensory updates
  - Potentially fix token expiration

## MAR 2022 [0.0.4]
  - Initial release
  - Creates a device for your bike in Home Assistant
  - Refreshed location and other information every 10 minutes

# What does it support?

- Location
  - It inherits zones, but you could also plot your location on a map
- Sensors
  - Like motor and battery temperature
- Binary Sensors
  - Light-status and Omni-lock status and theft status

# How to install?

- Use [HACS](https://hacs.xyz)
- Navigate to the `Integrations` page and use the three-dots icon on the top right to add a custom repository.
- Use the link to this page as the URL and select 'Integrations' as the category.
- Look for `Stromer` in `Integrations` and install it!

## How to add the integration to HA Core

For each bike (i.e. api-user) you will have to add it as an integration. Do note that you first have to retrieve your client ID and Secret using some tool like [mitmproxy](https://mitmproxy.org) to fetch these. If you don't know how to do this or what this implies; search from someone who can eloborate on this or do not use this integration. For more details and/or helpful users see [the Dutch Stromer forum](https://www.speedpedelecreview.com/forum/viewtopic.php?f=8&t=1445)

- [ ] In Home Assitant click on `Configuration`
- [ ] Click on `Integrations`
- [ ] Hit the `+` button in the right lower corner
- [ ] Search or browse for 'Stromer e-bike' and click it
- [ ] Enter your e-mail address, password and the client ID and Secret

# Frequently Asked Questions (FAQ)

## I don't like the name of the sensor or the icon

You can adjust these in `Configuration`, `Integration` -> `Entities` (e.g. `https://{Your HA address}/config/entities`)

Just click on the device and adjust accordingly!

Please note that you can also click the cogwheel right top corner to rename all entities of a device at once.

## It doesn't work

I'm on Discord and used to frequent the Dutch Stromer forum more often, but feel free to add a Bug through the Issues tab on [Github](https://github.com/CoMPaTech/stromer).

## Is it tested?

It works on my bike and Home Assistant installation :) Let me know if it works on yours!
