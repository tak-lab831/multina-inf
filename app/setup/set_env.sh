# AppサーバがProxyサーバ(Tinyproxy)を経由してpip等を利用するための設定
# .bashrc に追記して使用
export http_proxy="http://<PROXY_SERVER_PRIVATE_IP>:8888"
export https_proxy="http://<PROXY_SERVER_PRIVATE_IP>:8888"

# 自身のループバックアドレスや、AWS内部のメタデータサービス、VPC内通信をプロキシ除外に設定
export no_proxy="localhost,127.0.0.1,169.254.169.254,172.31.0.0/16"
