import numpy as np


def generate_inv_signal_unirank(inv_total_tradingday_df, rolling, sig_threshold):

    signal_df = inv_total_tradingday_df.diff(rolling - 1) / inv_total_tradingday_df.shift(rolling - 1)

    for row in range(len(signal_df)):

        row_obs = signal_df.iloc[row]

        if not np.all(row_obs.isnull()):
            
            if len(row_obs.dropna()) >= 2:
                # set quintile (top 20%) by using 'normal round' approach
                signal_numbers = round(sig_threshold * len(row_obs))
                # obtain products to long (buy)
                products_long = row_obs.dropna().sort_values()[0:signal_numbers]
                # obtain products to short (sell)
                products_short = row_obs.dropna().sort_values(ascending=False)[0:signal_numbers]
            else:
                if row_obs.dropna().iloc[0] > 0:
                    products_long = row_obs.dropna()
                elif row_obs.dropna().iloc[0] < 0:
                    products_short = row_obs.dropna()
                
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