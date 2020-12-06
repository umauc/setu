# setu
基于Graia Framework的，带有权限系统的，可由用户上传色图的色图插件
# 部署
以下部分假设您已经通过各种方式部署了mirai和mirai-api-http
```
git clone https://github.com/umauc/setu.git
cd setu
pip3 install -r requirements.txt
cp setu_config_example.py setu_config.py # 之后修改setu_config.py中的参数
python3 setu.py
```
插件启动并确认能正常接收消息后，使用在setu_config.py中钦点的管理员QQ账号，在任意群中发送#SETU init，得到返回消息后使用#SETU fupload上传几张色图（用法见下），即可部署完成
# 命令列表
命令格式：#SETU 模式 参数
## 群
模式|最低权限|参数|说明
--|:--:|--:|--:
init|0|无|将配置中的admin用户权限设置至5
fupload|1|Piviv插画ID，可用半角逗号分隔以批量上传|使用Pixiv插画ID上传色图
clear|5|无|清除使用次数数据
count|0|无|统计总色图数
delete|5|Pixiv插画ID|从数据库中删除色图
r18|2|关键词（非必须）|从本地或lolicon api处获取R18色图
无|0|无|从本地获取普通色图
关键词|0|无|从lolicon api处获取与关键词相关的色图
## 私聊
模式|最低权限|参数|说明
--|:--:|--:|--:
upload|0|start|通过图片上传色图
upload|0|stop|停止接收图片，开始识别处理
# 权限说明
权限|色图请求数|撤回时间|获得途径
--|:--:|--:|--:
0|3|30s|默认
1|10|30s|上传50~100张色图
2|25|60s|上传100~175张色图
3|30|60s|上传175~250张色图
4|10000|260s|上传250张色图
5|10000|260s|管理员
