# -*- coding: utf-8 -*-
import os
import glob
import settings
import json
import MeCab
from difflib import SequenceMatcher 

import sys
sys.path.append('./')
from commentutil import CommentEnum 

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

OUTPUT_DIR = './output/'
FILE_NAME = 'result'

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
        live_comments['id'] = comment;
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
      commentEnum = CommentEnum.value_of(type)
      commentKeys = commentEnum.get_keys();
      tmp = live_comments[key][SNIPPET]
      for commentKey in commentKeys:
        # コメントを取得する
        tmp = tmp[commentKey]
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
  ng_comments = {}
  for comment_key in mplg_results:
    mplg_result = mplg_results[comment_key]
    for ng_key in ng_pattern:
      similarity = SequenceMatcher(
        None,mplg_result,ng_pattern[ng_key]).ratio()
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
    
    """
    
    return_comment_list = []

    for key in comment_dict:
        comment_info = comment_dict[key]
        if key in ng_comment_dict:
            comment_info[NG_FLG_KEY] = True
            comment_info[NG_INFO_KEY] = ng_comment_dict[key]
        else:
            comment_info[NG_FLG_KEY] = False

        return_comment_list.append(comment_info)
    return return_comment_list

if __name__ == '__main__':


  # NGパターンの読み込み
  ng_pattern = get_ng_patterns()
  print(len(ng_pattern))

  # 指定されたVIDEO_IDのコメントファイル読み込み
  print('VIDEO_ID : {}'.format(VIDEO_ID))
  live_comment_dict = get_live_comments(VIDEO_ID)

  # コメントの形態素解析
  morphological_analysis_result_dict = morphological_analysis(live_comment_dict)
  print(len(morphological_analysis_result_dict))
  
  # 形態素解析したコメントとNGパターンの突合
  ng_comments = get_ng_chat_id(morphological_analysis_result_dict, ng_pattern, SIMILARITY_THRESHOLD)
  print(len(ng_comments))
  
  # 元のコメントjsonにNGフラグを設定
  comments_ng_merged = merge_ng_comments(live_comment_dict, ng_comments)
  print(len(comments_ng_merged))
  
  # NGフラグを設定したコメントのjsonを出力
  # 結果をファイルに出力
  with open(OUTPUT_DIR + 'result_' + VIDEO_ID + '.json' , mode='w') as f:
    f.write(json.dumps(comments_ng_merged))
  
  # NGに設定したユーザのチャンネルURLを出力
  
