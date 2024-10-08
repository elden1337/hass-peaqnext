> 2024-10-08
> 
> Dear Peaquser,
> 
> After three years of open source in these projects, I am about to set sail on the next leg of my journey.
> I will soon start a job where I will work with adjacent technology, and thus will seize to update the repos with new features.
> This is to not be questioned regarding IP going forward.
> 
> For the time being I want to let the codebases stay online, and will accept pull requests and occasionally do patch updates and bug fixes to > keep the solutions running.
> However, I will not take part in general feature discussions any longer, starting from 2024-11-01.
> 
> If you wish you may fork the projects and create features that you send me as pull requests. That way we can keep the flow going without > my direct interference in the inventions.
> For any usage not covered by the general download by hacs, look towards the license on the repos for guidance. Here's a snapshot of what > the licenses on my code requires: https://creativecommons.org/licenses/by-nc-nd/4.0/deed.en
> 
> Thanks for all engagement and happy to have helped a bunch of people with this spare time invention of mine. 
> //Magnus

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

This integration requires [Nordpool](https://github.com/custom-components/nordpool) or [EnergiDataService](https://github.com/MTrab/energidataservice)

### Setup:

In the configflow you are prompted with the following inputs:

- `Name` - The name of the sensor you are creating
- `Consumption-type` - The type of consumption pattern your appliance will run with. See examples below
- `Custom consumption pattern` - (optional) Your own custom consumption pattern if . Inputs must be numbers separated by a comma (,). If decimals, use a point (.) separator.
- `Total consumption in kWh` - Add the expected consumption of a cycle. 
- `Total duration in minutes` - Total duration of a cycle.
- `Nonhours start` - (optional) Check the hours in which your appliance cannot start
- `Nonhours end` - (optional) Check the hours in which your appliance cannot finish
- `Closest cheap hour` - (optional, defaults to 12h) Change the suggested "cheapest price within x hours" as sensor-state. Set to 48 or more to ignore it.
- `Deduct price` - (optional, defaults to 0) Should you need to deduct a fixed rate from the hourly price calculations, then add it here.
- `Update by` - Choose if you want the sensor update every minute or in the beginning of every hour.
- `Calculate by` - Choose if you want the sensor to calculate based on start-time or end-time.

#### Consumption-types:

* **Flat consumption** - the consumption is static througout the cycle. _Example is tumble dryer_
* **Peak in beginning** - the consumption peaks in the beginning of the cycle.
* **Peak in end** - the consumption peaks towards the end of the cycle. _Example is washing machine_
* **Peak in middle** - the consumption peaks in the middle of the cycle.
* **Peak in beginning and end** - the consumption peaks in the beginning and end of the cycle.
* **Custom consumption** - Custom pattern. Set your own pattern
