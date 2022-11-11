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
            self.connect_user().execute("""CREATE TABLE USER(
                ID          INTEGER     PRIMARY KEY     NOT NULL,
                QQID        INTEGER     NOT NULL,
                ARCID       INTEGER     NOT NULL
            )""")
        except sqlite3.OperationalError:
            pass
        except Exception:
            logger.error(traceback.format_exc())
    
    # 获取好友码和user_id
    def get_user(self, qqid: int) -> Union[tuple, bool]:
        """
        使用QQ号 `qqid` 获取好友码 `arcid`
        """
        try:
            result = self.connect_user().execute(f'SELECT ARCID, MODE FROM USER WHERE QQID = {qqid}').fetchall()
            if not result:
                return False
            else:
                return result[0]
        except Exception as e:
            logger.error(e)
            return False

    def select_user(self, code: int) -> bool:
        """
        查询好友码是否绑定过
        """
        try:
            result = self.connect_user().execute(f'SELECT * FROM USER WHERE ARCID = {code}').fetchall()
            if not result:
                return False
            else:
                return True
        except Exception as e:
            logger.error(e)
            return False

    def update_mode(self, qqid: int, mode: int) -> bool:
        """
        更改查询绘图
        """
        try:
            conn = self.connect_user()
            conn.execute(f'UPDATE USER SET MODE = {mode} WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def bind_user(self, qqid: int, code: str) -> bool:
        """
        绑定账号
        """
        try:
            conn = self.connect_user()
            conn.execute(f'INSERT INTO USER VALUES (NULL, {qqid}, {code}, 0)')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def delete_user(self, qqid: int) -> bool:
        """
        删除账号
        """
        try:
            conn = self.connect_user()
            conn.execute(f'DELETE FROM USER WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    def get_song(self, songid: str) -> list:
        """
        获取曲目
        """
        song = self.connect_song().execute(f'SELECT * FROM CHARTS WHERE SONG_ID = "{songid}"').fetchall()
        return song

    def add_alias(self, songid: str, alias: str) -> bool:
        """
        添加别名
        """
        conn = self.connect_song()
        conn.execute(f'INSERT INTO ALIAS VALUES ("{songid}", "{alias}")')
        conn.commit()
        return True

    def alias(self, name: str) -> list:
        """
        通过别名获取 `sid`
        """
        data = self.connect_song().execute(f'SELECT SID FROM ALIAS WHERE ALIAS = "{name}"').fetchall()
        return data

    def alias_sid(self, name: str) -> list:
        """
        通过 `sid` 获取别名
        """
        data = self.connect_song().execute(f'SELECT ALIAS FROM ALIAS WHERE SID = "{name}"').fetchall()
        return data

    def alias_for_list(self, alist: List[str]) -> List[List[str]]:
        """
        处理多个别名结果的数据库查询
        """
        temp_list = []
        for name in alist:
            data = self.connect_song().execute(f'SELECT ALIAS FROM ALIAS WHERE SID = "{name}"').fetchall()
            temp_list.append([i[0] for i in data])
        return temp_list

    def get_random_song(self, rating: float, plus: bool = False, diff: int = None) -> Union[bool, List[tuple]]:
        """
        随机获取曲目
        """
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