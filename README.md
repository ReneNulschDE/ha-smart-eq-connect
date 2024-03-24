
# Smart EQ Connect


> :warning: **This component is not maintained anymore.** Please try to use the [Mercedes component MBAPI2020](https://github.com/ReneNulschDE/mbapi2020).



Smart EQ Connect platform as a Custom Component for Home Assistant.


![Screenshot Smart EQ connect in Home Assistant](https://raw.githubusercontent.com/ReneNulschDE/renenulschde.github.io/master/assets/screen_smarteq_1.png)


IMPORTANT:

* **The component is in a very early state**

* Please login once in the "smart EQ control" IOS or Android app before you install this component.

* Tested Countries: DE, NL

### Installation
* This is not a Home Assistant Add-On. It's a custom component.
* Download the folder custom_component and copy it into your Home-Assistant config folder. 
* [How to install a custom component?](https://www.google.com/search?q=how+to+install+custom+components+home+assistant) 
* Restart HA, Refresh your HA Browser window

### Configuration
Use the "Add Integration" in Home Assistant and select "Smart EQ Connect" and follow the following steps:

1. Put in your email address in the component setup.
2. When the second "PIN" screen comes up, do the following:
3. Goto the [mercedes benz website](https://www.mercedes-benz.de/?group=all&subgroup=see-all&view=BODYTYPE) (NOT the smart website) 
4. Click on Login in in the upper right corner and type your smart/mb email address (the same like in step 1)
5. On the next screen select "Login with TAN"
6. You will receive now a TAN via email. Use this TAN in the dialog out of Step 2.

### Optional configuration values

See Options dialog in the Integration under Home-Assistant/Configuration/Integration.

```
Excluded Cars: comma-separated list of VINs.
Debug Save Messages: Enable this option to save all relevant received message into the messages folder of the component
```

## Available components 
Depends on your own car or purchased Mercedes Benz licenses.


### Binary Sensors

* Charging active

* Tire warning

* Precond active


### Sensors

* odometer
  ```
    Attributes: Serviceintervaldistance, Serviceintervaldays
  ```

* Range Electric
  ```
    Attributes: electricconsumptionstart, soc, chargingactive, chargingstatus

  ```


* State of Charge (soc)
  ```
  Internal Name: soc

  State of charge (SoC) is the level of charge of an electric battery relative to its capacity. The units of SoC are percentage points (0% = empty; 100% = full). 

  ```



### Services

### Services
* refresh_access_token:
  Refresh the API access token

* precond_start:
  Start the preconditioning of a zero emission car defined by a vin.



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
* Services for Preconditioning
* HACS Integration


### Useful links

* [Forum post](https://community.home-assistant.io/t/smart-eq-connect/356866)
