from entsoe import EntsoePandasClient
import pandas as pd
from datetime import date, timedelta, datetime
import numpy as np
import matplotlib.pyplot as plt
import argparse


def download_load_data(country_code, start, end):
    # Convert Time Stamp
    start_timestamp = pd.Timestamp(start, tz='Europe/Brussels')
    end_timestamp = pd.Timestamp(end, tz='Europe/Brussels')

    # Extract load
    pd_demand = client.query_load_forecast(country_code, start=start_timestamp, end=end_timestamp)
    # Extract wind and solar load
    pd_wind_solar_load = client.query_wind_and_solar_forecast(country_code, start=start_timestamp, end=end_timestamp, psr_type=None)

    return pd_demand, pd_wind_solar_load

def calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=0, print_value=False, format='text'):
    # Share of Renewables
    demand = pd_demand['Forecasted Load'][index]
    wind_solar_load = pd_wind_solar_load['Solar'][index] + pd_wind_solar_load['Wind Onshore'][index]
    if 'Wind Offshore' in pd_wind_solar_load.columns.values:
        wind_solar_load = wind_solar_load + pd_wind_solar_load['Wind Offshore'][index]

    share_of_renewables = wind_solar_load / demand

    if print_value is True:
        if format == 'text':
            print('Net Load: ' + str(pd_demand['Forecasted Load'][index]) + ' MW')
            print('Solar: ' + str(pd_wind_solar_load['Solar'][index]) + ' MW')
            if 'Wind Offshore' in pd_wind_solar_load.columns.values:
                print('Wind Offshore: ' + str(pd_wind_solar_load['Wind Offshore'][index]) + ' MW')
            print('Wind Onshore: ' + str(pd_wind_solar_load['Wind Onshore'][index]) + ' MW')
        elif format == 'json':
            print('"netLoad": ' + str(pd_demand['Forecasted Load'][index]) + ', ')
            print('"solar": ' + str(pd_wind_solar_load['Solar'][index]) + ', ')
            if 'Wind Offshore' in pd_wind_solar_load.columns.values:
                print('"windOffshore": ' + str(pd_wind_solar_load['Wind Offshore'][index]) + ', ')
            print('"windOnshore": ' + str(pd_wind_solar_load['Wind Onshore'][index]) + ", ")


    return share_of_renewables

def calculate_current_share_of_renewables(country_code, format):
    # Extract Timestamps
    timestamp_now = datetime.utcnow()  # .strftime("%Y%m%d%H%M")
    if format == 'text':
        print(timestamp_now)
    elif format == 'json':
        print('"timestamp_now": "' + str(timestamp_now.isoformat()) + '", ')
    timestamp_near_future = (datetime.utcnow() + timedelta(minutes=15))  # .strftime("%Y%m%d%H%M")

    #Calculate the current share of renewables
    pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                       start=timestamp_now,
                                                       end=timestamp_near_future)
    current_share_of_renewables = calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=0,
                                                       print_value=True, format=format)

    return current_share_of_renewables

def calculate_share_of_renewable_quantiles(country_code, no_of_quantiles, days_in_past, days_in_future, today_mode, format):
    # Downloads data
    if today_mode==True:
        pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                           start=date.today(),
                                                           end=date.today() + timedelta(days=1))
    elif today_mode==False:
        pd_demand, pd_wind_solar_load = download_load_data(country_code=country_code,
                                                       start=datetime.utcnow() - timedelta(days=days_in_past),
                                                       end=datetime.utcnow() + timedelta(days=days_in_future))
    # Calculates share of renewables for every timestep
    list_of_renewables = []
    renewables_dict = {}

    for i in range(len(pd_wind_solar_load['Wind Onshore'])):
        share_of_renewables = calculate_share_of_renewables(pd_demand, pd_wind_solar_load, index=i)
        list_of_renewables.append(share_of_renewables)
        renewables_dict[pd_demand.index[i]] = share_of_renewables

    renewables_df = pd.DataFrame(renewables_dict.values(),index=renewables_dict.keys())

    if format == 'text':
        print(renewables_df)
    elif format == 'json':
        print('"history": [')
        for label, series in renewables_df.items():
            #print('"' + str(label) + '": "' + str(series) + '", ')
            first = True
            for index, value in series.items():
                if first == False:
                    print(",")
                print('{ "timestamp": "' + str(index.isoformat()) + '", "value": ' + str(value) +  ' }', end='')
                first = False

        print()
        print('],')
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

    plt.axvline(x=datetime.utcnow(),color="gray")

    plt.show()

def main_app(token='xxx',
             country_code='DE',
             no_of_quantiles=4,
             color_scheme=['RED', 'ORANGE', 'YELLOW', 'GREEN'],
             days_in_past=5,
             days_in_future=5,
             today_mode=True,
             plotting=True,
             format='text'):

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

    if format == 'json':
        print('{')

    # Calculate the current share of renewables
    current_share_of_renewables = calculate_current_share_of_renewables(country_code, format)
    # Calculate quantiles of past and future
    quantiles, renewables_df = calculate_share_of_renewable_quantiles(country_code, no_of_quantiles,
                                                       days_in_past,
                                                       days_in_future,
                                                       today_mode=today_mode,
                                                       format=format)
    # Calculate current traffic light color
    color = calculate_traffic_light_color(current_share_of_renewables,quantiles,color_scheme)

    if format == 'text':
        print('Quantile: ' + str(quantiles))
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print('REGION: '+str(country_code))
        print('AKTUELLER ANTEIL ERNEUERBARER ENERGIEN: '+str(round(current_share_of_renewables * 100,2)) + ' %')
        print('AKTUELLER AMPELSTATUS: '+color)
        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
    elif format == 'json':
        print('"quantiles": ' + str(quantiles) + ', ')
        print('"region": "'+ str(country_code) + '", ')
        print('"current_share_of_renewables": '+str(round(current_share_of_renewables * 100,2)) + ', ')
        print('"current_calculate_traffic_light_color": "'+color + '" ' )
        print('}')

    if plotting == True:
        print_graph(df=renewables_df, quantiles=quantiles)

    return current_share_of_renewables, color

parser = argparse.ArgumentParser("Electricity_Mix_Traffic_Light.py")
parser.add_argument("--token", help="security token to access the API from EntsoePandas", required=True)
parser.add_argument("--format", help="output format", choices=["text", "json"], default="text")
parser.add_argument("--plot", help="plot chart", action='store_const', const=True, default=False)
args = parser.parse_args()

main_app(token=args.token,
             country_code='DE',
             no_of_quantiles=3,
             color_scheme=['RED', 'YELLOW', 'GREEN'],
             days_in_past=1,
             days_in_future=1,
             today_mode=True,
             plotting=args.plot,
             format=args.format)

