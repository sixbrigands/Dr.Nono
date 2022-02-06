import discord
import time
import asyncio
import json
import re
import random
from discord.utils import get
from discord.ext import commands
from collections import OrderedDict
from matplotlib import table
from table2ascii import table2ascii as t2a, PresetStyle


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

def spoiler(string):
    return "||" + string + "||"

def code_block(string):
    return "```" + string + "```"

def get_user_id_from_mention(mention_string):
    return int(mention_string[3:-1])

def nono_prefix(offender):
    nono_prefixes = [
        "Be it known that the criminal," + offender + " has committed the following offenses:",
        "My my, " + offender + ", such language...",
        offender + "! You're due for a donation to the swear jar",
        "This is a Christrian Minecraft server, " + offender,
        offender + "! For shame.",
        "Hmm, " + offender + "... why am I not surprised?"
    ]
    return " \n \n" + random.choice(nono_prefixes) + " \n"

# Provide a list of all nono words said and fun picture
#TODO Add second argument 'offender', default to author
@bot.command()
async def list(ctx, offender=None):
    print("bot id:")
    print(bot.user.id)
    print("offender id")
    print(offender)
    nono_dict = OrderedDict()
    with open('bad_words.txt') as f:
        nono_list = f.readlines()
        for bad_word in nono_list:
            nono_dict[bad_word.strip()] = 0

    # Who's nono words am I listing? Withou an argument, default to whoever made the command
    if offender == None:
        offender = ctx.author
    # Dr. Nono can't be the offender!
    elif get_user_id_from_mention(offender) == bot.user.id:
        await ctx.channel.send("Do not question Dr. Nono's character, " + get_name(ctx.author) + ".")
        return
    # If arg provided, get the user from the user_id
    else:
        try:
            print("Getting member fom mention arg")
            print(offender)
            print(get_user_id_from_mention(offender))
            offender = bot.get_user(get_user_id_from_mention(offender))
            print(offender)
        except:
            print(offender)
            await ctx.channel.send("I couldn't find that user, " + get_name(ctx.author) + ", try again.")
            return
    
    nono_table = ''
    table_prefix = nono_prefix(bold(get_name(offender)))
    table_body_list = []
    print('listing nono words!')
    for text_channel in ctx.guild.text_channels:
        print(text_channel)
        #print(text_channel.permissions_for(bot.get_user(bot.user.id)))
        print(text_channel.members)
        if bot.user in text_channel.members:
            async for message in text_channel.history(limit=1000):
                if message.author == offender:
                    message_list = message.content.lower().split()
                    for nono_word, count in nono_dict.items():
                        nono_dict[nono_word] = count + message_list.count(nono_word)
    for nono_word, count in nono_dict.items():
        if count > 0:
            hidden_word = nono_word
            table_body_list.append([hidden_word, count])

    # Send picture and nono_word table to channel
    with open('private/nono.gif', 'rb') as f:
        nono_gif = discord.File(f)
        await ctx.channel.send(file=nono_gif) 
    nono_table = t2a(
                header=["NoNo_Word", "Utterances"],
                body=table_body_list
            ) 
    #nono_string = table_prefix + nono_table
    nono_string = nono_table
    print(nono_string)
    nono_string = discord.Embed(title = table_prefix, description = code_block(nono_table))
    await ctx.channel.send(embed = nono_string)

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
async def poll(ctx):
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
    greetings = {"hi ", " hi", "hi," "hello", "hey ", " hey", "good morning", "good day", "how's it going", "how are you", "what's up", "wassup", " sup", "sup,", "sup " "good evening", "good afternoon", "to meet you", "how've you been", "nice to see you", "long time no see", "ahoy", "howdy", "how are you"}
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

ultimate_nono_alert = "🚨 ULTIMATE NONO ALERT 🚨\n"
ultimate_nono_dict = {
    'map': discord.Embed(title = ultimate_nono_alert, description = (bold("MAP") + ": Short for Minor Attracted Person, MAP refers to a person who is sexually attracted to children but does not sexually molest them.")),
    'chad':  discord.Embed(title = ultimate_nono_alert, description =  (bold("Chad") + ": Associated with the incel community and the website 4chan to refer stereotypical alpha males."))
}

# Respond to messages on text channels the bot can see
@bot.event 
async def on_message(message): #called when bot has recieves a message
    message_string = message.content.lower()
    author = get_name(message.author)
    message_word_list = message.content.split()
    message_word_list_lower = message_string.split()

    # bot.user == the bot itself
    # Respond to mentions of bot
    if str(bot.user.id) in message_string:
        #greetings
        if is_greeting(message_string):
                await message.channel.send("Hello, " + author + "!")
        #insults
        if is_insult(message_string):
            await message.channel.send("That's not very nice, " + author + ". Lucky for you, I'm not programmed to feel emotion.")

    for ultimate_nono_word in ultimate_nono_dict.keys():
        highlighted_message = "> "
        if ultimate_nono_word in message_word_list_lower:
            for word in message_word_list:
                if word.lower() == ultimate_nono_word:
                    highlighted_message += " " + bold(word)
                else:
                    highlighted_message += " " + word
            with open('private/ultimate_nono_alert.gif', 'rb') as f:
                nono_gif = discord.File(f)
                await message.channel.send(file=nono_gif) 
            await message.channel.send(highlighted_message)
            await message.channel.send(embed = ultimate_nono_dict[ultimate_nono_word])
          
        
    # This allows commands to be used along with on_message events
    await bot.process_commands(message)


with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TOKEN']


bot.run(TOKEN)



#TODO: logging https://discordpy.readthedocs.io/en/latest/logging.html#logging-setup
#TODO: copy this quene format https://github.com/Carberra/discord.py-music-tutorial/blob/master/bot/cogs/music.py