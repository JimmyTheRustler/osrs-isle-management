import discord
from discord.ext import commands
from discord.commands import Option
from datetime import datetime, timedelta
import asyncio

class CompileClanChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("CompileClanChat cog loaded")

    @commands.slash_command(
        name="compilecc",
        description="Count total lines of text in a channel within a date range"
    )
    async def compilecc(
        self,
        ctx,
        channel: discord.TextChannel,
        start_date: str = Option(
            description="Start date (YYYY-MM-DD)",
            required=True
        ),
        end_date: str = Option(
            description="End date (YYYY-MM-DD)",
            required=True
        )
    ):
        
        try:
            # Defer the response as fetching history might take time
            await ctx.defer(ephemeral=True)

            # Parse dates
            start = datetime.strptime(start_date, "%Y-%m-%d")
            end = datetime.strptime(end_date, "%Y-%m-%d")

            # Add time to make it cover the full day
            start = start.replace(hour=0, minute=0, second=0)
            end = end.replace(hour=23, minute=59, second=59)

            # Validate date range
            if start > end:
                await ctx.followup.send("Error: Start date must be before end date", ephemeral=True)
                return

            total_lines = 0
            total_messages = 0
            message_count_processed = 0 # Counter for debugging progress
            loop_finished_normally = False # Flag to check loop exit

            print(f"Fetching messages from #{channel.name} between {start} and {end} to count lines (using async for)")
            async for message in channel.history(limit=None, after=start, before=end):
                message_count_processed += 1
                # Optional progress print and delay
                if message_count_processed % 100 == 0: 
                    print(f"  Processed {message_count_processed} messages...")
                    await asyncio.sleep(1) # Add 1 second delay to ease rate limits
                
                # Include bot messages, but only count lines if there's text content
                if message.content:
                    total_lines += message.content.count('\n') + 1
                    total_messages += 1 # Counts messages *with content*
            
            loop_finished_normally = True # Set flag if loop completes
            print(f"Loop finished normally: {loop_finished_normally}")
            print(f"Finished processing. Found {total_messages} messages (including bots) with text content, containing {total_lines} lines.")

            if total_messages == 0:
                await ctx.followup.send(f"No messages (including bots) with text content found in #{channel.name} between {start_date} and {end_date}.", ephemeral=True)
                return

            # Prepare the results message
            result_message = f"**Total Lines in #{channel.name} ({start_date} to {end_date})**\n(Including Bot Messages)\n\n"
            result_message += f"Total Lines: {total_lines}\n"
            result_message += f"Total Messages Checked with Content: {total_messages}"

            # Send the results
            await ctx.followup.send(result_message, ephemeral=True)

        except ValueError:
            await ctx.followup.send("Error: Invalid date format. Please use YYYY-MM-DD", ephemeral=True)
        except discord.errors.Forbidden:
             await ctx.followup.send(f"Error: I don't have permission to read message history in #{channel.name}.", ephemeral=True)
        except AttributeError as e: # Catch potential AttributeError if channel is still a string
            if "'str' object has no attribute" in str(e):
                 await ctx.followup.send(f"Error: Failed to process channel object. Received type: {type(channel)}. Please report this.", ephemeral=True)
                 print(f"Still received string for channel: {channel}")
            else:
                 await ctx.followup.send(f"An unexpected error occurred: {str(e)}", ephemeral=True)
                 print(f"Error in compilecc: {e}") # Log the error for debugging
        except Exception as e:
            await ctx.followup.send(f"An unexpected error occurred: {str(e)}", ephemeral=True)
            print(f"Error in compilecc: {e}") # Log the error for debugging
            print(f"Loop finished normally: {loop_finished_normally}") # Print flag state even on error

def setup(bot):
    bot.add_cog(CompileClanChat(bot)) 