from __future__ import annotations

from dataclasses import dataclass
import os
import pickle
from typing import Generator, Iterable, Optional

from comment import Comment
from yak import Yak

@dataclass
class Archive:
	yaks: list[Yak]
	comments: dict[str, list[Comment]]

class YakArchive:
	def __init__(self, path: str):
		self.path = path
		
		if os.path.exists(self.path):
			with open(self.path, 'rb+') as file_handle:
				self.archive = pickle.load(file_handle)
		else:
			# print("Archive not found, creating new archive")
			self.archive = Archive([], {})
		
		print(len(self.archive.yaks), "yaks loaded from archive")
		
		# O(1) lookup for yaks by id
		self.yak_hash = {yak.id: yak for yak in self.archive.yaks}
	
	def save(self):
		self.archive.yaks.sort(key=lambda yak: yak.created_at, reverse=True)
		
		with open(self.path, 'wb+') as file_handle:
			pickle.dump(self.archive, file_handle)
			file_handle.flush()
		
		print(f"Archive saved (length {len(self.archive.yaks)})")
	
	def __enter__(self):
		return self
	
	def __exit__(self, exc_type, exc_value, traceback):
		self.save()
		return False
	
	def add_yak(self, yak: Yak):
		if yak not in self.archive.yaks:
			# this isnt in chronological order, but since we sort the yaks by 
			# date when we close the archive, it doesnt matter
			self.archive.yaks.append(yak)
			self.yak_hash[yak.id] = yak
		else:
			# update the yak if it already exists
			self.yak_hash[yak.id] = yak
			self.archive.yaks[self.archive.yaks.index(yak)] = yak
	
	def add_comments(self, yak_id: str, comments: Iterable[Comment]):
		for comment in comments:
			if comment not in self.archive.comments.get(yak_id, []):
				self.archive.comments.setdefault(yak_id, []).append(comment)
			else:
				self.archive.comments[yak_id][self.archive.comments[yak_id].index(comment)] = comment
	
	def __iter__(self):
		return self.get_yaks()
	
	def __len__(self):
		return len(self.archive.yaks)
	
	def __reversed__(self):
		for yak in reversed(self.archive.yaks):
			yield yak, self.archive.comments.get(yak.id, [])
	
	def get_yaks(self) -> Generator[tuple[Yak, list[Comment]], None, None]:
		for yak in self.archive.yaks:
			yield yak, self.archive.comments.get(yak.id, [])
	
	def get_yak(self, yak_id: str) -> Optional[tuple[Yak, list[Comment]]]:
		yak = self.yak_hash.get(yak_id)
		if yak:
			return yak, self.archive.comments.get(yak.id, [])
		return None
