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

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Client(
    "universal_appx_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# Core System check jo Linux DRM tools ko runtime par load aur permissions grant karega
def init_drm_engine():
    binary_path = "./N_m3u8DL-RE"
    if not os.path.exists(binary_path):
        logging.info("Downloading Linux x64 DRM Decryption Engine...")
        url = "https://github.com/nilaoda/N_m3u8DL-RE/releases/download/v0.3.0-beta/N_m3u8DL-RE_v0.3.0-beta_linux-x64.tar.gz"
        try:
            r = requests.get(url)
            with open("engine.tar.gz", "wb") as f:
                f.write(r.content)
            os.system("tar -xzf engine.tar.gz")
            if os.path.exists("./N_m3u8DL-RE_v0.3.0-beta_linux-x64/N_m3u8DL-RE"):
                os.rename("./N_m3u8DL-RE_v0.3.0-beta_linux-x64/N_m3u8DL-RE", binary_path)
            if os.path.exists("engine.tar.gz"): os.remove("engine.tar.gz")
        except Exception as e:
            logging.error(f"Failed to setup core binary: {e}")
            
    if os.path.exists(binary_path):
        os.chmod(binary_path, 0o755)

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text("👋 **Universal Downloader Bot Active!**\n\n➡ `/download` command bhejin aur batch download shuru karein.")

@bot.on_message(filters.command(["download"]))
async def processor(bot: Client, m: Message):
    if m.chat.id not in Config.VIP_USERS:
        await m.reply_text("❌ **Access Denied:** Aap authorized user nahi hain.")
        return
        
    init_drm_engine()
    try:
        editable = await m.reply_text('📂 **Kripya apni (.txt) link file upload karein...**')
        user_file: Message = await bot.listen(editable.chat.id)
        
        if not user_file.document:
            await editable.edit("❌ **Error:** Valid file nahi mili. Phir se try karein.")
            return

        await editable.edit("⏳ **File processing shuru hai...**")
        txt_path = await user_file.download()
        await user_file.delete(True)
        
        with open(txt_path, "r", encoding="utf-8") as f:
            content = f.read().split("\n")
        os.remove(txt_path)

        queue = []
        for line in content:
            if "http" in line:
                parts = re.split(r':(?=https?://)', line.strip(), maxsplit=1)
                if len(parts) == 2:
                    name = parts[0].replace("/", "").replace("\\", "").replace(":", "").strip()
                    url_data = parts[1].strip()
                    queue.append((name, url_data))

        if not queue:
            await editable.edit("❌ **Error:** File ke andar koi valid links nahi mili.")
            return

        await editable.edit(f"📊 Total **{len(queue)}** Links mili hain.\n\n🆔 Target **Channel ID** send karein (Ya direct inbox ke liye `/d`):")
        user_channel: Message = await bot.listen(editable.chat.id)
        channel_id = m.chat.id if "/d" in user_channel.text else user_channel.text.strip()
        await user_channel.delete(True)

        await editable.edit("🚀 **Processing queue initiated...**")
        await bot.send_message(chat_id=channel_id, text=f"🎯 **New Batch Started! Total Items: {len(queue)}**")
        await editable.delete()

        count = 1
        for name, raw_url in queue:
            video_name = f"{str(count).zfill(3)}) {name}"
            status_msg = await bot.send_message(channel_id, f"📥 **Downloading ({count}/{len(queue)}):** `{video_name}`")
            local_file = f"{video_name}.mp4"
            
            try:
                # ROUTE A: WIDEVINE DRM ENCRYPTED LINKS (Jisme '*' key structure hai)
                if "*" in raw_url:
                    mpd_url, key = raw_url.split("*", 1)
                    cmd = ["./N_m3u8DL-RE", mpd_url.strip(), "--key", key.strip(), "--save-name", video_name, "-m", "format=mp4", "--auto-select", "--log-level", "OFF"]
                    subprocess.run(cmd, check=True)
                
                # ROUTE B: APPX ENCRYPTED STREAMING CONTAINER LINKS (.zip formats)
                else:
                    # FFmpeg raw standard streaming dump logic layer
                    cmd = ["ffmpeg", "-y", "-i", raw_url, "-c", "copy", local_file]
                    subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                if os.path.exists(local_file):
                    await status_msg.edit(f"📤 **Uploading:** `{video_name}`")
                    await bot.send_video(
                        chat_id=channel_id,
                        video=local_file,
                        caption=f"🎥 **Lecture:** {str(count).zfill(3)}\n📝 **Topic:** {name}"
                    )
                    os.remove(local_file)
                    await status_msg.delete()
                    count += 1
                else:
                    raise FileNotFoundError("System output layer par video generate nahi hui.")
                
                time.sleep(2)

            except Exception as e:
                await bot.send_message(channel_id, f"❌ **Failed:** `{video_name}`\n⚠️ **Reason:** {e}")
                if os.path.exists(local_file): os.remove(local_file)
                continue

        await bot.send_message(channel_id, "🎉 **Batch successfully completed!**")

    except Exception as general_error:
        await m.reply_text(f"⚠️ **Core System Exception:** {general_error}")

bot.run()
