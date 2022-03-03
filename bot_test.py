from ast import Raise
import string
import discord
import json
import random
from discord.utils import get
from discord.ext import commands
from table2ascii import table2ascii as t2a
from collections import OrderedDict
import logging
from nono_word import NoNo_Word

# Set up logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='private/nono.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# A members intent is needed to get members objects from guilds
intents = discord.Intents.default()
intents.members = True
intents.guilds = True

# All commands must be prepended with '~'
bot = commands.Bot(command_prefix='~', intents=intents, chunk_guilds_at_startup=True)

@bot.event  #registers an event
async def on_ready(): #on ready called when bot has finish logging in
    print(f'{bot.user.name} has connected to Discord!')

@bot.event
async def on_guild_join(guild):
    join_message = "ZOMG! I JOINED" + guild.name
    print(join_message)
    for text_channel in guild.text_channels:
        if bot.user in text_channel.members: 
            await text_channel.send(join_message)



@bot.event
async def on_message(message): #called when bot has recieves a message
     # Don't respond to the bot itself
    if message.author == bot.user:
        return

    print(message.content)

    await message.channel.send(message.content)



# Load the secret token that allows configuation of the bot
with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TEST-TOKEN']

# Start the bot
bot.run(TOKEN)