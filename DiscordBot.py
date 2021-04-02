#!/usr/bin/env python3

import discord
import asyncio
import sqlite3
import time
import random
from discord.ext import commands
from datetime import datetime

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(command_prefix='!', intents = intents)

con = sqlite3.connect('bot.db')
bot.con = con

con.execute("PRAGMA foreign_keys = ON;")

con.execute('''
    CREATE TABLE IF NOT EXISTS mutes(
        id          INTEGER PRIMARY KEY,
        user_id     INTEGER,
        guild_id    INTEGER,
        unmute_time INTEGER
    )
    ''')

con.execute('''
    CREATE TABLE IF NOT EXISTS mute_roles(
        id          INTEGER PRIMARY KEY,
        mute_id     INTEGER,
        role_id     INTEGER,
        FOREIGN KEY(mute_id) REFERENCES mutes(id)
    )
    ''')
con.execute('''
    CREATE TABLE IF NOT EXISTS logs(
        id          INTEGER PRIMARY KEY,
        time        INTEGER,
        guild       INTEGER,
        log_group   TEXT,
        content     TEXT,
        thumbnail   TEXT
    )
    ''')
con.execute('''
    CREATE TABLE IF NOT EXISTS user_history(
        id            INTEGER PRIMARY KEY,
        last_indexed  INTEGER,
        user_id       INTEGER,
        guild_id      INTEGER,
        name          TEXT,
        discriminator TEXT,
        last_message  INTEGER,
        thumbnail     TEXT
    )
    ''')
con.commit()

async def log(group, content, guild, thumbnail = ''):
    channel = discord.utils.get(guild.channels, name='logs')
    embed=discord.Embed(title="Log [{}]".format(group), description=content, color=0x800000)
    embed.set_thumbnail(url=thumbnail)
    embed.timestamp=datetime.now()
    await channel.send("", embed=embed)

    cur = con.cursor()
    cur.execute("INSERT INTO logs VALUES (NULL,?, ?, ?, ?, ?)", (int(datetime.now().timestamp()), guild.id, group, content, str(thumbnail)))
    con.commit()

