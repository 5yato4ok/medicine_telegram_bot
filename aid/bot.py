import sys
from pathlib import Path
import logging
from telegram import *
from telegram.ext import *
import html
import json
import logging
from telegram.constants import ParseMode
import traceback
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
AGREE, INIT_KIT = range(2)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    reply_keyboard = [["Use existing one", "Create new one"]]

    await update.message.reply_text(
        f"💊I'm a first aid kit bot. 💊 I can help you to manage your first aid kit content. \n\n Want to use existing first aid kit or create new one?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Pick one"
        ),
    )

    return INIT_KIT


async def process_init_aid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    use_existing_one = "use existing one" in update.message.text.lower()
    msg = ""
    if use_existing_one:
        existing_aids = aids.get_aids()
        if existing_aids is not None:
            msg = "There are following first aid kits:"
            for x in existing_aids:
                msg += "\n    " + x['name']
        else:
            await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                           text=f"There is no existing first aid kits. Please create new one")
    await context.bot.send_message(chat_id=update.effective_chat.id,  reply_markup=ReplyKeyboardRemove(),
                                   text=msg + f"\n\nCall command /aid_kit <your_kit_name> to start using your first aid kit.\n Example:\n /aid_kit ivanov")
    return ConversationHandler.END


async def help_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not aids.is_initialized():
        return

    msg = "⚙️You can control your first aid kit by sending following commands:⚙️\n"\
        "/delete_kit - delete your first aid kit and it's content completely\n"\
        "/search - search the medicine in your aid\n"\
        "/add_med - add medicine to your first aid kit\n"\
        "/import - import csv with content of your first aid kit\n"\
        "/export - export the content of your current first aid kit\n"
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Total number of medicines in your first aid kit <b>{html.escape(aids.get_cur_aid_name())}</b> : "
                                   f"{aids.get_number_of_meds()} \n\n" + msg, parse_mode=ParseMode.HTML)


async def choose_aid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message is None:
        return
    message = update.message.text
    aid_name = message.split()
    if len(aid_name) != 2:
        logger.error("Sent incorect arg to /aid_kit")
        await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                       text="❌ Incorrect command. Run /aid_kit <aid_name>")
    aid_name = aid_name[1]
    aids.set_current_aid(aid_name)
    await context.bot.send_message(chat_id=update.effective_chat.id, reply_markup=ReplyKeyboardRemove(),
                                   text=f"Your first aid kit name is <b>{html.escape(aid_name)}</b>", parse_mode=ParseMode.HTML)
    logger.info(f"Setting first aid kit {aid_name} as current one successfuly")

    await help_reply(update, context)


async def delete_kit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not aids.is_initialized():
        context.user_data['error_del'] = True
        logger.error(
            f"Attempt to delete first aid kit without setting current one.")
        await update.message.reply_text(text="To delete current first aid kit you need to set one first. Run command /start to do this")
        return AGREE
    count = aids.get_number_of_meds()
    kit_name = aids.get_cur_aid_name()

    reply_keyboard = [["Yes", "No"]]

    await update.message.reply_text(
        f"I am going to delete first aid kit {kit_name}, which contains {count} medicine.\n\n Are you sure?",
        reply_markup=ReplyKeyboardMarkup(
            reply_keyboard, one_time_keyboard=True, input_field_placeholder="Are you sure?"
        ),
    )

    return AGREE


async def process_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if 'error_del' in context.user_data:
        del context.user_data['error_del']
        return ConversationHandler.END
    decision = update.message.text
    kit_name = aids.get_cur_aid_name()
    if decision.lower() == "yes":
        aids.delete_cur_aid()
        logger.info("Received confirmation.")
        logger.info(f"Deletion of {kit_name} completed successfuly")
        await update.message.reply_text(
            text=f"✅ Deleted first aid kit {kit_name} successfuly.\nCall /start to initiate new session.",
            reply_markup=ReplyKeyboardRemove())
    else:
        logger.info(
            f"Confirmation was not received. Abort deletion of first aid kit")
        await update.message.reply_text(
            text=f"❌ Confirmation was not received. Abort deletion of {kit_name}",
            reply_markup=ReplyKeyboardRemove())
        await help_reply(update, context)

    return ConversationHandler.END


async def photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Stores the photo and asks for a location."""
    user = update.message.from_user
    photo_file = await update.message.photo[-1].get_file()
    await photo_file.download_to_drive("user_photo.jpg")
    logger.info("Photo of %s: %s", user.first_name, "user_photo.jpg")
    await update.message.reply_text(
        "Gorgeous! Now, send me your location please, or send /skip if you don't want to."
    )

    return ConversationHandler.END


async def skip_photo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Skips the photo and asks for a location."""
    user = update.message.from_user
    logger.info("User %s did not send a photo.", user.first_name)
    await update.message.reply_text(
        "I bet you look great! Now, send me your location please, or send /skip."
    )

    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancels and ends the conversation."""
    user = update.message.from_user
    logger.info("User %s canceled the conversation.", user.first_name)
    await update.message.reply_text(
        "Action was canceled.", reply_markup=ReplyKeyboardRemove()
    )

    return ConversationHandler.END


def init_handlers(app):
    init_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            INIT_KIT: [MessageHandler(filters.Regex(
                "^(Use existing one|Create new one)$"), process_init_aid)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    choose_aid_handler = CommandHandler('aid_kit', choose_aid)
    app.add_handler(choose_aid_handler)
    app.add_handler(init_aid_handler)

    delete_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_kit", delete_kit)],
        states={
            AGREE: [MessageHandler(filters.Regex(
                "^(Yes|No|yes|no)$"), process_delete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(delete_aid_handler)


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
