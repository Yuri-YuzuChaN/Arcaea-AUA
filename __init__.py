from nonebot import CommandSession, NoneBot
from hoshino import Service, priv, MessageSegment
from hoshino.service import sucmd
from hoshino.typing import CQEvent

from .sql import asql
from .api import *
from .draw import (
    arc,
    draw_info,
    draw_score,
    bindinfo,
    random_music,
)

help = '请开启Arcaea插件使用 <archelp> 指令`'

helpimg = os.path.join(arc, 'img', 'help.png')

diffdict = {
    '0' : ['pst', 'past'],
    '1' : ['prs', 'present'],
    '2' : ['ftr', 'future'],
    '3' : ['byd', 'beyond']
}

NOTBIND = '账号尚未绑定，请输入 arcbind arcid(好友码)'

difficulty = ['0', '1', '2', '3', 'pst', 'prs', 'ftr', 'byd', 'past', 'present', 'future', 'beyond']

sv = Service('Arcaea', manage_priv=priv.ADMIN, enable_on_default=False, visible=True, help_=help)

@sv.on_prefix(['arcinfo', 'ARCINFO', 'Arcinfo'])
async def arcinfo(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    args: str = ev.message.extract_plain_text().strip()
    if ev.message[0].type == 'at':
        qqid = int(ev.message[0].data['qq'])
    result = asql.get_user(qqid)
    if args:
        if args.isdigit() and len(args) == 9:
            arcid = args
        else:
            await bot.finish(ev, '仅可以使用好友码查询', at_sender=True)
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
        if args.isdigit() and len(args) == 9:
            arcid = args
            mode = 0
        else:
            await bot.finish(ev, '请输入正确的好友码', at_sender=True)
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
            if not 10 <= rating < 116:
                await bot.finish(ev, '请输入定数：1-11.5|9+|10+')
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
                await bot.finish(ev, '请输入定数：1-11.5 | 9+ | 10+')
    elif len(args) == 2:
        try:
            rating = float(args[0]) * 10
            plus = False
            if not 10 <= rating < 116:
                await bot.finish(ev, '请输入定数：1-11.5 | 9+ | 10+')
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
                await bot.finish(ev, '请输入定数：1-11.5 | 9+ | 10+')
    else:
        await bot.finish(ev, '请输入正确参数')
    if not rating >= 70 and (diff == '2' or diff == '3'):
        await bot.finish(ev, 'ftr | byd 难度没有定数小于7的曲目')
    msg = random_music(rating, plus, diff)
    await bot.send(ev, msg)

@sv.on_prefix(['arcbind', 'ARCBIND', 'Arcbind'])
async def bind(bot: NoneBot, ev: CQEvent):
    qqid = ev.user_id
    arcid: str = ev.message.extract_plain_text().strip()
    binderror = '请重新输入好友码\n例如：arcbind 114514810'
    if not arcid.isdigit() and len(arcid) != 9:
        await bot.finish(ev, binderror, at_sender=True)
    result = asql.get_user(qqid)
    if result:
        await bot.finish(ev, '您已绑定，如需要解绑请输入arcun', at_sender=True)
    msg = await bindinfo(qqid, arcid)
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