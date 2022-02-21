from ast import Raise
import string
import discord
import json
import random
from discord.utils import get
from discord.ext import commands
from paramiko import Channel
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

# All commands must be prepended with '~'
bot = commands.Bot(command_prefix='~', intents=intents, chunk_guilds_at_startup=True)

# Members{NoNo_Words{}}
nono_dict_by_member = {}
# Guilds{NoNo_Words{}}
nono_dict_by_server = {}
# Build list of bad words for late dict insertion
nono_list = []
with open('private/bad_words.txt') as f:
        rough_list = f.readlines()
        for bad_word in rough_list:
            nono_list.append(bad_word.strip())

# # Add a member to the dictionary and tally their nono words
# def load_member(guild: discord.Guild, member: discord.Member):
#     print('Inserting ' + get_name(member) + ' into dicts!') 
#     logger.info('Inserting ' + get_name(member) + ' into dicts!')
#     nono_dict_by_member[member.id] = {}
#     for text_channel in guild.text_channels:
#         print("scanning ", text_channel.name)
#         if bot.user in text_channel.members and member in text_channel.members: # Check that bot and member is in this channel
#             for message in text_channel.history():
#                 #strip out punctutation
#                 message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
#                 message_list = message_string.lower().split()
#                 # Count nono words in messages, add to server and member counts
#                 for word in nono_list:
#                     if word in nono_dict_by_member[member.id]:
#                         nono_dict_by_member[member.id][word].update(message_list, message_list, message.jump_url)
#                     else:
#                         nono_dict_by_member[member.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)
#                     if word in nono_dict_by_server[guild.id]:
#                         nono_dict_by_server[guild.id][word].update(message_list, message_list, message.jump_url)
#                     else:
#                         nono_dict_by_server[guild.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)

# Scan a single message and update dicts with nono_words:
def load_message(message_list, author: discord.member):
    for word in nono_list:
        if word in nono_dict_by_member[author.id]:
            nono_dict_by_member[author.id][word].update(message_list, message_list, message.jump_url)
        else:
            nono_dict_by_member[author.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)
        if word in nono_dict_by_server[author.guild.id]:
            nono_dict_by_server[author.guild.id][word].update(message_list, message_list, message.jump_url)
        else:   
            nono_dict_by_server[author.guild.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)

# Comb through channel messages after bot is added to it
def load_channel(text_channel: discord.TextChannel):
    print('Inserting ' + text_channel.name + ' into dicts!') 
    logger.info('Inserting ' + text_channel.name + ' into dicts!')
    if bot.user in text_channel.members: # Check that bot has access to this channel
        for message in text_channel.history():
            #strip out punctutation
            message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
            message_list = message_string.lower().split()
            # Count nono words in messages, add to server and member counts
            for word in nono_list:
                if word in nono_dict_by_member[message.author.id]:
                    nono_dict_by_member[message.author.id][word].update(message_list, message_list, message.jump_url)
                else:
                    nono_dict_by_member[message.author.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)
                if word in nono_dict_by_server[message.author.guild.id]:
                    nono_dict_by_server[message.author.guild.id][word].update(message_list, message_list, message.jump_url)
                else:
                    nono_dict_by_server[message.author.guild.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)     


# Load all words and members currently on the server, add it to the guild dict
def load_server(guild: discord.Guild):
    print('Inserting all members on' + guild.name + ' into dicts!') 
    logger.info('Inserting all members on' + guild.name + ' into dicts!') 
    nono_dict_by_server[guild.id] = {}
    for text_channel in guild.text_channels:
        print("scanning ", text_channel.name)
        if bot.user in text_channel.members: # Check that bot has access to this channel
            for message in text_channel.history():
                #strip out punctutation
                message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
                message_list = message_string.lower().split()
                # Count nono words in messages, add to server and member counts
                for word in nono_list:
                    if word in nono_dict_by_member[message.author.id]:
                        nono_dict_by_member[message.author.id][word].update(message_list, message_list, message.jump_url)
                    else:
                        nono_dict_by_member[message.author.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)
                    if word in nono_dict_by_server[guild.id]:
                        nono_dict_by_server[guild.id][word].update(message_list, message_list, message.jump_url)
                    else:
                        nono_dict_by_server[guild.id][word] = NoNo_Word(message_list, message_list.count(word), message.jump_url)     


