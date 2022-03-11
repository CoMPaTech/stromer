# Stromer Custom Component for Home Assistant

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
