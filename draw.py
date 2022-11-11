import os, traceback, random, base64, aiohttp
from time import strftime, localtime, time, mktime
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
from datetime import datetime
from io import BytesIO
from typing import Optional, Union, Tuple

from hoshino.typing import MessageSegment

from .aua_error import ArcError
from .api import botarcapi, download_img
from .sql import asql
from . import *

img = os.path.join(arc, 'img')
recent_dir = os.path.join(img, 'recent')
diff_dir = os.path.join(img, 'diff')
song_dir = os.path.join(img, 'songs')
rank_dir = os.path.join(img, 'rank')
font_dir = os.path.join(img, 'font')
char_dir = os.path.join(img, 'char')
ptt_dir = os.path.join(img, 'ptt')
clear_dir = os.path.join(img, 'clear')

Exo_Regular = os.path.join(font_dir, 'Exo-Regular.ttf')
Exo_Semibold = os.path.join(font_dir, 'Exo-Semibold.ttf')
Kazesawa_Regular = os.path.join(font_dir, 'Kazesawa-Regular.ttf')
Kazesawa_Semibold = os.path.join(font_dir, 'Kazesawa-Semibold.ttf')

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
    elif ptt < 11:
        name = 'rating_3.png'
    elif ptt < 12:
        name = 'rating_4.png'
    elif ptt < 12.5:
        name = 'rating_5.png'
    elif ptt < 13:
        name = 'rating_6.png'
    else:
        name = 'rating_7.png'
    return name

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

def list2newline(text: list) -> str:
    return '\n'.join(text)

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

class DrawText:

    def __init__(self, image: ImageDraw.ImageDraw, font: str) -> None:
        self._img = image
        self._font = font

    def get_box(self, text: str, size: int):
        return ImageFont.truetype(self._font, size).getbbox(text)

    def draw(self,
            pos_x: int,
            pos_y: int,
            size: int,
            text: str,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            anchor: str = 'lt',
            stroke_width: int = 0,
            stroke_fill: Tuple[int, int, int, int] = (0, 0, 0, 0),
            multiline: bool = False):

        font = ImageFont.truetype(self._font, size)
        if multiline:
            self._img.multiline_text((pos_x, pos_y), str(text), color, font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)
        else:
            self._img.text((pos_x, pos_y), str(text), color, font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)
    
    def draw_partial_opacity(self,
            pos_x: int,
            pos_y: int,
            size: int,
            text: str,
            po: int = 2,
            color: Tuple[int, int, int, int] = (255, 255, 255, 255),
            anchor: str = 'lt',
            stroke_width: int = 0,
            stroke_fill: Tuple[int, int, int, int] = (0, 0, 0, 0)):

        font = ImageFont.truetype(self._font, size)
        self._img.text((pos_x + po, pos_y + po), str(text), (0, 0, 0, 128), font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)
        self._img.text((pos_x, pos_y), str(text), color, font, anchor, stroke_width=stroke_width, stroke_fill=stroke_fill)

