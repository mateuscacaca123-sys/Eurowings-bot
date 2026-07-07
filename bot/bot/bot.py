"""
EuroWings Digital Assistant — Discord Bot
==========================================
Customer support assistant with ticket system via DM.
"""

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN  = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

GUILD_ID        = 1523324131607711876
CATEGORY_NAME   = "EuroWings Airlines Roblox"
STAFF_ROLE_NAME = "EW | Staff"

COR_PRINCIPAL  = 0xE2007A
COR_SECUNDARIA = 0x00A1DE
COR_SUCESSO    = 0x2ECC71
COR_PERIGO     = 0xE74C3C
COR_AVISO      = 0xF39C12

tickets_por_user:  dict[int, int] = {}
tickets_por_canal: dict[int, int] = {}
pending_confirmation: set[int] = set()

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


class TicketConfirmView(discord.ui.View):
    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.user = user

    async def _open_ticket(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(title="🎫 Opening ticket…", description="Please wait while we create your support ticket.", color=COR_PRINCIPAL),
            view=None,
        )
        channel = await criar_ticket(self.user)
        if channel:
            await interaction.edit_original_response(
                embed=discord.Embed(title="🎫 Support Ticket Opened", description="Your message has been received and a ticket has been created.\nOur team will get back to you shortly!", color=COR_SUCESSO)
            )
        else:
            await interaction.edit_original_response(
                embed=discord.Embed(title="❌ Error", description="Could not create the ticket. Please try again later.", color=COR_PERIGO)
            )
        pending_confirmation.discard(self.user.id)

    @discord.ui.button(emoji="✅", style=discord.ButtonStyle.success)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your ticket.", ephemeral=True)
            return
        self.stop()
        await self._open_ticket(interaction)

    @discord.ui.button(emoji="🚫", style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message("This is not your ticket.", ephemeral=True)
            return
        self.stop()
        pending_confirmation.discard(self.user.id)
        await interaction.response.edit_message(
            embed=discord.Embed(title="❌ Ticket Cancelled", description="No ticket was created.\nIf you need help, feel free to message us again.", color=COR_PERIGO),
            view=None,
        )

    async def on_timeout(self):
        pending_confirmation.discard(self.user.id)


async def criar_ticket(user: discord.User) -> discord.TextChannel | None:
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return None
    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        category = await guild.create_category(CATEGORY_NAME)
    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)
    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(view_channel=True, send_messages=True, manage_channels=True),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
    channel_name = f"ticket-{user.name}".lower().replace(" ", "-")[:100]
    channel = await category.create_text_channel(channel_name, overwrites=overwrites)
    tickets_por_user[user.id] = channel.id
    tickets_por_canal[channel.id] = user.id
    embed = discord.Embed(
        title="🎫 New Support Ticket",
        description=f"**User:** {user.name} (`{user.id}`)\n**DM:** Active\n\nMessages sent here are forwarded to the user via DM.\nUse `{PREFIX}close` to close and delete this ticket.",
        color=COR_PRINCIPAL,
    )
    embed.set_footer(text="EuroWings Digital Assistant • Ticket System")
    await channel.send(embed=embed)
    if staff_role:
        await channel.send(f"{staff_role.mention} — new ticket opened!")
    return channel


