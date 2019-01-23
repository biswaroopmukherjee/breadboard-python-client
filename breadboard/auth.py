
class BreadboardAuth:
    def __init__(self, api_key):
        self.api_key = api_key
        self.headers = {
                'Authorization': 'Token '+ self.api_key,
                'Content-Type': "application/json",
        }
