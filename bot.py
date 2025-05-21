import lagrange as lag
from lagrange.client.events.friend import FriendMessage
from lagrange.client.events.group import GroupMessage
from lagrange.client.client import Client
from lagrange.utils.log import log as log
from selection_generation import DialogueSession
import asyncio

async def launch_lagrange(handle_friend_message):
    bot = lag.Lagrange(0, 'custom', sign_url="https://sign.lagrangecore.org/api/sign/25765")
    bot.subscribe(FriendMessage, handle_friend_message)
    try:
        await bot.run()
    except KeyboardInterrupt:
        bot.client._task_clear()
        log.root.info("Program exited by user")
    else:
        log.root.info("Program exited normally")


