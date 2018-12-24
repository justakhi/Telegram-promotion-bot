from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, BaseFilter, RegexHandler, ConversationHandler, CallbackQueryHandler
from telegram import ReplyKeyboardMarkup, ReplyKeyboardRemove, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.error import TelegramError, BadRequest ,TimedOut, ChatMigrated, NetworkError
from oauth2client.service_account import ServiceAccountCredentials
from gspread.exceptions import CellNotFound
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from emoji import emojize
import itertools as it
import telegram
import requests
import logging
import gspread
import lxml
import json
import re


class AddCommand(BaseFilter):
    def filter(self, message):
        return '!add' in str(message.text) # or '!Add' in message.text or '!ADD' in message.text
        # return '@' in message.text and (message.text).find("@") == 0

addcommand = AddCommand()

TOKEN = os.environ.get('TOKEN', None)
GROUPCHATID = os.environ.get('GROUPCHATID', None)

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)

CHOOSING, CHANNEL_REGISTER, CHECK_CHANNEL = range(3)

reply_keyboard = [
                  [f'Register New Channel {emojize(":black_nib:", use_aliases=True)}'],
                  [f'My Channels {emojize(":clipboard:", use_aliases=True)}'],
                  [f'Group {emojize(":loudspeaker:", use_aliases=True)}', f'Help {emojize(":grey_question:", use_aliases=True)}']
                  ]
markup = ReplyKeyboardMarkup(reply_keyboard, one_time_keyboard=True)


def grouper(inputs, n, fillvalue='', extrasremover = True):
    iters = [iter(inputs)] * n
    grouped = [list(i) for i in it.zip_longest(*iters, fillvalue=fillvalue)]

    if extrasremover and "" in grouped[-1] and len(grouped) > 0:
         while "" in grouped[-1]:
             grouped[-1].remove("")

    return grouped

def timer(n):
    return datetime.strptime(n,'%H:%M:%S').time()

def start(bot, update):
    print(update)
    if update.message.chat.id > 0:
        bot.send_message(chat_id=update.message.chat.id,
            text=f"Hi there {update.message.chat.first_name} {emojize(':wave:', use_aliases=True)}\nUse the bot to Contact for advertising & Register your channel for COMPANY services\nADMINS:-",
            reply_markup=markup)
        return CHOOSING
    else:
        return ConversationHandler.END

def my_channels(bot, update):
    if update.message.chat.id > 0:
        # Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(r"test.json", scope)
        gc = gspread.authorize(credentials)
        wks = gc.open("Group Promote").sheet1
        chat_ids = wks.col_values(3)
        records = wks.get_all_values()


        channel_list = []

        if str(update.message.chat.id) in chat_ids:
            while str(update.message.chat.id) in chat_ids:
                ddd = chat_ids.index(str(update.message.chat.id))
                channel_list.append(records[ddd][0])
                chat_ids.pop(ddd)
                records.pop(ddd)

            print(channel_list)
            bot.send_message(chat_id=update.message.chat.id, text=((f"{channel_list}".replace("[","")).replace("]","")).replace("'",""), timeout=30)
            channel_list.clear()
            return ConversationHandler.END
        else:
            update.message.reply_text("You have no Channels registered", timeout=30)
            return ConversationHandler.END
    else:
        return ConversationHandler.END

def register_channels(bot, update):
    if update.message.chat.id > 0:
        bot.send_message(chat_id=update.message.chat.id, text="Please send Your Channel's @username", reply_markup=ForceReply(), timeout=30)
        return CHANNEL_REGISTER
    else:
        return ConversationHandler.END

