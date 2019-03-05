import requests
import urllib
import json

from breadboard.auth import BreadboardAuth
from breadboard.mixins import ImageMixins


class QuoteFixedSession(requests.Session):
    def send(self, *a, **kw):
        # a[0] is prepared request
        a[0].url = a[0].url.replace(urllib.parse.quote(","), ",")
        a[0].url = a[0].url.replace(urllib.parse.quote(":"), ":")
        # print(a[0].url)
        return requests.Session.send(self, *a, **kw)



class BreadboardClient(ImageMixins.ImageMixin):
    def __init__(self, config_path, lab_name=None):

        if not config_path:
            raise ValueError("Please enter a directory for your API configuration json file")

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

        self.session = QuoteFixedSession()


    def _send_message(self, method, endpoint, params=None, data=None):
        """ Send an HTTP message to the API
        """
        url = self.api_url + endpoint
        try:
            r = self.session.request(method, url, params=params, data=data,
                                     headers=self.auth.headers, timeout=30)
        except:
            raise RuntimeError('Error sending the message to the API url. Please check your API url.')
        return r
