import discord
import time
import asyncio
import json
import re
import random
from discord.utils import get
from discord.ext import commands
from collections import OrderedDict


#client = discord.Client() #create a client instance
#https://discordpy.readthedocs.io/en/stable/ext/commands/commands.html
#https://discordpy.readthedocs.io/en/stable/ext/commands/api.html
bot = commands.Bot(command_prefix='~')



#get author's real name, or Discord handle otherwise
def get_name(author):
    if ("(" in author.display_name): #check if nickname has real name, e.g. Username (Name)
        open_paren = author.display_name.index('(') + 1
        close_paren = author.display_name.index(')')
        return author.display_name[open_paren:close_paren]
    else:
        return str(author)[:-5]

def bold(string):
    return "**" + string + "**"

nono_dict = OrderedDict()
with open('bad_words.txt') as f:
    nono_list = f.readlines()
    for bad_word in nono_list:
        nono_dict[bad_word.strip()] = 0

def nono_prefix(offender):
    nono_prefixes = [
        "Be it known that the criminal," + offender + " has committed the following offenses:",
        "My my, " + offender + "such language...",
        offender + "! You're due for a donation to the swear jar",
        "This is a Christrian Mincraft server, " + offender,
        offender + "! For shame.",
        "Hmm, " + offender + "... why am I not surprised?"
    ]
    return random.choice(nono_prefixes) + "\n"

# Provide a list of all nono words said
#TODO Add second argument 'offender', default to author
@bot.command()
async def list(ctx, offender=None):
    if offender == None:
        offender = ctx.author
    nono_string = nono_prefix(bold(get_name(offender)))
    print('listing nono words!')
    for text_channel in ctx.guild.text_channels:
        async for message in text_channel.history(limit=1000):
            if message.author == ctx.author:
                message_list = message.content.lower().split()
                for nono_word, count in nono_dict.items():
                    nono_dict[nono_word] = count + message_list.count(nono_word)
    for nono_word, count in nono_dict.items():
        if count > 0:
            nono_string += bold(nono_word) + ": " + str(count) +"\n"   
    await ctx.channel.send(nono_string)

# A command for playing youtube audio through voice channel
#https://discordpy.readthedocs.io/en/stable/api.html#discord.Member
# expects message to be ~play <youtube url>
@bot.command()
async def play(ctx, url):
    print(ctx, end=' ' + url)
    #Author is type dicord.Member https://discordpy.readthedocs.io/en/stable/api.html#discord.Member
    author = ctx.author
    voice_channel = author.voice.channel
    

    # client.user is the bot itself, it is of type "ClientUser" https://discordpy.readthedocs.io/en/stable/api.html#discord.ClientUser
    #print(client.user.voice_clients)
    
    
    #Connect to voice channel if not already
    # voice_client is this object: https://discordpy.readthedocs.io/en/stable/api.html#discord.VoiceClient
    

# Conduct a poll between two things
# TODO ask for choices and time limit
@bot.command()
async def poll():
    #TODO pipe in real value from database
    option1 = 'jackboots'
    option2 = 'sandles'

    actual_option1 = 'Hitler'
    actual_option2 = 'Ghandi'

    message = await ctx.channel.send('React with: \n' + '🌕' + ' for '  + option1 + ', \n' + '🌑' + ' for ' + option2)
    channel = message.channel  
    await message.add_reaction('🌕')
    await message.add_reaction('🌑')
    await asyncio.sleep(2)
    print("Getting count")
    updated_message = await channel.fetch_message(message.id)
    option1_reactions = get(updated_message.reactions, emoji = '🌕')
    option2_reactions = get(updated_message.reactions, emoji = '🌑')
    
    print(option1_reactions.count)
    print(option2_reactions.count)
    
    message2 = ''
    if (option1_reactions.count > option2_reactions.count):
        message2 = await message.channel.send('The majority has decided that '  + actual_option1 + ' is better than ' + actual_option2 + '.\nI love democracy!')
    if (option2_reactions.count > option1_reactions.count):
        message2 = await message.channel.send('The majority has decided that '  + actual_option2 + ' is better than ' + actual_option1 + '.\nI love democracy!')
    if (option2_reactions.count == option1_reactions.count):
        message2 = await message.channel.send('We have a tie! Clearly '  + actual_option2 + ' is exactly as good as ' + actual_option1 + '.\nI love democracy!')

#List history of all bad words someone has said
@bot.command()
async def nono(ctx, user):
    return



@bot.event  #registers an event
async def on_ready(): #on ready called when bot has finish logging in
    print(f'{bot.user.name} has connected to Discord!')

#returns True if string contains listed greetings, else False
def is_greeting(message_string):
    greetings = {"hi", " hi!", "hello", " hey", " hey!", "good morning", "good day", "how's it going", "how are you", "what's up", "wassup", " sup", "sup,", "sup!", "good evening", "good afternoon", "to meet you", "how've you been", "nice to see you", "long time no see", "ahoy", "howdy"}
    #short_greetings {}
    for greeting in greetings:
        if greeting in message_string:
            print(greeting)
            if "hi" in greeting and not message_string.endswith("hi") and message_string[message_string.find('hi') + 2].isalpha():
                print(message_string[message_string.find('hi') + 2])
                return False
            print("Greeting detected")
            return True
    return False

#returns True if string contains listed negative words, else False
def is_insult(message_string):
    insults = {"fuck", "shitty", "suck", "damn", "smelly", "hate", "stink", "loser"}
    for insult in insults:
        if insult in message_string:
            print("Meanie Detected")
            return True
    return False

#THIS MESSES UP COMMANDS!
#https://discordpy.readthedocs.io/en/stable/api.html#discord.Message
@bot.event #talk to bot
async def on_message(message): #called when bot has recieves a message
    message_string = message.content.lower()
    print(message_string)
    author = get_name(message.author)

    #<@!807971461226692649> == @Dylan-Bot when typed 807972428855771167 == @Dylan-Bot when copied
    if '807971461226692649' in message_string or '807972428855771167' in message_string: 
        #greetings
        if is_greeting(message_string):
                await message.channel.send("Hello, " + author + "!")
        #insults
        if is_insult(message_string):
            await message.channel.send("That's not very nice, " + author + ". Lucky for you, I'm not programmed to feel emotion.")
          
    await bot.process_commands(message)


with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TOKEN']


bot.run(TOKEN)



#TODO: logging https://discordpy.readthedocs.io/en/latest/logging.html#logging-setup
#TODO: copy this quene format https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py