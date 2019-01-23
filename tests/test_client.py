import pytest
import json
import time
import os
from breadboard.client import BreadboardClient

@pytest.fixture(scope='module')
def client():
    """Client that connects to the API. Needs auth info in API_CONFIG.json"""
    return BreadboardClient(config_path = 'tests/API_CONFIG.json')


@pytest.mark.usefixtures('client')
class TestClientRaw(object):

    @staticmethod
    def teardown_method():
        time.sleep(0.5) #Avoid a rate limit

    def test_get_single_image_raw(self, client):
        r = client.get_images_json('10-09-2018_00_21_57_TopA')
        assert r.status_code == 200

    def test_get_multiple_images_raw(self, client):
        r = client.get_images_json(['10-09-2018_00_21_57_TopA','10-09-2018_00_21_57_TopB'])
        assert r.status_code == 200


@pytest.mark.usefixtures('client')
class TestClientPandas(object):

    @staticmethod
    def teardown_method():
        time.sleep(0.5) #Avoid a rate limit

    def test_get_single_image_all_params_pandas(self, client):
        df = client.get_images_df('10-09-2018_00_21_57_TopA')
        assert df.at[0,'FB_field_13_V']==3.774

    def test_get_multiple_images_all_params_pandas(self, client):
        df = client.get_images_df(['10-09-2018_00_21_57_TopA','10-09-2018_00_21_57_TopB'])
        assert df.at[1,'ImagFreq0']==193.95

    def test_get_multiple_images_one_params_pandas(self, client):
        df = client.get_images_df(['10-09-2018_00_21_57_TopA','10-09-2018_00_21_57_TopB'], 'cylinder hold time')
        assert df.at[1,'cylinder hold time']==0.2

    def test_get_multiple_images_some_params_pandas(self, client):
        df = client.get_images_df(['10-09-2018_00_21_57_TopA','10-09-2018_00_21_57_TopB'], ['EndcapShakeOffset','cylinder hold time'])
        assert df.at[1,'EndcapShakeOffset']==2.5

    def test_update_single_image(self, client):
        params_update  = {
            'settings': [0,0,0]
        }
        r = client.update_image(10, "10-09-2018_00_21_57_TopA", params_update)
        assert r.status_code == 200
