import datetime
from dataclasses import dataclass
from typing import Literal, Optional


@dataclass
class Yak:
	id: str
	
	video_id: str | None
	video_playback_dash_url: str | None
	video_playback_hls_url: str | None
	video_download_mp4_url: str | None
	video_thumbnail_url: str | None
	video_state: Literal["NONE", "READY", "PROCESSING", "FAILED"]
	
	text: str
	
	user_emoji: Optional[str]
	user_color: Optional[Literal['#00CBFE', '#15FF46', '#5857FF', '#6EFFE6', '#76FFE7', '#8483FF', '#927AFF', '#C0FF2D', '#C16AFF', '#C38637', '#D9FB8A', '#E9FDFB', '#FA81FF', '#FF7373', '#FF7A7A', '#FF9541', '#FFA236', '#FFA953', '#FFD38C', '#FFD815', '#FFF680', '#FFF98D']]
	secondary_user_color: Optional[str]
	
	distance: int
	geohash: Optional[str]
	interest_areas: list[str]
	
	created_at: datetime.datetime
	
	comment_count: int
	vote_count: int
	
	is_incognito: bool
	is_mine: bool
	is_reported: bool
	
	my_vote: Literal["UP", "DOWN", "NONE"]
	
	user_id: str | None
	
	@classmethod
	def from_json(cls, yak_json, /) -> 'Yak':
		return cls(
			id=yak_json["id"],
			video_id=yak_json["videoId"] or None,
			video_playback_dash_url=yak_json["videoPlaybackDashUrl"] or None,
			video_playback_hls_url=yak_json["videoPlaybackHlsUrl"] or None,
			video_download_mp4_url=yak_json["videoDownloadMp4Url"] or None,
			video_thumbnail_url=yak_json["videoThumbnailUrl"] or None,
			video_state=yak_json["videoState"],
			text=yak_json["text"],
			user_emoji=yak_json["userEmoji"] or None,
			user_color=yak_json["userColor"] or None,
			secondary_user_color=yak_json["secondaryUserColor"] or None,
			distance=yak_json["distance"],
			geohash=yak_json["geohash"] or None,
			interest_areas=yak_json["interestAreas"],
			created_at=datetime.datetime.fromisoformat(yak_json["createdAt"]),
			comment_count=yak_json["commentCount"],
			vote_count=yak_json["voteCount"],
			is_incognito=yak_json["isIncognito"],
			is_mine=yak_json["isMine"],
			is_reported=yak_json["isReported"],
			my_vote=yak_json["myVote"],
			user_id=yak_json.get("userId"),
		)
	
	def __hash__(self) -> int:
		return hash(self.id)
	
	def __eq__(self, other: object) -> bool:
		if isinstance(other, Yak):
			return self.id == other.id
		return False
	
	def __format__(self, format_spec: str) -> str:
		if format_spec == "s":
			return self.text
		return super().__format__(format_spec)