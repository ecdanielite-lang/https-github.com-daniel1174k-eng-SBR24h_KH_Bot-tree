# ============ HIDE TOKEN FROM LOGS (MUST BE FIRST) ============
import logging
logging.getLogger("httpx").setLevel(logging.WARNING)

# ============ IMPORTS ============
import os
import asyncio
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler

# ============ LOGGING ============
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ============ ENVIRONMENT VARIABLES ============
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
HUGGINGFACE_API_KEY = os.getenv('HUGGINGFACE_API_KEY')

if not TELEGRAM_TOKEN:
    raise ValueError("No TELEGRAM_BOT_TOKEN set!")
if not HUGGINGFACE_API_KEY:
    raise ValueError("No HUGGINGFACE_API_KEY set!")

# ============ HUGGING FACE API ============
API_URL = "https://api-inference.huggingface.co/models/mistralai/Mistral-7B-Instruct-v0.1"
hf_headers = {
    "Authorization": f"Bearer {HUGGINGFACE_API_KEY}",
    "Content-Type": "application/json"
}

def call_huggingface_api(prompt):
    try:
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": 600,
                "temperature": 0.85,
                "top_p": 0.95,
                "do_sample": True,
                "return_full_text": False
            }
        }
        response = requests.post(API_URL, headers=hf_headers, json=payload, timeout=30)
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', 'No response')
            return str(result)
        else:
            return f"API Error {response.status_code}: {response.text}"
    except requests.exceptions.Timeout:
        return "The request took too long. Please try again."
    except Exception as e:
        return f"Error: {str(e)}"

def parse_usernames(text):
    lines = text.strip().split('\n')
    usernames = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line and line[0].isdigit():
            parts = line.split('.', 1)
            if len(parts) > 1:
                name_part = parts[1].strip()
                if ' - ' in name_part:
                    name, reasoning = name_part.split(' - ', 1)
                    usernames.append({'name': name.strip(), 'reasoning': reasoning.strip()})
                elif ':' in name_part:
                    name, reasoning = name_part.split(':', 1)
                    usernames.append({'name': name.strip(), 'reasoning': reasoning.strip()})
                else:
                    usernames.append({'name': name_part, 'reasoning': ''})
    if not usernames:
        for line in lines:
            if line and not line.startswith('Here are') and not line.startswith('```'):
                clean_line = line.lstrip('*-* ').strip()
                if clean_line and len(clean_line) > 3:
                    usernames.append({'name': clean_line, 'reasoning': ''})
    return usernames if usernames else [{'name': text[:150], 'reasoning': 'Generated usernames'}]

# ============ FLASK - KEEPS RENDER ALIVE ============
flask_app = Flask(__name__)

@flask_app.route('/')
def health_check():
    return "TikTok Username Bot is running!", 200

