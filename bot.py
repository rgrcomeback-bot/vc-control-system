import discord
from discord.ext import commands
from discord import app_commands
import logging
import os
from dotenv import load_dotenv

# ===== LOAD ENVIRONMENT VARIABLES (Optional) =====
load_dotenv()

# ===== YOUR ORIGINAL CONFIGURATION =====
TOKEN = "MTQ3MTc1MjY1OTU1MDczNjUwMg.GaW7V5.gMPBoVa8SdoDNxKmid2ycyHzD-fp3EfDKsV8Ro"
CATEGORY_ID = 1458449979491225713
ALLOWED_ROLES = ["Moderator", "Tournament Managers", "VC Controller", "1460248615330250752"]

# ===== OR USE ENVIRONMENT VARIABLES (Uncomment below) =====
# TOKEN = os.getenv("DISCORD_TOKEN", "MTQ3MTc1MjY1OTU1MDczNjUwMg.GaW7V5.gMPBoVa8SdoDNxKmid2ycyHzD-fp3EfDKsV8Ro")
# CATEGORY_ID = int(os.getenv("CATEGORY_ID", 1458449979491225713))
# ALLOWED_ROLES = os.getenv("ALLOWED_ROLES", "Moderator,Tournament Managers,VC Controller,1460248615330250752").split(",")

# ===== LOGGING =====
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===== BOT INTENTS =====
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents, case_insensitive=True)


# ===== HELPER FUNCTIONS =====
async def get_category_from_guild(guild):
    category = guild.get_channel(CATEGORY_ID)
    if category is None:
        return None
    return category


async def get_category(ctx):
    category = ctx.guild.get_channel(CATEGORY_ID)
    if category is None:
        await ctx.send("❌ Category not found.")
        return None
    return category


async def check_permissions(interaction: discord.Interaction):
    """Check if user has allowed roles"""
    user_roles = [role.id for role in interaction.user.roles]
    for role in ALLOWED_ROLES:
        if role.isdigit():
            if int(role) in user_roles:
                return True
        else:
            if discord.utils.get(interaction.guild.roles, name=role) in interaction.user.roles:
                return True
    return False


async def is_admin(interaction: discord.Interaction):
    """Check if user is server administrator"""
    return interaction.user.guild_permissions.administrator


# ===== EVENT HANDLERS =====
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    print(f"✅ Category ID: {CATEGORY_ID}")
    print(f"✅ Allowed Roles: {ALLOWED_ROLES}")
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="🔒 Voice Channels"
        )
    )
    
    try:
        synced = await bot.tree.sync()
        print(f"✅ Synced {len(synced)} slash commands!")
        for cmd in synced:
            print(f"   /{cmd.name}")
    except Exception as e:
        print(f"❌ Failed to sync: {e}")


# ====================================================
# ===== ADMIN COMMANDS =====
# ====================================================

@bot.tree.command(name="addmanagement", description="👑 Add a role to management list (Admin Only)")
@app_commands.describe(role="Role name or ID to add as manager")
async def slash_add_management(interaction: discord.Interaction, role: str):
    if not await is_admin(interaction):
        await interaction.response.send_message("❌ **Only server administrators can use this command.**", ephemeral=True)
        return
    
    if role in ALLOWED_ROLES:
        await interaction.response.send_message(f"⚠️ **{role}** is already in the management list.", ephemeral=True)
        return
    
    ALLOWED_ROLES.append(role)
    
    embed = discord.Embed(
        title="✅ Management Role Added",
        color=discord.Color.green(),
        description=f"**{role}** has been added to the management list."
    )
    embed.add_field(
        name="📋 Current Management Roles",
        value="\n".join([f"• {r}" for r in ALLOWED_ROLES]),
        inline=False
    )
    embed.set_footer(text=f"Added by {interaction.user}")
    
    await interaction.response.send_message(embed=embed)
    logger.info(f"Admin {interaction.user} added role {role}")


