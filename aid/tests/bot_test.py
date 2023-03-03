import pytest
from time import sleep
import os
from telethon.tl.custom.message import Message

SLEEP_SEC = 3


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
async def test_bot_start(empty_conv):
    resp: Message = await empty_conv.get_response()
    assert resp.button_count != 0
    assert "test_med_nika_bot" in resp.chat.username


@pytest.mark.anyio
async def test_bot_connect_delete_to_kit(empty_conv):
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


@pytest.mark.anyio
async def test_bot_import_export(conv_with_connection):
    # check import
    sleep(SLEEP_SEC)
    await conv_with_connection.send_message("/import_csv")
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Давай добавим лекарства из твоего файла" in resp.raw_text
    import_csv_path = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'input_example.csv')
    csv_path_exp = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), 'test_export.csv')
    num_of_meds = 59
    await conv_with_connection.send_file(import_csv_path)
    resp: Message = await conv_with_connection.get_response(timeout=15)
    assert f"Было успешно загружено {num_of_meds} лекарств" in resp.raw_text

    # check export
    await conv_with_connection.send_message("/export_csv")
    resp: Message = await conv_with_connection.get_response(timeout=5)
    await resp.download_media(file=csv_path_exp)
    sleep(4)
    assert os.path.exists(csv_path_exp)
    with open(csv_path_exp, 'r', encoding='utf-8') as exp:
        lines = [line for line in exp.readlines() if line.strip() != '']
        assert len(lines) == num_of_meds + 1

    os.remove(csv_path_exp)


@pytest.mark.anyio
async def test_bot_search_name(conv_with_data):
    await conv_with_data.send_message('/search')

    resp: Message = await conv_with_data.get_response(timeout=5)
    assert "Произвести поиск лекарcтва по имени" in resp.raw_text
    await resp.click(data=b'search_name')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'Введи имя лекарства.' in resp.raw_text
    await conv_with_data.send_message('АнвиМакс')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'Было найдено 1 лекарств.' in resp.raw_text

    await conv_with_data.send_message('/search')
    resp: Message = await conv_with_data.get_response(timeout=5)
    await resp.click(data=b'search_name')
    resp = await conv_with_data.get_response(timeout=5)
    await conv_with_data.send_message('unexisting')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'не было найдено.' in resp.raw_text


@pytest.mark.anyio
async def test_bot_search_category(conv_with_data):
    sleep(SLEEP_SEC)
    await conv_with_data.send_message('/search')

    resp: Message = await conv_with_data.get_response(timeout=5)
    assert "Произвести поиск лекарcтва по имени" in resp.raw_text
    await resp.click(data=b'search_cat')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'Введи имя категории.' in resp.raw_text
    await conv_with_data.send_message('Вывих')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'Было найдено 1 лекарств.' in resp.raw_text

    await conv_with_data.send_message('/search')
    resp: Message = await conv_with_data.get_response(timeout=5)
    await resp.click(data=b'search_cat')
    resp = await conv_with_data.get_response(timeout=5)
    await conv_with_data.send_message('unexisting')
    resp = await conv_with_data.get_response(timeout=5)
    assert 'не было найдено.' in resp.raw_text


@pytest.mark.anyio
async def test_bot_add_new_med_unique(conv_with_connection):
    sleep(SLEEP_SEC)
    await conv_with_connection.send_message('/add_med')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Давай добавим новое лекарство.' in resp.raw_text
    await conv_with_connection.send_message('test_med_1')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Теперь введи количество лекарства' in resp.raw_text
    await conv_with_connection.send_message('5')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Теперь введи местоположение лекарства' in resp.raw_text
    await conv_with_connection.send_message('location')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Теперь введи от чего данное лекарство." in resp.raw_text
    await conv_with_connection.send_message('ill')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Теперь введи срок годности лекарства." in resp.raw_text
    await conv_with_connection.send_message('09/2022')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Лекарство добавлено успешно:" in resp.raw_text
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Текущее количество лекарств в твоей аптечке test_1 : 1' in resp.raw_text

    await conv_with_connection.send_message('/add_med')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('test_med_2')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('5')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('location')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('ill')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('09/2022')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Лекарство добавлено успешно:" in resp.raw_text
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Текущее количество лекарств в твоей аптечке test_1 : 2' in resp.raw_text


@pytest.mark.anyio
async def test_bot_add_new_med_incorrect(conv_with_connection):
    sleep(SLEEP_SEC)
    await conv_with_connection.send_message('/add_med')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Давай добавим новое лекарство.' in resp.raw_text
    await conv_with_connection.send_message('test_med_1')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Теперь введи количество лекарства' in resp.raw_text
    await conv_with_connection.send_message('incorrect')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Некорректный формат количества. ' in resp.raw_text
    await conv_with_connection.send_message('5')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Теперь введи местоположение лекарства' in resp.raw_text
    await conv_with_connection.send_message('location')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Теперь введи от чего данное лекарство." in resp.raw_text
    await conv_with_connection.send_message('ill')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Теперь введи срок годности лекарства." in resp.raw_text
    await conv_with_connection.send_message('incorrect')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Некорректный формат даты.' in resp.raw_text
    await conv_with_connection.send_message('09/2022')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Лекарство добавлено успешно:" in resp.raw_text
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Текущее количество лекарств в твоей аптечке test_1 : 1' in resp.raw_text


@pytest.mark.anyio
async def test_bot_add_new_med_copy(conv_with_connection):
    sleep(SLEEP_SEC)
    num_1 = 5
    await conv_with_connection.send_message('/add_med')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('test_med_2')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message(str(num_1))
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('location')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('ill')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('09/2022')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Лекарство добавлено успешно:" in resp.raw_text
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Текущее количество лекарств в твоей аптечке test_1 : 1' in resp.raw_text

    num_2 = 15
    await conv_with_connection.send_message('/add_med')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('test_med_2')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message(str(num_2))
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('location')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('ill')
    await conv_with_connection.get_response(timeout=5)
    await conv_with_connection.send_message('09/2022')
    await conv_with_connection.get_response(timeout=5)
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert "Лекарство добавлено успешно:" in resp.raw_text
    assert str(num_2 + num_1) in resp.raw_text
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'Текущее количество лекарств в твоей аптечке test_1 : 1' in resp.raw_text


@pytest.mark.anyio
async def test_bot_list_med_empty(conv_with_connection):
    sleep(SLEEP_SEC)
    await conv_with_connection.send_message('/list_med')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'не содержит лекарств.' in resp.raw_text


@pytest.mark.anyio
async def test_bot_list_category_empty(conv_with_connection):
    sleep(SLEEP_SEC)
    await conv_with_connection.send_message('/list_med_category')
    resp: Message = await conv_with_connection.get_response(timeout=5)
    assert 'не содержит лекарств.' in resp.raw_text


@pytest.mark.anyio
async def test_bot_list_med(conv_with_data):
    sleep(SLEEP_SEC)
    await conv_with_data.send_message('/list_med')
    resp: Message = await conv_with_data.get_response(timeout=10)
    assert 'содержит 59' in resp.raw_text
    assert 'анвимакс' in resp.raw_text


@pytest.mark.anyio
async def test_bot_list_med(conv_with_data):
    sleep(SLEEP_SEC)
    await conv_with_data.send_message('/list_med_category')
    resp: Message = await conv_with_data.get_response(timeout=10)
    assert 'орви' in resp.raw_text


@pytest.mark.anyio
async def test_bot_take_med(conv_with_data):
    # check incorrect date
    # check incorrect quantity
    pass
