# Electricity Mix Traffic Light

## Description
With the help of this program, the current electricity mix of a European control area (freely selectable by the user) is evaluated and categorized with regard to the share of renewable energies (offshore wind, onshore wind, solar) - for example in a traffic light color scheme.

Forecast values from the [entsoe-py](https://github.com/EnergieID/entsoe-py) platform are used as the data basis. Based on the shares of renewable energies of each hour of the last _n_ and the next _m_ days (freely selectable by the user) determined. From the frequency distribution of the different shares of renewable energies _x_ quantiles (freely selectable by the user) are calculated. Each of these quantiles is assigned an attribute (for example, the colors of a traffic light). 

For the current electricity mix, the current share of renewable energies and the status attribute are returned.

## How To
```
main_app(token='xxxxx', # An entsoe-py API token is required, which can be freely requested
             country_code='DE', # Controle area to be investigated, e.g. 'DE' for Germany
             no_of_quantiles=4, # Number of quantiles to be calculated
             color_scheme=['RED', 'ORANGE', 'YELLOW', 'GREEN'], # Status Attribute for every quantile
             days_in_past=5, # number of past days to be considered to calculate the quantiles
             days_in_future=5 # number of future days to be considered to calculate the quantiles
             )

```

### Result

![Result Output](/images/output.png)

## Help Wanted!

We would like to host the electricity mix traffic light live as a web service. Feel free to contact us if you would like to contribute.

christian.klemm@fh-muenster.de
