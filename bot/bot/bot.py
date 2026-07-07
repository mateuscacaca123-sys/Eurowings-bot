"""
EuroWings Digital Assistant — Discord Bot
==========================================
Customer support assistant with ticket system via DM.

Commands:
- !help           — list all commands
- !faq            — frequently asked questions
- !faq <number>   — detailed answer
- !flight         — flight information
- !baggage        — baggage rules
- !checkin        — how to check in
- !contact        — Eurowings support channels
- !close          — close the ticket (used inside a ticket channel)
- !status         — check if bot is online
"""

import asyncio
import os

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN  = os.getenv("DISCORD_TOKEN")
PREFIX = os.getenv("BOT_PREFIX", "!")

# ── Ticket configuration ─────────────────────────────────
GUILD_ID        = 1523324131607711876
CATEGORY_NAME   = "EuroWings Airlines Roblox"
STAFF_ROLE_NAME = "EW | Staff"

# ── Brand colours ────────────────────────────────────────
COR_PRINCIPAL  = 0xE2007A   # Eurowings magenta
COR_SECUNDARIA = 0x00A1DE   # Eurowings light blue
COR_SUCESSO    = 0x2ECC71
COR_PERIGO     = 0xE74C3C
COR_AVISO      = 0xF39C12

# ── In-memory ticket store ───────────────────────────────
# { user_id: channel_id }  and  { channel_id: user_id }
tickets_por_user:  dict[int, int] = {}
tickets_por_canal: dict[int, int] = {}

# ── Users currently in the confirmation flow ─────────────
pending_confirmation: set[int] = set()

