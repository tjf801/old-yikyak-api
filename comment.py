from dataclasses import dataclass
import datetime
from typing import Any, Literal, Optional


@dataclass
class Comment:
	id: str
	text: str
	created_at: datetime.datetime
	user_emoji: str | Literal["OP"]
	user_color: Optional[str]
	secondary_user_color: Optional[str]
	is_mine: bool
	is_reported: bool
	vote_count: int
	my_vote: Literal["UP", "DOWN", "NONE"]
	
	user_id: str | None
	
	@classmethod
	def from_json(cls, comment_json: dict[str, Any]) -> 'Comment':
		return cls(
			id=comment_json["id"],
			text=comment_json["text"],
			created_at=datetime.datetime.fromisoformat(comment_json["createdAt"]),
			user_emoji=comment_json["userEmoji"] or "OP",
			user_color=comment_json["userColor"] or None,
			secondary_user_color=comment_json["secondaryUserColor"] or None,
			is_mine=comment_json["isMine"],
			is_reported=comment_json["isReported"],
			vote_count=comment_json["voteCount"],
			my_vote=comment_json["myVote"],
			user_id=comment_json.get("userId"),
		)
	
	def __hash__(self):
		return hash(self.id)
	
	def __eq__(self, other: object) -> bool:
		if isinstance(other, Comment):
			return self.id == other.id
		return False