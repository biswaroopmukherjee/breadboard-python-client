
import json
import pandas as pd
import datetime
import dateutil
import re

from warnings import warn

TIMEFORMATS = {
    'BEC1': '%m-%d-%Y_%H_%M_%S',
    'FERMI3':'%Y-%m-%d_%H_%M_%S',
    'FERMI3_2':'%Y-%m-%d_%H-%M-%S',
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


    def post_images(self, image_names=None, auto_time=True, image_times=None, force_match=False, datetime_range=None, imagetimeformat=TIMEFORMATS['FERMI3'], **kwargs):
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

        if auto_time:
            try:
                image_times = [timestr_to_datetime(image_name, format=imagetimeformat) for image_name in image_names]
            except:
                imagetimeformat = TIMEFORMATS['FERMI3_2']
                try:
                    image_times = [timestr_to_datetime(image_name, format=imagetimeformat) for image_name in image_names]
                except:
                    raise ValueError('Please check your image timestamps')


        if image_times:
            image_times = [clean_image_time(image_time) for image_time in image_times]
            image_times = ','.join(image_times)
        else:
            image_times = None

        if datetime_range:
            datetime_range = [clean_image_time(image_time) for image_time in datetime_range]

        payload_dirty = {
            'lab': self.lab_name,
            'names': namelist,
            'force_match': force_match,
            'created': image_times,
            'datetime_range': datetime_range,
            **kwargs
        }
        payload_clean = {k: v for k, v in payload_dirty.items() if not (
                        v==None or
                        (isinstance(v, tuple) and (None in v))
                )}
        response = self._send_message('post', '/images/', data=json.dumps(payload_clean))
        return response



    def get_images_df(self, image_names, paramsin="list_bound_only", xvar='unixtime', extended=False, imagetimeformat=TIMEFORMATS['FERMI3'], **kwargs):
        """ Return a pandas dataframe for the given imagenames
        inputs:
        - image_names: a list of image names
        - paramsin:
            > ['param1','param2',...] : a list of params
            > '*' for all params
            > 'list_bound_only' for listbound params only
        - xvar: a variable to use as df.x
        - extended: a boolean to show all the keys from the image, like the url and id
        - imagetimeformat : a python strptime format to parse the image times

        outputs:
        - df: the dataframe with params
        """

        if isinstance(image_names,str):
            image_names = [image_names]

        # Get data
        response = self.post_images(image_names, imagetimeformat=imagetimeformat, **kwargs)
        jsonresponse = response.json()

        # Catch no images
        if len(jsonresponse)==1 and jsonresponse['detail']=='warning: no run found':
            raise RuntimeError('No runs found. Make sure that breadboard is running on the control computer, and that the image names are correct.')

        # Prepare df
        df = pd.DataFrame(columns = ['imagename'])
        df['imagename'] = image_names
        df['x'] = 0

        # Prepare params:
        if extended:
            paramsall = set(jsonresponse[0].keys())
        else:
            paramsall = set()
        if paramsin=='*':
            #  Get all params
            for jr in jsonresponse:
                params = set(jr['run']['parameters'].keys())
                paramsall = paramsall.union(params)
        elif paramsin=='list_bound_only':
            # Get listbound params
            for jr in jsonresponse:
                try:
                    params = set(jr['run']['parameters']['ListBoundVariables'])
                except:
                    params = set()
                paramsall = paramsall.union(params)
        else:# use set of params provided
            if isinstance(paramsin, str):
                paramsin = [paramsin]
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
        addparams = set([
                    'unixtime'
                    ])

        paramsall = (paramsall - removeparams).union(addparams)


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

        # Get the xvar
        try:
            df['x'] = df[xvar]
        except:
            warn('Invalid xvar!')

        return df



    def get_images_df_clipboard(self, xvar='unixtime', **kwargs):
        """ A convenient clipboard getter. Returns all parameters, and places the desired one in xvar
        """
        df = self.get_images_df(pd.read_clipboard(header=None)[0].tolist(), xvar=xvar, **kwargs)
        return df
