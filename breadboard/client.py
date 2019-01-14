import requests
import json
from breadboard.auth import BreadboardAuth


class BreadboardClient:
    def __init__(self, config_path):
        # handle no config_path
        with open(config_path) as file:
            api_config = json.load(file)

        self.auth = BreadboardAuth(api_config.get('api_key'))

        if api_config.get('api_url')==None:
            self.api_url = 'http://breadboard-215702.appspot.com'
        else:
            self.api_url = api_config.get('api_url').rstrip('/')

        if api_config.get('api_url')==None:
            self.lab_name = 'bec1'
        else:
            self.lab_name = api_config.get('lab_name')

        self.session = requests.Session()


    def get_images(self, image_names):
        # todo: validate inputs
        if isinstance(image_names,str):
            image_names = [image_names]

        namelist = ','.join(image_names)
        payload = {
            'lab': self.lab_name,
            'names': namelist,
        }
        response = self._send_message('get', '/images', params=payload)
        print(response.url)
        return response

    def _send_message(self, method, endpoint, params=None, data=None):
        url = self.api_url + endpoint
        r = self.session.request(method, url, params=params, data=data,
                                 headers=self.auth.headers, timeout=30)
        return r
