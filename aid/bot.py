import sys
import os
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
aids = mngr.Aid()

# signals
AGREE, INIT_KIT, MED_NAME, MED_DATE, \
    MED_BOX, MED_CATEGORY, MED_NUM, \
    IMPORT_CSV, SEARCH_INIT, SEARCH_NAME, SEARCH_CATEGORY, \
    TAKE_NAME, TAKE_NUM, TAKE_FEW = range(14)

# path for import-export files
download_path = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'downloads')
file_size_limit = 30 * 1024 * 2024
MSG_MAX_SIZE = 4000
MAX_LINE_BUTTON_LENGTH = 3
DEVELOPER_CHAT_ID = 185374927


def split_by_size(msg, n):
    chunks = [msg[i:i + n] for i in range(0, len(msg), n)]
    return chunks


def get_msg(msg: str):
    if len(msg) < MSG_MAX_SIZE:
        return [msg]
    else:
        return split_by_size(msg, MSG_MAX_SIZE - 500)


async def send_message(msg: str, cb, **kwargs):
    parts = get_msg(msg)
    for p in parts:
        await cb(text=p, **kwargs)


def get_user_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    return context.user_data[chat_id]


async def is_not_initialized(operation_ru: str, operation_en: str, update: Update) -> bool:
    if not aids.is_initialized():
        logger.error(
            f"Attempt to process operation '{operation_en}' in first aid kit without setting current one.")
        await update.message.reply_text(
            text=f"Чтобы произвести операцию '{operation_ru}' необходимо подключится к аптечке. Запусти команду /start чтобы это сделать")
        return True
    return False


