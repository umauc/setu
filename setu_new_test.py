import requests
from io import BytesIO
import json
import random
import os
from mirai import Mirai, Plain, GroupMessage, Group, Image, Member, At, FriendMessage, MessageChain, Friend, TempMessage
import regex
from bs4 import BeautifulSoup
import asyncio
from typing import List
import imagehash
import aiohttp
from PIL import Image as Images
from PIL import ImageFile
from pixivpy3 import *
ImageFile.LOAD_TRUNCATED_IMAGES = True

qq = QQ # 字段 qq 的值
authKey = 'authKey' # 字段 authKey 的值
# httpapi所在主机的地址端口,如果 setting.yml 文件里字段 "enableWebsocket" 的值为 "true" 则需要将 "/" 换成 "/ws", 否则将接收不到消息.
mirai_api_http = '127.0.0.1:8080/ws'

app = Mirai(f"mirai://{mirai_api_http}?authKey={authKey}&qq={qq}")

api = ByPassSniApi()
api.require_appapi_hosts()
api.set_accept_language('en-us')
api.login('账号', '密码') # pixiv登陆

class setu_get(object):
    def __init__(self):
        print('初始化')
        self.setu_url = 'https://api.lolicon.app/setu/?apikey=408800685e6e285c17f744&size1200=true&keyword='
        self.setu_url_r18 = 'https://api.lolicon.app/setu/?apikey=408800685e6e285c17f744&size1200=true&r18=1&keyword='

    def local(self,r18=False):
        self.data = json.load(open('config.json', 'r'))
        pid_len = int(len(self.data.get('data').get('pid')))
        r18_pid_len = int(len(self.data.get('data').get('r18_pid')))
        if r18 == False:
            self.pid = self.data.get('data').get('pid')[random.randint(0,pid_len-1)]
        else:
            self.pid = self.data.get('data').get('r18_pid')[random.randint(0,r18_pid_len-1)]
        try:
            pic_data = api.illust_detail(self.pid)
            self.title = pic_data.get('illust').get('title')
            self.url = pic_data.get('illust').get('image_urls').get('large').replace('pximg.net','pixiv.cat')
            return {'pid':self.pid,'title':self.title,'url':self.url}
        except:
            pass
    def web(self,keyword='',r18=False):
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
            return {'pid':self.pid,'title':self.title,'url':self.url}



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
            return int(regex.compile('(^https://www.pixiv.net/artworks/(\d*)$)', regex.I).match(url_list[0])[2])
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
            self.user_config = json.load(open('config.json', 'r'))
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
        json.dump(self.user_config, open('config.json', 'w'))

    def count_zero(self):
        self.user_config.get('users').get('count').clear()
        json.dump(self.user_config, open('config.json', 'w'))

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
        json.dump(self.user_config, open('config.json', 'w'))

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
        json.dump(self.user_config, open('config.json', 'w'))

    def upload_delete(self,pid):
        try:
            self.user_config.get('pid').remove(int(pid))
        except:
            self.user_config.get('r18_pid').remove(int(pid))
        json.dump(self.user_config, open('config.json', 'w'))

    def permission_set(self, user, permission):
        self.user_config.get('users').get('permission')[str(user)] = permission
        json.dump(self.user_config, open('config.json', 'w'))

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
        json.dump(self.user_config, open('config.json', 'w'))

    def init(self, user, first_use=False):
        json_config = json.loads(
            '{"data": {"pid": [], "r18_pid": []}, "users": {"id": [], "permission": {}, "upload_count": {},"count":{}}}')
        users = json_config.get('users')
        if first_use == True:
            users.get('id').append(str(user))
            users.get('permission')[str(user)] = 6
            json.dump(json_config, open('config.json', 'w'))
            return 0
        else:
            if users.get('permission').get(str(user)) == 6:
                os.remove('config.json')
                users.get('id').append(str(user))
                users.get('permission')[str(user)] = 6
                json.dump(json_config, open('config.json', 'w'))
                return 0
            else:
                return 1
try:
    user_config = json.load(open('config.json', 'r'))
except:
    print('配置读取错误！请初始化！')
    first_use = True

config = config()
setu_get = setu_get()

