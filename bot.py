import discord
from discord.ext import commands
from discord_slash import SlashCommand, SlashContext
import logging

logging.basicConfig(level=logging.INFO)

# Bot setup
intents = discord.Intents.default()
intents.members = True
intents.invites = True

bot = commands.Bot(command_prefix="!", intents=intents)
slash = SlashCommand(bot, sync_commands=True)

invite_cache = {}
invite_counts = {}
leaderboard_channel = {}

@bot.event
async def on_ready():
    print(f'Bot is ready. Logged in as {bot.user}')
    for guild in bot.guilds:
        invites = await guild.invites()
        invite_cache[guild.id] = invites
        invite_counts[guild.id] = {}
    print("Invite data cached successfully.")

@bot.event
async def on_invite_create(invite):
    invites = await invite.guild.invites()
    invite_cache[invite.guild.id] = invites

@bot.event
async def on_invite_delete(invite):
    invites = await invite.guild.invites()
    invite_cache[invite.guild.id] = invites

@bot.event
async def on_member_join(member):
    guild_id = member.guild.id
    invites_before = invite_cache[guild_id]
    invites_after = await member.guild.invites()

    # Find the invite used
    for invite_before in invites_before:
        for invite_after in invites_after:
            if invite_before.code == invite_after.code:
                if invite_before.uses < invite_after.uses:
                    inviter = invite_before.inviter
                    # Track the inviter's invite count
                    if inviter.id not in invite_counts[guild_id]:
                        invite_counts[guild_id][inviter.id] = 0
                    invite_counts[guild_id][inviter.id] += 1

                    # Send log message to the designated channel
                    if guild_id in leaderboard_channel:
                        channel = bot.get_channel(leaderboard_channel[guild_id])
                        if channel:
                            await channel.send(
                                f'{member.mention} just joined. They were invited by {inviter.mention} who now has {invite_counts[guild_id][inviter.id]} invites!'
                            )
                    break

    # Update the invite cache after a member joins
    invite_cache[guild_id] = invites_after

@slash.slash(
    name="setleaderboardchannel",
    description="Set the leaderboard channel for invites.",
    guild_ids=[YOUR_GUILD_ID],  # Replace with your server ID
)
async def set_leaderboard_channel(ctx: SlashContext, channel: discord.TextChannel):
    leaderboard_channel[ctx.guild.id] = channel.id
    await ctx.send(f"Leaderboard channel set to {channel.mention}.")

@slash.slash(
    name="showleaderboard",
    description="Show the invite leaderboard.",
    guild_ids=[YOUR_GUILD_ID]  # Replace with your server ID
)
async def show_leaderboard(ctx: SlashContext):
    guild_id = ctx.guild.id

    if guild_id not in leaderboard_channel:
        await ctx.send("Leaderboard channel not set. Use `/setleaderboardchannel` first.")
        return

    sorted_invites = sorted(
        invite_counts[guild_id].items(), key=lambda x: x[1], reverse=True
    )

    leaderboard_message = "**Invite Leaderboard**\n\n"
    for rank, (user_id, count) in enumerate(sorted_invites, 1):
        member = ctx.guild.get_member(user_id)
        leaderboard_message += f"{rank}. {member.display_name} - {count} invites\n"

    channel = bot.get_channel(leaderboard_channel[guild_id])
    await channel.send(leaderboard_message)
    await ctx.send("Leaderboard updated.")

@bot.event
async def on_guild_join(guild):
    invites = await guild.invites()
    invite_cache[guild.id] = invites
    invite_counts[guild.id] = {}

@bot.event
async def on_guild_remove(guild):
    invite_cache.pop(guild.id, None)
    invite_counts.pop(guild.id, None)

bot.run('YOUR_BOT_TOKEN')  # Replace with your bot token