@bot.event
async def on_ready():
    print(f"✅ EuroWings Digital Assistant online as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(status=discord.Status.online, activity=None)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    if isinstance(message.channel, discord.DMChannel):
        user = message.author
        if user.id in pending_confirmation:
            await message.channel.send(embed=discord.Embed(description="⏳ Please respond to the confirmation prompt above first.", color=COR_AVISO))
            return
        if user.id in tickets_por_user:
            channel = bot.get_channel(tickets_por_user[user.id])
            if channel:
                embed = discord.Embed(description=message.content or "*(no text)*", color=COR_SECUNDARIA)
                embed.set_author(name=user.name, icon_url=user.display_avatar.url)
                if message.attachments:
                    embed.add_field(name="📎 Attachments", value="\n".join(a.url for a in message.attachments), inline=False)
                await channel.send(embed=embed)
                await bot.process_commands(message)
                return
            else:
                del tickets_por_user[user.id]
        pending_confirmation.add(user.id)
        view = TicketConfirmView(user)
        confirm_embed = discord.Embed(title="Please confirm if you wish to contact a representative.", description="Please utilize the options below.", color=COR_PRINCIPAL)
        await message.channel.send(embed=confirm_embed, view=view)
        await bot.process_commands(message)
        return

    if message.channel.id in tickets_por_canal:
        if message.content.startswith(PREFIX):
            await bot.process_commands(message)
            return
        user_id = tickets_por_canal[message.channel.id]
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            return
        embed = discord.Embed(description=message.content or "*(no text)*", color=COR_PRINCIPAL)
        embed.set_author(name=f"Staff — {message.author.display_name}", icon_url=message.author.display_avatar.url)
        embed.set_footer(text="EuroWings Digital Assistant • Support Team Reply")
        if message.attachments:
            embed.add_field(name="📎 Attachments", value="\n".join(a.url for a in message.attachments), inline=False)
        try:
            await user.send(embed=embed)
            await message.add_reaction("✅")
        except discord.Forbidden:
            await message.channel.send("⚠️ Could not send a DM to the user (DMs may be disabled).")
        return

    await bot.process_commands(message)


@bot.command(name="efhdbsjkgfweufvbsygiy", aliases=["commands"])
async def help_cmd(ctx):
    embed = discord.Embed(title="✈️ EuroWings Digital Assistant", description="Welcome! Here's what I can do for you:", color=COR_PRINCIPAL)
    embed.add_field(name=f"`{PREFIX}faq`", value="List all frequently asked questions", inline=False)
    embed.add_field(name=f"`{PREFIX}faq <number>`", value="Get a detailed answer (e.g. `!faq 1`)", inline=False)
    embed.add_field(name=f"`{PREFIX}checkin`", value="How to check in online", inline=False)
    embed.add_field(name=f"`{PREFIX}baggage`", value="Baggage rules and allowances", inline=False)
    embed.add_field(name=f"`{PREFIX}flight`", value="Flight information", inline=False)
    embed.add_field(name=f"`{PREFIX}contact`", value="Eurowings support channels", inline=False)
    embed.add_field(name=f"`{PREFIX}close`", value="Close a ticket (inside ticket channel only)", inline=False)
    embed.add_field(name=f"`{PREFIX}status`", value="Check bot status", inline=False)
    embed.set_footer(text="EuroWings Digital Assistant • eurowings.com")
    await ctx.send(embed=embed)


@bot.command(name="status", aliases=["ping"])
async def status(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(title="✅ EuroWings Digital Assistant — Online", description=f"Assistant is operational!\n🏓 Latency: **{latency}ms**", color=COR_SUCESSO)
    await ctx.send(embed=embed)


@bot.command(name="close", aliases=["fechar", "encerrar"])
async def close(ctx):
    if ctx.channel.id not in tickets_por_canal:
        await ctx.send("⚠️ This command can only be used inside a ticket channel.")
        return
    user_id = tickets_por_canal[ctx.channel.id]
    try:
        user = await bot.fetch_user(user_id)
        await user.send(embed=discord.Embed(title="🔒 Ticket Closed", description="Your support ticket has been closed by our team.\nIf you need further assistance, feel free to message us again!", color=COR_PERIGO))
    except Exception:
        pass
    tickets_por_user.pop(user_id, None)
    tickets_por_canal.pop(ctx.channel.id, None)
    await ctx.send(embed=discord.Embed(title="🔒 Ticket Closed", description="This channel will be deleted in 5 seconds…", color=COR_PERIGO))
    await asyncio.sleep(5)
    await ctx.channel.delete(reason="Ticket closed")


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Invalid input. Please try again.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"⚠️ An error occurred. Please try again or use `{PREFIX}help`.")


if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found!")
        exit(1)
    bot.run(TOKEN)
