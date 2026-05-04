import discord
import os
import requests
import csv
import difflib
import io
from discord.ext import commands
from datetime import datetime

# --- CONFIG & IDs ---
YAGPDB_ID = 204255221017214977
DATA_CHANNEL_ID = 1462273147909968025
SHEET_ID = "1hpCl5-kGjdz452A4pO2wM1sLCeJT6UAzH69S22aGYNc"
SHEET1_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/export?format=csv&gid=0"
PERMS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Perms"
WL_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=WL"
ADMINS_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=Admins"
GP_URL = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet=GP"

PINK_COLOR = 0xffc9e9 
ALLOWED_CHANNELS = [1462265715791888405, 1482475797963997196, 1488931777723502652]
IOS_USERS = [730138298621886544, 1454173039942963333]

# --- BOT SETUP ---
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# --- UTILITIES ---
def to_small_caps(text, user_id=None):
    if not text: return text
    if user_id not in IOS_USERS:
        return text
        
    mapping = str.maketrans(
        "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
        "ᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢᴀʙᴄᴅᴇꜰɢʜɪᴊᴋʟᴍɴᴏᴘǫʀꜱᴛᴜᴠᴡxʏᴢ"
    )
    return text.translate(mapping)

def esc(text):
    if not text: return text
    for char in ["_", "*", "~", "`"]:
        text = text.replace(char, f"\\{char}")
    return text

