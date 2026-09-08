#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import hashlib
import random
from datetime import datetime

import telebot
from telebot import types


# ==================================================
# إعدادات البوت
# ==================================================

BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    raise RuntimeError(
        "BOT_TOKEN is not set. Add BOT_TOKEN in Railway Variables."
    )

ADMIN_ID = 8855682617
ADMINS = [ADMIN_ID]

DEV = "@z_0_y2"
VERSION = "⤷ ᴠ𝟼.𝟶"
AUTHOR = "⤷ @z_0_y2"


# ==================================================
# بيانات المستخدمين والأكواد
# ==================================================

AUTHORIZED_USERS = [ADMIN_ID]

user_codes = {}
pending_codes = {}


# ==================================================
# إعداد البوت
# ==================================================

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML"
)


# ==================================================
# دوال نظام الأكواد
# ==================================================

def is_authorized(user_id):
    # الأدمن مسموح دائمًا
    if user_id in ADMINS:
        return True

    if user_id in user_codes:
        expiry = user_codes[user_id]["expiry"]

        if expiry > time.time():
            return True

        # انتهى الاشتراك
        del user_codes[user_id]

    return False


def generate_user_code(expiry_days):
    code = hashlib.md5(
        f"{time.time()}-{random.random()}".encode()
    ).hexdigest()[:12]

    pending_codes[code] = {
        "expiry": time.time() + (expiry_days * 86400),
        "created_by": ADMIN_ID
    }

    return code


def activate_user_code(user_id, code):
    code = code.strip()

    if code not in pending_codes:
        return False

    data = pending_codes[code]

    if data["expiry"] <= time.time():
        del pending_codes[code]
        return False

    user_codes[user_id] = {
        "expiry": data["expiry"]
    }

    del pending_codes[code]

    return True


def get_user_expiry(user_id):
    if user_id not in user_codes:
        return "Not registered"

    expiry = user_codes[user_id]["expiry"]

    if expiry <= time.time():
        del user_codes[user_id]
        return "Expired"

    return datetime.fromtimestamp(
        expiry
    ).strftime("%Y-%m-%d %H:%M:%S")


# ==================================================
# /start
# ==================================================

@bot.message_handler(commands=["start"])
def start_command(message):

    user_id = message.chat.id

    if user_id in ADMINS:

        markup = types.InlineKeyboardMarkup(row_width=1)

        markup.add(
            types.InlineKeyboardButton(
                "🔐 Create Code",
                callback_data="create_code"
            ),
            types.InlineKeyboardButton(
                "📊 Active Codes",
                callback_data="list_codes"
            ),
            types.InlineKeyboardButton(
                "👥 Users",
                callback_data="list_users"
            )
        )

        bot.reply_to(
            message,
            f"""
✅ <b>Telegram Bot</b>
━━━━━━━━━━━━━━━━━━━━━
👑 <b>Admin Panel</b>
━━━━━━━━━━━━━━━━━━━━━

📌 <b>Commands:</b>

/gencode days - Create code
/activate code - Activate code
/users - Users
/codes - Active codes
/status - Bot status

━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
""",
            reply_markup=markup
        )

        return

    if is_authorized(user_id):

        expiry = get_user_expiry(user_id)

        bot.reply_to(
            message,
            f"""
✅ <b>Welcome</b>
━━━━━━━━━━━━━━━━━━━━━
🆔 ID: <code>{user_id}</code>
📅 Expires: <code>{expiry}</code>
━━━━━━━━━━━━━━━━━━━━━

You are authorized to use the bot.

━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
"""
        )

        return

    bot.reply_to(
        message,
        f"""
❌ <b>ACCESS DENIED</b>
━━━━━━━━━━━━━━━━━━━━━

You don't have an active subscription.

🔑 Use:

<code>/activate CODE</code>

📞 Contact: {DEV}

━━━━━━━━━━━━━━━━━━━━━
"""
    )


# ==================================================
# /activate
# ==================================================

@bot.message_handler(commands=["activate"])
def activate_command(message):

    user_id = message.chat.id

    parts = message.text.split(maxsplit=1)

    if len(parts) < 2:

        bot.reply_to(
            message,
            """
❌ <b>Missing code</b>

Usage:

<code>/activate CODE</code>
"""
        )

        return

    code = parts[1].strip()

    if activate_user_code(user_id, code):

        expiry = get_user_expiry(user_id)

        bot.reply_to(
            message,
            f"""
✅ <b>Code activated successfully!</b>
━━━━━━━━━━━━━━━━━━━━━

🆔 User ID:
<code>{user_id}</code>

📅 Expires:
<code>{expiry}</code>

━━━━━━━━━━━━━━━━━━━━━
"""
        )

    else:

        bot.reply_to(
            message,
            """
❌ <b>Invalid or expired code!</b>
"""
        )


# ==================================================
# /gencode
# ==================================================

@bot.message_handler(commands=["gencode"])
def generate_code_command(message):

    user_id = message.chat.id

    if user_id not in ADMINS:

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    parts = message.text.split()

    if len(parts) != 2:

        bot.reply_to(
            message,
            """
❌ <b>Invalid usage</b>

Example:

<code>/gencode 30</code>
"""
        )

        return

    try:
        days = int(parts[1])
    except ValueError:

        bot.reply_to(
            message,
            "❌ Days must be a number."
        )

        return

    if days <= 0:

        bot.reply_to(
            message,
            "❌ Days must be greater than 0."
        )

        return

    code = generate_user_code(days)

    bot.reply_to(
        message,
        f"""
✅ <b>Code created!</b>
━━━━━━━━━━━━━━━━━━━━━

🔑 Code:
<code>{code}</code>

📅 Duration:
<b>{days} days</b>

━━━━━━━━━━━━━━━━━━━━━

Send to user:

<code>/activate {code}</code>
"""
    )


