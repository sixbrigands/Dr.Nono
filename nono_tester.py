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

# Guild_id{Members_id{word: NoNo_word}
nono_dict_by_member = {}
# Guild_id{NoNo_Words{}}
nono_dict_by_server = {}

# This dicts how the fun superlatives like 'filthiest_message', structured the same as the nono_dicts
superlatives_by_member = {}
superlatives_by_server = {}
# Build list of bad words for late dict insertion
nono_list = []
nono_set = set()
with open('private/bad_words.txt') as f:
        rough_list = f.readlines()
        for bad_word in rough_list:
            stripped_word = bad_word.strip()
            nono_list.append(stripped_word)
            nono_set.add(stripped_word)

# Scan a single message and update dicts with nono_words:
# TODO: I can't have the table be in code block and have the jump links working too. Maybe I just save the naughtiest message at the end  and link to that
async def load_message(message):
    if bot.user.id == message.author.id:
        return
    #strip out punctutation
    message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
    message_list = message_string.lower().split()
    # Count nono words in messages, add to server and member counts, save message with most nono words in it
    num_nono_words_in_message = 0
    most_nono_words_in_message = 0
    for word in nono_list:
        word_count = message_list.count(word)
        if word_count > 0:
            num_nono_words_in_message += word_count
            # Insert into nono_words_by_member
            if message.author.id in nono_dict_by_member[message.guild.id] and word in nono_dict_by_member[message.guild.id][message.author.id]:
                nono_dict_by_member[message.guild.id][message.author.id][word].update(message_list, message.jump_url)
            elif message.author.id in nono_dict_by_member[message.guild.id]:
                nono_dict_by_member[message.guild.id][message.author.id][word] = NoNo_Word(word, word_count, message.jump_url)
            # If the user ID in not present, add it 
            else:
                nono_dict_by_member[message.guild.id][message.author.id] = {word: NoNo_Word(word, word_count, message.jump_url)}
                superlatives_by_member[message.guild.id][message.author.id] = {
                    "filthiest_message_count": word_count,
                    "filthiest_message": message
                    }
            # Insert into nono_words_by_server
            # We assume the by_server dict has all guild names added during load_server
            if word in nono_dict_by_server[message.guild.id]:
                nono_dict_by_server[message.guild.id][word].update(message_list, message.jump_url)
            else:
                nono_dict_by_server[message.guild.id][word] = NoNo_Word(word, word_count, message.jump_url)
    # Check if this message has the most nono words of any one message written by a particular user, or by anyone on the server
    if num_nono_words_in_message > 0:
        if num_nono_words_in_message > superlatives_by_member[message.guild.id][message.author.id]['filthiest_message_count']:
            superlatives_by_member[message.guild.id][message.author.id]['filthiest_message'] = message
            superlatives_by_member[message.guild.id][message.author.id]['filthiest_message_count'] = num_nono_words_in_message
        if num_nono_words_in_message > superlatives_by_server[message.guild.id]['filthiest_message_count']:
            superlatives_by_server[message.guild.id]['filthiest_message'] = message
            superlatives_by_server[message.guild.id]['filthiest_message_count'] = num_nono_words_in_message


# Comb through channel messages after bot is added to it
async def load_channel(text_channel: discord.TextChannel):
    if bot.user not in text_channel.members:
        print('I am not allowed to load channel: ' + text_channel.name + ' into dicts!')
        return
    print('Inserting ' + text_channel.name + ' into dicts!') 
    logger.info('Inserting text channel: ' + text_channel.name + ' into dicts!')
    if bot.user in text_channel.members: # Check that bot has access to this channel
        async for message in text_channel.history(limit=None):
            await load_message(message)
        print("Done loading channel: " + text_channel.name)    

# Load all words and members currently on the server, add it to the guild dict
async def load_server(guild: discord.Guild):
    # Add guild_id to the top level of both dicts
    # Also init superlative dicts
    if guild.id not in nono_dict_by_server:
        nono_dict_by_member[guild.id] = {}
        nono_dict_by_server[guild.id] = {}
        superlatives_by_member[guild.id] = {}
        superlatives_by_server[guild.id] = {'filthiest_message_count': 0}
    print('Inserting all text channels on ' + guild.name + ' into dicts!') 
    logger.info('Inserting all text channels  on ' + guild.name + ' into dicts!') 
    for text_channel in guild.text_channels:
        await load_channel(text_channel)
    print("Done loading server: " + guild.name)


