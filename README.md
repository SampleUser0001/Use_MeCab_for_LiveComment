# Use MeCab for LiveComment

GoogleAPIで取得したYoutubeLiveコメントをOK/NGに振り分ける。  

## 使い方

### ディレクトリ構成

``` txt
.
└── app
    ├── input                     # 入力ファイル一覧
    │   ├── comment               # 動画ごとのコメントファイルを配置する。
    │   │   ├── ${動画ID}
    │   │   ├── ...
    │   │   └── ${動画ID}
    │   ├── ng_channel            # NGチャンネル一覧のファイルを配置する。
    │   └── ng_pattern            # NG判定する形態素解析結果を配置する。
    │       └── pmTQqhpHAHs
    ├── log
    ├── output                    # 実行結果が出力される
    │   ├── all                   # 元のコメントファイルにOK/NGを付与したjsonを出力
    │   ├── ng_channel            # NG判定したチャンネル一覧を出力する。
    │   ├── ng_message            # NG判定したコメントを出力する。
    │   └── ok_message            # OK判定したコメントを出力する。
    └── __pycache__
```

### 入力ファイルフォーマット

#### ng_channel

- ファイル名
    - .gitkeep以外の任意の名前。
- ファイル内容
    - ```http://www.youtube.com/channel/${チャンネルID}```のフォーマットで記載する。

#### ng_pattern

- MeCabで分析したファイルを配置する。
    - ここに配置したファイルとコメントファイルの形態素解析結果を比較し、一定以上の類似度の場合NGと判断する。

#### ng_comment

- 通常のコメントを配置する。
    - NG判定は完全一致ではなく類似度から判定する。

### 実行方法

1. 入力ファイル配置
    1. sample.envをコピーし、.envを作成する。
        1. video_idを指定する。
        2. USE_MPLGを指定する。
            - 形態素解析を使用するかどうかの値。trueで使用する。
    2. app/input/comment配下にGoogleAPIを使用して取得したコメントjsonファイルを配置する。
    3. app/ng_channel配下にNG判定したいチャンネルURL一覧のファイルを配置する。
    4. app/ng_pattern配下にNG判定に使用したいの形態素解析結果のファイルを配置する。
2. ```docker-compose up```を実行する。
