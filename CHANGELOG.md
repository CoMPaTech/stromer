# Stromer Custom Component Changelog

## Changelog

### JAN 2024 [no release, just an update]

- Added to HACS default repository (yay!)

### DEC 2023 [0.3.1 (alpha/beta]

- Released version 0.3

### DEC 2023 [0.3.0 (alpha/beta]

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
