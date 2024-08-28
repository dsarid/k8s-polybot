import discord
import os
import polybot_helper_lib
import json

# GUILD = "bot-test"
TOKEN = json.loads(polybot_helper_lib.get_secret("DISCORD_BOT_TOKEN")).get('DISCORD_BOT_TOKEN')
intents = discord.Intents.default()

client = discord.Client(intents=intents)

@client.event
async def on_ready():
    # my_guild = None
    # for guild in client.guilds:
    #     if guild.name == GUILD:
    #         my_guild = guild
    #         break

    print(
        f'{client.user} is connected to the following guild:\n'
        # f'{my_guild.name}(id: {my_guild.id})'
    )

client.run(TOKEN)
