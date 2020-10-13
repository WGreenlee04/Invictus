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


class DisquidClient(discord.Client):
    """
    Main body for the Discord Client interface for the project.
    Documentation Quick Reference https://discordpy.readthedocs.io/en/latest/api.html#
    """

    default_prefix = '*'
    auto_save_duration = 300  # in seconds
    admins: []

    def __init__(self, data_path: Path = Path('data/'), prefix_file_name: str = 'prefixes',
                 admin_file_name: str = 'admins', player_file_name: str = 'players', game_file_name: str = 'games',
                 **options):
        super().__init__(**options)
        self.data_path = data_path
        self.prefix_file = data_path.joinpath(prefix_file_name + '.json')
        self.admin_file = data_path.joinpath(admin_file_name + '.json')
        self.player_file = data_path.joinpath(player_file_name + '.pickle')
        self.game_file = data_path.joinpath(game_file_name + '.pickle')

        # Data directory loading
        if not os.path.exists(self.data_path):
            os.mkdir(self.data_path)

        # Prefix file loading
        if not os.path.exists(self.prefix_file):
            with open(self.prefix_file, 'w') as f:
                json.dump({}, f)
            self.prefixes: {int, str} = {}
        else:
            with open(self.prefix_file, 'r') as f:
                temp: {} = json.load(f)
                self.prefixes = {int(k): v for k, v in temp.items()}

        # Admin id file loading:
        if not os.path.exists(self.admin_file):
            with open(self.admin_file, 'w') as f:
                temp = [int(i) for i in input('Please give the starter admin(s)\'(s) '
                                              'userID(s) separated by a comma and a space.').split(', ')]
                json.dump(temp, f)
            DisquidClient.admins = temp
        else:
            with open(self.admin_file, 'r') as f:
                temp: [] = json.load(f)
                DisquidClient.admins = [int(i) for i in temp]

        # Player file loading
        if not os.path.exists(self.player_file):
            with open(self.player_file, 'wb') as f:
                pickle.dump({}, f)
            self.players: {int, Player} = {}
        else:
            with open(self.player_file, 'rb') as f:
                self.players: {int, Player} = pickle.load(f)

        # Active Game file loading
        if not os.path.exists(self.game_file):
            with open(self.game_file, 'wb') as f:
                pickle.dump({}, f)
            self.active_games: {int, Game} = {}
        else:
            with open(self.game_file, 'rb') as f:
                self.active_games: {int, Game} = pickle.load(f)

        # Adding auto save
        async def auto_save(duration: int):
            while True:
                await asyncio.sleep(duration)
                self.save()

        asyncio.run_coroutine_threadsafe(auto_save(DisquidClient.auto_save_duration), asyncio.get_event_loop())

    def get_prefix(self, gid: discord.Guild.id):
        """
        Returns the prefix for a given guild.
        :return: The prefix of the given guild.
        """
        try:
            return self.prefixes[gid]
        except KeyError:  # in case of failure of the on_guild_join event
            self.prefixes[gid] = self.default_prefix
            return self.default_prefix

    @save_action
    def save_prefixes(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.prefix_file, 'w') as f:
            f.truncate(0)
            json.dump(self.prefixes, f, indent=4)

    @save_action
    def save_admins(self):
        """
        Saves current dict of prefixes to a file using JSON.
        """
        with open(self.admin_file, 'w') as f:
            f.truncate(0)
            json.dump(DisquidClient.admins, f, indent=4)

    @save_action
    def save_players(self):
        """
        Saves current dict of players to a file using pickle.
        """
        with open(self.player_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(self.players, f)

    @save_action
    def save_game(self):
        """
        Saves current state of all levels to a file using pickle.
        """
        with open(self.game_file, 'wb') as f:
            f.truncate(0)
            pickle.dump(self.active_games, f)

    async def on_ready(self):
        """
        Called when bot is setup and ready.
        Put any startup actions here.
        """
        print(f'DungeonController {__version__} ready.')

    async def on_guild_join(self, guild: discord.Guild):
        """
        This is called when the bot is invited to and joins a new "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        self.prefixes[guild.id] = self.default_prefix

    async def on_guild_leave(self, guild: discord.Guild):
        """
        This is called when a bot leaves a "server".
        :param guild: Guild Class joined found at https://discordpy.readthedocs.io/en/latest/api.html#guild.
        """
        del self.prefixes[guild.id]

    async def on_message(self, message: discord.Message):
        """
        Called when a message is sent in a channel available to the bot.
        :param message: Message Class found at https://discordpy.readthedocs.io/en/latest/api.html#message.
        """

        if not self.is_ready() or not message.content or message.author.bot:
            return

        prefix = self.get_prefix(message.guild.id)
        if len(str(message.content)) >= len(prefix) and prefix == str(message.content)[:len(prefix)]:
            cmd = str(message.content).strip(prefix).split()[0].lower()
            try:
                await commands[cmd](self, message=message)
            except KeyError:
                print('User tried nonexistent command')

    @command(['help', 'h'])
    async def help_command(self, message: discord.Message):
        """
        [*, moves, tiles] Provides descriptions of commands.
        """
        is_admin = message.author.id in DisquidClient.admins
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
    async def ping(self, message: discord.Message):
        """
        PONG! Sends the bot's latency.
        """
        await message.channel.send(f'{self.latency * 1000}ms')

    @command(['changeprefix', 'cp'])
    async def change_prefix(self, message: discord.Message):
        """
        [prefix] Usable by admins to change the bot's server prefix.
        """
        if message.author.guild_permissions.administrator:
            processed_message = str(message.content).split()
            del processed_message[0]
            if len(processed_message) == 0:
                await message.channel.send('No prefix argument provided.')
                return
            self.prefixes.pop(message.guild.id)
            self.prefixes[message.guild.id] = processed_message[0]
            await message.guild.me.edit(nick=f'[{processed_message[0]}] ' + str(message.guild.me.name))
            await message.channel.send(f'Prefix is now \'{processed_message[0]}\'')
        else:
            await message.channel.send('Only administrators may do this.')

    @command(['profile'])
    async def player_profile(self, message: discord.Message):
        """
        [@mention/name] views a given player's profile.
        """
        pass

    @command(['top'])
    async def leaderboard(self, message: discord.Message):
        """
        Displays the top 10 players worldwide.
        """
        pass

    @command(['c'])
    async def challenge(self, message: discord.Message):
        """
        [@mention/name] Initiates a challenge against another player.
        """
        pass

    @command(['a'])
    async def accept(self, message: discord.Message):
        """
        [@mention/name] Accepts an existing challenge from another user.
        """
        pass

    @command(['changename', 'name'])
    async def change_name(self, message: discord.Message):
        """
        [name] Changes the name of the user who sends the message,
        as well as all of the user's custom emoji.
        """
        pass

    @command(['save'], True)
    async def save_command(self, message: discord.Message = None):
        """
        Called by a bot admin to save all files in the bot.
        """
        if message.author.id in DisquidClient.admins:
            self.save()
            await message.channel.send('Save Successful.')
        else:
            await message.channel.send('Insufficient user permissions.')

    @command(['exit', 'stop'], True)
    async def exit_command(self, message: discord.Message):
        """
        Called by a bot admin to exit the bot.
        """
        if message.author.id in DisquidClient.admins:
            await message.channel.send('Shutting down.')
            await self.close()
        else:
            await message.channel.send('Insufficient user permissions')

    @command(['op'], True)
    async def promote(self, message: discord.Message):
        """
        [@mention] Called by a bot admin to promote a new bot admin.
        """
        if message.author.id in DisquidClient.admins:
            mentions = message.mentions
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                if mention.id not in DisquidClient.admins:
                    DisquidClient.admins.append(mention.id)
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
        if message.author.id in DisquidClient.admins:
            if len(mentions) == 0:
                await message.channel.send('No argument provided!')
            for mention in mentions:
                DisquidClient.admins.remove(mention.id)
                await message.channel.send(f'@<{mention.id}> is no longer an admin.')
        else:
            await message.channel.send('Insufficient user permissions.')

    def save(self):
        """
        Goes through 
        """
        for fun in save_actions:
            fun(self)
        return

    async def close(self):
        self.save()
        await super(DisquidClient, self).close()


if __name__ == '__main__':
    DisquidClient().run(input('Bot API Token: '))
