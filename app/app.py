# -*- coding: utf-8 -*-
from logging import getLogger, config, StreamHandler, DEBUG
import settings
import json
from difflib import SequenceMatcher 

import sys
sys.path.append('./')
from commentutil import OutputCommentKeyEnum, CommentTypeEnum 
from util import LogUtil
from judgement import NotUseMPLGJudgement, UseMPLGJudegement

logger = getLogger(__name__)
log_conf = LogUtil.get_log_conf('./log_config.json')
config.dictConfig(log_conf)
handler = StreamHandler()
handler.setLevel(DEBUG)
logger.setLevel(DEBUG)
logger.addHandler(handler)
logger.propagate = False

# envのキーを読み込む。
VIDEO_ID = settings.ENV_DIC['video_id']

# 形態素解析を使用するかどうか。
USE_MPLG = bool(int(settings.ENV_DIC['mplg']))

# 類似度閾値
SIMILARITY_THRESHOLD = float(settings.ENV_DIC['similarity_threshold'])

OUTPUT_DIR_ALL = './output/all/'
OUTPUT_DIR_NG_CHANNEL = './output/ng_channel/'
OUTPUT_DIR_OK_MESSAGES = './output/ok_message/'
OUTPUT_DIR_NG_MESSAGES = './output/ng_message/'

if __name__ == '__main__':
  logger.info("start.")
  # 設定値のログ出力
  logger.info("video_id : {}".format(VIDEO_ID))
  logger.info("USE_MPLG : {}".format(USE_MPLG))

  if USE_MPLG:
    judgement = UseMPLGJudegement(VIDEO_ID, SIMILARITY_THRESHOLD)
  else:
    judgement = NotUseMPLGJudgement(VIDEO_ID, SIMILARITY_THRESHOLD)

  logger.info("instance type : {}".format(type(judgement)))

  # 判定実行
  judgement.exec()

  # NGフラグを設定したコメントのjsonを出力
  with open(OUTPUT_DIR_ALL + 'result_' + VIDEO_ID + '.json', encoding='utf-8' , mode='w') as f:
   f.write(json.dumps(judgement.get_result_all_comments()))
  
  # NGに設定したユーザのチャンネルURLを出力
  with open(OUTPUT_DIR_NG_CHANNEL + 'result_' + VIDEO_ID + '.txt' , mode='w') as f:
    for ng_channel in judgement.get_result_ng_channels():
      f.write(ng_channel+'\n')

  # OKに設定したコメントのみを出力
  with open(OUTPUT_DIR_OK_MESSAGES + 'result_' + VIDEO_ID + '.json', encoding='utf-8' , mode='w') as f:
    f.write(json.dumps(judgement.get_result_ok_comments()))
  
  # NGに設定したコメントのみを出力
  with open(OUTPUT_DIR_NG_MESSAGES + 'result_' + VIDEO_ID + '.json', encoding='utf-8' , mode='w') as f:
    f.write(json.dumps(judgement.get_result_ng_comments()))

  logger.info("finish.")
  # logger.debug(json.dumps(result_ng_channels))