@bot.command(aliases=['lynch', 'mute'])
@commands.has_permissions(manage_roles=True)
async def mute_command(ctx, member: discord.Member, minutes: int = 1):
    cur = con.cursor()

    cur.execute("SELECT * FROM mutes WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
    row = cur.fetchone()
    if row is not None:
        await ctx.reply("User is already muted!")
        return

    cur.execute("INSERT INTO mutes VALUES (NULL, ?, ?, ?)", (member.id, member.guild.id, int(datetime.now().timestamp()+minutes*60)))
    mute_id = cur.lastrowid

    roles = member.roles[1:]
    for role in roles:
        cur.execute("INSERT INTO mute_roles VALUES (NULL, ?, ?)", (mute_id, role.id))
    
    con.commit()
    
    for role in roles:
        await member.remove_roles(role)

    lynchedRole = discord.utils.get(ctx.guild.roles, name='Lynched')

    if(lynchedRole):
        await member.add_roles(lynchedRole)

    await ctx.reply("{0} has been lynched for {1} minutes!".format(member.mention, minutes))
    await log("MUTE", "{0} has been lynched for {1} minutes by {2}!".format(member.mention, minutes, ctx.author.mention), ctx.guild)    

@bot.command(aliases=['unlynch', 'unmute'])
@commands.has_permissions(manage_roles=True)
async def unmute_command(ctx, member: discord.Member):
    cur = con.cursor()
    cur.execute("SELECT * FROM mutes WHERE user_id = ? AND guild_id = ?", (member.id, member.guild.id))
    row = cur.fetchone()
    if row is None:
        await ctx.reply("User is not muted!")
        return

    mute_id = row[0]
    cur.execute("SELECT role_id FROM mute_roles WHERE mute_id = ?", (mute_id,))
    role_ids = cur.fetchall()

    for role_id in role_ids:
        role_id = role_id[0]
        role = member.guild.get_role(role_id)
        if role:
            await member.add_roles(role)

    lynchedRole = discord.utils.get(ctx.guild.roles, name='Lynched')
    if(lynchedRole):
        await member.remove_roles(lynchedRole)

    cur.execute("DELETE FROM mute_roles WHERE mute_id = ?", (mute_id,))
    cur.execute("DELETE FROM mutes WHERE id = ?", (mute_id,))
    con.commit()

    await ctx.reply("{0} has been unlynched".format(member.mention))
    await log("MUTE", "{0} has been unlynched by {1}!".format(member.mention, ctx.author.mention), ctx.guild)

@bot.command()
async def accountage(ctx, member: discord.Member):
    await ctx.reply("{} has been created at {}".format(member.mention, member.created_at.isoformat()))


async def mute_routine(bot):
    while True:
        if not bot.is_ready():
            await asyncio.sleep(1)
            continue

        current_time = int(datetime.now().timestamp())
        cur = con.cursor()
        cur.execute("SELECT * FROM mutes WHERE unmute_time < ?", (current_time,))
        rows = cur.fetchall()

        for row in rows:
            mute_id =  row[0]
            user_id =  row[1]
            guild_id = row[2]

            guild = bot.get_guild(guild_id)
            member = guild.get_member(user_id)

            lynchedRole = discord.utils.get(guild.roles, name='Lynched')

            if(lynchedRole):
                await member.remove_roles(lynchedRole)

            cur.execute("SELECT role_id FROM mute_roles WHERE mute_id = ?", (mute_id,))
            role_ids = cur.fetchall()

            for role_id in role_ids:
                role_id = role_id[0]
                role = guild.get_role(role_id)
                if role:
                    await member.add_roles(role)

            await log("MUTE", "{0} has been automatically unlynched!".format(member.mention), member.guild)
            
            cur.execute("DELETE FROM mute_roles WHERE mute_id = ?", (mute_id,))
            cur.execute("DELETE FROM mutes WHERE id = ?", (mute_id,))

        con.commit()

        await asyncio.sleep(1)

@bot.command()
async def hello(ctx):
    if(ctx.author.id == 277825914799128586):
        await ctx.reply("Hello solwer!");
    elif(ctx.author.id == 530441160288763905):
        await ctx.reply("Hello Noah!");
    elif(ctx.author.id == 490917365937078273):
        await ctx.reply("Hello slav!");
    elif(ctx.author.id == 412606466277507082):
        await ctx.reply("Hello doggy!");
    elif(ctx.author.id == 710376618211803176):
        await ctx.reply("Hello steiner!");
    else:
        await ctx.reply("Hello!")

@bot.command(aliases=['8ball'])
async def _8ball(ctx, *, question: str):
    question = question.casefold()
    responses = ["It is certain.",
             "It is decidedly so.",
             "Without a doubt.",
             "Yes - definitely.",
             "You may rely on it.",
             "As I see it, yes.",
             "Most likely.",
             "Yes, and Noah is gay.",
             "Yes.",
             "Signs point to yes.",
             "Reply hazy, try again.",
             "Ask again later.",
             "Better not tell you now.",
             "Cannot predict now.",
             "Concentrate and ask again.",
             "Don't count on it.",
             "My reply is no.",
             "My sources say no.",
             "Very doubtful."]
    await ctx.reply('{}'.format(random.choice(responses)))  

@bot.command(aliases=['prune'])
@commands.has_permissions(manage_messages=True)
async def purge(ctx, limit: int = 100):
    await ctx.channel.purge(limit = limit)
    await log('PURGE', '{} purged {} messages in {}'.format(ctx.message.author.mention, limit, ctx.channel.mention), ctx.guild)

@bot.command(aliases=['pruneword'])
@commands.has_permissions(manage_messages=True)
async def purgeword(ctx, word: str):
    await log('PURGE', '{} purged word "{}" in {}'.format(ctx.message.author.mention, word, ctx.channel.mention), ctx.guild)
    async for message in ctx.history(limit=None):
        if word.casefold() in message.content.casefold():
            await message.delete()

@bot.command()
@commands.has_permissions(manage_roles=True)
async def indexusers(ctx):
    cur = con.cursor()
    current_time = int(datetime.now().timestamp())
    for member in ctx.guild.members:
        last_message = 0
        cur.execute("INSERT INTO user_history VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)", (current_time, member.id, member.guild.id, member.name, member.discriminator, last_message, str(member.avatar_url)))
        
    con.commit()
    await log('INDEX', 'Users have been indexed by {}!'.format(ctx.message.author.mention), ctx.guild)

@bot.event
async def on_member_join(member):
    await log('JOINLOG', '{} ({}#{}) (created at {}) has joined the server!'.format(member.mention, member.name, member.discriminator, member.created_at.isoformat()), member.guild, member.avatar_url)
        
@bot.event
async def on_member_remove(member):
    await log('JOINLOG', '{} ({}#{}) has left the server!'.format(member.mention, member.name, member.discriminator), member.guild, member.avatar_url)

@bot.event
async def on_ready():
    print('We have logged in as {0.user}'.format(bot))
    print('Servers connected to:')
    for guild in bot.guilds:
        print(guild.name)
    print('------')

f = open(".token", "r")
token = f.read()
    
bot.loop.create_task(mute_routine(bot))
bot.run(token)
con.close()
