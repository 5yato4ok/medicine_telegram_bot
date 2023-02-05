import sys
import logging
import html
import json
import datetime
import os
import traceback
from pathlib import Path
from telegram import *
from telegram.ext import *
from telegram.constants import ParseMode
file = Path(__file__).resolve()  # nopep8
parent, root = file.parent, file.parents[1]  # nopep8
sys.path.append(str(root))  # nopep8

from aid import aid_manager as mngr

try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass


logging.basicConfig(
    format='Telegramm Bot: %(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
aids = mngr.Aid()

# signals
AGREE, INIT_KIT, MED_NAME, MED_DATE, \
    MED_BOX, MED_CATEGORY, MED_NUM, \
    IMPORT_CSV, SEARCH_INIT, SEARCH_NAME, SEARCH_CATEGORY, \
    TAKE_NAME, TAKE_NUM, TAKE_DATE, TAKE_BOX = range(15)

# path for import-export files
download_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'downloads')
file_size_limit = 30*1024*2024


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to search in first aid kit without setting current one.")
        await update.message.reply_text(text="Чтобы произвести поиск в аптечке необходимо подключится к ней. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    reply_keyboard = [["Поиск по имени", "Поиск по категории лекартсва"]]
    await update.message.reply_text(
        f"Произвести поиск лекартсва по имени или по категории лекарства.",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Выбери что-то одно"
        ),
    )
    return SEARCH_INIT


async def list_med(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not aids.is_initialized():
        logger.error(
            f"Attempt to list in first aid kit without setting current one.")
        await update.message.reply_text(text="Чтобы произвести вывод лекарств в аптечке необходимо подключится к ней. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    meds = aids.get_all_meds()
    msg_meds = ""
    for m in meds:
        msg_meds += "\n" + mngr.Aid.get_med_msg(m)
    num_of_found = len(meds)
    logger.info(f"Listing all {num_of_found} meds")
    await update.message.reply_text(f"Твоя аптечка содержит {num_of_found} лекарств. {msg_meds}")


async def list_med_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not aids.is_initialized():
        logger.error(
            f"Attempt to list in first aid kit without setting current one.")
        await update.message.reply_text(text="Чтобы произвести вывод лекарств в аптечке необходимо подключится к ней. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    categories = aids.get_all_categories()
    msg_cat = ""
    for c in categories:
        msg_cat += "\n" + c
    num_of_found = len(categories)
    logger.info(f"Listing all {num_of_found} categories")
    await update.message.reply_text(f"Твоя аптечка содержит {num_of_found} категорий. {msg_cat}")


async def process_search_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    logger.info(
        f"Attempt to search med with category {category} in first aid kit.")
    meds = aids.get_meds_by_category(category)
    msg_meds = ""
    for m in meds:
        msg_meds += "\n" + mngr.Aid.get_med_msg(m)
    num_of_found = len(meds)
    logger.info(f"Were found {num_of_found} medicines: {msg_meds}")
    await update.message.reply_text(f"Было найдено {num_of_found} лекарств. {msg_meds}")
    if num_of_found:
        await update.message.reply_text(f"Чтобы взять лекарство из аптечки используй команду \n"
                                        f"/take_medicine <имя_лекарства>")
    await help_reply(update, context)
    return ConversationHandler.END


async def process_search_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    logger.info(f"Attempt to search med with name {name} in first aid kit.")
    meds = aids.get_meds_by_name(name)
    msg_meds = ""
    for m in meds:
        msg_meds += "\n" + mngr.Aid.get_med_msg(m)
    num_of_found = len(meds)
    logger.info(f"Were found {num_of_found} medicines: {msg_meds}")
    await update.message.reply_text(f"Было найдено {num_of_found} лекарств. {msg_meds}")
    if num_of_found:
        await update.message.reply_text(f"Чтобы взять лекарство из аптечки используй команду \n"
                                        f"/take_medicine {name}")
    await help_reply(update, context)
    return ConversationHandler.END


async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    search_by_name = "имени" in update.message.text.lower()
    if search_by_name:
        await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                       text=f"Введи имя категории.\n Пример: ОРВИ")
        return SEARCH_NAME
    else:
        await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                       text=f"Введи имя лекарства.\n Пример: пенталгин")
        await SEARCH_CATEGORY


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        ["Использовать существующую аптечку", "Создать новую аптечку"]]

    await update.message.reply_text(
        f"💊Я твой бот-аптечка. 💊 Я могу помочь тебе с управлением состоянием аптечки \n\n"
        "Хочешь использовать существующую аптечку или создать новую?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Выбери что-то одно"
        ),
    )

    return INIT_KIT


