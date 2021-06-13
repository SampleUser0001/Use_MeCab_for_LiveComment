# -*- coding: utf-8 -*-
from logging import getLogger, config, StreamHandler, DEBUG
from abc import ABCMeta, abstractmethod
import os
import glob
import MeCab
import json
from difflib import SequenceMatcher 
import pycld2 as cld2

import sys
sys.path.append('./')
from commentutil import CommentTypeEnum, AddNGInfoKeyEnum, OutputCommentKeyEnum
from util import LogUtil

logger = getLogger("same_hierarchy")
log_conf = LogUtil.get_log_conf('./log_config.json')
config.dictConfig(log_conf)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# NGパターンとの突合結果
NG_RESULT_KEYS = ["pattern","similarity"]
INDEX_NG_RESULT_PATTERN = 0
INDEX_NG_RESULT_SIMILARITY = 1

class JudgementInterface():
  """
  NG判定用インターフェース
  """
  # NGチャンネル一覧のファイルが配置してあるパス
  NG_CHANNEL_DIR = './input/ng_channel/**'

  # 言語ごとのWARN判定文字列長TSVファイル
  LANG_LEN_PATH = './input/lang_len.tsv'

  def __init__( \
    self, \
    video_id, \
    ng_pattern_path, \
    threshold):
    """ コンストラクタ
    """
    self.video_id = video_id
    self.ng_pattern_path = ng_pattern_path
    self.threshold = threshold

    self.result_all_comments = None
    self.result_ok_comments = None
    self.result_ng_comments = None
    self.result_ng_channels = None

    self.LANG_LEN_DIC = {}
    with open(self.LANG_LEN_PATH, mode='r') as f:
      for line in f.readlines():
        lines = line.replace('\r', '').replace('\n', '').split('\t')
        self.LANG_LEN_DIC[lines[0]] = int(lines[1])
    logger.info("lang_len: {}".format(self.LANG_LEN_DIC))

  def exec(self):
    live_comments = self.import_live_comments(self.video_id)
    logger.info("live_comments len : {}".format(len(live_comments)))

    ng_channels = self.import_ng_channel()
    logger.info("ng_channels len : {}".format(len(ng_channels)))

    ng_patterns = self.import_ng_pattern(self.ng_pattern_path)
    logger.info("ng_patterns len : {}".format(len(ng_patterns)))

    pickup_comments = self.pickup_comment(live_comments)
    logger.info("pickup_comments len : {}".format(len(pickup_comments)))

    judged_ng_comments, self.result_ng_channels = \
      self.judgement( \
        live_comments,\
        pickup_comments, \
        ng_patterns, \
        ng_channels, \
        self.threshold)
    logger.info("judged_ng_comments len : {}".format(len(judged_ng_comments)))
    logger.info("result_ng_channels len : {}".format(len(self.result_ng_channels)))

    self.result_all_comments , self.result_ok_comments , self.result_ng_comments = \
      self.merge_comments(live_comments, judged_ng_comments)
    logger.info("result_ok_comments len : {}".format(len(self.result_ok_comments)))

  def get_result_all_comments(self):
    return self.result_all_comments
  def get_result_ok_comments(self):
    return self.result_ok_comments
  def get_result_ng_comments(self):
    return self.result_ng_comments
  def get_result_ng_channels(self):
    return self.result_ng_channels

  def import_live_comments(self, video_id):
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

  def import_ng_channel(self):
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
    return JudgementInterface.read_dir(JudgementInterface.NG_CHANNEL_DIR)

  @abstractmethod
  def import_ng_pattern(self, path):
    """ NGパターンの読み込み
    Parameters
    ---
    path : string
      NGパターンが配置されているファイルパス
    """
    pass

  def pickup_comment(self, live_comments):
    """
    GoogleAPIで取得したコメントをkey-commentのdictに変換する。
    形態素解析を使用する場合は、コメントを形態素解析した状態にする。
    
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
      comment = CommentTypeEnum.get_comment(live_comments[key])    

      # 形態素解析（実際に行うかは実装クラス依存。）
      comment = self.mplg(comment)
      morphological_analysis_result[key] = comment
  
    return morphological_analysis_result
    
  def judgement(self, comments, pickup_comments, ng_patterns, ng_channels ,threshold):
    """ NG判定を行う。
    
    Paramters:
    ----
    comments : dict
      インポートしたコメント。
      JudgementInterface.import_live_comments関数の戻り値。
    pickup_comments : dict
      key : commentsのキーと同値
      value : コメントの形態素解析結果 or コメント本体 (どちらを保持しているかは実装クラス次第)
    ng_patterns : dict or list
      NGパターン。
      形態素解析を使う場合はdict。
      形態素解析を使わない場合はlist。
    ng_channels : list
      NG判定するチャンネル一覧
    threshold : float
      類似度のしきい値。
      NGパターンと比較して、類似度がこの値以上の場合、NGと判断する。

    Returns:
    ----
    ng_comments : dict型。NG判定されたコメントを返す。
      key : コメントID
      value : dict {
        ng_channel (必須) : チャンネルURL
        ng_comment (任意) : {
          ng_pattern : ng_patternのキー, または元のNGパターンのコメント
          similarity : 類似度
        } 
        ng_pattern (必須) : 配列。どのパターンで引っかかったか。 ["comment","channel"]
      }
    ng_channels : list
      NG判定したチャンネル一覧
    """
    logger.info("threshold: {}".format(threshold))
    logger.info("ng_channels len: {}".format(len(ng_channels)))
    
    # 戻り値
    return_ng_comments = {}
    return_ng_channels = []

    for key in pickup_comments:
      # コメント取得
      comment = pickup_comments[key]

      # コメントのパターンからNG判定する。
      # 形態素解析有りと無しでNGパターンの型が異なるので、ポリモーフィズムを使う。
      ng, ng_comment, judgement_pattern = self.judgement_by_pattern(comment, ng_patterns, threshold)

      # チャンネルURLから判断
      channel_url = comments[key]['authorDetails']['channelUrl']
      if channel_url in ng_channels:
        ng = True
        judgement_pattern.append('channel')
  
      # どのチェックで引っかかったかはコメントIDをキーに登録
      if ng:
        ng_comment['ng_channel'] = channel_url
        return_ng_comments[key] = ng_comment
        if channel_url not in return_ng_channels:
          return_ng_channels.append(channel_url)

    return return_ng_comments, return_ng_channels

  @abstractmethod
  def judgement_by_pattern(self, comment, ng_patterns, threshold):
    pass

  def merge_comments(self, comments, ng_comments):
    """
    コメントにNG情報を付与する。
    
    Parameters:
    ----
    comments : dict
      JudgementInterface.import_live_commentsメソッドの戻り値。
    ng_comments : dict
      JudgementInterface.judgementメソッドの戻り値のうち、ng_comments。
     
    Returns:
    ----
    return_comment_list : list[dict]
      コメントの配列。元のコメントに下記を追加する。
      ng_flg : true or false
      ng_info : dict {
        ng_channel (必須) : チャンネルURL
        ng_comment (任意) : {
          ng_pattern_key : ng_patternのキー, 
          similarity : 類似度
        } 
        ng_pattern (必須) : 配列。どのパターンで引っかかったか。 ["comment","channel"]
      }
    ok_only_comments : list[dict]
      OKコメント一覧
    ng_only_comments : list[dict]
      NGコメント一覧
    """
    return_comment_list = []
    ok_only_comments = []
    ng_only_comments = []
  
    for comment_id in comments:
      comment_info = comments[comment_id]
  
      # TODO : もうちょっとなんとかならんか
      ID = OutputCommentKeyEnum.ID.get_ng_key()
      CHANNEL_ID = OutputCommentKeyEnum.CHANNEL_ID.get_ng_key()
      DISPLAY_NAME = OutputCommentKeyEnum.DISPLAY_NAME.get_ng_key()
      DISPLAY_MESSAGE = OutputCommentKeyEnum.DISPLAY_MESSAGE.get_ng_key()
  
      ID_ORIGIN = OutputCommentKeyEnum.ID.get_origin_key()
      CHANNEL_ID_ORIGIN = OutputCommentKeyEnum.CHANNEL_ID.get_origin_key()
      DISPLAY_NAME_ORIGIN = OutputCommentKeyEnum.DISPLAY_NAME.get_origin_key()
      DISPLAY_MESSAGE_ORIGIN = OutputCommentKeyEnum.DISPLAY_MESSAGE.get_origin_key()
  
      # ng_only_commentsかok_only_commentsに追加する用の変数。
      tmp_comment = {
        ID :              comment_info[ID_ORIGIN[0]],
        CHANNEL_ID :      comment_info[CHANNEL_ID_ORIGIN[0]][CHANNEL_ID_ORIGIN[1]],
        DISPLAY_NAME :    comment_info[DISPLAY_NAME_ORIGIN[0]][DISPLAY_NAME_ORIGIN[1]],
        DISPLAY_MESSAGE : comment_info[DISPLAY_MESSAGE_ORIGIN[0]][DISPLAY_MESSAGE_ORIGIN[1]]
      }
      
      if comment_id in ng_comments:
        comment_info[AddNGInfoKeyEnum.NG_FLG_KEY.value] = True
        comment_info[AddNGInfoKeyEnum.NG_INFO_KEY.value] = ng_comments[comment_id]
        ng_only_comments.append(tmp_comment)
      else:
        comment_info[AddNGInfoKeyEnum.NG_FLG_KEY.value] = False
        ok_only_comments.append(tmp_comment)
  
      return_comment_list.append(comment_info)
    return return_comment_list, ok_only_comments, ng_only_comments

  @abstractmethod
  def mplg(self, text):
    """ 必要であれば形態素解析を行う。必要かどうかはクラスに依存。
    """
    pass

  @classmethod
  def read_dir(cls, path):
    """
    指定されたディレクトリ配下のファイルを再帰検索し、
    ファイルの中身を読み込んで、listにして変換する。
    内容に重複がある場合は重複排除する。
    
    Parameters:
    ---
    path : string
      ディレクトリパス。
      この引数で指定されたディレクトリ配下に配置されているファイルを読み込む。
      .gitkeepは除外。
      
    Returns:
    ---
    return_value_list : list
      読み込み結果。
      
    """
    return_value_list = []
    for file in [p for p in glob.glob(path , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
      with open(file, mode='r') as f:
        for line in f.read().splitlines():
          if line not in return_value_list:
            return_value_list.append(line)
    return return_value_list

class NotUseMPLGJudgement(JudgementInterface):
  """ NG判定時に形態素解析を使用しない """

  # NGコメント一覧のファイルが配置してあるパス
  NG_COMMENT_DIR = './input/ng_comment/**'

  def __init__(self, video_id, threshold):
    super().__init__(video_id, NotUseMPLGJudgement.NG_COMMENT_DIR, threshold)

  def import_ng_pattern(self, path):
    """ NGパターンの読み込み
    Parameters
    ---
    path : string
      NGパターンが配置されているファイルパス
    """
    return JudgementInterface.read_dir(NotUseMPLGJudgement.NG_COMMENT_DIR)

  def judgement_by_pattern(self, comment, ng_patterns, threshold):
    ng = False
    ng_comment = {}
    judgement_pattern = []
    for i in range(len(ng_patterns)):
      similarity = SequenceMatcher(None, comment, ng_patterns[i]).ratio()

      if similarity > threshold:
        ng_comment['ng_comment'] = {
          NG_RESULT_KEYS[INDEX_NG_RESULT_PATTERN]: ng_patterns[i],
          NG_RESULT_KEYS[INDEX_NG_RESULT_SIMILARITY]: similarity
        }
        judgement_pattern.append('comment')
        ng = True
        break

    return ng, ng_comment, judgement_pattern

  def mplg(self, text):
    """ 
    形態素解析しない。何もせずそのままtextを返す。
    """
    return text

class UseMPLGJudegement(JudgementInterface):
  """ NG判定時に形態素解析を使用する """

  # 辞書ファイルパス
  DIC_PATH = ' -d /usr/local/mecab/lib/mecab/dic/mecab-ipadic-neologd'

  # NGパターンの形態素解析結果を配置しているファイルパス
  NG_PATTERN_DIR = './input/ng_pattern/**'

  def __init__(self, video_id, threshold):
    super().__init__(video_id, UseMPLGJudegement.NG_PATTERN_DIR, threshold)

  def import_ng_pattern(self, path):
    """
    NGパターン一覧を読み込む
    
    Parameters:
    ----
    path : ディレクトリパス
    
    Returns:
    ----
    ng_patterns : dict
      key : string
        ファイルパス
      value : string
        ファイル内容（形態素解析結果）
    """

    ng_pattern = {}
    for file in [p for p in glob.glob(path , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
      with open(file) as f:
        ng_pattern[file] = f.read()
    return ng_pattern  

  def judgement_by_pattern(self, comment, ng_patterns, threshold):
    ng = False
    ng_comment = {}
    judgement_pattern = []
    for ng_key in ng_patterns:
      similarity = SequenceMatcher(None, comment, ng_patterns[ng_key]).ratio()

      if similarity > threshold:
        ng_comment['ng_comment'] = {
          NG_RESULT_KEYS[INDEX_NG_RESULT_PATTERN]: ng_key,
          NG_RESULT_KEYS[INDEX_NG_RESULT_SIMILARITY]: similarity
        }
        judgement_pattern.append('comment')
        ng = True
        break

    return ng, ng_comment, judgement_pattern

  def mplg(self, text):
    """ 形態素解析する。
    """
    m = MeCab.Tagger(UseMPLGJudegement.DIC_PATH)
    soup = m.parse (text)
    return soup
