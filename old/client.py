from dataclasses import dataclass
from typing import Generator, Iterator, Literal, Optional
import requests
import jwt
from dm_thread import Message, Thread
from yak import Yak
from comment import Comment


@dataclass
class YikYakAuthToken:
    @dataclass
    class _FireBaseInfo:
        identities: dict[Literal["phone"], list[str]]
        sign_in_provider: Literal["phone"]
    
    _jwt: str # the actual token
    
    iss: str # issuer
    aud: str # audience
    auth_time: int
    user_id: str
    sub: str # subject
    iat: int # issued at
    exp: int # expires at
    phone_number: str
    firebase: _FireBaseInfo
    
    @classmethod
    def from_jwt(cls, token: str) -> "YikYakAuthToken":
        _json = jwt.decode(token, algorithms=["RS256"], options={"verify_signature": False})
        fb = cls._FireBaseInfo(**_json.pop('firebase'))
        return cls(token, firebase=fb, **_json)
    
    def encode(self) -> str:
        return self._jwt

class YikYakClient:
    def __init__(self, refresh_token: str, 
        location: tuple[float, float],
        client_name: str = "com.yikyak.2", 
        user_agent: str = "Yik%20Yak/96 CFNetwork/1335.0.3 Darwin/21.6.0",
    ):
        self.refresh_token = refresh_token
        self.location = f"POINT({location[0]} {location[1]})"
        self.client_name = client_name
        self.user_agent = user_agent
        
        self.refresh_access_token()
    
    def refresh_access_token(self):
        self.access_token = self.get_access_token()
    
    def get_access_token(self) -> YikYakAuthToken:
        response = requests.post(
            "https://securetoken.googleapis.com/v1/token?key=REDACTED",
            headers={
                'Content-Type': 'application/json',
                'X-Client-Version': 'iOS/FirebaseSDK/9.0.0/FirebaseCore-iOS',
                'X-Ios-Bundle-Identifier': 'com.yikyak.2',
                'User-Agent': 'FirebaseAuth.iOS/9.0.0 com.yikyak.2/1.6.4 iPhone/15.6 hw/iPhone13_2'
            },
            json={
                "grant_type": "refresh_token",
                "refresh_token": self.refresh_token
            }
        )
        response.raise_for_status()
        return YikYakAuthToken.from_jwt(response.json()['access_token'])
    
    def request_headers(self, operation_type: Literal["query", "mutation"], operation_name: str) -> dict[str, str]:
        return {
            "Host": "api.yikyak.com",
            "apollographql-client-version": "1.6.4-96",
            "Authorization": self.access_token.encode(),
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "en-US,en;q=0.9",
            "Location": self.location,
            "Connection": "keep-alive",
            "Content-Type": "application/json",
            "User-Agent": self.user_agent,
            "apollographql-client-name": self.client_name,
            
            "X-APOLLO-OPERATION-TYPE": operation_type,
            "X-APOLLO-OPERATION-NAME": operation_name,
        }
    
    def yakarma(self) -> int:
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'GetYakarma'),
            json={
                "operationName": "GetYakarma",
                "query": """query GetYakarma {\n  me {\n    __typename\n    yakarmaScore\n  }\n}""",
                "variables": None
            }
        )
        response.raise_for_status()
        response_json = response.json()
        
        return response_json['data']['me']['yakarmaScore']
    
    def posts(self, 
        num_posts: Optional[int] = None,
        cursor_position: Optional[str] = None,
        feed_order: Literal["NEW", "TOP"] = "NEW",
        feed_type: Literal["SELF", "LOCAL", "NATIONWIDE"] = "LOCAL"
    ) -> Generator[Yak, None, None]:
        """Get posts from the feed"""
        FEED_QUERY_GRAPHQL = """query Feed($feedType: FeedType, $feedOrder: FeedOrder, $pageLimit: Int, $cursor: String, $point: FixedPointScalar) {
  feed(
    feedType: $feedType
    feedOrder: $feedOrder
    first: $pageLimit
    after: $cursor
    point: $point
  ) {
    __typename
    edges {
      __typename
      node {
        __typename
        id
        userId
        videoId
        videoPlaybackDashUrl
        videoPlaybackHlsUrl
        videoDownloadMp4Url
        videoThumbnailUrl
        videoState
        text
        userEmoji
        userColor
        secondaryUserColor
        distance
        geohash
        interestAreas
        createdAt
        commentCount
        voteCount
        isIncognito
        isMine
        isReported
        myVote
      }
    }
    pageInfo {
      __typename
      endCursor
      hasNextPage
    }
  }
}"""
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'Feed'),
            json={
                "operationName": "Feed",
                "query": FEED_QUERY_GRAPHQL,
                "variables": {
                    "cursor": cursor_position,
                    "feedOrder": feed_order,
                    "feedType": feed_type,
                    "pageLimit": min(num_posts, 100) if num_posts is not None else 100,
                    "point": self.location
                }
            }
        )
        response.raise_for_status()
        response_json = response.json()
        
        posts = [Yak.from_json(yak_edge["node"]) for yak_edge in response_json['data']['feed']['edges']]
        if num_posts is not None: num_posts -= len(posts)
        yield from posts
        
        page_info = response_json['data']['feed']['pageInfo']
        cursor_position = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
        
        print(f"Cursor: {cursor_position}")
        
        while has_next_page and (num_posts is None or num_posts > 0):
            response = requests.post(
                'https://api.yikyak.com/graphql/',
                headers=self.request_headers('query', 'Feed'),
                json={
                    "operationName": "Feed",
                    "query": FEED_QUERY_GRAPHQL,
                    "variables": {
                        "cursor": cursor_position,
                        "feedOrder": feed_order,
                        "feedType": feed_type,
                        "pageLimit": min(num_posts, 100) if num_posts is not None else 100,
                        "point": self.location
                    }
                }
            )
            response.raise_for_status()
            response_json = response.json()
            
            posts = [Yak.from_json(yak_edge["node"]) for yak_edge in response_json['data']['feed']['edges']]
            if num_posts is not None: num_posts -= len(posts)
            yield from posts
            
            page_info = response_json['data']['feed']['pageInfo']
            cursor_position = page_info['endCursor']
            has_next_page = page_info['hasNextPage']
            
            print(f"Cursor: {cursor_position}")
    
    def comments(self, 
        yak_id: str, 
        cursor_position: Optional[str] = None,
        num_comments: Optional[int] = None,
    ) -> Generator[Comment, None, None]:
        COMMENT_QUERY_GRAPHQL = """query YakComments($id: ID!, $pageLimit: Int, $cursor: String) {\n  yak(id: $id) {\n   __typename\n   comments(first: $pageLimit, after: $cursor) {\n     __typename\n     edges {\n       __typename\n       node {\n         __typename\n         id\n         userId\n         text\n         createdAt\n         userEmoji\n         userColor\n         secondaryUserColor\n         isMine\n         isReported\n         voteCount\n         myVote\n       }\n      }\n      pageInfo {\n        __typename\n        endCursor\n        hasNextPage\n      }\n    }\n  }\n}"""
        
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'Comments'),
            json={
                "operationName": "YakComments",
                "query": COMMENT_QUERY_GRAPHQL,
                "variables": {
                    "cursor": cursor_position,
                    "id": yak_id,
                    "pageLimit": min(num_comments, 100) if num_comments is not None else 100
                }
            }
        )
        response.raise_for_status()
        response_json = response.json()
        
        if response_json['data']['yak'] is None:
            print(yak_id, response_json)
            raise ValueError(f"Yak with ID {yak_id} does not exist")
        
        comments = [Comment.from_json(comment_edge["node"]) for comment_edge in response_json['data']['yak']['comments']['edges']]
        if num_comments is not None: num_comments -= len(comments)
        yield from comments
        
        page_info = response_json['data']['yak']['comments']['pageInfo']
        cursor_position = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
        
        while has_next_page and (num_comments is None or num_comments > 0):
            response = requests.post(
                'https://api.yikyak.com/graphql/',
                headers=self.request_headers('query', 'Comments'),
                json={
                    "operationName": "YakComments",
                    "query": COMMENT_QUERY_GRAPHQL,
                    "variables": {
                        "cursor": cursor_position,
                        "id": yak_id,
                        "pageLimit": min(num_comments, 100) if num_comments is not None else 100
                    }
                }
            )
            response.raise_for_status()
            response_json = response.json()
            
            comments = [Comment.from_json(comment_edge["node"]) for comment_edge in response_json['data']['yak']['comments']['edges']]
            if num_comments is not None: num_comments -= len(comments)
            yield from comments
            
            page_info = response_json['data']['yak']['comments']['pageInfo']
            cursor_position = page_info['endCursor']
            has_next_page = page_info['hasNextPage']
    
    def messages(self, thread_id: str, 
        cursor: str | None = None,
        order_by: str = "-created_at",
        page_limit: int = 100,
    ) -> Iterator[Message]:
        MESSAGE_GRAPHQL_QUERY = """query Messages($threadId: ID!, $pageLimit: Int!, $cursor: String, $orderBy: String) {
  node(id: $threadId) {
    __typename
    id
    ... on Thread {
      __typename
      id
      createdAt
      instance
      title
      participants {
        __typename
        edges {
          __typename
          node {
            __typename
            id
            emoji
            color
            secondaryColor
            isOp
            isSelf
            isReported
            hasUnreadMessages
          }
        }
      }
      messages(first: $pageLimit, after: $cursor, orderBy: $orderBy) {
        __typename
        edges {
          __typename
          node {
            __typename
            id
            text
            isMine
            isOp
            participantId
            createdAt
          }
        }
        pageInfo {
          __typename
          endCursor
          hasNextPage
        }
      }
      isDisabled
      isDraft
    }
  }
}"""
        
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'Messages'),
            json={
                "operationName": "Messages",
                "query": MESSAGE_GRAPHQL_QUERY,
                "variables": {
                    "threadId": thread_id,
                    "cursor": cursor,
                    "pageLimit": page_limit,
                    "orderBy": order_by
                }
            }
        )
        print(response.json())
        response.raise_for_status()
        response_json = response.json()
        
        if response_json['data']['node'] is None:
            raise ValueError(f"Thread with ID {thread_id} does not exist")
        
        messages = [
            Message.from_json(message_edge["node"])
            for message_edge in response_json
            ['data']['node']['messages']['edges']
        ]
        yield from messages
        
        page_info = response_json['data']['node']['messages']['pageInfo']
        cursor_position = page_info['endCursor']
        has_next_page = page_info['hasNextPage']
        
        while has_next_page:
            response = requests.post(
                'https://api.yikyak.com/graphql/',
                headers=self.request_headers('query', 'Messages'),
                json={
                    "operationName": "Messages",
                    "query": MESSAGE_GRAPHQL_QUERY,
                    "variables": {
                        "threadId": thread_id,
                        "cursor": cursor_position,
                        "pageLimit": page_limit,
                        "orderBy": order_by
                    }
                }
            )
            response.raise_for_status()
            response_json = response.json()
            
            messages = [
                Message.from_json(message_edge["node"])
                for message_edge in response_json
                ['data']['node']['messages']['edges']
            ]
            yield from messages
            
            page_info = response_json['data']['node']['messages']['pageInfo']
            cursor_position = page_info['endCursor']
            has_next_page = page_info['hasNextPage']
    
    def yak(self, yak_id: str) -> Yak | None:
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'Yak'),
            json={
                "operationName": "Yak",
                "query": """query Yak($id: ID!) {
  yak(id: $id) {
    __typename
    id
    userId
    videoId
    videoPlaybackDashUrl
    videoPlaybackHlsUrl
    videoDownloadMp4Url
    videoThumbnailUrl
    videoState
    text
    userEmoji
    userColor
    secondaryUserColor
    distance
    geohash
    interestAreas
    createdAt
    commentCount
    voteCount
    isIncognito
    isMine
    isReported
    myVote
  }
}""",
                "variables": {
                    "id": yak_id
                }
            }
        )
        response.raise_for_status()
        response_json = response.json()
        
        if response_json['data']['yak'] is None:
            return None
        
        return Yak.from_json(response_json['data']['yak'])
    
    def thread(self, thread_id: str, fetch_messages = True) -> Thread:
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'Thread'),
            json={
                "operationName":"SingleThread",
                "query": """query SingleThread($id: ID!) {
  thread(id: $id) {
    __typename
    id
    title
    isDisabled
    isDraft
    participants {
      __typename
      edges {
        __typename
        node {
          __typename
          id
          emoji
          color
          secondaryColor
          isOp
          isSelf
          isReported
          hasUnreadMessages
        }
      }
    }
    createdAt
    lastActiveAt
    instance
    instanceDisplayType
  }
}""",
                "variables": {
                    "id": thread_id
                }
            }
        )
        print(response.json())
        response.raise_for_status()
        response_json = response.json()
        
        if response_json['data']['thread'] is None:
            raise ValueError(f"Thread with ID {thread_id} does not exist")
        
        thread = Thread.from_json(response_json['data']['thread'])
        
        if fetch_messages: thread.messages = list(self.messages(thread_id))
        
        return thread
    
    def threads(self) -> Iterator[Thread]:
        raise NotImplementedError # TODO
    
    
	
	
    def create_post(self, text: str,
        is_incognito: bool = True,
        point: Optional[str] = None,
        
    ):
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'Post'),
            json={
                "operationName": "CreateYak",
                "query": "mutation CreateYak($input: CreateYakInput!) {\n  createYak(input: $input) {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n    yak {\n      __typename\n      id\n      text\n      interestAreas\n      distance\n      userColor\n      secondaryUserColor\n      userEmoji\n    }\n  }\n}",
                "variables": {
                    "input": {
                        "interestAreas": ["University of Connecticut"],
                        "isIncognito": is_incognito,
                        "point": point or self.location,
                        "secondaryUserColor":"#C38737",
                        "userColor":"#FFD38C",
                        "text": text,
                        "userEmoji": "",
                        "videoId": ""
                    }
                }
            }
        )
        response.raise_for_status()
        response_json = response.json()
        print(response_json)
        return response_json['data']['createYak']['yak']
    
    def create_comment(self, yak_id: str, text: str,
        point: Optional[str] = None,
    ):
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'Comment'),
            json={
                "operationName": "CreateComment",
                "query": "mutation CreateComment($input: CreateCommentInput!) {\n  createComment(input: $input) {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n    comment {\n      __typename\n      id\n      text\n      userColor\n      secondaryUserColor\n      userEmoji\n      createdAt\n      voteCount\n      myVote\n    }\n  }\n}",
                "variables": {
                    "input": {
                        "yakId": yak_id,
                        "text": text,
                        "point": point or self.location
                    }
                }
            }
        )
        response.raise_for_status()
        response_json = response.json()
        return response_json['data']['createComment']['comment']
    
    def reset_conversation_icon(self) -> dict[str, str]:
        response = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'ResetConversationIcon'),
            json={
                "operationName": "ResetConversationIcon",
                "query": """mutation ResetConversationIcon {\n  resetConversationIcon {\n    __typename\n    emoji\n    color\n    secondaryColor\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}""",
                "variables": None
            }
        )
        response.raise_for_status()
        response_json = response.json()
        
        return {
            'emoji': response_json['data']['resetConversationIcon']['emoji'],
            'color': response_json['data']['resetConversationIcon']['color'],
            'secondaryColor': response_json['data']['resetConversationIcon']['secondaryColor']
        }
    
    def delete_yak(self, id: str):
        request = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'DeleteYak'),
            json={
                "operationName":"RemoveYak",
                "query":"mutation RemoveYak($input: RemoveYakInput!) {\n  removeYak(input: $input) {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}",
                "variables":{
                    "input":{
                        "id":id
                    }
                }
            }
        )
        request.raise_for_status()
        response_json = request.json()
        print(response_json)
    
    def delete_comment(self, id: str):
        request = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'DeleteComment'),
            json={
                "operationName":"RemoveComment",
                "query":"mutation RemoveComment($input: RemoveCommentInput!) {\n  removeComment(input: $input) {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}",
                "variables":{
                    "input":{
                        "id":id
                    }
                }
            }
        )
        request.raise_for_status()
        response_json = request.json()
        print(response_json)
    
    
    
    def me(self):
        # {"operationName":"GetMe","query":"query GetMe {\n  me {\n    __typename\n    completedTutorial\n    emoji\n    color\n    secondaryColor\n    yakarmaScore\n  }\n}","variables":null}
        request = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('query', 'GetMe'),
            json={
                "operationName":"GetMe",
                "query":"""query GetMe {
                    me {
                        __typename
                        username
                        completedTutorial
                        emoji
                        color
                        secondaryColor
                        yakarmaScore
                        muteDetails {
                            __typename
                            isMuted
                            expiration
                            instance
                            text
                        }
                    }
                }""",
                "variables":None
            }
        )
        request.raise_for_status()
        response_json = request.json()
        
        return response_json['data']['me']
    
    def get_dms(self):
        pass
    
    def unblock(self):
        request = requests.post(
            'https://api.yikyak.com/graphql/',
            headers=self.request_headers('mutation', 'UnblockAll'),
            json= {
                "operationName":"UnblockAll",
                "query":"mutation UnblockAll {\n  unblockAll {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}",
                "variables":None
            }
        )
        request.raise_for_status()
        response_json = request.json()
        print(response_json)
            

