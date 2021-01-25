from graia.broadcast.interrupt.waiter import Waiter
from graia.broadcast import Broadcast
from graia.application import GraiaMiraiApplication, Session
from graia.broadcast.interrupt import InterruptControl
from graia.application.message.chain import MessageChain
import asyncio

from graia.application.message.elements.internal import Plain, At, Image
from graia.application.group import Member, Group
from graia.application.friend import Friend
from graia.application.event.messages import FriendMessage

from graia.scheduler import GraiaScheduler
from graia.scheduler.timers import crontabify

from setu_config import qq, authKey, host, admin
from setu_module import *

loop = asyncio.get_event_loop()

bcc = Broadcast(loop=loop)
app = GraiaMiraiApplication(
    broadcast=bcc,
    connect_info=Session(
        host=host,  # 填入 httpapi 服务运行的地址
        authKey=authKey,  # 填入 authKey
        account=qq,  # 你的机器人的 qq 号
        websocket=True,  # Graia 已经可以根据所配置的消息接收的方式来保证消息接收部分的正常运作.
    )
)
scheduler = GraiaScheduler(
    loop, bcc
)

user_data = userData()
setu = setu()
inc = InterruptControl(bcc)


class SetuMessageChain(object):
    async def Creater(self, setu_type, qid, keyword='', r18=False):
        if setu_type == 'local':
            setu_info = await setu.get_local(loop, r18=r18)
            url = setu_info.get('small_url')
        else:
            setu_info = await setu.get_remote(keyword=keyword, r18=r18)
            url = setu_info.get('url')
        title = setu_info.get('title')
        pid = setu_info.get('pid')
        return [
            MessageChain.create([At(qid), Plain(text=f'标题:{title}，ID:{pid}，图片下载：https://pixivic.com/illusts/{pid}')]),
            MessageChain.create([At(qid), Image.fromNetworkAddress(url)])]

    async def Sender(self, group, qid, Creater, r18=False):
        if user_data.get_use_time(qid) <= user_data.get_limit(qid):
            CreaterData = Creater
            await app.sendGroupMessage(group, CreaterData[0])
            user_data.set_use_time(qid)
            if r18 == False:
                bot_message = await app.sendGroupMessage(group, CreaterData[1])
                await asyncio.sleep(user_data.get_revoke_time(qid))
                await app.revokeMessage(bot_message)
        else:
            await app.sendGroupMessage(group, MessageChain.create(
                [At(target=qid), Image.fromNetworkAddress(url='https://s1.ax1x.com/2020/07/28/aE47NR.jpg')]))

    async def FastSender(self, group, qid, text):
        await app.sendGroupMessage(group, MessageChain.create([At(target=qid), Plain(text=text)]))


SetuMessageChain = SetuMessageChain()


class SetuHandler(object):
    async def modeChoser(self, **var_dict):
        '''
        传入mode，group，qid，arg
        '''
        mode = var_dict.get('mode')
        if mode == 'info':
            await self.info(qid=var_dict.get('qid'), group=var_dict.get('group'))
        elif mode == 'upload':
            await self.upload(group=var_dict.get('group'), qid=var_dict.get('qid'))
        elif mode == 'fupload':
            if user_data.get_permission(var_dict.get('qid')) >= 2:
                try:
                    await self.fupload(group=var_dict.get('group'), qid=var_dict.get('qid'),
                                       pids=var_dict.get('arg').split(','))
                except:
                    await self.fupload(group=var_dict.get('group'), qid=var_dict.get('qid'), pids=[var_dict.get('arg')])
            else:
                await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')
        elif mode == 'clear':
            await self.clear(group=var_dict.get('group'), qid=var_dict.get('qid'))
        elif mode == 'count':
            await self.count(group=var_dict.get('group'), qid=var_dict.get('qid'))
        elif mode == 'delete':
            await self.delete(group=var_dict.get('group'), qid=var_dict.get('qid'), pid=var_dict.get('arg'))
        elif mode == 'init':
            await self.count(group=var_dict.get('group'), qid=var_dict.get('qid'))
        elif mode == 'r18':
            if user_data.get_permission(var_dict.get('qid')) >= 2:
                if bool(var_dict.get('arg')):
                    await SetuMessageChain.Sender(r18=True, qid=var_dict.get('qid'), group=var_dict.get('group'),
                                                  Creater=await SetuMessageChain.Creater(setu_type='remote',
                                                                                         qid=var_dict.get('qid'),
                                                                                         keyword=var_dict.get('arg'),
                                                                                         r18=True))
                else:
                    await SetuMessageChain.Sender(r18=True, qid=var_dict.get('qid'), group=var_dict.get('group'),
                                                  Creater=await SetuMessageChain.Creater(setu_type='local',
                                                                                         qid=var_dict.get('qid'),
                                                                                         r18=True))
            else:
                await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')
        elif mode == '':
            await SetuMessageChain.Sender(qid=var_dict.get('qid'), group=var_dict.get('group'),
                                          Creater=await SetuMessageChain.Creater(setu_type='local',
                                                                                 qid=var_dict.get('qid')))
        else:
            await SetuMessageChain.Sender(qid=var_dict.get('qid'), group=var_dict.get('group'),
                                          Creater=await SetuMessageChain.Creater(setu_type='remote',
                                                                                 qid=var_dict.get('qid'), keyword=mode))

    async def info(self, **var_dict):
        '''
        传入group，qid
        '''
        permission = user_data.get_permission(var_dict.get('qid'))
        upload_count = user_data.get_upload_time(var_dict.get('qid'))
        use_times = user_data.get_use_time(var_dict.get('qid'))
        limit = user_data.get_limit(var_dict.get('qid'))
        await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'),
                                          text=f'权限组：{permission}，图片上传次数：{upload_count}，已请求次数：{use_times}，剩余请求次数：{limit - use_times}')

    async def upload(self, **var_dict):
        '''
        传入group，qid
        '''
        await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='请在私聊中完成上传操作')

    async def fupload(self, **var_dict):
        '''
        传入pids（list），group，qid
        '''
        if user_data.get_permission(var_dict.get('qid')) >= 0:
            for i in var_dict.get('pids'):
                pic_info = await get_info(i)
                if pic_info.get('r18'):
                    setu.local_upload(pid=i, r18=True)
                else:
                    setu.local_upload(pid=i, r18=False)
                user_data.set_upload_time(var_dict.get('qid'))
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='上传成功')
        else:
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')

    async def clear(self, **var_dict):
        if user_data.get_permission(var_dict.get('qid')) == 5:
            user_data.clear_use_time()
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='清除成功')
        else:
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')

    async def count(self, **var_dict):
        '''
        传入group，qid
        '''
        await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'),
                                          text=f'图片总数为{setu.local_upload_count_all()}张')

    async def delete(self, **var_dict):
        '''
        传入group，qid，pid
        '''
        if user_data.get_permission(var_dict.get('qid')) == 5:
            try:
                setu.local_upload_del(var_dict.get('pid'))
                await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='删除成功')
            except:
                await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='无此图片')
        else:
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')

    async def init(self, **var_dict):
        if var_dict.get('qid') == admin:
            user_data.set_permission(qid=admin, permission=5)
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='初始化成功！')
        else:
            await SetuMessageChain.FastSender(group=var_dict.get('group'), qid=var_dict.get('qid'), text='你也配？')


