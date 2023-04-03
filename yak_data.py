from __future__ import annotations
import datetime
from functools import cache
from typing import TYPE_CHECKING, Callable, Optional, Protocol, TypeAlias, TypeVar, TypedDict

import matplotlib.pyplot as plt
from comment import Comment
from yak import Yak

from yak_archive import YakArchive
from yak_archive import Archive # type: ignore (for pickle purposes)

import nltk


if TYPE_CHECKING:
	class TotalYakData(TypedDict):
		posts: int | float
		comments: int | float
		total: int | float
	
	class UserActivity(TypedDict):
		posts: int
		comments: int
		total: int
		post_upvotes: int
		comment_upvotes: int
		total_upvotes: int

	_T_contra = TypeVar("_T_contra", contravariant=True)
	class SupportsDunderLT(Protocol[_T_contra]):
		def __lt__(self, __other: _T_contra) -> bool: ...
	class SupportsDunderGT(Protocol[_T_contra]):
		def __gt__(self, __other: _T_contra) -> bool: ...
	SupportsRichComparison: TypeAlias = SupportsDunderGT | SupportsDunderLT


TIMEZONE = datetime.timezone(datetime.timedelta(0,-4*3600))
_ARCHIVE_START = datetime.datetime(2022, 10, 13, 0, 0, 0, tzinfo=TIMEZONE)


def avg_yaks_per_hour(archive: YakArchive,
	user_id: Optional[str] = None,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
	show_graph: bool = False,
	graph_name: Optional[str] = None
) -> dict[int, float]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	hour_counts = {} # type: dict[int, TotalYakData]
	
	for yak, comments in archive:
		if user_id is None or yak.user_id == user_id:
			# NOTE: a micro optimization could be made here by continuing 
			#       if yak.created_at > end_time because the comments must 
			#       be made after the post, but this is fine for now
			if start_time <= yak.created_at <= end_time:
				hour = yak.created_at.astimezone(TIMEZONE).hour
				hour_counts[hour] = hour_counts.get(hour, {'posts': 0, 'comments': 0, 'total': 0})
				hour_counts[hour]['posts'] += 1
				hour_counts[hour]['total'] += 1
		
		for comment in comments:
			if user_id is None or comment.user_id == user_id:
				if start_time <= comment.created_at <= end_time:
					hour = comment.created_at.astimezone(TIMEZONE).hour
					hour_counts[hour] = hour_counts.get(hour, {'posts': 0, 'comments': 0, 'total': 0})
					hour_counts[hour]['comments'] += 1
					hour_counts[hour]['total'] += 1
	
	# convert hour counts into average yaks per hour
	# (divide by number of same hours since start time)
	num_days = (datetime.datetime.now(TIMEZONE) - start_time).days
	
	average_yaks_per_hour = {}
	for hour, count in hour_counts.items():
		# how many times this hour has occurred since start time
		hours_passed = num_days + (hour > datetime.datetime.now(TIMEZONE).hour)
		if hours_passed == 0:
			hours_passed = 1
		average_yaks_per_hour[hour] = {
			'posts': count['posts'] / hours_passed,
			'comments': count['comments'] / hours_passed,
			'total': count['total'] / hours_passed
		}
	
	if show_graph:
		# show a stacked bar graph of the average yaks per hour
		_, ax = plt.subplots()
		hours = list(average_yaks_per_hour.keys())
		
		posts = [average_yaks_per_hour[hour]['posts'] for hour in hours]
		comments = [average_yaks_per_hour[hour]['comments'] for hour in hours]
		
		ax.bar(hours, posts, label='Posts', color='tab:blue')
		ax.bar(hours, comments, bottom=posts, label='Comments', color='tab:green')
		
		# labels
		plt.title(f"Average Yaks+Comments Per Hour by {user_id and (graph_name or user_id) or 'All Users'}")
		plt.xlabel("Hour of Day")
		plt.ylabel(f"Average Yaks+Comments")
		plt.legend()
		
		# x axis scale (0-23) and ticks every 6
		plt.xticks(range(0, 24, 6))
		
		plt.show()
	
	return average_yaks_per_hour

def most_common_words(archive: YakArchive,
	user_id: Optional[str] = None,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
) -> dict[str, int]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	word_counts = {}
	# WORD_SPLIT_REGEX = r"[^a-zA-Z0-9'’]+"
	
	def filtered(text: str) -> str:
		return text.replace('’', "'") \
		.replace("“", '"') \
		.replace("”", '"') \
		.lower() \
		#.replace("'", '')
	
	for yak, comments in archive:
		if user_id is None or yak.user_id == user_id:
			if start_time <= yak.created_at <= end_time:
				for word in nltk.word_tokenize(filtered(yak.text)):
					word_counts[filtered(word)] = word_counts.get(filtered(word), 0) + 1
		
		for comment in comments:
			if user_id is None or comment.user_id == user_id:
				if start_time <= comment.created_at <= end_time:
					for word in nltk.word_tokenize(filtered(comment.text)):
						word_counts[filtered(word)] = word_counts.get(filtered(word), 0) + 1
	
	word_counts.pop('', None) # remove any random empty strings
	
	from nltk.corpus import stopwords
	for w in stopwords.words('english'):
		word_counts.pop(w, None) # remove stopwords
	
	return word_counts

