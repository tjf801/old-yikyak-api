from YakConnection import AccessToken, Connection
import json, requests

class QueryYaks(Connection):
    def __init__(self, Point=(0,0)):
        super().__init__()
        self.secret = AccessToken()
        self.Point = Point
        headers = {
            'content-type': 'application/json',
            'accept': '*/*',
            'apollographql-client-version': '3.0.3-3',
            'authorization': str(AccessToken()),
            'accept-language': 'en-US,en;q=0.9',
            'location': 'POINT(0 0)',
            'x-apollo-operation-type': 'query',
            'user-agent': 'Yik%20Yak/3 CFNetwork/1399 Darwin/22.1.0',
            'apollographql-client-name': 'com.yikyak.2-apollo-ios',
            'x-apollo-operation-name': 'Feed',
        }
        json_data = {
            'operationName': 'Feed',
            'query': 'query Feed($feedType: FeedType, $feedOrder: FeedOrder, $pageLimit: Int, $cursor: String, $point: FixedPointScalar) {\n  feed(\n    feedType: $feedType\n    feedOrder: $feedOrder\n    first: $pageLimit\n    after: $cursor\n    point: $point\n  ) {\n    __typename\n    edges {\n      __typename\n      node {\n        __typename\n        id\n        videoId\n        videoPlaybackDashUrl\n        videoPlaybackHlsUrl\n        videoDownloadMp4Url\n        videoThumbnailUrl\n        videoState\n        text\n        userEmoji\n        userColor\n        secondaryUserColor\n        distance\n        geohash\n        interestAreas\n        createdAt\n        commentCount\n        voteCount\n        isIncognito\n        isMine\n        isReported\n        myVote\n        threadId\n        isReplyable\n        notificationsEnabled\n      }\n    }\n    pageInfo {\n      __typename\n      endCursor\n      hasNextPage\n    }\n  }\n}',
            'variables': {
                'cursor': None,
                'feedOrder': "HOT",
                'feedType': 'LOCAL',
                'pageLimit': None,
                'point': f'POINT({Point[1]} {Point[0]})',
            },
        }
        response = requests.post('https://api.yikyak.com/graphql/', headers=headers, json=json_data)
        self.data = [d["node"] for d in json.loads(response.text)["data"]["feed"]["edges"]]
