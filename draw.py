import os, traceback, random, base64, random, aiofiles
from time import strftime, localtime, time, mktime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime
from io import BytesIO
from typing import Optional, Union
from hoshino.typing import MessageSegment
from hoshino.log import new_logger
from hoshino.config import NICKNAME

from .baa_error import ArcError
from .api import *
from .sql import asql

arc = os.path.dirname(__file__)
songdir = os.path.join(arc, 'img', 'songs')

BotNickname = ''

if isinstance(NICKNAME, str):
    if NICKNAME:
        BotNickname = NICKNAME
elif isinstance(NICKNAME, set):
    BotNickname = list(NICKNAME)[0]


diffdict = {
    '0' : ['pst', 'past'],
    '1' : ['prs', 'present'],
    '2' : ['ftr', 'future'],
    '3' : ['byd', 'beyond']
}

log = new_logger('Arcaea_draw')

class Data:
    
    _img = os.path.join(arc, 'img')
    _recent_dir = os.path.join(_img, 'recent')
    _diff_dir = os.path.join(_img, 'diff')
    _song_dir = os.path.join(_img, 'songs')
    _rank_dir = os.path.join(_img, 'rank')
    _font_dir = os.path.join(_img, 'font')
    _char_dir = os.path.join(_img, 'char')
    _ptt_dir = os.path.join(_img, 'ptt')
    _clear_dir = os.path.join(_img, 'clear')

    Exo_Regular = os.path.join(_font_dir, 'Exo-Regular.ttf')
    Kazesawa_Regular = os.path.join(_font_dir, 'Kazesawa-Regular.ttf')

    def __init__(self, project: str, info: dict) -> None:

        if project == 'recent' or project == 'best':
            _userinfo = info['account_info']
            _playinfo = info['recent_score'][0] if project == 'recent' else info['record']
            self._songinfo = info['songinfo'][0]

            self.arcid: str = _userinfo['code']
            self.arcname: str = _userinfo['name']
            self.ptt: int = _userinfo['rating']
            self.character: int = _userinfo['character']
            self.is_char_uncapped: bool = _userinfo['is_char_uncapped']
            self.is_char_uncapped_override: bool = _userinfo['is_char_uncapped_override']
            self.songid: str = _playinfo['song_id']
            self.difficulty: int = _playinfo['difficulty']
            self.score: int = _playinfo['score']
            self.sp_count: int = _playinfo['shiny_perfect_count']
            self.p_count: int = _playinfo['perfect_count']
            self.far_count: int = _playinfo['near_count']
            self.lost_count: int = _playinfo['miss_count']
            self.health: int = _playinfo['health']
            self.rating: float = _playinfo['rating']
            self.play_time: int = _playinfo['time_played']

        elif project == 'best30':
            _playinfo = info['account_info']
            self.b30: float = info['best30_avg']
            self.r10: float = info['recent10_avg']
            self.scorelist: list = info['best30_list']
            self.songinfolist: list = info['best30_songinfo']
            self.arcname: str = _playinfo['name']
            self.user_id: int = _playinfo['user_id']
            self.character: int = _playinfo['character']
            self.is_char_uncapped: bool = _playinfo['is_char_uncapped']
            self.is_char_uncapped_override: bool = _playinfo['is_char_uncapped_override']
            self.ptt: int = _playinfo['rating']

            t10 = 0
            num = len(self.scorelist) if len(self.scorelist) < 10 else 10
            for i in range(num):
                t10 += self.scorelist[i]['rating']
            
            self.maxptt: float = (self.b30 * 3 + t10 / num) / 4

        elif project == 'random':
            self._song_img = os.path.join(self._song_dir, info['song_id'], 'base.jpg' if info['difficulty'] != 3 else '3.jpg')
        else:
            raise TypeError
        
    async def recent(self, num: int) -> None:

        self.title: str = self._songinfo['name_jp'] if self._songinfo['name_jp'] else self._songinfo['name_en']
        self.artist: str = self._songinfo['artist']
        self.song_rating: int = self._songinfo['rating'] / 10
        if self.song_rating == 0.0 and self.rating != 0:
            self.song_rating = calc_rating(2, score=self.score, rating=self.rating)

        self._song_img = os.path.join(self._song_dir, self.songid, 'base.jpg' if self.difficulty != 3 else '3.jpg')
        _rank_img = os.path.join(self._rank_dir, f'grade_{self.isrank(self.score) if self.health != -1 else "F"}.png')
        _ptt_img = os.path.join(self._ptt_dir, self.pttbg(self.ptt))

        character_name = f'{self.character}u_icon.png' if self.is_char_uncapped ^ self.is_char_uncapped_override else f'{self.character}_icon.png'
        _character_img = os.path.join(self._char_dir, character_name)

        self.song_img = await self.async_img(self._song_img, 'songs', self.songid, self.difficulty)
        c_img = await self.async_img(_character_img, 'char', character_name)
        self.rank_img = await self.open_img(_rank_img)
        self.ptt_img = await self.open_img(_ptt_img)

        diffi = self.diff(self.difficulty)

        if num == 1:
            _info_img = os.path.join(self._recent_dir, 'info.png')
            _bg_img = os.path.join(self._recent_dir, 'bg.png')
            _diff_img = os.path.join(self._recent_dir, f'{diffi}.png')
            _black_line = os.path.join(self._recent_dir, 'black_line.png')
            _white_line = os.path.join(self._recent_dir, 'white_line.png')
            _time_img = os.path.join(self._recent_dir, 'time.png')
            
            self.character_img = c_img.resize((199, 200))
            self.bg_img = await self.open_img(_bg_img)
            self.time_img = await self.open_img(_time_img)
            self.ptt_img = (await self.open_img(_ptt_img)).resize((175, 175))
        elif num == 2:
            _black_bg = os.path.join(self._recent_dir, 'black_bg.png')
            _info_img = os.path.join(self._recent_dir, 'info_2.png')
            _diff_img = os.path.join(self._recent_dir, f'{diffi.upper()}_2.png')
            _diff_bg = os.path.join(self._recent_dir, f'{diffi.upper()}_BG.png')
            _black_line = os.path.join(self._recent_dir, 'black_line_2.png')
            _white_line = os.path.join(self._recent_dir, 'white_line_2.png')

            if self.health == -1:
                name = 'clear_fail.png'
            elif self.score > 1e7:
                name = 'clear_pure.png'
            elif self.lost_count == 0:
                name = 'clear_full.png'
            else:
                name = 'clear_normal.png'
            _clear_img = os.path.join(self._clear_dir, name)

            self.ptt_img = await self.open_img(_ptt_img)
            self.character_img = c_img.resize((143, 143))
            self.black_bg = await self.open_img(_black_bg)
            self.diff_bg = await self.open_img(_diff_bg)
            self.clear_img = await self.open_img(_clear_img)
        
        self.info_img = await self.open_img(_info_img)
        self.diff_img = await self.open_img(_diff_img)
        self.black_line = await self.open_img(_black_line)
        self.white_line = await self.open_img(_white_line)

    async def best30(self) -> None:

        _bg_img = os.path.join(self._img, 'b30_bg.png')
        _player_info = os.path.join(self._img, 'player_info.png')
        _ptt_img = os.path.join(self._ptt_dir, self.pttbg(self.ptt))
        _black_line = os.path.join(self._img, 'black_line.png')
        _time_img = os.path.join(self._img, 'time.png')
        character_name = f'{self.character}u_icon.png' if self.is_char_uncapped ^ self.is_char_uncapped_override else f'{self.character}_icon.png'
        _character_img = os.path.join(self._char_dir, character_name)

        c_img = await self.async_img(_character_img, 'char', character_name)
        self.character_img = c_img.resize((255, 255))
        self.bg_img = await self.open_img(_bg_img)
        self.player_info_img = await self.open_img(_player_info)
        self.ptt_img = (await self.open_img(_ptt_img)).resize((159, 159))
        self.black_line = await self.open_img(_black_line)
        self.time_img = await self.open_img(_time_img)

    async def songdata(self, num: int, info: dict) -> None:

        self._songinfo = self.songinfolist[num]

        self.songid: str = info['song_id']
        self.difficulty: int = info['difficulty']
        self.score: int = info['score']
        self.title: str = self._songinfo['name_jp'] if self._songinfo['name_jp'] else self._songinfo['name_en']
        self.song_rating: int = self._songinfo['rating'] / 10
        self.sp_count: int = info['shiny_perfect_count']
        self.p_count: int = info['perfect_count']
        self.far_count: int = info['near_count']
        self.lost_count: int = info['miss_count']
        self.health: int = info['health']
        self.rating: float = info['rating']
        self.play_time: int = info['time_played']

        _b30_img = os.path.join(self._img, 'b30_score_bg.png')
        _rank_img = os.path.join(self._rank_dir, f'grade_{self.isrank(self.score) if self.health != -1 else "F"}.png')
        _song_img = os.path.join(self._song_dir, self.songid, 'base.jpg' if self.difficulty != 3 else '3.jpg')
        _diff_img = os.path.join(self._diff_dir, f'{self.diff(self.difficulty).upper()}.png')
        _new_img = os.path.join(self._img, 'new.png')

        s_img = await self.async_img(_song_img, 'songs', self.songid, self.difficulty)
        self.song_img = s_img.resize((175, 175))
        self.b30_img = await self.open_img(_b30_img)
        self.rank_img = (await self.open_img(_rank_img)).resize((70, 40))
        self.diff_img = await self.open_img(_diff_img)
        self.new_img = await self.open_img(_new_img)

    async def open_img(self, img: str) -> Image.Image:
        async with aiofiles.open(img, 'rb') as f:
            im = Image.open(f.raw).convert('RGBA')
        return im

    async def async_img(self, img: str, project: str, data: str, diff: int = None) -> Image.Image:
        if not os.path.isfile(img):
            if diff:
                name = 'base.jpg' if diff != 3 else '3.jpg'
                new_img = await download_img(project, data, name)
            else:
                new_img = await download_img(project, data)
            if new_img:
                return await self.open_img(img)
        else:
            return await self.open_img(img)

    @staticmethod
    def pttbg(ptt: int) -> str:
        if ptt == -1:
            return 'rating_off.png'
        ptt /= 100
        if ptt < 3:
            name = 'rating_0.png'
        elif ptt < 7:
            name = 'rating_1.png'
        elif ptt < 10:
            name = 'rating_2.png'
        elif  ptt < 11:
            name = 'rating_3.png'
        elif  ptt < 12:
            name = 'rating_4.png'
        elif  ptt < 12.5:
            name = 'rating_5.png'
        else:
            name = 'rating_6.png'
        return name

    @staticmethod
    def isrank(score: int) -> str:
        if score < 86e5:
            rank = 'd'
        elif score < 89e5:
            rank = 'c'
        elif score < 92e5:
            rank = 'b'
        elif score < 95e5:
            rank = 'a'
        elif score < 98e5:
            rank = 'aa'
        elif score < 99e5:
            rank = 'ex'
        else:
            rank = 'ex+'
        return rank

    @staticmethod
    def diff(difficulty: int) -> str:
        if difficulty == 0:
            diff = 'pst'
        elif difficulty == 1:
            diff = 'prs'
        elif difficulty == 2:
            diff = 'ftr'
        else:
            diff = 'byd'
        return diff

    @staticmethod
    def draw_fillet(img: Image.Image, radii: int, position: str = 'all') -> Image.Image:

        circle = Image.new('L', (radii * 2, radii * 2), 0)  # 创建一个黑色背景的画布
        draw = ImageDraw.Draw(circle)
        draw.ellipse((0, 0, radii * 2, radii * 2), fill=255)  # 画白色圆形
        # 原图
        img = img.convert("RGBA")
        w, h = img.size
        alpha = Image.new('L', img.size, 255)
        if position == 'all':
            left_top = (0, 0, radii, radii)
            right_top = (radii, 0, radii * 2, radii)
            right_down = (radii, radii, radii * 2, radii * 2)
            left_down = (0, radii, radii, radii * 2)
        elif position == 'lt':
            left_top = (0, 0, radii, radii)
            right_top = (0, 0, 0, 0)
            right_down = (0, 0, 0, 0)
            left_down = (0, 0, 0, 0)
        elif position == 'rt':
            left_top = (0, 0, 0, 0)
            right_top = (radii, 0, radii * 2, radii)
            right_down = (0, 0, 0, 0)
            left_down = (0, 0, 0, 0)
        elif position == 'rd':
            left_top = (0, 0, 0, 0)
            right_top = (0, 0, 0, 0)
            right_down = (radii, radii, radii * 2, radii * 2)
            left_down = (0, 0, 0, 0)
        elif position == 'ld':
            left_top = (0, 0, 0, 0)
            right_top = (0, 0, 0, 0)
            right_down = (0, 0, 0, 0)
            left_down = (0, radii, radii, radii * 2)
        else:
            raise TypeError

        # 画4个角（将整圆分离为4个部分）
        alpha = Image.new('L', img.size, 255)
        alpha.paste(circle.crop(left_top), (0, 0))  # 左上角
        alpha.paste(circle.crop(right_top), (w - radii, 0))  # 右上角
        alpha.paste(circle.crop(right_down), (w - radii, h - radii))  # 右下角
        alpha.paste(circle.crop(left_down), (0, h - radii))  # 左下角
        # 白色区域透明可见，黑色区域不可见
        img.putalpha(alpha)

        return img

    @property
    def songbg(self) -> str:
        return self._song_img

    @property
    def song_bg_img(self) -> Image.Image:
        bg_w, bg_h = self.song_img.size
        fix_w, fix_h = [1200, 900]

        scale = fix_w / bg_w
        w = int(scale * bg_w)
        h = int(scale * bg_h)

        re = self.song_img.resize((w, h))
        crop_height = (h - fix_h) / 2

        crop_img = re.crop((0, crop_height, w, h - crop_height))

        bg_gb = crop_img.filter(ImageFilter.GaussianBlur(3))
        bg_bn = ImageEnhance.Brightness(bg_gb).enhance(2 / 4.0)

        return bg_bn