@bot.tree.command(name="showmanagement", description="📋 Show all management roles")
async def slash_show_management(interaction: discord.Interaction):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="📋 Management Roles",
        color=discord.Color.blue(),
        description="Users with these roles can use VC management commands:"
    )
    
    role_list = []
    for role in ALLOWED_ROLES:
        if role.isdigit():
            guild_role = discord.utils.get(interaction.guild.roles, id=int(role))
            if guild_role:
                role_list.append(f"• {guild_role.mention} (ID: {role})")
            else:
                role_list.append(f"• Role ID: {role}")
        else:
            guild_role = discord.utils.get(interaction.guild.roles, name=role)
            if guild_role:
                role_list.append(f"• {guild_role.mention}")
            else:
                role_list.append(f"• {role}")
    
    embed.add_field(
        name=f"Total: {len(role_list)} roles",
        value="\n".join(role_list) if role_list else "No roles configured",
        inline=False
    )
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="removemanagement", description="🗑️ Remove a role from management list (Admin Only)")
@app_commands.describe(role="Role name or ID to remove from managers")
async def slash_remove_management(interaction: discord.Interaction, role: str):
    if not await is_admin(interaction):
        await interaction.response.send_message("❌ **Only server administrators can use this command.**", ephemeral=True)
        return
    
    if role not in ALLOWED_ROLES:
        await interaction.response.send_message(f"⚠️ **{role}** is not in the management list.", ephemeral=True)
        return
    
    ALLOWED_ROLES.remove(role)
    
    embed = discord.Embed(
        title="🗑️ Management Role Removed",
        color=discord.Color.orange(),
        description=f"**{role}** has been removed from the management list."
    )
    embed.add_field(
        name="📋 Current Management Roles",
        value="\n".join([f"• {r}" for r in ALLOWED_ROLES]) if ALLOWED_ROLES else "No roles configured",
        inline=False
    )
    embed.set_footer(text=f"Removed by {interaction.user}")
    
    await interaction.response.send_message(embed=embed)
    logger.info(f"Admin {interaction.user} removed role {role}")


# ====================================================
# ===== VC COMMANDS =====
# ====================================================

@bot.tree.command(name="lock-all", description="🔒 Lock ALL voice channels")
async def slash_lock_all(interaction: discord.Interaction):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.followup.send("❌ Category not found.")
        return
    
    count = 0
    for channel in category.voice_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, connect=False)
            count += 1
        except discord.Forbidden:
            await interaction.followup.send(f"❌ Bot doesn't have permission to modify {channel.name}")
            return
    
    await interaction.followup.send(f"🔒 Locked **{count}** voice channels.")


@bot.tree.command(name="unlock-all", description="🔓 Unlock ALL voice channels")
async def slash_unlock_all(interaction: discord.Interaction):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.followup.send("❌ Category not found.")
        return
    
    count = 0
    for channel in category.voice_channels:
        try:
            await channel.set_permissions(interaction.guild.default_role, overwrite=None)
            await channel.set_permissions(interaction.guild.default_role, connect=True)
            count += 1
        except discord.Forbidden:
            await interaction.followup.send(f"❌ Bot doesn't have permission to modify {channel.name}")
            return
    
    await interaction.followup.send(f"🔓 Unlocked **{count}** voice channels.")


@bot.tree.command(name="lock", description="🔒 Lock a SINGLE voice channel")
@app_commands.describe(channel="Name of the voice channel to lock")
async def slash_lock(interaction: discord.Interaction, channel: str):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.followup.send("❌ Category not found.")
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel.lower():
            target = vc
            break
    
    if not target:
        await interaction.followup.send(f"❌ No voice channel found with name: **{channel}**")
        return
    
    try:
        await target.set_permissions(interaction.guild.default_role, connect=False)
        await interaction.followup.send(f"🔒 **{target.name}** has been **locked**.")
    except discord.Forbidden:
        await interaction.followup.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.tree.command(name="unlock", description="🔓 Unlock a SINGLE voice channel")
@app_commands.describe(channel="Name of the voice channel to unlock")
async def slash_unlock(interaction: discord.Interaction, channel: str):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.followup.send("❌ Category not found.")
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel.lower():
            target = vc
            break
    
    if not target:
        await interaction.followup.send(f"❌ No voice channel found with name: **{channel}**")
        return
    
    try:
        await target.set_permissions(interaction.guild.default_role, overwrite=None)
        await target.set_permissions(interaction.guild.default_role, connect=True)
        await interaction.followup.send(f"🔓 **{target.name}** has been **unlocked**.")
    except discord.Forbidden:
        await interaction.followup.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.tree.command(name="toggle", description="🔄 Toggle a SINGLE voice channel")
