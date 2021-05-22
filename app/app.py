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
NG_CHANNEL_DIR = './input/ng_channel/**'

# envのキーを読み込む。
VIDEO_ID = settings.ENV_DIC['video_id']

# 辞書ファイルパス
DIC_PATH = ' -d /usr/local/mecab/lib/mecab/dic/mecab-ipadic-neologd'

# NGパターンとの突合結果
NG_RESULT_KEYS = ["pattern","similarity"]
INDEX_NG_RESULT_PATTERN = 0
INDEX_NG_RESULT_SIMILARITY = 1

# 類似度閾値
SIMILARITY_THRESHOLD = 0.3

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
  ng_patterns : dict
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
      コメントID。['items']['id']で取得できた値。
    value : dict
      コメントIDに紐づくjson(Python上はdict)
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
  
def get_ng_channel():
  """
  NGチャンネル一覧を読み込む。
  
  Parameters:
  ----
  なし
  
  Returns:
  ----
  ng_channels: list
    NGチャンネル一覧
  """

  ng_channels = []
  for file in [p for p in glob.glob(NG_CHANNEL_DIR , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
    with open(file, mode='r') as f:
      for ng_channel in f.read().splitlines():
        # logger.debug("ng_channel: {}".format(ng_channel))
        ng_channels.append(ng_channel)
  return ng_channels
  
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
    value : dict
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
    # 形態素解析結果取得
    comment = CommentTypeEnum.get_comment(live_comments[key])    
    # logger.debug("comment : {}".format(comment))
    morphological_analysis_result[key] = mplg(comment)

  return morphological_analysis_result

def mplg(text):
  """ 形態素解析を行う。
  """
  m = MeCab.Tagger(DIC_PATH)
  soup = m.parse (text)
  return soup

def get_ng(live_comments, mplg_results, ng_patterns, threshold, ng_channels):
  """
  NGパターンに引っかかったコメントIDと、どのパターンに引っかかったかを返す。
  
  Parameters:
  ----
  live_comments : dict
    読み込んだコメント。
    get_live_comments(str)の戻り値。
  mplg_results : dict
    morphological_analysis(dict)の戻り値。
  ng_patterns : dict
    get_ng_patterns()の戻り値。
  threshold : float
    類似度の閾値。
    コメントの形態素解析結果と、NGパターンの形態素解析結果がの値より大きい場合、一致していると判断する。
  ng_channels : list
    NGチャンネルのリスト
    
  Returns:
  ----
  ng_comments : dict型。NG判定されたコメントを返す。
    key : コメントID
    value : dict {
      ng_channel (必須) : チャンネルURL
      ng_comment (任意) : {
        ng_pattern_key : ng_patternのキー, 
        similarity : 類似度
      } 
      ng_pattern (必須) : 配列。どのパターンで引っかかったか。 ["comment","channel"]
    }
  ng_channels : list
    NG判定したチャンネル一覧
  """
  logger.info("threshold: {}".format(threshold))
  logger.info("mplg_results len: {}".format(len(mplg_results)))
  logger.info("ng_patterns len: {}".format(len(ng_patterns)))
  logger.info("ng_channels len: {}".format(len(ng_channels)))

  # 戻り値
  return_ng_comments = {}
  return_ng_channels = []

  for comment_key in mplg_results:
    # logger.debug("comment_id:{}".format(comment_key))
    # logger.debug("{},{}".format(CommentTypeEnum.get_comment(live_comments[comment_key]), live_comments[comment_key]['authorDetails']['channelUrl']))
    # with open('./log/comment.csv', mode='a') as f:
    #   f.write("{},{}\n".format(CommentTypeEnum.get_comment(live_comments[comment_key]), live_comments[comment_key]['authorDetails']['channelUrl']))

    ng_comment = {}
    ng_pattern = []
    ng = False

    # 形態素解析結果から判断
    mplg_result = mplg_results[comment_key]
    for ng_key in ng_patterns:
      similarity = SequenceMatcher(
        None,mplg_result,ng_patterns[ng_key]).ratio()

      if similarity > threshold:
        logger.debug("comment_id:{}, ng_key:{}, similarity:{}".format(comment_key, ng_key, similarity))
        ng_comment['ng_comment'] = {
          NG_RESULT_KEYS[INDEX_NG_RESULT_PATTERN]: ng_key,
          NG_RESULT_KEYS[INDEX_NG_RESULT_SIMILARITY]: similarity
        }
        ng_pattern.append('comment')
        ng = True
        break

    # チャンネルURLから判断
    channel_url = live_comments[comment_key]['authorDetails']['channelUrl']
    if channel_url in ng_channels:
      ng = True
      ng_pattern.append('channel')

    # どちらかのチェックで引っかかった場合はコメントIDをキーに登録
    if ng:
      ng_comment['ng_channel'] = channel_url
      return_ng_comments[comment_key] = ng_comment
      if channel_url not in return_ng_channels:
        return_ng_channels.append(channel_url)
    
  return return_ng_comments, return_ng_channels

def merge_ng_comments(comments, ng_comments):
  """
  コメントにNG情報を付与する
  
  Parameters:
  ----
  comments : dict
    get_live_comments(string)の戻り値
    key : string
      コメントID
    value : json
      コメント

  ng_comments : dict型。NG判定されたコメントのdict。
    key : コメントID
    value : dict {
      ng_channel (必須) : チャンネルURL
      ng_comment (任意) : {
        ng_pattern_key : ng_patternのキー, 
        similarity : 類似度
      } 
      ng_pattern (必須) : 配列。どのパターンで引っかかったか。 ["comment","channel"]
    }
      
  Returns:
  ----
  return_comment_list : list[dict]
    コメントの配列。元のコメントに下記を追加する。
    ng_flg : True or False
    ng_info : dict {
      ng_channel (必須) : チャンネルURL
      ng_comment (任意) : {
        ng_pattern_key : ng_patternのキー, 
        similarity : 類似度
      } 
      ng_pattern (必須) : 配列。どのパターンで引っかかったか。 ["comment","channel"]
    }
  ng_only_comments : list[dict]
    NGコメント一覧
  """

  return_comment_list = []
  ng_only_comments = []

  for comment_id in comments:
    comment_info = comments[comment_id]
    if comment_id in ng_comments:
      comment_info[NG_FLG_KEY] = True
      comment_info[NG_INFO_KEY] = ng_comments[comment_id]
      
      # TODO : もうちょっとなんとかならんか
      ID = NGCommentKeyEnum.ID.get_ng_key()
      CHANNEL_ID = NGCommentKeyEnum.CHANNEL_ID.get_ng_key()
      DISPLAY_NAME = NGCommentKeyEnum.DISPLAY_NAME.get_ng_key()
      DISPLAY_MESSAGE = NGCommentKeyEnum.DISPLAY_MESSAGE.get_ng_key()

      ID_ORIGIN = NGCommentKeyEnum.ID.get_origin_key()
      CHANNEL_ID_ORIGIN = NGCommentKeyEnum.CHANNEL_ID.get_origin_key()
      DISPLAY_NAME_ORIGIN = NGCommentKeyEnum.DISPLAY_NAME.get_origin_key()
      DISPLAY_MESSAGE_ORIGIN = NGCommentKeyEnum.DISPLAY_MESSAGE.get_origin_key()

      ng_only_comments.append({
        ID :              comment_info[ID_ORIGIN[0]],
        CHANNEL_ID :      comment_info[CHANNEL_ID_ORIGIN[0]][CHANNEL_ID_ORIGIN[1]],
        DISPLAY_NAME :    comment_info[DISPLAY_NAME_ORIGIN[0]][DISPLAY_NAME_ORIGIN[1]],
        DISPLAY_MESSAGE : comment_info[DISPLAY_MESSAGE_ORIGIN[0]][DISPLAY_MESSAGE_ORIGIN[1]]
      })
      
    else:
      comment_info[NG_FLG_KEY] = False

    return_comment_list.append(comment_info)
  return return_comment_list, ng_only_comments

if __name__ == '__main__':
  # NGパターンの読み込み
  # dict
  #  key : string ファイルパス
  #  value : string ファイル内容（形態素解析結果）
  input_ng_patterns = get_ng_patterns()
  logger.info("input_ng_patterns len : {} ".format(len(input_ng_patterns)))
  
  # NGチャンネル一覧の読み込み
  # list : NGチャンネル一覧
  input_ng_channels = get_ng_channel()
  logger.info("input_ng_channels len : {} ".format(len(input_ng_channels)))

  # 指定されたVIDEO_IDのコメントファイル読み込み
  logger.info('VIDEO_ID : {}'.format(VIDEO_ID))
  # dict :
  #   key : string
  #     コメントID。['items']['id']で取得できた値。
  #   value : dict
  #     コメントIDに紐づくjson(Python上はdict)
  input_live_comments = get_live_comments(VIDEO_ID)
  logger.info("input_live_comments len : {} ".format(len(input_live_comments)))

  # コメントの形態素解析
  # dict :
  #   key : string
  #     コメントID。引数のkeyと同値。
  #   value : string
  #     コメントの形態素解析結果。
  mplg_results = morphological_analysis(input_live_comments)
  logger.info("mplg_results len : {} ".format(len(mplg_results)))
  
  # 形態素解析したコメントとNGパターンの突合
  result_ng_comments, result_ng_channels = get_ng( 
    input_live_comments, 
    mplg_results, 
    input_ng_patterns, 
    SIMILARITY_THRESHOLD, 
    input_ng_channels)
  logger.info("result_ng_comments len : {} ".format(len(result_ng_comments)))
  logger.info("result_ng_channels len : {} ".format(len(result_ng_channels)))
  
  # 元のコメントjsonにNGフラグを設定
  # NGコメントのみを取得
  ng_merged_comments, ng_only_comments = merge_ng_comments(input_live_comments, result_ng_comments)
  logger.info("ng_merged_comments len : {} ".format(len(ng_merged_comments)))
  logger.info("ng_only_comments len : {} ".format(len(ng_only_comments)))
  
  # NGフラグを設定したコメントのjsonを出力
  with open(OUTPUT_DIR_ALL + 'result_' + VIDEO_ID + '.json' , mode='w') as f:
    f.write(json.dumps(ng_merged_comments))
  
  # NGに設定したユーザのチャンネルURLを出力
  with open(OUTPUT_DIR_NG_CHANNEL + 'result_' + VIDEO_ID + '.txt' , mode='w') as f:
    for ng_channel in result_ng_channels:
      f.write(ng_channel+'\n')
  
  # NGに設定したコメントのみを出力
  with open(OUTPUT_DIR_NG_MESSAGES + 'result_' + VIDEO_ID + '.json' , mode='w') as f:
    f.write(json.dumps(ng_only_comments))

  # logger.debug(json.dumps(result_ng_channels))
