import pytest
import os
from time import sleep
import asyncio
from telethon.sessions import StringSession
from telethon import TelegramClient
from telethon.tl.custom.message import Message
import platform

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


# Your API ID, hash and session string here
api_id = int(os.environ["TELEGRAM_APP_ID"])
api_hash = os.environ["TELEGRAM_APP_HASH"]

session_str = os.environ["TELETHON_SESSION"]
SLEEP_SEC = 4


async def delete_cur_kit(conv, click=b'delete_yes'):
    sleep(SLEEP_SEC)
    await conv.send_message("/delete_aid_kit")
    resp: Message = await conv.get_response(timeout=5)
    await resp.click(data=click)
    resp: Message = await conv.get_response(timeout=5)
    return resp


async def create_new_kit(conv, aid_name):
    sleep(SLEEP_SEC)
    await conv.send_message("/start")
    resp: Message = await conv.get_response(timeout=5)
    await resp.click(data=b'new')
    await conv.get_response(timeout=5)
    await conv.send_message(aid_name)
    resp: Message = await conv.get_response(timeout=5)
    return resp


@pytest.fixture(scope="function")
async def conv_with_connection():
    client = TelegramClient(
        StringSession(session_str), api_id, api_hash,
        sequential_updates=True
    )
    await client.connect()
    async with client.conversation("@test_med_nika_bot") as conv:
        await create_new_kit(conv, "test_1")
        yield conv
        await delete_cur_kit(conv)


@pytest.fixture(scope="function")
async def conv_with_data():
    client = TelegramClient(
        StringSession(session_str), api_id, api_hash,
        sequential_updates=True
    )
    await client.connect()
    async with client.conversation("@test_med_nika_bot") as conv:
        await create_new_kit(conv, "test_data")
        await conv.send_message("/import_csv")
        await conv.get_response(timeout=5)
        import_csv_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), 'input_example.csv')
        await conv.send_file(import_csv_path)
        await conv.get_response(timeout=5)
        await conv.get_response(timeout=5)
        yield conv
        await delete_cur_kit(conv)


@pytest.fixture(scope="function")
async def empty_conv():
    client = TelegramClient(
        StringSession(session_str), api_id, api_hash,
        sequential_updates=True
    )
    await client.connect()
    async with client.conversation("@test_med_nika_bot") as conv:
        await conv.send_message("/start")
        yield conv
