import sys
from pathlib import Path
file = Path(__file__).resolve()
parent, root = file.parent, file.parents[1]
sys.path.append(str(root))

try:
    sys.path.remove(str(parent))
except ValueError:  # Already removed
    pass


from aid import aid_manager as mngr
from telegram.ext import ApplicationBuilder, ContextTypes, CommandHandler
from telegram import Update
import logging




logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)
aids = mngr.Aid()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="I'm a aid bot, please run command /aid <aid_name> to connect to your aid")


async def choose_aid(update: Update, context: ContextTypes.DEFAULT_TYPE):
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


if __name__ == '__main__':
    # TODO: move token to secure place
    app = ApplicationBuilder().token(
        '5898027021:AAG-et5fU_5nONWeaFjkbdbtDSTSqi0G_50').build()

    start_handler = CommandHandler('start', start)
    choose_aid = CommandHandler('aid', choose_aid)
    app.add_handler(start_handler)
    app.add_handler(choose_aid)

    app.run_polling()
