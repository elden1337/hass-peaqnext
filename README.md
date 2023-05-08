<img src="https://raw.githubusercontent.com/creativecommons/cc-assets/main/license_badges/big/by_nc_nd.svg" width="90">

[![Peaqnext_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaqnext/total)](https://github.com/elden1337/hass-peaqnext) 
[![hass-peaqnext_downloads](https://img.shields.io/github/downloads/elden1337/hass-peaqnext/latest/total)](https://github.com/elden1337/hass-peaqnext)
[![Paypal](https://img.shields.io/badge/Sponsor-PayPal-orange.svg)](https://www.paypal.com/donate/?hosted_button_id=GLGW8QAAQC2FG)
[![BuyMeACoffee](https://img.shields.io/badge/Sponsor-BuyMeACoffee-orange.svg)](https://buymeacoffee.com/elden)

# Peaqnext utility sensors


<img src="https://raw.githubusercontent.com/elden1337/hass-peaq/main/assets/icon.png" width="125">

## Installation
Preferred if you have HACS installed is to search for Peaqnext there.

Otherwise you may:
- Copy `custom_components/peaqnext` folder to `<config_dir>/custom_components/peaqnext/`
- Restart Home assistant
- Go to Configuration > Devices & Services > Add integration

### Config setup:

Peaqnext lets you set up sensors from config flow by giving a name, total consumption for a cycle, consumption-pattern (see below for examples) and duration of a cycle. 
You may also specify hours where the suggestion may not begin, or end. This can be handy for say washing machines that you may not wish to be done in the middle of the night.
When this is done, the sensors will appear and give you a status on the next best cycle to run the appliance with start-time, end-time and the total expected cost in parenthesis. 
The state of the sensor will be cheapest cycle within 12hrs from now. It may be the cheapest overall, or may not. If you wish to see all the cycles you can open the sensor to reveal the attributes.

This integration requires [Nordpool](https://github.com/custom-components/nordpool).

#### Consumption-types:

* **Flat consumption** - the consumption is static througout the cycle. _Example is tumble dryer_
* **Peak in beginning** - the consumption peaks in the beginning of the cycle.
* **Peak in end** - the consumption peaks towards the end of the cycle. _Example is washing machine_
* **Peak in middle** - the consumption peaks in the middle of the cycle.
* **Peak in beginning and end** - the consumption peaks in the beginning and end of the cycle.