# ──────────────────────────────────────────
# FAQ — Eurowings
# ──────────────────────────────────────────
FAQ = {
    1: {
        "question": "How do I check in online?",
        "answer": (
            "✈️ **Online Check-in — Eurowings**\n\n"
            "Online check-in is available **from 30 days up to 40 minutes** before departure.\n\n"
            "**Steps:**\n"
            "1. Visit [eurowings.com](https://www.eurowings.com)\n"
            "2. Click **Check-in** at the top of the page\n"
            "3. Enter your booking reference and last name\n"
            "4. Select your seat and confirm\n"
            "5. Download or email your boarding pass\n\n"
            "📱 Also available on the **Eurowings app** (iOS & Android)."
        ),
    },
    2: {
        "question": "What are the carry-on baggage rules?",
        "answer": (
            "🧳 **Carry-on Baggage — Eurowings**\n\n"
            "**BASIC fare:**\n"
            "• 1 small bag: max. **40 × 30 × 10 cm** (free, under seat)\n"
            "• Cabin bag (55 × 40 × 23 cm) at an additional fee\n\n"
            "**SMART / BIZclass fares:**\n"
            "• 1 small bag + 1 cabin bag **included**\n"
            "• Max. cabin bag weight: **8 kg**\n\n"
            "💡 Add baggage in advance online — it's cheaper than at the airport!"
        ),
    },
    3: {
        "question": "How do I add checked baggage to my booking?",
        "answer": (
            "🎒 **Checked Baggage — Eurowings**\n\n"
            "**Available options:**\n"
            "• **23 kg** — standard option\n"
            "• **32 kg** — XL option\n\n"
            "**How to add:**\n"
            "1. Go to **My Bookings** on eurowings.com\n"
            "2. Select the relevant flight\n"
            "3. Click **Add Baggage**\n"
            "4. Confirm and pay\n\n"
            "⚠️ Excess baggage at the airport can cost up to **3× more**."
        ),
    },
    4: {
        "question": "How can I change or cancel my booking?",
        "answer": (
            "🔄 **Change or Cancel a Booking**\n\n"
            "**Changes:**\n"
            "• Go to **My Bookings** → select flight → **Change flight**\n"
            "• BASIC fares generally do not include free changes\n"
            "• SMART and BIZclass fares offer more flexibility\n\n"
            "**Cancellations:**\n"
            "• Go to **My Bookings** → **Cancel**\n"
            "• Refunds depend on the fare purchased\n"
            "• BASIC fares are generally non-refundable\n\n"
            "📞 For assistance, contact Eurowings support."
        ),
    },
    5: {
        "question": "My flight was cancelled or delayed. What are my rights?",
        "answer": (
            "⚖️ **Your Rights — Flight Cancellation or Delay**\n\n"
            "Under **EU Regulation 261/2004**:\n\n"
            "**Delay of 2h+ (short-haul up to 1,500 km):**\n"
            "• Right to meals and refreshments\n\n"
            "**Delay of 3h+ at destination:**\n"
            "• Compensation of €250 to €600 depending on distance\n\n"
            "**Cancelled flight:**\n"
            "• Full refund **or** alternative flight\n"
            "• Financial compensation (if notified less than 14 days before)\n\n"
            "📋 Submit your claim at: eurowings.com/contact-us"
        ),
    },
    6: {
        "question": "How does the Boomerang Club loyalty programme work?",
        "answer": (
            "⭐ **Boomerang Club — Loyalty Programme**\n\n"
            "Eurowings' frequent flyer programme.\n\n"
            "**How to earn points:**\n"
            "• Eurowings flights and Lufthansa Group partners\n"
            "• Partners: hotels, car rentals, credit cards\n\n"
            "**How to redeem:**\n"
            "• Free flights\n"
            "• Fare upgrades\n"
            "• Free extra baggage\n\n"
            "**Sign up:** [boomerang.eurowings.com](https://boomerang.eurowings.com)\n\n"
            "💡 Status members enjoy priority boarding and lounge access!"
        ),
    },
    7: {
        "question": "Can I travel with pets?",
        "answer": (
            "🐾 **Travelling with Pets — Eurowings**\n\n"
            "**In the cabin (dogs/cats):**\n"
            "• Total weight (animal + carrier): max. **8 kg**\n"
            "• Carrier: max. 55 × 40 × 23 cm\n"
            "• Fee per flight: from **€50**\n\n"
            "**In the hold (medium/large dogs):**\n"
            "• Must be booked in advance\n"
            "• Subject to availability\n\n"
            "⚠️ **Not permitted:** rodents, reptiles, birds, or exotic animals\n\n"
            "📋 Book pet transport when purchasing your ticket or in My Bookings."
        ),
    },
    8: {
        "question": "What baggage allowance is included in my ticket?",
        "answer": (
            "🎫 **Baggage Allowance by Fare**\n\n"
            "| Fare | Small bag | Cabin bag | Checked bag |\n"
            "|------|-----------|-----------|-------------|\n"
            "| BASIC | ✅ Included | ❌ Paid | ❌ Paid |\n"
            "| SMART | ✅ Included | ✅ Included | ❌ Paid |\n"
            "| BIZclass | ✅ Included | ✅ Included | ✅ 1× 23 kg |\n\n"
            "💡 Check the exact details on your e-ticket or in My Bookings."
        ),
    },
}

CONTACT = {
    "website":  "https://www.eurowings.com",
    "support":  "https://www.eurowings.com/contact-us",
    "app":      "Eurowings App (iOS / Android)",
    "phone":    "+49 221 599 8800 (international line)",
    "chat":     "Live chat at eurowings.com (8 AM – 8 PM CET)",
}

KEYWORDS = {
    ("check-in", "checkin", "boarding pass", "boarding"): 1,
    ("carry-on", "cabin bag", "hand luggage", "hand bag"): 2,
    ("checked baggage", "check baggage", "luggage", "baggage"): 3,
    ("cancel", "cancellation", "change", "reschedule"): 4,
    ("delayed", "delay", "cancelled", "rights", "compensation"): 5,
    ("loyalty", "miles", "points", "boomerang"): 6,
    ("pet", "animal", "dog", "cat"): 7,
    ("allowance", "included", "basic fare", "smart fare"): 8,
}

SUPPORT_CHANNELS = {"support", "help", "assistance", "tickets", "suporte", "ajuda"}

# ──────────────────────────────────────────
# Bot setup
# ──────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents, help_command=None)


# ══════════════════════════════════════════
# TICKET CONFIRMATION VIEW
# ══════════════════════════════════════════

