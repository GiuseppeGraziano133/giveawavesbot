import os
from typing import Final
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from dotenv import load_dotenv

load_dotenv()

TOKEN: Final = os.getenv('TOKEN')
BOT_USERNAME: Final = os.getenv('BOT_USERNAME')
ADMINS_str: Final = os.getenv('ADMINS')
GROUP: Final = os.getenv('GROUP')
ADMINS: Final = [int(numero) for numero in ADMINS_str.split(',') if numero]

waitingForLink: bool = False
spinLink: str = ''
spinType: str = ''
hasMarkup: bool = False
markup: any


# Commands
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global hasMarkup
    global markup
    hasMarkup = True
    tastiera_inline = [[
        InlineKeyboardButton("Aiuto", callback_data='help'),
        InlineKeyboardButton("Crea Spin", callback_data='createspin')
    ]]
    markup = InlineKeyboardMarkup(tastiera_inline)
    await update.message.reply_text('Benvenuto in GiveaWavesBot. Per cominciare, scegli cosa fare', reply_markup=markup)
    hasMarkup = False


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await get_message(update).reply_text('Con il comando /createspin si può mandare un messaggio nel gruppo GiveaWaves, specificando il link e la tipologia di ruota\n\nSe durante la creazione della ruota si vuole interrompere il flusso digitare il comando /stop')


async def stop_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global waitingForLink
    global spinLink
    global spinType
    global hasMarkup
    waitingForLink = False
    spinLink = ''
    spinType = ''
    hasMarkup = False
    await update.message.reply_text('Flusso interrotto')


async def create_spin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if str(get_message(update).chat.id) in ADMINS:
        global waitingForLink
        waitingForLink = True
        await get_message(update).reply_text('Specificare il link della ruota')
    else:
        await get_message(update).reply_text('Non hai i permessi per eseguire questo comando')


# Utils
def get_message(update: Update):
    if not update.message:
        return update.callback_query.message
    else:
        return update.message


async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global spinType
    message_type: str = update.callback_query.message.chat.type
    text: str = update.callback_query.data
    print(f'User ({update.callback_query.message.chat.id}) in {message_type}: {text}')

    if text == 'help':
        await help_command(update, context)
    elif text == 'createspin':
        await create_spin_command(update, context)
    else:
        spinType = text
        await context.bot.send_message(GROUP, build_spin_message(), parse_mode='html')
        await update.callback_query.message.delete()
        await update.callback_query.message.reply_text('Messaggio inviato nel gruppo')


def build_spin_message():
    if spinType == 'default':
        return f"🌊 ONDA IN ARRIVO!\nClicca sul link, logga e clicca partecipa sopra la ruota!\n👉🏼 <a href='{spinLink}'>Partecipa all'estrazione</a>\nCondividi e cavalca l'onda con i tuoi amici!"
    if spinType == '25':
        return f"🌊 ONDA IN ARRIVO!\n<b>25€ PREMIO GARANTITO!</b>\nClicca sul link, logga e clicca partecipa sopra la ruota!\n👉🏼 <a href='{spinLink}'>Partecipa all'estrazione</a>\nCondividi e cavalca l'onda con i tuoi amici!"
    if spinType == '50':
        return f"🌊 ONDA IN ARRIVO!\n<b>50€ GARANTITI AL VINCITORE!</b>\nClicca sul link, logga e clicca partecipa sopra la ruota!\n👉🏼 <a href='{spinLink}'>Partecipa all'estrazione</a>\nCondividi e cavalca l'onda con i tuoi amici!"


# Responses
def handle_response(text: str) -> str:
    text = text.lower()
    global spinLink
    global waitingForLink
    global hasMarkup
    global markup

    if waitingForLink:
        if 'https://' in text:
            spinLink = text
            waitingForLink = False
            hasMarkup = True
            tastiera_inline = [[
                InlineKeyboardButton("Normale", callback_data='default'),
                InlineKeyboardButton("25", callback_data='25'),
                InlineKeyboardButton("50", callback_data='50')
            ]]
            markup = InlineKeyboardMarkup(tastiera_inline)
            return 'Scegli la tipologia di ruota'

        return 'Questo non è un link valido, riprova'
    else:
        return 'Per proseguire, utilizza uno dei comandi che puoi trovare con /help'


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text
    global hasMarkup
    global markup

    print(f'User ({update.message.chat.id}) in {message_type}: {text}')

    if message_type == 'group':
        if BOT_USERNAME in text:
            new_text: str = text.replace(BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)

    print('Bot: ', response)

    if hasMarkup:
        await update.message.reply_text(response, reply_markup=markup)
    else:
        await update.message.reply_text(response)

    hasMarkup = False


async def error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f'Update {update} caused error {context.error}')


# Main
if __name__ == '__main__':
    print('Starting bot...')

    # Set token
    app = Application.builder().token(TOKEN).build()

    # Commands
    commands = [
        ['start', start_command],
        ['help', help_command],
        ['createspin', create_spin_command],
        ['stop', stop_command]
    ]

    for c in commands:
        app.add_handler(CommandHandler(c[0], c[1]))

    # Messages
    app.add_handler(MessageHandler(filters.TEXT, handle_message))
    app.add_handler(CallbackQueryHandler(handle_button))

    # Error
    #app.add_error_handler(error)

    # Listener
    interval = 3
    print(f'Polling (interval: {interval})...')
    app.run_polling(poll_interval=interval)
