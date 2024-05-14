import asyncio
import time
import websockets
import json
import requests
from utils.logger import setup_logger
logging = setup_logger(__name__)

type_dict = {
    3: '图片消息不做处理',
    47: '表情消息暂时不做处理',
    49: '卡片消息暂时不做处理',
    10002: '撤回消息暂时不做处理',
}
Group = '43203712205@chatroom'

async def get_uri():
    url = "http://127.0.0.1:8203/ext/www/key.ini"
    response = requests.get(url=url)
    if not response:
        logging.error("Empty response received from %s", url)
        return
    try:
        response_data = response.json()
        secret = response_data.get("key")
        _uri = "ws://127.0.0.1:8202/wx?name=www&key=" + secret
        return _uri
    except json.JSONDecodeError as e:
        logging.error("Failed to decode JSON response from %s: %s", url, e)


async def send_GroupInvite(websocket, Group, wxid):
    data = {
        "method": "sendGroupInvite",
        "wxid": Group,
        "msg": wxid,
        "pid": 0
    }
    await websocket.send(json.dumps(data))
    response = await websocket.recv()
    if response['data']['type'] == 51 and response['data']['utype'] == 3:
        logging.info(f"邀请成功:{response['data']['alias']}")


async def websocket_client():
    uri = await get_uri()
    while True:
        try:
            async with websockets.connect(uri) as websocket:
                async for message in websocket:
                    try:
                        message = json.loads(message)
                        if message.get("method") == "newmsg":
                            msg = f'来自:{message["data"]["nickName"]}, 用户:{message["data"]["memname"]}' if int(
                                message["data"][
                                    'utype']) == 2 else f'用户:{message["data"]["nickName"]}'
                            if int(message["data"]['type']) in type_dict:
                                logging.warning(f'{msg}, 消息：({type_dict[int(message["data"]["type"])]})')
                            else:
                                print(message)
                                if '拉群' == message["data"]["msg"]:
                                    await send_GroupInvite(websocket, Group, message["data"]["fromid"])
                                logging.info(f'{msg}, 消息:{message["data"]["msg"]}')
                    except Exception as e:
                        logging.error(str(e))
                        pass
        except Exception as e:
            logging.error(e)


if __name__ == '__main__':
    asyncio.run(websocket_client())