class TicketConfirmView(discord.ui.View):
    """Confirmation prompt sent via DM before opening a ticket."""

    def __init__(self, user: discord.User):
        super().__init__(timeout=60)
        self.user = user

    async def _open_ticket(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="🎫 Opening ticket…",
                description="Please wait while we create your support ticket.",
                color=COR_PRINCIPAL,
            ),
            view=None,
        )
        channel = await criar_ticket(self.user)
        if channel:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="🎫 Support Ticket Opened",
                    description=(
                        "Your message has been received and a ticket has been created.\n"
                        "Our team will get back to you shortly!\n\n"
                        f"While you wait, you can use `{PREFIX}faq` to browse our FAQs."
                    ),
                    color=COR_SUCESSO,
                )
            )
        else:
            await interaction.edit_original_response(
                embed=discord.Embed(
                    title="❌ Error",
                    description="Could not create the ticket. Please try again later.",
                    color=COR_PERIGO,
                )
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
            embed=discord.Embed(
                title="❌ Ticket Cancelled",
                description=(
                    "No ticket was created.\n"
                    f"If you need help, feel free to message us again or use `{PREFIX}faq`."
                ),
                color=COR_PERIGO,
            ),
            view=None,
        )

    async def on_timeout(self):
        pending_confirmation.discard(self.user.id)


# ══════════════════════════════════════════
# TICKET HELPERS
# ══════════════════════════════════════════

async def criar_ticket(user: discord.User) -> discord.TextChannel | None:
    """Create a ticket channel for the user and return it, or None on failure."""
    guild = bot.get_guild(GUILD_ID)
    if not guild:
        return None

    category = discord.utils.get(guild.categories, name=CATEGORY_NAME)
    if not category:
        category = await guild.create_category(CATEGORY_NAME)

    staff_role = discord.utils.get(guild.roles, name=STAFF_ROLE_NAME)

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        guild.me: discord.PermissionOverwrite(
            view_channel=True, send_messages=True, manage_channels=True
        ),
    }
    if staff_role:
        overwrites[staff_role] = discord.PermissionOverwrite(
            view_channel=True, send_messages=True
        )

    channel_name = f"ticket-{user.name}".lower().replace(" ", "-")[:100]
    channel = await category.create_text_channel(channel_name, overwrites=overwrites)

    tickets_por_user[user.id]    = channel.id
    tickets_por_canal[channel.id] = user.id

    embed = discord.Embed(
        title="🎫 New Support Ticket",
        description=(
            f"**User:** {user.name} (`{user.id}`)\n"
            f"**DM:** Active\n\n"
            "Messages sent here are forwarded to the user via DM.\n"
            f"Use `{PREFIX}close` to close and delete this ticket."
        ),
        color=COR_PRINCIPAL,
    )
    embed.set_footer(text="EuroWings Digital Assistant • Ticket System")
    await channel.send(embed=embed)

    if staff_role:
        await channel.send(f"{staff_role.mention} — new ticket opened!")

    return channel


# ══════════════════════════════════════════
# EVENTS
# ══════════════════════════════════════════

@bot.event
async def on_ready():
    print(f"✅ EuroWings Digital Assistant online as {bot.user} (ID: {bot.user.id})")
    await bot.change_presence(status=discord.Status.online, activity=None)


