import pytest
from time import sleep
from telethon.tl.custom.message import Message

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


@pytest.mark.anyio
async def test_start(empty_conv):
    resp: Message = await empty_conv.get_response()
    assert resp.button_count != 0
    assert "test_med_nika_bot" in resp.chat.username


@pytest.mark.anyio
async def test_connect_delete_to_kit(empty_conv):
    # create additional kit
    aid_name2 = "my_test2"
    resp: Message = await create_new_kit(empty_conv, aid_name2)
    assert f"Имя твоей аптечки {aid_name2}" in resp.raw_text

    # reconnect and create
    aid_name = "my_test"
    resp = await create_new_kit(empty_conv, aid_name)
    assert f"Имя твоей аптечки {aid_name}" in resp.raw_text

    # delete-no aid_kit
    resp = await delete_cur_kit(empty_conv, b'delete_no')
    assert 'Подтвтерждение процесса удаления не было получено.' in resp.raw_text

    # check connect to existing one
    sleep(SLEEP_SEC)
    await empty_conv.send_message("/start")
    resp: Message = await empty_conv.get_response(timeout=5)
    await resp.click(data=b'old')
    resp = await empty_conv.get_response(timeout=5)
    assert 'Выбери одну из существующих аптечек' in resp.raw_text

    # check list of existing kits
    list_of_kits = []
    for row in resp.buttons:
        for b in row:
            list_of_kits.append(b.text)

    assert len(list_of_kits) == 2
    assert aid_name in list_of_kits
    assert aid_name2 in list_of_kits

    await resp.click(text=aid_name2)
    await empty_conv.get_response(timeout=5)
    resp: Message = await empty_conv.get_response(timeout=5)
    assert f"Текущее количество лекарств в твоей аптечке {aid_name2} : 0" in resp.raw_text

    # delete-yes aid_kit1
    resp = await delete_cur_kit(empty_conv, b'delete_yes')
    assert f'Аптечка {aid_name2} успешно удалена.' in resp.raw_text

    await empty_conv.send_message("/start")
    resp: Message = await empty_conv.get_response(timeout=5)
    await resp.click(data=b'old')
    resp = await empty_conv.get_response(timeout=5)
    for row in resp.buttons:
        for b in row:
            assert aid_name2 not in b.text

    # delete-yes aid_kit 2 without connection
    await empty_conv.send_message("/delete_aid_kit")
    resp: Message = await empty_conv.get_response(timeout=5)
    assert "Чтобы произвести операцию 'удаление аптечки' необходимо подключится к аптечке." in resp.raw_text

    # delete-yes aid_kit 2 with connection
    sleep(SLEEP_SEC)
    await empty_conv.send_message("/start")
    resp: Message = await empty_conv.get_response(timeout=5)
    await resp.click(data=b'old')
    resp = await empty_conv.get_response(timeout=5)
    await resp.click(text=aid_name)

    # there are no kits in current conversation
    sleep(SLEEP_SEC)
    resp = await delete_cur_kit(empty_conv)
    assert f'Аптечка {aid_name} успешно удалена.' in resp.raw_text
    await empty_conv.send_message("/start")
    resp: Message = await empty_conv.get_response(timeout=5)
    await resp.click(data=b'old')
    resp = await empty_conv.get_response(timeout=5)
    assert f"Сейчас нету существующих аптечек." in resp.raw_text
