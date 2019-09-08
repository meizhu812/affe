import pandas as pd
import matplotlib.pyplot as plt
hours = list(range(24))
data_file=r'D:\Truman\Desktop\qc5.csv'
order = ['dt',
         'q']
data = pd.read_csv(data_file,usecols=order,
                                parse_dates=[0],
                                na_values=-9999)
data.set_index(data.columns[0], inplace=True)
data.dropna(inplace=True)
data=data.resample('H').mean()
data['hour']=data.index.hour
hourly_data = {}
for hour in hours:
    hourly_data[hour]=list(pd.Series(data[data['hour'] == hour]['q']).values)
hourly_data=pd.DataFrame.from_dict(hourly_data,orient='index').transpose()
hourly_data.to_csv(r'D:\Truman\Desktop\box.csv')

