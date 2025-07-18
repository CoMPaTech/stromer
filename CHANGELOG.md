# Stromer Custom Component Changelog

## Changelog

### JUL 2025 [0.4.2]

- Attempt to fix getting initial code (due to DNS issues) #139

### SEP 2024 [0.4.1]

- Onboarding devices fix

### AUG 2024 [0.4.0]

- Add multibike support
- Single and Multi-bike (proper) selection using config_flow setup
- Improve support for migration from <= v0.3.x (single bike in multi-bike)
- Remove stale VIA_DEVICE (i.e. the 'Connected to' when viewing the device page)
- Below-the-surface each bike is now created with a unique id `stromerbike-xxxxx`
- Improve timeout and aiohttp connection handling [tnx @dbrgn]
- Timestamp/TZ improvements [tnx @dbrgn]

### JUL 2024 [0.3.3]

- Added Portuguese Language [tnx @ViPeR5000]
- Other smaller fixes and contributes [tnx @L2v@p]
  
### JUN 2024 [0.3.2]

- Added trip_reset button
- Released v0.3(.2) as new stable version

### JAN 2024

- Added to HACS default repository (yay!)

### DEC 2023 [0.3.1 (alpha/beta]

- Released version 0.3

### DEC 2023 [0.3.0 (alpha/beta)]

- Introduce Lock and Light switches
- Fix UnitOf[X] for future HA compatibility (e.g. TEMP_CELSIUS => UnitOfTemperature.CELSIUS)
- Improve naming through translation_keys (as also introduced way back)

### DEC 2023 [0.2.9]

- Fix energy measurement to total/total_increasing

### NOV 2023 [0.2.8]

- Code cleanup and quality improvements

### NOV 2023 [0.2.7]

- Fix to appropriate `device_class` from 0.2.5

### NOV 2023 [0.2.6]

- Fix API recall (reverted maintenance approach from 0.2.5) tnx to @simonwolf83

### NOV 2023 [0.2.5]

- Fix unit from W to Wh (thanks @Tinus78) via #46

## OCT 2023 [0.2.4]

- Improve quality

### SEP 2023 [0.2.3]

- Conform to hacs and HA files
- Adding HACS validation

### SEP 2023 [0.2.2]

- Fix location (i.e. `device_tracker`) reporting

### AUG 2023 [0.2.1]

- Quickfix sensors lost due to some data not available

### MAR 2023 [0.2.0]

- Fix 2023.3 compliance

### APR 2022 [0.1.0]

- Include last update sensors

### APR 2022 [0.0.8]

- v4 API support
- Data handling and reconnection

### APR 2022 [0.0.7]

- Fix sensory updates
- Potentially fix token expiration

### MAR 2022 [0.0.4]

- Initial release
- Creates a device for your bike in Home Assistant
- Refreshed location and other information every 10 minutes
