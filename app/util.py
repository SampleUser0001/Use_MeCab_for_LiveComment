# -*- coding: utf-8 -*-
import json

class LogUtil:
  
  @classmethod
  def get_log_conf(cls, log_conf_path):
    """ ログ設定ファイルを読み込む
    """
    with open(log_conf_path, mode='r') as f:
      log_conf = json.loads(f.read())
    return log_conf