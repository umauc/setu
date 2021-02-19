import asyncio
from io import BytesIO

import aiohttp
import imagehash
import regex
import pdb
from PIL import Image as Images
from PIL import ImageFile
from bs4 import BeautifulSoup
from tinydb import TinyDB, where

ImageFile.LOAD_TRUNCATED_IMAGES = True
from random import choice
from setu_config import apikey, refresh_token
from pixivpy3 import ByPassSniApi

api = ByPassSniApi()

def init():
    api.require_appapi_hosts(hostname="public-api.secure.pixiv.net")
    api.set_accept_language('en-us')
    api.auth(refresh_token=refresh_token)

init()

def get_pixiv_info(pid):
    try:
        result = api.illust_detail(pid)
    except:
        init()
        result = api.illust_detail(pid)
    return result


class PicNotFoundError(Exception):
    pass


class userData(object):
    def __init__(self):
        self.db = TinyDB('data.json').table('user')

    def user_check(self, qid):
        if not bool(self.db.search(where('qid') == qid)):
            self.user_init(qid)

    def user_init(self, qid):
        self.db.insert({'qid': qid, 'permission': 0, 'use_times': 0, 'upload_times': 0})

    def get_permission(self, qid):
        self.user_check(qid)
        return self.db.search(where('qid') == qid)[0].get('permission')

    def set_permission(self, qid, permission):
        self.user_check(qid)
        self.db.update({'permission': permission}, where('qid') == qid)

    def get_limit(self, qid):
        self.user_check(qid)
        limit_dict = {'0': 3, '1': 10, '2': 25, '3': 40, '4': 10000, '5': 10000}
        return limit_dict.get(str(self.db.search(where('qid') == qid)[0].get('permission')))

    def get_use_time(self, qid):
        self.user_check(qid)
        return self.db.search(where('qid') == qid)[0].get('use_times')

    def set_use_time(self, qid):
        """
        每次+1
        """
        self.user_check(qid)
        self.db.update({'use_times': self.get_use_time(qid) + 1}, where('qid') == qid)
        self.refresh_premission(qid)

    def clear_use_time(self):
        for i in self.db.all():
            self.db.update({'use_times': 0}, where('qid') == i.get('qid'))

    def get_revoke_time(self, qid):
        self.user_check(qid)
        revoke_time_dict = {'0': 30, '1': 30, '2': 60, '3': 60, '4': 260, '5': 260}
        return revoke_time_dict.get(str(self.db.search(where('qid') == qid)[0].get('permission')))

    def get_upload_time(self, qid):
        self.user_check(qid)
        return self.db.search(where('qid') == qid)[0].get('upload_times')

    def set_upload_time(self, qid):
        """
        每次+1
        """
        self.user_check(qid)
        self.db.update({'upload_times': self.get_upload_time(qid) + 1}, where('qid') == qid)

    def refresh_premission(self, qid):
        permission = self.get_permission(qid)
        local_upload_time = self.get_upload_time(qid)
        if permission > 4:
            pass
        else:
            if local_upload_time < 50:
                self.set_permission(qid, 0)
            elif local_upload_time >= 50 and local_upload_time < 100:
                self.set_permission(qid, 1)
            elif local_upload_time >= 100 and local_upload_time < 175:
                self.set_permission(qid, 2)
            elif local_upload_time >= 175 and local_upload_time < 250:
                self.set_permission(qid, 3)
            elif local_upload_time >= 250:
                self.set_permission(qid, 4)


def get_info(pid):
    """
    返回字典
    {'pid':xxx,'r18': False,'title':xxx,'url':xxx,'small_url':xxx}
    """
    try:
        pic_info = get_pixiv_info(int(pid))
        pic_title = pic_info['illust']['title']
        if str(pic_info['illust']['tags']).find('R-18') != -1:
            pic_r18 = True
        else:
            pic_r18 = False
        pic_url = pic_info['illust']['meta_single_page']['original_image_url'].replace('i.pximg.net', 'pixivdl.sfcloud.workers.dev')
        pic_large_url = pic_info['illust']['image_urls']['large'].replace('i.pximg.net', 'pixivdl.sfcloud.workers.dev')
        return {'pid': pid, 'r18': pic_r18, 'title': pic_title, 'url': pic_url, 'small_url': pic_large_url}
    except:
        raise PicNotFoundError

class setu(object):
    def __init__(self):
        self.db = TinyDB('data.json').table('setu')

    async def get_local(self, loop, r18=False):
        """
        获取本地图片，返回字典
        {'pid':xxx,'r18': False,'title':xxx,'url':xxx,'small_url':xxx}
        """
        if not r18:
            pid = choice(self.db.search(where('type') == 'all-age')).get('pid')
        else:
            pid = choice(self.db.search(where('type') == 'r18')).get('pid')
        return get_info(pid)

    async def get_remote(self, keyword='', r18=False):
        """
        获取来自lolicon.app的图片，返回字典
        {'pid':xxx,'r18': False,'title':xxx,'url':xxx,'small_url':xxx}
        """
        session = aiohttp.ClientSession()
        if not r18:
            async with session.get(f'https://api.lolicon.app/setu/?apikey={apikey}&keyword={keyword}') as resp:
                pic_info = await resp.json()
            await session.close()
        else:
            async with session.get(f'https://api.lolicon.app/setu/?apikey={apikey}&keyword={keyword}&r18=1') as resp:
                pic_info = await resp.json()
            await session.close()
        if pic_info.get('code') == 0:
            title = pic_info.get('data')[0].get('title')
            if pic_info.get('data')[0].get('r18') == 'false':
                r18 = False
            else:
                r18 = True
            pid = pic_info.get('data')[0].get('pid')
            url = pic_info.get('data')[0].get('url')
            # small_url = setu_info.get('small_url')
            setu_dict = {'pid': pid, 'r18': r18, 'title': title, 'url': url}
            return setu_dict
        else:
            raise PicNotFoundError

    def local_upload(self, pid, r18=False):
        if not bool(self.db.search(where('pid') == pid)):
            if r18:
                self.db.insert({'type': 'r18', 'pid': pid})
            else:
                self.db.insert({'type': 'all-age', 'pid': pid})

    def local_upload_del(self, pid):
        self.db.remove(where('pid') == pid)

    def local_upload_count_all(self):
        return len(self.db.all())


async def pic_get(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post('https://ascii2d.net/search/uri', data={'uri': url}) as resp:
                data = await resp.text()
        soup = BeautifulSoup(data, features="html.parser")
        url_list = []
        for link in soup.find_all(target="_blank", rel="noopener"):
            if link.get('href').find('pixiv') != -1:
                url_list.append(link.get('href'))
        if url_list == []:
            return 114514
        else:
            return int(regex.compile(r'(^https://www.pixiv.net/artworks/(\d*)$)', regex.I).match(url_list[0])[2])
    except:
        return 114514


async def image_match(url1, url2):
    try:
        highfreq_factor = 1
        hash_size = 8
        async with aiohttp.ClientSession() as session:
            async with session.get(url1) as resp:
                r1 = await resp.content.read()
        async with aiohttp.ClientSession() as session:
            async with session.get(url1) as resp:
                r2 = await resp.content.read()
        hash1 = imagehash.phash(Images.open(
            BytesIO(r1)), hash_size=hash_size, highfreq_factor=highfreq_factor)
        hash2 = imagehash.phash(Images.open(
            BytesIO(r2)), hash_size=hash_size, highfreq_factor=highfreq_factor)
        return 1 - (hash1 - hash2) / len(hash1.hash) ** 2
    except:
        return 0.0
