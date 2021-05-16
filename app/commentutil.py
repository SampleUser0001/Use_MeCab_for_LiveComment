# -*- coding: utf-8 -*-
from enum import Enum

class CommentEnum(Enum):
  textMessageEvent = {
    "key":"textMessageEvent",
    "detailsKey":"textMessageDetails",
    "commentKey":"messageText"
  }
  superChatEvent = {
    "key":"superChatEvent",
    "detailsKey":"superChatDetails",
    "commentKey":"userComment" 
  }
  superStickerEvent = {
    "key":"superStickerEvent",
    "detailsKey":"superStickerDetails",
    "metaKey":"superStickerMetadata", 
    "commentKey":"superStickerMetadata"
  }
  
  @classmethod
  def value_of(cls, target_value):
    for e in CommentEnum:
      if e['key'] == target_value:
        return e
    raise ValueError('{} is not found.'.format(target_value))
    
  @classmethod
  def get_comment(cls, snippet):
    keys = CommentEnum.value_of(snippet[''])