import discord
from discord.ext import commands
from discord.commands import Option
from datetime import datetime, timedelta
import asyncio
from collections import defaultdict
import re
import os

class CompileClanChat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        print("CompileClanChat cog loaded")

    def write_to_output_file(self, sorted_users, date):
        """
        Write sorted user data to a text file with current month-year format.
        If a file for the current month-year exists, aggregate message counts and XP for existing users.
        """
        # Format the passed date to show month and year
        current_date = date.strftime('%m-%Y')
        file_name = f"output-{current_date}.txt"
        
        # Check if file exists
        file_exists = os.path.exists(file_name)
        
        try:
            # If file exists, read existing data
            existing_data = {}
            existing_xp = {}
            if file_exists:
                with open(file_name, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if ':' in line and 'messages' in line and 'awarding' in line:
                            # Parse existing data
                            parts = line.split(':')
                            username = parts[0].strip()
                            count = int(parts[1].split('messages')[0].strip())
                            xp = int(parts[1].split('awarding')[1].split('xp')[0].strip())
                            existing_data[username] = count
                            existing_xp[username] = xp

            # Calculate XP for new messages
            new_xp = {}
            for username, count in sorted_users:
                pts = 0
                if int(count) > 400:
                    pts = 100
                elif int(count) > 200:
                    pts = 50
                elif int(count) > 100:
                    pts = 25
                new_xp[username] = pts

            # Merge message counts and XP
            merged_data = {}
            for username, count in sorted_users:
                if username in existing_data:
                    merged_data[username] = {
                        'count': existing_data[username] + count,
                        'xp': existing_xp[username] + new_xp[username]
                    }
                else:
                    merged_data[username] = {
                        'count': count,
                        'xp': new_xp[username]
                    }

            # Sort the merged data by message count
            sorted_merged_data = sorted(merged_data.items(), key=lambda x: x[1]['count'], reverse=True)

            # Write the merged data back to file
            with open(file_name, 'w', encoding='utf-8') as f:
                # Write header
                f.write(f"Clan Chat Statistics - {current_date}\n")
                f.write("=" * 50 + "\n\n")
                
                # Write each user's data
                for username, data in sorted_merged_data:
                    f.write(f"{username}: {data['count']} messages, awarding {data['xp']}xp\n")
                
                # Add a separator at the end
                f.write("\n" + "-" * 50 + "\n\n")
            
            return True, file_name
        except Exception as e:
            print(f"Error writing to file: {e}")
            return False, str(e)

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
        12. username has completed the [difficulty] [area] diary
        13. username received special loot from a raid
        14. username has reached the highest possible total level of 2277
        15. username received a clue item
        16. username has unlocked the [tier] tier of rewards from Combat Achievements
        17. username has reached a total level of [number]
        18. username has been invited into the clan by
        19. username has opened a loot key worth [number]
        Returns the username if found, None otherwise.
        """

        # Strip content between < and > symbols
        content = re.sub(r'<[^>]+>', '', content)

        # Define username pattern that allows letters, numbers, spaces, and common special characters
        username_pattern = r'[A-Za-z0-9\s\-_]+'

        # Pattern for **username**: format
        pattern1 = rf"\s*\*\*({username_pattern})\*\*"
        # Pattern for username has achieved a new format
        pattern2 = rf"\s*({username_pattern})\s+has\s+achieved\s+a\s+new.*"
        # Pattern for username received a drop format
        pattern3 = rf"\s*({username_pattern})\s+received\s+a\s+drop.*"
        # Pattern for username received a new collection log item format
        pattern4 = rf"\s*({username_pattern})\s+received\s+a\s+new\s+collection\s+log\s+item.*"
        # Pattern for username has reached [skill] level format
        skills = [
            "Sailing", "Hunter", "Construction", "Farming", "Slayer", "Runecraft",
            "Agility", "Thieving", "Fletching", "Herblore", "Fishing", "Magic",
            "Prayer", "Crafting", "Attack", "Hitpoints", "Cooking", "Defence",
            "Firemaking", "Mining", "Ranged", "Smithing", "Strength", "Woodcutting",
            "combat", "total"
        ]
        skills_pattern = "|".join(skills)
        pattern5 = rf"\s*({username_pattern})\s+has\s+reached\s+({skills_pattern})\s+level.*"
        # Pattern for username has reached [number] XP in [skill] format
        pattern6 = rf"\s*({username_pattern})\s+has\s+reached\s+([0-9,]+)\s+XP\s+in\s+({skills_pattern}).*"
        # Pattern for username has completed a [difficulty] combat task format
        difficulties = ["easy", "medium", "hard", "elite", "master", "grandmaster"]
        difficulties_pattern = "|".join(difficulties)
        pattern7 = rf"\s*({username_pattern})\s+has\s+completed\s+a\s+({difficulties_pattern})\s+combat\s+task.*"
        # Pattern for username has a funny feeling format
        pattern8 = rf"\s*({username_pattern})\s+has\s+a\s+funny\s+feeling.*"
        # Pattern for username has been defeated format
        pattern9 = rf"\s*({username_pattern})\s+has\s+been\s+defeated.*"
        # Pattern for username has defeated format
        pattern10 = rf"\s*({username_pattern})\s+has\s+defeated.*"
        # Pattern for username has deposited [number] coins into the coffer format
        pattern11 = rf"\s*({username_pattern})\s+has\s+deposited\s+[0-9,]+\s+coins\s+into\s+the\s+coffer.*"
        # Pattern for username has completed the [difficulty] [area] diary format
        difficulties = ["Easy", "Medium", "Hard", "Elite"]
        areas = [
            "Ardougne", "Desert", "Falador", "Fremennik", "Kandarin",
            "Kourend & Kebos", "Lumbridge & Draynor", "Morytania",
            "Varrock", "Western Provinces", "Wilderness"
        ]
        difficulties_pattern = "|".join(difficulties)
        areas_pattern = "|".join(areas)
        pattern12 = rf"\s*({username_pattern})\s+has\s+completed\s+the\s+({difficulties_pattern})\s+({areas_pattern})\s+diary.*"
        # Pattern for username received special loot from a raid format
        pattern13 = rf"\s*({username_pattern})\s+received\s+special\s+loot\s+from\s+a\s+raid.*"
        # Pattern for username has reached the highest possible total level format
        pattern14 = rf"\s*({username_pattern})\s+has\s+reached\s+the\s+highest\s+possible\s+total\s+level\s+of\s+2277.*"
        # Pattern for username received a clue item format
        pattern15 = rf"\s*({username_pattern})\s+received\s+a\s+clue\s+item.*"
        # Pattern for username has unlocked the [tier] tier of rewards from Combat Achievements format
        combat_tiers = ["Easy", "Medium", "Hard", "Elite", "Master", "Grandmaster"]
        combat_tiers_pattern = "|".join(combat_tiers)
        pattern16 = rf"\s*({username_pattern})\s+has\s+unlocked\s+the\s+({combat_tiers_pattern})\s+tier\s+of\s+rewards\s+from\s+Combat\s+Achievements.*"
        # Pattern for username has reached a total level of [number] format
        pattern17 = rf"\s*({username_pattern})\s+has\s+reached\s+a\s+total\s+level\s+of\s+[0-9]+.*"
        # Pattern for username has been invited into the clan by format
        pattern18 = rf"\s*({username_pattern})\s+has\s+been\s+invited\s+into\s+the\s+clan\s+by.*"
        # Pattern for username has opened a loot key worth [number] format
        pattern19 = rf"\s*({username_pattern})\s+has\s+opened\s+a\s+loot\s+key\s+worth\s+[0-9,]+.*"
        
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
        match12 = re.search(pattern12, content)
        match13 = re.search(pattern13, content)
        match14 = re.search(pattern14, content)
        match15 = re.search(pattern15, content)
        match16 = re.search(pattern16, content)
        match17 = re.search(pattern17, content)
        match18 = re.search(pattern18, content)
        match19 = re.search(pattern19, content)
        
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
        elif match12:
            return match12.group(1)
        elif match13:
            return match13.group(1)
        elif match14:
            return match14.group(1)
        elif match15:
            return match15.group(1)
        elif match16:
            return match16.group(1)
        elif match17:
            return match17.group(1)
        elif match18:
            return match18.group(1)
        elif match19:
            return match19.group(1)
        else:
            #print("unknown format: " + content)
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
                # Optional progress print and delay
                if message_count_processed % 100 == 0: 
                    print(f"  Processed {message_count_processed} messages...")
                    await asyncio.sleep(1) # Add 1 second delay to ease rate limits
                
                # Include bot messages, but only count lines if there's text content
                if message.content:
                    # Split message content by newlines and process each line
                    for line in message.content.split('\n'):
                        if line.strip():  # Only process non-empty lines
                            # Use the new extract_username function
                            username = self.extract_username(line)
                            if username:
                                user_message_counts[username] += 1
                                total_messages += 1  # Only count messages with valid usernames
            
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
            
            # Write to output file
            success, result = self.write_to_output_file(sorted_users, start)
            if success:
                result_message += f"\nResults have been written to {result}\n\n"
            else:
                result_message += f"\nError writing to file: {result}\n\n"
            
            # Split the message into chunks of 2000 characters or less
            current_chunk = result_message
            for username, count in sorted_users:
                pts = 0  # Initialize pts for each user
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