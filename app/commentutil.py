# -*- coding: utf-8 -*-
from enum import Enum

class NGCommentKeyEnum(Enum):
  ID = ('id', ['id'])
  CHANNEL_ID = ('channelId', ['authorDetails', 'channelId'])
  DISPLAY_NAME = ('displayName', ['authorDetails', 'displayName'])
  DISPLAY_MESSAGE = ('displayMessage' , ['snippet', 'displayMessage'])

  def __init__(self, ng_key, origin_key):
    self.ng_key = ng_key
    self.origin_key = origin_key
    # 変数名にvalueは使えない。

  def get_ng_key(self):
    return self.ng_key;

  def get_origin_key(self):
    return self.origin_key;

  @classmethod
  def value_of(cls, ng_key):
    for e in NGCommentKeyEnum:
      if e.get_origin_message_key() == ng_key:
        return e
    raise ValueError('{} is not found.'.format(ng_key))

class CommentTypeEnum(Enum):  
  textMessageEvent = (
    "textMessageEvent",
    ["textMessageDetails","messageText"]
  ) 

  superChatEvent = (
    "superChatEvent",
    ["superChatDetails","userComment"]
  )
  
  superStickerEvent = (
    "superStickerEvent",
    ["superStickerDetails","superStickerMetadata", "superStickerMetadata"]
  )

  def __init__(self, type, keys):
    self.type = type
    self.keys = keys
    # 変数名にvalueは使えない。

  def get_type(self):
    return self.type;

  def get_keys(self):
    return self.keys;

  @classmethod
  def value_of(cls, target_value):
    for e in CommentTypeEnum:
      if e.get_type() == target_value:
        return e
    raise ValueError('{} is not found.'.format(target_value))
    
