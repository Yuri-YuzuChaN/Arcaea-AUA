from hoshino.log import new_logger
from hoshino.config import NICKNAME
import os

logger = new_logger('Arcaea')

arc = os.path.dirname(__file__)
songdir = os.path.join(arc, 'img', 'songs')
dir = os.path.join(arc, 'img')
bot = list(NICKNAME)[0] if NICKNAME else ''

USERSQL = os.path.expanduser('~/.hoshino/arcaea.db')
SONGSQL = os.path.join(arc, 'arcsong.db')

help = '''arcinfo/b30 [@] [arcid] 查询b30，带@或好友码查询TA人
arcre [@] [arcid] 查询最近一次游玩成绩，带@或好友码查询TA人
arcsc/score [@] [arcid] [songid] [difficulty] 查询指定曲目难度的成绩，默认为ftr难度，带@或好友码查询TA人
arcbind [arcid] 绑定用户
arcun 解除绑定
arcrd [定数] [难度] 随机一首该定数的曲目，例如：`arcrd 10.8`，`arcrd 10+`，`arcrd 9+ byd`
archart/chart [songid] [difficulty] 查看指定谱面
arcset [序号] 更改指令arcre成绩图'''

helpimg = os.path.join(arc, 'img', 'help.png')

diffdict = {
    '0' : ['pst', 'past'],
    '1' : ['prs', 'present'],
    '2' : ['ftr', 'future'],
    '3' : ['byd', 'beyond']
}