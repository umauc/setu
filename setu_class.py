import requests
import imagehash
import aiohttp
from PIL import Image as Images
from PIL import ImageFile
import json
import random
import os
from bs4 import BeautifulSoup
from pixivpy3 import *
from setu_config import *
from io import BytesIO
import regex
ImageFile.LOAD_TRUNCATED_IMAGES = True
from tenacity import retry, stop_after_delay

api = ByPassSniApi()
api.require_appapi_hosts()
api.set_accept_language('en-us')
api.login(pixiv_account, pixiv_password)

class setu_get(object):
    def __init__(self):
        print('初始化')
        self.setu_url = f'https://api.lolicon.app/setu/?apikey={setu_key}&size1200=true&keyword='
        self.setu_url_r18 = f'https://api.lolicon.app/setu/?apikey={setu_key}&size1200=true&r18=1&keyword='

    @retry()
    def local(self, r18=False):
        self.data = json.load(open('data.json', 'r'))
        pid_len = int(len(self.data.get('data').get('pid')))
        r18_pid_len = int(len(self.data.get('data').get('r18_pid')))
        if r18 == False:
            self.pid = random.choice(self.data.get('data').get('pid'))
        else:
            self.pid = random.choice(self.data.get('data').get('r18_pid'))
        info = pic_get_info(self.pid)
        if info == 404:
            config = config()
            config.upload_delete(self.pid)
            raise TypeError
        else:
            return info

    def web(self, keyword='', r18=False):
        print('获取数据')
        if r18 == False:
            self.setu_data = requests.get(self.setu_url + keyword)
        else:
            self.setu_data = requests.get(self.setu_url_r18 + keyword)
        if str(self.setu_data.json()['code']) == '404':
            return 404
        else:
            self.data = self.setu_data.json()['data'][0]
            self.pid = self.data.get('pid')
            self.url = self.data.get('url')
            self.title = self.data.get('title')
            return {'pid': self.pid, 'title': self.title, 'url': self.url}


def pic_get_info(pid):
    try:
        pic_data = api.illust_detail(pid)
        title = pic_data.get('illust').get('title')
        url = pic_data.get('illust').get('image_urls').get('large').replace('pximg.net', 'pixiv.cat')
        large_url = pic_data.get('illust').get('meta_pages')[0].get('original')
        if pic_data.get('illust').get('tags')[0].get('name') == 'R-18':
            r18 = True
        else:
            r18 = False
        return {'pid': pid, 'title': title, 'url': url, 'r18': r18, 'large_url': large_url}
    except:
        try:
            pic_data = requests.get(
                f'https://api.imjad.cn/pixiv/v1/?type=illust&id={pid}').json()
            title = pic_data.get('response')[0].get('title')
            url = pic_data.get('response')[0].get('image_urls').get('medium').replace('pximg.net', 'pixiv.cat')
            large_url = pic_data.get('response')[0].get('image_urls').get('large').replace('pximg.net', 'pixiv.cat')
            if pic_data.get('response')[0].get('age_limit') == 'all-age':
                r18 = False
            else:
                r18 = True
            return {'pid': pid, 'title': title, 'url': url, 'r18': r18, 'large_url': large_url}
        except:
            return 404


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
            return 0
        else:
            return int(regex.compile(r'(^https://www.pixiv.net/artworks/(\d*)$)', regex.I).match(url_list[0])[2])
    except:
        pass


async def image_match(url1, url2):
    try:
        highfreq_factor = 1
        hash_size = 8
        async with aiohttp.ClientSession() as session:
            async with session.get(url1) as resp:
                r1 = await resp.read()
        async with aiohttp.ClientSession() as session:
            async with session.get(url1) as resp:
                r2 = await resp.read()
        hash1 = imagehash.phash(Images.open(
            BytesIO(r1)), hash_size=hash_size, highfreq_factor=highfreq_factor)
        hash2 = imagehash.phash(Images.open(
            BytesIO(r2)), hash_size=hash_size, highfreq_factor=highfreq_factor)
        return 1 - (hash1 - hash2)/len(hash1.hash)**2
    except:
        return 0.0