class DrawText:

    def __init__(self, 
                image: Image.Image,
                X: float,
                Y: float,
                size: int,
                text: str,
                font: str,
                po: int = 2,
                color: tuple = (255, 255, 255, 255),
                stroke_width: int = 0,
                stroke_fill: tuple = (0, 0, 0, 0),
                anchor: str = 'lt') -> None:
        self._img = image
        self._pos = (X, Y)
        self._pos_2 = (X + po, Y + po)
        self._text = str(text)
        self._font = ImageFont.truetype(font, size)
        self._color = color
        self._stroke_width = stroke_width
        self._stroke_fill = stroke_fill
        self._anchor = anchor

    def draw_text(self, multiline: Optional[bool] = False) -> Image.Image:

        text_img = Image.new('RGBA', self._img.size, (255, 255, 255, 0))
        draw_img = ImageDraw.Draw(text_img)
        if multiline:
            draw_img.multiline_text(self._pos, '\n'.join([i for i in self._text]), self._color, self._font, self._anchor, stroke_width=self._stroke_width, stroke_fill=self._stroke_fill)
        else:
            draw_img.text(self._pos, self._text, self._color, self._font, self._anchor, stroke_width=self._stroke_width, stroke_fill=self._stroke_fill)
        return Image.alpha_composite(self._img, text_img)

    def draw_partial_opacity(self) -> Image.Image:

        text_img = Image.new('RGBA', self._img.size, (255, 255, 255, 0))
        draw_img = ImageDraw.Draw(text_img)
        draw_img.text(self._pos_2, self._text, (0, 0, 0, 128), self._font, self._anchor, stroke_width=self._stroke_width, stroke_fill=self._stroke_fill)
        draw_img.text(self._pos, self._text, self._color, self._font, self._anchor, stroke_width=self._stroke_width, stroke_fill=self._stroke_fill)
        return Image.alpha_composite(self._img, text_img)

