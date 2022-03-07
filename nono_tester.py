from ast import Raise
import string
import discord
import json
import random
from discord.utils import get
from discord.ext import commands
from table2ascii import PresetStyle, table2ascii as t2a
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
# Guild_id{word: NoNo_word}
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
async def load_message(message):
    if bot.user.id == message.author.id:
        return
    #strip out punctutation
    message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ' or c == '\n')
    message_list = message_string.lower().split()
    # Count nono words in messages, add to server and member counts, save message with most nono words in it
    num_nono_words_in_message = 0
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
                    "filthiest_message": message,
                    'total_nono_words' : 0,
                    'favorite_nono_word_count': 0
                    }
            # Insert into nono_words_by_server
            # We assume the by_server dict has all guild names added during load_server
            if word in nono_dict_by_server[message.guild.id]:
                nono_dict_by_server[message.guild.id][word].update(message_list, message.jump_url)
            else:
                nono_dict_by_server[message.guild.id][word] = NoNo_Word(word, word_count, message.jump_url)
            # Update favorite nono word:
            if nono_dict_by_member[message.guild.id][message.author.id][word].count > superlatives_by_member[message.guild.id][message.author.id]['favorite_nono_word_count']:
                superlatives_by_member[message.guild.id][message.author.id]['favorite_nono_word'] = word
                superlatives_by_member[message.guild.id][message.author.id]['favorite_nono_word_count'] = nono_dict_by_member[message.guild.id][message.author.id][word].count
            if nono_dict_by_server[message.guild.id][word].count > superlatives_by_server[message.guild.id]['favorite_nono_word_count']:
                superlatives_by_server[message.guild.id]['favorite_nono_word'] = word
                superlatives_by_server[message.guild.id]['favorite_nono_word_count'] = nono_dict_by_server[message.guild.id][word].count
    # Check if this message has the most nono words of any one message written by a particular user, or by anyone on the server
    if num_nono_words_in_message > 0:
        if num_nono_words_in_message > superlatives_by_member[message.guild.id][message.author.id]['filthiest_message_count']:
            superlatives_by_member[message.guild.id][message.author.id]['filthiest_message'] = message
            superlatives_by_member[message.guild.id][message.author.id]['filthiest_message_count'] = num_nono_words_in_message
        if num_nono_words_in_message > superlatives_by_server[message.guild.id]['filthiest_message_count']:
            superlatives_by_server[message.guild.id]['filthiest_message'] = message
            superlatives_by_server[message.guild.id]['filthiest_message_count'] = num_nono_words_in_message
        #Update total_nono_words for both superlative dicts
        superlatives_by_member[message.guild.id][message.author.id]['total_nono_words'] += num_nono_words_in_message
        superlatives_by_server[message.guild.id]['total_nono_words'] += num_nono_words_in_message

# Comb through channel messages after bot is added to it
async def load_channel(text_channel: discord.TextChannel):
    if bot.user not in text_channel.members:
        print('I am not allowed to load channel: ' + text_channel.name + ' into dicts!')
        return
    print('Inserting text channel: ' + text_channel.name + ' into dicts!') 
    logger.info('Inserting text channel: ' + text_channel.name + ' into dicts!')
    if bot.user in text_channel.members: # Check that bot has access to this channel
        report_rate    = 500
        report_counter = 0
        report_total   = 0
        async for message in text_channel.history(limit=None):
            await load_message(message)
            report_counter += 1
            if report_counter >= report_rate:
                report_total += report_counter
                print(str(report_total) +" messages loaded so far for channel " + text_channel.name)
                report_counter = 0
        print("Done loading channel: " + text_channel.name)    

# Load all words and members currently on the server, add it to the guild dict
async def load_server(guild: discord.Guild):
    # Add guild_id to the top level of both dicts
    # Also init superlative dicts
    if guild.id not in nono_dict_by_server:
        nono_dict_by_member[guild.id] = {}
        nono_dict_by_server[guild.id] = {}
        superlatives_by_member[guild.id] = {}
        superlatives_by_server[guild.id] = {
            'filthiest_message_count' : 0,
            'total_nono_words'        : 0,
            'favorite_nono_word_count': 0
            }
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
    print("DONE LOADING ALL SERVERS")

# What happens when the bot joins a new server/guild
@bot.event
async def on_guild_join(guild):
    print("I joined the " + guild.name)
    await load_server(guild)

# When Channel permissions change, and the bot is added, load that channel
# Before = the channel previously, and After = current channel
@bot.event
async def on_guild_channel_update(before, after):
    if bot.user not in before.members and bot.user in after.members:
        print("Dr. NoNo has joined a new channel, " + after.name)
        await load_channel(after)