def channel_checker(bot, update):
    def channelexistence(username):
        try:
            bot.getChat(username)
            return True
        except BadRequest:
            return False
    if update.message.chat.id > 0:
        # bot.delete_message(chat_id=633454130, message_id=update.message.reply_to_message.message_id)
        keyboard = [[InlineKeyboardButton("Done✅", callback_data = 'done')]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        global username
        username = (update.message.text).replace("@", "")
        # Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(r"test.json", scope)
        gc = gspread.authorize(credentials)
        wks = gc.open("Group Promote").sheet1

        if f"@{username}" not in wks.col_values(1):
            if channelexistence(f"@{username}"):
                bot.send_message(chat_id=update.message.chat.id, text="Now please add the Bot in your given channel as Admin WITH following Permissions (Its mandatory)\n\n <code>•can_post_messages</code>\n <code>•can_delete_messages</code>\n <code>•can_edit_messages</code>\n\n\n  CLICK on Done ✅ Button below After adding the bot in your channel with required permissions",
                reply_markup=reply_markup, parse_mode = telegram.ParseMode.HTML, timeout=100)
                return CHECK_CHANNEL
            else:
                bot.send_message(chat_id=update.message.chat.id, text=f"@{username} Channel doesn't exist", timeout=100)
                return ConversationHandler.END
        else:
            bot.send_message(chat_id=update.message.chat.id, text="This Channel is already registered", timeout=50)
            return ConversationHandler.END
    else:
        return ConversationHandler.END

def done(bot, update):
    query = update.callback_query
    print(query)
    channel_username = f"@{username}"
    dope = bot.getChatMember(channel_username, 633454130)
    print(dope)
    chat_info = bot.getChat(f"@{username}")
    if dope.can_post_messages == True and dope.can_edit_messages == True and dope.can_delete_messages == True:
        # Google Sheets
        scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
        credentials = ServiceAccountCredentials.from_json_keyfile_name(r"test.json", scope)
        gc = gspread.authorize(credentials)
        wks = gc.open("Group Promote").sheet1
        lenght = len(wks.col_values(1)) + 1
        wks.update_cell(lenght, 1, channel_username)
        wks.update_cell(lenght, 2, chat_info["id"])
        wks.update_cell(lenght, 3, query.message.chat.id)
        wks.update_cell(lenght, 4, query.message.chat.username)
        bot.send_message(chat_id=query.message.chat.id, text="verified", timeout=50)
        return ConversationHandler.END
    else:
        bot.send_message(chat_id=query.message.chat.id, text="verification falied", timeout=10)
        return ConversationHandler.END

def group(bot, update):
    bot.send_message(chat_id=update.message.chat.id, text = "Group name")
    return ConversationHandler.END

def help(bot, update):
    if update.message.chat.id > 0:
        bot.send_message(chat_id=update.message.chat.id, text = "Help")
        return ConversationHandler.END
    else:
        return ConversationHandler.END

def cancel(bot, update):
    if update.message.chat.id > 0:
        bot.send_message(update.message.chat_id, "Bye!")
        return ConversationHandler.END
    else:
        return ConversationHandler.END

def error(bot, update, error):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, error)

