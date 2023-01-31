import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

import logging
from telegram import *
from telegram.ext import *
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


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a first aid kit bot. I can help you to manage your first aid kit content.\n\n"
                                   "To connect to your personal first aid kit use command:\n"
                                   "/aid <aid_name>\n"
                                   "You can control your first aid kit by sending following commands:\n"
                                   "/search - search the medicine in your aid\n"
                                   "/delete_kit - delete your first aid kit and it's content completely\n"
                                   "/import - import csv with content of your first aid kit\n"
                                   "/export - export the content of your current first aid kit\n"
                                   )


async def choose_aid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    #create new one or use existing one
    message = update.message.text
    aid_name = message.split()
    if len(aid_name) != 2:
        logger.error("Sent incorect arg to /aid")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                       text="Incorrect command run /aid <aid_name>")
    aid_name = aid_name[1]
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Your aid name is {aid_name}")
    count = aids.set_current_aid(aid_name)
    logger.info(f"Setting aid {aid_name} as current one successfuly")
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=f"Total number of meds in aid {aid_name}:{count}")

AGREE = range(9)

async def delete_kit(update: Update, context: ContextTypes.DEFAULT_TYPE)->int:
    if aids.get_cur_aid_name() is None:
        logger.error(f"Attempt to delete first aid kit without setting current one.")
        await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="To delete current first aid kit you need to set one first. Run command /aid <aid_name> to do this")
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



GENDER, PHOTO, LOCATION, BIO = range(4)


async def process_delete(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    decision = update.message.text
    if decision.lower() == "yes":
        aids.delete_cur_aid()
        logger.info("Received confirmation.")
        kit_name = aids.get_cur_aid_name()
        logger.info(f"Deletion of {kit_name} completed successfuly")
        await update.message.reply_text(
                                    text=f"Deleted first aid kit {kit_name} successfuly",
                                    reply_markup=ReplyKeyboardRemove())
    else:
        logger.info(f"Confirmation was not received. Abort deletion of first aid kit")
        await update.message.reply_text(
                                    text=f"Confirmation was not received. Abort deletion of {kit_name}", 
                                    reply_markup=ReplyKeyboardRemove())

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
    start_handler = CommandHandler('start', start)
    choose_aid_handler = CommandHandler('aid', choose_aid)
    app.add_handler(start_handler)
    app.add_handler(choose_aid_handler)

    delete_aid_handler = ConversationHandler(
        entry_points=[CommandHandler("delete_kit", delete_kit)],
        states={
            AGREE: [MessageHandler(filters.Regex("^(Yes|No|yes|no)$"), process_delete)]
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    app.add_handler(delete_aid_handler)

if __name__ == '__main__':
    # TODO: move token to secure place
    app = ApplicationBuilder().token(
        '5898027021:AAG-et5fU_5nONWeaFjkbdbtDSTSqi0G_50').build()

    init_handlers(app)

    app.run_polling()
