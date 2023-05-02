import requests, json, PositionStackAPI

class Connection:
    def __init__(self, config_path):
        self.connection_settings = json.load(open(config_path))

    def get_setting(self, key):
        return self.connection_settings[key]
        

class AccessToken(Connection): #Access / Id Token TODO: Implement better solution to retreiving access token
    def __init__(self):
        super().__init__()
        headers = self.get_setting('headers')

        params = {
            'key': self.get_setting("key"),
        }

        json_data = {
            'grantType': 'refresh_token',
            'refreshToken': self.get_setting('refresh_token'),
        }

        self.response = requests.post('https://securetoken.googleapis.com/v1/token', params=params, headers=headers, json=json_data)
    def __str__(self) -> str:
        return json.loads(self.response.text)['access_token']