# What happens when the bot is fully connected and online
@bot.event  #registers an event
async def on_ready(): #on ready called when bot has finish logging in
    print(f'{bot.user.name} has connected to Discord!')
    for server in bot.guilds:
        await load_server(server)

# What happens when the bot joins a new server/guild
@bot.event
async def on_guild_join(guild):
    print("I joined the " + guild.name)
    await load_server(guild)


#get author's real name, or Discord handle otherwise
def get_name(author):
    try:
        if ("(" in author.display_name and ")" in author.display_name): #check if nickname has real name, e.g. Username (Name)
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
def hyperlink(string, link):
    return "[" + string + "](" + link + ")"

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
# Offender can be a member object or 'all'
def nono_prefix(offender, ctx):
    # Different prefix if offender is an entire server
    server = bold(ctx.guild.name)
    server_nono_prefixes = [
        server + ", look upon your sins...",
        "What a filthy place this is...",
        server + ", never have I seen a more wretched hive of scum and profanity",
        "This is clearly NOT a Christrian Minecraft server",
        "Shame on you all.",
        "I suppose I should have expected this. This is " + server + " after all"
    ]
    if offender == 'all':
        return " \n \n" + random.choice(server_nono_prefixes) + " \n"
    
    # IF offender is a member
    offender = bold(get_name(offender))
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

# Build table by user giver a user id number
def build_member_table(server_id: int, offender_id: int):
    # Return None if dict is empty
    if not nono_dict_by_member[server_id]:
        return None
    # If the offender isn't in the member dict, they haven't uttered a nono word
    if offender_id not in nono_dict_by_member[server_id]:
        return -1
    no_nono_words_found = True
    table_body_list = []
    # Loop through dict with word itself and the nono_word object
    for word, nono_word in nono_dict_by_member[server_id][offender_id].items():
        if nono_word.count > 0:
            no_nono_words_found = False
            # Caculate the percentage of utterances over the user alone, and over the entire server
            serverwide_percentage = str(round(nono_word.count / nono_dict_by_server[server_id][word].count * 100, 2)) + "%"
            table_body_list.append([word, nono_word.count, serverwide_percentage])
    # Return None if dict has no nono words
    if no_nono_words_found:
        return -1
    nono_table = t2a(
            header=["NoNo_Word", "Utterances", "Serverwide_Percentage"],
            body=table_body_list
            ) 
    return nono_table

# Build a table for an entire server given a guild/server id
def build_server_table(server_id: int):
    # If no words exist for the server, return -1
    if not nono_dict_by_server[server_id]:
        return -1
    no_nono_words_found = True
    table_body_list = []
    # Loop through dict with word itself and the nono_word object
    for word, nono_word in nono_dict_by_server[server_id].items():
        if nono_word.count > 0:
            no_nono_words_found = False
            # Embed a link to a random message with the nono word
            table_body_list.append([word, nono_word.count])
    # Return None if dict has no nono words
    if no_nono_words_found:
        return -1
    nono_table = t2a(
            header=["NoNo_Word", "Utterances"],
            body=table_body_list
            ) 
    return nono_table