@app.receiver('GroupMessage')
async def setu(app: Mirai, gm: GroupMessage, group: Group, member: Member):
    if str(type(gm.messageChain.__root__[1])) == "<class 'mirai.event.message.components.Plain'>":
        message = gm.messageChain.__root__[1].text
        try:
            match = regex.compile('^#?(SETU)?(?<keyword>.*)$', regex.I).match(message)[1]
            if match == 'SETU':
                keyword = regex.compile('^#?(SETU)?(?<keyword>.*)$', regex.I).match(message)[2].replace(' ','')
                if keyword == 'info':
                    permission = config.permission_get(member.id)
                    upload_count = config.upload_count_get(member.id)
                    await app.sendGroupMessage(group, [At(target=member.id), Plain(text=f'权限组：{permission}，图片上传次数：{upload_count}')])
                elif keyword =="init":
                    if config.init(user=member.id,first_use=first_use) == 0:
                        await app.sendGroupMessage(group,[At(target=member.id),Plain(text='初始化成功！您已成为插件管理员！')])
                    else:
                        await app.sendGroupMessage(group,[At(target=member.id),Plain(text='你是个锤子插件管理员，爪巴')])
                elif keyword == 'upload':
                    await app.sendGroupMessage(group,[At(target=member.id),Plain(text='请在私聊中完成上传操作')])
                elif keyword == 'zero':
                    permission = config.permission_get(member.id)
                    if permission == 6:
                        config.count_zero()
                        await app.sendGroupMessage(group,[At(target=member.id),Plain(text='已将次数清零')])
                    else:
                        await app.sendGroupMessage(group,[At(target=member.id),Plain(text='你是个锤子插件管理员，爪巴')])
                elif keyword == 'count':
                    count = str(config.setu_count())
                    await app.sendGroupMessage(group,[At(target=member.id),Plain(text=f'色图总数为{count}张')])
                elif str(keyword).find('delete') == 0:
                    permission = config.permission_get(member.id)
                    if permission == 6:
                        await app.sendGroupMessage(group, [At(target=member.id), Plain(text='已删除')])
                        config.upload_delete(int(keyword.replace('delete','')))
                    else:
                        await app.sendGroupMessage(group, [At(target=member.id), Plain(text='你是个锤子插件管理员，爪巴')])
                elif keyword == '':
                    print('无关键词')
                    if config.count_get(member.id) <= config.limit(member.id):
                        setu_data = setu_get.local()
                        setu_pid = setu_data.get('pid')
                        setu_title = setu_data.get('title')
                        setu_url = setu_data.get('url')
                        await app.sendGroupMessage(group,[At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')])
                        try:
                            bot_message = await app.sendGroupMessage(group,[Plain(text=setu_url),await Image.fromRemote(setu_get.url)])
                        except:
                            await app.sendGroupMessage(group,[Plain(text=setu_url)])
                        permission = config.permission_get(member.id)
                        if permission >= 4:
                            pass
                        else:
                            await asyncio.sleep(config.revoke(member.id))
                            await app.revokeMessage(bot_message.messageId)
                        config.count(member.id)
                    else:
                        await app.sendGroupMessage(group,[At(target=member.id),await Image.fromRemote('https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
                else:
                    if keyword.find('R18') == 0:
                        print('R18')
                        permission = config.permission_get(member.id)
                        if permission >= 3:
                            if keyword.replace('R18','') == '':
                                print('R18无关键词')
                                setu_data = setu_get.local(r18=True)
                                setu_pid = setu_data.get('pid')
                                setu_title = setu_data.get('title')
                                setu_url = setu_data.get('url')
                                await app.sendGroupMessage(group,[At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')])
                                try:
                                    bot_message = await app.sendGroupMessage(group,[Plain(text=setu_get.url),await Image.fromRemote(setu_url)])
                                except:
                                    await app.sendGroupMessage(group,[Plain(text=setu_url)])
                                permission = config.permission_get(member.id)
                                if permission >= 4:
                                    pass
                                else:
                                    await asyncio.sleep(config.revoke(member.id))
                                    await app.revokeMessage(bot_message.messageId)
                                config.count(member.id)
                            else:
                                print('R18有关键词')
                                setu_data = setu_get.web(keyword=keyword.replace('R18',''),r18=True)
                                setu_pid = setu_data.get('pid')
                                setu_title = setu_data.get('title')
                                setu_url = setu_data.get('url')
                                await app.sendGroupMessage(group,[At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')])
                                try:
                                    bot_message = await app.sendGroupMessage(group,[Plain(text=setu_url),await Image.fromRemote(setu_url)])
                                except:
                                    await app.sendGroupMessage(group,[Plain(text=setu_url)])
                                permission = config.permission_get(member.id)
                                if permission >= 4:
                                    pass
                                else:
                                    await asyncio.sleep(config.revoke(member.id))
                                    await app.revokeMessage(bot_message.messageId)
                                config.count(member.id)
                        else:
                            await app.sendGroupMessage(group, [At(target=member.id), await Image.fromRemote('https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
                    else:
                        print('有关键词')
                        if config.count_get(member.id) <= config.limit(member.id):
                            setu_data = setu_get.web(keyword)
                            setu_pid = setu_data.get('pid')
                            setu_title = setu_data.get('title')
                            setu_url = setu_data.get('url')
                            await app.sendGroupMessage(group, [At(target=member.id), Plain(text=f'标题:{setu_get.title}，ID:{setu_get.pid}')])
                            try:
                                bot_message = await app.sendGroupMessage(group,[Plain(text=setu_get.url),await Image.fromRemote(setu_url)])
                            except:
                                await app.sendGroupMessage(group,[Plain(text=setu_url)])
                                permission = config.permission_get(member.id)
                                if permission >= 4:
                                    pass
                                else:
                                    await asyncio.sleep(config.revoke(member.id))
                                    await app.revokeMessage(bot_message.messageId)
                                config.count(member.id)
                        else:
                            await app.sendGroupMessage(group, [At(target=member.id), await Image.fromRemote('https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
        except:
            raise
    elif str(type(gm.messageChain.__root__[1])) == "<class 'mirai.event.message.components.Image'>":
        imageID = gm.messageChain.__root__[1].imageId
        if imageID == 'B407F708-A2C6-A506-3420-98DF7CAC4A57':
            if config.count_get(member.id) <= config.limit(member.id):
                setu_data = setu_get.local()
                setu_pid = setu_data.get('pid')
                setu_title = setu_data.get('title')
                setu_url = setu_data.get('url')
                await app.sendGroupMessage(group,[At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')])
                try:
                    bot_message = await app.sendGroupMessage(group,[Plain(text=setu_url),await Image.fromRemote(setu_url)])
                except:
                    await app.sendGroupMessage(group,[Plain(text=setu_url)])
                permission = config.permission_get(member.id)
                if permission >= 4:
                    pass
                else:
                    await asyncio.sleep(config.revoke(member.id))
                    await app.revokeMessage(bot_message.messageId)
                config.count(member.id)
            else:
                await app.sendGroupMessage(group,[At(target=member.id),await Image.fromRemote('https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
setuon = False
@app.receiver('FriendMessage')
async def setu_upload(app: Mirai, message: MessageChain, friend: Friend):
    global setuon
    global all_images_url
    async def pic_con(all_images_url,user):
        all_images_pid = []
        try:
            await app.sendFriendMessage(user,[Plain(text='获取ID')])
            print(friend.nickname+'：获取ID')
            for i in all_images_url:
                pid = await pic_get(i)
                if pid == 0:
                    pass
                else:
                    all_images_pid.append(pid)
            all_images_pid_for = all_images_pid.copy()
            await app.sendFriendMessage(user,[Plain(text='图片差异处理')])
            print(friend.nickname+'：图片差异处理')
            for i in range(len(all_images_url)):
                try:
                    diff = await image_match(url1='https://pixiv.cat/' + str(all_images_pid_for[i]) + '.png', url2=all_images_url[i])
                    if diff < 0.9:
                        all_images_pid.remove(i)
                except:
                    pass
            all_images_pid_r18 = []
            try:
                await app.sendFriendMessage(user,[Plain(text='R18识别')])
                print(friend.nickname+'：R18识别')
                for i in all_images_pid:
                    if api.illust_detail(i).get('illust').get('tags')[0].get('name') == 'R-18':
                        all_images_pid_r18.append(i)
                        all_images_pid.remove(i)
            except:
                pass
        except:
            pass
        try:
            print ('处理完成')
            user = friend.id
            config.upload(data=all_images_pid,r18_data=all_images_pid_r18)
            config.upload_count(user=user,count=len(all_images_pid)+len(all_images_pid_r18))
            config.permission_refresh(user=user)
            config.__init__
            permission = config.permission_get(user)
            upload_count = config.upload_count_get(user)
            await app.sendFriendMessage(user,[Plain(text=f'添加成功！你现在的权限组为{permission}，上传数为{upload_count}')])
        except:
            await app.sendFriendMessage(user,[Plain(text='你有传图？？？')])
    if str(type(message.__root__[1])) == "<class 'mirai.event.message.components.Plain'>":
        text = message.__root__[1].text
        if text.replace(' ','') == '#SETUupload':
                print(friend.nickname+'：开始处理上传')
                user = friend.id
                await app.sendFriendMessage(user,[Plain(text='正在处理...\n此过程可能耗费较长时间')])
                all_images: List[Image] = \
                    message.getAllofComponent(Image)
                #if len(all_images) >6:
                    #await app.sendFriendMessage(user,[Plain(text='太多了…不要 ♡')])
                all_images_url = []
                for i in all_images:
                    all_images_url.append(i.url)
                await pic_con(all_images_url=all_images_url,user=friend)
        elif text.replace(' ','') == '#SETUuploadon':
            user = friend
            setuon = True
            await app.sendFriendMessage(user,[Plain(text='现在，开始你的表演')])
        elif text.replace(' ','') == '#SETUuploadoff':
            user = friend
            setuon = False
            await app.sendFriendMessage(user,[Plain(text='表演结束，开始处理')])
            await pic_con(all_images_url=all_images_url,user=friend)
    elif str(type(message.__root__[1])) == "<class 'mirai.event.message.components.Image'>" and setuon == True:
        try:
            all_images_url
        except NameError:
            all_images_url = []
        else:
            pass
        all_images: List[Image] = \
            message.getAllofComponent(Image)
        for i in all_images:
            all_images_url.append(i.url)
        await app.sendFriendMessage(friend,[Plain(text='图片已添加')])

if __name__ == '__main__':
    app.run()