# TODO:
# updateYak (UpdateYakInput!)
# updateMe (UpdateMeInput!)
# {"operationName":"GetMe","query":"query GetMe {\n  me {\n    __typename\n    completedTutorial\n    emoji\n    color\n    secondaryColor\n    yakarmaScore\n  }\n}","variables":null}
# {"operationName":"ResetConversationIcon","query":"mutation ResetConversationIcon {\n  resetConversationIcon {\n    __typename\n    emoji\n    color\n    secondaryColor\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}","variables":null}
# {"operationName":"isMuted","query":"query isMuted {\n  me {\n    __typename\n    muteDetails {\n      __typename\n      isMuted\n      expiration\n      instance\n      text\n    }\n  }\n}","variables":null}
# {"operationName":"UnblockAll","query":"mutation UnblockAll {\n  unblockAll {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}","variables":null}
# {"operationName":"Vote","query":"mutation Vote($input: VoteInput!) {\n  vote(input: $input) {\n    __typename\n    errors {\n      __typename\n      code\n      field\n      message\n    }\n  }\n}","variables":{"input":{"instance":"","vote":"UP"}}}

def main():
    client = YikYakClient(
        refresh_token="REDACTED",
        location=( 0.0, 0.0 )
    )
    
    print(*client.posts(100))

if __name__ == '__main__': main()