#TODO Fill this is for role updates that give access to new channels
# Before = the member object before, and After = current memeber object
# Will likely need a "channels I have access to" dict
async def on_member_update(before, after):
    # Bail out if this isn't the bot
    if before.id != bot.user.id:
        return


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
def trophy(string):
    return '🏆 ' + string + ' 🏆'
def number_one(string):
    return string + ' #1'

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
# Offender2 is only used for comparisons
def nono_prefix(ctx, offender1: discord.Member, offender2: discord.Member = None):
    # If the offender is an entire server:
    if offender1 == 'all':
        server = bold(ctx.guild.name)
        server_nono_prefixes = [
            server + ", look upon your sins...",
            "What a filthy place this is...",
            server + ", never have I seen a more wretched hive of scum and profanity",
            "This is clearly NOT a Christrian Minecraft server",
            "Shame on you all.",
            "I suppose I should have expected this. This is " + server + " after all"
        ]
        return " \n \n" + random.choice(server_nono_prefixes) + " \n"
    # If we're comparing two offenders:
    elif offender2 != None:
        offender1 = bold(get_name(offender1))
        offender2 = bold(get_name(offender2))
        compare_prefixes = [
            offender1 + " vs  " + offender2,
            "Let's compare " + offender1 + " and " + offender2
        ]
        return " \n \n" + random.choice(compare_prefixes) + " \n"   
    # Finally, if we're just doing a list for one member:
    offender1 = bold(get_name(offender1))
    nono_prefixes = [
        "Be it known that the criminal, " + offender1 + ", has committed the following offenses:",
        "My my, " + offender1 + ", such language...",
        offender1 + "! You're due for a donation to the swear jar",
        "This is a Christrian Minecraft server, " + offender1,
        offender1 + "! For shame.",
        "Hmm, " + offender1 + "... why am I not surprised?",
        "I've got my eye on you, " + offender1 + "...",
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
    member_total = superlatives_by_member[server_id][offender_id]['total_nono_words']
    server_total = superlatives_by_server[server_id]['total_nono_words']
    # Loop through dict with word itself and the nono_word object
    for word, nono_word in nono_dict_by_member[server_id][offender_id].items():
        if nono_word.count > 0:
            no_nono_words_found = False
            # Caculate the percentage of utterances over the user alone, and over the entire server
            serverwide_percentage = str(round(nono_word.count / nono_dict_by_server[server_id][word].count * 100, 2)) + "%"
            # Leave out personal percentage for now to save space
            #personal_percentage = str(round(nono_word.count / member_total * 100, 2)) + "%"
            if word == superlatives_by_member[server_id][offender_id]['favorite_nono_word']:
                word = number_one(word)
            table_body_list.append([word, nono_word.count, serverwide_percentage])
    # Return None if dict has no nono words
    if no_nono_words_found:
        return -1
    total_serverwide_percentage = str(round(member_total/ server_total * 100, 2)) + "%"
    footer = ["Totals:", member_total, total_serverwide_percentage]
    nono_table = t2a(
            header=["NoNo Word", "#", "Server%"],
            body=table_body_list,
            footer = footer,
            style = PresetStyle.minimalist
            ) 
    return nono_table

# Build a table for an entire server given a guild/server id
def build_server_table(server_id: int):
    # If no words exist for the server, return -1
    if not nono_dict_by_server[server_id]:
        return -1
    no_nono_words_found = True
    table_body_list = []
    server_total = superlatives_by_server[server_id]['total_nono_words']
    # Loop through dict with word itself and the nono_word object
    for word, nono_word in nono_dict_by_server[server_id].items():
        if nono_word.count > 0:
            no_nono_words_found = False
            server_percentage = str(round(nono_word.count / server_total * 100, 2)) + "%"
            if word == superlatives_by_server[server_id]['favorite_nono_word']:
                word = number_one(word)
            table_body_list.append([word, nono_word.count, server_percentage])
    # Return None if dict has no nono words
    if no_nono_words_found:
        return -1
    footer = ["Totals:", server_total, "100.0%"]
    nono_table = t2a(
            header=["NoNo Word", "#", "%"],
            body=table_body_list,
            footer = footer,
            style = PresetStyle.minimalist
    )
    return nono_table

# Provide a list of all nono words a user has said with a fun picture
@bot.command()
async def list(ctx, offender=None):
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
    # print nono table here
    embed = discord.Embed(title = nono_prefix(ctx, offender), description = code_block(nono_table))
    # If embed is too large (max is 6000 char), write to text file and send to channel
    if len(embed) > 5999 or len(code_block(nono_table)) > 4095:
        print("Embed too large at " + str(len(embed)))
        with open('list.txt', 'w') as f:
            f.write(nono_table)
        with open('list.txt', 'r') as r:
            list_txt = discord.File(r)
            await ctx.channel.send(nono_prefix(ctx, offender))
            await ctx.channel.send(file=list_txt) 
        return
    await ctx.channel.send(embed = embed)

# Show the worst message a user has posted, in terms of nono words
@bot.command()
async def worst(ctx, offender=None):
    entire_server = False
    message = ''
    prefix = ''
    num_nonos = 0
    if offender == None:
        offender = ctx.author
    elif bot.user.id == get_user_id_from_mention(offender):
        await ctx.channel.send("Do not question Dr. Nono's character, " + get_name(ctx.author) + ".")
        return
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
        num_nonos = superlatives_by_server[ctx.guild.id]['filthiest_message_count']
    else:
        if offender.id not in superlatives_by_member[ctx.guild.id]:
            await ctx.channel.send("I can't believe it. " + bold(get_name(offender)) +" has never said a NoNo word!")
            return
        message = superlatives_by_member[offender.guild.id][offender.id]['filthiest_message']
        prefix = get_name(offender) + "'s worst message:\n"
        num_nonos = superlatives_by_member[ctx.guild.id][offender.id]['filthiest_message_count']
    #message_string = ''.join(c for c in message.content if c.isalpha() or c == ' ')
    message_word_list = message.content.split()
    highlighted_message = "> "
    for word in message_word_list:
        clean_word = ''.join(c for c in word if c.isalpha() or c == ' ' or c == '\n').lower()
        if clean_word in nono_set:
            highlighted_message += " " + bold(word)
        else:
            highlighted_message += " " + word

    suffix = "~" + get_name(message.author) + ", " + message.created_at.strftime("%d%b%Y").upper()
    suffix = hyperlink(suffix, message.jump_url)
    postfix = str(num_nonos) + " NoNos"
    description = highlighted_message + "\n" + suffix + "\n" + postfix
    embed = discord.Embed(title = prefix, description = description)
    if len(embed) > 5999 or len(description) > 4095:
        print("Embed too large at " + str(len(embed)))  
        with open('worst.txt', 'w+') as f:
            f.write(message.content)
        with open('worst.txt', 'r') as r:
            worst_txt = discord.File(r)
            await ctx.channel.send(bold(prefix))
            await ctx.channel.send(file=worst_txt)
            suffix_embed = discord.Embed(description="\n" + suffix + "\n" + postfix)
            await ctx.channel.send(embed=suffix_embed)
        return
    await ctx.channel.send(embed = embed)

# Show the worst message a user has posted, in terms of nono words
@bot.command()
async def compare(ctx, offender1 = None, offender2 = None):
    # What if user doesn't provide any args?
    if offender1 == None:
        await ctx.channel.send('Please specify at least one member. Type "~explain compare" for details.')
        return
    # Comparing to a user to themselves is pointless
    if offender1 == offender2:
        await ctx.channel.send('Please provide at least 2 different members for comparison.')
        return
    if str(bot.user.id) in str(offender1) or str(bot.user.id) in str(offender2):
        await ctx.channel.send('Dr. NoNo is incomparable.')
        return
    # if only one user is provided, the other is the author
    elif offender2 == None:
        # Comparing to a user to themselves is pointless
        if str(ctx.author.id) in str(offender1):
            await ctx.channel.send('Please provide at least 2 different members for comparison.')
            return
        offender2 = ctx.guild.get_member(get_user_id_from_mention(offender1))
        offender1 = ctx.author
    # Otherwise just try and get both provided offenders
    else:
        try:
            offender1 = ctx.guild.get_member(get_user_id_from_mention(offender1))
            if offender1 == None:
                raise Exception("Offender1 not found")
        except Exception as e:
            print(e)
            logger.debug("I can't find this offender:")
            logger.debug(offender1)
            await ctx.channel.send("I couldn't find the first user, " + get_name(ctx.author) + ", try again.")
            return   
        try:
            offender2 = ctx.guild.get_member(get_user_id_from_mention(offender2))
            if offender1 == None:
                raise Exception("Offender1 not found")
        except Exception as e:
            print(e)
            logger.debug("I can't find this offender:")
            logger.debug(offender1)
            await ctx.channel.send("I couldn't find the second user, " + get_name(ctx.author) + ", try again.")
            return  
    # Check if either offender has no nono words:
    if offender1.id not in nono_dict_by_member[ctx.guild.id] and offender2.id not in nono_dict_by_member[ctx.guild.id]:
        await ctx.channel.send("Both users have never said a NoNo word! It's a tie!")
        return
    elif offender1.id not in nono_dict_by_member[ctx.guild.id]:
        await ctx.channel.send(bold(get_name(offender1)) + " has never said a NoNo word! " + bold(get_name(offender2)) + " wins by default.")
        return
    elif offender2.id not in nono_dict_by_member[ctx.guild.id]:
        await ctx.channel.send(bold(get_name(offender2)) + " has never said a NoNo word! " + bold(get_name(offender1)) + " wins by default.")
        return

    # Build a comparison table
    offender1_dict = nono_dict_by_member[ctx.guild.id][offender1.id]
    offender2_dict = nono_dict_by_member[ctx.guild.id][offender2.id]
    offender1_total = superlatives_by_member[ctx.guild.id][offender1.id]['total_nono_words']
    offender2_total = superlatives_by_member[ctx.guild.id][offender2.id]['total_nono_words']
    table_body_list = []
    # Keep track of the variety of offender nono words
    offender1_vocab = 0
    offender2_vocab = 0
    for word in nono_list:
        if word in offender1_dict or word in offender2_dict:
            word_count_1 = 0
            word_count_2 = 0
            winner = 'Tie'
            if word in offender1_dict:
                offender1_vocab += 1
                word_count_1 = offender1_dict[word].count
            if word in offender2_dict:
                offender2_vocab += 1
                word_count_2 = offender2_dict[word].count
            if word_count_1 > word_count_2:
                winner = '<---'
            elif word_count_2 > word_count_1:
                winner = '--->'
            table_body_list.append([word, word_count_1, winner, word_count_2])
    overall_winner = 'Tie'
    if offender1_total > offender2_total:
        overall_winner = '<---'
    elif offender2_total > offender1_total:
        overall_winner = '--->'
    footer = ["Totals:", offender1_total, overall_winner, offender2_total]
    abbreviated_name1 = get_name(offender1)
    abbreviated_name2 = get_name(offender2)
    if len(get_name(offender1)) > 8:
        abbreviated_name1 = get_name(offender1)[:8] + "-"
    if len(get_name(offender2)) > 8:
        abbreviated_name2 = get_name(offender2)[:8] + "-"
    nono_table = t2a(
            header=["NoNo_Word", abbreviated_name1, "Winner", abbreviated_name2],
            body=table_body_list,
            footer = footer,
            style = PresetStyle.minimalist
            )
    #Craft a winner message:
    winner_message = ''
    if offender1_total > offender2_total and offender1_vocab > offender2_vocab:
        winner_message = trophy(bold(get_name(offender1))) + " claimed victory in both total NoNo totals and variety."
    elif offender1_total < offender2_total and offender1_vocab < offender2_vocab:
        winner_message = trophy(bold(get_name(offender2))) + " claimed victory in both total NoNo totals and variety."
    elif offender1_total > offender2_total and offender1_vocab < offender2_vocab:
        winner_message = bold(get_name(offender1)) + " said more NoNo words, but " + bold(get_name(offender2)) + " has a larger NoNo vocabulary."
    elif offender1_total < offender2_total and offender1_vocab > offender2_vocab:
        winner_message = bold(get_name(offender2)) + " said more NoNo words, but " + bold(get_name(offender1)) + " has a larger NoNo vocabulary."
    elif offender1_total == offender2_total and offender1_vocab == offender2_vocab:
        winner_message = "Astonishing! It's a perfect tie!"
    elif offender1_total == offender2_total and offender1_vocab > offender2_vocab:
        winner_message = "The total NoNos are tied, but " + bold(get_name(offender1)) + " has a larger NoNo vocabulary."
    elif offender1_total == offender2_total and offender1_vocab < offender2_vocab:
        winner_message = "The total NoNos are tied, but " + bold(get_name(offender2)) + " has a larger NoNo vocabulary."
    elif offender1_total > offender2_total and offender1_vocab == offender2_vocab:
        winner_message = trophy(bold(get_name(offender1))) + " is the winner! However, they are equally matched in NoNo vocabulary."
    elif offender1_total < offender2_total and offender1_vocab == offender2_vocab:
        winner_message = trophy(bold(get_name(offender2))) + " is the winner! However, they are equally matched in NoNo vocabulary."
    # Send picture and nono_word table to channel
    with open('private/compare.gif', 'rb') as f:
        nono_gif = discord.File(f)
        await ctx.channel.send(file=nono_gif) 
    #Don' t even bother with the embed, it can't be displayed on mobile
    #embed = discord.Embed(title = nono_prefix(ctx, offender1, offender2), description = code_block(nono_table))
    with open('comparison.txt', 'w+') as f:
        f.write(nono_table)
    with open('comparison.txt', 'r') as r:
        compare_txt = discord.File(r)
        await ctx.channel.send(nono_prefix(ctx, offender1, offender2))
        await ctx.channel.send(file=compare_txt)
        await ctx.channel.send(winner_message)
        return
    # await ctx.channel.send(embed = embed)
    # # Send a winner message to sum it all up
    # await ctx.channel.send(winner_message)

# A detailed explainer
@bot.command()
async def explain(ctx, command = None):
    logger.info(ctx.author.name + " used the help command.")
    print(ctx.author.name + " asked for help.")
    if command == None:
        explainer_string = discord.Embed(title = 'Please specify the command you want explained.', description = '\nMy commands are: ' + code_block("list, compare, and worst")\
            + '\nMy command prefix is ' + bold("~") + ' (tilde)' + '. Type: '+ code_block("~explain <command>") + ' for more information.')
        await ctx.channel.send(embed=explainer_string)
        return
    explainer_string = ''
    if "list" in command: 
        explainer_string  = discord.Embed(title = "~list", description = "I have compiled a list of all the shocking obscenities you've uttered here. "\
    + "\nTo see your own list, type: ```~list```To see someone else's, type: ```~list @username```To see results for the whole server, type:```~list all```")
    elif "compare" in command: 
        explainer_string  = discord.Embed(title = "~compare", description = "Compare two user's NoNo words. "\
    + "\nTo compare yourself to another user, type: ```~compare @username```To compare two other users, type: ```~list @username @another_username```")
    elif "worst" in command: 
        explainer_string  = discord.Embed(title = "~worst", description = "I have preserved the filthiest messages posted on this server. "\
    + "\nTo see your own worst message, type: ```~worst```To see someone else's, type: ```~worst @username```To see the worst message posted by anyone, type:```~worst all```")
    else:
        await ctx.channel.send("I don't recognize that command, " + get_name(ctx.author) + ". Try again.")
        return
    await ctx.channel.send(embed=explainer_string)

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

    message_string_clean = ''.join(c for c in message.content if c.isalpha() or c == ' ' or c == '\n').lower()
    print('message: ' + message_string_clean)
    message_word_list = message.content.split()
    author = get_name(message.author)
    
    # Call out those especially dirty NoNo words on sight
    for ultimate_nono_word in ultimate_nono_dict.keys():
        highlighted_message = "> "
        if ultimate_nono_word in message_string_clean.split() or (ultimate_nono_word + 's') in message_string_clean.split():
            for word in message_word_list:
                clean_word = ''.join(c for c in word if c.isalpha() or c == ' ' or c == '\n').lower()
                if clean_word == ultimate_nono_word or clean_word == (ultimate_nono_word + 's'):
                    highlighted_message += " " + bold(word)
                else:
                    highlighted_message += " " + word
            with open('private/ultimate_nono_alert.gif', 'rb') as f:
                nono_gif = discord.File(f)
                await message.channel.send(file=nono_gif) 
            await message.channel.send(author + ' said:\n' + highlighted_message)
            await message.channel.send(embed = ultimate_nono_dict[ultimate_nono_word])
    
    # Respond to mentions of bot
    if str(bot.user.id) in message.content:
        #help
        if 'help' in message_string_clean or 'who' in message_string_clean or 'command' in message_string_clean:
            print(message_string_clean)
            logger.info(author + " asked for help.")
            print(author + " asked for help.")
            greeting_string = discord.Embed(title = "Greetings, I am Dr. NoNo", description = '\nMy commands are: ' + code_block("list, compare, and worst")\
            + '\nMy command prefix is ' + bold("~") + ' (tilde)' + '. Type: '+ code_block("~explain <command>") + ' for more information.')
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
        elif "I visited Dylan's Github" in message.content:
            logger.info(author + " activated the secret!")
            print("secret")
            with open('private/secret_nono.gif', 'rb') as f:
                nono_gif = discord.File(f)
                await message.channel.send(file=nono_gif) 

    # Scan the message for nono words and add them to the dicts
    await load_message(message)
          
    # This allows commands to be used along with on_message events
    await bot.process_commands(message)

# Load the secret token that allows configuation of the bot
with open("private/secret.json", "r") as file:
    TOKEN = json.load(file)['TEST-TOKEN']

# Start the bot
bot.run(TOKEN)