@bot.event
async def on_message(message: discord.Message):
    if message.author == bot.user:
        return

    # ── DM received ──────────────────────────────────────
    if isinstance(message.channel, discord.DMChannel):
        user = message.author

        # Already waiting for confirmation — ignore further messages
        if user.id in pending_confirmation:
            await message.channel.send(
                embed=discord.Embed(
                    description="⏳ Please respond to the confirmation prompt above first.",
                    color=COR_AVISO,
                )
            )
            return

        # Ticket already open — forward message to channel
        if user.id in tickets_por_user:
            channel = bot.get_channel(tickets_por_user[user.id])
            if channel:
                embed = discord.Embed(
                    description=message.content or "*(no text)*",
                    color=COR_SECUNDARIA,
                )
                embed.set_author(name=user.name, icon_url=user.display_avatar.url)
                if message.attachments:
                    embed.add_field(
                        name="📎 Attachments",
                        value="\n".join(a.url for a in message.attachments),
                        inline=False,
                    )
                await channel.send(embed=embed)
                await bot.process_commands(message)
                return
            else:
                # Channel was deleted — remove stale reference
                del tickets_por_user[user.id]

        # No open ticket — show confirmation prompt
        pending_confirmation.add(user.id)
        view = TicketConfirmView(user)
        confirm_embed = discord.Embed(
            title="Please confirm if you wish to contact a representative.",
            description="Please utilize the options below.",
            color=COR_PRINCIPAL,
        )
        sent = await message.channel.send(embed=confirm_embed, view=view)

        # Store the first message content so it can be forwarded after ticket opens
        # (handled by the view — channel forwards are done after creation)
        await bot.process_commands(message)
        return

    # ── Message in a ticket channel — forward to user ────
    if message.channel.id in tickets_por_canal:
        if message.content.startswith(PREFIX):
            await bot.process_commands(message)
            return

        user_id = tickets_por_canal[message.channel.id]
        try:
            user = await bot.fetch_user(user_id)
        except discord.NotFound:
            return

        embed = discord.Embed(
            description=message.content or "*(no text)*",
            color=COR_PRINCIPAL,
        )
        embed.set_author(
            name=f"Staff — {message.author.display_name}",
            icon_url=message.author.display_avatar.url,
        )
        embed.set_footer(text="EuroWings Digital Assistant • Support Team Reply")
        if message.attachments:
            embed.add_field(
                name="📎 Attachments",
                value="\n".join(a.url for a in message.attachments),
                inline=False,
            )
        try:
            await user.send(embed=embed)
            await message.add_reaction("✅")
        except discord.Forbidden:
            await message.channel.send(
                "⚠️ Could not send a DM to the user (DMs may be disabled)."
            )
        return

    # ── Auto-reply by keyword in support channels ────────
    if message.guild and isinstance(message.channel, discord.TextChannel):
        if message.channel.name in SUPPORT_CHANNELS:
            text = message.content.lower()
            for keywords, faq_num in KEYWORDS.items():
                if any(k in text for k in keywords):
                    item = FAQ[faq_num]
                    embed = discord.Embed(
                        title=item["question"],
                        description=item["answer"],
                        color=COR_SECUNDARIA,
                    )
                    embed.set_footer(
                        text=f"💡 Automated reply | Use {PREFIX}faq for all FAQs"
                    )
                    await message.reply(embed=embed)
                    break

    await bot.process_commands(message)


# ══════════════════════════════════════════
# COMMANDS
# ══════════════════════════════════════════

# ── !help ────────────────────────────────
@bot.command(name="help", aliases=["commands", "ajuda"])
async def help_cmd(ctx):
    embed = discord.Embed(
        title="✈️ EuroWings Digital Assistant",
        description="Welcome! Here's what I can do for you:",
        color=COR_PRINCIPAL,
    )
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


# ── !faq ─────────────────────────────────
@bot.command(name="faq", aliases=["question", "q"])
async def faq(ctx, number: int = None):
    if number is None:
        embed = discord.Embed(
            title="❓ Frequently Asked Questions — Eurowings",
            description=f"Use `{PREFIX}faq <number>` for a detailed answer.",
            color=COR_SECUNDARIA,
        )
        for num, item in FAQ.items():
            embed.add_field(name=f"`{PREFIX}faq {num}`", value=item["question"], inline=False)
        embed.set_footer(text="Can't find your answer? DM the bot to open a support ticket.")
        await ctx.send(embed=embed)
    elif number in FAQ:
        item = FAQ[number]
        embed = discord.Embed(title=item["question"], description=item["answer"], color=COR_SECUNDARIA)
        embed.set_footer(text=f"More questions? {PREFIX}faq • EuroWings Digital Assistant")
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"⚠️ Question **{number}** not found. Use `{PREFIX}faq` to see the full list.")


# ── !checkin ──────────────────────────────
@bot.command(name="checkin", aliases=["check-in", "boarding"])
async def checkin(ctx):
    item = FAQ[1]
    embed = discord.Embed(title=item["question"], description=item["answer"], color=COR_PRINCIPAL)
    embed.set_footer(text="EuroWings Digital Assistant • eurowings.com")
    await ctx.send(embed=embed)


