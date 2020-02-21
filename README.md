# breadboard-python-client

The python client for the [Breadboard API](https://github.com/biswaroopmukherjee/breadboard). Gets parameters from the experiment and matches them to your images.

## Installation

Get it with `pip install breadboard`. Ask me for an API key, and store it somewhere locally.

---

## Usage

First, import the breadboard module and initialize with your secure API key (stored under `filepath/API_CONFIG.json`):

```python
from breadboard import BreadboardClient
bc = BreadboardClient(config_path='filepath/API_CONFIG.json')
```

---

### Ctrl-C:
This is the easiest way to get parameters:
1. Copy a list of imagenames.
2. Run the following:
```python
df = bc.get_images_df_clipboard()
print(df.head())
```

This produces a pandas dataframe:

|    | imagename                      |           x |   reWhirrFreq |   holdTime |   TOF |   evapEndTOPMHz |   accordionHoldSpacing |    unixtime |   reWhirrTime |
|---:|:-------------------------------|------------:|--------------:|-----------:|------:|----------------:|-----------------------:|------------:|--------------:|
|  0 | 2019-03-04_15-36-22_SensicamQE | 1.55171e+09 |          4.75 |        300 |     0 |            1777 |                    4.4 | 1.55171e+09 |             7 |
|  1 | 2019-03-04_15-35-52_SensicamQE | 1.55171e+09 |          4.75 |        275 |     0 |            1777 |                    4.4 | 1.55171e+09 |             7 |


---

By default, you will get the variables that were list-bound in Cicero. This is most convenient if you were running a list (F12), and don't want to write down which variables were important. 

The `paramsin` keyword argument lets you choose what parameters to return. You can request all parameters by passing the argument `paramsin='*'`, or pass a list of desired parameters `paramsin=[param1, param2, ...]`. 

The x column is a copy of another column. This makes plotting and analysis easy (everything is versus `df.x`). By default, the x column is the timestamp, but you can select any other parameter (say `paramname`) by passing the argument `xvar=paramname`.


---

### General getting and posting:

To get specific parameters, use: 
```python
imagenames = ['10-09-2018_00_27_44_TopA','10-09-2018_00_27_44_TopB']
params = ['FB_field_13_V','ImagFreq0']
df = bc.get_images_df(imagenames, paramsin=params)
```
This produces:


|    | imagename                |           x |   ImagFreq0 |   FB_field_13_V |    unixtime |
|---:|:-------------------------|------------:|------------:|----------------:|------------:|
|  0 | 10-09-2018_00_27_44_TopA | 1.53904e+09 |      193.95 |           3.774 | 1.53904e+09 |
|  1 | 10-09-2018_00_27_44_TopB | 1.53904e+09 |      193.95 |           3.774 | 1.53904e+09 |'



---

An example of posting imagenames (can be an array or a list):

`bc.post_images(imagenames, pixel_size=3, notes='test')`

---

To copy images from your clipboard and use it for other things, use:

`pd.read_clipboard(header=None)[0].tolist()`


---

To get a list of images between two datetimes, use:
```python
import datetime
start_datetime = datetime.datetime(2019,7,1,0,0,55)
end_datetime = datetime.datetime(2019,7,2,0,20,55)
out = bc.get_images_df(datetime_range=[start_datetime, end_datetime])
```