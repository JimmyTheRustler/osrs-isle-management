import discord
from discord.ext import commands
from discord.commands import Option

class Example(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.slash_command(name="test", description="A test command with options")
    async def test(
        self,
        ctx,
        message: Option(str, "The message to echo", required=True),
        repeat: Option(int, "Number of times to repeat", required=False, default=1)
    ):
        for _ in range(repeat):
            await ctx.respond(f'You said: {message}')
    @commands.slash_command(name="hello", description="Say hello to the bot")
    async def hello(self, ctx):
        await ctx.respond(f'Hello {ctx.author.name}! 👋')

    @commands.slash_command(name="ping", description="Check bot latency")
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000)
        await ctx.respond(f'Pong! Latency: {latency}ms')

def setup(bot):
    bot.add_cog(Example(bot)) 