def add(bot, update):
    print(update)

    def col_update(col):
        lenght = len(wks.col_values(col)) + 1
        wks.update_cell(lenght, col - 1, f"{username}")
        wks.update_cell(lenght, col, f"{description}")

    def channelexistence(username):
        try:
            bot.getChat(username)
            return True
        except BadRequest:
            return False

    # Google Sheets
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(r"test.json", scope)
    gc = gspread.authorize(credentials)
    wks1 = gc.open("Group Promote").get_worksheet(0)
    registered_channels = str(wks1.get_all_records())
    msg_id = update.message.message_id
    message = update.message.text

    if message.count(",") == 1 and "@" in message:
        username = message[message.find("@") + 1:message.find(",")]
        description = message[message.find(",") + 1::]

        if str(update.message.chat.id) in registered_channels and username in registered_channels:
            wks2 = gc.open("Group Promote").get_worksheet(1)

            if len(description.split()) > 10:
                bot.send_message(chat_id=GROUPCHATID ,text="We don't accept description morethan 10 words", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
            elif not (channelexistence(f"@{username}")):
                bot.send_message(chat_id=GROUPCHATID ,text="this channel doesn't exits", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
            elif username in str(wks.get_all_values()):
                bot.send_message(chat_id=GROUPCHATID ,text="This channel is already in today's List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
            else:
                req = requests.get(f"https://t.me/{username}")
                soup = BeautifulSoup(req.content, "lxml")
                member = soup.find("div", "tgme_page_extra").text
                member = int(re.sub('[a-zA-Z\s]', '', member))

                if member >= 0 and member <= 999:
                    col_update(2)
                    bot.send_message(chat_id=GROUPCHATID ,text="You are been added to 0 to 999 List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
                elif member >= 1000 and member <= 9999:
                    col_update(4)
                    bot.send_message(chat_id=GROUPCHATID ,text="You are been added to 1000 to 9999 List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
                elif member >= 10000 and member <= 49999:
                    col_update(6)
                    bot.send_message(chat_id=GROUPCHATID ,text="You are been added to 10000 to 49999 List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
                elif member >= 50000 and member <= 199999:
                    col_update(8)
                    bot.send_message(chat_id=GROUPCHATID ,text="You are been added to 50000 to 199999 List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
                elif member >= 200000:
                    col_update(10)
                    bot.send_message(chat_id=GROUPCHATID ,text="You are been added to 200000 and more List", reply_to_message_id=msg_id, disable_notification=True, timeout=50)

        elif str(update.message.chat.id) in registered_channels and username not in registered_channels:
            bot.send_message(chat_id=GROUPCHATID ,text=f"You need to register @{username} channel in @registeringbot", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
        elif str(update.message.chat.id) not in registered_channels and username in registered_channels:
            bot.send_message(chat_id=GROUPCHATID ,text=f"You haven't registered this @{username} channel under your name in @registeringbot", reply_to_message_id=msg_id, disable_notification=True, timeout=50)
        else: bot.send_message(chat_id=GROUPCHATID ,text=f"You haven't registered in @registeringbot", reply_to_message_id=msg_id, disable_notification=True, timeout=50)

    elif message.count(",") != 1 or "@" not in message:
        bot.send_message(chat_id=GROUPCHATID ,text="Format is not correct", reply_to_message_id=msg_id, disable_notification=True)

def list_maker():
    # Google sheets for Storing the Chat ID of every new Telegram user who press start
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    credentials = ServiceAccountCredentials.from_json_keyfile_name(r"test.json", scope)
    gc = gspread.authorize(credentials)
    wk = gc.open("Group Promote")
    wks = wk.get_worksheet(1)

    for column in range(2, 11, 2):
        usernamecolvalues = wks.col_values(column-1)
        descriptioncolvalues = wks.col_values(column)
        usernamecolvalues.pop(0)
        descriptioncolvalues.pop(0)

        if len(usernamecolvalues) > 0:
            usernamecollist = grouper(usernamecolvalues, 20)
            descriptioncollist = grouper(descriptioncolvalues, 20)
            len_col = len(usernamecollist)

            n = 0
            while n < len_col:
                dope = ['\n\n@' + '\n📲'.join(pair) for pair in zip(usernamecollist[n], descriptioncollist[n])]
                column = ''.join(a for a in dope)
                for i in usernamecollist[n]:
                    send_message(chat_id=f"@{i}", text=column, timeout=100)
                n =  n + 1

    row_len = len(wks.get_all_values())
    wk.values_clear(f'Sheet3!A2:J{row_len}')
    send_message(chat_id=518999273, text="List Updated", timeout=100)

def main():
    # Create the Updater and pass it your bot's token.
    updater = Updater(TOKEN)

    # Get the dispatcher to register handlers
    dp = updater.dispatcher
    job = dp.job_queue

    conv_handler = ConversationHandler(
        entry_points = [CommandHandler('start', start)],

        states = {
            CHOOSING:  [
                        RegexHandler(f'^(Register New Channel {emojize(":black_nib:", use_aliases=True)})$', register_channels),
                        RegexHandler(f'^(My Channels {emojize(":clipboard:", use_aliases=True)})$', my_channels),
                        RegexHandler(f'^(Group {emojize(":loudspeaker:", use_aliases=True)})$', group),
                        RegexHandler(f'^(Help {emojize(":grey_question:", use_aliases=True)})$', help)
                        ],
            CHANNEL_REGISTER: [MessageHandler(Filters.reply, channel_checker)],
            CHECK_CHANNEL: [CallbackQueryHandler(done)]
        },

        fallbacks = [CommandHandler('cancel', cancel)])

    help_handler = CommandHandler('help', help)
    my_channels_handler = CommandHandler("channels", my_channels)
    add_command_handler = MessageHandler(addcommand, add)

    dp.add_handler(help_handler)
    dp.add_handler(my_channels_handler)
    dp.add_handler(add_command_handler)
    dp.add_handler(conv_handler)
    dp.add_error_handler(error) # log all errors

    # Job Queue
    job.run_daily(list_maker, time=timer('18:30:00'), days=(0,1,2,3,4,5,6))

    # Start the Bot
    updater.start_polling()

    # Run the bot until you press Ctrl-C or the process receives SIGINT,
    # SIGTERM or SIGABRT. This should be used most of the time, since
    # start_polling() is non-blocking and will stop the bot gracefully.
    updater.idle()


if __name__ == '__main__':
    main()
