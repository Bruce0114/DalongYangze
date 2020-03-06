import math
import numpy as np
import pandas as pd


def _generate_signal_separaterank(row_obs, sig_threshold):
    # single out negative change of inventory
    neg_chg_series = row_obs[row_obs < 0]
    # generate the list of products to long
    if len(neg_chg_series) > 0:
        # set top quintile (top 20%) by using 'round-up' approach
        signal_numbers = math.ceil(sig_threshold * len(neg_chg_series))
        # obtain products to long (buy)
        products_long = neg_chg_series.sort_values()[0:signal_numbers]
        ### print(neg_chg_series.sort_values(ascending=False)[0:signal_numbers].index, len(neg_chig_series.sort_values()[0:signal_numbers].index))
    
    # single out positive change of inventory
    pos_chg_series = row_obs[row_obs > 0]
    # generate the list of products to short
    if len(pos_chg_series) > 0:
        # set top quintile (top 20%) by using 'round-up' approach
        signal_numbers = math.ceil(sig_threshold * len(pos_chg_series))
        # obtain products to short (sell)
        products_short = pos_chg_series.sort_values(ascending=False)[0:signal_numbers]
    
    return products_long, products_short


def _generate_signal_universalrank(row_obs, sig_threshold):   
    # if len() >= 2, then long/short pair(s) exist
    if len(row_obs.dropna()) >= 2:
        # set quintile (top 20%) by using 'normal round' approach
        signal_numbers = round(sig_threshold * len(row_obs))
        # obtain products to long (buy)
        products_long = row_obs.dropna().sort_values()[0:signal_numbers]
        # obtain products to short (sell)
        products_short = row_obs.dropna().sort_values(ascending=False)[0:signal_numbers]
    else:
        # one side long
        if row_obs.dropna().iloc[0] > 0:
            products_long = row_obs.dropna()
        # one side short
        elif row_obs.dropna().iloc[0] < 0:
            products_short = row_obs.dropna()

    return products_long, products_short


def _generate_signal_ewmarank(signal_df, **kwargs):
    # apply exponentially-weighted moving average to total inventory change
    # 'span' parameter indicates 'day', i.e. span=10 means '10-day EWMA'
    signal_df = pd.DataFrame.ewm(signal_df, span=kwargs['span']).mean()
    
    return signal_df


def generate_inv_signal_allinone(inv_total_tradingday_df, rolling, sig_threshold, signal_type, **kwargs):
    
    if signal_type == 'ewma_universal_rank':
        signal_df = inv_total_tradingday_df.diff(rolling - 1) / inv_total_tradingday_df.shift(rolling - 1)
        signal_df = _generate_signal_ewmarank(signal_df, span=kwargs['span'])
    else:
        signal_df = inv_total_tradingday_df.diff(rolling - 1) / inv_total_tradingday_df.shift(rolling - 1)

    for row in range(len(signal_df)):

        row_obs = signal_df.iloc[row]

        if not np.all(row_obs.isnull()):

            if signal_type == 'separate_rank':
                products_long, products_short = _generate_signal_separaterank(row_obs, sig_threshold)      
            elif signal_type == 'universal_rank':
                products_long, products_short = _generate_signal_universalrank(row_obs, sig_threshold)  
            elif signal_type == 'ewma_universal_rank':
                # use universal rank for now
                # keep flexible and open for other ranking methods
                products_long, products_short =  _generate_signal_universalrank(row_obs, sig_threshold) 
            else:
                print("Input error for 'signal_type' parameter. Please enter again.")
                print("3 input options: 'separate_rank', 'universal_rank', 'ewma_universal_rank'.")
                sys.exit(1)

            # key loop to create long/short signal            
            for col in range(len(signal_df.columns)):
                if signal_df.columns[col] in products_long.index:
                    signal_df.iloc[row, col] = 1  # long signal
                elif signal_df.columns[col] in products_short.index:
                    signal_df.iloc[row, col] = -1  # short signal
                else:
                    if not np.isnan(signal_df.iloc[row, col]):
                        signal_df.iloc[row, col] = 0
                        
        else:
            continue        

    return signal_df