import requests, json, YakConnection

class PositionStackAPI(YakConnection.Connection): # POSITION STACK AP
    def __init__(self):
        super().__init__()
        self.api_key = self.get_setting("POSITION_STACK_API_KEY")

    def ReverseGeocode(self,Point): #Get Landmark Name From Coordinate 
        params = {
            'access_key': self.api_key,
            'query': f'{Point[0]},{Point[1]}',
        }
        data = requests.get('http://api.positionstack.com/v1/reverse', params=params)
        data = json.loads(data.text)["data"]
        for p in data:
            if p['type'] == "address":
                return p['name']
    
        return data["data"][0]['name']
    
    def ForwardGeocode(self, Address): # Get Landmark Name From Address
        params = {
            'access_key': self.api_key,
            'query': Address,
            'reigon':'North America',
            'limit':1
        }
        data = requests.get('http://api.positionstack.com/v1/forward', params=params)
        data = json.loads(data.text)["data"][0]
        return (data["latitude"], data["longitude"])