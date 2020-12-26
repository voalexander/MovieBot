import datetime
import asyncio
import os
import traceback
import random
import IMDB
import discord
import sqlite3 as sl;
from datetime import timedelta
from discord.ext import commands

def _getTitle(*args: str):
    title = ""
    for x in args:
        for y in x:
            for z in y:
                title += z + " "
    return str(title[:-1])

def _getTimeTill(time):
    if time < datetime.datetime.now():
        return "It started already. Might be over idk"
    duration = time - datetime.datetime.now()
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
    return toPrint + "away"

class MovieBot(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ia = IMDB.IMDB()
        self.database = sl.connect('MovieBot.db')
        self.dCursor = self.database.cursor()
        if os.stat('MovieBot.db').st_size <= 5:
            print("Creating new database")
            self._databaseInitial()
            print("Created new database")

    @commands.command('time', help="Shows when movie night is\n!mn time")
    async def time(self, ctx):
        time = self._getTime()
        tt = _getTimeTill(time)
        self.dCursor.execute("SELECT * FROM SelectedMovie")
        result = self.dCursor.fetchall()
        embed=discord.Embed(title="Movie Night", description=result[0][3], color=0xF79202)
        if result[0][0] == 'None':
            embed.add_field(name="No movie planned", value="Maybe some other time")
        else:
            if result[0][6] != 'None':
                embed.set_thumbnail(url=result[0][6])
            embed.add_field(name="{} - IMDb: {}/10".format(result[0][0], result[0][4]), value="{}\n[IMDb]({})".format(result[0][1], result[0][5]))
        embed.add_field(name="Time until", value=tt, inline=False)
        embed.set_footer(text="Requested by {}".format(ctx.author))
        await ctx.send(embed=embed)

    @commands.command('help')
    async def help(self,ctx, *args):
        helpstr = ""
        for arg in args:
            helpstr += arg + " "
        helpstr = helpstr[:-1]
        print(helpstr)
        try:
            embed=discord.Embed(title="MovieBot Help", description="If you need help with a specific command, type `help command`.\nAll commands begin with `!mn`", color=0xF79202)
            if helpstr == "time":
                embed.add_field(name="`!mn time`", value="""Shows you when the next movie is and what movie we're watching
                                                            \nAlso shows you a description of the movie as well as the time until movie night""", inline=False)
            elif helpstr == "register":
                embed.add_field(name="`register`", value="""Registers you for pings whenever the next movie night is
                                                            \nUnregister with `unregister`""", inline=False)
            elif helpstr == "unregister":
                embed.add_field(name="`unregister`", value="""Unregisters you for pings about the next movie night\n""", inline=False)
            elif helpstr == "search":
                embed.add_field(name="`search [movie]`", value="""Searches IMDb for the movie and gives you the top 3 results
                                                        \nReplace [movie] with your movie name""", inline=False)
            elif helpstr == "nextup":
                embed.add_field(name="`nextup [movie]`", value="""Changes the next movie we plan to watch
                                                        \nNote that the movie MUST already be in the watchlist for it to be added to nextup
                                                        \nReplace [movie] with your movie name
                                                        \nIf you say nextup RANDOM, it'll select a random movie from our watchlist""", inline=False)
            elif helpstr == "settime":
                embed.add_field(name="`settime [time]`", value="""Sets the time of the next movie night
                                                        \nThe format for time is the following
                                                        \nFullDay, FullMonth, DayNumber, Year at TimeAM/PM
                                                        \nEx: Tuesday, December 22, 2020 at 04:24PM CST
                                                        \nNote: All numbers must be zero-padded""", inline=False)
            elif helpstr == "watchlist":
                embed.add_field(name="`watchlist`", value="""Shows the next movies we plan to watch""", inline=False)
                embed.add_field(name="`watchlist add [movie]`", value="""Adds a movie to the watchlist
                                                        \nIt will return the top 3 results from IMDb, and then you reply with the number of the correct movie or 'cancel' to pick none
                                                        \nYou do not have to type !mn cancel, just reply cancel
                                                        \nAfter it will add that movie into the watchlist
                                                        \nReplace [movie] with the movie name""", inline=False)
                embed.add_field(name="`watchlist remove [movie]`", value="""Removes a movie from the watchlist
                                                        \nRemoves the movie that best matches with the name you enter
                                                        \nReaplce [movie] with the movie name""", inline=False)
            elif helpstr == "watchedlist":
                embed.add_field(name="`watchedlist`", value="""Shows the next movies we plan to watch""", inline=False)
                embed.add_field(name="`watchedlist add [movie]`", value="""Adds a movie to the watchedlist
                                                        \nIt will return the top 3 results from IMDb, and then you reply with the number of the correct movie
                                                        \nAfter it will add that movie into the watchedlist
                                                        \nReplace [movie] with the movie name""", inline=False)
                embed.add_field(name="`watchedlist remove [movie]`", value="""Removes a movie from the watchedlist
                                                        \nRemoves the movie that best matches with the name you enter
                                                        \nReaplce [movie] with the movie name""", inline=False)
            elif helpstr == "watched":
                embed.add_field(name="`watched [movie]`", value="""Marks a movie from the watchlist and/or the nextup as watched
                                                                \nMoves the movie from the watchlist and/or nextup to the watchedlist""", inline=False)
            elif helpstr == "announce":
                embed.add_field(name="`announce`", value="""Announces the next movie night and pings all registered users
                                                        \nRegister with !register
                                                        \nOnly verified users can use this command. Ask Alex if you wanna be verified""", inline=False)
            elif helpstr == "sql":
                embed.add_field(name="`sql`", value="A secret-ish command for Alex only to send raw SQL queries to the bot", inline=False)
            else:
                #embed.set_thumbnail(url='https://i.pinimg.com/originals/a5/e5/94/a5e5946affa44b4e47561137d544e2f5.png')
                embed.add_field(name="When and What", value="`time`\nShows you when the next movie is and what movie we're watching", inline=False)
                embed.add_field(name="watchlist", value="""`watchlist`\nShows the movies we plan to watch
                                                            \n\n`help watchlist`\nfor more""")
                embed.add_field(name="watchedlist", value="""`watchedlist`\nShows the movies we watched already
                                                            \n\n`help watchedlist`\nfor more""")
                embed.add_field(name="registration", value="""`register`\nRegisters you for pings whenever the next movie night is
                                                            \n`unregister`\nUnregisters you for pings""")
                embed.add_field(name="other", value="""`search [movie]` Searches IMDb for a movie
                                                    `nextup [movie]` Changes the next movie to watch
                                                    `watched [movie]` Markes movie from the watchlist as watched
                                                    `settime [time]` Sets the time of the next movie night
                                                    `announce` Announces the next movie night""")
            embed.set_footer(text="Requested by {}".format(ctx.author))
            await ctx.send(embed=embed)
        except Exception as e:
            print(e)
            pass

    @commands.command('watched')
    async def watched(self, ctx, *args):
        title = _getTitle([args])
        found = False
        if len(title) == 0:
            await ctx.send("```Invalid usage of watched\nSee `help watched` ```")
            return
        self.dCursor.execute("SELECT * FROM {} WHERE name LIKE '%{}%'".format("FutureMovies", title))
        results = self.dCursor.fetchall()
        if len(results) > 0:
            result = None
            if len(results) > 1:
                toSend = "```Multiple results found. Choose from below\n"
                i = 1
                for found in results:
                    toSend += "{}. {}\n".format(i, found[0])
                    i += 1
                await ctx.send(toSend + "or 'cancel' to choose none```")

                def check(m):
                    valid = True
                    try:
                        if m.content == "cancel":
                            return valid and m.author == ctx.author and m.channel == ctx.channel
                        num = int(m.content)
                        if num < 1 or num > len(results):
                            valid = False
                    except Exception:
                        valid = False
                    return valid and m.author == ctx.author and m.channel == ctx.channel
                response = await self.bot.wait_for('message', check=check)
                if response.content == "cancel":
                    await ctx.send(content="```No movie picked```",embed=None)
                    return
                else:
                    num = int(response.content) - 1
                    result = results[num]
            else:
                result = results[0]
            toSend = "```\n"
            self.dCursor.execute("DELETE FROM FutureMovies WHERE imdbid IS '{}'".format(result[3]))
            toSend += "Removed {} from watchlist\n".format(result[0])
            self.dCursor.execute("SELECT * FROM SelectedMovie WHERE imdbid IS '{}'".format(result[3]))
            results = self.dCursor.fetchall()
            if len(results) == 1:
                self.dCursor.execute("UPDATE SelectedMovie SET name='{}' WHERE imdbid IS '{}'".format("None", result[3]))
                toSend += "Removed {} from nextup\n".format(result[0])

            self.dCursor.execute("INSERT INTO WatchedMovies VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                result[0], result[1], result[2], result[3], result[4], result[5], result[6]))
            self.database.commit()
            toSend += "Added {} to watchedlist\n```".format(result[0])
            await ctx.send(toSend)
            # Remove from watchlist add to watched list check selected
        else:
            await ctx.send("```Movie must already be in the watchlist to be marked was watched!\nSee `help watched` ```")

    @commands.command('watchlist', help="Shows the watchlist")
    async def watchlist(self, ctx, *args):
        print("Watchlist")
        db = "FutureMovies"
        # Parsing sub commands
        if len(args) > 0:
            if "add" in args[0]:
                print(args[1:])
                await self.list_add(ctx, db, args[1:])
            elif "remove" in args[0]:
                await self.list_remove(ctx, db, args[1:])
            elif "watched" in args[0]:
                await self.watchlist_watched(ctx, args[1:])
        else:
            await self.list_display(ctx, db, args)
            return

    @commands.command('watchedlist', help="Shows the watchlist")
    async def watchedlist(self, ctx, *args):
        print("Watchlist")
        db = "WatchedMovies"
        # Parsing sub commands
        if len(args) > 0:
            if "add" in args[0]:
                print(args[1:])
                await self.list_add(ctx, db, args[1:])
            elif "remove" in args[0]:
                await self.list_remove(ctx, db, args[1:])
        else:
            await self.list_display(ctx, db, args)
            return

    @commands.command('settime',help='Changes time of the next movie night')
    async def settime(self, ctx, *args):
        try:
            time = ""
            for arg in args:
                time += arg + " "
            time = time[:-1]
            print(time)
            newtime = datetime.datetime.strptime(time, '%A, %B %d, %Y at %I:%M%p')
            self.dCursor.execute("SELECT * FROM SelectedMovie")
            result = self.dCursor.fetchall()
            self.dCursor.execute("UPDATE SelectedMovie SET watchtime='{}' WHERE imdbid IS '{}'".format(time + " CST", result[0][2]))
            self.database.commit()
            await ctx.send("```css\nNext Movie Night has been set to\n{} CST```".format(time))
        except Exception as e:
            await ctx.send("```css\nYour date does not match the format\nPlease see `help settime` ```")

    @commands.command('search', help="Searches IMDb and gives the top 3 results")
    async def search(self, ctx, *args):
        print("search")
        title = _getTitle([args])
        try:
            top3 = self.ia.getTop3(title)
            await self._outputTop3(ctx, "Top {} Results from IMDb".format(len(top3)), top3)
        except Exception as e:
            traceback.print_exc()
            pass

    @commands.command('nextup',help='Changes the next movie')
    async def nextup(self, ctx, *args):
        title = _getTitle([args])
        if len(title) == 0:
            await ctx.send("```Incorrect usage of nextup. Please see `help nextup` ```")
            return
        time = self._getTime().strftime("%A, %B %d, %Y at %I:%M%p CST")
        result = None
        if title == "RANDOM":
            self.dCursor.execute("SELECT * FROM FutureMovies")
            result = self.dCursor.fetchall()
            if len(result) == 0:
                await ctx.send("```No movies in watchlist to choose from!```")
                return
            result = [result[random.randrange(0, len(result), 1)]]
        else:
            self.dCursor.execute("SELECT * FROM FutureMovies WHERE name LIKE '%{}%'".format(title))
            result = self.dCursor.fetchall()
        print(result)
        if len(result) == 0:
            await ctx.send("```No results found for {} in the watchlist\nPlease add to the watchlist before nextup```".format(title))
        elif len(result) > 1:
            await ctx.send("```Multiple results found for {} in the watchlist```".format(title))
        else:
            self.dCursor.execute("DELETE FROM SelectedMovie")
            self.dCursor.execute("INSERT INTO SelectedMovie VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                 result[0][0], result[0][2], result[0][3], time, result[0][4], result[0][5], result[0][6]
            ))
            self.database.commit()
            await ctx.send("```Next movie changed to {}```".format(result[0][0]))

    @commands.command('search', help="Searches IMDb and gives the top 3 results")
    async def search(self, ctx, *args):
        print("search")
        title = _getTitle([args])
        if len(title) == 0:
            await ctx.send("```Invalid usage of search. Please see `help search` ```")
        try:
            top3 = self.ia.getTop3(title)
            await self._outputTop3(ctx, "Top {} Results from IMDb".format(len(top3)), top3)
        except Exception as e:
            traceback.print_exc()
            pass

    @commands.command('watchlist', help="Shows the watchlist")
    async def watchlist(self, ctx, *args):
        print("Watchlist")
        db = "FutureMovies"
        # Parsing sub commands
        if len(args) > 0:
            if "add" in args[0]:
                print(args[1:])
                await self.list_add(ctx, db, args[1:])
            elif "remove" in args[0]:
                await self.list_remove(ctx, db, args[1:])
            elif "watched" in args[0]:
                await self.watchlist_watched(ctx, args[1:])
        else:
            await self.list_display(ctx, db, args)
            return

    @commands.command('watchedlist', help="Shows the watchlist")
    async def watchedlist(self, ctx, *args):
        print("Watchlist")
        db = "WatchedMovies"
        # Parsing sub commands
        if len(args) > 0:
            if "add" in args[0]:
                print(args[1:])
                await self.list_add(ctx, db, args[1:])
            elif "remove" in args[0]:
                await self.list_remove(ctx, db, args[1:])
        else:
            await self.list_display(ctx, db, args)
            return

    @commands.command('register',help='Register for notifications')
    async def register(self, ctx):
        self.dCursor.execute("SELECT * FROM RegisteredUsers WHERE authorID IS '{}'".format(ctx.author.id))
        result = self.dCursor.fetchall()
        if len(result) != 0:
            await ctx.send(f"```css\n{ctx.author} is already registered!```")
        else:
            self.dCursor.execute("INSERT INTO RegisteredUsers VALUES ('{}', '{}')".format(ctx.author, ctx.author.id))
            self.database.commit()
            await ctx.send(f"```css\n{ctx.author} registered!```")

    @commands.command('unregister', help='Unregisters for notifications')
    async def unregister(self, ctx):
        self.dCursor.execute("SELECT * FROM RegisteredUsers WHERE authorID IS '{}'".format(ctx.author.id))
        result = self.dCursor.fetchall()
        if len(result) != 0:
            self.dCursor.execute("DELETE FROM RegisteredUsers WHERE authorID IS '{}'".format(ctx.author.id))
            await ctx.send(f"```css\n{ctx.author} unregistered```")
        else:
            await ctx.send(f"```css\n{ctx.author} was never registered!```")

    @commands.command('announce', help='announces shit')
    async def announce(self, ctx):
        self.dCursor.execute("SELECT * FROM VerifiedHosts WHERE authorID IS {}".format(ctx.author.id))
        if len(self.dCursor.fetchall()) > 0:
            embed=discord.Embed(title="Movie Night is starting soon!", description="", color=0xF79202)
            toPrint = ""
            time = self._getTime()
            tt = _getTimeTill(time)
            self.dCursor.execute("SELECT * FROM SelectedMovie")
            result = self.dCursor.fetchall()
            embed=discord.Embed(title="Movie Night is starting soon!", description=result[0][3], color=0xF79202)
            if result[0][0] == 'None':
                embed.add_field(name="No movie planned", value="Maybe some other time")
            else:
                if result[0][6] != 'None':
                    embed.set_thumbnail(url=result[0][6])
                embed.add_field(name="{} - IMDb: {}/10".format(result[0][0], result[0][4]), value="{}\n[IMDb]({})".format(result[0][1], result[0][5]))
            embed.add_field(name="Time until", value=tt, inline=False)
            embed.set_footer(text="Requested by {}".format(ctx.author))
            await ctx.send(embed=embed)

            # Ping people
            self.dCursor.execute("SELECT * FROM RegisteredUsers")
            results = self.dCursor.fetchall()
            for result in results:
                try:
                    member = await ctx.guild.fetch_member(int(result[1]))
                    toPrint += member.mention + " "
                except Exception:
                    continue
            await ctx.send(toPrint)
        else:
            await ctx.send("```css\nnope```")

    @commands.command('sql',help='Register for notifications')
    async def sql(self, ctx, *args):
        if str(ctx.author.id) == '154422225275977728':
            sqlQuery = ""
            for arg in args:
                sqlQuery += arg + " "
            sqlQuery = sqlQuery[:-1]
            self.dCursor.execute(sqlQuery)
            self.database.commit()
            await ctx.send('```' + str(self.dCursor.fetchall()) + '```')
        else:
            await ctx.send("You can't use this command")

    async def list_add(self, ctx, db, *args):
        message = await ctx.send("```Searching....```")
        dbname = ""
        if db == "FutureMovies":
            dbname = "WatchList"
        elif db == "WatchedMovies":
            dbname = "WatchedList"
        print(dbname + " add")
        title = _getTitle(args)
        try:
            # Get top 3 results
            top3 = self.ia.getTop3(title)

            # No results found
            if len(top3) == 0:
                await message.edit(content="```No movies found```")
            # Picking from top 3 results
            await self._outputTop3(ctx, "Reply the correct movie number or cancel to pick none", top3, message)
            def check(m):
                valid = True
                try:
                    if m.content == "cancel":
                        return valid and m.author == ctx.author and m.channel == ctx.channel
                    num = int(m.content)
                    if num < 1 or num > 3:
                        valid = False
                except Exception:
                    valid = False
                return valid and m.author == ctx.author and m.channel == ctx.channel
            response = await self.bot.wait_for('message', check=check)
            if response.content == "cancel":
                await message.edit(content="```No movie picked```",embed=None)
                return
            movie = top3[int(response.content) - 1]

            # Add to database
            self.dCursor.execute("SELECT * FROM {} WHERE imdbID = '{}'".format(db, movie[3]))
            result = self.dCursor.fetchall()
            print(result)
            if len(result) == 0:
                print("INSERT INTO {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                     db, movie[0], datetime.datetime.now().strftime("%b %d"), movie[2], movie[3], movie[1], movie[4], movie[5]))
                self.dCursor.execute("INSERT INTO {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                     db, movie[0], datetime.datetime.now().strftime("%b %d"), movie[2], movie[3], movie[1], movie[4], movie[5]))
                self.database.commit()
                # If adding to watched movies and that movie is in the watchlist, remove from the watchlist
                toSend = "```"
                if db == "WatchedMovies":
                    self.dCursor.execute("SELECT * FROM {} WHERE imdbID = '{}'".format("FutureMovies", movie[3]))
                    result = self.dCursor.fetchall()
                    if len(result) != 0:
                        self.dCursor.execute("DELETE FROM {} WHERE imdbID IS '{}'".format("FutureMovies", movie[3]))
                        self.database.commit()
                        toSend += "\nRemoved {} from {}```".format(result[0][0], "Watchlist")
                    self.dCursor.execute("SELECT * FROM {} WHERE imdbID = '{}'".format("SelectedMovie", movie[3]))
                    result = self.dCursor.fetchall()
                    if len(result) != 0:
                        self.dCursor.execute("UPDATE SelectedMovie SET name='{}' WHERE imdbid IS '{}'".format('None', movie[3]))
                        self.database.commit()
                        toSend += ("\nRemoved {} from {}```".format(result[0][0], "nextup"))
                toSend += "\nAdded {} to the {}```".format(movie[0], dbname)
                await ctx.send(toSend)
            else: # Movie already added (probably)
                await ctx.send("```Unable to add {} to the {}\nIs it already added?```".format(movie[0], dbname))

        except Exception as e:
            traceback.print_exc()

    async def list_display(self, ctx, db, *args):
        title = ""
        if db == "FutureMovies":
            title = "WatchList"
        elif db == "WatchedMovies":
            title = "WatchedList"
        print(title + " display")
        self.dCursor.execute("SELECT * FROM {}".format(db))
        results = self.dCursor.fetchall()
        i = 0
        j = 1
        embed=discord.Embed(title="{} {}/{}".format(title, j, int(len(results)/10.1) + 1), description="", color=0xF79202)
        for result in results:
            # Avoiding max embed limit by sending two messages
            if i % 10 == 0 and i != 0:
                embed.set_footer(text="Requested by {}".format(ctx.author))
                await ctx.send(embed=embed)
                j += 1
                embed=discord.Embed(title="{} {}/{}".format(title, j, int(len(results)/10.1) + 1), description="", color=0xF79202)
                embed.set_footer(text="Requested by {}".format(ctx.author))
                embed.clear_fields()
            print(result)
            if db == "FutureMovies":
                embed.add_field(name="{} - {}/10".format(result[0], result[4]), value="[IMDb]({})".format(result[5]), inline=False)
            elif db == "WatchedMovies":
                embed.add_field(name="{}:\t{} - {}/10".format(result[1], result[0], result[4]), value="[IMDb]({})".format(result[5]), inline=False)
            i += 1
        embed.set_footer(text="Requested by {}".format(ctx.author))
        await ctx.send(embed=embed)

    async def list_remove(self, ctx, db, *args):
        dbname = ""
        if db == "FutureMovies":
            dbname = "WatchList"
        elif db == "WatchedMovies":
            dbname = "WatchedList"
        print(dbname + " remove")
        title = _getTitle(args)
        self.dCursor.execute("SELECT * FROM {} WHERE name LIKE '%{}%'".format(db, title))
        print("SELECT * FROM {} WHERE name LIKE '%{}%'".format(db, title))
        result = self.dCursor.fetchall()
        print(result)
        if len(result) == 0:
            await ctx.send("```No results found for {}```".format(title))
        elif len(result) > 1:
            await ctx.send("```Multiple results found for {}```".format(title))
        else:
            self.dCursor.execute("DELETE FROM {} WHERE imdbID IS '{}'".format(db, result[0][3]))
            self.database.commit()
            await ctx.send("```Removed {} from {}```".format(result[0][0], dbname))

    async def watchlist_watched(self, ctx, *args):
        print("watchlist watched")
        title = _getTitle(args)
        self.dCursor.execute("SELECT * FROM FutureMovies WHERE name LIKE '%{}%'".format(title))
        result = self.dCursor.fetchall()
        print(result)
        if len(result) == 0:
            await ctx.send("```No results found for {}```".format(title))
        elif len(result) > 1:
            await ctx.send("```Multiple results found for {}```".format(title))
        else:
            toSend = '```'
            self.dCursor.execute("DELETE FROM FutureMovies WHERE imdbID IS '{}'".format(result[0][3]))
            self.database.commit()
            self.dCursor.execute("INSERT INTO WatchedMovies VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                  result[0][0], result[0][1], result[0][2], result[0][3], result[0][4], result[0][5], result[0][6]))
            self.database.commit()
            toSend += "\nRemoved {} from watchlist\nAdding {} to watchedlist".format(result[0][0], result[0][0])
            self.dCursor.execute("SELECT * from {} WHERE imdbID = '{}'".format("SelectedMovie", result[0][3]))
            result = self.dCursor.fetchall()
            if len(result) != 0:
                self.dCursor.execute("UPDATE SelectedMovie SET name='{}' WHERE imdbid IS '{}'".format('None', result[0][3]))
                self.database.commit()
                toSend += "\nRemoved {} from {}".format(result[0][0], "nextup")
            await ctx.send(toSend + '```')

    def _databaseInitial(self):
        # Create tables
        self.dCursor.execute('''CREATE TABLE WatchedMovies
                            (name text, date text, desciption text, imdbID text, rating text, imdbLink text, imdbCover text)''')
        self.dCursor.execute('''CREATE TABLE FutureMovies
                            (name text, date text, desciption text, imdbID text, rating text, imdbLink text, imdbCover text)''')
        self.dCursor.execute('''CREATE TABLE RegisteredUsers
                            (author text, authorID text)''')
        self.dCursor.execute('''CREATE TABLE SelectedMovie
                            (name text, desciption text, imdbID text, watchtime text, rating text, imdbLink text, imdbCover text)''')
        self.dCursor.execute("INSERT INTO SelectedMovie VALUES ('None', 'None', 'None', '{}', '0', 'None', 'None')".format(datetime.datetime.now().strftime("%A, %B %d, %Y at %I:%M%p CST")))
        self.dCursor.execute('''CREATE TABLE VerifiedHosts (author text, authorID text)''')
        self.database.commit()

    def _getTime(self):
        self.dCursor.execute("SELECT * FROM SelectedMovie")
        result = self.dCursor.fetchall()
        return datetime.datetime.strptime(result[0][3], '%A, %B %d, %Y at %I:%M%p CST')

    async def _outputTop3(self, ctx, title, top3, edit=None):
        embed=discord.Embed(title=title, description="", color=0xF79202)
        if top3[0][5] is not None:
            embed.set_thumbnail(url=top3[0][5])
        i = 1
        for result in top3:
            embed.add_field(name="{}.\t{} - IMDb {}/10".format(i, result[0], result[1]), value="{}\n[IMDb]({})\n".format(result[2], result[4]), inline=False)
            i += 1
        embed.set_footer(text="Requested by {}".format(ctx.author))
        if edit is not None:
            await edit.edit(content="", embed=embed)
        else:
            await ctx.send(embed=embed)

