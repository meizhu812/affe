import pandas as pd
import matplotlib.pyplot as plt
hours = list(range(24))
data_file=r'D:\Truman\Desktop\present_work\01_academic\01_ammonia\03_2018summer\South\03Eddy\eddypro_ADV_full_output_2019-04-15T112708_adv.csv'
order = ['date',
         'time',
         'air_temperature']
data = pd.read_csv(data_file,skiprows=[0, 2],
                                usecols=order,
                                parse_dates=[[0, 1]],
                                na_values=-9999)
data.set_index(data.columns[0], inplace=True)
data.dropna(inplace=True)
data=data.resample('H').mean()
data['hour']=data.index.hour
hourly_data = {}
for hour in hours:
    hourly_data[hour]=list(pd.Series(data[data['hour'] == hour]['air_temperature']).values)
hourly_data=pd.DataFrame.from_dict(hourly_data,orient='index').transpose()
hourly_data.to_csv(r'D:\Truman\Desktop\box.csv')

