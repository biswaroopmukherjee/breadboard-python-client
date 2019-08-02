import json
import pandas as pd
import datetime
import dateutil
import re
from tqdm import tqdm_notebook as tqdm
import logging

from warnings import warn

TIMEFORMATS = {
    'BEC1': '%m-%d-%Y_%H_%M_%S',
    'FERMI3':'%Y-%m-%d_%H_%M_%S',
    'FERMI3_2':'%Y-%m-%d_%H-%M-%S',
}

FORCEMATCH_BATCHSIZE = 20

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


    def post_images(self, image_names=None, auto_time=True, image_times=None, force_match=False, datetime_range=None, imagetimeformat=TIMEFORMATS['FERMI3'], page='', **kwargs):
        """
        Returns all the API data corresponding to a set of images as JSON

        Query modes:
        0) Nothing: returns a list of images
        1) Just a list of image names
        2) Image names + image times
        3) Force match : if you want to reset the runtimes of the images. 
        4) datetime range: get all images between two times

        Inputs:
        - image_names: a list of image names
        - auto_time: if True, automatically find the image_times from the image names (eg if the image name is a timestamp)
        - image_times: an optional list of image times
        - force_match: option to reset image runtimes in the API
        - datetime_range: a [start, end] array of python datetimes
        - imagetimeformat: python strptime format for reading the image times: eg '%Y-%m-%d_%H_%M_%S' (for Fermi 3)
        
        Outputs:
        - a json object containing the entire response from the API

        """
        if image_names:
            if isinstance(image_names,str):
                image_names = [image_names]
            namelist = ','.join(image_names)
        else:
            namelist = None

        if self.lab_name=='bec1':
            imagetimeformat = TIMEFORMATS['BEC1']

        # Automatically find the image times from the imagenames
        if image_names:
            if auto_time:
                try:
                    image_times = [timestr_to_datetime(image_name, format=imagetimeformat) for image_name in image_names]
                except:
                    imagetimeformat = TIMEFORMATS['FERMI3_2']
                    try:
                        image_times = [timestr_to_datetime(image_name, format=imagetimeformat) for image_name in image_names]
                    except:
                        raise ValueError('Please check your image timestamps')
        else:
            image_times = None

        if image_times:
            image_times = [clean_image_time(image_time) for image_time in image_times]
            image_times = ','.join(image_times)
        else:
            image_times = None

        if datetime_range:
            datetime_range = [clean_image_time(image_time) for image_time in datetime_range]
        else:
            datetime_range = [None, None]
    
        payload_dirty = {
            'lab': self.lab_name,
            'names': namelist,
            'force_match': force_match,
            'created': image_times,
            'start_datetime': datetime_range[0],
            'end_datetime': datetime_range[1],
            **kwargs
        }

        payload_clean = {k: v for k, v in payload_dirty.items() if not (
                        v==None or
                        (isinstance(v, tuple) and (None in v))
                )}

        response = self._send_message('post', '/images/'+page, data=json.dumps(payload_clean))
 
        if not response.json().get('results'):
            raise RuntimeError(response.json().get('detail'))
        return response




    def get_images_df(self, image_names=None, paramsin="list_bound_only", xvar='unixtime', extended=False, imagetimeformat=TIMEFORMATS['FERMI3'], force_match=False, **kwargs):
        """ Return a pandas dataframe for the given imagenames
        Inputs:
        - image_names: a list of image names
        - paramsin:
            > ['param1','param2',...] : a list of params
            > '*' for all params
            > 'list_bound_only' for listbound params only
        - xvar: a variable to use as df.x
        - extended: a boolean to show all the keys from the image, like the url and id
        - imagetimeformat : a python strptime format to parse the image times: eg '%Y-%m-%d_%H_%M_%S' (for Fermi 3)
        - force_match: option to reset image runtimes in the API
        Extra inputs used by post_message:
        - auto_time: if True, automatically find the image_times from the image names (eg if the image name is a timestamp)
        - image_times: an optional list of image times
        - datetime_range: a [start, end] array of python datetimes
 

        Outputs:
        - df: the dataframe with params

        Note: force_match increases the time, so the input is broken up to prevent blackbox timeouts.
        If force_match:
        - Print a quick message saying this is time-consuming, and wait until the API returns something (TODO: speed this process up)
        - When the API returns something, assume the force_match is done, and then query the rest of the data without force_match (as follows:)

        If not force_match:
        - Query through all pages, with a tqdm display
        - Collate all the data in a combined json
        
        """
        if image_names:
            if isinstance(image_names,str):
                image_names = [image_names]
            
            logging.debug('Number of images to get:' + str(len(image_names)))

            # Force match if needed
            if force_match:
                print('Re-matching runs to images. Note: this takes some time, so run force_match=False to speed up.')
                for i in tqdm(range(1+len(image_names)//FORCEMATCH_BATCHSIZE), 
                            desc='Matching...',
                            leave=False):
                    images_to_post = image_names[i*FORCEMATCH_BATCHSIZE : (i+1)*FORCEMATCH_BATCHSIZE]
                    if images_to_post:
                        self.post_images(images_to_post, imagetimeformat=imagetimeformat, force_match=True, **kwargs)


        
        # Get the first page
        response = self.post_images(image_names=image_names, imagetimeformat=imagetimeformat, force_match=False, **kwargs)
        jsonresponse = response.json()
        pbar = tqdm(total=jsonresponse.get('count'))
        images = jsonresponse.get('results')
        pbar.update(len(images))

        # Get all pages. Note: Force matching only needs to be run once
        while jsonresponse.get('next'):
            page = re.split('images/', jsonresponse.get('next'))[1]
            response = self.post_images(image_names, imagetimeformat=imagetimeformat, force_match=False, page=page, **kwargs)
            jsonresponse = response.json()
            images = images + jsonresponse.get('results')
            pbar.update(len(jsonresponse.get('results')))

        # Prepare df
        df = pd.DataFrame(columns = ['imagename'])
        try:
            df['imagename'] = [image['name'] for image in images]
        except:
            raise RuntimeError('Couldnt extract imagenames')
        df['x'] = 0

        # Prepare params:
        if extended:
            paramsall = set(images[0].keys())
        else:
            paramsall = set()
        if paramsin=='*':
            #  Get all params
            for jr in images:
                try:    params = set(jr['run']['parameters'].keys())
                except: params = set()
                paramsall = paramsall.union(params)
        elif paramsin=='list_bound_only':
            # Get listbound params
            for jr in images:
                try:    params = set(jr['run']['parameters']['ListBoundVariables'])
                except: params = set()
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
        for i, _ in df.iterrows():

            try: # to get the runtime
                runtime = images[i]['run']['runtime']
                logging.debug(runtime)
            except:
                runtime = '1970'
                warn('no run found for some images')

            for param in paramsall:

                if param=='runtime':
                    df.at[i, param] = runtime
                elif param=='unixtime':
                    df.at[i, param] = int(dateutil.parser.parse(runtime).timestamp())
                else:
                    # try to get run params
                    try: df.at[i,param] = images[i]['run']['parameters'][param]
                    except:
                        # try to get the bare image parameters
                        try:    df.at[i,param] = images[i][param]
                        except: df.at[i,param] = float('nan') # nan the rest


        # Get the xvar
        try:        df['x'] = df[xvar]
        except:     warn('Invalid xvar!')

        df = df.sort_values(by='imagename', ascending=True).reset_index(drop=True)

        return df


    def get_images_df_clipboard(self, xvar='unixtime', **kwargs):
        """ A convenient clipboard getter. Returns all parameters, and places the desired one in xvar
        """
        df = self.get_images_df(pd.read_clipboard(header=None)[0].tolist(), xvar=xvar, **kwargs)
        return df