def calc_rating(project: int, songrating: Optional[float] = 0, score: Optional[int] = 0, rating: Optional[float] = 0) -> Union[int, float]:
    if project == 0:
        '''用定数和分数算ptt'''
        if score >= 1e7:
            result = songrating + 2
        elif score >= 98e5:
            result = songrating + 1 + (score - 98e5) / 2e5
        else:
            result = songrating + (score - 95e5) / 3e5
    elif project == 1:
        '''用定数和ptt算分数'''
        if rating - 2 == songrating:
            result = 1e7
        elif rating - 2 < songrating and rating >= songrating:
            result = 98e5 + (rating - songrating - 1) * 2e5
        elif rating < songrating:
            result = 95e5 + (rating - songrating) * 3e5
    elif project == 2:
        '''用分数和ptt算定数'''
        if score >= 1e7:
            result = rating - 2
        elif score >= 98e5:
            result = rating - 1 - (score - 98e5) / 2e5
        else:
            result = rating - (score - 95e5) / 3e5
        result = float(f'{result:.1f}')

    return result

def playtime(date: int) -> str:
    timearray = localtime(date / 1000)
    datetime = strftime('%Y-%m-%d %H:%M:%S', timearray)
    return datetime

def timediff(date: int) -> float:
    now = mktime(datetime.now().timetuple())
    time_diff = (now - date / 1000) / 86400
    return time_diff

