# Template Python on Docker

## 使い方

1. Dockerfileのimageを変更する。
2. 必要に応じてDockerfileにpipを書く。
3. 必要に応じてdocker-compose.ymlを修正する。
4. 下記実行。
    ``` sh
    docker-compose build
    docker-compose up
    ```

## 参考

- [Qiita:Docker を使う（python のイメージで色々確認してみる）](https://qiita.com/landwarrior/items/fd918da9ebae20486b81)
- [Future Tech Blog:仕事でPythonコンテナをデプロイする人向けのDockerfile (1): オールマイティ編](https://future-architect.github.io/articles/20200513/)