import discord
import os.path
import datetime
import imdbExceptions
import asyncio
from datetime import timedelta
from discord.ext import commands
from os import path

class MovieBot(commands.Cog):
    def __init__(self, bot, imdb):
        self.bot = bot
        self.ia = imdb
        self.movieQueue = []
        self.movieWatched = []
        self.movieTime = datetime.datetime.now()
        self.selectedMovie = 0
        self.registeredUsers = []
        self.__getData()

    # @private_method: Refreshes the data of the bot with the data in the file
    def __getData(self): 
        if path.exists("/home/pi/MovieBot/data.pk1") == True:
            self.selectedMovie = 0
            self.registeredUsers = []
            self.movieQueue = []
            self.movieWatched = []
            file = open("/home/pi/MovieBot/data.pk1", "r")

            #For watchlist
            queue = file.readline()
            films = queue.split("(||)")[:-1]
            for data in films:
                filmData = data.split("(@@)")
                self.movieQueue.append(filmData)

            #For time
            time = file.readline()
            date = time.split(" ")
            dateFirst = date[0].split("/")
            dateSecond = date[1].split(":")
            self.movieTime = datetime.datetime(2020, int(dateFirst[0]), int(dateFirst[1]), int(dateSecond[0]), int(dateSecond[1].rsplit('\n')[0]))

            #For selected movie
            self.selectedMovie = int(file.readline())

            #For registered Users
            regUsers = file.readline().split("(@@@)")[:-1]
            self.registeredUsers = regUsers

            watchedMovies = file.readline().split("(||)")[:-1]
            for data in watchedMovies:
                filmData = data.split("(@@)")
                self.movieWatched.append(filmData)

            file.close()    

    #@private_method: Saves all the data to an external file
    def __saveAll(self):
        print("Saving...")
        file = open("/home/pi/MovieBot/data.pk1", "w+")
        # Movies watched
        for x in self.movieQueue:
            file.write(str(x[0]) + "(@@)" + str(x[1]) + "(@@)" + str(x[2]) + "(||)")
        file.write("\n")

        # Time
        file.write(self.movieTime.strftime("%m/%d %H:%M"))
        file.write("\n")

        # Selected Movie
        file.write(str(self.selectedMovie))
        file.write("\n")

        # Registered Users
        for x in self.registeredUsers:
            file.write(str(x) + "(@@@)")
        file.write("\n")

        # Movies Watched
        for x in self.movieWatched:
            file.write(str(x[0]) + "(@@)" + str(x[1]) + "(@@)" + str(x[2]) + "(||)")
        file.close()
        print("Saving done")

    #@private_method: Takes moviedata and returns formatted string
    def __filmFormat(self, movieData):
        fData = "\n[" + movieData[0] + "]\t #IMDb:" + movieData[1] + "\nPlot: " + movieData[2]
        return fData

    #@private_method: Gets the time until movienight as a string
    def __getTimeTill(self):
        duration = self.movieTime - datetime.datetime.now()
        days, seconds = duration.days, duration.seconds
        hours = days * 24 + seconds // 3600
        hours = hours - (days * 24)
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        toPrint = ""
        if days > 0:
            toPrint += str(days) + " day(s), " + str(hours) + " hours(s), and " + str(minutes) + " minute(s)"
        elif hours > 0:
            toPrint += str(hours) + " hours(s), and " + str(minutes) + " minute(s)"
        else:
            toPrint += str(minutes) + " minute(s)"
        return toPrint

    #@private_method: Convers args to a title
    def __getTitle(self, *args):
        title = ""
        for x in args:
            title = title + " " + x
        return title

    #@bot_command: Prints time of upcoming movie
    @commands.command('time', help="Shows when movie night is\n!mn time")
    async def time(self, ctx):
        timeP = self.movieTime.strftime("%A, %B %d at %I:%M")
        if len(self.movieQueue) == 0:
            await ctx.send("```css\n[Movie Night is on " + str(timeP) + " CST].\n\nWe have no planned movies right now```")
        else:
            tt = self.__getTimeTill()
            await ctx.send("```css\n[Movie Night is on " + str(timeP) + " CST].\n[" + tt + " away]\n\nWe plan to watch\n" + self.__filmFormat(self.movieQueue[self.selectedMovie]) + "```")

    #@bot_command: Sets the time of movienight
    @commands.command('setTime', help="Sets the movie night time\n!mn setTime MM/DD 00:00\nUses 24hour time\nDEFAULT TIMEZONE IS CST")
    async def setTime(self, ctx, date, time):
        dateFirst = date.split("/")
        dateSecond = time.split(":")
        if len(dateFirst) != 2 or len(dateSecond) != 2:
            await ctx.send("```Invalid date time. MM/DD 00:00```")
        else:
            try:
                newDate = datetime.datetime(2020, int(dateFirst[0]), int(dateFirst[1]), int(dateSecond[0]), int(dateSecond[1]))
                await ctx.send("```css\nDate changed to [" + newDate.strftime("%A, %B %d at %I:%M %p") + " CST]```")
                self.movieTime = newDate
                self.__saveAll()
            except Exception:
                await ctx.send("```Invalid date time```")

    #@bot_command: Changes the movie to watch at the next movienight
    @commands.command('changenext', help="Changes the next up movie\n!mn change next { moviename }")
    async def changeSelection(self, ctx, *args):
        title = self.__getTitle(args)
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieQueue) == True:
                self.selectedMovie = self.movieQueue.index(movieData)
                await ctx.send("```css\nNext up is changed to \n" + self.__filmFormat(self.movieQueue[self.selectedMovie]) + "```")
                self.__saveAll()
        except Exception:
            await ctx.send("```Movie cannot be found```")

    #@bot_command: Outputs a list of movies to watch
    @commands.command('watchlist', help='Displays the next few movies\n!mn watchlist')
    async def watchlist(self, ctx):
        toPrint = "```css\n"
        for title in self.movieQueue:
            toPrint += self.__filmFormat(title) + "\n\n"
        if len(self.movieQueue) == 0:
            toPrint = "```css\nEmpty - add movies with !mn add { film }"
        toPrint += "```"
        await ctx.send(toPrint)

    #@bot_command: Finds and puts a movie into the watchlist
    @commands.command('add', help='Adds a movie to the watchlist\n!mn add moviename')
    async def add(self, ctx, *args):
        title = self.__getTitle(args)
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieQueue) == True:
                raise imdbExceptions.AlreadyExists
            self.movieQueue.append(movieData)
            await ctx.send("```css" + self.__filmFormat(movieData) + "```\nAdded to the watchlist")
            self.__saveAll()        
        except imdbExceptions.CannotFindFilm:
            await ctx.send("```Cannot find movie: " + title + "```")
        except imdbExceptions.AlreadyExists:
            await ctx.send("```Movie is already in the watchlist```")

    #@bot_command: Finds and removes a movie from the watchlist
    @commands.command('remove', help="Removes a movie from the watchlist\n!mn remove {watchlist number}")
    async def remove(self, ctx, *args):
        title = self.__getTitle(args)
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieQueue) == True:
                if self.selectedMovie == self.movieQueue.index(movieData):
                    self.selectedMovie = 0
                del self.movieQueue[self.movieQueue.index(movieData)]
                await ctx.send("```css\n[" + self.movieQueue[self.movieQueue.index(movieData)][0] + "] removed```")
                self.__saveAll()
            else:
                await ctx.send("```Movie not in list```")
        except Exception:
            await ctx.send("```Movie cannot be found```")

    #@bot_command: Searches imdb and returns movie data
    @commands.command('search', help='Seaches imdb for a movie\n!mn search moviename')
    async def search(self, ctx, *args):
        title = self.__getTitle(args)
        try:
            movieData = self.ia.getFilmData(title)
            await ctx.send("```css" + self.__filmFormat(movieData) + "```")
        except imdbExceptions.CannotFindFilm:
            await ctx.send("```Cannot find movie: " + title + "```")

    #@bot_command: Registers a user for notifications
    @commands.command('register',help='Register for notifications\n!mn register')
    async def register(self, ctx):
        if str(ctx.author.id) not in self.registeredUsers:
            self.registeredUsers.append(ctx.author.id)
            await ctx.send(f"```css\n{ctx.author} registered!```")
            self.__saveAll()
        else:
            await ctx.send(f"```css\n{ctx.author} is already registered```")
        
    #@bot_command: Unregisters a user for notifications
    @commands.command('unregister', help='Unregister for notifications\n!mn unregister')
    async def unregister(self, ctx):
        if str(ctx.author.id) in self.registeredUsers == True:
            self.registeredUsers.remove(str(ctx.author.id))
            await ctx.send(f"```css\n{ctx.author} unregistered```")
            self.__saveAll()
        else:
            await ctx.send("```css\nYou were never registered```")
    
    #@bot_command: Announces the movietime, movie, and pings registered users
    @commands.command('announce', help='Alex only permission\nstop snooping')
    async def announce(self, ctx):
        if str(ctx.author.id) == "154422225275977728":
            tt = self.__getTimeTill()
            toPrint = "```css\n[The movie is now " + tt + " away]\n\n"
            toPrint += "We are watching\n"
            toPrint += self.__filmFormat(self.movieQueue[self.selectedMovie])
            toPrint += "```"
            for user in self.registeredUsers:
                toPrint += self.bot.get_user(int(user)).mention + " "
            await ctx.send(toPrint)
        else:
            await ctx.send("```css\nnope```")

    #bot_command: Automatically announces that the movie starts in 30 minutes
    @commands.command('autoannounce', help="Alex only permission\nCan't be turned off lmao")
    async def autoannounce(self, ctx, arg):
        if str(ctx.author.id) == "154422225275977728":
            if arg == "on":
                await ctx.send("```css\n[Autoannounce ON]```")
                await asyncio.sleep((self.movieTime - datetime.datetime.now()).seconds - 1800)
                self.announce(ctx)
    
    #@bot_command: Lists the registered users
    @commands.command('listregistered',help="Lists the registered users\n!mn listregistered")
    async def listRegistered(self, ctx):
        toPrint = "```css\n"
        for x in self.registeredUsers:
            toPrint += str(self.bot.get_user(int(x)))
            toPrint += "\n"
        toPrint += "```"
        await ctx.send(str(toPrint))

    #@bot_command: Prints out a list of watched movies
    @commands.command('watchedlist',help='Gets all the watched movies\n!mn watchedlist')
    async def listWatched(self, ctx):
        toPrint = "```css\n"
        for title in self.movieWatched:
            toPrint += self.__filmFormat(title) + "\n\n"
        if len(self.movieWatched) == 0:
            toPrint = "```css\nEmpty - add movies with !mn watched { moviename }"
        toPrint += "```"
        await ctx.send(toPrint)

    #@bot_command: Adds movie to watched movies list
    @commands.command('watched',help='Mark movie as watched\n!mn watched { moviename }')
    async def watched(self, ctx, *args):
        title = self.__getTitle()
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieWatched) == True:
                await ctx.send("```css\nMovie already in watched```")
            else:
                if self.ia.alreadyExists(movieData, self.movieQueue) == True:
                    if self.selectedMovie == self.movieQueue.index(movieData):
                        self.selectedMovie = 0
                    self.movieWatched.append(movieData)
                    del self.movieQueue[self.movieQueue.index(movieData)]
                    await ctx.send("```css\n[" + movieData[0] + "] added to watched films```")
                else:
                    self.movieWatched.append(movieData)
                    await ctx.send("```css\n[" + movieData[0] + "] added to watched films```")
                self.__saveAll()
        except Exception:
            await ctx.send("```Movie cannot be found```")

    #@bot_command: Removes a watched movie from the list
    @commands.command('removewatched', help="Removes a movie from the watchlist\n!mn remove {watchlist number}")
    async def removeWatched(self, ctx, *args):
        title = self.__getTitle()
        try:
            movieData = self.ia.getFilmData(title)
            if self.ia.alreadyExists(movieData, self.movieWatched) == True:
                del self.movieWatched[self.movieWatched.index(movieData)]
                await ctx.send("```css\n[" + movieData[0] + "] removed```")
                self.__saveAll()
            else:
                await ctx.send("```Movie not in list```")
        except Exception:
            await ctx.send("```Movie cannot be found```")

    @commands.command('clear', help="Clears certain list")
    async def clear(self, ctx, arg):
        valid = False
        if arg == "watchlist":
            self.movieQueue = []
            self.selectedMovie = 0
            valid = True
        elif arg == "watchedlist":
            self.movieWatched = []
            valid = True
        elif arg == "registeredlist":
            self.registeredUsers = []
            valid = True
        self.__saveAll()
        if valid == True:
            await ctx.send("```" + arg + "cleared```")

    @commands.command('refresh', help="Refresh data")
    async def refresh(self, ctx):
        self.__getData()
        await ctx.send("```Refreshed```")
