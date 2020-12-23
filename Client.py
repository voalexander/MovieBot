# Intro Client to MovieBot
import os
import discord
import atexit
import MovieBotCommands
from dotenv import load_dotenv
from discord.ext import commands

load_dotenv()
token = os.getenv('DISCORD_TOKEN')


bot = commands.Bot(command_prefix='!mn ')
bot.remove_command('help')

@bot.event
async def on_ready():
    print(f'{bot.user.name} connected to Discord')
    await bot.change_presence(activity=discord.Game(name='!mn help'))

bot.add_cog(MovieBotCommands.MovieBot(bot))
bot.run(token)

def exit_handler():
    print("exiting...")

atexit.register(exit_handler)
