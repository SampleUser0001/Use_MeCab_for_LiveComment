# -*- coding: utf-8 -*-
from enum import Enum

class CommentEnum(Enum):  
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
    for e in CommentEnum:
      if e.get_type() == target_value:
        return e
    raise ValueError('{} is not found.'.format(target_value))
    
