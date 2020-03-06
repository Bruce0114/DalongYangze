import sys
import pandas as pd
# from yzutil import YzDataClient


# calculate total inventory for one product
def calc_inv_data(prod_id, inv_index_tb, yz, shift_inv):
    """Function for Concatenating and Summing Up Inventories of Single Product.
    """
    
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
    
    # use shift parameter to correct for 'future function':
    # -- the time gap between 'index_time' and 'insert_time'
    shift_list = list(inv_index_tb[inv_index_tb['product_id'] == prod_id]['shift'])
    
    join_df = pd.DataFrame()
    
    for i in range(len(ya_id_list)):
        
        # start and end dates here are 'calendar days' rather than 'trading days',
        # need to single out 'trading days' in later steps
        single_df = yz.get_alt_data(ya_id_list[i], fields=['index_time', 'index_value'], 
                                  start_date='2010-1-1', end_date='2017-12-31', latest=True)
        
        if shift_inv == 'shift_yes':
            # convert all units to MT (Metric Ton)
            single_df[inv_type_list[i]] = (single_df['index_value'] * conversion_coeff_list[i]).shift(shift_list[i])
        elif shift_inv == 'shift_no':
            # convert all units to MT (Metric Ton)
            single_df[inv_type_list[i]] = single_df['index_value'] * conversion_coeff_list[i]
        else:
            print("Input error for 'shift_inv' parameter. Please enter again. Only 2 input options: 'shift_yes', 'shift_no'.")
            sys.exit(1)
            
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