class Data:

    def __init__(self, project: str, info: dict) -> None:

        if project == 'recent' or project == 'best' or project == 'pack':
            if project == 'pack':
                _playinfo = info
            else:
                _userinfo = info['account_info']
                self.arcid: str = _userinfo['code']
                self.arcname: str = _userinfo['name']
                self.ptt: int = _userinfo['rating']
                self.character: int = _userinfo['character']
                self.is_char_uncapped: bool = _userinfo['is_char_uncapped']
                self.is_char_uncapped_override: bool = _userinfo['is_char_uncapped_override']

                _playinfo = info['recent_score'][0] if project == 'recent' else info['record']
                self._songinfo = info['songinfo'][0]

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
            self.overflowlist: list = info['best30_overflow']
            self.overflowinfolist: list = info['best30_overflow_songinfo']
            self.arcname: str = _playinfo['name']
            self.core: str = _playinfo['code']
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
            self._song_img = os.path.join(song_dir, info['song_id'], 'base.jpg' if info['difficulty'] != 3 else '3.jpg')
        else:
            raise TypeError
        
    async def recent(self, randint: int) -> Image.Image:
        """
        Draw player recent score or best score
        """

        title: str = self._songinfo['name_jp'] if self._songinfo['name_jp'] else self._songinfo['name_en']
        artist: str = self._songinfo['artist']
        song_rating: int = self._songinfo['rating'] / 10
        if song_rating == 0.0 and self.rating != 0:
            song_rating = calc_rating(2, score=self.score, rating=self.rating)

        _song_img = os.path.join(song_dir, self.songid, 'base.jpg' if self.difficulty != 3 else '3.jpg')
        _rank_img = os.path.join(rank_dir, f'grade_{isrank(self.score) if self.health != -1 else "F"}.png')
        _ptt_img = os.path.join(ptt_dir, pttbg(self.ptt))

        character_name = f'{self.character}u_icon.png' if self.is_char_uncapped ^ self.is_char_uncapped_override else f'{self.character}_icon.png'
        _character_img = os.path.join(char_dir, character_name)

        song_img = await self.async_img(_song_img, 'songs', self.songid, self.difficulty)
        song_img_fillet = draw_fillet(song_img, 25, 'ld')
        c_img = await self.async_img(_character_img, 'char', character_name)
        rank_img = Image.open(_rank_img).convert('RGBA')
        ptt_img = Image.open(_ptt_img).convert('RGBA')

        ptt = f'{self.ptt / 100:.2f}' if self.ptt != -1 else '--'
        diffi = diff(self.difficulty)

        if randint == 1:
            _info_img = os.path.join(recent_dir, 'info.png')
            _bg_img = os.path.join(recent_dir, 'bg.png')
            _diff_img = os.path.join(recent_dir, f'{diffi}.png')
            _black_line = os.path.join(recent_dir, 'black_line.png')
            _white_line = os.path.join(recent_dir, 'white_line.png')
            _time_img = os.path.join(recent_dir, 'time.png')

            info_img = Image.open(_info_img).convert('RGBA')
            diff_img = Image.open(_diff_img).convert('RGBA')
            black_line = Image.open(_black_line).convert('RGBA')
            white_line = Image.open(_white_line).convert('RGBA')
            
            character_img = c_img.resize((199, 200))
            bg_img = Image.open(_bg_img).convert('RGBA')
            time_img = Image.open(_time_img).convert('RGBA')
            ptt_img = Image.open(_ptt_img).convert('RGBA').resize((175, 175))

            im = Image.new('RGBA', (1200, 900))
            # 底图
            bg_w, bg_h = song_img.size
            fix_w, fix_h = [1200, 900]

            scale = fix_w / bg_w
            w = int(scale * bg_w)
            h = int(scale * bg_h)

            re = song_img.resize((w, h))
            crop_height = (h - fix_h) / 2

            crop_img = re.crop((0, crop_height, w, h - crop_height))

            bg_gb = crop_img.filter(ImageFilter.GaussianBlur(3))
            bg_bn = ImageEnhance.Brightness(bg_gb).enhance(2 / 4.0)

            im.alpha_composite(bg_bn)
            # 白线
            im.alpha_composite(white_line, (140, 132))
            # info
            im.alpha_composite(info_img, (155, 75))
            # 搭档
            im.alpha_composite(character_img, (70, 35))
            # ptt背景
            im.alpha_composite(ptt_img, (615, 50))
            # 成绩背景
            im.alpha_composite(bg_img, (50, 268))
            # 黑线
            im.alpha_composite(black_line, (50, 333))
            # 曲绘
            im.alpha_composite(song_img_fillet, (50, 338))
            # 难度
            im.alpha_composite(diff_img, (50, 800))
            # 时间
            im.alpha_composite(time_img, (562, 800))
            # 评价
            im.alpha_composite(rank_img, (900, 630))

            text_im = ImageDraw.Draw(im)
            font = DrawText(text_im, Exo_Regular)
            jpfont = DrawText(text_im, Kazesawa_Regular)
            # 昵称
            font.draw(455, 105, 38, self.arcname, color=(0, 0, 0, 255), anchor='mm')
            # 好友码
            font.draw(455, 165, 35, f'ArcID | {self.arcid}', color=(0, 0, 0, 255), anchor='mm')
            # ptt
            font.draw(702, 135, 50, ptt, stroke_width=1, stroke_fill=(0, 0, 0, 255), anchor='mm')
            # rating
            font.draw(890, 105, 40, f'RATING', color=(0, 0, 0, 255), anchor='mm')
            font.draw(890, 165, 40, f'{self.rating:.3f}', color=(0, 0, 0, 255), anchor='mm')
            # 曲名
            jpfont.draw(600, 300, 45, title, color=(0, 0, 0, 255), anchor='mm')
            # 分数
            font.draw(600, 410, 100, f'{self.score:,}', color=(0, 0, 0, 255), anchor='lm')
            # Pure
            font.draw(600, 550, 55, 'Pure', color=(0, 0, 0, 255), anchor='ls')
            # Player Pure
            font.draw(800, 550, 55, f'{self.p_count}', color=(0, 0, 0, 255), anchor='ls')
            font.draw(960, 550, 40, f'| +{self.sp_count}', color=(0, 0, 0, 255), anchor='ls')
            # Far
            font.draw(600, 635, 55, 'Far', color=(0, 0, 0, 255), anchor='ls')
            # Player Far
            font.draw(800, 635, 55, self.far_count, color=(0, 0, 0, 255), anchor='ls')
            # Lost
            font.draw(600, 720, 55, 'Lost', color=(0, 0, 0, 255), anchor='ls')
            # Player Lost
            font.draw(800, 720, 55, self.lost_count, color=(0, 0, 0, 255), anchor='ls')
            # Difficultys
            font.draw(306, 825, 40, f'{diffi.upper()} | {song_rating}', anchor='mm')
            # Time
            font.draw(858, 825, 40, playtime(self.play_time), anchor='mm')

        elif randint == 2:
            _black_bg = os.path.join(recent_dir, 'black_bg.png')
            _info_img = os.path.join(recent_dir, 'info_2.png')
            _diff_img = os.path.join(recent_dir, f'{diffi.upper()}_2.png')
            _diff_bg = os.path.join(recent_dir, f'{diffi.upper()}_BG.png')
            _black_line = os.path.join(recent_dir, 'black_line_2.png')
            _white_line = os.path.join(recent_dir, 'white_line_2.png')

            if self.health == -1:
                name = 'clear_fail.png'
            elif self.score > 1e7:
                name = 'clear_pure.png'
            elif self.lost_count == 0:
                name = 'clear_full.png'
            else:
                name = 'clear_normal.png'
            _clear_img = os.path.join(clear_dir, name)

            info_img = Image.open(_info_img).convert('RGBA')
            ptt_img = Image.open(_ptt_img).convert('RGBA').resize((119, 119))
            character_img = c_img.resize((143, 143))
            black_bg = Image.open(_black_bg).convert('RGBA')
            diff_img = Image.open(_diff_img).convert('RGBA')
            diff_bg = Image.open(_diff_bg).convert('RGBA')
            clear_img = Image.open(_clear_img).convert('RGBA')
            black_line = Image.open(_black_line).convert('RGBA')
            white_line = Image.open(_white_line).convert('RGBA')

            r, g, b = Image.open(_song_img).resize((1, 1)).load()[0, 0]
            im = Image.new('RGBA', (712, 1412), (r, g, b, 255))
            # 黑色透明
            im.alpha_composite(black_bg)
            # info
            im.alpha_composite(info_img, (130, 50))
            # 黑线
            im.alpha_composite(black_line, (156, 97))
            # 搭档
            im.alpha_composite(character_img, (28, 15))
            # ptt
            im.alpha_composite(ptt_img, (407, 30))
            # 难度背景
            im.alpha_composite(diff_bg, (100, 175))
            # 曲绘
            im.alpha_composite(song_img.convert('RGBA').resize((474, 474)), (119, 194))
            # 难度定数
            im.alpha_composite(diff_img, (119, 220))
            # 白线
            im.alpha_composite(white_line, (31, 800))
            # clear
            im.alpha_composite(clear_img, (16, 815))
            # rank
            im.alpha_composite(rank_img, (466, 1160))

            text_im = ImageDraw.Draw(im)
            font = DrawText(text_im, Exo_Regular)
            jpfont = DrawText(text_im, Kazesawa_Regular)
            # 昵称
            font.draw(295, 60, 30, self.arcname, color=(0, 0, 0, 255), anchor='mt')
            # Rating
            font.draw(572, 60, 30, 'RATING', color=(0, 0, 0, 255), anchor='mt')
            # arcid
            font.draw(295, 105, 20, f'ArcID | {self.arcid}', color=(0, 0, 0, 255), anchor='mt')
            # rating
            font.draw(572, 105, 20, f'{self.rating:.3f}', color=(0, 0, 0, 255), anchor='mt')
            # ptt
            font.draw(466, 87, 30, ptt, stroke_width=1, stroke_fill=(0, 0, 0, 255), anchor='mm')
            # 难度
            font.draw(135, 240, 22, f'{diffi.upper()} | {song_rating}', anchor='lm')
            # 曲名
            jpfont.draw_partial_opacity(356, 704, 40, title, anchor='mt')
            # 曲师
            jpfont.draw_partial_opacity(356, 755, 20, artist, anchor='mt')
            # 分数
            font.draw_partial_opacity(356, 925, 80, f'{self.score:,}', anchor='mt')
            # Pure
            font.draw_partial_opacity(74, 1090, 60, 'Pure', anchor='ls')
            # Player Pure
            font.draw_partial_opacity(356, 1090, 60, self.p_count, anchor='ls')
            # Player SP
            font.draw_partial_opacity(510, 1090, 35, f'| +{self.sp_count}', anchor='ls')
            # Far
            font.draw_partial_opacity(74, 1175, 60, 'Far', anchor='ls')
            # Player Far
            font.draw_partial_opacity(356, 1175, 60, self.far_count, anchor='ls')
            # Lost
            font.draw_partial_opacity(74, 1255, 60, 'Lost', anchor='ls')
            # Player Lost
            font.draw_partial_opacity(356, 1255, 60, self.lost_count, anchor='ls')
            # Playtime
            font.draw_partial_opacity(356, 1340, 30, f'PlayTime | {playtime(self.play_time)}', anchor='mm')
            # info
            font.draw_partial_opacity(356, 1400, 20, f'Generated by {bot} | Powered by project Arcaea-AUA', anchor='ms')

        return im

    async def b30_song_data(self, num: int, info: dict, songinfolist: dict) -> None:

        self._songinfo = songinfolist[num]

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

        _song_img = os.path.join(song_dir, self.songid, 'base.jpg' if self.difficulty != 3 else '3.jpg')
        _diff_img = os.path.join(diff_dir, f'{diff(self.difficulty).upper()}.png')

        self.song_img = (await self.async_img(_song_img, 'songs', self.songid, self.difficulty)).resize((190, 190))
        self.diff_img = Image.open(_diff_img).convert('RGBA')

    async def best30(self) -> Image.Image:
        """
        Draw Player Best30
        """
        _bg_img = os.path.join(img, 'b30.png')
        _ptt_img = os.path.join(ptt_dir, pttbg(self.ptt))
        character_name = f'{self.character}u_icon.png' if self.is_char_uncapped ^ self.is_char_uncapped_override else f'{self.character}_icon.png'
        _character_img = os.path.join(char_dir, character_name)
        _new_img = os.path.join(img, 'new.png')

        c_img = await self.async_img(_character_img, 'char', character_name)
        character_img = c_img.resize((255, 255))
        ptt_img = Image.open(_ptt_img).convert('RGBA').resize((159, 159))
        self.new_img = Image.open(_new_img).convert('RGBA')

        self.text_color = [(51, 122, 139, 255), (116, 146, 80, 255), (135, 70, 116, 255), (142, 28, 55, 255)]
        # 底图
        self.im = Image.open(_bg_img).convert('RGBA')
        # 字体
        text_im = ImageDraw.Draw(self.im)
        self.exo_r = DrawText(text_im, Exo_Regular)
        self.exo_b = DrawText(text_im, Exo_Semibold)
        self.Kazesawa_r = DrawText(text_im, Kazesawa_Regular)
        self.Kazesawa_b = DrawText(text_im, Kazesawa_Semibold)
        # 搭档
        self.im.alpha_composite(character_img, (680, 186))
        # ptt
        self.im.alpha_composite(ptt_img, (800, 320))
        # 玩家信息
        ptt = f'{self.ptt / 100:.2f}' if self.ptt != -1 else '--'
        if '.' in ptt:
            ptt = ptt.split('.')
            self.exo_r.draw(872, 412, 46, ptt[0], anchor='rs', stroke_width=1, stroke_fill=(0, 0, 0, 255))
            self.exo_r.draw(872, 412, 34, f'.{ptt[1]}', anchor='ls', stroke_width=1, stroke_fill=(0, 0, 0, 255))
        else:
            self.exo_r.draw(878, 395, 45, ptt, anchor='mm', stroke_width=1, stroke_fill=(0, 0, 0, 255))
        self.exo_r.draw(440, 275, 44, self.arcname, color=(0, 0, 0, 255), anchor='mm')
        self.exo_r.draw(440, 340, 40, self.core, color=(0, 0, 0, 255), anchor='mm')
        self.exo_r.draw(1090, 250, 42, f'{self.r10:.4f}', color=(0, 0, 0, 255), anchor='mm')
        self.exo_r.draw(1350, 315, 36, f'{self.maxptt:.4f}', color=(0, 0, 0, 255), anchor='mm')
        self.exo_r.draw(1090, 380, 42, f'{self.b30:.4f}', color=(0, 0, 0, 255), anchor='mm')
        # best 30
        self.bg_y = 540
        for num, data in enumerate(self.scorelist):
            await self.draw_b30(num, data, self.songinfolist)
        # best 40
        self.bg_y = 2880
        for num, data in enumerate(self.overflowlist):
            await self.draw_b30(num, data, self.overflowinfolist)
        
        self.exo_b.draw_partial_opacity(800, 3580, 26, f'Draw Time {playtime(time() * 1000)}  |  Credit to YuzuChaN  |  Generated by {bot}  |  Powered by project Arcaea-AUA', anchor='ms')

        return self.im

    async def draw_b30(self, num: int, data: dict, songinfolist: dict):
        if num % 3 == 0:
            self.bg_y += 230 if num != 0 else 0
            self.bg_x = 20
        else:
            self.bg_x += 530
        
        await self.b30_song_data(num, data, songinfolist)
        # 难度
        self.im.alpha_composite(self.diff_img, (self.bg_x, self.bg_y))
        # 曲绘
        self.im.alpha_composite(self.song_img, (self.bg_x + 5, self.bg_y + 5))
        # songrating
        songrating = f'{self.song_rating:.1f}'.split('.')
        srbox = self.exo_b.get_box(songrating[0], 34)
        self.exo_b.draw(self.bg_x + 205, self.bg_y + 22, 34, songrating[0], anchor='lm')
        self.exo_b.draw(self.bg_x + 205 + srbox[2], self.bg_y + 25, 26, f'.{songrating[1]}', anchor='lm')
        # ->
        self.Kazesawa_r.draw(self.bg_x + 275, self.bg_y + 22, 34, '→', anchor='lm')
        # playrating
        playrating = f'{self.rating:.3f}'.split('.')
        prbox = self.exo_b.get_box(playrating[0], 34)
        self.exo_b.draw(self.bg_x + 320, self.bg_y + 22, 34, playrating[0], anchor='lm')
        self.exo_b.draw(self.bg_x + 320 + prbox[2], self.bg_y + 25, 26, f'.{playrating[1]}', anchor='lm')
        # 排名
        self.exo_b.draw(self.bg_x + 490, self.bg_y + 22, 30, f'#{num + 1}', anchor='rm')
        # 曲名
        if len(self.title) > 20:
            title = f'{self.title[:17]}...'
        else:
            title = self.title
        self.Kazesawa_b.draw(self.bg_x + 205, self.bg_y + 55, 25, title, self.text_color[self.difficulty], 'lm')
        # 分数
        self.exo_b.draw(self.bg_x + 205, self.bg_y + 100, 40, f'{self.score:,}', self.text_color[self.difficulty], 'lm')
        # P
        self.exo_r.draw(self.bg_x + 205, self.bg_y + 155, 30, 'P', (0, 174, 255, 255), 'ls')
        pcbox = self.exo_r.get_box(str(self.p_count), 22)
        self.exo_r.draw(self.bg_x + 230, self.bg_y + 155, 22, self.p_count, (0, 174, 255, 255), 'ls')
        self.exo_r.draw(self.bg_x + 235 + pcbox[2], self.bg_y + 155, 18, f'+{self.sp_count}', (0, 174, 255, 255), 'ls')
        # F
        self.exo_r.draw(self.bg_x + 340, self.bg_y + 155, 30, 'F', (255, 162, 0, 255), 'ls')
        self.exo_r.draw(self.bg_x + 365, self.bg_y + 155, 22, self.far_count, (255, 162, 0, 255), 'ls')
        # L
        self.exo_r.draw(self.bg_x + 420, self.bg_y + 155, 30, 'L', (163, 0, 0, 255), 'ls')
        self.exo_r.draw(self.bg_x + 445, self.bg_y + 155, 22, self.lost_count, (163, 0, 0, 255), 'ls')
        # 时间
        self.exo_b.draw(self.bg_x + 205, self.bg_y + 180, 22, playtime(self.play_time), self.text_color[self.difficulty], 'lm')
        # 新成绩
        if timediff(self.play_time) <= 7:
            self.im.alpha_composite(self.new_img, (self.bg_x, self.bg_y))

    async def async_img(self, img: str, project: str, data: str, diff: int = None) -> Image.Image:
        if not os.path.isfile(img):
            if diff:
                name = 'base.jpg' if diff != 3 else '3.jpg'
                new_img = await download_img(project, data, name)
            else:
                new_img = await download_img(project, data)
            if new_img:
                return Image.open(img).convert('RGBA')
        else:
            return Image.open(img).convert('RGBA')

    @property
    def songbg(self) -> str:
        return self._song_img

