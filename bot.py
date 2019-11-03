import datetime
import asyncio
import traceback
import json
import re

import discord
from discord.ext.commands import Bot
from discord.ext import commands, tasks
# import POSifiedText
from twitter_scraper import get_tweets
import markovify

# Settings
with open('settings.json') as settings_file:
    settings = json.load(settings_file)


# Some variables
trump_text_model = None
bell_text_model = None
mcd_text_model = None

username = settings["discord"]["description"]
version = settings["discord"]["version"]
start_time = datetime.datetime.utcnow()
bot = Bot(
    command_prefix=settings["discord"]["command_prefix"],
    description=settings["discord"]["description"])

print('{} - {}'.format(username, version))


# Ping
# @checks.admin_or_permissions(manage_server=True)
@bot.command(pass_context=True, name="ping")
async def bot_ping(ctx):
    pong_message = await ctx.message.channel.send("Pong!")
    await asyncio.sleep(0.5)
    delta = pong_message.created_at - ctx.message.created_at
    millis = delta.days * 24 * 60 * 60 * 1000
    millis += delta.seconds * 1000
    millis += delta.microseconds / 1000
    await pong_message.edit(content="Pong! `{}ms`".format(int(millis)))


# The following is trivial and self-explanatory
@bot.event
async def on_command_error(error, ctx):
    if isinstance(error, commands.errors.CommandNotFound):
        pass  # ...don't need to know if commands don't exist
    if isinstance(error, commands.errors.CheckFailure):
        await ctx.message.channel.send(
            ctx.message.channel,
            '{} You don''t have permission to use this command.' \
            .format(ctx.message.author.mention))
    elif isinstance(error, commands.errors.CommandOnCooldown):
        try:
            await ctx.message.delete()
        except discord.errors.NotFound:
            pass
        await ctx.message.channel.send(
            ctx.message.channel, '{} This command was used {:.2f}s ago ' \
            'and is on cooldown. Try again in {:.2f}s.' \
            .format(ctx.message.author.mention,
                    error.cooldown.per - error.retry_after,
                    error.retry_after))
        await asyncio.sleep(10)
        await ctx.message.delete()
    else:
        await ctx.message.channel.send(
            'An error occured while processing the `{}` command.' \
            .format(ctx.command.name))
        print('Ignoring exception in command {0.command} ' \
            'in {0.message.channel}'.format(ctx))
        tb = traceback.format_exception(type(error), error, error.__traceback__)
        print(''.join(tb))


# Similar to above
@bot.event
async def on_error(event_method, *args, **kwargs):
    if isinstance(args[0], commands.errors.CommandNotFound):
        # For some reason runs despite the above
        return
    print('Ignoring exception in {}'.format(event_method))
    mods_msg = "Exception occured in {}".format(event_method)
    tb = traceback.format_exc()
    print(''.join(tb))
    mods_msg += '\n```' + ''.join(tb) + '\n```'
    mods_msg += '\nargs: `{}`\n\nkwargs: `{}`'.format(args, kwargs)
    print(mods_msg)
    print(args)
    print(kwargs)


# Ready
@bot.event
async def on_ready():
    await asyncio.sleep(1)
    print("Logged in to discord.")
    try:
        await bot.change_presence(
            activity=discord.Game(name=settings["discord"]["game"]), #'(name=settings["discord"]["game"]),
            status=discord.Status.online,
            afk=False)
    except Exception as e:
        print('on_ready : ', e)
        pass
    await asyncio.sleep(1)


@tasks.loop(hours=2.0, reconnect=True)
async def twitter_task():
    global trump_text_model, bell_text_model, mcd_text_model
    await bot.wait_until_ready()
    await asyncio.sleep(5)
    try:
        tweets = [t['text'] for t in get_tweets('realDonaldTrump', pages=20)]
        await asyncio.sleep(0.5)
        text = '\n'.join(tweets)
        await asyncio.sleep(0.5)
        corpus = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
        await asyncio.sleep(0.5)
        #trump_text_model = POSifiedText.spacyPOSifiedText(corpus)
        trump_text_model = markovify.NewlineText(corpus)
        print('Trump text model built.')
        await asyncio.sleep(0.5)
    except Exception as e:
        print('background_loop : ', e)
        pass
    try:
        tweets = [t['text'] for t in get_tweets('tacobell', pages=20)]
        await asyncio.sleep(0.5)
        text = '\n'.join(tweets)
        await asyncio.sleep(0.5)
        corpus = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
        await asyncio.sleep(0.5)
        #bell_text_model = POSifiedText.spacyPOSifiedText(corpus)
        bell_text_model = markovify.NewlineText(corpus)
        print('Taco Bell text model built.')
        await asyncio.sleep(0.5)
    except Exception as e:
        print('background_loop : ', e)
        pass
    try:
        tweets = [t['text'] for t in get_tweets('McDonalds', pages=20)]
        await asyncio.sleep(0.5)
        text = '\n'.join(tweets)
        await asyncio.sleep(0.5)
        corpus = re.sub(r'http\S+', '', text, flags=re.MULTILINE)
        await asyncio.sleep(0.5)
        #mcd_text_model = POSifiedText.spacyPOSifiedText(corpus)
        mcd_text_model = markovify.NewlineText(corpus)
        print('McDonalds text model built.')
        await asyncio.sleep(0.5)
    except Exception as e:
        print('background_loop : ', e)
        pass


@bot.command(pass_context=True, name='potus')
async def potus(ctx):
    try:
        if ctx.message.author == bot.user:
            return
        if not trump_text_model:
            return
        await generate_reply(ctx, trump_text_model)
    except Exception as e:
        print('potus : ', e)
        pass


@bot.command(pass_context=True, name='maga')
async def maga(ctx):
    try:
        if ctx.message.author == bot.user:
            return
        if not trump_text_model:
            return
        await generate_reply(ctx, trump_text_model)
    except Exception as e:
        print('maga : ', e)
        pass


@bot.command(pass_context=True, name='wall')
async def wall(ctx):
    try:
        if ctx.message.author == bot.user:
            return
        if not trump_text_model:
            return
        if not bell_text_model:
            return
        await generate_reply(ctx, markovify.combine([trump_text_model, bell_text_model], [1, 1.5]))
    except Exception as e:
        print('wall : ', e)
        pass


@bot.command(pass_context=True, name='berder')
async def berder(ctx):
    try:
        if ctx.message.author == bot.user:
            return
        if not trump_text_model:
            return
        if not mcd_text_model:
            return
        await generate_reply(ctx, markovify.combine([trump_text_model, mcd_text_model], [1, 1.5]))
    except Exception as e:
        print('berder : ', e)
        pass


async def generate_reply(ctx, model):
    try:
        sentence = model.make_sentence(tries=100, retain_original=False)
        sentence = sentence.replace("pic.twitter.com", "https://pic.twitter.com")
        sentence = re.sub(r'http\S+', '', sentence, flags=re.MULTILINE)
        if sentence:
            await ctx.send('{0.author.mention} {1}'.format(ctx.message, sentence))
        else:
            await ctx.send('{0.author.mention} {1}'.format(ctx.message, '`Unable to build text chain`'))
    except Exception as e:
        print('generate_reply : ', e)
        pass


# Starts the bot
twitter_task.start()
bot.run(settings["discord"]["client_token"])