SetuHandler = SetuHandler()


@bcc.receiver("GroupMessage")
async def group_listener(app: GraiaMiraiApplication, MessageChain: MessageChain, group: Group, member: Member):
    message = MessageChain.asDisplay()
    if message == '来点色图' or message == '色图来' or message == '色图时间':
        await SetuMessageChain.Sender(group=group, qid=member.id,
                                      Creater=await SetuMessageChain.Creater(setu_type='local', qid=member.id))
    try:
        if MessageChain.get(Image)[0].imageId == '{B407F708-A2C6-A506-3420-98DF7CAC4A57}.jpg':
            await SetuMessageChain.Sender(group=group, qid=member.id,
                                          Creater=await SetuMessageChain.Creater(setu_type='local', qid=member.id))
    #        elif MessageChain.get(Image)[0].imageId == '{}':
    except:
        pass
    try:
        if message.split(' ')[0] == '#SETU':
            try:
                mode = message.split(' ')[1]
            except:
                mode = ''
            try:
                arg = message.split(' ')[2]
            except:
                arg = ''
            await SetuHandler.modeChoser(mode=mode, group=group, qid=member.id, arg=arg)
    except:
        pass


# 存储用临时变量
setu_upload_urls = []
setu_upload_pids = []


@bcc.receiver("FriendMessage")
async def friend_listener(app: GraiaMiraiApplication, message: MessageChain, friend: Friend):
    if message.asDisplay() == "#SETU upload start":
        await app.sendFriendMessage(friend, MessageChain.create([Plain("请发送图片")]))

        @Waiter.create_using_function([FriendMessage])
        def waiter(event: FriendMessage, waiter_friend: Friend, waiter_message: MessageChain):
            if all([waiter_friend.id == friend.id, MessageChain.has(waiter_message, Image)]):
                setu_upload_urls.append(waiter_message.get(Image)[0].url)
                return event

        while message.asDisplay() != '#SETU upload stop':
            await inc.wait(waiter)
    elif message.asDisplay() == '#SETU upload stop':
        try:
            await app.sendFriendMessage(friend, MessageChain.create([Plain(f"开始处理，已接收{len(setu_upload_urls)}图片")]))
            for i in setu_upload_urls:  # 丢到ascii2d里面识别
                setu_upload_pids.append(await pic_get(i))
            for i in setu_upload_urls:  # 图片比对
                for j in setu_upload_pids:
                    pic_info = await get_info(j)
                    pid_url = pic_info.get('url')
                    if await image_match(i, pid_url) <= 0.8:
                        setu_upload_pids.remove(j)
            for i in setu_upload_pids:
                pic_info = await get_info(i)
                r18 = pic_info.get('r18')
                if r18:
                    setu.local_upload(pid=i, r18=True)
                else:
                    setu.local_upload(pid=i)
            for i in range(len(setu_upload_pids)):
                user_data.set_upload_time(qid=friend.id)
            await app.sendFriendMessage(friend, MessageChain.create([Plain(
                f"上传成功！接收图片：{len(setu_upload_urls)}张，成功上传：{len(setu_upload_pids)}张，上传失败：{len(setu_upload_urls) - len(setu_upload_pids)}张")]))
            setu_upload_pids.clear()
            setu_upload_urls.clear()
        except:
            setu_upload_pids.clear()
            setu_upload_urls.clear()


@scheduler.schedule(crontabify("0 4 * * * *"))
def clear_use_times():
    user_data.clear_use_time()


app.launch_blocking()
