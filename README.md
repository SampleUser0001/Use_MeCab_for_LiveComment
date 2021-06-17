# Use MeCab for LiveComment

GoogleAPIで取得したYoutubeLiveコメントをOK/NGに振り分ける。  

## ディレクトリ構成

``` txt
.
└── app
    ├── input                     # 入力ファイル一覧
    │   ├── comment               # 動画ごとのコメントファイルを配置する。
    │   │   ├── ${動画ID}
    │   │   ├── ...
    │   │   └── ${動画ID}
    │   ├── ng_channel            # NGチャンネル一覧のファイルを配置する。
    │   ├── ng_comment            # NG判定するコメントを配置する。
    │   └── ng_pattern            # NG判定する形態素解析結果を配置する。
    │       └── pmTQqhpHAHs
    ├── log
    ├── output                    # 実行結果が出力される
    │   ├── all                   # 元のコメントファイルにOK/NGを付与したjsonを出力
    │   ├── ng_channel            # NG判定したチャンネル一覧を出力する。
    │   ├── ng_message            # NG判定したコメントを出力する。
    │   └── ok_message            # OK判定したコメントを出力する。
    └── __pycache__
```

## 入力ファイルフォーマット

### ng_channel

- ファイル名
    - .gitkeep以外の任意の名前。
- ファイル内容
    - ```http://www.youtube.com/channel/${チャンネルID}```のフォーマットで記載する。

### ng_pattern

- MeCabで分析したファイルを配置する。
    - ここに配置したファイルとコメントファイルの形態素解析結果を比較し、一定以上の類似度の場合NGと判断する。

### ng_comment

- 通常のコメントを配置する。
    - NG判定は完全一致ではなく類似度から判定する。

## 出力ファイルフォーマット

### all配下

GoogleAPIの実行結果に加えて、下記が出力される。

#### 条件なし

``` json
lang : "string コメントの言語"
```

#### NGコメント

``` json
... ,
ng_flg : true or false ,
ng_info : {
    ng_comment : {
        pattern : "string NG判定されたパターン",
        similarity : 小数 元のコメントとパターンとの類似度
    },
    ng_channel : "string NGコメントをしたチャンネルURL"
}
```

##### 出力パターン

| jsonキー | OK(NGではない) | 投稿者自体がNG | 形態素解析あり | 形態素解析なし |
| :-- | :------------ | :------------ | :------------ | :----------- |
| ng_flg | false | true | true | true |
| ng_info | 出力されない | 出力されない | 出力される | 出力される |
| ng_info - ng_comment - pattern | 出力されない | 出力されない | 比較対象の形態素解析結果 | 比較対象のメッセージ |
| ng_info - ng_comment - similarity | 出力されない | 出力されない | 元のコメントと比較対象の類似度 | 元のコメントと比較対象の類似度 |
| ng_info - ng_channel | 出力されない | 投稿者のチャンネルURL | 投稿者のチャンネルURL | 投稿者のチャンネルURL |

##### 備考

- ng_pattern
  - channel, commentの両方が出力される可能性がある。
  - 出力されない場合は空の配列にもならない。

#### WARNコメント

``` json
... ,
warn_flg : true or false ,
warn_comment_info {
    lang : コメント言語,
    length : コメント帳
},
warn_channel : "string WARNコメントをしたチャンネルURL",
warn_pattern : "array[string] どのチェックで引っかかったか"
```

##### 出力パターン

| jsonキー | OK(WARNではない) | コメント長 |
| :-- | :------------ | :------------ |
| warn_flg | false | true |
| warn_comment_info | 出力されない | 出力される |
| warn_comment_info - lang | 出力されない | コメントの言語 |
| warn_comment_info - len | 出力されない | コメント長 |
| warn_channel | 出力されない | 投稿者のチャンネルURL |
| warn_pattern | 出力されない | length |

### ng_channel配下

``` txt
http://www.youtube.com/channel/${チャンネルID}
```

### ok_message, ng_message, warn_message配下

``` json
[
    {
        "id": "string コメントID",
        "channelId": "string チャンネルID",
        "displayName": "string ユーザ名",
        "displayMessage": "string コメント"
    },
    ...
]
```

## 実行方法

1. 入力ファイル配置
    1. sample.envをコピーし、.envを作成する。
        1. video_idを指定する。
        2. USE_MPLGを指定する。
            - 形態素解析を使用するかどうかの値。trueで使用する。
    2. app/input/comment配下にGoogleAPIを使用して取得したコメントjsonファイルを配置する。
    3. app/ng_channel配下にNG判定したいチャンネルURL一覧のファイルを配置する。
    4. app/ng_pattern配下にNG判定に使用したいの形態素解析結果のファイルを配置する。
2. ```docker-compose up```を実行する。