async def process_init_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    use_existing_one = "существующую" in update.message.text.lower()
    msg = ""
    if use_existing_one:
        existing_aids = aids.get_aids()
        if existing_aids is not None:
            msg = "Сейчас есть следующие аптечки:"
            for x in existing_aids:
                msg += "\n    " + x['name']
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                           text=f"Сейчас нету существующих аптечек. Создай новую")
    await context.bot.send_message(chat_id=update.effective_chat.id,  reply_markup=ReplyKeyboardRemove(),
                                   text=msg + f"\n\nВызови команду /aid_kit <имя_аптечки> для того чтобы подключится к своей аптечке.\n Пример:\n /aid_kit имя123")
    return ConversationHandler.END


async def help_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not aids.is_initialized():
        return

    msg = "⚙️Ты можешь управлять своей аптечкой, исопльзуя следующие команды:⚙️\n"\
        "/delete_aid_kit - удалить аптечку и всё ее содержимое\n"\
        "/search - поиск лекарства в аптечке\n"\
        "/take_med - взять лекарство из аптечки\n"\
        "/add_med - добавить лекарство в аптечку\n"\
        "/list_med - вывести все лекартсва из аптечки\n"\
        "/list_med_category - вывести все категории лекарств из аптечки\n"\
        "/import_csv - импортировать состояние аптечки из csv\n"\
        "/export_csv - экспортировать состояние в csv\n"
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Текущее количество лекарств в твооей аптечке <i><b>{html.escape(aids.get_cur_aid_name())}</b></i> : "
                                   f"{aids.get_number_of_meds()} \n\n" + msg, parse_mode=ParseMode.HTML)


async def choose_aid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    message = update.message.text
    aid_name = message.split()
    if len(aid_name) != 2:
        logger.error("Sent incorect arg to /aid_kit")
        await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                       text="❌ Некорректная команда. Используй /aid_kit <имя_аптечки>")
    aid_name = aid_name[1]
    aids.set_current_aid(aid_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                   text=f"Имя твоей аптечки <b>{html.escape(aid_name)}</b>", parse_mode=ParseMode.HTML)
    logger.info(f"Setting first aid kit {aid_name} as current one successfuly")

    await help_reply(update, context)


async def delete_kit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to delete first aid kit without setting current one.")
        await update.message.reply_text(text="Чтобы удалить аптечку тебе нужно сначала подключится к ней. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    count = aids.get_number_of_meds()
    kit_name = aids.get_cur_aid_name()

    reply_keyboard = [["Да", "Нет"]]

    await update.message.reply_text(
        f"Я собираюсь удалить аптечку {kit_name}, которая содержит {count} лекарств.\n\n Ты уверен?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Ты уверен?"
        ),
    )

    return AGREE


async def process_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    decision = update.message.text
    kit_name = aids.get_cur_aid_name()
    if decision.lower() == "да":
        aids.delete_cur_aid()
        logger.info("Received confirmation.")
        logger.info(f"Deletion of {kit_name} completed successfuly")
        await update.message.reply_text(
            text=f"✅ Аптечка {kit_name} успешно удалена.\nВызови комнаду /start чтобы начать новую сессию.",
            reply_markup=ReplyKeyboardRemove())
    else:
        logger.info(
            f"Confirmation was not received. Abort deletion of first aid kit")
        await update.message.reply_text(
            text=f"❌ Подтвтерждение процесса удаления не было получено. Удаление аптечки {kit_name} приостановлено",
            reply_markup=ReplyKeyboardRemove())
        await help_reply(update, context)

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the action conversation.", user.first_name)
    await update.message.reply_text(
        "Действие было отменено.", reply_markup=ReplyKeyboardRemove()
    )

    if aids.is_initialized():
        await help_reply(update, context)
    return ConversationHandler.END


