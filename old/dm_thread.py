from dataclasses import dataclass
import datetime
from typing import Any, Literal, Optional, Self


@dataclass
class Participant:
	id: str
	emoji: str
	color: str
	secondary_color: str
	is_op: bool
	is_self: bool
	is_reported: bool
	has_unread_messages: bool
	
	@classmethod
	def from_json(cls, json: dict[str, Any]) -> Self:
		return cls(
			id=json['id'],
			emoji=json['emoji'],
			color=json['color'],
			secondary_color=json['secondaryColor'],
			is_op=json['isOp'],
			is_self=json['isSelf'],
			is_reported=json['isReported'],
			has_unread_messages=json['hasUnreadMessages'],
		)

@dataclass
class Message:
	id: str
	text: str
	is_mine: bool
	is_op: bool
	participant_id: str
	created_at: datetime.datetime
	
	@classmethod
	def from_json(cls, json: dict[str, Any]) -> Self:
		raise NotImplementedError(json)

@dataclass
class Thread:
	id: str
	title: str
	is_disabled: bool
	is_draft: bool
	participants: list[Participant]
	created_at: datetime.datetime
	last_active_at: datetime.datetime
	instance: str
	instance_display_type: Literal["Comment", "Yak"]
	messages: Optional[list[Message]]
	
	@classmethod
	def from_json(cls, json: dict[str, Any]) -> Self:
		assert json['__typename'] == 'Thread'
		return cls(
			id=json['id'],
			title=json['title'],
			is_disabled=json['isDisabled'],
			is_draft=json['isDraft'],
			participants=[
				Participant.from_json(edge['node']) 
				for edge in json['participants']['edges']
			],
			created_at=datetime.datetime.fromisoformat(json['createdAt']),
			last_active_at=datetime.datetime.fromisoformat(json['lastActiveAt']),
			instance=json['instance'],
			instance_display_type=json['instanceDisplayType'],
			messages = [
				Message.from_json(edge['node'])
				for edge in json['messages']['edges']
			] if json.get('messages') else None,
		)

