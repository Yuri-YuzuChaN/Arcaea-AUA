import aiohttp, os, aiofiles
from typing import Union

from .aua_error import ArcError
from . import *

imgapi = 'http://106.53.138.218:6321/api/'
char_api = 'arcaea/char/'

AUAPI = ''
TOKEN = ''
ENDPOINT = {
    'recent' : 'user/info',
    'best' : 'user/best',
    'best30' : 'user/best30'
}

dir = os.path.join(os.path.dirname(__file__), 'img')

async def download_img(project: str, data: str, name: int = None) -> Union[bool, str]:
    if project == 'songs':
        async with aiohttp.request('GET', f'{imgapi}arcaea?songid={data}') as req:
            new_data = await req.json()
        
        if name == 'base.jpg':
            url = new_data['base_url']
        else:
            url = new_data['byd_url'] if 'byd_url' in new_data else ''

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
        async with aiohttp.request('GET', url) as req:
            data = await req.read()
            async with aiofiles.open(dirname, 'wb') as f:
                await f.write(data)
            logger.info(f'文件：{dirname} 下载完成')
            return True
    except Exception as e:
        logger.info(f'文件：{dirname} 下载失败')
        return f'Error {type(e)}'

async def botarcapi(project: str, params: dict) -> dict:

    headers = {'Authorization': f'Bearer {TOKEN}'}
    timeout = aiohttp.ClientTimeout(total=180)
    async with aiohttp.request('GET', f'{AUAPI}/{ENDPOINT[project]}', params=params, headers=headers, timeout=timeout) as req:
        data = await req.json()
        if data['status'] != 0 and data['status'] != -8 and data['status'] != -7:
            raise ArcError(str(data['status']))
        else:
            return data