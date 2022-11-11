import asyncio, random, traceback
from nonebot import NoneBot
from hoshino import Service, priv, MessageSegment
from hoshino.config import SUPERUSERS
from hoshino.typing import CQEvent
from aiocqhttp import ActionFailed

from .sql import asql
from .api import *
from .draw import (
    songdir,
    list2newline,
    draw_chart,
    draw_info,
    draw_score,
    bindinfo,
    random_music,
)

NOTBIND = '账号尚未绑定，请输入 arcbind ID(好友码或账户名) 进行绑定'

difficulty = ['0', '1', '2', '3', 'pst', 'prs', 'ftr', 'byd', 'past', 'present', 'future', 'beyond']

sv = Service('Arcaea', manage_priv=priv.ADMIN, enable_on_default=True, visible=True, help_=help)

class Alias:

    def __init__(self) -> None:
        self.list: dict[str, dict[str, Union[int, list[int]]]] = {}

    def open(self, gid: int, songid: str, alias: str):
        self.list[str(gid)] = {
            'vote' : 0,
            'user' : []
        }
        self.songid = songid
        self.alias: alias

    def close(self, gid: int):
        self.list.pop(str(gid))
    
    def add(self, gid: int, uid: int):
        self.list[str(gid)]['vote'] += 1
        self.list[str(gid)]['user'].append(uid)

    def remove(self, gid: int, uid: int):
        if self.list[str(gid)]['vote'] <= 0:
            pass
        else:
            self.list[str(gid)]['vote'] -= 1
            self.list[str(gid)]['user'].append(uid)

ali = Alias()

