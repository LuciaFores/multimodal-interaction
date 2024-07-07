import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
import asyncio
import re

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
SESSION_NAME = os.getenv("SESSION_NAME")

client = TelegramClient(SESSION_NAME, API_KEY, API_HASH)
italian_days = {
    "monday": "Lunedì",
    "tuesday": "Martedì",
    "wednesday": "Mercoledì",
    "thursday": "Giovedì",
    "friday": "Venerdì",
    "saturday": "Sabato",
    "sunday": "Domenica"
}


async def main():
    """
    Main function to start the Telegram bot and handle various commands.
    """
    await client.start(bot_token=BOT_TOKEN)

    @client.on(events.NewMessage(pattern="/start"))
    async def handler(event):
        """
        Handle the /start command by sending a welcome message.

        Args:
            event (telethon.events.NewMessage.Event): The event object containing message details.
        """
        await event.respond("Welcome to the patient helper!")

    @client.on(events.NewMessage(pattern="/help"))
    async def handler(event):
        """
        Handle the /help command by sending a help message.

        Args:
            event (telethon.events.NewMessage.Event): The event object containing message details.
        """
        await event.respond("The bot will notify you when your assisted person needs help and when they took their medications.")

    @client.on(events.NewMessage(pattern="/sendhelp<([a-zA-Z' ]+)>"))
    async def handler(event):
        """
        Handle the /sendhelp command by notifying that the patient needs help.

        Args:
            event (telethon.events.NewMessage.Event): The event object containing message details.
        """
        msg = event.message.text
        await event.delete()
        pattern = r"/sendhelp<([a-zA-Z' ]+)>"
        match = re.match(pattern, msg)
        if match:
            patient_name = match.group(1)
        await asyncio.sleep(1)
        await event.respond(f"{patient_name} ha bisogno del tuo aiuto!\nMettiti in contatto il prima possible!")
    
    @client.on(events.NewMessage(pattern="/sendrecap<([a-zA-Z' ]+)><(bene|male)><(monday|tuesday|wednesday|thursday|friday|saturday|sunday)-([01]?[0-9]|2[0-3]):([0-5][0-9])>"))
    async def handler(event):
        """
        Handle the /sendrecap command by sending a recap of the patient's medication and feelings.

        Args:
            event (telethon.events.NewMessage.Event): The event object containing message details.
        """
        msg = event.message.text
        await event.delete()
        pattern = r"/sendrecap<([a-zA-Z' ]+)><(bene|male)><(monday|tuesday|wednesday|thursday|friday|saturday|sunday)-([01]?[0-9]|2[0-3]):([0-5][0-9])>"
        match = re.match(pattern, msg)
        if match:
            patient_name = match.group(1)
            feeling = match.group(2)
            day = italian_days[match.group(3)]
            hour = match.group(4)
            minute = match.group(5)
            image_path = f'../medications/{match.group(3)}'
        await asyncio.sleep(1)
        await event.respond(f"Ecco il recap per {patient_name}.\nSi sente {feeling}.\n{day} alle {hour}:{minute} ha preso i seguenti farmaci:")
        for img in os.listdir(image_path):
            await client.send_file(event.chat_id, f"{image_path}/{img}", caption=img.split(".")[0])


if __name__ == "__main__":
    client.loop.run_until_complete(main())
    client.run_until_disconnected()