def clear_up(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update is None:
        return
    if update.effective_chat is None:
        return
    chat_id = update.effective_chat.id
    if chat_id not in context.user_data:
        return
    if 'med' in context.user_data[chat_id]:
        del context.user_data[chat_id]['med']
    if 'take' in context.user_data[chat_id]:
        del context.user_data[chat_id]['take']


async def search(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("поиск", "search", update):
        return ConversationHandler.END

    reply_keyboard = [
        [
            InlineKeyboardButton("Поиск по имени", callback_data="search_name"),
            InlineKeyboardButton("Поиск по категории лекарcтва", callback_data="search_cat")
        ]
    ]

    await update.message.reply_text(f"Произвести поиск лекарcтва по имени или по категории лекарства.",
                                    reply_markup=InlineKeyboardMarkup(reply_keyboard))
    return SEARCH_INIT


async def list_med(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_not_initialized("вывод лекарств", "list med", update):
        return ConversationHandler.END
    meds = aids.get_all_meds()
    msg = ""
    if meds is None:
        msg = "Твоя аптечка не содержит лекарств. Используй команду /add_med для того чтобы добавить новое лекарство"
    else:
        msg_meds = ""
        for m in meds:
            msg_meds += "\n" + mngr.Aid.get_med_msg(m)
        num_of_found = len(meds)
        logger.info(f"Listing all {num_of_found} meds")
        msg = f"Твоя аптечка содержит {num_of_found} лекарств. {msg_meds}"
    await send_message(msg, update.message.reply_text)
    await help_reply(update, context)
    return ConversationHandler.END


async def list_med_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if await is_not_initialized("вывод категорий лекарств", "list med category", update):
        return ConversationHandler.END
    categories = aids.get_all_categories()
    if categories is None:
        msg = "Твоя аптечка не содержит лекарств.\n Используй команду /add_med для того чтобы добавить новое лекарство"
    else:
        msg_cat = ""
        for c in categories:
            msg_cat += "\n" + c
        num_of_found = len(categories)
        logger.info(f"Listing all {num_of_found} categories")
        msg = f"Твоя аптечка содержит {num_of_found} категорий. {msg_cat}"
    await send_message(msg, update.message.reply_text)
    await help_reply(update, context)
    return ConversationHandler.END


async def process_search_by_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    category = update.message.text
    logger.info(
        f"Attempt to search med with category {category} in first aid kit.")
    meds = aids.get_meds_by_category(category)

    if meds is not None:
        msg_meds = ""
        for m in meds:
            msg_meds += "\n" + mngr.Aid.get_med_msg(m)
        num_of_found = len(meds)
        logger.info(f"Were found {num_of_found} medicines.")
        msg = f"Было найдено {num_of_found} лекарств. {msg_meds}\n" \
              f"Чтобы взять лекарство из аптечки используй команду /take_med"
    else:
        msg = f"Категория {category} не была найдена"
    await send_message(msg, update.message.reply_text)
    await help_reply(update, context)
    return ConversationHandler.END


async def process_search_by_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    name = update.message.text
    logger.info(f"Attempt to search med with name {name} in first aid kit.")
    meds = aids.get_meds_by_name(name)
    if meds is None:
        meds = aids.get_similar_meds_by_name(name)

    if meds is not None:
        msg_meds = ""
        for m in meds:
            msg_meds += "\n" + mngr.Aid.get_med_msg(m)
        num_of_found = len(meds)
        logger.info(f"Were found {num_of_found} medicines.")
        msg = f"Было найдено {num_of_found} лекарств. {msg_meds}\n" \
              f"Чтобы взять лекарство из аптечки используй команду /take_med"
    else:
        msg = f"Лекарство {name} не было найдено."

    await send_message(msg, update.message.reply_text)
    await help_reply(update, context)
    return ConversationHandler.END


async def dialog_search_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await send_message(f"Введи имя лекарства.\n Пример: пенталгин", update.callback_query.message.reply_text)
    return SEARCH_NAME


async def dialog_search_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await send_message(f"Введи имя категории.\n Пример: ОРВИ", update.callback_query.message.reply_text)
    return SEARCH_CATEGORY


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [
        [
            InlineKeyboardButton("Использовать существующую аптечку", callback_data="old"),
            InlineKeyboardButton("Создать новую аптечку", callback_data="new")
        ]
    ]

    await send_message(
        f"💊Я твой бот-аптечка. 💊 Я могу помочь тебе с управлением состоянием аптечки \n\n"
        "Хочешь использовать существующую аптечку или создать новую?", update.message.reply_text,
        reply_markup=InlineKeyboardMarkup(reply_keyboard)
    )

    return INIT_KIT


AID_CREATE_START, AID_CHOOSE_START, AID_CREATE, AID_CHOOSE = range(4)


async def connect_to_aid(update: Update, context: ContextTypes.DEFAULT_TYPE, aid_name) -> int:
    chat_id = update.effective_chat.id
    aids.connect_to_aid(aid_name, str(chat_id))
    await send_message(f"Имя твоей аптечки <b>{html.escape(aid_name)}</b>", context.bot.send_message,
                       parse_mode=ParseMode.HTML, chat_id=chat_id, reply_markup=ReplyKeyboardRemove())
    logger.info(f"Setting first aid kit {aid_name} as current one successfuly")

    await help_reply(update, context)
    return ConversationHandler.END


async def init_create_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    await send_message("Введи имя новой аптечки", update.callback_query.message.reply_text)
    return AID_CREATE


async def process_create_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    aid_name = update.message.text
    await connect_to_aid(update, context, aid_name)
    return ConversationHandler.END


async def process_choose_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    aid_name = query.data
    aid_name = aid_name.replace('aid_name:', '')
    await connect_to_aid(update, context, aid_name)
    return ConversationHandler.END


async def init_choose_existing_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.callback_query.answer()
    existing_aids = aids.get_aids(owner=str(update.effective_chat.id))
    if existing_aids is not None:
        res_aids_name = []
        user_aids_line = []
        for x in existing_aids:
            user_aids_line.append(InlineKeyboardButton(text=x['name'], callback_data="aid_name:" + x['name']))
            if len(user_aids_line) >= MAX_LINE_BUTTON_LENGTH:
                res_aids_name.append(user_aids_line)
                user_aids_line = []
        if len(user_aids_line) != 0:
            res_aids_name.append(user_aids_line)

        await send_message("Выбери одну из существующих аптечек", update.callback_query.message.reply_text,
                           reply_markup=InlineKeyboardMarkup(res_aids_name))

        return AID_CHOOSE
    else:
        await send_message("Сейчас нету существующих аптечек. Введи имя новой аптечки",
                           update.callback_query.message.reply_text)
        return AID_CREATE


async def help_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not aids.is_initialized():
        return

    msg = "⚙️Ты можешь управлять своей аптечкой, используя следующие команды:⚙️\n" \
          "/delete_aid_kit - удалить аптечку и всё ее содержимое\n" \
          "/search - поиск лекарства в аптечке\n" \
          "/take_med - взять лекарство из аптечки\n" \
          "/add_med - добавить лекарство в аптечку\n" \
          "/list_med - вывести все лекартсва из аптечки\n" \
          "/list_med_category - вывести все категории лекарств из аптечки\n" \
          "/import_csv - импортировать состояние аптечки из csv\n" \
          "/export_csv - экспортировать состояние в csv\n" \
          "/cancel - отменить текущую команду"
    await send_message(
        f"Текущее количество лекарств в твоей аптечке <i><b>{html.escape(aids.get_cur_aid_name())}</b></i> : "
        f"{aids.get_number_of_meds()} \n\n" + msg,
        context.bot.send_message, chat_id=update.effective_chat.id, parse_mode=ParseMode.HTML)


async def delete_kit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("удаление аптечки", "delete aid kit", update) or update.message is None:
        return ConversationHandler.END
    count = aids.get_number_of_meds()
    kit_name = aids.get_cur_aid_name()

    reply_keyboard = [
        [
            InlineKeyboardButton("Да", callback_data="delete_yes"),
            InlineKeyboardButton("Нет", callback_data="delete_no")
        ]
    ]

    await send_message(f"Я собираюсь удалить аптечку {kit_name}, которая содержит {count} лекарств.\n\n Ты уверен?",
                       update.message.reply_text, reply_markup=InlineKeyboardMarkup(reply_keyboard))

    return AGREE


async def process_delete_yes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kit_name = aids.get_cur_aid_name()
    aids.delete_cur_aid()
    logger.info("Received confirmation.")
    logger.info(f"Deletion of {kit_name} completed successfuly")
    await send_message(f"✅ Аптечка {kit_name} успешно удалена.\nВызови комнаду /start чтобы начать новую сессию.",
                       update.callback_query.message.reply_text)
    return ConversationHandler.END


async def process_delete_no(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    kit_name = aids.get_cur_aid_name()
    logger.info(f"Confirmation was not received. Abort deletion of first aid kit")
    await send_message(
        f"❌ Подтвтерждение процесса удаления не было получено. Удаление аптечки {kit_name} приостановлено",
        update.callback_query.message.reply_text)
    await help_reply(update, context)
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the action conversation.", user.first_name)
    await send_message("Действие было отменено.", update.message.reply_text, reply_markup=ReplyKeyboardRemove())
    clear_up(update, context)
    if aids.is_initialized():
        await help_reply(update, context)
    return ConversationHandler.END


async def add_med(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("добавление лекарств", "add med", update):
        return ConversationHandler.END
    chat_id = update.effective_chat.id
    context.user_data[chat_id] = {'med': {}}
    await send_message(f"Давай добавим новое лекарство. Введи название лекарства", update.message.reply_text)
    return MED_NAME


async def take_med(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("взять лекарство", "take med", update):
        return ConversationHandler.END
    chat_id = update.effective_chat.id
    context.user_data[chat_id] = {'take': {}}
    await send_message("Введи имя лекарства, которое ты хочешь взять", update.message.reply_text)
    return TAKE_NAME


async def process_take_med_few(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    med_id = None
    med_spl = query.data.split(':')
    if len(med_spl):
        med_id = med_spl[1]
    if med_id is None:
        logger.error("Unexpected input. Abort")
        await send_message("Некорректные входные данные. Операция отменена", update.callback_query.message.reply_text)
        clear_up(update, context)
        return ConversationHandler.END

    get_user_data(update, context)['take']['old_med'] = aids.get_med_by_id(med_id)
    await send_message("Теперь введи количество лекарства", update.callback_query.message.reply_text)
    return TAKE_NUM


async def process_take_med_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    meds = aids.get_meds_by_name(update.message.text)

    if meds is None:
        logger.error(
            f"Take medicine: medicine with name {update.message.text} were not found")
        await send_message(f"❌ Ошибка: Лекарство с именем {update.message.text} не было найдено",
                           update.message.reply_text)
        clear_up(update, context)
        await help_reply(update, context)
        return ConversationHandler.END
    if len(meds) == 1:
        logger.info(
            f"Take medicine: were found only one med for name {update.message.text}")
        get_user_data(update, context)['take']['old_med'] = meds[0]
        await send_message("Теперь введи количество лекарства", update.message.reply_text)
        return TAKE_NUM

    logger.info(
        f"Take medicine: were found few meds for name {update.message.text}")
    full_choices = []
    choices_line = []
    for m in meds:
        choices_line.append(InlineKeyboardButton(mngr.Aid.get_med_msg(m), callback_data=f"take_few:{m['id']}"))
        if len(choices_line) >= MAX_LINE_BUTTON_LENGTH:
            full_choices.append(choices_line)
            choices_line = []
    if len(choices_line):
        full_choices.append(choices_line)

    await send_message(f"ℹ️ Было найдено несколько лекарств с именем {update.message.text}. \n Выбери одно из них",
                       update.message.reply_text, reply_markup=InlineKeyboardMarkup(full_choices))
    return TAKE_FEW


async def process_take_med_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    med_desc = get_user_data(update, context)['take']
    try:
        med_desc['new_quantity'] = float(update.message.text)
    except:
        logger.error(f"Incorrect format of quantity")
        await send_message("❌ Некорректный формат количества. Пожалуйста предоставь количество лекарства как число.",
                           update.message.reply_text)
        return MED_NUM

    old_med = med_desc['old_med']
    msg = ""
    if old_med is not None:
        logger.info(
            f"Attempt to reduce medicine {old_med['id']} on quantity {med_desc['new_quantity']}")
        aids.reduce_med(med_desc['new_quantity'], old_med)

        new_med = aids.get_med_by_id(old_med['id'])
        msg = "✅ Изменение количества лекарства успешно произведено.\n"
        if new_med is None:
            msg += "Лекарство было удалено из аптечки, так как было взято полное количество лекарства"
        else:
            msg += "Текущее состояние лекарства:" + \
                   mngr.Aid.get_med_msg(new_med)
    else:
        logger.error('Incorrect medicine were found')
        msg = "❌ Некорректные входные данные. Операция отменена"
    await send_message(msg, update.message.reply_text)
    clear_up(update, context)
    await help_reply(update, context)
    return ConversationHandler.END


async def process_med_name(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_user_data(update, context)['med']['name'] = update.message.text
    await send_message("Теперь введи количество лекарства", update.message.reply_text)
    return MED_NUM


async def process_med_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        get_user_data(update, context)['med']['valid'] = datetime.datetime.strptime(
            update.message.text, '%m/%Y')
    except Exception as e:
        logger.error(f"Incorrect format of date. Exception: {e}")
        await send_message("❌ Некорректный формат даты. Пожалуйста предоставь дату в следующем формате: mm/yyyy",
                           update.message.reply_text)
        return MED_DATE

    cur_med = get_user_data(update, context)['med']
    id = aids.add_med(name=cur_med['name'], quantity=cur_med['quantity'],
                      category=cur_med['category'], box=cur_med['box'], valid_date=cur_med['valid'])
    logger.info(f"Created medicine {cur_med} with id {id}")
    await send_message("✅ Лекарство добавлено успешно:\n" + mngr.Aid.get_med_msg(aids.get_med_by_id(id)),
                       update.message.reply_text)

    await help_reply(update, context)
    clear_up(update, context)
    return ConversationHandler.END


async def process_med_box(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_user_data(update, context)['med']['box'] = update.message.text
    await send_message("Теперь введи от чего данное лекарство.", update.message.reply_text)
    return MED_CATEGORY


async def process_med_category(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    get_user_data(update, context)['med']['category'] = update.message.text
    await send_message("Теперь введи срок годности лекарства. Формат даты: mm/yyyy", update.message.reply_text)
    return MED_DATE


async def process_med_quantity(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        get_user_data(update, context)[
            'med']['quantity'] = float(update.message.text)
    except:
        logger.error(f"Incorrect format of quantity")
        await send_message("❌ Некорректный формат количества. Пожалуйста предоставь количество лекарства как число.",
                           update.message.reply_text)
        return MED_NUM
    await update.message.reply_text("Теперь введи местоположение лекарства")
    return MED_BOX


async def import_entry(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("импорт лекарств из csv", "import meds", update):
        return ConversationHandler.END
    await send_message(
        f"Давай добавим лекарства из твоего файла. Добавь как приложение файл csv к сообщению, из которого надо произвести импорт\n"
        "Ожидается что формат строки в  CSV файле будет следующим:\n"
        "Название,Срок годности,От чего,Местоположение,Количество\n"
        "Формат даты: mm/yyyy\n"
        "Размер файла максимум 20mb\n", update.message.reply_text)

    if not os.path.exists(download_path):
        os.mkdir(download_path)
    return IMPORT_CSV


async def export_csv(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if await is_not_initialized("экспорт лекарств из csv", "export meds", update):
        return ConversationHandler.END

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
        await send_message(f"❌ Ошибка: файл слишком большой. Максимальный размер 20мб.", update.message.reply_text)
        logger.error(
            f'Attempt to load file too big from user {user.first_name}. Document description: {update.message.document}')
        return ConversationHandler.END
    doc_file = await update.message.document.get_file()
    await doc_file.download_to_drive(file_path)
    logger.info(
        f"Loaded file {update.message.document} from user {user.first_name} successfuly")
    imp_meds = aids.import_aid_from_csv(file_path)
    os.remove(file_path)

    await send_message(f"✅ Было успешно загружено {len(imp_meds)} лекарств", update.message.reply_text)

    await help_reply(update, context)
    return ConversationHandler.END


def init_handlers(app):
    init_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INIT_KIT: [
                CallbackQueryHandler(init_create_aid, pattern="^new$"),
                CallbackQueryHandler(init_choose_existing_aid, pattern="^old$")
            ],
            AID_CHOOSE: [CallbackQueryHandler(process_choose_aid, pattern="^aid_name:.*")],
            AID_CREATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_create_aid)]
        },
        fallbacks=[CommandHandler("start", start)]
    )
    app.add_handler(init_aid_handler)

    delete_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_aid_kit", delete_kit)],
        states={
            AGREE: [CallbackQueryHandler(process_delete_yes, pattern="^delete_yes$"),
                    CallbackQueryHandler(process_delete_no, pattern="^delete_no$")]
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
            SEARCH_INIT: [CallbackQueryHandler(dialog_search_name, pattern="^search_name$"),
                          CallbackQueryHandler(dialog_search_category, pattern="^search_cat$")],
            SEARCH_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_by_name)],
            SEARCH_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search_by_category)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(search_med_handler)

    take_med_handler = ConversationHandler(
        entry_points=[CommandHandler("take_med", take_med)],
        states={
            TAKE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_take_med_name)],
            TAKE_NUM: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_take_med_quantity)],
            TAKE_FEW: [CallbackQueryHandler(process_take_med_few, pattern="^take_few:.*")]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    app.add_handler(take_med_handler)


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.error(msg="Exception while handling an update:", exc_info=context.error)

    # clearing up the user data
    clear_up(update, context)

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
        f"update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}"
        f"<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n"
        f"<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n"
        f"<pre>{html.escape(tb_string)}</pre>"
    )

    # Finally, send the message
    await send_message(message, context.bot.send_message, chat_id=DEVELOPER_CHAT_ID, parse_mode=ParseMode.HTML)
    await send_message("Sorry, error occurred, while trying to process command.", context.bot.send_message,
                       chat_id=update.effective_chat.id)
    await help_reply(update, context)


if __name__ == '__main__':
    # TODO: move token to secure place
    real =  os.environ["MED_BOT_TOKEN"]
    test = os.environ["MED_BOT_TEST_TOKEN"]
    app = ApplicationBuilder().token(test).build()
    init_handlers(app)
    app.add_error_handler(error_handler)
    app.run_polling()
