import os
import re
import time
import logging
import asyncio
import aiohttp
import subprocess
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod import listen
from pyrogram.errors import FloodWait
from config import Config

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

bot = Client(
    "universal_appx_bot",
    bot_token=Config.BOT_TOKEN,
    api_id=Config.API_ID,
    api_hash=Config.API_HASH
)

# FloodWait controller function to prevent crashes
async def safe_send(func, *args, **kwargs):
    while True:
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            logging.warning(f"FloodWait hit! Sleeping for {e.value + 5} seconds...")
            await asyncio.sleep(e.value + 5)
        except Exception as general_err:
            logging.error(f"Error in execution: {general_err}")
            raise general_err

@bot.on_message(filters.command(["start"]))
async def start(bot: Client, m: Message):
    await safe_send(m.reply_text, "👋 **Universal Appx Stable Downloader Active!**\n\n➡ `/download` command bhejin.")

@bot.on_message(filters.command(["download"]))
async def processor(bot: Client, m: Message):
    if m.chat.id not in Config.VIP_USERS:
        await safe_send(m.reply_text, "❌ **Access Denied:** Aap authorized user nahi hain.")
        return
        
    try:
        editable = await safe_send(m.reply_text, '📂 **Kripya apni (.txt) link file upload karein...**')
        user_file: Message = await bot.listen(editable.chat.id)
        
        if not user_file.document:
            await safe_send(editable.edit, "❌ **Error:** Valid file nahi mili.")
            return

        await safe_send(editable.edit, "⏳ **File processing shuru hai...**")
        txt_path = await user_file.download()
        await safe_send(user_file.delete, True)
        
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
            await safe_send(editable.edit, "❌ **Error:** File ke andar koi valid links nahi mili.")
            return

        await safe_send(editable.edit, f"📊 Total **{len(queue)}** Items mile hain.\n\n🆔 Target **Channel ID** send karein (Ya direct inbox ke liye `/d`):")
        user_channel: Message = await bot.listen(editable.chat.id)
        channel_id = m.chat.id if "/d" in user_channel.text else user_channel.text.strip()
        await safe_send(user_channel.delete, True)

        await safe_send(editable.delete)
        start_msg = await safe_send(bot.send_message, chat_id=channel_id, text=f"🎯 **New Batch Started! Total Items: {len(queue)}**")

        # Fixed Header Dictionary structure to comply with modern appx rules
        appx_headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "*/*",
            "Origin": "https://web.appx.co.in",
            "Referer": "https://web.appx.co.in/"
        }

        count = 1
        for name, raw_url in queue:
            actual_url = raw_url.split("*", 1)[0].strip() if "*" in raw_url else raw_url
            
            # --- CASE 1: AGAR LINK PDF HAI ---
            if ".pdf" in actual_url.lower():
                status_msg = await safe_send(bot.send_message, channel_id, f"📥 **Downloading PDF ({count}/{len(queue)}):** `{name}`")
                local_pdf = f"{name}.pdf"
                try:
                    async with aiohttp.ClientSession(headers=appx_headers) as session:
                        async with session.get(actual_url, timeout=60) as response:
                            if response.status == 200:
                                with open(local_pdf, 'wb') as f:
                                    f.write(await response.read())
                            else:
                                raise Exception(f"Server returned status {response.status}")
                    
                    if os.path.exists(local_pdf) and os.path.getsize(local_pdf) > 500:
                        await safe_send(status_msg.edit, f"📤 **Uploading PDF:** `{name}`")
                        await safe_send(bot.send_document, chat_id=channel_id, document=local_pdf, caption=f"📄 **Document:** {str(count).zfill(3)}\n📝 **Title:** {name}")
                        os.remove(local_pdf)
                        await safe_send(status_msg.delete)
                        count += 1
                    else:
                        raise Exception("Downloaded PDF file is blank or corrupted.")
                except Exception as pdf_err:
                    await safe_send(bot.send_message, channel_id, f"❌ **PDF Failed:** `{name}`\n⚠️ **Reason:** {pdf_err}")
                    if os.path.exists(local_pdf): os.remove(local_pdf)
                
                await asyncio.sleep(4) # Standard cool down buffer
                continue

            # --- CASE 2: AGAR LINK VIDEO/ZIP HAI ---
            video_name = f"{str(count).zfill(3)}) {name}"
            status_msg = await safe_send(bot.send_message, channel_id, f"📥 **Downloading Video ({count}/{len(queue)}):** `{video_name}`")
            local_file = f"{video_name}.mp4"
            
            try:
                # Cleaner execution block using optimized modern args
                cmd = [
                    "ffmpeg", "-y",
                    "-headers", "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64)\r\nReferer: https://web.appx.co.in/\r\n",
                    "-i", actual_url,
                    "-c", "copy",
                    local_file
                ]
                
                process = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL
                )
                await process.wait()

                if os.path.exists(local_file) and os.path.getsize(local_file) > 5000:
                    await safe_send(status_msg.edit, f"📤 **Uploading Video:** `{video_name}`")
                    await safe_send(bot.send_video, chat_id=channel_id, video=local_file, caption=f"🎥 **Lecture:** {str(count).zfill(3)}\n📝 **Topic:** {name}")
                    os.remove(local_file)
                    await safe_send(status_msg.delete)
                    count += 1
                else:
                    raise FileNotFoundError("Video packet stream dump empty. Link is highly encrypted or expired.")

            except Exception as e:
                await safe_send(bot.send_message, channel_id, f"❌ **Video Failed:** `{video_name}`\n⚠️ **Reason:** {e}")
                if os.path.exists(local_file): os.remove(local_file)
                continue

            await asyncio.sleep(5) # Anti flood wait time to maintain account safety

        await safe_send(bot.send_message, channel_id, "🎉 **Batch successfully completed!**")

    except Exception as general_error:
        await m.reply_text(f"⚠️ **Core System Exception:** {general_error}")

bot.run()
