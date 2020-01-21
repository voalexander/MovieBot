import discord
import datetime
import myExceptions
from discord.ext import commands

class MovieBot(commands.Cog):
    def __init__(self, bot, imdb):
        self.bot = bot
        self.ia = imdb
        self.movieQueue = []
        self.movieTime = datetime.datetime.now()
        self.selectedMovie = 0

    def __filmFormat(self, movieData):
        fData = "\n[" + movieData[0] + "]\t #IMDb:" + movieData[1] + "\nPlot: " + movieData[2]
        return fData

    @commands.command('time', help="Shows when movie night is\n!mn time")
    async def time(self, ctx):
        mt = self.movieTime
        timeP = mt.strftime("%A, %B %w at %I:%M")
        if len(self.movieQueue) == 0:
            await ctx.send("```css\n[Movie Night is on " + str(timeP) + " CST].\n\nWe have no planned movies right now```")
        else:
            await ctx.send("```css\n[Movie Night is on " + str(timeP) + " CST].\n\nWe plan to watch\n" + self.__filmFormat(self.movieQueue[self.selectedMovie]) + "```")

    @commands.command('setTime', help="Sets the movie night time\n!mn setTime MM/DD 00:00\nUses 24hour time\nDEFAULT TIMEZONE IS CST")
    async def setTime(self, ctx, date, time):
        dateFirst = date.split("/")
        dateSecond = time.split(":")
        if len(dateFirst) != 2 or len(dateSecond) != 2:
            await ctx.send("```Invalid date time. MM/DD 00:00```")
        else:
            try:
                newDate = datetime.datetime(2020, int(dateFirst[0]), int(dateFirst[1]), int(dateSecond[0]), int(dateSecond[1]))
                await ctx.send("```css\nDate changed to [" + newDate.strftime("%A, %B %w at %I:%M") + "] CST```")
                self.movieTime = newDate
            except Exception:
                await ctx.send("```Invalid date time```")

    @commands.command('changenext', help="Changes the next up movie\n!mn change next {watchlist number}")
    async def changeSelection(self, ctx, arg: int):
        try:
            await ctx.send("```css\nNext up is changed to \n" + self.__filmFormat(self.movieQueue[arg - 1]) + "```")
            self.selectedMovie = arg - 1
        except Exception:
            await ctx.send("```Invalid number```")

    @commands.command('watchlist', help='Displays the next few movies\n!mn watchlist')
    async def watchlist(self, ctx):
        num = 1
        toPrint = "```css\n"
        for title in self.movieQueue:
            toPrint += str(num) + ": " + self.__filmFormat(title) + "\n\n"
            num += 1
        if num == 1:
            toPrint = "```css\nEmpty - add movies with !mn add { film }"
        toPrint += "```"
        await ctx.send(toPrint)

    @commands.command('add', help='Adds a movie to the watchlist\n!mn add moviename')
    async def add(self, ctx, *args):
        title = ""
        for x in args:
            title = title + " " + x
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieQueue) == True:
                raise myExceptions.AlreadyExists
            self.movieQueue.append(movieData)
            await ctx.send("```css" + self.__filmFormat(movieData) + "```\nAdded to the watchlist")
        except myExceptions.CannotFindFilm:
            await ctx.send("```Cannot find movie: " + title + "```")
        except myExceptions.AlreadyExists:
            await ctx.send("```Movie is already in the watchlist```")

    @commands.command('remove', help="Removes a movie from the watchlist\n!mn remove {watchlist number}")
    async def remove(self, ctx, arg: int):
        try:
            await ctx.send("```css\n[" + self.movieQueue[arg - 1][0] + "] removed```")
            del self.movieQueue[arg - 1]
        except Exception:
            await ctx.send(arg <= len(self.movieQueue))
            await ctx.send(str(len(self.movieQueue)))
            await ctx.send("```Invalid number\n!mn remove {watchlist number}```")

    @commands.command('search', help='Seaches imdb for a movie\n!mn search moviename')
    async def search(self, ctx, *args):
        title = ""
        for x in args:
            title = title + " " + x
        try:
            movieData = self.ia.getFilmData(title)
            await ctx.send("```css" + self.__filmFormat(movieData) + "```")
        except CannotFindFilm:
            await ctx.send("```Cannot find movie: " + title + "```")