# Provide a list of all nono words a user has said with a fun picture
# TODO: When provided with @everyone, print the server stats
# TODO: look at listing swear count ratio against average
# TODO: Look at compairing two members
@bot.command()
async def test(ctx, offender=None):
    bot_id = int(bot.user.id)
    nono_table = None
    # Who's nono words am I listing? Without an argument, default to whoever made the command
    if offender == None:
        offender = ctx.author
        nono_table = build_member_table(offender.guild.id, offender.id)
    # Dr. Nono can't be the offender!
    elif bot_id == get_user_id_from_mention(offender):
        await ctx.channel.send("Do not question Dr. Nono's character, " + get_name(ctx.author) + ".")
        return
    # If arg is @everyone, build a table server
    elif offender == 'all':
        nono_table = build_server_table(ctx.guild.id)
        # If the entire server has no documented nono words... IDK dude just give up
        if nono_table == -1:
            logger.debug("The entire server known as: " + ctx.guild.name + " has said no NoNo words.")
            await ctx.channel.send("This.. this is impossible... " + bold(ctx.guild.name) +" has no history of nono words!")
            return
    # If arg provided, get the user from the user_id
    else:
        try:
            offender = ctx.guild.get_member(get_user_id_from_mention(offender)) # This returns a member object with nickname
            if offender == None:
                raise Exception("Offender not found")
            nono_table = build_member_table(offender.guild.id, offender.id)    
            # If user has said no NoNo words, bail out
            if nono_table == -1:
                logger.debug("User: " + get_name(offender) + " has said no NoNo words.")
                await ctx.channel.send("I can't believe it. " + bold(get_name(offender)) +" has never said a NoNo word!")
                return
        except Exception as e:
            print(e)
            logger.debug("I can't find this offender:")
            logger.debug(offender)
            await ctx.channel.send("I couldn't find that user, " + get_name(ctx.author) + ", try again.")
            return
    
    
    # Send picture and nono_word table to channel
    with open('private/nono.gif', 'rb') as f:
        nono_gif = discord.File(f)
        await ctx.channel.send(file=nono_gif) 
    # print nono table here:
    nono_string = discord.Embed(title = nono_prefix(offender, ctx), description = code_block(nono_table))
    await ctx.channel.send(embed = nono_string)

# Compare two members, or another member and the author
@bot.command()
async def compare(ctx, offender=None):
    pass

# Show the worst message a user has posted, in terms of nono words
@bot.command()
async def worst(ctx, offender=None):
    entire_server = False
    message = ''
    prefix = ''
    if offender == None:
        offender = ctx.author
    elif offender == "all":
        entire_server = True
    else:
        try: 
            offender = ctx.guild.get_member(get_user_id_from_mention(offender))
            if offender == None:
                raise Exception("Offender not found")
        except Exception as e:
            print(e)
            logger.debug("I can't find this offender:")
            logger.debug(offender)
            await ctx.channel.send("I couldn't find that user, " + get_name(ctx.author) + ", try again.")
            return   
    if entire_server:
        if 'filthiest_message' not in superlatives_by_server[ctx.guild.id]:
            await ctx.channel.send("This.. this is impossible... " + bold(ctx.guild.name) +" has no history of nono words!")
            return
        message = superlatives_by_server[ctx.guild.id]['filthiest_message']
        prefix = 'Worst message posted on ' + ctx.guild.name + ':\n'
    else:
        if offender.id not in superlatives_by_member[ctx.guild.id]:
            await ctx.channel.send("I can't believe it. " + bold(get_name(offender)) +" has never said a NoNo word!")
            return
        message = superlatives_by_member[offender.guild.id][offender.id]['filthiest_message']
        prefix = get_name(offender) + "'s worst message:\n"
    #message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
    message_word_list = message.content.split()
    highlighted_message = "> "
    for word in message_word_list:
        clean_word = ''.join(c for c in word if c.isalpha() or c == ' ').lower()
        if clean_word in nono_set:
            highlighted_message += " " + bold(word)
        else:
            highlighted_message += " " + word

    suffix = "~" + get_name(message.author) + ", " + message.created_at.strftime("%d%b%Y").upper()
    suffix = hyperlink(suffix, message.jump_url)
    embed = discord.Embed(title = prefix, description = highlighted_message + "\n" + suffix)
    await ctx.channel.send(embed = embed)

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
    await load_message(message)
          
    # This allows commands to be used along with on_message events
    await bot.process_commands(message)

# Load the secret token that allows configuation of the bot
with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TEST-TOKEN']

# Start the bot
bot.run(TOKEN)


#TODO Consider adding 'jump links' somewhere to give an example of a nono_word
#https://stackoverflow.com/questions/64527464/clickable-link-inside-message-discord-py
#These can be embedded in messages.. but only within embeds
#https://stackoverflow.com/questions/63863871/discord-py-how-to-go-through-channel-history-and-search-for-a-specific-message

#TODO put starts or number 1's around someone's top nono word
#TODO make a nono word object to hold the word, count, link, ratio, etc