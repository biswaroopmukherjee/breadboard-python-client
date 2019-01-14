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
class TestClient(object):

    @staticmethod
    def teardown_method():
        time.sleep(0.5) #Avoid a rate limit

    def test_get_single_image(self, client):
        r = client.get_images('10-09-2018_00_21_57_TopA')
        assert r.status_code == 200

    def test_get_multiple_images(self, client):
        r = client.get_images(['10-09-2018_00_21_57_TopA','10-09-2018_00_21_57_TopB'])
        assert r.status_code == 200
