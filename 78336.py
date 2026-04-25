import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask, request
import threading
import asyncio
import json
import os
from datetime import datetime

BOT_TOKEN = ""
OWNER_ID =
GUILD_ID =
ROLE_ID =
SECRET_KEY = ""

DATA_FILE = "verified_users.json"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

app = Flask(__name__)

if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        verified_users = json.load(f)
else:
    verified_users = {}

def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(verified_users, f, indent=4, ensure_ascii=False)

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("X-Secret") != SECRET_KEY:
        return "unauthorized", 403

    data = request.json
    user_id = int(data["id"])
    email = data.get("email", "取得不可")
    ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    verified_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    verified_users[str(user_id)] = {
        "email": email,
        "ip": ip,
        "verified_at": verified_at
    }
    save_data()

    guild = bot.get_guild(GUILD_ID)
    if guild:
        member = guild.get_member(user_id)
        role = guild.get_role(ROLE_ID)
        if member and role:
            asyncio.run_coroutine_threadsafe(member.add_roles(role), bot.loop)

    return "ok"

@bot.command()
async def cccp(ctx):
    if ctx.author.id != OWNER_ID:
        return

    embed = discord.Embed(
        title="認証パネル",
        description="下のリンクから認証してください"
    )
    view = discord.ui.View()
    view.add_item(discord.ui.Button(
        label="認証する",
        url="https://あなたのworkers/pages/"
    ))
    await ctx.send(embed=embed, view=view)

@tree.command(name="access")
async def access(interaction: discord.Interaction, user_id: str):
    if interaction.user.id != OWNER_ID:
        return await interaction.response.send_message("権限なし", ephemeral=True)

    data = verified_users.get(user_id)
    if not data:
        return await interaction.response.send_message("未認証", ephemeral=True)

    embed = discord.Embed(title="認証情報")
    embed.add_field(name="IP", value=data["ip"], inline=False)
    embed.add_field(name="Email", value=data["email"], inline=False)
    embed.add_field(name="日時", value=data["verified_at"], inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(bot.user)

def run_web():
    app.run(host="0.0.0.0", port=5000)

threading.Thread(target=run_web).start()
bot.run(BOT_TOKEN)
