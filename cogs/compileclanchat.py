import discord
from discord.ext import commands
from discord.commands import Option
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import re  # Add regex import

class CompileClanChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("CompileClanChat cog loaded")

    def extract_username(self, content: str) -> str:
        """
        Extract username from message content using regex.
        Handles eleven formats:
        1. **username**:
        2. username has achieved a new
        3. username received a drop
        4. username received a new collection log item
        5. username has reached [skill] level
        6. username has reached [number] XP in [skill]
        7. username has completed a [difficulty] combat task
        8. username has a funny feeling
        9. username has been defeated
        10. username has defeated
        11. username has deposited [number] coins into the coffer
        Returns the username if found, None otherwise.
        """
        # Pattern for **username**: format
        pattern1 = r"\*\*(.*?)\*\*"
        # Pattern for username has achieved a new format
        pattern2 = r"^(.*?)\s+has\s+achieved\s+a\s+new"
        # Pattern for username received a drop format
        pattern3 = r"^(.*?)\s+received\s+a\s+drop"
        # Pattern for username received a new collection log item format
        pattern4 = r"^(.*?)\s+received\s+a\s+new\s+collection\s+log\s+item"
        # Pattern for username has reached [skill] level format
        skills = [
            "Sailing", "Hunter", "Construction", "Farming", "Slayer", "Runecraft",
            "Agility", "Thieving", "Fletching", "Herblore", "Fishing", "Magic",
            "Prayer", "Crafting", "Attack", "Hitpoints", "Cooking", "Defence",
            "Firemaking", "Mining", "Ranged", "Smithing", "Strength", "Woodcutting",
            "combat", "total"
        ]
        skills_pattern = "|".join(skills)
        pattern5 = rf"^(.*?)\s+has\s+reached\s+({skills_pattern})\s+level"
        # Pattern for username has reached [number] XP in [skill] format
        pattern6 = rf"^(.*?)\s+has\s+reached\s+([0-9,]+)\s+XP\s+in\s+({skills_pattern})"
        # Pattern for username has completed a [difficulty] combat task format
        difficulties = ["easy", "medium", "hard", "elite", "master", "grandmaster"]
        difficulties_pattern = "|".join(difficulties)
        pattern7 = rf"^(.*?)\s+has\s+completed\s+a\s+({difficulties_pattern})\s+combat\s+task"
        # Pattern for username has a funny feeling format
        pattern8 = r"^(.*?)\s+has\s+a\s+funny\s+feeling"
        # Pattern for username has been defeated format
        pattern9 = r"^(.*?)\s+has\s+been\s+defeated"
        # Pattern for username has defeated format
        pattern10 = r"^(.*?)\s+has\s+defeated"
        # Pattern for username has deposited [number] coins into the coffer format
        pattern11 = r"^(.*?)\s+has\s+deposited\s+[0-9,]+\s+coins\s+into\s+the\s+coffer"
        
        # Try all patterns
        match1 = re.search(pattern1, content)
        match2 = re.search(pattern2, content)
        match3 = re.search(pattern3, content)
        match4 = re.search(pattern4, content)
        match5 = re.search(pattern5, content)
        match6 = re.search(pattern6, content)
        match7 = re.search(pattern7, content)
        match8 = re.search(pattern8, content)
        match9 = re.search(pattern9, content)
        match10 = re.search(pattern10, content)
        match11 = re.search(pattern11, content)
        
        if match1:
            return match1.group(1)
        elif match2:
            return match2.group(1)
        elif match3:
            return match3.group(1)
        elif match4:
            return match4.group(1)
        elif match5:
            return match5.group(1)
        elif match6:
            return match6.group(1)
        elif match7:
            return match7.group(1)
        elif match8:
            return match8.group(1)
        elif match9:
            return match9.group(1)
        elif match10:
            return match10.group(1)
        elif match11:
            return match11.group(1)
        return None

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

            total_messages = 0
            message_count_processed = 0 # Counter for debugging progress
            loop_finished_normally = False # Flag to check loop exit
            user_message_counts = defaultdict(int) # Dictionary to track user message counts

            print(f"Fetching messages from #{channel.name} between {start} and {end} to count lines (using async for)")
            async for message in channel.history(limit=None, after=start, before=end):
                message_count_processed += 1
                print('messages read: ' + str(message_count_processed))
                # Optional progress print and delay
                if message_count_processed % 100 == 0: 
                    print(f"  Processed {message_count_processed} messages...")
                    await asyncio.sleep(1) # Add 1 second delay to ease rate limits
                
                # Include bot messages, but only count lines if there's text content
                if message.content:
                    # Split message content by newlines and process each line
                    for line in message.content.split('\n'):
                        if line.strip():  # Only process non-empty lines
                            print(line)
                            total_messages += 1  # Counts messages with content
                            # Use the new extract_username function
                            username = self.extract_username(line)
                            if username:
                                print('Found username: ' + username)
                                user_message_counts[username] += 1
            
            loop_finished_normally = True # Set flag if loop completes
            print(f"Loop finished normally: {loop_finished_normally}")
            print(f"Finished processing. Found {total_messages} messages (including bots) with text content.")

            if total_messages == 0:
                await ctx.followup.send(f"No messages (including bots) with text content found in #{channel.name} between {start_date} and {end_date}.", ephemeral=True)
                return

            # Prepare the results message
            result_message = f"**Message Statistics for #{channel.name} ({start_date} to {end_date})**\n\n"
            result_message += f"Total Messages Checked with Content: {total_messages}\n\n"
            result_message += "**User Message Counts:**\n"
            
            # Sort users by message count in descending order
            sorted_users = sorted(user_message_counts.items(), key=lambda x: x[1], reverse=True)
            
            # Split the message into chunks of 2000 characters or less
            current_chunk = result_message
            pts = 0
            for username, count in sorted_users:
                if int(count) > 400:
                    pts = 100
                elif int(count) > 200:
                    pts = 50
                elif int(count) > 100:
                    pts = 25
                user_line = f"{username}: {count} messages, awarding {pts}xp\n"
                # If adding this line would exceed 2000 characters, send current chunk and start new one
                if len(current_chunk) + len(user_line) > 1980: #2000 is the char limit
                    await ctx.followup.send(current_chunk, ephemeral=True)
                    current_chunk = user_line
                else:
                    current_chunk += user_line
                pts = 0
            
            # Send any remaining content
            if current_chunk:
                await ctx.followup.send(current_chunk, ephemeral=True)

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