# ==================================================
# زر إنشاء كود
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "create_code"
)
def create_code_callback(call):

    if call.from_user.id not in ADMINS:

        bot.answer_callback_query(
            call.id,
            "❌ Admin only"
        )

        return

    bot.answer_callback_query(call.id)

    msg = bot.send_message(
        call.from_user.id,
        """
📝 <b>Enter subscription duration</b>

Example:

<code>30</code>
"""
    )

    bot.register_next_step_handler(
        msg,
        create_code_from_button
    )


def create_code_from_button(message):

    if message.from_user.id not in ADMINS:
        return

    try:
        days = int(message.text.strip())
    except ValueError:

        bot.send_message(
            message.chat.id,
            "❌ Please enter a valid number."
        )

        return

    if days <= 0:

        bot.send_message(
            message.chat.id,
            "❌ Days must be greater than 0."
        )

        return

    code = generate_user_code(days)

    bot.send_message(
        message.chat.id,
        f"""
✅ <b>Code created!</b>
━━━━━━━━━━━━━━━━━━━━━

🔑 <code>{code}</code>

📅 {days} days

━━━━━━━━━━━━━━━━━━━━━

<code>/activate {code}</code>
"""
    )


# ==================================================
# قائمة الأكواد
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "list_codes"
)
def list_codes_callback(call):

    if call.from_user.id not in ADMINS:

        bot.answer_callback_query(
            call.id,
            "❌ Admin only"
        )

        return

    bot.answer_callback_query(call.id)

    if not pending_codes:

        bot.send_message(
            call.from_user.id,
            "📭 No active codes."
        )

        return

    text = """
📋 <b>Active Codes</b>
━━━━━━━━━━━━━━━━━━━━━
"""

    expired = []

    for code, data in pending_codes.items():

        if data["expiry"] <= time.time():

            expired.append(code)
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += (
            f"\n🔑 <code>{code}</code>"
            f"\n📅 {expiry}\n"
        )

    for code in expired:
        del pending_codes[code]

    bot.send_message(
        call.from_user.id,
        text
    )


# ==================================================
# قائمة المستخدمين
# ==================================================

@bot.callback_query_handler(
    func=lambda call: call.data == "list_users"
)
def list_users_callback(call):

    if call.from_user.id not in ADMINS:

        bot.answer_callback_query(
            call.id,
            "❌ Admin only"
        )

        return

    bot.answer_callback_query(call.id)

    if not user_codes:

        bot.send_message(
            call.from_user.id,
            "📭 No active users."
        )

        return

    text = """
👥 <b>Users</b>
━━━━━━━━━━━━━━━━━━━━━
"""

    expired = []

    for uid, data in user_codes.items():

        if data["expiry"] <= time.time():

            expired.append(uid)
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += (
            f"\n🆔 <code>{uid}</code>"
            f"\n📅 {expiry}\n"
        )

    for uid in expired:
        del user_codes[uid]

    bot.send_message(
        call.from_user.id,
        text
    )


# ==================================================
# /codes
# ==================================================

@bot.message_handler(commands=["codes"])
def codes_command(message):

    if message.chat.id not in ADMINS:

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    if not pending_codes:

        bot.reply_to(
            message,
            "📭 No active codes."
        )

        return

    text = """
📋 <b>Active Codes</b>
━━━━━━━━━━━━━━━━━━━━━
"""

    for code, data in list(pending_codes.items()):

        if data["expiry"] <= time.time():
            del pending_codes[code]
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += (
            f"\n🔑 <code>{code}</code>"
            f"\n📅 {expiry}\n"
        )

    bot.reply_to(
        message,
        text
    )


# ==================================================
# /users
# ==================================================

@bot.message_handler(commands=["users"])
def users_command(message):

    if message.chat.id not in ADMINS:

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    if not user_codes:

        bot.reply_to(
            message,
            "📭 No active users."
        )

        return

    text = """
👥 <b>Users</b>
━━━━━━━━━━━━━━━━━━━━━
"""

    for uid, data in list(user_codes.items()):

        if data["expiry"] <= time.time():

            del user_codes[uid]
            continue

        expiry = datetime.fromtimestamp(
            data["expiry"]
        ).strftime("%Y-%m-%d %H:%M:%S")

        text += (
            f"\n🆔 <code>{uid}</code>"
            f"\n📅 {expiry}\n"
        )

    bot.reply_to(
        message,
        text
    )


# ==================================================
# /status
# ==================================================

@bot.message_handler(commands=["status"])
def status_command(message):

    if not is_authorized(message.chat.id):

        bot.reply_to(
            message,
            "❌ ACCESS DENIED"
        )

        return

    active_users = 0

    for uid, data in list(user_codes.items()):

        if data["expiry"] > time.time():
            active_users += 1

    bot.reply_to(
        message,
        f"""
📊 <b>Bot Status</b>
━━━━━━━━━━━━━━━━━━━━━

🟢 Bot: Online
👥 Active users: <b>{active_users}</b>
🔑 Pending codes: <b>{len(pending_codes)}</b>

━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
"""
    )


# ==================================================
# تشغيل البوت
# ==================================================

if __name__ == "__main__":

    print("=" * 50)
    print("🤖 TELEGRAM BOT")
    print("=" * 50)
    print(f"👑 Admins: {ADMINS}")
    print(f"👤 Developer: {DEV}")
    print(f"📌 Version: {VERSION}")
    print("=" * 50)
    print("🚀 Bot is running...")

    bot.infinity_polling(
        skip_pending=True,
        timeout=30,
        long_polling_timeout=30
    )
