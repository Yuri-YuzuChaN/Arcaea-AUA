# Arcaea-BAA

基于HoshinoBotV2的Arcaea-BAA查询插件

项目地址：https://github.com/Yuri-YuzuChaN/Arcaea-BAA

## 使用方法

1. 将该项目放在HoshinoBot插件目录 `modules` 下，或者clone本项目 `git clone https://github.com/Yuri-YuzuChaN/Arcaea-BAA`
2. pip以下依赖：`pillow`, `aiohttp`, `aiofiles`
3. 在 `api.py` 文件填入 `BAAPI` 和 `TOKEN`，如果不需要 `User-Agent` 请删除 `24` 行 `headers` 和 `26` 行 `headers=headers`，请勿询问BAAPI和TOKEN
4. 在`config/__bot__.py`模块列表中添加 `Arcaea-BAA`

**该插件默认关闭，请手动开启**

# 指令

| 指令              | 功能      | 可选参数              | 说明                            |
| :---------------- | :-------- | :-------------------- | :------------------------------ |
| arcinfo           | 查询B30   |  [@] [arcid]             | 查询B30成绩，带@或好友码查询TA人 |
| arcre             | 查询最近  |  [@] [arcid]        | 查询最近一次游玩成绩，带@或好友码查询TA人 |
| arcsc             | 查询单曲  |   [@] [arcid] [songid] [difficulty] | 查询指定曲目难度的成绩，默认为ftr难度，带@或好友码查询TA人 |
| arcbind           | 绑定      | [arcid]               | 绑定用户                        |
| arcun             | 解绑      | 无                    | 解除绑定                        |
| arcrd             | 随机曲目   | [定数] [难度]         | 随机一首该定数的曲目，例如：`arcrd 10.8`，`arcrd 10+`，`arcrd 9+ byd` |