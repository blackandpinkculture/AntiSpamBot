import asyncio
import aiogram
import time
import sqlite3

dp = aiogram.Dispatcher()
TOKEN = "TOKEN"
del_msg = True

conn = sqlite3.connect("database.db", check_same_thread=False)
cur = conn.cursor()

user_messages = {}
user_unvarns = {}

cur.execute('''
CREATE TABLE IF NOT EXISTS users (
userId INTEGER,
warning INTEGER,
chatId INTEGER)''')
cur.execute('''
CREATE TABLE IF NOT EXISTS stats (
userId INTEGER,
action TEXT,
date TEXT,
chatId INTEGER)
''')
conn.commit()

@dp.message()
async def new_message(message: aiogram.types.Message, bot) -> None:
	if message.chat.type == "private":
		await message.reply("я работаю только в общих чатах! просто добавь меня в группу, назначь администратором, и твой чат будет в безопасности!")
		return
	 
	if message.from_user.id in user_messages:
		if int(time.time()) - user_messages[message.from_user.id] < 3:
			user_unvarns[message.from_user.id] += 1
			user_messages[message.from_user.id] = int(time.time())
		else:
			user_unvarns[message.from_user.id] = 0
			user_messages[message.from_user.id] = int(time.time())
	else:
		user_messages[message.from_user.id] = int(time.time()) 
		user_unvarns[message.from_user.id] = 0
		return

	if user_unvarns[message.from_user.id] >= 3:
		admin_list = []
		admins = await message.bot.get_chat_administrators(message.chat.id)
		for member in admins:
			admin_list.append(member.user.id)
		if message.from_user.id in admin_list:
			return
		user = cur.execute("SELECT * FROM users WHERE userId=? AND chatId=?", (message.from_user.id, message.chat.id, )).fetchone()
		if user:
			if user[1] < 3:
				await bot.delete_message(message.chat.id, message.message_id)
				cur.execute("UPDATE users SET warning=? WHERE userId=? AND chatId=?", (user[1]+1, message.from_user.id, message.chat.id, ))
				await message.answer(f"🛡️ {message.from_user.username}, вы слишком много пишите! у вас {user[1]+1}/3 предупреждений. Для обжаливания пишите администраторам.")
			elif user[1] >= 3:
				cur.execute("DELETE FROM users WHERE userId=? AND chatId=?", (message.from_user.id, message.chat.id, ))
				now_time = time.strftime("%d.%m.%y - %H:%M:%S", time.localtime())
				action = f"Участник {message.from_user.first_name} ({message.from_user.username}) был заблокирован ботом за спам."
				cur.execute("INSERT INTO stats(userId, action, date, chatId) VALUES(?, ?, ?, ?)", (message.from_user.id, action, now_time, message.chat.id, ))
				await bot.delete_message(message.chat.id, message.message_id)
				await bot.ban_chat_member(chat_id=message.chat.id, user_id=message.from_user.id, revoke_messages=del_msg)
				await message.answer(f"🛡️ {message.from_user.username} был забанен в чате за неоднократный спам. Если вы не согласны с баном - пишите администраторам чата.")
		else:
			cur.execute("INSERT INTO users(userId, warning, chatId) VALUES(?, ?, ?)", (message.from_user.id, 1, message.chat.id, ))
			await message.reply(f"🛡️ {message.from_user.username}, вы слишком много пишите! У вас 1/3 предупреждений. Для обжаливания пишите администраторам.")
		conn.commit()
	
	if message.text == "/spam_stat":
		admin_list = []
		admins = await message.bot.get_chat_administrators(message.chat.id)
		for member in admins:
			admin_list.append(member.user.id)
		if message.from_user.id in admin_list:
			history_chat = cur.execute("SELECT * FROM stats WHERE chatId=?", (message.chat.id, )).fetchall()
			if history_chat:
				msg = ""
				for history in history_chat:
					msg += f"Действие: {history[1]} \nДата: {history[2]}\n\n"
				await message.answer(f"🛡️ Отчёт: \n\n{msg}")
			else:
				await message.answer("📝 В базе нету записей о действиях в этом чате.")
		else:
			await message.answer("❌ Вы не являетесь администратором в данном чате.")
	
	if message.text == "/clear_chat":
		admin_list = []
		admins = await message.bot.get_chat_administrators(message.chat.id)
		for member in admins:
			admin_list.append(member.user.id)
		if message.from_user.id in admin_list:
			quantity = message.message_id - 100
			if quantity < 100:
				await message.reply("❌ Команда рассчитана на удаление прошлых 100 сообщений. В данном чате сообщений менее сотни.")
				return
			for msgId in range(quantity):
				await bot.delete_message(message.chat.id, msgId)
			await message.answer("✅ Чистка завершена.")
		else:
			await message.reply("❌ Вы не являетесь администратором в данном чате.")

async def main() -> None:
	bot = aiogram.Bot(token=TOKEN)
	print("LOG IN")
	await dp.start_polling(bot)

if __name__ == "__main__":
	asyncio.run(main())
