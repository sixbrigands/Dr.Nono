import discord
import json
import random
from discord.utils import get
from discord.ext import commands
from collections import OrderedDict
from table2ascii import table2ascii as t2a
import logging

# Set up logging

logger = logging.getLogger('discord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename='private/discord.log', encoding='utf-8', mode='w')
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# All commands must be prepended with '~'
bot = commands.Bot(command_prefix='~')

# What happens when bot connects to the server
@bot.event  #registers an event
async def on_ready(): #on ready called when bot has finish logging in
    print(f'{bot.user.name} has connected to Discord!')

#get author's real name, or Discord handle otherwise
def get_name(author):
    if ("(" in author.display_name): #check if nickname has real name, e.g. Username (Name)
        open_paren = author.display_name.index('(') + 1
        close_paren = author.display_name.index(')')
        return author.display_name[open_paren:close_paren]
    else:
        return str(author)[:-5]

# Helper methods for formatting
def bold(string):
    return "**" + string + "**"
def spoiler(string):
    return "||" + string + "||"
def code_block(string):
    return "```" + string + "```"

# Get member object from <@username> string
def get_user_id_from_mention(mention_string):
    return int(mention_string[3:-1])

# What Dr. NoNo says before listing your NoNo words
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

# Provide a list of all nono words a user has said with a fun picture
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
    no_nono_words_found = True
    for nono_word, count in nono_dict.items():
        if count > 0:
            no_nono_words_found = False
            table_body_list.append([nono_word, count])

    # If user has said no NoNo words, bail out
    if no_nono_words_found:
        logger.debug("User: " + get_name(offender) + " has said no NoNo words.")
        await ctx.channel.send("I can't believe it. " + get_name(offender) +" has never said a NoNo word!")
        return

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

# Is a user message a greeting?
def is_greeting(message_string):
    greetings = {"hi ", " hi", "hi,", "hello", "hey ", " hey", "good morning", "good day", "how's it going", "how are you", "what's up", "wassup", " sup", "sup,", "sup " "good evening", "good afternoon", "to meet you", "how've you been", "nice to see you", "long time no see", "ahoy", "howdy", "how are you"}
    for greeting in greetings:
        if greeting in message_string:
            print(greeting)
            if "hi" in greeting and not message_string.endswith("hi") and message_string[message_string.find('hi') + 2].isalpha():
                return False
            return True
    return False

# Is a user message an insult?
def is_insult(message_string):
    insults = {"fuck", "shitty", "suck", "damn", "smelly", "hate", "stink", "loser"}
    for insult in insults:
        if insult in message_string:
            return True
    return False

# What are the unforgivable NoNo words that must be called out when said?
ultimate_nono_alert = "🚨 ULTIMATE NONO ALERT 🚨\n"
ultimate_nono_dict = {
    'map': discord.Embed(title = ultimate_nono_alert, description = (bold("MAP") + ": Short for Minor Attracted Person, MAP refers to a person who is sexually attracted to children but does not sexually molest them.")),
    'chad':  discord.Embed(title = ultimate_nono_alert, description =  (bold("Chad") + ": Associated with the incel community and the website 4chan to refer stereotypical alpha males."))
}

# Respond to messages on text channels the bot can see
@bot.event 
async def on_message(message): #called when bot has recieves a message
    # Don't respond to the bot itself
    if message.author == bot.user:
        return

    print(message.content)
    message_string = message.content.lower()
    author = get_name(message.author)
    message_word_list = message.content.split()
    message_word_list_lower = message_string.split()

    # Respond to mentions of bot
    if str(bot.user.id) in message_string:
        #greetings
        if is_greeting(message_string):
            logger.info(author + "greeted me.")
            logger.info(message.content)
            await message.channel.send("Hello, " + author + "!")
        #insults
        if is_insult(message_string):
            logger.info(author + "insulted me.")
            logger.info(message.content)
            await message.channel.send("That's not very nice, " + author + ". Lucky for you, I'm not programmed to feel emotion.")
        #help
        if 'help' in message_word_list_lower:
            logger.info(author + "asked for help.")
            greeting_string = discord.Embed(title = "Greetings. I am Dr. NoNo", description = "I have compiled a list of all the shocking obscenities you've uttered here. "\
            + "\nTo see your own list, type ```~list```To someone else's, type: ```~list @username```")
            await message.channel.send(embed=greeting_string)
    
    # Call out those especially dirty NoNo words on sight
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

# Load the secret token that allows configuation of the bot
with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TOKEN']

# Start the bot
bot.run(TOKEN)
