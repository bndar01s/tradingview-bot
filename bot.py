import telebot
from telebot import types
import pandas as pd
import openpyxl
from openpyxl.styles import PatternFill, Font
import os
import json

TOKEN = '8249661500:AAF-8Co6x9EamaMqm8Taj2XSXViQzK4fC8U'
bot = telebot.TeleBot(TOKEN)

telebot.apihelper.CONNECT_TIMEOUT = 60
telebot.apihelper.READ_TIMEOUT = 60

DATA_FILE = "members_data.json"
EXCEL_FILE = "tradingview_members.xlsx"
ADMIN_IDS = ["331668623", "329119501"]

def load_data():
    # محاولة قراءة ملف البيانات الجاهز
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data:
                    return data
        except Exception:
            pass
    
    # إذا لم يوجد JSON، نقرأ مباشرة من ملف الإكسل المرفوع لضمان جلب الـ 405 أعضاء
    members = {}
    if os.path.exists(EXCEL_FILE):
        try:
            df = pd.read_excel(EXCEL_FILE)
            for _, row in df.iterrows():
                uid = str(row.get('المعرف (ID)', ''))
                if uid and uid != 'nan':
                    members[uid] = {
                        'المعرف (ID)': row.get('المعرف (ID)', ''),
                        'الاسم': str(row.get('الاسم', '')),
                        'يوزر تيليجرام': str(row.get('يوزر تيليجرام', 'لا يوجد')),
                        'يوزر TradingView': str(row.get('يوزر TradingView', 'غير مدخل')),
                        'الحالة': str(row.get('الحالة', 'متواجد'))
                    }
        except Exception as e:
            print(f"خطأ قراءة الإكسل: {e}")
            
    return members

def save_data():
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(members_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"خطأ بالحفظ: {e}")

members_data = load_data()
if not os.path.exists(DATA_FILE) and members_data:
    save_data()

waiting_for_tradingview = {}

