import math
import numpy as np
import pandas as pd

def generate_inv_signal(inv_rateofchg_df):

    signal_df = inv_rateofchg_df

    for row in range(len(signal_df)):

        row_obs = inv_rateofchg_df.iloc[row]

        if not np.all(row_obs.isnull()):

            # single out negative change of inventory
            neg_chg_series = row_obs[row_obs < 0]
            # generate the list of products to long
            if len(neg_chg_series) > 0:
                # set top quintile (top 20%) by using 'round-up' approach
                signal_numbers = math.ceil(0.2 * len(neg_chg_series))
                # obtain products to long (buy)
                products_long = neg_chg_series.sort_values()[0:signal_numbers]
                ### print(neg_chg_series.sort_values(ascending=False)[0:signal_numbers].index, len(neg_chig_series.sort_values()[0:signal_numbers].index))
            
            # single out positive change of inventory
            pos_chg_series = row_obs[row_obs > 0]
            # generate the list of products to short
            if len(pos_chg_series) > 0:
                # set top quintile (top 20%) by using 'round-up' approach
                signal_numbers = math.ceil(0.2 * len(pos_chg_series))
                # obtain products to short (sell)
                products_short = pos_chg_series.sort_values(ascending=False)[0:signal_numbers]

            # key loop to create long/short signal            
            for col in range(len(signal_df.columns)):
                if signal_df.columns[col] in products_long.index:
                    signal_df.iloc[row, col] = 1  # long signal
                elif signal_df.columns[col] in products_short.index:
                    signal_df.iloc[row, col] = -1  # short signal
                else:
                    signal_df.iloc[row, col] = 0      
        else:
            continue        

    return signal_df


# load processed total inventory data
inv_total_tradingday_df = pd.read_csv('/home/dalong/bruce/Task8_Reproduce_Report/data/inventory_total_TradingDays.csv', index_col=0)

# set rolling parameter and calculate rate of change of total inventory levels
rolling = 10
inv_rateofchg_df = inv_total_tradingday_df.diff(rolling - 1) / inv_total_tradingday_df.shift(rolling - 1)

# main function call
signal_df = generate_inv_signal(inv_rateofchg_df)



