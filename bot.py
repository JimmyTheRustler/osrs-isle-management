import os
import discord
from discord.ext import commands
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot setup with default intents
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

# Create bot instance with command prefix '!' and enable slash commands
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'{bot.user} has connected to Discord!')
    print(f'Bot is in {len(bot.guilds)} guilds')
    
    # Sync commands for each guild
    for guild in bot.guilds:
        try:
            print(f"Syncing commands for guild: {guild.name}")
            await bot.sync_commands(guild_ids=[guild.id])
            print(f"Successfully synced commands for {guild.name}")
        except Exception as e:
            print(f"Failed to sync commands for {guild.name}: {e}")

# Error handling
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("Command not found. Use !help to see available commands.")
    else:
        await ctx.send(f"An error occurred: {str(error)}")

# Load all cogs
async def load_extensions():
    print("Loading cogs...")
    cogs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'cogs')
    for filename in os.listdir(cogs_dir):
        if filename.endswith('.py'):
            try:
                bot.load_extension(f'cogs.{filename[:-3]}')
                print(f'Successfully loaded extension: {filename[:-3]}')
            except Exception as e:
                print(f'Failed to load extension {filename[:-3]}: {e}')

# Run the bot
if __name__ == "__main__":
    token = str(os.getenv("DISCORD_TOKEN"))
    if not token:
        raise ValueError("No token found! Make sure to set DISCORD_TOKEN in .env file")
    
    async def main():
        await load_extensions()
        await bot.start(token)
    
    import asyncio
    asyncio.run(main()) 