import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import Forbidden, BadRequest
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    CommandHandler,
    MessageHandler,
    filters,
    ConversationHandler,
    CallbackQueryHandler,
)

# --- CONFIGURATION ---
TOKEN = "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"  # <--- REPLACE THIS
ADMIN_ID = 2037442900           # <--- REPLACE THIS

# --- LOGGING SETUP ---
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# --- DATABASE HANDLER ---
DB_NAME = "bot_data.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (user_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT, joined_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS config
                 (key TEXT PRIMARY KEY, content TEXT, file_id TEXT, type TEXT)''')
    
    # Defaults
    c.execute("INSERT OR IGNORE INTO config (key, content, file_id, type) VALUES ('welcome_msg', 'Here is your link!', NULL, 'text')")
    c.execute("INSERT OR IGNORE INTO config (key, content, file_id, type) VALUES ('timer', '0', NULL, 'number')") 
    conn.commit()
    conn.close()

def add_user(user):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    # INSERT OR IGNORE means: If user exists, do nothing. If new, save them.
    c.execute("INSERT OR IGNORE INTO users (user_id, username, first_name) VALUES (?, ?, ?)", 
              (user.id, user.username, user.first_name))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM users")
    count = c.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT user_id FROM users")
    users = [row[0] for row in c.fetchall()]
    conn.close()
    return users

def get_config(key):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT content, file_id, type FROM config WHERE key=?", (key,))
    data = c.fetchone()
    conn.close()
    return data

def set_config(key, content, file_id, msg_type):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO config (key, content, file_id, type) VALUES (?, ?, ?, ?)", 
              (key, content, file_id, msg_type))
    conn.commit()
    conn.close()

# --- JOB QUEUE (DELETE AND SEND WARNING) ---

async def delete_and_warn_job(context: ContextTypes.DEFAULT_TYPE):
    job = context.job
    chat_id = job.chat_id
    message_id = job.data
    
    # 1. Delete the Link Message
    try:
        await context.bot.delete_message(chat_id=chat_id, message_id=message_id)
    except BadRequest:
        pass 
    except Exception as e:
        logging.error(f"Error deleting: {e}")

    # 2. Send the Persistent Warning
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ **Message Deleted**\n\nThe link was deleted automatically.\n\n🔄 **To get the link again:** Send 'Hi' or click /start.\n📞 **Issues?** DM Admin.",
            parse_mode='Markdown'
        )
    except Exception as e:
        logging.error(f"Error sending warning: {e}")

# --- CONVERSATION STATES ---
SELECTING_ACTION, TYPING_NEW_MSG, TYPING_TIMER = range(3)
AWAITING_BROADCAST = 10

# --- USER HANDLER ---

async def user_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main handler for /start and text messages."""
    user = update.effective_user
    add_user(user) # This works for both new and old users
    
    # 1. Get Config
    msg_data = get_config('welcome_msg')
    content = msg_data[0]
    file_id = msg_data[1]
    msg_type = msg_data[2]
    
    timer_data = get_config('timer')
    timer_seconds = int(timer_data[0]) if timer_data else 0

    footer = ""
    if timer_seconds > 0:
        footer = f"\n\n⏳ _This message will disappear in {timer_seconds} seconds._"

    sent_msg = None
    try:
        # 3. Send the Content
        if msg_type == 'photo' and file_id:
            full_caption = (content + footer)
            sent_msg = await update.message.reply_photo(photo=file_id, caption=full_caption[:1024], parse_mode='Markdown')
        else:
            full_text = (content + footer)
            sent_msg = await update.message.reply_text(full_text, parse_mode='Markdown')
            
        # 4. Schedule Timer
        if timer_seconds > 0 and sent_msg:
            context.job_queue.run_once(
                delete_and_warn_job, 
                timer_seconds, 
                chat_id=user.id, 
                data=sent_msg.message_id
            )

    except Exception as e:
        logging.error(f"Error sending content: {e}")
        await update.message.reply_text("Welcome! (Error loading custom message)")

async def restart(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forces the user_reply function to run when /start is pressed in a menu."""
    await user_reply(update, context)
    return ConversationHandler.END

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Operation cancelled.")
    return ConversationHandler.END

# --- ADMIN PANEL ---

async def admin_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id != ADMIN_ID: return

    t_data = get_config('timer')
    curr_timer = t_data[0] if t_data else "0"

    keyboard = [
        [InlineKeyboardButton("📊 Stats", callback_data='stats'), InlineKeyboardButton("👁️ View Message", callback_data='view_current')],
        [InlineKeyboardButton(f"⏱️ Set Timer ({curr_timer}s)", callback_data='set_timer')],
        [InlineKeyboardButton("✏️ Set New Message", callback_data='set_new')],
        [InlineKeyboardButton("❌ Close", callback_data='close')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "👮‍♂️ **Admin Panel**"
    
    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode='Markdown')
    return SELECTING_ACTION

# ... Standard Admin Functions ...
async def admin_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    count = get_stats()
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
    await query.edit_message_text(f"Users: `{count}`", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
    return SELECTING_ACTION

async def admin_view_current(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = get_config('welcome_msg')
    keyboard = [[InlineKeyboardButton("🔙 Back", callback_data='back')]]
    if data[2] == 'photo':
        await query.message.reply_photo(photo=data[1], caption=data[0])
        await query.message.reply_text("Use menu below:", reply_markup=InlineKeyboardMarkup(keyboard))
    else:
        await query.edit_message_text(data[0], reply_markup=InlineKeyboardMarkup(keyboard))
    return SELECTING_ACTION

async def admin_close(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("Closed.")
    return ConversationHandler.END

async def admin_ask_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("⏱️ **Send timer in seconds.**\n\n- `0`: No delete\n- `10`: Delete after 10s")
    return TYPING_TIMER

async def admin_save_timer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text.isdigit():
        await update.message.reply_text("Send numbers only.")
        return TYPING_TIMER
    set_config('timer', text, None, 'number')
    await update.message.reply_text(f"✅ Timer set to {text}s.\n/admin to return.")
    return ConversationHandler.END

async def admin_ask_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("📝 **Send new message.** (Text or Image)")
    return TYPING_NEW_MSG

async def admin_save_new(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.photo:
        file_id = update.message.photo[-1].file_id
        content = update.message.caption if update.message.caption else ""
        set_config('welcome_msg', content, file_id, 'photo')
        reply_text = "✅ Image Saved."
    elif update.message.text:
        content = update.message.text
        set_config('welcome_msg', content, None, 'text')
        reply_text = "✅ Text Saved."
    else:
        await update.message.reply_text("Send Text or Photo.")
        return TYPING_NEW_MSG
    await update.message.reply_text(f"{reply_text}\nType /admin to return.")
    return ConversationHandler.END

# --- BROADCAST ---
async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID: return
    await update.message.reply_text("📢 Send broadcast message.")
    return AWAITING_BROADCAST

async def send_broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = update.message
    users = get_all_users()
    await update.message.reply_text(f"Sending to {len(users)} users...")
    for uid in users:
        try:
            await context.bot.copy_message(chat_id=uid, from_chat_id=update.effective_chat.id, message_id=msg.message_id)
        except: pass
    await update.message.reply_text("✅ Done.")
    return ConversationHandler.END

# --- MAIN BLOCK ---
if __name__ == '__main__':
    init_db()
    print("Bot is running...")
    
    # Enable JobQueue
    application = ApplicationBuilder().token(TOKEN).build()

    # 1. Admin & Broadcast Conversations
    common_fallbacks = [CommandHandler('cancel', cancel), CommandHandler('start', restart)]

    admin_conv = ConversationHandler(
        entry_points=[CommandHandler('admin', admin_start)],
        states={
            SELECTING_ACTION: [
                CallbackQueryHandler(admin_stats, pattern='^stats$'),
                CallbackQueryHandler(admin_view_current, pattern='^view_current$'),
                CallbackQueryHandler(admin_ask_new, pattern='^set_new$'),
                CallbackQueryHandler(admin_ask_timer, pattern='^set_timer$'),
                CallbackQueryHandler(admin_start, pattern='^back$'), 
                CallbackQueryHandler(admin_close, pattern='^close$'),
            ],
            TYPING_NEW_MSG: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_new), MessageHandler(filters.PHOTO, admin_save_new)],
            TYPING_TIMER: [MessageHandler(filters.TEXT & ~filters.COMMAND, admin_save_timer)]
        },
        fallbacks=common_fallbacks, allow_reentry=True
    )
    
    broadcast_conv = ConversationHandler(
        entry_points=[CommandHandler('broadcast', broadcast_command)],
        states={AWAITING_BROADCAST: [MessageHandler(filters.ALL & ~filters.COMMAND, send_broadcast)]},
        fallbacks=common_fallbacks, allow_reentry=True
    )

    application.add_handler(admin_conv)
    application.add_handler(broadcast_conv)
    
    # 2. EXPLICIT START COMMAND (Fixes the issue)
    # This ensures /start is always caught first, regardless of user status
    application.add_handler(CommandHandler('start', user_reply))

    # 3. TEXT HANDLER (For Hi/Hello/Etc)
    # Catches any text that isn't a command
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, user_reply))


    application.run_polling()
