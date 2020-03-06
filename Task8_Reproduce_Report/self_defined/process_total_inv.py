import pandas as pd
# from yzutil import YzDataClient
from calc_inv_data import calc_inv_data

# integrate total inventory of all products into one dataframe
# perform data processing: match trading dates, length, frequency
def process_total_inv(inv_index_tb, yz, shift_inv):
    """Function for Concatenating and Matching Total Inventory of All the 22 Products
    """
    
    prod_id_list = list(inv_index_tb['product_id'].drop_duplicates())
    
    # pre-allocation
    inv_total_df = pd.DataFrame()
    
    for prod_id in prod_id_list:
    
        inv_single_df = calc_inv_data(prod_id, inv_index_tb, yz, shift_inv)
        
        inv_total_df = pd.concat([inv_total_df, round(inv_single_df[prod_id], 2)], axis=1, join='outer', sort=False)
    
    # fetch trading days
    trade_days = yz.get_trade_day(start_date="2010-01-01",end_date="2017-12-31")
    
    # create separate dataframe for calendar days and trading days
    # set timestamp index with identical name 'timestamp'
    calendardays_df = pd.DataFrame(inv_total_df.index, columns=['calendar_day'])
    calendardays_df['timestamp'] = calendardays_df['calendar_day']
    calendardays_df = calendardays_df.set_index('timestamp')
    
    tradingdays_df = pd.DataFrame(pd.to_datetime(trade_days), columns=['trading_day'])
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
