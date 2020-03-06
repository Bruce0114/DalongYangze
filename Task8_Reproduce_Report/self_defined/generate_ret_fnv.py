import sys
import numpy as np
import pandas as pd


def generate_ret_fnv(inv_index_tb, futures_data_df, signal_df, shift_sig, mode, end_date):

    futures_data_df.index.name = 'timestamp'
    futures_data_df.index = pd.to_datetime(futures_data_df.reset_index()['timestamp'])
    futures_dailyret_df = futures_data_df.diff(1) / futures_data_df.shift(1)
    
    signal_df.index.name = 'timestamp'
    signal_df.index = pd.to_datetime(signal_df.reset_index()['timestamp'])
    
    signal_df['transaction_cost'] = -0.0003 * abs(signal_df.fillna(0).diff(1)).sum(axis=1) 
    
    # generate daily weight series by applying 'equally weighted' scheme
    signal_df['weight_equal'] = pd.Series([np.nan for i in range(len(signal_df))])
    for row in range(len(signal_df)):
        targets = signal_df.iloc[row][(signal_df.iloc[row] == 1) | (signal_df.iloc[row] == -1)]
        if len(targets) > 0:
            signal_df.iloc[row, -1] = 1 / len(targets)
        else:
            signal_df.iloc[row, -1] = 0
    
    # correct for the position-building process/effect caused by using 'twap'
    if shift_sig == 'shift_yes':
        shift_param = 2
    elif shift_sig == 'shift_no':
        shift_param = 1
    else:
        print("Input error for 'shift_sig' parameter. Please enter again. Only 2 input options: 'shift_yes', 'shift_no'.")
        sys.exit(1)
        
    signal_shift_df = signal_df.shift(shift_param)
    
    portfolio_dailyret_df = (signal_shift_df[signal_shift_df.columns[0:-2]] * futures_dailyret_df).sum(axis=1)
    portfolio_dailyret_df = pd.DataFrame(signal_shift_df['weight_equal'] * portfolio_dailyret_df, columns=['daily_ret_portfolio'])
    portfolio_dailyret_df['ret_plus1'] = portfolio_dailyret_df['daily_ret_portfolio']
    portfolio_dailyret_df['ret_plus1'] = portfolio_dailyret_df['ret_plus1'].apply(lambda x: x + 1)
    portfolio_dailyret_df['transaction_cost'] = signal_shift_df['transaction_cost'] * signal_shift_df['weight_equal']
    portfolio_dailyret_df['ret_plus1_DeductTC'] = portfolio_dailyret_df['ret_plus1']
    portfolio_dailyret_df['ret_plus1_DeductTC'] = portfolio_dailyret_df.apply(lambda df: df['ret_plus1'] + df['transaction_cost'], axis=1)
    portfolio_dailyret_df['fund_net_value'] = portfolio_dailyret_df['ret_plus1']
    portfolio_dailyret_df['fund_net_value'] = portfolio_dailyret_df['fund_net_value'].cumprod()
    portfolio_dailyret_df['fund_net_value_DeductTC'] = portfolio_dailyret_df['ret_plus1_DeductTC']
    portfolio_dailyret_df['fund_net_value_DeductTC'] = portfolio_dailyret_df['fund_net_value_DeductTC'].cumprod()
    portfolio_dailyret_df = portfolio_dailyret_df.dropna()
    
    # create date selection index
    date_index_annualized = (portfolio_dailyret_df.index >= pd.to_datetime('2010-01-01')) & (portfolio_dailyret_df.index <= pd.to_datetime(end_date))
    date_index_cumulative = (portfolio_dailyret_df.index >= pd.to_datetime('2017-01-01')) & (portfolio_dailyret_df.index <= pd.to_datetime(end_date))

    # calculte annualized returns, without and with transaction cost deducted
    portfolio_slice_annualized_df = portfolio_dailyret_df[date_index_annualized]
    trading_years = len(portfolio_slice_annualized_df) / 243
    annualized_ret = round((portfolio_slice_annualized_df['fund_net_value'][-1] / portfolio_slice_annualized_df['fund_net_value'][0]) ** (1/trading_years) - 1, 4)
    annualized_ret_DeductTC = round((portfolio_slice_annualized_df['fund_net_value_DeductTC'][-1] / portfolio_slice_annualized_df['fund_net_value_DeductTC'][0]) ** (1/trading_years) - 1, 4)
    annualized_ret_pair = [annualized_ret, annualized_ret_DeductTC]

    # calculte cumulative returns, without and with transaction cost deducted
    portfolio_slice_cumulative_df = portfolio_dailyret_df[date_index_cumulative]
    cumulative_ret = round((portfolio_slice_cumulative_df['fund_net_value'][-1] / portfolio_slice_cumulative_df['fund_net_value'][0]) - 1, 4)
    cumulative_ret_DeductTC = round((portfolio_slice_cumulative_df['fund_net_value_DeductTC'][-1] / portfolio_slice_cumulative_df['fund_net_value_DeductTC'][0]) - 1, 4)
    cumulative_ret_pair = [cumulative_ret, cumulative_ret_DeductTC]
    
    if mode == 'ret_portfolio_df':
        return portfolio_slice_annualized_df
    elif mode == 'ret_annualized_pair':
        return annualized_ret_pair
    elif mode == 'ret_cumulative_pair':
        return cumulative_ret_pair
    else:
        print("Input error for 'mode' parameter. Please enter again.")
        print("3 input options: 'ret_portfolio_df', 'ret_annualized_pair', 'ret_cumulative_pair'.")
        sys.exit(1)
