import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
import aiohttp

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Replace with your actual bot token
TOKEN = "6936679307:AAEtMUVlvRw0jNHcpH6MIVHJxRojHSSDeZM"

# API base URLs
BASE_URL = "http://oralbekov.dias19.fvds.ru/api/"
AUTH_BASE_URL = "http://localhost:8080/api/v1/auth/"

# Define the endpoints for categories under info, calendar, and news
INFO_CATEGORIES = {
    'main': 'info/main/',
    'what-to-take': 'info/what-to-take/'
}

CALENDAR_CATEGORIES = {
    'hajj': 'calendar/hajj/',
    'umrah': 'calendar/umrah/'
}

QUESTION_ENDPOINT = "questions/"
NEWS_ENDPOINT = "news/"

# New API endpoints
TAXI_ENDPOINT = "maps/taxi/"
PLACES_ENDPOINT = "maps/places/"
RESTAURANTS_ENDPOINT = "maps/restaurants/"
CITY_ENDPOINT = "maps/city/"
ROUTE_ENDPOINT = "maps/route/"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Use /info, /calendar, /questions, /news, /maps, /send_location to get started.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = [
        [InlineKeyboardButton("What to take", callback_data="category_what-to-take")],
        [InlineKeyboardButton("Main", callback_data="category_main")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a category:", reply_markup=reply_markup)

async def calendar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide category options when /calendar command is issued."""
    keyboard = [
        [InlineKeyboardButton("Hajj", callback_data="calendar_hajj")],
        [InlineKeyboardButton("Umrah", callback_data="calendar_umrah")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a category:", reply_markup=reply_markup)

async def questions(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display questions when /questions command is issued."""
    data = await fetch_data(f"{BASE_URL}{QUESTION_ENDPOINT}")

    # Store the questions in the context for later use
    context.user_data['questions'] = data

    # Create buttons for each question
    keyboard = [
        [InlineKeyboardButton(item['title_en'], callback_data=f"question_{item['id']}")]
        for item in data
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a question:", reply_markup=reply_markup)

async def news(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fetch and display news when /news command is issued."""
    data = await fetch_data(f"{BASE_URL}{NEWS_ENDPOINT}")

    # Store the news in the context for later use
    context.user_data['news'] = data

    # Create buttons for each news item
    keyboard = [
        [InlineKeyboardButton(item['title'], callback_data=f"news_{item['id']}")]
        for item in data
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Select a news item:", reply_markup=reply_markup)

async def maps(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Provide options when /maps command is issued."""
    keyboard = [
        [InlineKeyboardButton("Taxi", callback_data="maps_taxi")],
        [InlineKeyboardButton("Places", callback_data="maps_places")],
        [InlineKeyboardButton("Restaurants", callback_data="maps_restaurants")],
        [InlineKeyboardButton("City Info", callback_data="maps_city")],
        [InlineKeyboardButton("Route Info", callback_data="maps_route")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Please choose a category:", reply_markup=reply_markup)

async def fetch_data(url: str, headers: dict = None) -> list:
    """Fetch data from the API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch data: {response.status}")
                return []

async def handle_button_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info(f"Callback data: {query.data}")  # Log the callback data

    if query.data.startswith("category_"):
        category = query.data.split("_")[1]
        endpoint = INFO_CATEGORIES.get(category)
        if endpoint:
            data = await fetch_data(f"{BASE_URL}{endpoint}")

            # Create buttons for each item
            keyboard = [
                [InlineKeyboardButton(item['title'], callback_data=f"item_{item['id']}")]
                for item in data
            ] + [[InlineKeyboardButton("Back", callback_data="back_info")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Select an item:", reply_markup=reply_markup)

    elif query.data.startswith("calendar_"):
        category = query.data.split("_")[1]
        endpoint = CALENDAR_CATEGORIES.get(category)
        if endpoint:
            data = await fetch_data(f"{BASE_URL}{endpoint}")

            # Create buttons for each date
            keyboard = [
                           [InlineKeyboardButton(item['date'],
                                                 callback_data=f"calendar_date_{category}_{item['date']}")]
                           for item in data
                       ] + [[InlineKeyboardButton("Back", callback_data="back_calendar")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Select a date:", reply_markup=reply_markup)

    elif query.data.startswith("item_"):
        parts = query.data.split("_")
        if len(parts) >= 2:
            item_id = parts[1]
            endpoint = f"info/{item_id}/"
            item_data = await fetch_data(f"{BASE_URL}{endpoint}")

            if isinstance(item_data, list):
                item_data = item_data[0] if item_data else {}

            if item_data:
                # Extract the content value from the item_data dictionary
                content = item_data.get('content', 'Content not available')

                # Telegram has a 4096 character limit for message text
                if len(content) > 4096:
                    content = content[:4093] + '...'

                # Send the content value as a message
                await query.edit_message_text(content, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Back", callback_data="back_info")]]))
            else:
                await query.edit_message_text("Sorry, couldn't fetch the content for this item.",
                                              reply_markup=InlineKeyboardMarkup(
                                                  [[InlineKeyboardButton("Back", callback_data="back_info")]]))
        else:
            await query.edit_message_text("Invalid query data format.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="back_info")]]))

    elif query.data.startswith("calendar_date_"):
        parts = query.data.split("_")
        logger.info(f"parts: {parts}")
        if len(parts) >= 4:
            item_date = parts[3]
            category = parts[2]
            endpoint = CALENDAR_CATEGORIES.get(category)
            if endpoint:
                # Fetch all calendar data
                data = await fetch_data(f"{BASE_URL}{endpoint}")

                # Log the fetched data for debugging
                logger.info(f"Fetched data: {data}")

                # Find the specific item by date
                item_data = next((item for item in data if item["date"] == item_date), None)

                logger.info(f"Found item: {item_data}")

                if item_data:
                    # Extract the content value from the item_data dictionary
                    content = item_data.get('content', 'Content not available')

                    # Telegram has a 4096 character limit for message text
                    if len(content) > 4096:
                        content = content[:4093] + '...'

                    # Send the content value as a message
                    await query.edit_message_text(content, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(
                        [[InlineKeyboardButton("Back", callback_data="back_calendar")]]))
                else:
                    await query.edit_message_text("Sorry, couldn't fetch the content for this item.",
                                                  reply_markup=InlineKeyboardMarkup(
                                                      [[InlineKeyboardButton("Back", callback_data="back_calendar")]]))
            else:
                await query.edit_message_text("Invalid calendar category.", reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Back", callback_data="back_calendar")]]))
        else:
            await query.edit_message_text("Invalid query data format.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="back_calendar")]]))

    elif query.data.startswith("question_"):
        parts = query.data.split("_")
        if len(parts) >= 2:
            question_id = int(parts[1])
            questions = context.user_data['questions']

            question_data = next((item for item in questions if item["id"] == question_id), None)

            if question_data:
                # Extract the response value from the question_data dictionary
                response = question_data.get('response_en', 'Response not available')

                # Telegram has a 4096 character limit for message text
                if len(response) > 4096:
                    response = response[:4093] + '...'

                # Send the response value as a message
                await query.edit_message_text(response, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Back", callback_data="back_questions")]]))
            else:
                await query.edit_message_text("Sorry, couldn't fetch the response for this question.",
                                              reply_markup=InlineKeyboardMarkup(
                                                  [[InlineKeyboardButton("Back", callback_data="back_questions")]]))
        else:
            await query.edit_message_text("Invalid query data format.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="back_questions")]]))

    elif query.data.startswith("news_"):
        parts = query.data.split("_")
        if len(parts) >= 2:
            news_id = int(parts[1])
            news_items = context.user_data['news']

            news_data = next((item for item in news_items if item["id"] == news_id), None)

            if news_data:
                # Extract the content value from the news_data dictionary
                content = news_data.get('content', 'Content not available')

                # Telegram has a 4096 character limit for message text
                if len(content) > 4096:
                    content = content[:4093] + '...'

                # Send the content value as a message
                await query.edit_message_text(content, parse_mode='HTML', reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("Back", callback_data="back_news")]]))
            else:
                await query.edit_message_text("Sorry, couldn't fetch the content for this news item.",
                                              reply_markup=InlineKeyboardMarkup(
                                                  [[InlineKeyboardButton("Back", callback_data="back_news")]]))
        else:
            await query.edit_message_text("Invalid query data format.", reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Back", callback_data="back_news")]]))

    elif query.data.startswith("maps_"):
        category = query.data.split("_")[1]
        if category == 'taxi':
            data = await fetch_data(f"{BASE_URL}{TAXI_ENDPOINT}")
            response = "\n\n".join([f"{item['name']}: {item['desc']}\nLink: {item['link']}" for item in data])
        elif category == 'places':
            data = await fetch_data(f"{BASE_URL}{PLACES_ENDPOINT}")
            response = "\n\n".join(
                [f"{item['title']}: {item['content']}\nLocation: {item['latitude']}, {item['longitude']}" for item in
                 data])
        elif category == 'restaurants':
            data = await fetch_data(f"{BASE_URL}{RESTAURANTS_ENDPOINT}")
            response = "\n\n".join(
                [f"{item['title']}: {item['content']}\nRating: {item['rating']}\nPhone: {item['phone']}" for item in
                 data])
        elif category == 'city':
            data = await fetch_data(f"{BASE_URL}{CITY_ENDPOINT}")
            response = "\n\n".join([f"{item['name']}: {item['content']}" for item in data])
        elif category == 'route':
            data = await fetch_data(f"{BASE_URL}{ROUTE_ENDPOINT}")
            response = f"Route Info: {data}"
        else:
            response = "Invalid category"

        await query.edit_message_text(response, reply_markup=InlineKeyboardMarkup(
            [[InlineKeyboardButton("Back", callback_data="back_maps")]]))

    elif query.data.startswith("back_"):
        back_target = query.data.split("_")[1]
        if back_target == "info":
            await info(query, context)
        elif back_target == "calendar":
            await calendar(query, context)
        elif back_target == "questions":
            await questions(query, context)
        elif back_target == "news":
            await news(query, context)
        elif back_target == "maps":
            await maps(query, context)

async def request_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Ask the user to share their location."""
    await update.message.reply_text(
        "Please share your location.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Share Location", request_location=True)]
        ])
    )

async def location_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the location sent by the user."""
    user_location = update.message.location
    context.user_data['location'] = (user_location.latitude, user_location.longitude)
    await update.message.reply_text("Location received. Now use /send_location <pilgrim_id> to send the location.")

async def send_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle the /send_location command."""
    if 'location' not in context.user_data:
        await update.message.reply_text("First share your location using /request_location.")
        return

    latitude, longitude = context.user_data['location']
    try:
        _, pilgrim_id = update.message.text.split()
    except ValueError:
        await update.message.reply_text("Usage: /send_location <pilgrim_id>")
        return

    async with aiohttp.ClientSession() as session:
        async with session.put(f"http://localhost:8080/api/v1/pilgrim/update-location/{pilgrim_id}", json={
            "locationOne": str(latitude),
            "locationTwo": str(longitude)
        }) as response:
            if response.status == 200:
                await update.message.reply_text("Location updated successfully.")
            else:
                await update.message.reply_text("Failed to update location.")

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await handle_button_callback(query, context)

def main() -> None:
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info))
    application.add_handler(CommandHandler("calendar", calendar))
    application.add_handler(CommandHandler("questions", questions))
    application.add_handler(CommandHandler("news", news))
    application.add_handler(CommandHandler("maps", maps))
    application.add_handler(CommandHandler("request_location", request_location))
    application.add_handler(CommandHandler("send_location", send_location))
    application.add_handler(MessageHandler(filters.LOCATION, location_handler))
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