# ============ COMMANDS ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    msg = (
        "<b>Welcome to TikTok Username Generator Bot!</b>\n\n"
        f"Hi {user.first_name}! I help you find the perfect TikTok username!\n\n"
        "<b>How to use me:</b>\n"
        "Simply describe your content niche and I generate 10 creative username ideas!\n\n"
        "<b>Examples:</b>\n"
        "- Gaming content creator focusing on FPS games\n"
        "- Fashion influencer sharing outfit ideas\n"
        "- Food reviewer trying street food\n"
        "- Fitness coach sharing workout routines\n\n"
        "<b>Commands:</b>\n"
        "/start - Show this message\n"
        "/help - Get help and tips\n"
        "/niches - See popular content niches\n"
        "/about - Learn more about this bot\n\n"
        "Ready to find your perfect username? Describe your content!"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>How to get the best TikTok usernames:</b>\n\n"
        "1. Describe your content niche\n"
        "2. Get 10 creative username ideas\n"
        "3. Mix and match elements!\n\n"
        "<b>Good descriptions:</b>\n"
        "- Travel vlogger exploring hidden gems\n"
        "- Tech reviewer testing the latest gadgets\n"
        "- Comedy skit creator making relatable content\n\n"
        "<b>Username tips:</b>\n"
        "- Use your niche keywords\n"
        "- Keep it short and memorable\n"
        "- Check if the username is available!\n\n"
        "Send /niches to see popular content categories!"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def niches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>Popular TikTok Content Niches:</b>\n\n"
        "1. Gaming - FPS, RPG, Mobile, Strategy\n"
        "2. Fashion - Outfit ideas, Styling, Hauls\n"
        "3. Food - Reviews, Cooking, Street food\n"
        "4. Fitness - Workouts, Nutrition, Yoga\n"
        "5. Travel - Vlogs, Hidden gems, Adventures\n"
        "6. Tech - Reviews, Tutorials, Gadgets, AI\n"
        "7. Comedy - Skits, Pranks, Relatable content\n"
        "8. Music - Covers, Originals, Beatmaking\n"
        "9. Education - Study tips, History, Science\n"
        "10. Lifestyle - Daily vlogs, Productivity\n"
        "11. Beauty - Makeup, Skincare, Hair\n"
        "12. Pets - Cute animals, Training, Funny moments\n\n"
        "Pick your niche and describe your content to me!"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def about_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "<b>About This Bot</b>\n\n"
        "Uses AI to generate creative TikTok usernames based on your content niche.\n\n"
        "<b>How it works:</b>\n"
        "1. You describe your content\n"
        "2. AI analyzes your description\n"
        "3. Generates 10 unique username ideas\n"
        "4. Each with explanation of why it works\n\n"
        "<b>Technology:</b>\n"
        "- Hugging Face AI (Mistral 7B)\n"
        "- Python Telegram Bot framework\n\n"
        "Made with love for content creators!"
    )
    await update.message.reply_text(msg, parse_mode='HTML')

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    description = update.message.text.strip()

    thinking_message = await update.message.reply_text(
        "<b>Generating creative TikTok usernames...</b>\n\n"
        "Analyzing your content niche and creating unique username ideas.\n"
        "This may take 10-20 seconds...\n\n"
        f"<b>Your content:</b>\n<i>{description[:100]}{'...' if len(description) > 100 else ''}</i>",
        parse_mode='HTML'
    )

    try:
        prompt = (
            "<|system|>\n"
            "You are a creative TikTok username generator. Generate unique, catchy, and memorable usernames.\n\n"
            "<|user|>\n"
            f"Generate 10 creative TikTok usernames for a content creator with this niche: {description}\n\n"
            "The usernames should be:\n"
            "- Short and memorable (under 20 characters if possible)\n"
            "- Easy to spell and pronounce\n"
            "- Related to their content niche\n"
            "- Creative and unique\n\n"
            "Format as a numbered list 1-10. For each, provide a brief explanation.\n\n"
            "<|assistant|>\n"
            f"Here are 10 creative TikTok usernames for \"{description}\":\n\n"
        )

        raw_response = call_huggingface_api(prompt)
        usernames_list = parse_usernames(raw_response)

        if usernames_list:
            response_text = "<b>Your TikTok Username Ideas:</b>\n\n"
            for idx, name_data in enumerate(usernames_list[:10], 1):
                name = name_data.get('name', 'Unknown').replace('@', '').strip()
                reasoning = name_data.get('reasoning', '')
                response_text += f"{idx}. <b>@{name}</b>\n"
                if reasoning:
                    response_text += f"   {reasoning}\n"
                response_text += "\n"

            response_text += "\n<b>Pro Tips:</b>\n"
            response_text += "- Check if the username is available on TikTok!\n"
            response_text += "- Try variations if taken\n"
            response_text += "- Combine elements from different suggestions\n"

            keyboard = [
                [InlineKeyboardButton("Try Again", callback_data="retry"),
                 InlineKeyboardButton("Niches", callback_data="niches")],
                [InlineKeyboardButton("Help", callback_data="help"),
                 InlineKeyboardButton("About", callback_data="about")]
            ]
            await thinking_message.edit_text(
                response_text,
                parse_mode='HTML',
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await thinking_message.edit_text(
                "Could not generate usernames. Please try a more specific description."
            )

    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await thinking_message.edit_text(
            f"<b>Something went wrong.</b>\n\nError: {str(e)}\n\nPlease try again.",
            parse_mode='HTML'
        )

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "retry":
        await query.edit_message_text(
            "<b>Ready to try again!</b>\n\nSend me a new content description!",
            parse_mode='HTML'
        )
    elif query.data == "niches":
        await query.edit_message_text(
            "<b>Popular TikTok Content Niches:</b>\n\n"
            "1. Gaming\n2. Fashion\n3. Food\n4. Fitness\n5. Travel\n"
            "6. Tech\n7. Comedy\n8. Music\n9. Education\n10. Lifestyle\n\n"
            "Pick one and describe your content to me!",
            parse_mode='HTML'
        )
    elif query.data == "help":
        await query.edit_message_text(
            "<b>Quick Help:</b>\n\n"
            "1. Describe your content niche\n"
            "2. I generate 10 creative usernames\n"
            "3. Check availability on TikTok!\n\n"
            "Example: Gaming content creator focusing on Valorant",
            parse_mode='HTML'
        )
    elif query.data == "about":
        await query.edit_message_text(
            "<b>TikTok Username Generator Bot</b>\n\n"
            "Creates 10 creative TikTok usernames using AI!\n\n"
            "Powered by Hugging Face AI (Mistral 7B)\n\n"
            "Ready to find your username? Describe your content!",
            parse_mode='HTML'
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} caused error {context.error}")
    try:
        if update and update.effective_message:
            await update.effective_message.reply_text("An error occurred. Please try again.")
    except Exception:
        pass

# ============ BOT STARTUP ============
async def run_bot_async():
    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("niches", niches_command))
    app.add_handler(CommandHandler("about", about_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(CallbackQueryHandler(button_callback))
    app.add_error_handler(error_handler)

    await app.initialize()
    await app.start()
    await app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )

    logger.info("TikTok Username Generator Bot is polling and ready!")

    while True:
        await asyncio.sleep(1)

def run_bot():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_bot_async())

bot_thread = threading.Thread(target=run_bot, daemon=True)
bot_thread.start()
