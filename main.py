import os
import re
import time
import logging
import subprocess
import requests
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
from config import Config

logging.basicConfig(level=logging.INFO)

bot = Client(
    "appx_drm_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Server par N_m3u8DL-RE tool ko automatic setup karne ka dynamic mechanism
def setup_drm_engine():
    binary_path = "./N_m3u8DL-RE"
    if not os.path.exists(binary_path):
        logging.info("Downloading DRM Engine (N_m3u8DL-RE)...")
        # Direct stable Linux x64 binary link
        url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_linux-x64.tar.gz"
        try:
            r = requests.get(url)
            with open("engine.tar.gz", "wb") as f:
                f.write(r.content)
            # tar file ko extract karna
            os.system("tar -xzf engine.tar.gz")
            # Extra extracted folder se binary bahar nikalna agar zaroorat ho
            if os.path.exists("./N_m3u8DL-RE_v0.3.0-beta_linux-x64/N_m3u8DL-RE"):
                os.rename("./N_m3u8DL-RE_v0.3.0-beta_linux-x64/N_m3u8DL-RE", binary_path)
            
            # Temporary files clear karna
            if os.path.exists("engine.tar.gz"): os.remove("engine.tar.gz")
        except Exception as e:
            logging.error(f"Engine download fail: {e}")
            
    # Executable permission set karna (Strict 0o755)
    if os.path.exists(binary_path):
        os.chmod(binary_path, 0o755)

@bot.on_message(filters.command(["start"]))
async def start_handler(bot: Client, m: Message):
    await m.reply_text("👋 **Hi! Main Appx DRM Protected (* encrypted) links ko download aur decrypt kar sakta hoon.**\n\n🎯 Shuru karne ke liye `/master` bhejiye.")

@bot.on_message(filters.command(["master"]))
async def download_handler(bot: Client, m: Message):
    if m.chat.id not in Config.VIP_USERS:
        await m.reply_text("❌ **Oopss! You are not a Premium member.**")
        return
        
    setup_drm_engine()
    try:
        editable = await m.reply_text('📂 **Apni Master TXT file bhejiye...**')
        user_file: Message = await bot.listen(editable.chat.id)
        
        if not user_file.document:
            await editable.edit("❌ **Error:** Kripya valid text file hi bhejiye.")
            return

        await editable.edit("⏳ **File processing chal rahi hai...**")
        downloaded_txt = await user_file.download()
        await user_file.delete(True)
        
        with open(downloaded_txt, "r", encoding="utf-8") as f:
            content = f.read().split("\n")
        os.remove(downloaded_txt)

        links = []
        for line in content:
            if "http" in line and "*" in line:
                parts = re.split(r':(?=https?://)', line.strip(), maxsplit=1)
                if len(parts) == 2:
                    name = parts[0].replace("/", "").replace("\\", "").replace(":", "").strip()
                    url_part = parts[1].strip()
                    mpd_url, key = url_part.split("*", 1)
                    links.append((name, mpd_url, key))

        if not links:
            await editable.edit("❌ **Error:** File me koi valid '*' encrypted DRM link nahi mili!")
            return

        await editable.edit(f"📊 Total **{len(links)}** DRM links mili hain!\n\n🆔 Ab target **Channel ID** bhejiye (Ya khud ke liye `/d`):")
        user_channel: Message = await bot.listen(editable.chat.id)
        channel_id = m.chat.id if "/d" in user_channel.text else user_channel.text.strip()
        await user_channel.delete(True)

        await editable.edit("🚀 **Decryption aur Downloading process shuru ho rahi hai...**")
        await bot.send_message(chat_id=channel_id, text=f"🎯 **DRM Batch Started! Total Videos: {len(links)}**")
        await editable.delete()

        count = 1
        for name, mpd_url, key in links:
            video_name = f"{str(count).zfill(3)}) {name}"
            status_msg = await bot.send_message(channel_id, f"📥 **Decrypting & Downloading ({count}/{len(links)}):** `{video_name}`")
            
            try:
                cmd = [
                    "./N_m3u8DL-RE",
                    mpd_url,
                    "--key", key.strip(),
                    "--save-name", video_name,
                    "-m", "format=mp4",
                    "--auto-select",
                    "--log-level", "OFF"
                ]
                
                subprocess.run(cmd, check=True)
                expected_mp4 = f"{video_name}.mp4"
                
                if os.path.exists(expected_mp4):
                    await status_msg.edit(f"📤 **Uploading Decrypted Video:** `{video_name}`")
                    caption_text = f"🎥 **Lecture:** {str(count).zfill(3)}\n📝 **Topic:** {name}\n\n🔐 *Successfully Decrypted by Bot*"
                    
                    await bot.send_video(
                        chat_id=channel_id,
                        video=expected_mp4,
                        caption=caption_text
                    )
                    os.remove(expected_mp4)
                    await status_msg.delete()
                    count += 1
                else:
                    raise FileNotFoundError("Decrypted MP4 file generate nahi ho paayi!")
                
                time.sleep(2)

            except Exception as file_err:
                await bot.send_message(channel_id, f"❌ **Failed:** `{video_name}`\n⚠️ **Reason:** {file_err}")
                if os.path.exists(f"{video_name}.mp4"):
                    os.remove(f"{video_name}.mp4")
                continue

        await bot.send_message(channel_id, "🎉 **Saari DRM videos kamyabi se decrypt aur upload ho gayi hain!**")

    except Exception as total_err:
        await m.reply_text(f"⚠️ **Main Error:** {total_err}")

bot.run()
