#!/usr/bin/env python
# coding: utf-8

import pandas as pd
from yzutil import YzDataClient


# calculate total inventory for one product
def calc_inv_data(prod_id, inv_index_tb, yz):
    
    # - fetch data: single 'ya_id'
    # - each 'ya_id' corresponds to a distinct inventory type
    # - each commodity product's gross inventory level is comprised of
    # multiple inventory types/sources
    ya_id_list = list(inv_index_tb[inv_index_tb['product_id'] == prod_id]['ya_id'])
   
    # rename the field 'index_value' with corresponding inventory type
    # to avoid the 'identical field name' issue after joining data
    inv_type_list = list(inv_index_tb[inv_index_tb['product_id'] == prod_id]['inventory_type'])
    
    # use unit conversion coefficient to convert all units to MT (Metric Ton)
    conversion_coeff_list = list(inv_index_tb[inv_index_tb['product_id'] == prod_id]['conversion_coeff'])
    
    join_df = pd.DataFrame()
    
    for i in range(len(ya_id_list)):
        
        # start and end dates here are 'calendar days' rather than 'trading days',
        # need to single out 'trading days' in later steps
        single_df = yz.get_alt_data(ya_id_list[i], fields=['index_time', 'index_value'], 
                                  start_date='2010-1-1', end_date='2017-12-31', latest=True)
        
        # convert all units to MT (Metric Ton)
        single_df[inv_type_list[i]] = single_df['index_value'] * conversion_coeff_list[i]
        
        # create timestamp from 'index_time'
        # drop duplicates and sort
        # set timestamp as row index in order to outer-join different inventory types later
        single_df['timestamp'] = pd.to_datetime(single_df['index_time'])
        single_df.drop_duplicates('timestamp', keep='last', inplace=True)
        single_df = single_df.sort_values(by=['timestamp'])
        single_df = single_df.set_index('timestamp')
        
        # - drop field 'index_time' to make dataframe more compact
        # - drop field 'index_value' to perform sum() correctly,
        #   otherwise the sum will be wrong/highly distorted
        single_df.drop(columns=['index_time', 'index_value'], inplace=True)
        
        # outer-join different inventory types into one dataframe
        join_df = pd.concat([join_df, single_df], axis=1, join='outer', sort=False)
    
    # use 'forward fill': key for sum
    join_df = join_df.fillna(method='ffill')
    
    # calculate total inventory level by summing up all inventory types
    join_df[prod_id] = join_df.sum(axis=1)
        
    return join_df


# integrate total inventory of all products into one dataframe
# perform data processing: match trading dates, length, frequency
def process_total_inv(inv_index_tb, yz):
    
    prod_id_list = list(inv_index_tb['product_id'].drop_duplicates())
    
    # pre-allocation
    inv_total_df = pd.DataFrame()
    
    for prod_id in prod_id_list:
    
        inv_single_df = calc_inv_data(prod_id, inv_index_tb, yz)
        
        inv_total_df = pd.concat([inv_total_df, round(inv_single_df[prod_id], 2)], axis=1, join='outer', sort=False)
    
    # fetch trading days from futures data
    day_twap_futures_df = yz.get_roll_feature("TEZA2",'day_twap', 1, instrument=1,
                                      start_date="2010-01-01", end_date="2017-12-31")
    
    # create separate dataframe for calendar days and trading days
    # set timestamp index with identical name 'timestamp'
    calendardays_df = pd.DataFrame(inv_total_df.index, columns=['calendar_day'])
    calendardays_df['timestamp'] = calendardays_df['calendar_day']
    calendardays_df = calendardays_df.set_index('timestamp')
    
    tradingdays_df = pd.DataFrame(pd.to_datetime(day_twap_futures_df.index), columns=['trading_day'])
    tradingdays_df['timestamp'] = tradingdays_df['trading_day']
    tradingdays_df = tradingdays_df.set_index('timestamp')
    
    # concatenate calendar days with trading days
    alldays_df = pd.concat([calendardays_df, tradingdays_df], axis=1, join='outer', sort=False)
    
    # create trading-day index
    tradingday_index = ~alldays_df['trading_day'].isnull()
    
    # retrieve trading-day data
    inv_total_tradingday_df = inv_total_df[tradingday_index]
    
    # match/convert frequency by 'forward fill' method
    inv_total_tradingday_df = inv_total_tradingday_df.fillna(method='ffill')
    
    return inv_total_tradingday_df


if __name__ == '__main__':

    # import KEY index table,
    # -- without which the program would cease to work
    inv_index_tb = pd.read_csv('/Users/apple/desktop/Yangze_Investment/Task8_Reproduce_Report/inventory_data_index.csv')

    # set up DataClient obj
    yz = YzDataClient('bruce@yangzeinvest.com', 'bruce123') 

    # run main processing program
    inv_total_tradingday_df = process_total_inv(inv_index_tb, yz)