def get_roster_data(url, start_row=2):
    try:
        response = requests.get(url, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        roster = {}
        for row in reader[start_row:]:
            if row and row[0].strip() and row[0].strip().upper() != "DNU":
                name = row[0].strip()
                parties = row[3].strip() if len(row) > 3 and row[3].strip() else "0"
                status = row[4].strip().upper() if len(row) > 4 and row[4].strip() else ""
                gp_status = row[5].strip() if len(row) > 5 and row[5].strip() else "None"
                roster[name.lower()] = {"name": name, "parties": parties, "status": status, "gp_status": gp_status}
        return roster
    except Exception as e: 
        print(f"Error fetching roster data: {e}")
        return {}

def get_admin_categories():
    try:
        response = requests.get(ADMINS_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        vps = [row[0].strip() for row in reader[1:8] if row and row[0].strip() and row[0].strip().upper() != "DNU"]
        execs = [row[0].strip() for row in reader[9:21] if row and row[0].strip() and row[0].strip().upper() != "DNU"]
        ihs = [row[0].strip() for row in reader[22:24] if row and row[0].strip() and row[0].strip().upper() != "DNU"]
        return vps, execs, ihs
    except Exception as e: 
        print(f"Error fetching admin categories: {e}")
        return [], [], []

def get_admin_shifts():
    try:
        response = requests.get(ADMINS_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        shifts = {}
        for row in reader[1:25]:
            if row and row[0].strip() and row[0].strip().upper() != "DNU":
                name = row[0].strip().lower()
                shift = row[1].strip() if len(row) > 1 and row[1].strip() else ""
                shifts[name] = shift
        return shifts
    except Exception as e: 
        print(f"Error fetching admin shifts: {e}")
        return {}

def get_gp_sheet_data():
    try:
        response = requests.get(GP_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        gp_days = {}
        for row in reader[2:]: 
            if row and row[0].strip() and row[0].strip().upper() != "DNU":
                name = row[0].strip().lower()
                days = row[1].strip() if len(row) > 1 and row[1].strip() else ""
                gp_days[name] = days
        return gp_days
    except Exception as e:
        print(f"Error fetching GP data: {e}")
        return {}

def get_main_data():
    try:
        response = requests.get(SHEET1_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        o2_val = int(float(reader[1][14])) if len(reader[1]) > 14 and reader[1][14].strip() else 0
        return {
            "l1": str(reader[0][11]), "l2": int(float(reader[1][11])), "l3": int(float(reader[2][11])),
            "l5": int(float(reader[4][11])), "l6": int(float(reader[5][11])), "l7": int(float(reader[6][11])), "l8": int(float(reader[7][11])),
            "o2": o2_val
        }
    except Exception as e: 
        print(f"Error fetching main data: {e}")
        return None

def get_admin_slots():
    try:
        response = requests.get(ADMINS_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        vps = []
        for i in range(1, 8):
            if i < len(reader) and len(reader[i]) > 1:
                if not reader[i][0].strip() and reader[i][1].strip():
                    vps.append(reader[i][1].strip())
        execs = []
        for i in range(9, 21):
            if i < len(reader) and len(reader[i]) > 1:
                if not reader[i][0].strip() and reader[i][1].strip():
                    execs.append(reader[i][1].strip())
        d1_val = ""
        try:
            if len(reader) > 0 and len(reader[0]) > 3:
                d1_val = reader[0][3].strip()
                if d1_val.upper() == "DNU": d1_val = ""
        except IndexError: pass 
        return vps, execs, d1_val
    except Exception as e:
        print(f"Slot fetch error: {e}")
        return [], [], ""

def get_wl_data():
    try:
        response = requests.get(WL_URL, timeout=10)
        response.encoding = 'utf-8'
        reader = list(csv.reader(io.StringIO(response.text)))
        gp = [row[0].strip() for row in reader[1:] if len(row) > 0 and row[0].strip() and row[0].strip().upper() != "DNU"]
        perms_wl = [row[1].strip() for row in reader[1:] if len(row) > 1 and row[1].strip() and row[1].strip().upper() != "DNU"]
        inv = [row[2].strip() for row in reader[1:] if len(row) > 2 and row[2].strip() and row[2].strip().upper() != "DNU"]
        dog = [row[3].strip() for row in reader[1:] if len(row) > 3 and row[3].strip() and row[3].strip().upper() != "DNU"]
        return gp, perms_wl, inv, dog
    except Exception as e: 
        print(f"Error fetching WL data: {e}")
        return [], [], [], []

@bot.event
async def on_ready(): 
    print(f'Logged in successfully as {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user: return

    if message.channel.id == DATA_CHANNEL_ID:
        if message.author.id == YAGPDB_ID:
            if "FETCH_ADMINS_D1" in message.content:
                _, _, d1_val = get_admin_slots()
                if d1_val and d1_val.strip():
                    fixed_banner = d1_val.replace("\\n", "\n")
                    final_banner = to_small_caps(fixed_banner.strip(), IOS_USERS[0])
                    await message.channel.send(final_banner)
                return
        return

    clean_content = message.content.replace(f'<@!{bot.user.id}>', '').replace(f'<@{bot.user.id}>', '').strip()
    msg_lower = clean_content.lower()
    cmd_check = msg_lower.lstrip('!/?.-')

    if cmd_check == "bot":
        embed = discord.Embed(title="🤖 Clocky Bot Keywords", color=PINK_COLOR)
        embed.description = "• `overview` / `count` \n• `slots` / `slot` / `wl` / `waitlist` \n• `ihs name` \n• `admin` / `hire` \n• `bot` "
        await message.reply(embed=embed)
        return
        
    if cmd_check in ["admin", "hire", "hiring", "need admins"]:
        vps, execs, d1_val = get_admin_slots()
        if not vps and not execs:
            await message.reply("⚠️ Error: I couldn't find any admin data.")
            return
        embed = discord.Embed(title="👔 Hiring Admin Slots", color=PINK_COLOR)
        total_slots = len(vps) + len(execs)
        slot_word = "slot" if total_slots == 1 else "slots"
        embed.description = f"We are currently hiring for the following time {slot_word} (in EST):\n\n"
        vp_word = "Slot" if len(vps) == 1 else "Slots"
        embed.description += f"**VP {vp_word}:**\n{chr(10).join(['• '+esc(to_small_caps(n, message.author.id)) for n in vps]) if vps else 'None'}\n\n"
        exec_word = "Slot" if len(execs) == 1 else "Slots"
        embed.description += f"**Exec {exec_word}:**\n{chr(10).join(['• '+esc(to_small_caps(n, message.author.id)) for n in execs]) if execs else 'None'}"
        await message.reply(embed=embed)
        if d1_val and d1_val.strip():
            fixed_banner = d1_val.replace("\\n", "\n")
            await message.channel.send(to_small_caps(fixed_banner.strip(), message.author.id))
        return
    
    if cmd_check in ["count", "overview"]:
        data = get_main_data()
        if data:
            embed = discord.Embed(title="📊 Club Overview", color=PINK_COLOR, timestamp=datetime.utcnow())
            # Calculating Total based on provided structure: Members (L5) + Admins (L6) + IHS (L7) + Perms (O1)
            total = data['l5'] + data['l6'] + data['l7'] + data['o2']
            desc = (
                f"**Party Number:** {data['l1']}\n"
                f"**Members:** {data['l5']}\n"
                f"**Perms:** {data['o2']}\n"
                f"**Frozen Perms:** {data['l10'] if 'l10' in data else 'N/A'}\n"
                f"**Admins:** {data['l6']}\n"
                f"**IHS:** {data['l7']}\n\n"
                f"**Total:** **{data['l8']}/100**"
            )
            embed.description = desc
            await message.reply(embed=embed)
        else:
            await message.reply("Failed to pull overview data from the sheet.")
        return
        

    if cmd_check in ["slot", "slots", "wl", "waitlist"]:
        data = get_main_data()
        gp_wl, perms_wl, inv_wl, dog_wl = get_wl_data()
        if data:
            gp_avail = max(0, 30 - data['l3'])
            mem_word = "Slot" if data['l2'] == 1 else "Slots"
            perm_word = "Slot" if data.get('o2', 0) == 1 else "Slots"
            gp_word = "Slot" if gp_avail == 1 else "Slots"
            total_wl = len(inv_wl) + len(dog_wl) + len(gp_wl) + len(perms_wl)
            wl_word = "Waitlist" if total_wl == 1 else "Waitlists"
            embed = discord.Embed(title="🎰 Slots & Waitlists", color=PINK_COLOR)
            embed.description = (
                f"👥 **Member {mem_word}:** {data['l2']}\n"
                f"🛡️ **Perms {perm_word}:** {data['o2']}\n"
                f"💳 **GP {gp_word}:** {gp_avail}\n\n"
                f"**{wl_word}:**\n"
                f"• **Invite:** {', '.join([esc(n) for n in inv_wl]) if inv_wl else 'None'}\n"
                f"• **Dog:** {', '.join([esc(n) for n in dog_wl]) if dog_wl else 'None'}\n"
                f"• **Perms:** {', '.join([esc(n) for n in perms_wl]) if perms_wl else 'None'}\n"
                f"• **Gold Pass:** {', '.join([esc(n) for n in gp_wl]) if gp_wl else 'Empty'}"
            )
            await message.reply(embed=embed)
        else:
            await message.reply("Failed to pull slot data from the sheet.")
        return

    if cmd_check in ["ihs name", "ihs names", "ihs"]:
        _, _, ihs_list = get_admin_categories()
        if not ihs_list:
            await message.reply("We currently do not have an IHS.")
        elif len(ihs_list) == 1:
            await message.reply(f"Our club IHS is **{esc(ihs_list[0])}**.")
        elif len(ihs_list) == 2:
            await message.reply(f"Our club IHS are **{esc(ihs_list[0])}** and **{esc(ihs_list[1])}**.")
        else:
            names = ", ".join([f"**{esc(name)}**" for name in ihs_list[:-1]]) + f", and **{esc(ihs_list[-1])}**"
            await message.reply(f"Our club IHS are {names}.")
        return

    if 0 < len(clean_content.split()) <= 3:
        vps, execs, ihs = get_admin_categories()
        members_data = get_roster_data(SHEET1_URL)
        perms_data = get_roster_data(PERMS_URL)
        admin_shifts = get_admin_shifts()
        gp_days_data = get_gp_sheet_data()
        
        members_names = [info["name"] for info in members_data.values()]
        perms_names = [info["name"] for info in perms_data.values()]
        
        all_names = vps + execs + ihs + members_names + perms_names
        all_names_lower = [n.lower() for n in all_names]
        
        target_lower = None
        
        if msg_lower in all_names_lower:
            target_lower = msg_lower
        else:
            close_matches = difflib.get_close_matches(msg_lower, all_names_lower, n=1, cutoff=0.6)
            if close_matches:
                target_lower = close_matches[0]
                
        if target_lower:
            orig_name = next(n for n in all_names if n.lower() == target_lower)
            gp_days = gp_days_data.get(target_lower, "")
            
            if target_lower in gp_days_data:
                gp_status = "Yes"
                has_gp = True
            else:
                gp_status = "No"
                has_gp = False
            
            if target_lower in [n.lower() for n in vps]: 
                shift = admin_shifts.get(target_lower, "N/A")
                role_msg = f"**{esc(orig_name)}** (Vice President)\n**Shift time:** {shift}\n**GP:** {gp_status}"
                
            elif target_lower in [n.lower() for n in execs]: 
                shift = admin_shifts.get(target_lower, "N/A")
                role_msg = f"**{esc(orig_name)}** (Executive)\n**Shift time:** {shift}\n**GP:** {gp_status}"
                if has_gp and gp_days:
                    role_msg += f"\n**GP days left:** {gp_days}"
                    
            elif target_lower in [n.lower() for n in ihs]: 
                role_msg = f"**{esc(orig_name)}** (IHS)"
                
            elif target_lower in perms_data: 
                status = perms_data[target_lower]["status"]
                parties_left = "FROZEN" if status == "FROZEN" else perms_data[target_lower]["parties"]
                role_msg = f"**{esc(orig_name)}** (Perm)\n**Parties left:** {parties_left}\n**GP:** {gp_status}"
                if has_gp and gp_days:
                    role_msg += f"\n**GP days left:** {gp_days}"
                    
            else: 
                parties_left = members_data[target_lower]["parties"]
                role_msg = f"**{esc(orig_name)}** (Member)\n**Parties left:** {parties_left}\n**GP:** {gp_status}"
                if has_gp and gp_days:
                    role_msg += f"\n**GP days left:** {gp_days}"
                
            await message.reply(role_msg)
            return
            
        else:
            ignore_triggers = ["bot", "admin", "hire", "hiring", "need admins", "count", "overview", "slot", "slots", "wl", "waitlist", "ihs name", "ihs names", "ihs"]
            if cmd_check not in ignore_triggers:
                await message.reply(f"Hey! {esc(clean_content)} can't be found in Sheets.")
                return

    await bot.process_commands(message)

if __name__ == "__main__":
    token = os.environ.get('DISCORD_TOKEN')
    if token:
        bot.run(token)
