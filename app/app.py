# -*- coding: utf-8 -*-
import os
import glob
from logging import getLogger, config, StreamHandler, DEBUG
import settings
import json
import MeCab
from difflib import SequenceMatcher 

import sys
sys.path.append('./')
from commentutil import NGCommentKeyEnum, CommentTypeEnum 
from util import LogUtil

logger = getLogger(__name__)
log_conf = LogUtil.get_log_conf('./log_config.json')
config.dictConfig(log_conf)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

NG_PATTERN_DIR = './input/ng_pattern/**'

# envのキーを読み込む。
VIDEO_ID = settings.ENV_DIC['video_id']

# 辞書ファイルパス
DIC_PATH = ' -d /usr/local/mecab/lib/mecab/dic/mecab-ipadic-neologd'

# NGパターンとの突合結果
NG_RESULT_KEYS = ["pattern","similarity"]
INDEX_NG_RESULT_PATTERN = 0
INDEX_NG_RESULT_SIMILARITY = 1

# 類似度閾値
SIMILARITY_THRESHOLD = 0.8

NG_FLG_KEY = 'ng_flg'
NG_INFO_KEY = 'ng_info'

OUTPUT_DIR_ALL = './output/all/'
OUTPUT_DIR_NG_CHANNEL = './output/ng_channel/'
OUTPUT_DIR_NG_MESSAGES = './output/ng_message/'

