import datetime
import asyncio
import os
import traceback
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
        message = await ctx.send("```Working...```")
        time = self.__getTime()
        tt = _getTimeTill(time)
        self.dCursor.execute("SELECT * FROM SelectedMovie")
        result = self.dCursor.fetchall()
        embed=discord.Embed(title="Movie Night", description=result[0][3], color=0xF79202)
        if result[0][0] == 'None':
            embed.add_field(name="No movie planned", value="Maybe some other time")
        else:
            cover = self.ia.getCover(result[0][2])
            if cover is not None:
                embed.set_thumbnail(url=cover)
            embed.add_field(name="{} - IMDb: {}/10".format(result[0][0], result[0][4]), value="{}\n[IMDb]({})".format(result[0][1], result[0][5]))
        embed.add_field(name="Time until", value=tt, inline=False)
        embed.set_footer(text="Requested by {}".format(ctx.author))
        await message.edit(content="", embed=embed)

    @commands.command('help')
    async def help(self,ctx):
        try:
            cmds_desc = '```css\n'
            hidden = ["refresh", "clear", "autoannounce", "announce", "setTime", "listregistered", "help"]
            for y in self.bot.walk_commands():
                if y.name not in hidden:
                    cmds_desc += ("[!mn {}]\n{}\n\n".format(y.name, y.help))
            cmds_desc += "```"
            await ctx.send(cmds_desc)
        except Exception as e:
            print(type(e))
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
            await self._outputTop3(ctx, "Reply the correct movie number", top3, message)
            def check(m):
                valid = True
                try:
                    num = int(m.content)
                    if num < 1 or num > 3:
                        valid = False
                except Exception:
                    valid = False
                return valid and m.author == ctx.author and m.channel == ctx.channel
            response = await self.bot.wait_for('message', check=check)
            movie = top3[int(response.content) - 1]
            
            # Add to database
            self.dCursor.execute("SELECT * from {} WHERE imdbID = '{}'".format(db, movie[3]))
            result = self.dCursor.fetchall()
            print(result)
            if len(result) == 0:
                self.dCursor.execute("INSERT INTO {} VALUES ('{}', '{}', '{}', '{}', '{}', '{}', '{}')".format(
                                     db, movie[0], datetime.datetime.now().strftime("%b %d"), movie[2], movie[3], movie[1], movie[4], movie[5]))
                self.database.commit()
                # If adding to watched movies and that movie is in the watchlist, remove from the watchlist
                if db == "WatchedMovies":
                    self.dCursor.execute("SELECT * from {} WHERE imdbID = '{}'".format("FutureMovies", movie[3]))
                    result = self.dCursor.fetchall()
                    if len(result) != 0:
                        self.dCursor.execute("DELETE FROM {} WHERE imdbID IS '{}'".format("FutureMovies", movie[3]))
                        self.database.commit()
                        await ctx.send("```Removing {} from {}```".format(result[0][0], "Watchlist"))
                    self.dCursor.execute("SELECT * from {} WHERE imdbID = '{}'".format("SelectedMovie", movie[3]))
                    result = self.dCursor.fetchall()
                    if len(result) != 0:
                        self.dCursor.execute("UPDATE SelectedMovie SET name='{}' WHERE imdbid IS '{}'".format('None', movie[3]))
                        self.database.commit()
                        await ctx.send("```Removing {} from {}```".format(result[0][0], "nextup"))
                await ctx.send("```Added {} to the {}```".format(movie[0], dbname))
            else: # Movie already added (probably)
                await ctx.send("```Unable to add {} to the {}\nIs it already added?```".format(movie[0], dbname))

        except Exception as e:
            traceback.print_exc()

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
            time = self.__getTime()
            tt = _getTimeTill(time)
            self.dCursor.execute("SELECT * FROM SelectedMovie")
            result = self.dCursor.fetchall()
            embed=discord.Embed(title="Movie Night is starting soon!", description=result[0][3], color=0xF79202)
            if result[0][0] == 'None':
                embed.add_field(name="No movie planned", value="Maybe some other time")
            else:
                cover = self.ia.getCover(result[0][2])
                if cover is not None:
                    embed.set_thumbnail(url=cover)
                embed.add_field(name="{} - IMDb: {}/10".format(result[0][0], result[0][4]), value="{}\n[IMDb]({})".format(result[0][1], result[0][5]))
            embed.add_field(name="Time until", value=tt, inline=False)
            embed.set_footer(text="Requested by {}".format(ctx.author))
            await ctx.send(embed=embed)

            # Ping people
            self.dCursor.execute("SELECT * FROM RegisteredUsers")
            results = self.dCursor.fetchall()
            for result in results:
                toPrint += self.bot.get_user(int(result[1])).mention + " "
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
        embed=discord.Embed(title="{} {}/{}".format(title, j, int(len(results)/25.1) + 1), description="", color=0xF79202)
        for result in results:
            # Avoiding max embed limit by sending two messages
            if i == 25:
                embed.set_footer(text="Requested by {}".format(ctx.author))
                await ctx.send(embed=embed)
                j += 1
                embed=discord.Embed(title="{} {}/{}".format(title, j, int(len(results)/25.1) + 1), description="", color=0xF79202)
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
            await ctx.send("```Removing {} from {}```".format(result[0][0], dbname))
    
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
            self.dCursor.execute("DELETE FROM FutureMovies WHERE imdbID IS '{}'".format(result[0][3]))
            self.database.commit()
            self.dCursor.execute("INSERT INTO WatchedMovies VALUES ('{}', '{}', '{}', '{}', '{}', '{}')".format(
                                  result[0][0], result[0][1], result[0][2], result[0][3], result[0][4], result[0][5]))
            self.database.commit()
            await ctx.send("```Removing {} from watchlist\nAdding {} to watchedlist```".format(result[0][0], result[0][0]))
            self.dCursor.execute("SELECT * from {} WHERE imdbID = '{}'".format("SelectedMovie", result[0][3]))
            result = self.dCursor.fetchall()
            if len(result) != 0:
                self.dCursor.execute("UPDATE SelectedMovie SET name='{}' WHERE imdbid IS '{}'".format('None', result[0][3]))
                self.database.commit()
                await ctx.send("```Removing {} from {}```".format(result[0][0], "nextup"))

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
    
    def __getTime(self):
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

