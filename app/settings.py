# -*- coding: utf-8 -*-
import os
from os.path import join, dirname
from dotenv import load_dotenv

load_dotenv(verbose=True)

dotenv_path = join(dirname(__file__), '.env')
load_dotenv(dotenv_path)

ENV_DIC = {}
ENV_KEYS = ['video_id','mplg','similarity_threshold','comment_len_warn']

for key in ENV_KEYS:
  ENV_DIC[key] = os.environ.get(key)
