from telegram import Update, InlineQueryResultPhoto, InlineQueryResultGif, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram.parsemode import ParseMode
from telegram.ext.dispatcher import run_async
import re
import urllib.parse
import requests
import logging
import os

# start logging to file
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename='gmage_log.log', encoding='utf-8', level=logging.INFO)

# Define the API key and the search engine ID
global api_key, akindex, limit
search_engine_id = "your-google-search-engine-cx-id"
akindex = 0
limit = 0

# loading apikeys into a list
file_path = "apikeys.txt"
api_key = []
try:
    with open(file_path, "r") as file:
        # Read each line and add it to the list
        for line in file:
            api_key.append(line.strip())  # Strip any leading/trailing whitespaces
    logging.info(f"no of api_keys: {len(api_key)}")
except FileNotFoundError:
    logging.error("API KEYS File not found.")
except Exception as e:
    logging.error("An error occurred:", e)


# Save new User Ids
def save_user_info(update: Update, context: CallbackContext):
    try:
        user_id = update.inline_query.from_user.id
        username = update.inline_query.from_user.username
    except:
        user_id = update.message.from_user.id
        username = update.message.from_user.username

    # Check if the user already exists in the file
    file_path = "gmage_users.txt"
    if not os.path.exists(file_path):
        with open(file_path, "w"):
            pass  # Create the file if it doesn't exist

    with open(file_path, "r") as file:
        existing_users = file.readlines()

    if f"{user_id}, {username}\n" not in existing_users:
        with open(file_path, "a") as file:
            file.write(f"{user_id}, {username}\n")
            logging.info("New user: %s", username)

# Handler function for inline queries
@run_async
def inline_search(update, context):
    global api_key, akindex, limit
    query = update.inline_query.query
    if not query:
        return
    try:
        #logging.info("Search: %s", query)
        gquery = re.sub(r'-gif[s]{0,1}\b', '', query, flags=re.IGNORECASE) #query for gifs
        query = urllib.parse.quote_plus(query)
        gquery = urllib.parse.quote_plus(gquery)

        payload = {}
        headers = {
        'X-Referer': 'https://explorer.apis.google.com'
        }

        url = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={query}&searchType=image&num=10"
        response = requests.request("GET", url, headers=headers, data=payload)

        limit+=1
        if(limit == 100):
            akindex+=1
            if(akindex==len(api_key)):
                    akindex=0
            limit = 0
        while response.status_code != 200:
            akindex+=1
            if(akindex==len(api_key)):
                akindex=0
            logging.info(f"new key: {api_key[akindex]}")
            url = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={query}&searchType=image&num=10"
            response = requests.request("GET", url, headers=headers, data=payload)

        url2 = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={query}&searchType=image&num=10&start=11"
        url3 = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={query}&searchType=image&num=10&start=21"
        if re.search(r'\b(?:gif|gifs)\b', query, re.IGNORECASE):
            url = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={gquery}&searchType=image&fileType=gif&num=10"
            url2 = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={gquery}&searchType=image&fileType=gif&num=10&start=11"
            url3 = f"https://customsearch.googleapis.com/customsearch/v1?key={api_key[akindex]}&cx={search_engine_id}&q={gquery}&searchType=image&fileType=gif&num=10&start=21"
        

        response.raise_for_status()
        
        response = response.json()["items"]
        response2 = requests.request("GET", url2, headers=headers, data=payload).json()["items"]
        response3 = requests.request("GET", url3, headers=headers, data=payload).json()["items"]
        response.extend(response2)
        response.extend(response3)

        if len(response)>0:
            results = []
            for i in range (len(response)):
                if("." in os.path.basename(response[i]["link"])):
                    photo_url = response[i]["link"]
                    thumb_url = response[i]["link"]
                    if re.search(r'\b(?:gif|gifs)\b', query, re.IGNORECASE) and  ".gif" in photo_url.lower():
                        result = InlineQueryResultGif(id=str(i), title=response[i]["title"], gif_url=photo_url, thumb_url=thumb_url, gif_width=512, gif_height=512)
                    else:
                        result = InlineQueryResultPhoto(id=str(i), title=response[i]["title"], photo_url=photo_url, thumb_url=thumb_url, photo_width=512, photo_height=512)
                    results.append(result)
            
            update.inline_query.answer(results)

        else:
            update.inline_query.answer([])

    except Exception as e:
        logging.error("An error occurred: %s", e)
        update.inline_query.answer([])

    save_user_info(update, context)


# Define a command handler for the /start command
def start(update: Update, context: CallbackContext) -> None:
    response = f"🔎This bot can help you find and share images and gifs using Google search. It works automatically, no need to add it anywhere. Simply open any of your chats and type `@{context.bot.username} something` in the message field. Then tap on a result to send.\n\nFor example, try typing `@{context.bot.username} cute cats` here.\n\n🖼To search for Gifs, make sure to include the word `gif` or `gifs` inside your search query to directly load gifs from google images.\n\nFor example, try typing `@{context.bot.username} cute cat gifs` here.\n\n\nnote: to exclude the word `gif` or `gifs` from your query while searching for gifs, use `-gif` and `-gifs` instead"        
    update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)
    save_user_info(update, context)

# Define a function to respond back all received messages with the start message
def respond(update: Update, context: CallbackContext) -> None:
    try:
        if(update.message.via_bot.username == context.bot.username):
            return 0
    except:
        response = f"🔎This bot can help you find and share images and gifs using Google search. It works automatically, no need to add it anywhere. Simply open any of your chats and type `@{context.bot.username} something` in the message field. Then tap on a result to send.\n\nFor example, try typing `@{context.bot.username} cute cats` here.\n\n🖼To search for Gifs, make sure to include the word `gif` or `gifs` inside your search query to directly load gifs from google images.\n\nFor example, try typing `@{context.bot.username} cute cat gifs` here.\n\n\nnote: to exclude the word `gif` or `gifs` from your query while searching for gifs, use `-gif` and `-gifs` instead"        
        update.message.reply_text(response, parse_mode=ParseMode.MARKDOWN)

# Set up the bot and start polling for inline queries
updater = Updater("your-telegram-bot-token", use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler("start", start))
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, respond))
dispatcher.add_handler(InlineQueryHandler(inline_search))
updater.start_polling()
updater.idle()