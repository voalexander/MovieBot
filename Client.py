# Intro Client to MovieBot
import os
import discord
import pickle
import atexit
import imdb_stuff
import mb_commands
from dotenv import load_dotenv
from discord.ext import commands
from os import path

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='!mn ')

@bot.event
async def on_ready():
    print(f'{bot.user.name} connected to Discord')
    await bot.change_presence(activity=discord.Game(name='!mn help'))

bot.add_cog(mb_commands.MovieBot(bot, imdb_stuff.IMDB()))
bot.run(token)

def exit_handler():
    print("exiting...")

atexit.register(exit_handler)