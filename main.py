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

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await m.reply_text("👋 **Universal Appx Patched Downloader Active!**\n\n➡ `/download` command bhejin.")

@bot.on_message(filters.command(["download"]))
async def processor(bot: Client, m: Message):
    if m.chat.id not in Config.VIP_USERS:
        await m.reply_text("❌ **Access Denied:** Aap authorized user nahi hain.")
        return
        
    try:
        editable = await m.reply_text('📂 **Kripya apni (.txt) link file upload karein...**')
        user_file: Message = await bot.listen(editable.chat.id)
        
        if not user_file.document:
            await editable.edit("❌ **Error:** Valid file nahi mili.")
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

        await editable.edit(f"📊 Total **{len(queue)}** Items mile hain.\n\n🆔 Target **Channel ID** send karein (Ya direct inbox ke liye `/d`):")
        user_channel: Message = await bot.listen(editable.chat.id)
        channel_id = m.chat.id if "/d" in user_channel.text else user_channel.text.strip()
        await user_channel.delete(True)

        await editable.edit("🚀 **Processing queue initiated...**")
        await bot.send_message(chat_id=channel_id, text=f"🎯 **New Batch Started! Total Items: {len(queue)}**")
        await editable.delete()

        # Premium Spoofing Headers for Appx Server Security Bypass
        headers_str = (
            "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36\r\n"
            "Accept: */*\r\n"
            "Accept-Language: en-US,en;q=0.9\r\n"
            "Origin: https://web.appx.co.in\r\n"
            "Referer: https://web.appx.co.in/\r\n"
        )

        count = 1
        for name, raw_url in queue:
            actual_url = raw_url.split("*", 1)[0].strip() if "*" in raw_url else raw_url
            
            # --- CASE 1: AGAR LINK PDF HAI ---
            if ".pdf" in actual_url.lower():
                status_msg = await bot.send_message(channel_id, f"📥 **Downloading PDF ({count}/{len(queue)}):** `{name}`")
                local_pdf = f"{name}.pdf"
                try:
                    pdf_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                        "Accept": "*/*",
                        "Referer": "https://web.appx.co.in/"
                    }
                    r = requests.get(actual_url, headers=pdf_headers, stream=True, timeout=30)
                    with open(local_pdf, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=8192):
                            f.write(chunk)
                    
                    await status_msg.edit(f"📤 **Uploading PDF:** `{name}`")
                    await bot.send_document(
                        chat_id=channel_id,
                        document=local_pdf,
                        caption=f"📄 **Document:** {str(count).zfill(3)}\n📝 **Title:** {name}"
                    )
                    os.remove(local_pdf)
                    await status_msg.delete()
                    count += 1
                except Exception as pdf_err:
                    await bot.send_message(channel_id, f"❌ **PDF Failed:** `{name}`\n⚠️ **Reason:** {pdf_err}")
                    if os.path.exists(local_pdf): os.remove(local_pdf)
                continue

            # --- CASE 2: AGAR LINK VIDEO/ZIP HAI ---
            video_name = f"{str(count).zfill(3)}) {name}"
            status_msg = await bot.send_message(channel_id, f"📥 **Downloading Video ({count}/{len(queue)}):** `{video_name}`")
            local_file = f"{video_name}.mp4"
            
            try:
                # Spoofing parameters include karke ffmpeg command run karna
                cmd = [
                    "ffmpeg", "-y",
                    "-headers", headers_str,
                    "-i", actual_url,
                    "-c", "copy",
                    "-bsf:a", "aac_adtstoasc",  # Audio filter for stream extraction stability
                    local_file
                ]
                
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)

                if os.path.exists(local_file) and os.path.getsize(local_file) > 1000:
                    await status_msg.edit(f"📤 **Uploading Video:** `{video_name}`")
                    await bot.send_video(
                        chat_id=channel_id,
                        video=local_file,
                        caption=f"🎥 **Lecture:** {str(count).zfill(3)}\n📝 **Topic:** {name}"
                    )
                    os.remove(local_file)
                    await status_msg.delete()
                    count += 1
                else:
                    raise FileNotFoundError("Server se video package correctly fetch nahi hua (Size limit issue).")

            except Exception as e:
                await bot.send_message(channel_id, f"❌ **Video Failed:** `{video_name}`\n⚠️ **Reason:** {e}")
                if os.path.exists(local_file): os.remove(local_file)
                continue

        await bot.send_message(channel_id, "🎉 **Batch successfully completed!**")

    except Exception as general_error:
        await m.reply_text(f"⚠️ **Core System Exception:** {general_error}")

bot.run()
