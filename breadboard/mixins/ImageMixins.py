
import json
import pandas as pd
import datetime
import dateutil

TIMEFORMATS = {
    'BEC1': '%m-%d-%Y_%H_%M_%S',
    'FERMI3':'%Y-%m-%d_%H_%M_%S'
}

def timestr_to_datetime(time_string, format=None):
    time_string = re.sub(' ','0',time_string[0:19])
    if not format: format = TIMEFORMATS['FERMI3']
    return datetime.datetime.strptime(time_string,format)


def clean_image_time(image_time):
    if type(image_time)==datetime.datetime:
        return image_time.isoformat()+'Z'
    else:
        return image_time


class ImageMixin:
    """ Useful functions for Image queries through the breadboard Client
    Plugs into breadboard/client.py
    """

    def update_image(self, id, image_name, params ):
        # return all the API data corresponding to a set of images as JSON
        # todo: validate inputs
        payload = {
            'name': image_name
        }
        payload = {**payload, **params}
        if isinstance(id, float):
            id = int(id)
        update_url =  '/images/'+str(id)+'/'
        response = self._send_message('PUT', update_url,
                            data=json.dumps(payload)
                            )
        return response


    def get_images_json(self, image_names=None, auto_time=False, image_times=None, force_match=False, datetime_range=None ):
        # return all the API data corresponding to a set of images as JSON
        # todo: handle error codes
        """
        Query modes:
        0) Nothing: returns a list of images
        1) Just a list of image names
        2) Image names + image times
        3) Force match : if you want to set the runtimes of the images
        4) datetime range: a [start, end] array of python datetimes
        """
        if image_names:
            if isinstance(image_names,str):
                image_names = [image_names]
            namelist = ','.join(image_names)
        else:
            namelist = None

        if self.lab_name=='bec1':
            imagetimeformat = TIMEFORMATS['BEC1']
        else:
            imagetimeformat = TIMEFORMATS['FERMI3']

        if auto_time:
            image_times = [timestr_to_datetime(image_name, format=imagetimeformat) for image_name in image_names]

        if image_times:
            image_times = [clean_image_time(image_time) for image_time in image_times]

        if datetime_range:
            datetime_range = [clean_image_time(image_time) for image_time in datetime_range]

        payload_dirty = {
            'lab': self.lab_name,
            'names': namelist,
            'force_match': force_match,
            'image_times': image_times,
            'datetime_range': datetime_range
        }
        payload_clean = {k: v for k, v in payload_dirty.items() if not (
                        v==None or
                        (isinstance(v, tuple) and (None in v))
                )}

        response = self._send_message('get', '/images', params=payload_clean)
        return response




    def get_images_df(self, image_names, paramsin="*"):
        """ Return a pandas dataframe for the given imagenames
        """
        if isinstance(image_names,str):
            image_names = [image_names]

        # Get data
        response = self.get_images_json(image_names)
        jsonresponse = response.json()

        # Prepare df
        df = pd.DataFrame(columns = ['imagename'])
        df['imagename'] = image_names

        # Prepare params:
        paramsall = set(jsonresponse[0].keys())
        if paramsin=='*':
            #  Get all params
            for jr in jsonresponse:
                params = set(jr['run']['parameters'].keys())
                paramsall = paramsall.union(params)
        else:
            if isinstance(paramsin, str):
                paramsin = [paramsin]
            # use set of params provided
            paramsall = paramsall.union(set(paramsin))

        removeparams = set([
                    'run',
                    'name',
                    'thumbnail',
                    'atomsperpixel',
                    'odpath',
                    'settings',
                    'ListBoundVariables',
                    'camera',
                    ])
        paramsall = paramsall - removeparams

        # Populate dataframe
        for i,r in df.iterrows():
            for param in paramsall:
                if param=='runtime':
                    df.at[i, param] = jsonresponse[i]['run']['runtime']
                elif param=='unixtime':
                    df.at[i, param] = int(dateutil.parser.parse(jsonresponse[i]['run']['runtime']).timestamp())
                else:
                    try: # to get the run parameters
                        df.at[i,param] = jsonresponse[i]['run']['parameters'][param]
                    except:
                        try:# to get the bare image parameters
                            df.at[i,param] = jsonresponse[i][param]
                        except: # nan the rest
                            df.at[i,param] = float('nan')

        return df
