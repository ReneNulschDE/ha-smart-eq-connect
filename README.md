

# Smart EQ Connect
[![HassFest tests](https://github.com/renenulschde/ha-smart-eq-connect/workflows/Validate%20with%20hassfest/badge.svg)]



Smart EQ Connect platform as a Custom Component for Home Assistant.

IMPORTANT:

* Please login once in the Smart EQ Connect IOS or Android app before you install this component.

* Tested Countries: DE

### Installation
* This is not a Home Assistant Add-On. It's a custom component.
* Download the folder custom_component and copy it into your Home-Assistant config folder. 
* [How to install a custom component?](https://www.google.com/search?q=how+to+install+custom+components+home+assistant) 
* Restart HA, Refresh your HA Browser window
### Configuration

Use the "Add Integration" in Home Assistant and select "Smart EQ Connect".

### Optional configuration values

See Options dialog in the Integration under Home-Assistant/Configuration/Integration.

```
Excluded Cars: comma-separated list of VINs.
Debug Save Messages: Enable this option to save all relevant received message into the messages folder of the component
```

## Available components 
Depends on your own car or purchased Mercedes Benz licenses.


### Binary Sensors

* None so far


### Sensors

* odometer
 

* Range Electric


* State of Charge (soc)
  ```
  Internal Name: soc

  State of charge (SoC) is the level of charge of an electric battery relative to its capacity. The units of SoC are percentage points (0% = empty; 100% = full). 

  ```



### Services

* None so far


### Switches

* None so far


### Logging

Set the logging to debug with the following settings in case of problems.

```
logger:
  default: warn
  logs:
    custom_components.smarteqconnect: debug
```

### Open Items
* Auto Refresh
* Clean Up


### Useful links

* [Forum post](https://community.home-assistant.io/t/mercedes-me-component/41911)