@app_commands.describe(channel="Name of the voice channel to toggle")
async def slash_toggle(interaction: discord.Interaction, channel: str):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    await interaction.response.defer()
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.followup.send("❌ Category not found.")
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel.lower():
            target = vc
            break
    
    if not target:
        await interaction.followup.send(f"❌ No voice channel found with name: **{channel}**")
        return
    
    try:
        current = target.overwrites_for(interaction.guild.default_role)
        
        if current.connect is False:
            await target.set_permissions(interaction.guild.default_role, overwrite=None)
            await target.set_permissions(interaction.guild.default_role, connect=True)
            await interaction.followup.send(f"🔓 **{target.name}** is now **unlocked**.")
        else:
            await target.set_permissions(interaction.guild.default_role, connect=False)
            await interaction.followup.send(f"🔒 **{target.name}** is now **locked**.")
    except discord.Forbidden:
        await interaction.followup.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.tree.command(name="status", description="📊 Check which channels are locked/unlocked")
async def slash_status(interaction: discord.Interaction):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    category = await get_category_from_guild(interaction.guild)
    if category is None:
        await interaction.response.send_message("❌ Category not found.", ephemeral=True)
        return
    
    locked = []
    unlocked = []
    
    for channel in category.voice_channels:
        perms = channel.overwrites_for(interaction.guild.default_role)
        if perms.connect is False:
            locked.append(channel.name)
        else:
            unlocked.append(channel.name)
    
    embed = discord.Embed(
        title="📊 Voice Channel Status",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(
        name=f"🔒 Locked ({len(locked)})", 
        value=", ".join(locked) if locked else "None", 
        inline=False
    )
    embed.add_field(
        name=f"🔓 Unlocked ({len(unlocked)})", 
        value=", ".join(unlocked) if unlocked else "None", 
        inline=False
    )
    embed.set_footer(text=f"Requested by {interaction.user}")
    
    await interaction.response.send_message(embed=embed)


@bot.tree.command(name="help-vc", description="📚 Show all available commands")
async def slash_help(interaction: discord.Interaction):
    if not await check_permissions(interaction):
        await interaction.response.send_message("❌ **You do not have enough permissions to use this command.**", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="🎤 VC Management Commands",
        color=discord.Color.blue(),
        description="**All available commands:**"
    )
    
    embed.add_field(
        name="👑 Admin Commands",
        value="`/addmanagement` - Add management role\n`/removemanagement` - Remove management role\n`/showmanagement` - Show all management roles",
        inline=False
    )
    
    embed.add_field(
        name="🔒 Lock Commands",
        value="`/lock-all` - Lock ALL VCs\n`/lock` - Lock SINGLE VC",
        inline=False
    )
    
    embed.add_field(
        name="🔓 Unlock Commands",
        value="`/unlock-all` - Unlock ALL VCs\n`/unlock` - Unlock SINGLE VC",
        inline=False
    )
    
    embed.add_field(
        name="🔄 Toggle & Status",
        value="`/toggle` - Toggle SINGLE VC\n`/status` - Check VC status",
        inline=False
    )
    
    embed.set_footer(text="Example: /lock General")
    await interaction.response.send_message(embed=embed)


# ====================================================
# ===== PREFIX COMMANDS =====
# ====================================================

@bot.command(name="lock-all")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_lock_all(ctx):
    category = await get_category(ctx)
    if not category:
        return
    count = 0
    for channel in category.voice_channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, connect=False)
            count += 1
        except discord.Forbidden:
            await ctx.send(f"❌ Bot doesn't have permission to modify {channel.name}")
            return
    await ctx.send(f"🔒 Locked **{count}** voice channels.")


@bot.command(name="unlock-all")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_unlock_all(ctx):
    category = await get_category(ctx)
    if not category:
        return
    count = 0
    for channel in category.voice_channels:
        try:
            await channel.set_permissions(ctx.guild.default_role, overwrite=None)
            await channel.set_permissions(ctx.guild.default_role, connect=True)
            count += 1
        except discord.Forbidden:
            await ctx.send(f"❌ Bot doesn't have permission to modify {channel.name}")
            return
    await ctx.send(f"🔓 Unlocked **{count}** voice channels.")


