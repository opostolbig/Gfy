import time
import os
import json
import random
from datetime import datetime, timedelta
from telethon.errors import FloodWaitError
from telethon import TelegramClient, events, types
from telethon.tl import functions
from telethon.tl.functions.messages import ReportRequest
from telethon.tl.types import InputReportReasonSpam  # Удалили импорты InlineKeyboardButton и InlineKeyboardMarkup
from colorama import Fore, Style

api_id = 25055016
api_hash = '25edf5b7becebe91a2d61fe8d9d9931b'
bot_token = '7642861396:AAHKFGfwLyq3TG96HjCRjWmqHOyJr0gO0Ig'
subs_file = "sub/sub.txt"
image_path = "image/image.jpg"
usage_limits = {}
sessions_path = "sessions"
admin_ids = [7070612847, 1730733360, 7310051494,721151979]
bot = TelegramClient("bot", api_id, api_hash).start(bot_token=bot_token)

if not os.path.exists(subs_file):
    os.makedirs(os.path.dirname(subs_file), exist_ok=True)
    with open(subs_file, "w") as f:
        f.write("{}")

reptexts = ['Good afternoon dear Telegram support! I would like to complain about this message for violating the Telegram (ToS) rules, please take action!',
            'Dear, Telegram support! I would like to tell you that this message contains threats and violates the rules of Telegram messenger. Please, take action.']

try:
    with open(subs_file, "r") as f:
        subscriptions = json.load(f)
except json.JSONDecodeError:
    subscriptions = {}
    with open(subs_file, "w") as f:
        json.dump(subscriptions, f)

def save_subscriptions():
    with open(subs_file, "w") as f:
        json.dump(subscriptions, f)

# Проверка активной подписки
def has_active_subscription(user_id):
    if str(user_id) in subscriptions:
        expiry = datetime.fromisoformat(subscriptions[str(user_id)])
        if expiry > datetime.now():
            return expiry
        else:
            del subscriptions[str(user_id)]
            save_subscriptions()
    return None

@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    expiry = has_active_subscription(user_id)
    if expiry:
        text1 = f'У вас имеется активная подписка до {expiry.strftime("%H:%M %d.%m.%Y")}'
    else:
        text1 = 'У вас нет подписки'
    
    # Если изображение существует, отправляем его
    if os.path.exists(image_path):
        await bot.send_message(
            user_id,
            f'Добро пожаловать в GLONET Botnet.\n\nВведите /ss и ссылку на сообщение.\n\n{text1}',
            parse_mode='html',
            file=image_path
        )
    else:
        await bot.send_message(
            user_id,
            f'Добро пожаловать в GLONET Botnet.\n\nВведите /ss и ссылку на сообщение.\n\n{text1}',
            parse_mode='html'
        )

@bot.on(events.NewMessage(pattern="/ss (.+)"))
async def report_message(event):
    user_id = event.sender_id
    expiry = has_active_subscription(user_id)
    if not expiry:
        await event.reply('У вас не имеется активной подписки.')
        return
    target = event.message.text.split(maxsplit=1)[1]
    await event.reply("Жалобы отправляются...")
    start_time = datetime.now()
    link_parts = target.split('/')
    chat_username = link_parts[-2]
    message_id = int(link_parts[-1])

    successful_reports = 0
    unsuccessful_reports = 0
    now = datetime.now()
    if user_id not in admin_ids:
        if user_id in usage_limits and now < usage_limits[user_id]:
            remaining = (usage_limits[user_id] - now).total_seconds() / 60
            await event.reply(f"Вы можете использовать эту команду через {remaining:.1f} минут.")
            return
        usage_limits[user_id] = now + timedelta(minutes=7)
    for session_file in os.listdir(sessions_path):
            session_path = os.path.join(sessions_path, session_file)
            client = TelegramClient(session_path, api_id, api_hash)
            delaytext = random.uniform(0.01, 0.02)
            messagetext = random.choice(reptexts)
            try:
                time.sleep(delaytext)
                await client.connect()
                chat = await client.get_entity(chat_username)
                await client(ReportRequest(
                                peer=chat,
                                id=[message_id],
                                reason=InputReportReasonSpam(),
                                message=messagetext
                            ))
                successful_reports += 1
                print(f"Жалоба успешно отправлена: {session_file}, {target}, {datetime.now()}, {messagetext}")
            except Exception as e:
                unsuccessful_reports += 1
                print(f"ОШИБКА: {session_file}: {e}")
            finally:
                await client.disconnect()
    await event.reply(
            f"Жалобы отправлены.\n\n[Ссылка на сообщение]({target})\n\n"
            f"Успешных жалоб: {successful_reports}\n"
            f"Неуспешных жалоб: {unsuccessful_reports}\n\n"
            )

@bot.on(events.NewMessage(pattern="/add", from_users=admin_ids))
async def add_sessions(event):
    print("Команда /add получена от пользователя:", event.sender_id)
    if event.message.file:
        try:
            file_path = os.path.join(sessions_path, event.message.file.name)
            await event.message.download_media(file=file_path)
            if os.path.exists(file_path):
                await event.reply(f"Файл {file_path} успешно загружен в папку сессий.")
                print(f"Файл успешно загружен: {file_path}")
            else:
                await event.reply("Произошла ошибка при загрузке файла.")
                print("Файл не найден после загрузки.")
        except Exception as e:
            await event.reply(f"Произошла ошибка при загрузке файла: {e}")
            print(f"Ошибка при загрузке файла: {e}")
    else:
        await event.reply("Пожалуйста, отправьте файл сессии для загрузки.")
        print("Файл не был прикреплен к команде /add.")

@bot.on(events.NewMessage(pattern="/give (\\d+) (\\d+)", from_users=admin_ids))
async def give_subscription(event):
    try:
        args = event.message.text.split()
        user_id = int(args[1])
        days = int(args[2])

        # Вычисляем срок подписки
        expiry = datetime.now() + timedelta(days=days)

        subscriptions[str(user_id)] = expiry.isoformat()
        save_subscriptions()
        await event.reply(f"🎉 Подписка для пользователя {user_id} выдана на {days} дня(ей), до {expiry.strftime('%H:%M %d.%m.%Y')}.")

    except Exception as e:
        await event.reply(f"❌ Ошибка: {e}")

@bot.on(events.NewMessage(pattern="/remove_sub (\\d+)", from_users=admin_ids))
async def remove_subscription(event):
    try:
        user_id = int(event.message.text.split()[1])
        if str(user_id) in subscriptions:
            del subscriptions[str(user_id)]
            save_subscriptions()
            await event.reply(f"🚫 Подписка для пользователя {user_id} удалена.")
        else:
            await event.reply("У пользователя нет активной подписки.")
    except Exception as e:
        await event.reply(f"❌ Ошибка: {e}")

bot.run_until_disconnected()
