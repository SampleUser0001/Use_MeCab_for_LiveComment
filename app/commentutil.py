# -*- coding: utf-8 -*-
from enum import Enum

class CommentEnum(Enum):
  ENUM_KEY = "enumKey"
  COMMENT_KEY = "commentKey"
  
  textMessageEvent = {
    ENUM_KEY: "textMessageEvent",
    COMMENT_KEY: ["textMessageDetails","messageText"]
  }
  superChatEvent = {
    ENUM_KEY: "superChatEvent",
    COMMENT_KEY: ["superChatDetails","userComment"]
  }
  superStickerEvent = {
    ENUM_KEY: "superStickerEvent",
    COMMENT_KEY: [ "superStickerDetails","superStickerMetadata", "superStickerMetadata"]
  }
  
  @classmethod
  def value_of(cls, target_value):
    for e in CommentEnum:
      if e[CommentEnum.ENUM_KEY] == target_value:
        return e
    raise ValueError('{} is not found.'.format(target_value))
    
