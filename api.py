import aiohttp, os
from typing import Union
from hoshino.log import new_logger

from .baa_error import ArcError
from .sql import asql

imgapi = 'http://106.53.138.218:6321/api/'
char_api = 'arcaea/char/'

BAAPI = ''
TOKEN = ''
ENDPOINT = {
    'recent' : 'user/info',
    'best' : 'user/best',
    'best30' : 'user/best30'
}

dir = os.path.join(os.path.dirname(__file__), 'img')
logger = new_logger('Arcaea')

async def botarcapi(project: str, params: dict) -> dict:

    headers = {'User-Agent': TOKEN}

    async with aiohttp.request('GET', f'{BAAPI}/{ENDPOINT[project]}', params=params, headers=headers) as req:
        data = await req.json()
        if data['status'] != 0 and data['status'] != -8 and data['status'] != -7:
            raise ArcError(str(data['status']))
        else:
            return data

async def download_img(project: str, data: str, name: int = None):
    if project == 'songs':
        async with aiohttp.ClientSession() as session:
            async with session.get(f'{imgapi}arcaea?songid={data}') as req:
                new_data = await req.json()
        
        songid = new_data['songid']
        artist = new_data['artist']
        name_en = new_data['name_en']
        name_jp = new_data['name_jp']
        if name == 'base.jpg':
            url = new_data['base_url']
        else:
            url = new_data['byd_url'] if 'byd_url' in new_data else ''
        result = asql.song_info(songid, 'ftr')
        if not result:
            asql.add_song(songid, name_en, name_jp, artist)

        new_dir = os.path.join(dir, 'songs', data)
        if not os.path.isdir(new_dir):
            os.makedirs(new_dir)
        dirname = os.path.join(new_dir, name)
    elif project == 'char':
        url = imgapi + char_api + data
        dirname = os.path.join(dir, 'char', data)
    if os.path.isfile(dirname):
        return False
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as req:
                data = await req.read()
                open(dirname, 'wb').write(data)
                logger.info(f'文件：{dirname} 下载完成')
                return True
    except Exception as e:
        logger.info(f'文件：{dirname} 下载失败')
        return f'Error {type(e)}'