class config(object):
    def __init__(self):
        try:
            self.user_config = json.load(open('data.json', 'r'))
        except:
            print('配置读取错误！请初始化！')
        self.users = self.user_config.get('users')

    def limit(self, user):
        if self.users.get('permission').get(str(user)) == None:
            self.permission = 0
        else:
            self.permission = self.users.get('permission').get(str(user))
        if self.permission == 0:
            return 3
        elif self.permission == 1:
            return 10
        elif self.permission == 2:
            return 25
        elif self.permission == 3:
            return 40
        elif self.permission == 4 or self.permission == 5 or self.permission == 6:
            return 10000

    def revoke(self, user):
        if self.users.get('permission').get(str(user)) == None:
            self.permission = 0
        else:
            self.permission = self.users.get('permission').get(str(user))
        if self.permission == 0:
            return 30
        elif self.permission == 1:
            return 30
        elif self.permission == 2:
            return 60
        elif self.permission == 3:
            return 60
        elif self.permission == 4:
            return 260
        elif self.permission == 5 or self.permission == 6:
            return 260

    def setu_count(self):
        return len(self.user_config.get('data').get('pid'))+len(self.user_config.get('data').get('r18_pid'))

    def count(self, user):
        try:
            self.user_config.get('users').get('count')[str(user)] += 1
        except:
            self.user_config.get('users').get('count')[str(user)] = 1
        json.dump(self.user_config, open('data.json', 'w'))

    def count_zero(self):
        self.user_config.get('users').get('count').clear()
        json.dump(self.user_config, open('data.json', 'w'))

    def count_get(self, user):
        if self.user_config.get('users').get('count').get(str(user)) == None:
            return 3
        else:
            return self.user_config.get('users').get('count').get(str(user))

    def upload_count(self, user, count):
        try:
            self.user_config.get('users').get(
                'upload_count')[str(user)] += count
        except:
            self.user_config.get('users').get(
                'upload_count')[str(user)] = count
        json.dump(self.user_config, open('data.json', 'w'))

    def upload_count_get(self, user):
        try:
            return self.user_config.get('users').get('upload_count')[str(user)]
        except:
            return 0

    def upload(self, data, r18_data=[]):
        data_for = data.copy()
        for i in data_for:
            if self.user_config.get('data').get('pid').count(i) != 0:
                data.remove(i)
        if r18_data == False:
            pass
        else:
            r18_data_for = r18_data.copy()
            for i in r18_data_for:
                if self.user_config.get('data').get('r18_pid').count(i) != 0:
                    r18_data.remove(i)
        self.user_config.get('data').get('pid').extend(data)
        self.user_config.get('data').get('r18_pid').extend(r18_data)
        json.dump(self.user_config, open('data.json', 'w'))

    def upload_delete(self, pid):
        try:
            self.user_config.get('data').get('pid').remove(int(pid))
        except:
            self.user_config.get('data').get('r18_pid').remove(int(pid))
        json.dump(self.user_config, open('data.json', 'w'))

    def permission_set(self, user, permission):
        self.user_config.get('users').get('permission')[str(user)] = permission
        json.dump(self.user_config, open('data.json', 'w'))

    def permission_get(self, user):
        if self.users.get('permission').get(str(user)) == None:
            self.permission = 0
        else:
            self.permission = self.users.get('permission').get(str(user))
        return self.permission

    def permission_refresh(self, user):
        if self.users.get('permission').get(str(user)) == None:
            permission = 0
        else:
            permission = self.users.get('permission').get(str(user))
        if permission > 4:
            pass
        else:
            if self.user_config.get('users').get('upload_count')[str(user)] < 50:
                self.user_config.get('users').get('permission')[str(user)] = 0
            elif self.user_config.get('users').get('upload_count')[str(user)] >= 50 and self.user_config.get('users').get('upload_count')[str(user)] < 100:
                self.user_config.get('users').get('permission')[str(user)] = 1
            elif self.user_config.get('users').get('upload_count')[str(user)] >= 100 and self.user_config.get('users').get('upload_count')[str(user)] < 175:
                self.user_config.get('users').get('permission')[str(user)] = 2
            elif self.user_config.get('users').get('upload_count')[str(user)] >= 175 and self.user_config.get('users').get('upload_count')[str(user)] < 250:
                self.user_config.get('users').get('permission')[str(user)] = 3
            elif self.user_config.get('users').get('upload_count')[str(user)] >= 250:
                self.user_config.get('users').get('permission')[str(user)] = 4
        json.dump(self.user_config, open('data.json', 'w'))

    def init(self, user, first_use=False):
        json_config = json.loads(
            '{"data": {"pid": [], "r18_pid": []}, "users": {"id": [], "permission": {}, "upload_count": {},"count":{}}}')
        users = json_config.get('users')
        if first_use == True:
            users.get('id').append(str(user))
            users.get('permission')[str(user)] = 6
            json.dump(json_config, open('data.json', 'w'))
            return 0
        else:
            if users.get('permission').get(str(user)) == 6:
                os.remove('data.json')
                users.get('id').append(str(user))
                users.get('permission')[str(user)] = 6
                json.dump(json_config, open('data.json', 'w'))
                return 0
            else:
                return 1