@sv.on_prefix(['arcinfo', 'ARCINFO', 'Arcinfo', 'arcb30', 'Arcb30', 'ARCB30', 'b30', 'B30'])
async def arcinfo(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    args: str = ev.message.extract_plain_text().strip()
    if ev.message[0].type == 'at':
        qqid = int(ev.message[0].data['qq'])
    result = asql.get_user(qqid)
    if args:
        arcid = args
    elif not result:
        await bot.finish(ev, NOTBIND, at_sender=True)
    else:
        arcid = result[0]
    info = await draw_info(arcid)
    await bot.send(ev, info, at_sender=True)

@sv.on_prefix(['arcre', 'Arcre', 'ARCRE'])
async def arcre(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    args: str = ev.message.extract_plain_text().strip()
    if ev.message[0].type == 'at':
        qqid = int(ev.message[0].data['qq'])
    result = asql.get_user(qqid)
    if args:
        arcid = args
        mode = 0
    elif not result:
        await bot.finish(ev, NOTBIND, at_sender=True)
    else:
        arcid, mode = result
    info = await draw_score('recent', arcid, mode)
    await bot.send(ev, info, at_sender=True)

@sv.on_prefix(['arcscore', 'Arcscore', 'ARCSCORE', 'arcsc', 'Arcsc', 'ARCSC', 'arcbest', 'Arcbest', 'ARCBEST'])
async def arcscore(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    args: list[str] = ev.message.extract_plain_text().strip().split()
    if ev.message[0].type == 'at':
        qqid = int(ev.message[0].data['qq'])
    result = asql.get_user(qqid)
    arcid = 0
    if args:
        if args[0].isdigit() and len(args[0]) == 9:
            arcid = args[0]
            mode = 0
            args.remove(arcid)
        elif not result:
            await bot.finish(ev, NOTBIND, at_sender=True)
    if not args:
        await bot.finish(ev, '请输入曲名', at_sender=True)
    if len(args) != 1:
        if args[-1].lower() in difficulty:
            name = ' '.join(args[:-1])
            diff = int(difficulty.index(args[-1].lower()) % 4)
        else:
            name = ' '.join(args)
            diff = 2
        if arcid == 0:
            arcid, mode = result
        else:
            mode = result[1]
    else:
        if arcid == 0:
            arcid, mode = result
        else:
            mode = result[1]
        name = args[0]
        diff = 2
    sname = asql.alias(name)
    if sname:
        name = sname[0][0]
    
    info = await draw_score('best', arcid, mode, name, diff)
    await bot.send(ev, info, at_sender=True)

@sv.on_prefix(['arcrd', 'Arcrd', 'ARCRD'])
async def arcrd(bot: NoneBot, ev: CQEvent):
    args: list[str] = ev.message.extract_plain_text().strip().split()
    diff = None
    if not args:
        await bot.finish(ev, '请输入定数')
    elif len(args) == 1:
        try:
            rating = float(args[0]) * 10
            if not 10 <= rating < 120:
                await bot.finish(ev, '请输入定数：1-12 | 9+ | 10+')
            plus = False
        except ValueError:
            if '+' in args[0] and args[0][-1] == '+':
                rating = float(args[0][:-1]) * 10
                if rating % 10 != 0:
                    await bot.finish(ev, '仅允许定数为：9+ | 10+')
                if not 90 <= rating < 110:
                    await bot.finish(ev, '仅允许定数为：9 | 10')
                plus = True
            else:
                await bot.finish(ev, '请输入定数：1-12 | 9+ | 10+')
    elif len(args) == 2:
        try:
            rating = float(args[0]) * 10
            plus = False
            if not 10 <= rating < 120:
                await bot.finish(ev, '请输入定数：1-12 | 9+ | 10+')
            if args[1].isdigit():
                if args[1] not in diffdict:
                    await bot.finish(ev, '请输入正确的难度：3 | byd | beyond')
                else:
                    diff = int(args[1])
            else:
                for d in diffdict:
                    if args[1].lower() in diffdict[d]:
                        diff = int(d)
                        break
        except ValueError:
            if '+' in args[0] and args[0][-1] == '+':
                rating = float(args[0][:-1]) * 10
                if rating % 10 != 0:
                    await bot.finish(ev, '仅允许定数为：9+ | 10+')
                if not 90 <= rating < 110:
                    await bot.finish(ev, '仅允许定数为：9 | 10')
                plus = True
                if args[1].isdigit():
                    if args[1] not in diffdict:
                        await bot.finish(ev, '请输入正确的难度：3 | byd | beyond')
                    else:
                        diff = int(args[1])
                else:
                    for d in diffdict:
                        if args[1].lower() in diffdict[d]:
                            diff = int(d)
                            break
            else:
                await bot.finish(ev, '请输入定数：1-12 | 9+ | 10+')
    else:
        await bot.finish(ev, '请输入正确参数')
    if not rating >= 70 and (diff == '2' or diff == '3'):
        await bot.finish(ev, 'ftr | byd 难度没有定数小于7的曲目')
    msg = random_music(rating, plus, diff)
    await bot.send(ev, msg)

@sv.on_prefix(['arcalias', 'Arcalias', 'ARCALIAS', 'arcali'])
async def alias(bot: NoneBot, ev: CQEvent):
    args: str = ev.message.extract_plain_text()
    gid = str(ev.group_id)
    if '+' in args:
        argslist = args.strip().split('+')
        if gid not in ali.list:
            song_id = argslist[0].strip()
            song_alias = argslist[1].strip()
            if song_id == song_alias:
                await bot.finish(ev, '请勿滥用该功能', at_sender=True)

            # 查询 song_id 的sid或者别名是否存在
            siddata =  await botarcapi('alias', {'songname': song_id})
            # 如果api存在
            if siddata['status'] == 0:
                result = asql.alias(siddata['content'][0])
                sid = result[0][0]
            # 如果api没有，查询本地数据库
            elif siddata['status'] == -7:
                result = asql.alias_sid(song_id)
                sid = result[0][0]
            # 如果曲目结果过多
            elif siddata['status'] == -8:
                await bot.finish(ev, f'需要添加别名的曲目 <{song_id}> 查询结果过多，请细化关键词', at_sender=True)
            else:
                await bot.finish(ev, '发送未知错误，请联系BOT管理员', at_sender=True)

            # 查询 song_alias 是否存在
            data = await botarcapi('alias', {'songname': song_alias})
            if data['status'] == 0:
                result = asql.alias(data['content'][0])
                im = MessageSegment.image(file=f'file:///{os.path.join(songdir, result[0][0], "base.jpg")}')
                await bot.finish(ev, f'{im}\n别名 <{song_alias}> 已绑定过曲目 -> {result[0][0]}', at_sender=True)
            # 如果api不存在
            elif data['status'] == -7:
                # 查询数据库是否存在该别名
                result = asql.alias(song_alias)
                # 投票
                if not result:
                    if priv.check_priv(ev, priv.SUPERUSER):
                        asql.add_alias(sid, song_alias)
                        await bot.send(ev, f'曲目 <{sid}> 成功添加别名 <{song_alias}>')
                    else:
                        ali.open(gid, sid, song_alias)
                        im = MessageSegment.image(file=f'file:///{os.path.join(songdir, sid, "base.jpg")}')
                        await bot.send(ev, f'已开启别名投票，在120s内同意票数5票通过，请输入 "同意别名" 和 "不同意别名"，请勿滥用该功能\n当前投票：\n{im}\nSongID：{sid}\n别名：{song_alias}')
                        await asyncio.sleep(60)
                        if gid in ali.list:
                            await bot.send(ev, f'投票时间剩余60s，当前同意票数 <{ali.list[gid]["vote"]}>')
                        await asyncio.sleep(60)
                        if gid in ali.list:
                            if ali.list[gid]['vote'] < 5:
                                await bot.send(ev, f'同意票不足5票，曲目 <{sid}> 添加别名 <{song_alias}> 操作已取消')
                                ali.close(gid)
                # 数据库存在发送曲目
                else:
                    im = MessageSegment.image(file=f'file:///{os.path.join(songdir, result[0][0], "base.jpg")}')
                    await bot.finish(ev, f'{im}\n别名 <{song_alias}> 已绑定过曲目 -> {result[0][0]}', at_sender=True)
            # 如果曲目结果过多
            elif data['status'] == -8:
                await bot.send(ev, f'当前别名 <{song_alias}> 找到多个相似别名，为防止冲突请输入其它别名', at_sender=True)
        else:
            await bot.send(ev, '正在进行添加别名，请勿重复', at_sender=True)
    else:
        songid = args
        data = await botarcapi('alias', {'songname': songid})
        if data['status'] == -7:
            await bot.send(ev, f'没有找到别名或曲目，你可以通过<arcali 曲名/别名 + 别名>指令添加别名，例如：arcali lasteternity + last2', at_sender=True)
        elif data['status'] == -8:
            aname: list[str] = data['content']['songs']
            if len(aname) <= 10:
                templist = asql.alias_for_list(aname)
                s = []
                for num, i in enumerate(templist):
                    s.append(f'\nSongID: {aname[num]}\nAlias: {" | ".join(i)}\n')
                await bot.send(ev, f'找到多个相似别名{"----------".join(s)}', at_sender=True)
            else:
                await bot.send(ev, '查询的结果过多，请缩小词条', at_sender=True)
        else:
            aname: list[str] = data['content']
            sid = asql.alias(aname[0])
            aliasname = asql.alias_sid(sid[0][0])
            local = [i[0] for i in aliasname]
            aliaslist = set(aname + local)
            im = MessageSegment.image(file=f'file:///{os.path.join(songdir, sid[0][0], "base.jpg")}')
            await bot.send(ev, f'{im}\n该曲目拥有的别名\n----------\n{list2newline(aliaslist)}', at_sender=True)

@sv.on_fullmatch(['同意别名'])
async def t(bot: NoneBot, ev: CQEvent):
    gid = str(ev.group_id)
    uid = ev.user_id
    if gid in ali.list:
        if uid in ali.list[gid]['user']:
            await bot.finish(ev, '您已进行过投票', at_sender=True)
        ali.add(gid, uid)
        await bot.send(ev, f'已同意票数：<{ali.list[gid]["vote"]}>')
        if ali.list[gid]['vote'] == 5:
            ali.close(gid)
            asql.add_alias(ali.songid, ali.alias)
            await bot.send(ev, f'曲目 <{ali.songid}> 成功添加别名 <{ali.alias}>')
            await bot.send_private_msg(user_id=SUPERUSERS[0], message=f'群组：{gid}\n将曲目 <{ali.songid}> 成功添加别名 <{ali.alias}>')

@sv.on_fullmatch(['不同意别名'])
async def f(bot: NoneBot, ev: CQEvent):
    gid = str(ev.group_id)
    uid = ev.user_id
    if gid in ali.list:
        if uid in ali.list[gid]['user']:
            await bot.finish(ev, '您已进行过投票', at_sender=True)
        ali.remove(gid, uid)
        await bot.send(ev, f'已同意票数：<{ali.list[str(gid)]["vote"]}>')

@sv.on_prefix(['archart', 'Archart', 'ARCHART', 'chart', 'Chart'])
async def chart(bot: NoneBot, ev: CQEvent):
    try:
        args: list[str]= ev.message.extract_plain_text().strip().split()
        if len(args) != 1:
            if args[-1].lower() in difficulty:
                name = ' '.join(args[:-1])
                diff = int(difficulty.index(args[-1].lower()) % 4)
            else:
                name = ' '.join(args)
                diff = 2
        else:
            name = args[0]
            diff = 2
        sname = asql.alias(name)
        if sname:
            name = sname[0][0]
        info = await draw_chart(name, diff)
    except Exception as e:
        logger.error(traceback.format_exc())
        info = f'Error：{type(e)}，请联系Bot管理员'
    await bot.send(ev, info, at_sender=True)

@sv.on_prefix(['arcbind', 'ARCBIND', 'Arcbind'])
async def bind(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    arcid: str = ev.message.extract_plain_text().strip()
    if not arcid:
        await bot.finish(ev, '请重新输入好友码或者用户名', at_sender=True)
    result = asql.get_user(qqid)
    if result:
        await bot.finish(ev, '您已绑定，如需要解绑请输入arcun', at_sender=True)
    try:
        data = await bindinfo(qqid, arcid)
        msg = f'用户 {data[0]}({data[1]}) 已成功绑定QQ {qqid}，现可使用 <b30> 指令查询B30成绩和 <arcre> 指令查询最近游玩'
    except ActionFailed:
        msg = f'用户 {arcid} 已成功绑定QQ {qqid}，现可使用 <b30> 指令查询B30成绩和 <arcre> 指令查询最近游玩'
    except ArcError as e:
        msg = f'Error：{e.error_str}'
    await bot.send(ev, msg, at_sender=True)

@sv.on_fullmatch(['arcun', 'Arcun', 'ARCUN'])
async def unbind(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    result = asql.get_user(qqid)
    if result:
        if asql.delete_user(qqid):
            msg = '解绑成功'
        else:
            msg = '数据库错误'
    else:
        msg = '您未绑定，无需解绑'
    await bot.send(ev, msg, at_sender=True)

@sv.on_prefix('arcset')
async def arcset(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    args: str = ev.message.extract_plain_text().strip()
    result = asql.get_user(qqid)
    if not result:
        await bot.finish(ev, NOTBIND, at_sender=True)
    if not args:
        await bot.finish(ev, '请重新输入设置的发送样式编号', at_sender=True)
    elif args.isdigit() and len(args) == 1 and args in ['0', '1', '2']:
        asql.update_mode(qqid, int(args))
    else:
        await bot.finish(ev, '请重新输入设置的发送样式编号', at_sender=True)
    await bot.send(ev, f'已将发送样式修改为 {f"-> [{args}]" if args != "0" else "[随机]"}', at_sender=True)

@sv.on_fullmatch('archelp')
async def archelp(bot: NoneBot, ev: CQEvent):
    await bot.send(ev, MessageSegment.image(file=f'file:///{helpimg}'))