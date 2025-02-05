import discord
from discord.ext import commands
from discord.ext import tasks
from discord import app_commands
import asyncio
import os
from petpet import make
from bot_utility import *

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='/', intents=intents)

@tasks.loop(minutes=60) 
async def auto_update():
    await check_for_update()
    
@auto_update.before_loop
async def before_start():
    await bot.wait_until_ready()

@bot.event
async def on_ready():
    auto_update.start()
    await bot.tree.sync()
    await bot.change_presence(activity=discord.Game(name="Princess Connect! Re:Dive"))

    print('Neneka is ready to take commands!')

@bot.tree.command(name="review", description="Review a unit")
@app_commands.describe(unit_name='[STRING] The name or nickname of the unit to review (i.e. neneka, nnk, nene etc)')
async def review(interaction: discord.Interaction, unit_name: str):
    unit_name = unit_name.lower()

    if unit_name == 'afhie':
        unit_name = 'cyui'

    await interaction.response.defer()

    embeds = unit_review(unit_name)
    
    if len(embeds) == 2:
        current_embed = 0

        followup_message = await interaction.followup.send(embed=embeds[current_embed])

        await followup_message.add_reaction("⬅️")
        await followup_message.add_reaction("➡️")

        def check(reaction, user):
            return (str(reaction.emoji) in ["⬅️", "➡️"] and
                    reaction.message.id == followup_message.id)

        while True:
            try:
                reaction, user = await bot.wait_for("reaction_add", timeout=120.0, check=check)
                if str(reaction.emoji) == "➡️":
                    current_embed = (current_embed + 1) % len(embeds)
                elif str(reaction.emoji) == "⬅️" and current_embed > 0:
                    current_embed = (current_embed - 1) % len(embeds)
                await followup_message.edit(embed=embeds[current_embed])
                await followup_message.remove_reaction(reaction, user)
            except asyncio.TimeoutError:
                await followup_message.clear_reactions()
                break
    else:
        followup_message = await interaction.followup.send(embed=embeds)
        await asyncio.sleep(120)
        await followup_message.delete()

@bot.tree.command(name="list", description="List every units")
async def list(interaction: discord.Interaction):
    embed = discord.Embed(title=f"As of now, there are {len(units)} units in the game",
                          description='These names and nicknames can be used with the /review command but you dont have to type them exactly. For example: /review neneka, /review nnk and /review nene all give review for neneka',
                          color=discord.Colour.from_rgb(255, 255, 255))
    for field_value in unit_columns(units):
        embed.add_field(name='\u200B', value=field_value, inline=True)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name="bless", description="Bless someone")
@app_commands.describe(username='[STRING] Discord username of who you would like to bless (i.e. ripsol5k)')
async def bless(interaction: discord.Interaction, username: str):
    for member in bot.get_all_members():
        if member.name == username:
            await interaction.response.send_message(file=discord.File(image_utility(member.avatar.url), filename='nozomibless.png'))
            return
    await interaction.response.send_message('Discord user not found', ephemeral=True)

@bot.tree.command(name='pat', description='pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat pat')
@app_commands.describe(username='[STRING] Discord username of who you would like to pat (i.e. ripsol5k)')
async def pat(interaction: discord.Interaction, username: str):
    for member in bot.get_all_members():
        if member.name == username:
            make(image_utility(member.avatar.url, 2), 'Images/pat.gif')
            await interaction.response.send_message(file=discord.File('Images/pat.gif'))
            return
    await interaction.response.send_message('Discord user not found', ephemeral=True)

bot.run(os.getenv('DISCORD_BOT_TOKEN'))