@bot.command(name="lock")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_lock(ctx, *, channel_name: str):
    category = await get_category(ctx)
    if not category:
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel_name.lower():
            target = vc
            break
    
    if not target:
        await ctx.send(f"❌ No voice channel found with name: **{channel_name}**")
        return
    
    try:
        await target.set_permissions(ctx.guild.default_role, connect=False)
        await ctx.send(f"🔒 **{target.name}** has been **locked**.")
    except discord.Forbidden:
        await ctx.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.command(name="unlock")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_unlock(ctx, *, channel_name: str):
    category = await get_category(ctx)
    if not category:
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel_name.lower():
            target = vc
            break
    
    if not target:
        await ctx.send(f"❌ No voice channel found with name: **{channel_name}**")
        return
    
    try:
        await target.set_permissions(ctx.guild.default_role, overwrite=None)
        await target.set_permissions(ctx.guild.default_role, connect=True)
        await ctx.send(f"🔓 **{target.name}** has been **unlocked**.")
    except discord.Forbidden:
        await ctx.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.command(name="toggle")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_toggle(ctx, *, channel_name: str):
    category = await get_category(ctx)
    if not category:
        return
    
    target = None
    for vc in category.voice_channels:
        if vc.name.lower() == channel_name.lower():
            target = vc
            break
    
    if not target:
        await ctx.send(f"❌ No voice channel found with name: **{channel_name}**")
        return
    
    try:
        current = target.overwrites_for(ctx.guild.default_role)
        
        if current.connect is False:
            await target.set_permissions(ctx.guild.default_role, overwrite=None)
            await target.set_permissions(ctx.guild.default_role, connect=True)
            await ctx.send(f"🔓 **{target.name}** is now **unlocked**.")
        else:
            await target.set_permissions(ctx.guild.default_role, connect=False)
            await ctx.send(f"🔒 **{target.name}** is now **locked**.")
    except discord.Forbidden:
        await ctx.send(f"❌ Bot doesn't have permission to modify **{target.name}**")


@bot.command(name="status")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_status(ctx):
    category = await get_category(ctx)
    if not category:
        return
    
    locked = []
    unlocked = []
    
    for channel in category.voice_channels:
        perms = channel.overwrites_for(ctx.guild.default_role)
        if perms.connect is False:
            locked.append(channel.name)
        else:
            unlocked.append(channel.name)
    
    embed = discord.Embed(
        title="📊 Voice Channel Status",
        color=discord.Color.blue(),
        timestamp=discord.utils.utcnow()
    )
    embed.add_field(
        name=f"🔒 Locked ({len(locked)})", 
        value=", ".join(locked) if locked else "None", 
        inline=False
    )
    embed.add_field(
        name=f"🔓 Unlocked ({len(unlocked)})", 
        value=", ".join(unlocked) if unlocked else "None", 
        inline=False
    )
    embed.set_footer(text=f"Requested by {ctx.author}")
    await ctx.send(embed=embed)


@bot.command(name="help-vc")
@commands.has_any_role(*ALLOWED_ROLES)
async def prefix_help(ctx):
    embed = discord.Embed(
        title="🎤 VC Management Commands",
        color=discord.Color.blue(),
        description="**Both Slash (/) and Prefix (!) commands available!**"
    )
    
    embed.add_field(
        name="👑 Admin Commands",
        value="`/addmanagement` - Add management role\n`/removemanagement` - Remove management role\n`/showmanagement` - Show all management roles",
        inline=False
    )
    
    embed.add_field(
        name="🔒 Lock Commands",
        value="`/lock-all` or `!lock-all` - Lock ALL VCs\n`/lock` or `!lock` - Lock SINGLE VC",
        inline=False
    )
    
    embed.add_field(
        name="🔓 Unlock Commands",
        value="`/unlock-all` or `!unlock-all` - Unlock ALL VCs\n`/unlock` or `!unlock` - Unlock SINGLE VC",
        inline=False
    )
    
    embed.add_field(
        name="🔄 Toggle & Status",
        value="`/toggle` or `!toggle` - Toggle SINGLE VC\n`/status` or `!status` - Check VC status",
        inline=False
    )
    
    embed.set_footer(text="Example: /lock General")
    await ctx.send(embed=embed)


# ===== ERROR HANDLING =====
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingAnyRole):
        await ctx.send("❌ **You do not have enough permissions to use this command.**")
    elif isinstance(error, commands.CommandInvokeError):
        if "Forbidden" in str(error):
            await ctx.send("❌ **Bot doesn't have permission to modify channels. Give bot Administrator or Manage Channels permission.**")


# ===== RUN BOT =====
if __name__ == "__main__":
    bot.run(TOKEN)
