import pandas as pd
import numpy as np
from pandas import read_csv

sum_path = r'D:\Truman\Desktop\present_work\01_academic\01_ammonia\03_2018summer\North\04Footprint\fcsum.csv'

dateparse = lambda dates: pd.datetime.strptime(dates[0:10], '%y%m%d%H%M')
order_f = [' Datetm', ' Site_no', ' Fcsum(s/m)', ' Ratio(%)']
order_c = ['DATE_TIME', 'NH3_Raw']
fc_sum = pd.read_csv(sum_path, usecols=order_f, na_values=-9999, parse_dates=[0],date_parser=dateparse)
fc_sum.set_index(fc_sum.columns[0], inplace=True)
ammo_path = r'D:\Truman\Desktop\present_work\01_academic\01_ammonia\03_2018summer\North\02PrepData\Ammonia\data_averaged.csv'
ammo = read_csv(ammo_path, usecols=order_c, parse_dates=[0], na_values=-9999)
ammo.set_index(ammo.columns[0], inplace=True)
sumup = pd.merge(fc_sum, ammo, left_index=True, right_index=True, how='outer')
# sumup.eval('Qn = (c_n -c_s)/Fc_n', inplace=True)
# sumup.eval('Qs = (c_s -c_n)/Fc_s', inplace=True)
# sumup.replace([np.inf, -np.inf], np.nan,inplace=True)
# sumup.to_csv(SUM_UP)
# print(fc_n)
# print(c_all)
# print(c_s)
# print(c_n)
sumup.to_csv(r'D:\Truman\Desktop\sumup.csv')