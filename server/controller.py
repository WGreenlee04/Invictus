import asyncio
import pickle
import json
import os
from pathlib import Path

import discord

from server.storage import Player, Game

__version__ = 'v0.1beta'

"""
AUTHORS:
*William Greenlee

The MIT License (MIT)

Permission is hereby granted, free of charge, to any person obtaining a
copy of this software and associated documentation files (the "Software"),
to deal in the Software without restriction, including without limitation
the rights to use, copy, modify, merge, publish, distribute, sublicense,
and/or sell copies of the Software, and to permit persons to whom the
Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS
OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
DEALINGS IN THE SOFTWARE.
"""

commands: {callable} = {}
save_actions: [callable] = []


def command(aliases: [str] = None, hidden: bool = False):
    def decorator(function: callable):
        function.hidden = hidden
        commands[function.__name__] = function
        if aliases:
            for alias in aliases:
                commands[alias] = function
        return function

    return decorator


def save_action(function: callable):
    save_actions.append(function)
    return function


class Color:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def start():
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    client = discord.Client()

    default_prefix = '*'
    auto_save_duration = 300  # in seconds
    admins: []

    data_path = Path('data/')
    prefix_file = data_path.joinpath('prefixes.json')
    admin_file = data_path.joinpath('admins.json')
    player_file = data_path.joinpath('players.pickle')
    game_file = data_path.joinpath('game.pickle')

    # Data directory loading
    if not os.path.exists(data_path):
        os.mkdir(data_path)

    # Prefix file loading
    if not os.path.exists(prefix_file):
        with open(prefix_file, 'w') as f:
            json.dump({}, f)
            prefixes: {int, str} = {}
    else:
        with open(prefix_file, 'r') as f:
            temp: {} = json.load(f)
            prefixes = {int(k): v for k, v in temp.items()}

    # Admin id file loading:
    if not os.path.exists(admin_file):
        with open(admin_file, 'w') as f:
            temp = [int(i) for i in input('Please give the starter admin(s)\'(s) '
                                          'userID(s) separated by a comma and a space.').split(', ')]
            json.dump(temp, f)
            admins = temp
    else:
        with open(admin_file, 'r') as f:
            temp: [] = json.load(f)
            admins = [int(i) for i in temp]

    # Player file loading
    if not os.path.exists(player_file):
        with open(player_file, 'wb') as f:
            pickle.dump({}, f)
            players: {int, Player} = {}
    else:
        with open(player_file, 'rb') as f:
            players: {int, Player} = pickle.load(f)

    # Active Game file loading
    if not os.path.exists(game_file):
        with open(game_file, 'wb') as f:
            pickle.dump({}, f)
            active_games: {int, Game} = {}
    else:
        with open(game_file, 'rb') as f:
            active_games: {int, Game} = pickle.load(f)

    # Adding auto save
    async def auto_save(duration: int):
        while True:
            await asyncio.sleep(duration)
            save()

    asyncio.run_coroutine_threadsafe(auto_save(auto_save_duration), asyncio.get_event_loop())
    client.start(input('Bot API Token: '))

    def get_prefix(gid: discord.Guild.id):
        """
        Returns the prefix for a given guild.
        :return: The prefix of the given guild.
        """
        try:
            return prefixes[gid]
        except KeyError:  # in case of failure of the on_guild_join event
            prefixes[gid] = default_prefix
            return default_prefix

    @save_action
    def save_prefixes():
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(prefix_file, 'w') as f:
            f.truncate(0)
            json.dump(prefixes, f, indent=4)

    @save_action
    def save_admins():
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(admin_file, 'w') as f:
            f.truncate(0)
            json.dump(admins, f, indent=4)

    @save_action
    def save_players():
        """
        Saves current dict of players to a file using pickle.
        """
        with open(player_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(players, f)

    @save_action
    def save_game():
        """
        Saves current state of all levels to a file using pickle.
        """
        with open(game_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(active_games, f)

    async def on_ready():
        """
        Called when bot is setup and ready.
        Put any startup actions here.
        """
        print(f'DungeonController {__version__} ready.')

    async def on_guild_join(guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        prefixes[guild.id] = default_prefix

    async def on_guild_leave(guild: discord.Guild):
        """
        This is called when a bot leaves a "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        del prefixes[guild.id]

    async def on_message(message: discord.Message):
        """
        Called when a message is sent in a channel available to the bot.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        """

        if not client.is_ready() or not message.content or message.author.bot:
            return

        prefix = get_prefix(message.guild.id)
        if len(str(message.content)) >= len(prefix) and prefix == str(message.content)[:len(prefix)]:
            cmd = str(message.content).strip(prefix).split()[0].lower()
            try:
                await commands[cmd](message=message)
            except KeyError:
                print('User tried nonexistent command')

    @command(['help', 'h'])
    async def help_command(message: discord.Message):
        """
        [*, moves, tiles] Provides descriptions of commands.
        """
        is_admin = message.author.id in admins
        processed_message = str(message.content).split()
        del processed_message[0]
        if len(processed_message) == 0:
            active_descs = {}
            embed_vars = [discord.Embed(title='Help Commands', color=0xc0365e)]
            char_count = len(embed_vars[0].title)
            for key in commands:
                if not commands[key].hidden or is_admin:
                    aliases = []
                    for k in commands:
                        aliases.append(k) if commands[key] == commands[k] else aliases
                    if str(aliases) not in active_descs:
                        active_descs[str(aliases)] = commands[key].__doc__
                        char_count += len(str(aliases)) + len(str(commands[key].__doc__).replace('\n', ''))
                        if char_count >= 6000:
                            embed_vars.append(discord.Embed(title=f'Help Commands {len(embed_vars) + 1}',
                                                            color=0xc0365e))
                        embed_vars[-1].add_field(name=str(aliases), value=str(commands[key].__doc__).replace('\n', ''),
                                            inline=False)
            for embed_var in embed_vars:
                await message.channel.send(embed=embed_var)
        else:
            pass #other cases

    @command()
    async def ping(message: discord.Message):
        """
        PONG! Sends the bot's latency.
        """
        await message.channel.send(f'{client.latency * 1000}ms')

    @command(['changeprefix', 'cp'])
    async def change_prefix(message: discord.Message):
        """
        [prefix] Usable by admins to change the bot's server prefix.
        """
        if message.author.guild_permissions.administrator:
            processed_message = str(message.content).split()
            del processed_message[0]
            if len(processed_message) == 0:
                await message.channel.send('No prefix argument provided.')
                return
            prefixes.pop(message.guild.id)
            prefixes[message.guild.id] = processed_message[0]
            await message.guild.me.edit(nick=f'[{processed_message[0]}] ' + str(message.guild.me.name))
            await message.channel.send(f'Prefix is now \'{processed_message[0]}\'')
        else:
            await message.channel.send('Only administrators may do this.')

    @command(['profile'])
    async def player_profile(message: discord.Message):
        """
        [@mention/name] views a given player's profile.
        """
        pass

    @command(['top'])
    async def leaderboard(message: discord.Message):
        """
        Displays the top 10 players worldwide.
        """
        pass

    @command(['c'])
    async def challenge(message: discord.Message):
        """
        [@mention/name] Initiates a challenge against another player.
        """
        pass

    @command(['a'])
    async def accept(message: discord.Message):
        """
        [@mention/name] Accepts an existing challenge from another user.
        """
        pass

    @command(['changename', 'name'])
    async def change_name(message: discord.Message):
        """
        [name] Changes the name of the user who sends the message,
        as well as all of the user's custom emoji.
        """
        pass

    @command(['save'], True)
    async def save_command(message: discord.Message = None):
        """
        Called by a bot admin to save all files in the bot.
        """
        if message.author.id in admins:
            save()
            await message.channel.send('Save Successful.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['exit', 'stop'], True)
    async def exit_command(self, message: discord.Message):
        """
        Called by a bot admin to exit the bot.
        """
        if message.author.id in admins:
            await message.channel.send('Shutting down.')
            await close()
        else:
            await message.channel.send('Insufficient user permissions')

    @command(['op'], True)
    async def promote(message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        if message.author.id in admins:
            mentions = message.mentions
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                if mention.id not in admins:
                    admins.append(mention.id)
                    await message.channel.send(f'<@{mention.id}> is now an admin.')
                else:
                    await message.channel.send(f'<@{mention.id}> was already an admin!')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['deop'], True)
    async def demote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        mentions = message.mentions
        if message.author.id in admins:
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                admins.remove(mention.id)
                await message.channel.send(f'@<{mention.id}> is no longer an admin.')
        else:
            await message.channel.send('Insufficient user permissions.')

    def save():
        """
        Goes through and calls save actions of the bot.
        """
        for fun in save_actions:
            fun()
        return

    async def close():
        save()
        await client.close()


if __name__ == '__main__':
    start()