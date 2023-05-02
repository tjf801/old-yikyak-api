from api_connectors.PositionStackAPI import PositionStackAPI #The API that can convert landmark / address to coordinate 
from api_connectors.Interyak import QueryYaks # One File to contain all endpoints (simplicity)

Geocoder = PositionStackAPI.PositionStackAPI()

point = Geocoder.ForwardGeocode("College of Idaho") 
data = QueryYaks(point).data

for d in data: print(d["voteCount"], d["text"])

