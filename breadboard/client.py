import requests
import json
import pandas as pd

from breadboard.auth import BreadboardAuth


class BreadboardClient:
    def __init__(self, config_path, lab_name=None):
        # handle no config_path
        with open(config_path) as file:
            api_config = json.load(file)

        self.auth = BreadboardAuth(api_config.get('api_key'))

        if api_config.get('api_url')==None:
            self.api_url = 'http://breadboard-215702.appspot.com'
        else:
            self.api_url = api_config.get('api_url').rstrip('/')

        if lab_name==None:
            if api_config.get('lab_name')==None:
                raise ValueError("Please enter a lab name.")
            else:
                self.lab_name = api_config.get('lab_name')
        else:
            self.lab_name = lab_name

        self.session = requests.Session()

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




    def get_images_json(self, image_names):
        # return all the API data corresponding to a set of images as JSON
        # todo: validate inputs
        if isinstance(image_names,str):
            image_names = [image_names]

        namelist = ','.join(image_names)
        payload = {
            'lab': self.lab_name,
            'names': namelist,
        }
        response = self._send_message('get', '/images', params=payload)
        return response




    def get_images_df(self, image_names, paramsin="*"):
        # Return a pandas dataframe
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
                try: # to get the run parameters
                    df.at[i,param] = jsonresponse[i]['run']['parameters'][param]
                except:
                    try:# to get the bare image parameters
                        df.at[i,param] = jsonresponse[i][param]
                    except: # nan the rest
                        df.at[i,param] = float('nan')

        return df




    def _send_message(self, method, endpoint, params=None, data=None):
        url = self.api_url + endpoint
        r = self.session.request(method, url, params=params, data=data,
                                 headers=self.auth.headers, timeout=30)
        return r
