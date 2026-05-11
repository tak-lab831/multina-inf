# AWS Reverse Proxy Architecture

このリポジトリは、セキュリティ重視の設計をテーマに「多層防御（Defense in Depth）」と「プライベート環境の保護」を意識した2層構造インフラ構築案です。

インターネットから直接Appサーバーにアクセスさせず、必ずリバースプロキシを経由させることで、バックエンドの安全性を高めています。（コスト面からHTTP運用としていますが、本来ならドメインを取得しSSL/TLS化（HTTPS）を行い、443ポート開放と証明書自動更新機能を導入するのが望ましいと考えています）

webアプリの稼働と外部からの攻撃遮断や内部サーバを隔離する構成を、実サーバー（AWS EC2）へ展開する設定ファイルを公開しています。


## 構成
* Public Layer(Reverse Proxy)
  * 役割：外部からのリクエストを受け、Appサーバへ安全に転送します。
  * 利用技術：Nginx

* Private-like Layer(App Server)
  * 役割：webアプリケーションの実行。外部ネットワークからはアクセスできない環境で動作します。
  * 利用技術：Python(Flask) + Gunicorn

## 実装内容
* ネットワーク隔離とアウトバウンドの管理
  * 隔離環境：AppサーバにパブリックIPを割り当ていない
  * Tinyproxyの採用：Appサーバがライブラリの更新（apt,pipなど）を行う際、Proxyサーバ上のTinyproxyを経由させることで、不用意な外部通信を制限しています。

* 不正アクセスの防御（fail2ban）
  * Nginxのログを監視し、不審なIPアドレスを検知し遮断

* コンテナ設計
  * docker-compose.yml では、Appサーバを expose のみに限定。Nginxを介さずにアプリへ直接接続することを構造的に禁止しています。


## ディレクトリ構造
.
├── docker-compose.yml
├── proxy/
│   ├── nginx/ 
│   │   └── nginx.conf				# Nginx転送設定 
│   ├── fail2ban/	
│	│	├── jail.local				# 不正アクセス自動遮断設定
│	│	└── filter.d/
│   │       └── nginx-4xx.conf		# 4xx監視フィルタの設定
│   └── tinyproxy/
│		└── tinyproxy.conf			# Tinyproxyの設定（許可するIPなど）
└── app/
    ├── app.py						# Flaskアプリケーション本体
	├── wsgi.py						# Gunicorn用の入り口
	├── Dockerfile
	├── requirements.txt			# pythonで必要なライブラリのリスト
	├── templates/ 
	│	└── index.html
	├── uploads/					# app.py実行時に使用
	│	└── .gitkeep
    └── setup/	
	　	├── 80proxy					# apt用の設定
		└── set_env.sh				# .bashrcに追記する環境変数のメモ（Dockerやpipなどで利用）
		

## 実サーバ（EC2など）への展開について
各設定ファイルは、AWS上の2台のUbuntuインスタンスで動作確認済みです。
  * 実際に稼働させているアドレス：http://100.24.26.163

実環境へ適用する際は、以下のファイルを参考にIPアドレス等を環境に合わせて書き換えてください。
  * proxy/nginx/nginx.conf: proxy_pass の接続先IPをAppサーバのプライベートIPへ。
  * app/setup/80proxy: ProxyサーバのプライベートIPへ。