async def add_med(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to add medicine without setting current first aid kit.")
        await update.message.reply_text(text="Чтобы добавить лекарство необходимо подключится к аптечке. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    user = update.message.from_user['id']
    context.user_data[user] = {'med': {}}
    await update.message.reply_text(
        f"Давай добавим новое лекарство. Введи название лекарства"
    )
    return MED_NAME


async def take_med(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to take medicine in first aid kit without setting current one.")
        await update.message.reply_text(text="Чтобы взять лекарство из аптечки необходимо подключится к ней. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    user = update.message.from_user['id']
    context.user_data[user] = {'take': {}}
    await update.message.reply_text(f"Введи имя лекарства, которое ты хочешь взять")
    return TAKE_NAME


async def take_med_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    try:
        context.user_data[user]['take']['expected_date'] = datetime.datetime.strptime(
            update.message.text, '%m/%Y')
    except Exception as e:
        logger.error(f"Incorrect format of date. Exception: {e}")
        await update.message.reply_text("❌ Некореектный формат даты. Пожалуйста предоставь дату в следующем формате: mm/yyyy")
        return TAKE_DATE

    has_such_date = False
    existed_dates = ""
    found_med = None
    for m in context.user_data[user]['take']['meds']:
        existed_dates += "\n" + m['valid_date'].strftime('%m/%Y')
        if m['valid_date'] == context.user_data[user]['take']['expected_date']:
            has_such_date = True
            found_med = m
            break

    if not has_such_date:
        logger.error(f"Found meds doesnot contain provided date.")
        await update.message.reply_text(f"❌ Найденные лекарства не соответсвуют введенному сроку годности {update.message.text}\n"
                                        f"Выберите даты одни из приведенных ниже:{existed_dates}")
        return TAKE_DATE

    if 'check_box' in context.user_data[user]['take']:
        await update.message.reply_text(f"Введи местоположение лекарства, которое ты хочешь взять")
        return TAKE_BOX

    del context.user_data[user]['take']['check_date']
    context.user_data[user]['take']['old_med'] = found_med
    await update.message.reply_text("Теперь введи количество лекарства")
    return TAKE_NUM


async def take_med_box(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    context.user_data[user]['take']['expected_box'] = update.message.text

    has_such_box = False
    has_such_date = 'expected_date' not in context.user_data[user]['take']
    existed_dates = ""
    existed_box = ""
    found_med = None
    for m in context.user_data[user]['take']['meds']:
        existed_box += "\n" + m['box']
        existed_dates += "\n" + m['valid_date'].strftime('%m/%Y')
        if m['box'] == context.user_data[user]['take']['expected_box']:
            has_such_box = True
            if 'expected_date' in context.user_data[user]['take'] \
                    and m['valid_date'] == context.user_data[user]['take']['expected_date']:
                has_such_date = True
                found_med = m
                break
    if found_med is None:
        logger.error(
            f"Were provided incorrect input. Meds has provided box: {has_such_box} and has providied date:{has_such_date}")
        if not has_such_box:
            await update.message.reply_text(f"❌ Найденные лекарства не соответсвуют введенному местоположению {update.message.text}\n"
                                            f"Выберите местоположение одно из приведенных ниже:{existed_box}")
            return TAKE_BOX
        if not has_such_date:
            date_msg = context.user_data[user]['take']['expected_date'].strftime('%m/%Y')
            await update.message.reply_text(f"❌ Найденные лекарства не соответсвуют введеной комбинации местоположения {update.message.text} и срока годности {date_msg}\n"
                                            f"Выберите даты одни из приведенных ниже:{existed_dates}")
                                            
            return TAKE_DATE
    del context.user_data[user]['take']['check_box']
    await update.message.reply_text("Теперь введи количество лекарства")
    return TAKE_NUM


async def process_take_med_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    meds = aids.get_meds_by_name(update.message.text)

    if meds is None:
        logger.error(
            f"Take medicine: medicine with name {update.message.text} were not found")
        await update.message.reply_text(f"❌ Ошибка: Лекарство с именем {update.message.text} не было найдено")
        await help_reply(update, context)
        return ConversationHandler.END
    if len(meds) == 1:
        logger.info(
            f"Take medicine: were found only one med for name {update.message.text}")
        context.user_data[user]['take']['old_med'] = meds[0]
        await update.message.reply_text("Теперь введи количество лекарства")
        return TAKE_NUM

    logger.info(
        f"Take medicine: were found only few meds for name {update.message.text}")
    msg_meds = ""
    meds_date = set()
    meds_box = set()
    for m in meds:
        msg_meds += "\n" + mngr.Aid.get_med_msg(m)
        meds_date.add(m['valid_date'])
        meds_box.add(m['box'])
    context.user_data[user]['take']['meds'] = meds
    msg = f"ℹ️ Было найдено несколько лекарств с именем {update.message.text}. \n"
    if len(meds_date) > 1:
        context.user_data[user]['take']['check_date'] = True
        msg += "⏲️ Лекарства имеют одинаковое название, но разный срок годности.\n"

    if len(meds_box) > 1:
        context.user_data[user]['take']['check_box'] = True
        msg += "💼 Лекарства имеют одинаковое название, но разное местоположение.\n"

    msg += f"Найденные лекарства: {msg_meds}\n"
    if 'check_date' in context.user_data[user]['take']:
        msg += f"Пожалуйста введи срок годности лекарства {update.message.text}."
        await update.message.reply_text(text=msg)
        return TAKE_DATE

    if 'check_box' in context.user_data[user]['take']:
        msg += f"Пожалуйста введи местоположение лекарства {update.message.text}."
        await update.message.reply_text(text=msg)
        return TAKE_BOX
    msg += "❌ Ошибка: Необработанное различие между лекарствами. Обратитесь к разработчику.\n"
    await update.message.reply_text(text=msg)
    return ConversationHandler.END


async def process_take_med_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    try:
        context.user_data[user]['take']['new_quantity'] = float(
            update.message.text)
    except:
        logger.error(f"Incorrect format of quantity")
        await update.message.reply_text("❌ Некорректный формат количества. Пожалуйста предоставь количество лекарства как число.")
        return MED_NUM

    med_desc = context.user_data[user]['take']
    logger.info(
        f"Attempt to reduce medicine {med_desc['old_med']['id']} on quantity {med_desc['new_quantity']}")
    aids.reduce_med(med_desc['quantity'], med_desc['old_med'])

    new_med = aids.get_med_by_id(med_desc['old_med']['id'])
    msg = "✅ Изменение количества лекарства успешно произведено.\n"
    if new_med is None:
        msg += "Лекарство было удалено из аптечки, так как было взято полное количество лекарства"
    else:
        msg += "Текущее состояние лекарства:" + mngr.Aid.get_med_msg(new_med)
    await update.message.reply_text(msg)
    return ConversationHandler.END


async def process_med_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    context.user_data[user]['med']['name'] = update.message.text
    await update.message.reply_text("Теперь введи количество лекарства")
    return MED_NUM


async def process_med_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    try:
        context.user_data[user]['med']['valid_date'] = datetime.datetime.strptime(
            update.message.text, '%m/%Y')
    except Exception as e:
        logger.error(f"Incorrect format of date. Exception: {e}")
        await update.message.reply_text("❌ Некореектный формат даты. Пожалуйста предоставь дату в следующем формате: mm/yyyy")
        return MED_DATE
    cur_med = context.user_data[user]['med']
    id = aids.add_med(name=cur_med['name'], quantity=cur_med['quantity'],
                      category=cur_med['category'], box=cur_med['box'], valid_date=cur_med['valid_date'])
    logger.info(f"Created medicine {cur_med} with id {id}")
    await update.message.reply_text("✅ Лекарство добавлено успешно:\n" + mngr.Aid.get_med_msg(cur_med))
    await help_reply(update, context)
    return ConversationHandler.END


async def process_med_box(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    context.user_data[user]['med']['box'] = update.message.text
    await update.message.reply_text("Теперь введи от чего данное лекарство.")
    return MED_CATEGORY


async def process_med_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    context.user_data[user]['med']['category'] = update.message.text
    await update.message.reply_text("Теперь введи срок годности лекарства. Формат даты: mm/yyyy")
    return MED_DATE


async def process_med_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user['id']
    try:
        context.user_data[user]['med']['quantity'] = float(update.message.text)
    except:
        logger.error(f"Incorrect format of quantity")
        await update.message.reply_text("❌ Некорректный формат количества. Пожалуйста предоставь количество лекарства как число.")
        return MED_NUM
    await update.message.reply_text("Теперь введи местоположение лекарства")
    return MED_BOX


async def import_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to import medicines without setting current first aid kit.")
        await update.message.reply_text(text="Для того чтобы импортировать лекарства из csv файла, необходимо подключится к аптечке. Запусти команду /start чтобы это сделать")
        return ConversationHandler.END
    await update.message.reply_text(
        f"Давай добавим лекарства из твоего файла. Добавь как приложение файл csv, из которого надо произвести импорт"
        "Ожидается что формат строки в  CSV файле будет следующим:\n"
        "Название,Срок годности,От чего,Местоположение,Количество\n"
        "Формат даты: mm/yyyy"
        "Размер файла максимум 20mb"
    )

    if not os.path.exists(download_path):
        os.mkdir(download_path)
    return IMPORT_CSV


async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to export medicines without setting current first aid kit.")
        await update.message.reply_text(text="Чтобы экспортировать лекарства из аптечки необходимо сначала подключится к аптечке. Чтобы это сделать запусти команду /start")
        return

    if not os.path.exists(download_path):
        os.mkdir(download_path)

    user = update.message.from_user
    file_path = os.path.join(download_path, f"{user.id}.csv")
    if os.path.exists(file_path):
        os.remove(file_path)

    aids.export_aid_to_csv(file_path)
    await context.bot.send_document(chat_id=update.effective_chat.id, document=file_path)
    await help_reply(update, context)


async def process_import(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.message.from_user
    file_path = os.path.join(download_path, f"{user.id}.csv")

    if update.message.document.file_size >= file_size_limit:
        await update.message.reply_text(f"❌ Ошибка: файл слишком большой. Максимальный размер 20мб.")
        logger.error(
            f'Attempt to load file too big from user {user.first_name}. Document description: {update.message.document}')
        return ConversationHandler.END
    doc_file = await update.message.document.get_file()
    await doc_file.download_to_drive(file_path)
    logger.info(
        f"Loaded file {update.message.document} from user {user.first_name} successfuly")
    imp_meds = aids.import_aid_from_csv(file_path)
    os.remove(file_path)

    await update.message.reply_text(f"✅ Было успешно загружено {len(imp_meds)} лекарств")

    await help_reply(update, context)
    return ConversationHandler.END


def init_handlers(app):
    init_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INIT_KIT: [MessageHandler(filters.Regex(
                "^(Использовать существующую аптечку|Создать новую аптечку)$"), process_init_aid)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(CommandHandler("aid_kit", choose_aid))
    app.add_handler(init_aid_handler)

    delete_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_aid_kit", delete_kit)],
        states={
            AGREE: [MessageHandler(filters.Regex(
                "^(Да|Нет|да|нет)$"), process_delete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(delete_aid_handler)

    add_med_handler = ConversationHandler(
        entry_points=[CommandHandler("add_med", add_med)],
        states={
            MED_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_med_name)],
            MED_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_med_date)],
            MED_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_med_category)],
            MED_BOX: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_med_box)],
            MED_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_med_quantity)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(add_med_handler)

    import_csv_handler = ConversationHandler(
        entry_points=[CommandHandler("import_csv", import_entry)],
        states={IMPORT_CSV: [MessageHandler(
            filters.Document.FileExtension("csv"), process_import)]},
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(import_csv_handler)
    app.add_handler(CommandHandler("export_csv", export_csv))
    app.add_handler(CommandHandler("list_med", list_med))
    app.add_handler(CommandHandler("list_med_category", list_med_category))

    search_med_handler = ConversationHandler(
        entry_points=[CommandHandler("search", search)],
        states={
            SEARCH_INIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)],
            SEARCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_by_name)],
            SEARCH_CATEGORY: [MessageHandler(
                filters.TEXT & ~filters.COMMAND, process_search_by_category)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(search_med_handler)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:",
                 exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    # You might need to add some logic to deal with messages longer than the 4096 character limit.
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    message = (
        f"An exception was raised while handling an update\n"
        f"<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        "</pre>\n\n"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await context.bot.send_message(chat_id=update.effective_chat.id, text=message, parse_mode=ParseMode.HTML)


if __name__ == '__main__':
    # TODO: move token to secure place
    app = ApplicationBuilder().token(
        '5898027021:AAG-et5fU_5nONWeaFjkbdbtDSTSqi0G_50').build()
    init_handlers(app)
    app.add_error_handler(error_handler)
    app.run_polling()