def most_active_users(archive: YakArchive,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
	sort_by: Optional[Callable[[UserActivity], SupportsRichComparison]] = None,
) -> dict[str, UserActivity]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	user_activity = {} # type: dict[str, UserActivity]
	
	for yak, comments in archive:
		if start_time <= yak.created_at <= end_time:
			if yak.user_id is None: continue
			user_activity[yak.user_id] = user_activity.get(yak.user_id, {'posts': 0, 'comments': 0, 'total': 0, 'post_upvotes': 0, 'comment_upvotes': 0, 'total_upvotes': 0})
			user_activity[yak.user_id]['posts'] += 1
			user_activity[yak.user_id]['total'] += 1
			user_activity[yak.user_id]['post_upvotes'] += yak.vote_count
			user_activity[yak.user_id]['total_upvotes'] += yak.vote_count
		
		for comment in comments:
			if start_time <= comment.created_at <= end_time:
				if comment.user_id is None: continue
				user_activity[comment.user_id] = user_activity.get(comment.user_id, {'posts': 0, 'comments': 0, 'total': 0, 'post_upvotes': 0, 'comment_upvotes': 0, 'total_upvotes': 0})
				user_activity[comment.user_id]['comments'] += 1
				user_activity[comment.user_id]['total'] += 1
				user_activity[comment.user_id]['comment_upvotes'] += comment.vote_count
				user_activity[comment.user_id]['total_upvotes'] += comment.vote_count
	
	sort_by = sort_by or (lambda activity: activity['total']) # sort by total yaks by default
	
	# sort and return the user activity dict
	return dict(sorted(user_activity.items(), key=lambda x:sort_by(x[1]), reverse=True))

def common_coupled_users(archive: YakArchive,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
	include_self: bool = False,
	repeat_comments_per_thread: bool = True,
	only_anonymous: bool = True,
) -> dict[tuple[str, str], int]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	coupled_users = {} # type: dict[tuple[str, str], int]
	
	for yak, comments in archive:
		if start_time <= yak.created_at <= end_time:
			if yak.user_id is None: continue
			if only_anonymous and not yak.is_incognito: continue
			seen_users = set()
			for comment in comments:
				if comment.user_id is None: continue
				if not include_self and comment.user_id == yak.user_id: continue
				if not repeat_comments_per_thread:
					if comment.user_id in seen_users: continue
					seen_users.add(comment.user_id)
				coupled_users[(yak.user_id, comment.user_id)] = coupled_users.get((yak.user_id, comment.user_id), 0) + 1
	
	return dict(sorted(coupled_users.items(), key=lambda x:x[1], reverse=True))

@cache
def get_emojis(archive: YakArchive,
	user_id: str,
	percentage_cutoff: float = 0.0,
) -> list[str]:
	COLOR_CODES = {
		('#00CBFE', '#00CBFE'): "LB",
		('#00CBFE', '#0D13D5'): "GB", # yes
		('#15FF46', '#15FF46'): "G",
		('#15FF46', '#3FC0FF'): "G2", # yes
		('#5857FF', '#5857FF'): "PB", 
		('#6EFFE6', '#6EFFE6'): "CY",
		('#76FFE7', '#00A4FF'): "GC", # yes
		('#8483FF', '#5857FF'): "GP", # yes
		('#927AFF', '#927AFF'): "PW",
		('#C0FF2D', '#C0FF2D'): "YG",
		('#C16AFF', '#C16AFF'): "P",
		('#C38637', '#C38637'): "BR",
		('#D9FB8A', '#B1FD00'): "GG", # yes
		('#E9FDFB', '#E9FDFB'): "W",  
		('#FA81FF', '#722DFF'): "LP", # yes
		('#FA81FF', '#FF1885'): "PI", # yes
		('#FF7373', '#FF7373'): "CO",
		('#FF7A7A', '#FF7A7A'): "CO",
		('#FF9541', '#FF9541'): "O",
		('#FFA236', '#FF3232'): "GO", # yes
		('#FFA953', '#FFA953'): "LO",
		('#FFD38C', '#C38737'): "GT", # yes
		('#FFD38C', '#FFD38C'): "T",
		('#FFD815', '#FFD815'): "Y",
		('#FFF680', '#FFDA00'): "GY", # yes
		('#FFF98D', '#FFF98D'): "LY",
	}
	
	result = {}
	for _, comments in archive:
		for comment in comments:
			if comment.user_id == user_id and comment.user_emoji not in (None, 'OP'):
				emoji = COLOR_CODES.get((comment.user_color, comment.secondary_user_color),'??')+comment.user_emoji # type: ignore
				result[emoji] = result.get(emoji, 0) + 1
	
	# return the emojis sorted by count
	return [emoji for emoji, count in sorted(result.items(), key=lambda x:x[1], reverse=True) if count/sum(result.values()) > percentage_cutoff]

def yaks_by_user(archive: YakArchive,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
) -> dict[str, list[Yak]]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	yaks_by_user = {} # type: dict[str, list[Yak]]
	
	for yak, _ in archive:
		if start_time <= yak.created_at <= end_time:
			if yak.user_id is None: continue
			yaks_by_user[yak.user_id] = yaks_by_user.get(yak.user_id, [])
			yaks_by_user[yak.user_id].append(yak)
	
	return yaks_by_user

def comments_by_user(archive: YakArchive,
	start_time: datetime.datetime = _ARCHIVE_START,
	end_time: Optional[datetime.datetime] = None,
) -> dict[str, list[Comment]]:
	end_time = end_time or datetime.datetime.now(tz=TIMEZONE)
	
	comments_by_user = {} # type: dict[str, list[Comment]]
	
	for _, comments in archive:
		for comment in comments:
			if start_time <= comment.created_at <= end_time:
				if comment.user_id is None: continue
				comments_by_user[comment.user_id] = comments_by_user.get(comment.user_id, [])
				comments_by_user[comment.user_id].append(comment)
	
	return comments_by_user
