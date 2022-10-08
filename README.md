# Arcaea-AUA

基于HoshinoBotV2的Arcaea查询插件

项目地址：https://github.com/Yuri-YuzuChaN/Arcaea-AUA

## 使用方法

1. 将该项目放在HoshinoBot插件目录 `modules` 下，或者clone本项目 `git clone https://github.com/Yuri-YuzuChaN/Arcaea-AUA`
2. pip以下依赖：`pillow`, `aiohttp`, `aiofiles`
3. 在 `api.py` 文件填入 `AUAPI` 和 `TOKEN`
4. 在`config/__bot__.py` 模块列表中添加 `Arcaea`
5. 重启BOT

# 指令

| 指令              | 功能      | 可选参数              | 说明                            |
| :---------------- | :-------- | :-------------------- | :------------------------------ |
| arcinfo/b30           | 查询B30   |  [@] [arcid]             | 查询B30成绩，带@或好友码查询TA人 |
| arcre             | 查询最近  |  [@] [arcid]        | 查询最近一次游玩成绩，带@或好友码查询TA人 |
| arcsc             | 查询单曲  |   [@] [arcid] [songid] [difficulty] | 查询指定曲目难度的成绩，默认为ftr难度，带@或好友码查询TA人 |
| arcbind           | 绑定      | [arcid]               | 绑定用户                        |
| arcun             | 解绑      | 无                    | 解除绑定                        |
| arcrd             | 随机曲目   | [定数] [难度]         | 随机一首该定数的曲目，例如：`arcrd 10.8`，`arcrd 10+`，`arcrd 9+ byd` |
| arcset            | 修改成绩图 |[序号]                |   更改指令arcre成绩图             |