def img2b64(img: Image.Image) -> str:
    bytesio = BytesIO()
    img.save(bytesio, 'PNG')
    bytes = bytesio.getvalue()
    base64_str = base64.b64encode(bytes).decode()
    return 'base64://' + base64_str

async def draw_info(arcid: Union[int, str]) -> str:
    try:
        userdict = {
            'usercode' : str(arcid),
            'withsonginfo' : 'true'
        }

        log.info(f'Starting BotArcAPI -> {playtime(time() * 1000)}')
        info = await botarcapi('best30', userdict)
        log.info(f'Ending BotArcAPI and Starting Draw Piture -> {playtime(time() * 1000)}')
        if isinstance(info, dict):
            
            data = Data('best30', info['content'])
            await data.best30()
            
            ptt = f'{data.ptt / 100:.2f}' if data.ptt != -1 else '--'
            # 底图
            im = Image.new('RGBA', (1800, 3000))
            im.alpha_composite(data.bg_img)
            # 玩家信息底图
            im.alpha_composite(data.player_info_img, (111, 213))
            # 搭档
            im.alpha_composite(data.character_img, (773, 222))
            # ptt背景
            im.alpha_composite(data.ptt_img, (872, 338))
            # ptt
            im = DrawText(im, 950, 415, 45, ptt, data.Exo_Regular, anchor='mm', stroke_width=1, stroke_fill=(0, 0, 0, 255)).draw_text()
            # arcname
            im = DrawText(im, 537, 310, 44, data.arcname, data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # arcid
            im = DrawText(im, 537, 375, 40, arcid, data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # r10
            im = DrawText(im, 1178, 285, 42, f'{data.r10:.4f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # maxptt
            im = DrawText(im, 1450, 351, 36, f'{data.maxptt:.4f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # b30
            im = DrawText(im, 1178, 416, 42, f'{data.b30:.4f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # 30个成绩
            bg_y = 500
            for num, i in enumerate(data.scorelist):
                if num == 30:
                    break
                # 横3竖10
                if num % 3 == 0:
                    bg_y += 245 if num != 0 else 0
                    bg_x = 20
                else:
                    bg_x += 590

                await data.songdata(num, i)

                # 背景
                im.alpha_composite(data.b30_img, (bg_x + 40, bg_y))
                # 难度
                im.alpha_composite(data.diff_img, (bg_x + 40, bg_y + 25))
                # 曲绘
                im.alpha_composite(data.song_img, (bg_x + 70, bg_y + 50))
                # rank
                im.alpha_composite(data.rank_img, (bg_x + 425, bg_y + 120))
                # 黑线
                im.alpha_composite(data.black_line, (bg_x + 70, bg_y + 48))
                # 时间
                im.alpha_composite(data.time_img, (bg_x + 245, bg_y + 205))
                # 曲名
                im = DrawText(im, bg_x + 290, bg_y + 35, 20, data.title, data.Kazesawa_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
                # songrating
                sr = f'{data.song_rating:.1f}'
                if data.song_rating < 10:
                    im = DrawText(im, bg_x + 55, bg_y + 110, 20, sr[0], data.Exo_Regular, anchor='mm').draw_text()
                    im = DrawText(im, bg_x + 55, bg_y + 120, 20, sr[1], data.Exo_Regular, anchor='mm').draw_text()
                    im = DrawText(im, bg_x + 55, bg_y + 140, 20, sr[2], data.Exo_Regular, anchor='mm').draw_text()
                else:
                    im = DrawText(im, bg_x + 55, bg_y + 100, 20, sr[0], data.Exo_Regular, anchor='mm').draw_text()
                    im = DrawText(im, bg_x + 55, bg_y + 120, 20, sr[1], data.Exo_Regular, anchor='mm').draw_text()
                    im = DrawText(im, bg_x + 55, bg_y + 130, 20, sr[2], data.Exo_Regular, anchor='mm').draw_text()
                    im = DrawText(im, bg_x + 55, bg_y + 150, 20, sr[3], data.Exo_Regular, anchor='mm').draw_text()
                # 名次
                im = DrawText(im, bg_x + 530, bg_y + 35, 45, num + 1, data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
                # 分数
                im = DrawText(im, bg_x + 260, bg_y + 75, 45, f'{data.score:,}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='lm').draw_text()
                # PURE 
                im = DrawText(im, bg_x + 260, bg_y + 130, 30, 'P', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                im = DrawText(im, bg_x + 290, bg_y + 130, 25, data.p_count, data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                im = DrawText(im, bg_x + 355, bg_y + 130, 20, f'| +{data.sp_count}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                # FAR
                im = DrawText(im, bg_x + 260, bg_y + 162, 30, 'F', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                im = DrawText(im, bg_x + 290, bg_y + 162, 25, data.far_count, data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                # LOST
                im = DrawText(im, bg_x + 260, bg_y + 194, 30, 'L', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                im = DrawText(im, bg_x + 290, bg_y + 194, 25, data.lost_count, data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                # Rating
                im = DrawText(im, bg_x + 360, bg_y + 194, 25, f'Rating | {data.rating:.3f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
                # time
                im = DrawText(im, bg_x + 395, bg_y + 215, 20, playtime(data.play_time), data.Exo_Regular, anchor='mm').draw_text()
                # new
                if timediff(data.play_time) <= 7:
                    im.alpha_composite(data.new_img, (bg_x + 32, bg_y - 8))

            im = DrawText(im, 900, 2990, 25, f'Draw Time {playtime(time() * 1000)}  |  Generated by {BotNickname}  |  Powered by project Arcaea', data.Exo_Regular, anchor='ms').draw_partial_opacity()
            # save
            log.info(f'Ending Draw Piture -> {playtime(time() * 1000)}')
            base64str = img2b64(im)
            msg = MessageSegment.image(base64str)
        else:
            msg = info
        return msg
    except ArcError as e:
        log.error(f'Error: {e.error_str}')
        return e.error_str
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'Error：{type(e)}，请联系Bot管理员'
        return msg

async def draw_score(project: str, arcid: int, mode: int = 0, name: str = None, diff: int = None) -> Union[MessageSegment, str]:
    try:
        log.info(f'Starting BotArcAPI -> {playtime(time() * 1000)}')
        if project == 'recent':
            userdict = {
                'usercode' : str(arcid),
                'withsonginfo' : 'true'
            }
            userinfo = await botarcapi(project, userdict)
            data = Data('recent', userinfo['content'])

        elif project == 'best':

            userdict = {
                'usercode' : str(arcid),
                'songname' : name,
                'difficulty' : diff,
                'withsonginfo' : 'true'
            }
            userinfo = await botarcapi(project, userdict)
            if userinfo['status'] == -8:
                return f'找到{len(userinfo["content"]["songs"])}个相似曲目：{" | ".join(userinfo["content"]["songs"])}'
            elif userinfo['status'] == -7:
                return f'未找到曲目 -> {name}'
            elif userinfo['status'] == 0:
                data = Data('best', userinfo['content'])

        if mode == 0:
            randint = random.randint(1, 50) % 2 + 1
        else:
            randint = mode

        await data.recent(randint)

        ptt = f'{data.ptt / 100:.2f}' if data.ptt != -1 else '--'

        diffi = data.diff(data.difficulty)

        log.info(f'Ending BotArcAPI and Starting Draw Piture -> {playtime(time() * 1000)}')
        if randint == 1:
        
            im = Image.new('RGBA', (1200, 900))
            # 底图
            im.alpha_composite(data.song_bg_img)
            # 白线
            im.alpha_composite(data.white_line, (140, 132))
            # info
            im.alpha_composite(data.info_img, (155, 75))
            # 搭档
            im.alpha_composite(data.character_img, (70, 35))
            # ptt背景
            im.alpha_composite(data.ptt_img, (615, 50))
            # 成绩背景
            im.alpha_composite(data.bg_img, (50, 268))
            # 黑线
            im.alpha_composite(data.black_line, (50, 333))
            # 曲绘
            song_img_fillet = data.draw_fillet(data.song_img, 25, 'ld')
            im.alpha_composite(song_img_fillet, (50, 338))
            # 难度
            im.alpha_composite(data.diff_img, (50, 800))
            # 时间
            im.alpha_composite(data.time_img, (562, 800))
            # 评价
            im.alpha_composite(data.rank_img, (900, 630))
            # 昵称
            im = DrawText(im, 455, 105, 38, data.arcname, data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # 好友码
            im = DrawText(im, 455, 165, 35, f'ArcID | {data.arcid}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # ptt
            im = DrawText(im, 702, 135, 50, ptt, data.Exo_Regular, stroke_width=1, stroke_fill=(0, 0, 0, 255), anchor='mm').draw_text()
            # rating
            im = DrawText(im, 890, 105, 40, f'RATING', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            im = DrawText(im, 890, 165, 40, f'{data.rating:.3f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # 曲名
            im = DrawText(im, 600, 300, 45, data.title, data.Kazesawa_Regular, color=(0, 0, 0, 255), anchor='mm').draw_text()
            # 分数
            im = DrawText(im, 600, 410, 100, f'{data.score:,}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='lm').draw_text()
            # Pure
            im = DrawText(im, 600, 550, 55, 'Pure', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Player Pure
            im = DrawText(im, 800, 550, 55, f'{data.p_count}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            im = DrawText(im, 960, 550, 40, f'| +{data.sp_count}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Far
            im = DrawText(im, 600, 635, 55, 'Far', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Player Far
            im = DrawText(im, 800, 635, 55, data.far_count, data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Lost
            im = DrawText(im, 600, 720, 55, 'Lost', data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Player Lost
            im = DrawText(im, 800, 720, 55, data.lost_count, data.Exo_Regular, color=(0, 0, 0, 255), anchor='ls').draw_text()
            # Difficultys
            im = DrawText(im, 306, 825, 40, f'{diffi.upper()} | {data.song_rating}', data.Exo_Regular, anchor='mm').draw_text()
            # Time
            im = DrawText(im, 858, 825, 40, playtime(data.play_time), data.Exo_Regular, anchor='mm').draw_text()
        
        elif randint == 2:

            r, g, b = Image.open(data._song_img).resize((1, 1)).load()[0, 0]
            im = Image.new('RGBA', (712, 1412), (r, g, b, 255))
            # 黑色透明
            im.alpha_composite(data.black_bg)
            # info
            im.alpha_composite(data.info_img, (130, 50))
            # 黑线
            im.alpha_composite(data.black_line, (156, 97))
            # 搭档
            im.alpha_composite(data.character_img, (28, 15))
            # ptt
            im.alpha_composite(data.ptt_img, (407, 30))
            # 难度背景
            im.alpha_composite(data.diff_bg, (100, 175))
            # 曲绘
            im.alpha_composite(data.song_img.convert('RGBA').resize((474, 474)), (119, 194))
            # 难度定数
            im.alpha_composite(data.diff_img, (119, 220))
            # 白线
            im.alpha_composite(data.white_line, (31, 800))
            # clear
            im.alpha_composite(data.clear_img, (16, 815))
            # rank
            im.alpha_composite(data.rank_img, (466, 1160))
            # 昵称
            im = DrawText(im, 295, 60, 30, data.arcname, data.Exo_Regular, color=(0, 0, 0, 255), anchor='mt').draw_text()
            # Rating
            im = DrawText(im, 572, 60, 30, 'RATING', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mt').draw_text()
            # arcid
            im = DrawText(im, 295, 105, 20, f'ArcID | {data.arcid}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mt').draw_text()
            # rating
            im = DrawText(im, 572, 105, 20, f'{data.rating:.3f}', data.Exo_Regular, color=(0, 0, 0, 255), anchor='mt').draw_text()
            # ptt
            im = DrawText(im, 466, 87, 30, ptt, data.Exo_Regular, stroke_width=1, stroke_fill=(0, 0, 0, 255), anchor='mm').draw_text()
            # 难度
            im = DrawText(im, 135, 240, 22, f'{diffi.upper()} | {data.song_rating}', data.Exo_Regular, anchor='lm').draw_text()
            # 曲名
            im = DrawText(im, 356, 704, 40, data.title, data.Kazesawa_Regular, anchor='mt').draw_partial_opacity()
            # 曲师
            im = DrawText(im, 356, 755, 20, data.artist, data.Kazesawa_Regular, anchor='mt').draw_partial_opacity()
            # 分数
            im = DrawText(im, 356, 925, 80, f'{data.score:,}', data.Exo_Regular, anchor='mt').draw_partial_opacity()
            # Pure
            im = DrawText(im, 74, 1090, 60, 'Pure', data.Kazesawa_Regular, anchor='ls').draw_partial_opacity()
            # Player Pure
            im = DrawText(im, 356, 1090, 60, data.p_count, data.Exo_Regular, anchor='ls').draw_partial_opacity()
            # Player SP
            im = DrawText(im, 510, 1090, 35, f'| +{data.sp_count}', data.Exo_Regular, anchor='ls').draw_partial_opacity()
            # Far
            im = DrawText(im, 74, 1175, 60, 'Far', data.Kazesawa_Regular, anchor='ls').draw_partial_opacity()
            # Player Far
            im = DrawText(im, 356, 1175, 60, data.far_count, data.Exo_Regular, anchor='ls').draw_partial_opacity()
            # Lost
            im = DrawText(im, 74, 1255, 60, 'Lost', data.Kazesawa_Regular, anchor='ls').draw_partial_opacity()
            # Player Lost
            im = DrawText(im, 356, 1255, 60, data.lost_count, data.Exo_Regular, anchor='ls').draw_partial_opacity()
            # Playtime
            im = DrawText(im, 356, 1340, 30, f'PlayTime | {playtime(data.play_time)}', data.Exo_Regular, anchor='mm').draw_partial_opacity()
            # info
            im = DrawText(im, 356, 1400, 20, f'Generated by {BotNickname} | Powered by project Arcaea', data.Exo_Regular, anchor='ms').draw_partial_opacity()

        log.info(f'Ending Draw Piture -> {playtime(time() * 1000)}')
        base64str = img2b64(im)
        msg = MessageSegment.image(base64str)
    except ArcError as e:
        log.error(e.error_str)
        msg = f'Error：{e.error_str}'
    except Exception as e:
        log.error(traceback.format_exc())
        msg = f'Error：{type(e)}，请联系Bot管理员'
    return msg

def random_music(rating: int, plus: bool, diff: int) -> str:

    difficulty = 0
    if diff:
        difficulty = diff
        song = asql.get_song(rating, plus, diffdict[str(diff)][0])
    elif plus:
        song = asql.get_song(rating, plus)
    else:
        song = asql.get_song(rating)

    if rating % 10 != 0 and diff:
        for i in song:
            if i[diff + 4] != rating:
                song.remove(i)

    if not song:
        return '未找到符合的曲目'

    random_list_int = random.randint(0, len(song) - 1)
    songinfo = song[random_list_int]

    songrating = [str(i / 10) for n, i in enumerate(songinfo) if n >= 4 and i != -1]
    diffc = [diffdict[str(_)][0].upper() for _ in range(len(songrating))]

    songs = {
        'song_id': songinfo[0],
        'difficulty': difficulty
    }

    data = Data('random', songs)
    img = MessageSegment.image(file=f'file:///{data.songbg}')

    msg = f'''{img}
Song: {songinfo[2] if songinfo[2] else songinfo[1]}
Artist: {songinfo[3]}
Difficulty: {' | '.join(diffc)}
Rating: {' | '.join(songrating)}'''

    return msg

async def bindinfo(qqid: int, arcid: int) -> str:
    try:
        info = await botarcapi('recent', {'usercode': arcid})
        asql.bind_user(qqid, arcid)
        return f'用户 {info["content"]["account_info"]["name"]}({arcid}) 已成功绑定QQ {qqid}，现可使用 <arcinfo> 指令查询B30成绩和 <arcre> 指令查询最近游玩'
    except ArcError as e:
        return f'Error：{e.error_str}'