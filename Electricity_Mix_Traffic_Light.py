from entsoe import EntsoePandasClient
import pandas as pd
from datetime import date, timedelta, datetime
import numpy as np
import matplotlib.pyplot as plt


def download_load_data(country_code, start, end):
    # Convert Time Stamp
    start_timestamp = pd.Timestamp(start, tz='Europe/Brussels')
    end_timestamp = pd.Timestamp(end, tz='Europe/Brussels')

    # Extract load
    pd_demand = client.query_load_forecast(country_code, start=start_timestamp, end=end_timestamp)
    # Extract wind and solar load
    pd_wind_solar_load = client.query_wind_and_solar_forecast(country_code, start=start_timestamp, end=end_timestamp, psr_type=None)

    return pd_demand, pd_wind_solar_load

def calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=0, print_value=False):
    # Share of Renewables
    demand = pd_demand['Forecasted Load'][index]
    wind_solar_load = pd_wind_solar_load['Solar'][index] + pd_wind_solar_load['Wind Onshore'][index]
    if 'Wind Offshore' in pd_wind_solar_load.columns.values:
        wind_solar_load = wind_solar_load + pd_wind_solar_load['Wind Offshore'][index]

    share_of_renewables = wind_solar_load / demand

    if print_value is True:
        print('Net Load: ' + str(pd_demand['Forecasted Load'][index]) + ' MW')
        print('Solar: ' + str(pd_wind_solar_load['Solar'][index]) + ' MW')
        if 'Wind Offshore' in pd_wind_solar_load.columns.values:
            print('Wind Offshore: ' + str(pd_wind_solar_load['Wind Offshore'][index]) + ' MW')
        print('Wind Onshore: ' + str(pd_wind_solar_load['Wind Onshore'][index]) + ' MW')

    return share_of_renewables

def calculate_current_share_of_renewables(country_code):
    # Extract Timestamps
    timestamp_now = datetime.now()  # .strftime("%Y%m%d%H%M")
    print(timestamp_now)
    timestamp_near_future = (datetime.now() + timedelta(minutes=15))  # .strftime("%Y%m%d%H%M")

    #Calculate the current share of renewables
    pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                       start=timestamp_now,
                                                       end=timestamp_near_future)
    current_share_of_renewables = calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=0,
                                                       print_value=True)

    return current_share_of_renewables

def calculate_share_of_renewable_quantiles(country_code, no_of_quantiles, days_in_past, days_in_future, today_mode):
    # Downloads data
    if today_mode==True:
        pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                           start=date.today(),
                                                           end=date.today() + timedelta(days=1))
    elif today_mode==False:
        pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                       start=datetime.now() - timedelta(days=days_in_past),
                                                       end=datetime.now() + timedelta(days=days_in_future))
    # Calculates share of renewables for every timestep
    list_of_renewables = []
    renewables_dict = {}

    for i in range(len(pd_wind_solar_load['Wind Onshore'])):
        share_of_renewables = calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=i)
        list_of_renewables.append(share_of_renewables)
        renewables_dict[pd_demand.index[i]] = share_of_renewables

    renewables_df = pd.DataFrame(renewables_dict.values(),index=renewables_dict.keys())
    print(renewables_df)
    # print(list_of_renewables)

    # Calculates quantiles
    quantiles = []
    for i in range(no_of_quantiles-1):
        grenze = 100/no_of_quantiles*(i+1)
        quantiles.append(np.percentile(np.array(list_of_renewables), int(grenze)))

    return quantiles, renewables_df

def calculate_traffic_light_color(current_share_of_renewables, quantiles, color_scheme):
    for i in range(len(quantiles)):
        if current_share_of_renewables <= quantiles[i]:
            color = color_scheme[i]
            break
    if current_share_of_renewables > quantiles[len(quantiles)-1]:
        color = color_scheme[len(quantiles)]

    return color

def print_graph(df, quantiles):
    # ax = plt.gca()
    # df.plot(kind='line', x='0', y=index, ax=ax)
    plt.plot(df.index, df[0])
    for quantil in quantiles:
        plt.axhline(y=quantil, color="black")

    plt.axvline(x=datetime.now(),color="gray")

    plt.show()

def main_app(token='xxx',
             country_code='DE',
             no_of_quantiles=4,
             color_scheme=['RED', 'ORANGE', 'YELLOW', 'GREEN'],
             days_in_past=5,
             days_in_future=5,
             today_mode=True,
             plotting=True):

    global client
    client = EntsoePandasClient(api_key=token)

    ##############################
    #### PARAMETER DEFINITION ####
    ##############################
    # country_code = 'DE'  # Germany
    # no_of_quantiles=4
    # color_scheme = ['RED', 'ORANGE', 'YELLOW', 'GREEN']
    # days_in_past=5
    # days_in_future=5
    ##############################
    ##############################

    # Calculate the current share of renewables
    current_share_of_renewables = calculate_current_share_of_renewables(country_code)
    # Calculate quantiles of past and future
    quantiles, renewables_df = calculate_share_of_renewable_quantiles(country_code, no_of_quantiles,
                                                       days_in_past,
                                                       days_in_future,
                                                       today_mode=today_mode)
    # Calculate current traffic light color
    color = calculate_traffic_light_color(current_share_of_renewables,quantiles,color_scheme)

    print('Quantile: ' + str(quantiles))
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    print('REGION: '+str(country_code))
    print('AKTUELLER ANTEIL ERNEUERBARER ENERGIEN: '+str(round(current_share_of_renewables * 100,2)) + ' %')
    print('AKTUELLER AMPELSTATUS: '+color)
    print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')

    if plotting == True:
        print_graph(df=renewables_df, quantiles=quantiles)

    return current_share_of_renewables, color

main_app(token='xxx',
             country_code='DE',
             no_of_quantiles=3,
             color_scheme=['RED', 'YELLOW', 'GREEN'],
             days_in_past=1,
             days_in_future=1,
             today_mode=True,
             plotting=True)

