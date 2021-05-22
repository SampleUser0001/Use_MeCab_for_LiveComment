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
  
  newSponsorEvent = (
    "newSponsorEvent",
    []
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
    raise ValueError("{} is not found.".format(target_value))
    
  @classmethod
  def get_comment(cls, comment_dict):
    """
    コメントdictからメッセージを取得する。
    
    Parameters:
    ----
    comment_dict : dict
      コメント情報
    
    Returns:
    ----
    comment : str
      コメント
    """
    # ['snippet']['type']はチャットの種類(superChatEvent, superStickerEvent, textMessageEvent)を持っている。
    type = str(comment_dict['snippet']['type'])
    commentTypeEnum = CommentTypeEnum.value_of(type)
    commentKeys = commentTypeEnum.get_keys();
    tmp = comment_dict['snippet']

    if commentTypeEnum == CommentTypeEnum.newSponsorEvent:
      # メンバーシップ加入コメントは何も出力されない。
      return ''
    else:
      for commentKey in commentKeys:
        # コメントを取得する
        if commentKey in tmp:
          tmp = tmp[commentKey]
        else:
          # superChatはコメントなしでも打てる。コメントなしで打った場合はjsonにキーが出力されない。
          tmp = ' '
          break
      return tmp

# TODO YoutubeCommentJsonへのアクセスをしやすくする。
# class CommonCommentKeyEnum(Enum):
#   kind=(["kind"])
#   etag=(["etag"])
#   id=(["id"])
#   snippet=(["snippet"])
#   type=(["snippet","type"])
#   liveChatId=(["snippet","liveChatId"])
#   authorChannelId=(["snippet","authorChannelId"])
#   publishedAt=(["snippet","publishedAt"])
#   hasDisplayContent=(["snippet","hasDisplayContent"])
#   displayMessage=(["snippet"])
#   
#   def __init__(self, keys):
#     self.keys = keys

