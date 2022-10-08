import sqlite3, os, traceback
from typing import Union, List, Dict, Tuple

from . import *

class ARCSQL:

    def __init__(self):
        os.makedirs(os.path.dirname(USERSQL), exist_ok=True)
        self.__MakeSQL__()
    
    def connect_user(self):
        return sqlite3.connect(USERSQL)

    def connect_song(self) -> sqlite3.Connection:
        return sqlite3.connect(SONGSQL)

    def __MakeSQL__(self):
        try:
            self.connect_user().execute('''CREATE TABLE USER(
                ID          INTEGER     PRIMARY KEY     NOT NULL,
                QQID        INTEGER     NOT NULL,
                ARCID       INTEGER     NOT NULL
            )''')
        except sqlite3.OperationalError:
            pass
        except Exception:
            logger.error(traceback.format_exc())
    
    # 获取好友码和user_id
    def get_user(self, qqid: int) -> Union[tuple, bool]:
        '''
        使用QQ号 `qqid` 获取好友码 `arcid`
        '''
        try:
            result = self.connect_user().execute(f'SELECT ARCID, MODE FROM USER WHERE QQID = {qqid}').fetchall()
            if not result:
                return False
            else:
                return result[0]
        except Exception as e:
            logger.error(e)
            return False

    def update_mode(self, qqid: int, mode: int) -> bool:
        try:
            conn = self.connect_user()
            conn.execute(f'UPDATE USER SET MODE = {mode} WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 绑定账号
    def bind_user(self, qqid: int, arcid: str) -> bool:
        try:
            conn = self.connect_user()
            conn.execute(f'INSERT INTO USER VALUES (NULL, {qqid}, {arcid}, 0)')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 删除账号
    def delete_user(self, qqid: int) -> bool:
        try:
            conn = self.connect_user()
            conn.execute(f'DELETE FROM USER WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 获取曲目
    def get_song(self, songid: str) -> list:
        song = self.connect_song().execute(f'SELECT * FROM CHARTS WHERE SONG_ID = "{songid}"').fetchall()
        return song

    def add_alias(self, songid: str, alias: str) -> bool:
        conn = self.connect_song()
        conn.execute(f'INSERT INTO ALIAS VALUES ("{songid}", "{alias}")')
        conn.commit()
        return True

    # 查询别名
    def get_alias(self, name: str, songname: bool = False, onlyalias: bool = False) -> Union[list, Tuple[List[Dict[str, Union[str, List[str]]]], bool]]:

        sqllist = [
            f'SELECT * FROM CHARTS WHERE SONG_ID = "{name}"',
            f'SELECT * FROM CHARTS WHERE NAME_EN = "{name}" OR NAME_JP = "{name}"',
            f'SELECT * FROM ALIAS WHERE ALIAS = "{name}"',
            f'SELECT * FROM ALIAS WHERE ALIAS LIKE "%{name}%"',
            f'SELECT * FROM CHARTS WHERE SONG_ID LIKE "%{name}%" OR NAME_EN LIKE "%{name}%" OR NAME_JP LIKE "%{name}%"'
        ]

        if onlyalias:
            data = self.connect_song().execute(sqllist[2]).fetchall()
            if not data:
                data = self.connect_song().execute(sqllist[3]).fetchall()
            return list(set([i[0] for i in data]))
        
        for sql in sqllist:
            data = self.connect_song().execute(sql).fetchall()
            setdata = set([i[0] for i in data])
            if data and len(setdata) == 1:
                songlist = [data[0][0]]
                if songname:
                    result = self.connect_song().execute(
                                f'SELECT * FROM ALIAS WHERE SID = "{data[0][0]}"').fetchall()
                    songlist = [i[1] for i in result].append(result[0][0])
                return songlist
            elif len(setdata) > 1:
                songlist = list(setdata)
                if songname:
                    sl = []
                    for i in songlist:
                        result = self.connect_song().execute(
                                f'SELECT * FROM ALIAS WHERE SID = "{i}"').fetchall()
                        sl.append({'songid' : i, 'alias': [i[1] for i in result]})
                    songlist = sl, False
                return songlist
        return []

    # 获取随机曲目
    def get_random_song(self, rating: float, plus: bool = False, diff: int = None) -> Union[bool, List[tuple]]:
        try:
            if diff:
                if plus:
                    rmin, rmax = rating + 7, rating + 10
                    sql = f'SELECT * FROM CHARTS WHERE RATING_CLASS = {diff} AND RATING >= {rmin} AND RATING < {rmax}'
                else:
                    sql = f'SELECT * FROM CHARTS WHERE RATING_CLASS = {diff} AND RATING = {rating} AND RATING < {rating + 7}'
            elif plus:
                rmin, rmax = rating + 7, rating + 10
                sql = f'SELECT * FROM CHARTS WHERE RATING >= {rmin} AND RATING < {rmax}'
            elif rating >= 90:
                if rating % 10 != 0:
                    sql = f'SELECT * FROM CHARTS WHERE RATING = {rating}'
                else:
                    rmin, rmax = rating, rating + 7
                    sql = f'SELECT * FROM CHARTS WHERE RATING >= {rmin} AND RATING < {rmax}'
            else:
                rmin, rmax = rating, rating + 10
                sql = f'SELECT * FROM CHARTS WHERE RATING >= {rmin} AND RATING < {rmax}'
            
            result = self.connect_song().execute(sql).fetchall()
            if not result:
                return [False]
            else:
                return result
        except Exception as e:
            return False

    def get_all_music_info(self):
        result = self.connect_song().execute('SELECT * FROM CHARTS').fetchall()
        return result

asql = ARCSQL()