# What happens when bot connects to the server
@bot.event  #registers an event
async def on_ready(): #on ready called when bot has finish logging in
    print(f'{bot.user.name} has connected to Discord!')
    for server in bot.guilds:
        load_server(server)
    
@bot.event\
async def on bot is added to server..(server):
    load_server(server)


@bot.event
async def on_group_join(channel, user)¶

    load_channel(text_channel)
    # this will prob need to be added  to ~list, a check that I've been added to new channels. Will also need a channels dict to check for new additions
    
nono_dict_by_server = {}
    #TODO: Write a function to list nono words for member, do all members here and save to dict of a dict

# When a user joins the server, add
@bot.event
async def on_member_join(member):
    load_member(member)


#get author's real name, or Discord handle otherwise
def get_name(author):
    try:
        if ("(" in author.display_name): #check if nickname has real name, e.g. Username (Name)
            open_paren = author.display_name.index('(') + 1
            close_paren = author.display_name.index(')')
            return author.display_name[open_paren:close_paren]
        else:
            return str(author)[:-5]
    except Exception as e:
        print("get_name failed")
        print(e)
        return None

# Helper methods for formatting
def bold(string):
    return "**" + string + "**"
def spoiler(string):
    return "||" + string + "||"
def code_block(string):
    return "```" + string + "```"

# Get member object from <@username> string
def get_user_id_from_mention(mention_string):
    if not mention_string.startswith('<'):
        return None
    clean_string = ''.join(c for c in mention_string if c.isnumeric() or c == ' ')
    try:
        user_id_int = int(clean_string)
        return user_id_int
    except:
        return None 

# What Dr. NoNo says before listing your NoNo words
def nono_prefix(offender):
    nono_prefixes = [
        "Be it known that the criminal, " + offender + ", has committed the following offenses:",
        "My my, " + offender + ", such language...",
        offender + "! You're due for a donation to the swear jar",
        "This is a Christrian Minecraft server, " + offender,
        offender + "! For shame.",
        "Hmm, " + offender + "... why am I not surprised?",
        "I've got my eye on you, " + offender + "...",
    ]
    return " \n \n" + random.choice(nono_prefixes) + " \n"

# Build a table with provided dict
def build_table(nono_dict: dict):
    nono_table = t2a(
            header=["NoNo_Word", "Utterances"],
            body=table_body_list
            ) 
    #nono_string = table_prefix + nono_table
    nono_string = nono_table
    print(nono_string)
    nono_string = discord.Embed(title = table_prefix, description = code_block(nono_table))

# Provide a list of all nono words a user has said with a fun picture
# TODO: When provided with @everyone, print the server stats
# TODO: look at listing swear count ratio against average
# TODO: Look at compairing two members
@bot.command()
async def list(ctx, offender=None):
    bot_id = int(bot.user.id)
    
    # Who's nono words am I listing? Without an argument, default to whoever made the command
    if offender == None:
        offender = ctx.author
    # Dr. Nono can't be the offender!
    elif bot_id == get_user_id_from_mention(offender):
        await ctx.channel.send("Do not question Dr. Nono's character, " + get_name(ctx.author) + ".")
        return
    # If arg is @everyone, build a table server
    elif offender == @everyone:
        nono_table = build_table(nono_dict_by_server)
    # If arg provided, get the user from the user_id
    else:
        try:
            offender = ctx.guild.get_member(get_user_id_from_mention(offender)) # This returns a member object with nickname
            if offender == None:
                Raise: Exception("Offender not found")
            nono_table = build_table(nono_dict_by_member)
        except Exception as e:
            print(e)
            logger.debug("I can't find this offender:")
            logger.debug(offender)
            await ctx.channel.send("I couldn't find that user, " + get_name(ctx.author) + ", try again.")
            return



    
    # build table here, if none there are no nono words

    # If user has said no NoNo words, bail out
    if nono_table == None:
        logger.debug("User: " + get_name(offender) + " has said no NoNo words.")
        await ctx.channel.send("I can't believe it. " + bold(get_name(offender)) +" has never said a NoNo word!")
        return

    # Send picture and nono_word table to channel
    with open('private/nono.gif', 'rb') as f:
        nono_gif = discord.File(f)
        await ctx.channel.send(file=nono_gif) 


    # print nono table here:

    await ctx.channel.send(embed = nono_string)



