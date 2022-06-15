import sqlite3, os, traceback
from typing import Union, List

from hoshino.log import new_logger

SQL = os.path.expanduser('~/.hoshino/arcaea.db')
SONGSQL = os.path.join(os.path.dirname(__file__), 'arcsong.db')
logger = new_logger('Arcaea_SQL')

class ARCSQL:

    def __init__(self):
        os.makedirs(os.path.dirname(SQL), exist_ok=True)
        self.makesql()
    
    def arc_conn(self):
        return sqlite3.connect(SQL)

    def song_conn(self):
        return sqlite3.connect(SONGSQL)

    def makesql(self):
        try:
            self.arc_conn().execute('''CREATE TABLE USER(
                ID          INTEGER     PRIMARY KEY     NOT NULL,
                QQID        INTEGER     NOT NULL,
                ARCID       INTEGER     NOT NULL,
                MODE        INTEGER     NOT NULL
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
            result = self.arc_conn().execute(f'SELECT ARCID, MODE FROM USER WHERE QQID = {qqid}').fetchall()
            if not result:
                return False
            else:
                return result[0]
        except Exception as e:
            logger.error(e)
            return False

    def update_mode(self, qqid: int, mode: int) -> bool:
        try:
            conn = self.arc_conn()
            conn.execute(f'UPDATE USER SET MODE = {mode} WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 绑定账号
    def bind_user(self, qqid: int, arcid: str) -> bool:
        try:
            conn = self.arc_conn()
            conn.execute(f'INSERT INTO USER VALUES (NULL, {qqid}, {arcid}, 0)')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 删除账号
    def delete_user(self, qqid: int) -> bool:
        try:
            conn = self.arc_conn()
            conn.execute(f'DELETE FROM USER WHERE QQID = {qqid}')
            conn.commit()
            return True
        except Exception as e:
            logger.error(e)
            return False

    # 查询歌曲
    def song_info(self, songid: str, diff: str) -> Union[bool, tuple]:
        try:
            result = self.song_conn().execute(f'SELECT NAME_EN, NAME_JP, ARTIST, {diff} FROM SONG WHERE SONGID = "{songid}"').fetchall()
            if not result:
                return False
            else:
                return result[0]
        except Exception as e:
            logger.error(e)
            return False

    def add_song(self, songid: str, name_en: str, name_jp: str, artist: str) -> bool:
        try:
            conn = self.song_conn()
            conn.execute(f'INSERT INTO SONG VALUES ("{songid}", "{name_en}", "{name_jp}", "{artist}", -1, -1, -1, -1)')
            conn.commit()
            return True
        except:
            return False

    def add_song_rating(self, songid: str, diff: str, rating: int) -> bool:
        try:
            conn = self.song_conn()
            conn.execute(f'UPDATE SONG SET {diff} = {rating} WHERE SONGID = "{songid}"')
            conn.commit()
            return True
        except:
            return False

    def get_song(self, rating: float, plus: bool = False, diff: str = None) -> Union[bool, List[tuple]]:
        try:
            if diff:
                if plus:
                    sql = f'SELECT * FROM SONG WHERE {diff} >= {rating + 7} AND {diff} < {rating + 10}'
                else:
                    sql = f'SELECT * FROM SONG WHERE {diff} >= {rating} AND {diff} < {rating + 7}'
            elif plus:
                rmin, rmax = rating + 7, rating + 10
                sql = f'SELECT * FROM SONG WHERE (PST >= {rmin} AND PST < {rmax}) or (PRS >= {rmin} AND PRS < {rmax}) or (FTR >= {rmin} AND FTR < {rmax}) or (BYD >= {rmin} AND BYD < {rmax})'
            elif rating >= 90:
                if rating % 10 != 0:
                    sql = f'SELECT * FROM SONG WHERE PST = {rating} or PRS = {rating} or FTR = {rating} or BYD = {rating}'
                else:
                    rmin, rmax = rating, rating + 7
                    sql = f'SELECT * FROM SONG WHERE (PST >= {rmin} AND PST < {rmax}) or (PRS >= {rmin} AND PRS < {rmax}) or (FTR >= {rmin} AND FTR < {rmax}) or (BYD >= {rmin} AND BYD < {rmax})'
            else:
                rmin, rmax = rating, rating + 10
                sql = f'SELECT * FROM SONG WHERE (PST >= {rmin} AND PST < {rmax}) or (PRS >= {rmin} AND PRS < {rmax}) or (FTR >= {rmin} AND FTR < {rmax}) or (BYD >= {rmin} AND BYD < {rmax})'
            
            result = self.song_conn().execute(sql).fetchall()
            if not result:
                return False
            else:
                return result
        except Exception as e:
            logger.error(e)
            return False

asql = ARCSQL()