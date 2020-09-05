from graia.application.event.messages import Member, Group, Friend
from graia.application.message.chain import MessageChain
from graia.application.event.messages import GroupMessage, FriendMessage
from graia.application import GraiaMiraiApplication, Session
from graia.broadcast import Broadcast
from graia.application import group
import requests
import json
import random
import os
import requests
import regex
import asyncio
from typing import List
from pixivpy3 import *
from setu_config import *
from setu_class import *
from graia.application.message.elements.internal import Plain ,At ,Image

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=host,  # 填入 httpapi 服务运行的地址
        authKey=authKey,  # 填入 authKey
        account=qq,  # 你的机器人的 qq 号
        websocket=True  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)

try:
    user_config = json.load(open('data.json', 'r'))
except:
    print('配置读取错误！请初始化！')
    first_use = True

config = config()
setu_get = setu_get()

@bcc.receiver('GroupMessage')
async def setu(app: GraiaMiraiApplication, gm: GroupMessage, group: Group, member: Member):
    if str(type(gm.messageChain.__root__[1])) == "<class 'graia.application.message.elements.internal.Plain'>":
        message = gm.messageChain.__root__[1].text
        if message == '色图来' or message == '来点色图':
            if config.count_get(member.id) <= config.limit(member.id):
                setu_data = setu_get.local()
                setu_pid = setu_data.get('pid')
                setu_title = setu_data.get('title')
                setu_url = setu_data.get('url')
                setu_large_url = setu_data.get('large_url')
                await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')]))
                try:
                    bot_message = await app.sendGroupMessage(group, MessageChain.create([Plain(text=setu_large_url), Image.fromNetworkAddress(url=setu_url)]))
                except:
                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url)]))
                permission = config.permission_get(member.id)
                if permission >= 4:
                    pass
                else:
                    await asyncio.sleep(config.revoke(member.id))
                    await app.revokeMessage(bot_message.messageId)
                config.count(member.id)
            else:
                await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')]))
        else:
            try:
                match = regex.compile('^#?(SETU)?(?<keyword>.*)$', regex.I).match(message)[1]
                if match == 'SETU':
                    keyword = regex.compile('^#?(SETU)?(?<keyword>.*)$', regex.I).match(message)[2].replace(' ','')
                    if keyword == 'info':
                        permission = config.permission_get(member.id)
                        upload_count = config.upload_count_get(member.id)
                        await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Plain(text=f'权限组：{permission}，图片上传次数：{upload_count}')]))
                    elif keyword =="init":
                        if config.init(user=member.id,first_use=first_use) == 0:
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='初始化成功！您已成为插件管理员！')]))
                        else:
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='你是个锤子插件管理员，爪巴')]))
                    elif keyword == 'upload':
                        await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='请在私聊中完成上传操作')]))
                    elif keyword.find('fupload') == 0:
                        permission = config.permission_get(member.id)
                        if permission >= 2:
                            try:
                                try:
                                    setu_list_raw = keyword.replace('fupload','').split(',')
                                    setu_list = []
                                    for i in setu_list_raw:
                                        setu_list.append(int(i))
                                    config.upload(setu_list)
                                    config.upload_count(member.id,len(setu_list))
                                    await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='上传成功！')]))
                                except:
                                    config.upload([int(keyword.replace('fupload',''))])
                                    config.upload_count(member.id,1)
                                    await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='上传成功！')]))
                            except:
                                await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='上传失败！')]))
                        else:
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='你无权限使用快速上传功能')]))
                    elif keyword == 'zero':
                        permission = config.permission_get(member.id)
                        if permission == 6:
                            config.count_zero()
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='已将次数清零')]))
                        else:
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text='你是个锤子插件管理员，爪巴')]))
                    elif keyword == 'count':
                        count = str(config.setu_count())
                        await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'色图总数为{count}张')]))
                    elif str(keyword).find('delete') == 0:
                        permission = config.permission_get(member.id)
                        if permission == 6:
                            await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Plain(text='已删除')]))
                            config.upload_delete(keyword.replace('delete',''))
                        else:
                            await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Plain(text='你是个锤子插件管理员，爪巴')]))
                    elif keyword == '':
                        print('无关键词')
                        if config.count_get(member.id) <= config.limit(member.id):
                            setu_data = setu_get.local()
                            setu_pid = setu_data.get('pid')
                            setu_title = setu_data.get('title')
                            setu_url = setu_data.get('url')
                            setu_large_url = setu_data.get('large_url')
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')]))
                            try:
                                bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url),Image.fromNetworkAddress(url=setu_get.url)]))
                            except:
                                bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url)]))
                            permission = config.permission_get(member.id)
                            if permission >= 4:
                                pass
                            else:
                                await asyncio.sleep(config.revoke(member.id))
                                await app.revokeMessage(bot_message.messageId)
                            config.count(member.id)
                        else:
                            await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')]))
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
                                    setu_large_url = setu_data.get('large_url')
                                    await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')]))
                                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url)]))
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
                                    await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')]))
                                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_url)]))
                                    permission = config.permission_get(member.id)
                                    if permission >= 4:
                                        pass
                                    else:
                                        await asyncio.sleep(config.revoke(member.id))
                                        await app.revokeMessage(bot_message.messageId)
                                    config.count(member.id)
                            else:
                                await app.sendGroupMessage(group, [At(target=member.id), Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
                        else:
                            print('有关键词')
                            if config.count_get(member.id) <= config.limit(member.id):
                                setu_data = setu_get.web(keyword)
                                setu_pid = setu_data.get('pid')
                                setu_title = setu_data.get('title')
                                setu_url = setu_data.get('url')
                                await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Plain(text=f'标题:{setu_get.title}，ID:{setu_get.pid}')]))
                                try:
                                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_get.url),Image.fromNetworkAddress(url=setu_url)]))
                                except:
                                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_url)]))
                                    permission = config.permission_get(member.id)
                                    if permission >= 4:
                                        pass
                                    else:
                                        await asyncio.sleep(config.revoke(member.id))
                                        await app.revokeMessage(bot_message.messageId)
                                    config.count(member.id)
                            else:
                                await app.sendGroupMessage(group, [At(target=member.id), Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')])
            except:
                raise
    elif str(type(gm.messageChain.__root__[1])) == "<class 'graia.application.message.elements.internal.Image'>":
        imageID = gm.messageChain.__root__[1].imageId
        if imageID == 'B407F708-A2C6-A506-3420-98DF7CAC4A57':
            if config.count_get(member.id) <= config.limit(member.id):
                setu_data = setu_get.local()
                setu_pid = setu_data.get('pid')
                setu_title = setu_data.get('title')
                setu_url = setu_data.get('url')
                setu_large_url = setu_data.get('large_url')
                await app.sendGroupMessage(group,MessageChain.create([At(target=member.id),Plain(text=f'标题:{setu_title}，ID:{setu_pid}')]))
                try:
                    bot_message = await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url),Image.fromNetworkAddress(url=setu_url)]))
                except:
                    await app.sendGroupMessage(group,MessageChain.create([Plain(text=setu_large_url)]))
                permission = config.permission_get(member.id)
                if permission >= 4:
                    pass
                else:
                    await asyncio.sleep(config.revoke(member.id))
                    await app.revokeMessage(bot_message.messageId)
                config.count(member.id)
            else:
                await app.sendGroupMessage(group, MessageChain.create([At(target=member.id), Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')]))
setuon = False

@bcc.receiver('FriendMessage')
async def setu_upload(app: GraiaMiraiApplication, message: MessageChain, friend: Friend):
    global setuon
    global all_images_url
    async def pic_con(all_images_url,user):
        all_images_pid = []
        try:
            await app.sendFriendMessage(user,MessageChain.create([Plain(text='获取ID')]))
            print(friend.nickname+'：获取ID')
            for i in all_images_url:
                pid = await pic_get(i)
                if pid == 0:
                    pass
                else:
                    all_images_pid.append(pid)
            all_images_pid_for = all_images_pid.copy()
            await app.sendFriendMessage(user,MessageChain.create([Plain(text='图片差异处理')]))
            print(friend.nickname+'：图片差异处理')
            for i in range(len(all_images_url)):
                try:
                    diff = await image_match(url1=pic_get_info(all_images_pid_for[i]), url2=all_images_url[i])
                    if diff < 0.9:
                        all_images_pid.remove(i)
                except:
                    pass
            all_images_pid_r18 = []
            try:
                await app.sendFriendMessage(user,MessageChain.create([Plain(text='R18识别')]))
                print(friend.nickname+'：R18识别')
                for i in all_images_pid:
                    if pic_get_info(i).get('r18') == True:
                        all_images_pid_r18.append(i)
                        all_images_pid.remove(i)
            except:
                raise
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
            await app.sendFriendMessage(user,MessageChain.create([Plain(text=f'添加成功！你现在的权限组为{permission}，上传数为{upload_count}')]))
        except:
            await app.sendFriendMessage(user,MessageChain.create([Plain(text='你有传图？？？')]))
    if str(type(message.__root__[1])) == "<class 'graia.application.message.elements.internal.Plain'>":
        text = message.__root__[1].text
        if text.replace(' ','') == '#SETUupload':
                print(friend.nickname+'：开始处理上传')
                user = friend.id
                await app.sendFriendMessage(user,MessageChain.create([Plain(text='正在处理...\n此过程可能耗费较长时间')]))
                all_images: List[Image] = \
                    message.getAllofComponent(Image)
                #if len(all_images) >6:
                    #await app.sendFriendMessage(user,MessageChain.create([Plain(text='太多了…不要 ♡')]))
                all_images_url = []
                for i in all_images:
                    all_images_url.append(i.url)
                await pic_con(all_images_url=all_images_url,user=friend)
        elif text.replace(' ','') == '#SETUuploadon':
            user = friend
            setuon = True
            await app.sendFriendMessage(user,MessageChain.create([Plain(text='现在，开始你的表演')]))
        elif text.replace(' ','') == '#SETUuploadoff':
            user = friend
            setuon = False
            await app.sendFriendMessage(user,MessageChain.create([Plain(text='表演结束，开始处理')]))
            await pic_con(all_images_url=all_images_url,user=friend)
    elif str(type(message.__root__[1])) == "<class 'graia.application.message.elements.internal.Image'>" and setuon == True:
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
        await app.sendFriendMessage(friend,MessageChain.create([Plain(text='图片已添加')]))

if __name__ == '__main__':
    app.launch_blocking()