# ── !baggage ──────────────────────────────
@bot.command(name="baggage", aliases=["luggage", "bag"])
async def baggage(ctx):
    embed = discord.Embed(title="🧳 Baggage Guide — Eurowings", color=COR_PRINCIPAL)
    embed.add_field(name=f"`{PREFIX}faq 2` — Carry-on baggage", value="Sizes and weights allowed in the cabin", inline=False)
    embed.add_field(name=f"`{PREFIX}faq 3` — Checked baggage", value="How to add and pricing", inline=False)
    embed.add_field(name=f"`{PREFIX}faq 8` — Allowance by fare", value="What's included in each ticket type", inline=False)
    embed.set_footer(text="EuroWings Digital Assistant • eurowings.com")
    await ctx.send(embed=embed)


# ── !flight ───────────────────────────────
@bot.command(name="flight", aliases=["flights", "voo"])
async def flight(ctx):
    embed = discord.Embed(title="✈️ Flight Information — Eurowings", color=COR_PRINCIPAL)
    embed.add_field(name=f"`{PREFIX}faq 4` — Change or cancel booking", value="Flexibility options", inline=False)
    embed.add_field(name=f"`{PREFIX}faq 5` — Cancelled or delayed flight", value="Your rights and compensation", inline=False)
    embed.add_field(name=f"`{PREFIX}faq 1` — Check-in", value="How to check in online", inline=False)
    embed.set_footer(text="EuroWings Digital Assistant • eurowings.com")
    await ctx.send(embed=embed)


# ── !contact ──────────────────────────────
@bot.command(name="contact", aliases=["support", "contato"])
async def contact(ctx):
    embed = discord.Embed(
        title="📞 Contact Eurowings",
        description=(
            "Our team is ready to help!\n\n"
            "💬 You can also **DM this bot** to open a support ticket."
        ),
        color=COR_PRINCIPAL,
    )
    embed.add_field(name="🌐 Website", value=CONTACT["website"], inline=False)
    embed.add_field(name="📋 Support form", value=CONTACT["support"], inline=False)
    embed.add_field(name="💬 Live chat", value=CONTACT["chat"], inline=False)
    embed.add_field(name="📱 App", value=CONTACT["app"], inline=False)
    embed.add_field(name="📞 Phone", value=CONTACT["phone"], inline=False)
    embed.set_footer(text="EuroWings Digital Assistant • eurowings.com")
    await ctx.send(embed=embed)


# ── !close ────────────────────────────────
@bot.command(name="close", aliases=["fechar", "encerrar"])
async def close(ctx):
    if ctx.channel.id not in tickets_por_canal:
        await ctx.send("⚠️ This command can only be used inside a ticket channel.")
        return

    user_id = tickets_por_canal[ctx.channel.id]

    try:
        user = await bot.fetch_user(user_id)
        await user.send(
            embed=discord.Embed(
                title="🔒 Ticket Closed",
                description=(
                    "Your support ticket has been closed by our team.\n"
                    "If you need further assistance, feel free to message us again!"
                ),
                color=COR_PERIGO,
            )
        )
    except Exception:
        pass

    tickets_por_user.pop(user_id, None)
    tickets_por_canal.pop(ctx.channel.id, None)

    await ctx.send(
        embed=discord.Embed(
            title="🔒 Ticket Closed",
            description="This channel will be deleted in 5 seconds…",
            color=COR_PERIGO,
        )
    )
    await asyncio.sleep(5)
    await ctx.channel.delete(reason="Ticket closed")


# ── !status ───────────────────────────────
@bot.command(name="status", aliases=["ping"])
async def status(ctx):
    latency = round(bot.latency * 1000)
    embed = discord.Embed(
        title="✅ EuroWings Digital Assistant — Online",
        description=f"Assistant is operational!\n🏓 Latency: **{latency}ms**",
        color=COR_SUCESSO,
    )
    await ctx.send(embed=embed)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.BadArgument):
        await ctx.send(f"⚠️ Invalid number. Use `{PREFIX}faq` to see available questions.")
    elif isinstance(error, commands.CommandNotFound):
        pass
    else:
        await ctx.send(f"⚠️ An error occurred. Please try again or use `{PREFIX}help`.")


# ──────────────────────────────────────────
# Start
# ──────────────────────────────────────────
if __name__ == "__main__":
    if not TOKEN:
        print("❌ ERROR: DISCORD_TOKEN not found!")
        exit(1)
    bot.run(TOKEN)