def get_ng_patterns():
  """
  NGパターン一覧を読み込む
  
  Parameters:
  ----
  なし
  
  Returns:
  ----
  ng_pattern : dict
    key : string
      ファイルパス
    value : string
      ファイル内容（形態素解析結果）
  """
  
  ng_pattern = {}
  for file in [p for p in glob.glob(NG_PATTERN_DIR , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
    with open(file) as f:
      ng_pattern[file] = f.read()
  return ng_pattern  

def get_live_comments(video_id):
  """
  指定された動画IDのコメント一覧を読み込んでマージする。
  コメントjsonのうち、items配列だけを取得し、['items']['id']をキーとしたdict型を返す。  
  
  Parameters:
  ----
  video_id : string
    動画ID。
    input/comment/video_id配下のjsonを取得する。
  
  Returns:
  ----
  live_comments : dict
    key : string
      コメントID。
      ['items']['id']をキーとする。
    value : json
      コメントIDに紐づくjson
  """
  INPUT_COMMENT_PATH = './input/comment/' + video_id + '/**'
  live_comments = {}
  for file in [p for p in glob.glob(INPUT_COMMENT_PATH , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
    with open(file, mode='r') as f:
      comments = json.load(f)
      # コメント本体(items配下)だけほしい。
      for comment in comments['items']:
        comment_id = comment['id']
        live_comments[comment_id] = comment;
  return live_comments

def morphological_analysis(live_comments):
  """
  コメントを形態素解析する。
  get_live_comments関数の結果を引数にとり、同じキーのdict型に形態素解析結果を設定して返す。
  
  Parameters:
  ---- 
  live_comments : dict
    get_live_comments(string)の戻り値を想定する。
    key : string
      コメントID。
    value : json
      コメントIDに紐づくjson
    
  Returns:
  ----
  morphological_analysis_result : dict
    key : string
      コメントID
    value : string
      コメントの形態素解析結果。
      対象のコメントはENV_KEYを使用して取得する。（GoogleAPIが返してくるjsonがコメントの種類によってキーが異なる。）
  """
  
  morphological_analysis_result = {}
  for key in live_comments:
    SNIPPET = 'snippet'
    
    # ['snippet']['type']はチャットの種類(superChatEvent, superStickerEvent, textMessageEvent)を持っている。
    type = str(live_comments[key][SNIPPET]['type'])
    try:
      commentTypeEnum = CommentTypeEnum.value_of(type)
      commentKeys = commentTypeEnum.get_keys();
      tmp = live_comments[key][SNIPPET]
      logger.info("comment_id:{} , type:{}".format(key, type))

      for commentKey in commentKeys:
        # コメントを取得する
        if commentKey in tmp:
          tmp = tmp[commentKey]
        else:
          # superChatはコメントなしでも打てる。コメントなしで打った場合はjsonにキーが出力されない。
          tmp = ''
          break
      # 形態素解析結果取得
      morphological_analysis_result[key] = mplg(tmp)
    except ValueError:
      pass

  return morphological_analysis_result

def mplg(text):
  """ 形態素解析を行う。
  """
  m = MeCab.Tagger(DIC_PATH)
  soup = m.parse (text)
  return soup

def get_ng_chat_id(mplg_results, ng_pattern, threshold):
  """
  NGパターンに引っかかったコメントIDと、どのパターンに引っかかったかを返す。
  
  Parameters:
  ----
  mplg_results : dict
    morphological_analysis(dict)の戻り値。
  ng_patterns : dict
    get_ng_patterns()の戻り値。
  threshold : float
    類似度の閾値。
    コメントの形態素解析結果と、NGパターンの形態素解析結果がの値より大きい場合、一致していると判断する。
  
  Returns:
  ----
  ng_comments : dict
    key : string
      コメントID。
    value : list
      [ng_patternのキー,類似度]
  
  """
  logger.info("threshold: {}".format(threshold))
  ng_comments = {}
  for comment_key in mplg_results:
    mplg_result = mplg_results[comment_key]
    for ng_key in ng_pattern:
      similarity = SequenceMatcher(
        None,mplg_result,ng_pattern[ng_key]).ratio()
      logger.info("comment_id:{} , ng_key:{} , similarity:{}".format(comment_key, ng_key, similarity))
      if similarity > threshold:
        ng_comments[comment_key] = {
          NG_RESULT_KEYS[INDEX_NG_RESULT_PATTERN]: ng_key,
          NG_RESULT_KEYS[INDEX_NG_RESULT_SIMILARITY]: similarity
        }
      break
  return ng_comments

def merge_ng_comments(comment_dict, ng_comment_dict):
  """
  コメントにNG情報を付与する
  
  Parameters:
  ----
  comment_dict : dict
    get_live_comments(string)の戻り値
    key : string
      コメントID
    value : json
      コメント

  ng_comment_dict : dict
    get_ng_chat_id(dict, dict, float)の戻り値
    key : string
      コメントID。comment_dictと同値。
    value : list
      [ng_patternのキー,類似度]
      
  Returns:
  ----
  return_comment_list : list[json]
    コメントの配列
  ng_channel : list[string]
    NGユーザのチャンネル
  ng_comments : list[json]
    NGコメント一覧
  """
    
  return_comment_list = []
  ng_channels = []
  ng_comments = []

  for key in comment_dict:
    comment_info = comment_dict[key]
    if key in ng_comment_dict:
      comment_info[NG_FLG_KEY] = True
      comment_info[NG_INFO_KEY] = ng_comment_dict[key]
      
      # TODO : もうちょっとなんとかならんか
      ID = NGCommentKeyEnum.ID.get_ng_key()
      CHANNEL_ID = NGCommentKeyEnum.CHANNEL_ID.get_ng_key()
      DISPLAY_NAME = NGCommentKeyEnum.DISPLAY_NAME.get_ng_key()
      DISPLAY_MESSAGE = NGCommentKeyEnum.DISPLAY_MESSAGE.get_ng_key()

      ID_ORIGIN = NGCommentKeyEnum.ID.get_origin_key()
      CHANNEL_ID_ORIGIN = NGCommentKeyEnum.CHANNEL_ID.get_origin_key()
      DISPLAY_NAME_ORIGIN = NGCommentKeyEnum.DISPLAY_NAME.get_origin_key()
      DISPLAY_MESSAGE_ORIGIN = NGCommentKeyEnum.DISPLAY_MESSAGE.get_origin_key()
      ng_comments.append({
        ID :              comment_info[ID_ORIGIN[0]],
        CHANNEL_ID :      comment_info[CHANNEL_ID[0]][CHANNEL_ID[1]],
        DISPLAY_NAME :    comment_info[DISPLAY_NAME_ORIGIN[0]][DISPLAY_NAME_ORIGIN[1]],
        DISPLAY_MESSAGE : comment_info[DISPLAY_MESSAGE_ORIGIN[0]][DISPLAY_MESSAGE_ORIGIN[1]]
      })
      
      ng_channel = comment_dict[key]['authorDetails']['channelUrl']
      if ng_channel not in ng_channels:
        ng_channels.append(ng_channel)
    else:
      comment_info[NG_FLG_KEY] = False

    return_comment_list.append(comment_info)
  return return_comment_list, ng_channels, ng_comments

if __name__ == '__main__':
  # NGパターンの読み込み
  ng_pattern = get_ng_patterns()
  logger.info("ng_pattern len : {} ".format(len(ng_pattern)))

  # 指定されたVIDEO_IDのコメントファイル読み込み
  logger.info('VIDEO_ID : {}'.format(VIDEO_ID))
  live_comment_dict = get_live_comments(VIDEO_ID)
  logger.info("live_comment_dict len : {} ".format(len(live_comment_dict)))

  # コメントの形態素解析
  morphological_analysis_result_dict = morphological_analysis(live_comment_dict)
  logger.info("morphological_analysis_result_dict len : {} ".format(len(morphological_analysis_result_dict)))
  
  # 形態素解析したコメントとNGパターンの突合
  ng_comments = get_ng_chat_id(morphological_analysis_result_dict, ng_pattern, SIMILARITY_THRESHOLD)
  logger.info("ng_comments len : {} ".format(len(ng_comments)))
  
  # 元のコメントjsonにNGフラグを設定
  # NGユーザのチャンネル一覧を取得
  # NGコメントのみを取得
  comments_ng_merged, ng_channels, ng_comments = merge_ng_comments(live_comment_dict, ng_comments)
  logger.info("comments_ng_merged len : {} ".format(len(comments_ng_merged)))
  logger.info("ng_channels len : {} ".format(len(ng_channels)))
  logger.info("ng_comments len : {} ".format(len(ng_comments)))
  
  # NGフラグを設定したコメントのjsonを出力
  with open(OUTPUT_DIR_ALL + 'result_' + VIDEO_ID + '.json' , mode='w') as f:
    f.write(json.dumps(comments_ng_merged))
  
  # NGに設定したユーザのチャンネルURLを出力
  with open(OUTPUT_DIR_NG_CHANNEL + 'result_' + VIDEO_ID + '.txt' , mode='w') as f:
    if len(ng_channels) != 0:
      f.write(ng_channels)
    else:
      pass
  
  # NGに設定したコメントのみを出力
  with open(OUTPUT_DIR_NG_MESSAGES + 'result_' + VIDEO_ID + '.json' , mode='w') as f:
    f.write(json.dumps(ng_comments))
