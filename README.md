The bot is designed to track spam in shared Telegram chats. In order for the bot to work, do not forget to grant it user rights!
Commands:
1) /clear_chat - deletes the last 100 messages in the selected chat, including the command message itself
2) /spam_stat - sends the ban history of the participants in this chat
The bot uses sqlite3 and aiogram. It also uses standard modules such as time and asyncio.