@bot.message_handler(commands=['post_register'])
def post_register_message(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ عذراً، هذا الأمر مخصص لمالكي البوت فقط.")
        return

    markup = types.InlineKeyboardMarkup()
    bot_username = bot.get_me().username
    btn_private = types.InlineKeyboardButton(
        "📝 اضغط هنا لتسجيل يوزر TradingView",
        url=f"https://t.me/{bot_username}?start=register"
    )
    markup.add(btn_private)

    text = (
        "📊 **تسجيل حسابات TradingView الرسمية**\n\n"
        "إلى كافة الأعضاء (القدامى والجُدد)، يرجى الضغط على الزر أدناه لتسجيل وتوثيق يوزر TradingView الخاص بك.\n\n"
        "*(التسجيل يتم بشكل سري وخاص تماماً بينك وبين البوت)*"
    )

    args = message.text.split()
    target_chat = args[1] if len(args) > 1 else message.chat.id

    try:
        bot.send_message(target_chat, text, reply_markup=markup, parse_mode="Markdown")
        if message.chat.type != 'private':
            bot.delete_message(message.chat.id, message.message_id)
        else:
            bot.reply_to(message, "✅ تم نشر منشور التسجيل بنجاح!")
    except Exception as e:
        bot.reply_to(message, f"❌ حدث خطأ أثناء النشر: {e}")

@bot.message_handler(commands=['edit'])
def admin_edit_member(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ عذراً، هذا الأمر مخصص لمالكي البوت فقط.")
        return

    if message.chat.type != 'private':
        return

    args = message.text.split()
    if len(args) >= 3:
        target_id = args[1]
        new_tv = " ".join(args[2:])
    else:
        bot.reply_to(message, "⚠️ خطأ في الصيغة.\nاستخدم الأمر هكذا:\n`/edit 123456789 New_Username`", parse_mode="Markdown")
        return

    if target_id in members_data:
        members_data[target_id]['يوزر TradingView'] = new_tv
        save_data()
        bot.reply_to(message, f"✅ تم تحديث بيانات العضو (`{target_id}`) بنجاح ليكون يوزر TradingView: `{new_tv}`", parse_mode="Markdown")
    else:
        bot.reply_to(message, f"❌ العضو بمعرف `{target_id}` غير مسجل في قاعدة البيانات بعد.", parse_mode="Markdown")

@bot.message_handler(content_types=['new_chat_members'])
def welcome_new_member(message):
    for user in message.new_chat_members:
        if user.is_bot:
            continue
        user_id = str(user.id)
        first_name = user.first_name or ''
        tg_username = f"@{user.username}" if user.username else 'لا يوجد'

        if user_id in members_data:
            members_data[user_id]['الحالة'] = 'متواجد'
            members_data[user_id]['الاسم'] = first_name
            members_data[user_id]['يوزر تيليجرام'] = tg_username
        else:
            members_data[user_id] = {
                'المعرف (ID)': user_id,
                'الاسم': first_name,
                'يوزر تيليجرام': tg_username,
                'يوزر TradingView': 'غير مدخل',
                'الحالة': 'متواجد'
            }
        save_data()

@bot.message_handler(content_types=['left_chat_member'])
def member_left(message):
    user = message.left_chat_member
    if user and not user.is_bot:
        user_id = str(user.id)
        if user_id in members_data:
            members_data[user_id]['الحالة'] = '❌ خرج من المجموعة'
            save_data()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or ''
    tg_username = f"@{message.from_user.username}" if message.from_user.username else 'لا يوجد'

    if user_id not in members_data:
        members_data[user_id] = {
            'المعرف (ID)': user_id,
            'الاسم': first_name,
            'يوزر تيليجرام': tg_username,
            'يوزر TradingView': 'غير مدخل',
            'الحالة': 'متواجد'
        }
        save_data()

    if message.chat.type == 'private':
        already_registered = (
            user_id in members_data and
            members_data[user_id].get('يوزر TradingView') and
            members_data[user_id].get('يوزر TradingView') != 'غير مدخل'
        )

        if len(message.text.split()) > 1 and message.text.split()[1] == 'register':
            if already_registered:
                saved_tv = members_data[user_id]['يوزر TradingView']
                bot.reply_to(message, f"⚠️ أنت مسجل مسبقاً بالفعل!\nيوزر TradingView الخاص بك هو: `{saved_tv}`", parse_mode="Markdown")
            else:
                waiting_for_tradingview[user_id] = True
                bot.reply_to(message, f"أهلاً بك يا {first_name} 🌟\nمن فضلك أرسل الآن اسم المستخدم (Username) الخاص بك في TradingView:")
        else:
            if already_registered:
                saved_tv = members_data[user_id]['يوزر TradingView']
                bot.reply_to(message, f"أهلاً بك يا {first_name}.\nأنت مسجل بالفعل ويوزرك في TradingView هو: `{saved_tv}`", parse_mode="Markdown")
            else:
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("📝 تسجيل يوزر TradingView", callback_data="btn_register"))
                bot.reply_to(message, f"أهلاً بك يا {first_name} في بوت التوثيق.", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    user_id = str(call.from_user.id)
    if call.data == "btn_register":
        if user_id in members_data and members_data[user_id].get('يوزر TradingView') and members_data[user_id].get('يوزر TradingView') != 'غير مدخل':
            saved_tv = members_data[user_id]['يوزر TradingView']
            bot.answer_callback_query(call.id, "أنت مسجل مسبقاً!", show_alert=True)
            bot.send_message(call.message.chat.id, f"⚠️ أنت مسجل مسبقاً بالفعل ويوزرك هو: `{saved_tv}`", parse_mode="Markdown")
        else:
            waiting_for_tradingview[user_id] = True
            bot.answer_callback_query(call.id)
            bot.send_message(call.message.chat.id, "أرسل الآن اسم المستخدم (Username) الخاص بك في TradingView:")

@bot.message_handler(func=lambda message: message.chat.type == 'private' and str(message.from_user.id) in waiting_for_tradingview)
def capture_tradingview_username(message):
    user_id = str(message.from_user.id)
    tradingview_username = message.text.strip()
    first_name = message.from_user.first_name or ''
    tg_username = f"@{message.from_user.username}" if message.from_user.username else 'لا يوجد'

    if user_id in members_data:
        members_data[user_id]['يوزر TradingView'] = tradingview_username
        members_data[user_id]['الاسم'] = first_name
        members_data[user_id]['يوزر تيليجرام'] = tg_username
        members_data[user_id]['الحالة'] = 'متواجد'
    else:
        members_data[user_id] = {
            'المعرف (ID)': user_id,
            'الاسم': first_name,
            'يوزر تيليجرام': tg_username,
            'يوزر TradingView': tradingview_username,
            'الحالة': 'متواجد'
        }

    if user_id in waiting_for_tradingview:
        del waiting_for_tradingview[user_id]

    save_data()
    bot.reply_to(message, f"✅ تم حفظ وتوثيق حساب TradingView بنجاح: `{tradingview_username}`\nلن تحتاج للتسجيل مرة أخرى.", parse_mode="Markdown")

@bot.message_handler(commands=['excel', 'export'])
def export_to_excel(message):
    if str(message.from_user.id) not in ADMIN_IDS:
        bot.reply_to(message, "⚠️ عذراً، هذا الأمر مخصص لمالكي البوت فقط.")
        return

    if not members_data:
        bot.reply_to(message, "لا توجد بيانات مسجلة حتى الآن.")
        return

    try:
        df = pd.DataFrame(list(members_data.values()))
        file_name = "tradingview_members.xlsx"
        df.to_excel(file_name, index=False, engine='openpyxl')

        wb = openpyxl.load_workbook(file_name)
        ws = wb.active
        ws.sheet_view.rightToLeft = True

        red_fill = PatternFill(start_color="FFC7CE", end_color="FFC7CE", fill_type="solid")
        red_font = Font(color="9C0006")

        header_row = [cell.value for cell in ws[1]]
        status_col_idx = header_row.index('الحالة') + 1 if 'الحالة' in header_row else None

        if status_col_idx:
            for row in range(2, ws.max_row + 1):
                status_val = ws.cell(row=row, column=status_col_idx).value
                if status_val and "خرج" in str(status_val):
                    for col in range(1, ws.max_column + 1):
                        cell = ws.cell(row=row, column=col)
                        cell.fill = red_fill
                        cell.font = red_font

        for col in ws.columns:
            max_len = 0
            col_letter = openpyxl.utils.get_column_letter(col[0].column)
            for cell in col:
                if cell.value:
                    max_len = max(max_len, len(str(cell.value)))
            ws.column_dimensions[col_letter].width = max(max_len + 5, 15)

        wb.save(file_name)

        with open(file_name, 'rb') as file:
            bot.send_document(
                chat_id=message.chat.id,
                document=file,
                caption=f"📊 تقرير الأعضاء المنظم - إجمالي السجلات: {len(members_data)} عضو."
            )

        if os.path.exists(file_name):
            os.remove(file_name)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ أثناء إنتاج الملف: {e}")

print("البوت يعمل الآن مع قراءة ملف الإكسل المرفوع مباشرة...")
bot.infinity_polling()