async def draw_info(arcid: Union[int, str]) -> str:
    try:
        userdict = {
            'user' : str(arcid),
            'overflow': 9,
            'withsonginfo' : 'true'
        }

        logger.info(f'Starting BotArcAPI -> {playtime(time() * 1000)}')
        info = await botarcapi('best30', userdict)
        logger.info(f'Ending BotArcAPI and Starting Draw Piture -> {playtime(time() * 1000)}')
        if isinstance(info, dict):
            
            data = Data('best30', info['content'])
            im = await data.best30()
            logger.info(f'Ending Draw Piture -> {playtime(time() * 1000)}')
            base64str = img2b64(im)
            msg = MessageSegment.image(base64str)
        else:
            msg = info
    except ArcError as e:
        logger.error(f'Error: {e.error_str}')
        msg = e.error_str
    except aiohttp.ContentTypeError:
        logger.error(traceback.format_exc())
        msg = f'AUA请求超时，请稍后再试'
    except Exception as e:
        logger.error(traceback.format_exc())
        msg = f'Error：{type(e)}，请联系Bot管理员'
    return msg

async def draw_score(project: str, arcid: int, mode: int = 0, name: str = None, diff: int = None) -> Union[MessageSegment, str]:
    try:
        logger.info(f'Starting BotArcAPI -> {playtime(time() * 1000)}')
        if project == 'recent':
            userdict = {
                'user' : str(arcid),
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
                return f'找到{len(userinfo["content"]["songs"])}个相似曲目：\n----------\n{list2newline(userinfo["content"]["songs"])}'
            elif userinfo['status'] == -7:
                return f'未找到曲目 -> {name}'
            elif userinfo['status'] == 0:
                data = Data('best', userinfo['content'])

        if mode == 0:
            randint = random.randint(1, 50) % 2 + 1
        else:
            randint = mode

        logger.info(f'Ending BotArcAPI and Starting Draw Piture -> {playtime(time() * 1000)}')
        im = await data.recent(randint)

        logger.info(f'Ending Draw Piture -> {playtime(time() * 1000)}')
        base64str = img2b64(im)
        msg = MessageSegment.image(base64str)
    except ArcError as e:
        logger.error(e.error_str)
        msg = f'Error：{e.error_str}'
    except aiohttp.ContentTypeError:
        logger.error(traceback.format_exc())
        msg = f'AUA请求超时，请稍后再尝试'
    except Exception as e:
        logger.error(traceback.format_exc())
        msg = f'Error：{type(e)}，请联系Bot管理员'
    return msg

async def draw_chart(name: str, diff: int):
    try:
        data = await botarcapi('chart', {'songname': name, 'difficulty': diff})
        im = Image.open(BytesIO(data))
        base64str = img2b64(im)
        msg = MessageSegment.image(base64str)
    except ArcError as e:
        msg = f'Error：{e.error_str}'
    except Exception as e:
        logger.error(traceback.format_exc())
        msg = f'Error：{type(e)}，请联系Bot管理员'
    return msg

def random_music(rating: int, plus: bool, diff: int) -> str:

    song = asql.get_random_song(rating, plus, diff)

    if rating % 10 != 0 and diff:
        for i in song:
            if i[diff + 4] != rating:
                song.remove(i)

    if not song:
        return '未找到符合的曲目'

    random_list_int = random.randint(0, len(song) - 1)
    songinfo = asql.get_song(song[random_list_int][0])

    songrating = [str(i[16] / 10) for i in songinfo]
    diffc = [diffdict[str(_)][0].upper() for _ in range(len(songrating))]

    songs = {
        'song_id': song[random_list_int][0],
        'difficulty': diff
    }

    data = Data('random', songs)
    img = MessageSegment.image(file=f'file:///{data.songbg}')

    msg = f'''{img}
Song: {songinfo[0][3] if songinfo[0][3] else songinfo[0][2]}
Artist: {songinfo[0][4]}
Difficulty: {' | '.join(diffc)}
Rating: {' | '.join(songrating)}'''

    return msg

async def bindinfo(qqid: int, arcid: Union[int, str]) -> Tuple[str, str]:
    info = await botarcapi('recent', {'user': arcid})
    name = info['content']['account_info']['name']
    code = info['content']['account_info']['code']
    user = asql.select_user(code)
    if user:
        raise ArcError('-500')
    asql.bind_user(qqid, code)
    return (name, code)