# Is a user message a greeting?
def is_greeting(message_string):
    greetings = {"hi ", " hi", "hello", "hey ", " hey", "good morning", "good day", "hows it going", "how are you", "whats up", "wassup", " sup", "sup,", "sup " "good evening", "good afternoon", "to meet you", "howve you been", "nice to see you", "long time no see", "ahoy", "howdy", "how are you"}
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

    message_string_clean = ''.join(c for c in message.content if c.isalpha() or c == ' ').lower()
    print(message_string_clean)
    message_word_list = message.content.split()
    author = get_name(message.author)
    
    # Call out those especially dirty NoNo words on sight
    for ultimate_nono_word in ultimate_nono_dict.keys():
        highlighted_message = "> "
        if ultimate_nono_word in message_string_clean.split() or (ultimate_nono_word + 's') in message_string_clean.split():
            for word in message_word_list:
                clean_word = ''.join(c for c in word if c.isalpha() or c == ' ').lower()
                if clean_word == ultimate_nono_word or clean_word == (ultimate_nono_word + 's'):
                    highlighted_message += " " + bold(word)
                else:
                    highlighted_message += " " + word
            with open('private/ultimate_nono_alert.gif', 'rb') as f:
                nono_gif = discord.File(f)
                await message.channel.send(file=nono_gif) 
            await message.channel.send(author + ' said:\n' + highlighted_message)
            await message.channel.send(embed = ultimate_nono_dict[ultimate_nono_word])

    # Add message nono_words to dicts
    
    # Respond to mentions of bot
    if str(bot.user.id) in message.content:
        #help
        if 'help' in message_string_clean:
            logger.info(author + "asked for help.")
            greeting_string = discord.Embed(title = "Greetings, I am Dr. NoNo", description = "I have compiled a list of all the shocking obscenities you've uttered here. "\
            + "\nTo see your own list, type: ```~list```To see someone else's, type: ```~list @username```")
            await message.channel.send(embed=greeting_string)
        #greetings
        elif is_greeting(message_string_clean):
            logger.info(author + "greeted me.")
            logger.info(message.content)
            await message.channel.send("Hello, " + author + "!")
        #insults
        elif is_insult(message_string_clean):
            logger.info(author + "insulted me.")
            logger.info(message.content)
            await message.channel.send("That's not very nice, " + author + ". Lucky for you, I'm not programmed to feel emotion.")

    # Scan the message for nono words and add them to the dicts
    load_message(message_word_list)
          
    # This allows commands to be used along with on_message events
    await bot.process_commands(message)

# Load the secret token that allows configuation of the bot
with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TOKEN']

# Start the bot
bot.run(TOKEN)


#TODO Consider adding 'jump links' somewhere to give an example of a nono_word
#https://stackoverflow.com/questions/64527464/clickable-link-inside-message-discord-py
#These can be embedded in messages.. but only within embeds
#https://stackoverflow.com/questions/63863871/discord-py-how-to-go-through-channel-history-and-search-for-a-specific-message

#TODO put starts or number 1's around someone's top nono word
#TODO make a nono word object to hold the word, count, link, ratio, etc