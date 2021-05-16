# -*- coding: utf-8 -*-
import os
import glob
import settings
import json

import sys
sys.path.append('./')
from CommentEnum import CommentEnum 

NG_PATTERN_DIR = './input/ng_pattern/**'

# envのキーを読み込む。
keyIndex = 0
VIDEO_ID = settings.ENV_KEYS[keyIndex]; keyIndex = keyIndex + 1;

def get_ng_patterns():
  """ NGパターン一覧を読み込む
  """
  ng_pattern = {}
  for file in [p for p in glob.glob(NG_PATTERN_DIR , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
    with open(file) as f:
      ng_pattern[file] = f.read()
  return ng_pattern  

def get_live_comments(video_id):
  """ 指定された動画IDのコメント一覧を読み込んでマージする
  """
  INPUT_COMMENT_PATH = './input/comment/' + video_id + '/**'
  live_comments = {}
  for file in [p for p in glob.glob(INPUT_COMMENT_PATH , recursive=True) if os.path.isfile(p) and os.path.splitext(p)[1][1:] != 'gitkeep' ]:
    with open(file, mode='r') as f:
      comments = json.load(f)
      # コメント本体だけほしい。
      for comment in comments['items']:
        comment_id = comment['id']
        live_comments['id'] = comment;
  return live_comments

def morphological_analysis(live_comment):
  """ コメントを形態素解析する
  """
  
  morphological_analysis_result = {}
  for key in live_comment:
    # ['snippet']['type']はチャットの種類(superChatEvent, superStickerEvent, textMessageEvent)を持っている。
    type = str(live_comment[key]['snippet']['type'])
    message = ''
    try:
      commentEnum = CommentEnum.value_of(type)
      if('metaKey' in commentEnum){
        
      } else {
        
      }
      message = live_comment[key]['snippet']
    except ValueError:
      pass

  return morphological_analysis_result

if __name__ == '__main__':
  # NGパターンの読み込み
  ng_pattern = get_ng_patterns()
  
  # 指定されたVIDEO_IDのコメントファイル読み込み
  live_comment = get_live_comment(VIDEO_ID)
  
  # コメントの形態素解析
  morphological_analysis_result = morphological_analysis_result(live_comment_dict)
  
  # 形態素解析したコメントとNGパターンの突合
  
  
  # 元のコメントjsonにNGフラグを設定
  
  
  # NGフラグを設定したコメントのjsonを出力
  
  # NGに設定したユーザのチャンネルURLを出力
  
  
  pass