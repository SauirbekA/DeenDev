import logging
import sqlite3
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
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

# Initialize the database
def init_db():
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    email TEXT,
                    token TEXT
                )''')
    conn.commit()
    conn.close()

def get_token(user_id):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('SELECT token FROM users WHERE user_id = ?', (user_id,))
    result = c.fetchone()
    conn.close()
    return result[0] if result else None

def set_token(user_id, email, token):
    conn = sqlite3.connect('users.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users (user_id, email, token) VALUES (?, ?, ?)', (user_id, email, token))
    conn.commit()
    conn.close()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Welcome! Use /register <email> <password>, /login <email> <password>, /logout to manage your account.")

async def register(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        _, email, password = update.message.text.split()
    except ValueError:
        await update.message.reply_text("Usage: /register <email> <password>")
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{AUTH_BASE_URL}register", json={
            "firstname": "Telegram",
            "lastname": "User",
            "email": email,
            "password": password,
            "role": "USER"
        }) as response:
            if response.status == 200:
                data = await response.json()
                access_token = data['access_token']
                set_token(user_id, email, access_token)
                await update.message.reply_text("Registration successful.")
            else:
                await update.message.reply_text("Registration failed.")

async def login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    try:
        _, email, password = update.message.text.split()
    except ValueError:
        await update.message.reply_text("Usage: /login <email> <password>")
        return

    async with aiohttp.ClientSession() as session:
        async with session.post(f"{AUTH_BASE_URL}authenticate", json={
            "email": email,
            "password": password
        }) as response:
            if response.status == 200:
                data = await response.json()
                access_token = data['access_token']
                set_token(user_id, email, access_token)
                await update.message.reply_text("Login successful.")
            else:
                await update.message.reply_text("Login failed.")

async def logout(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.message.from_user.id
    set_token(user_id, None, None)
    await update.message.reply_text("Logout successful.")

async def info(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:


    headers = {"Authorization": f"Bearer {token}"}
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


async def fetch_data(url: str, headers: dict) -> list:
    """Fetch data from the API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            if response.status == 200:
                return await response.json()
            else:
                logger.error(f"Failed to fetch data: {response.status}")
                return []

async def handle_button_callback(query, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = query.from_user.id
    token = get_token(user_id)
    if not token:
        await query.answer("Please log in first using /login <email> <password>")
        return

    headers = {"Authorization": f"Bearer {token}"}
    logger.info(f"Callback data: {query.data}")  # Log the callback data

    if query.data.startswith("category_"):
        category = query.data.split("_")[1]
        endpoint = INFO_CATEGORIES.get(category)
        if endpoint:
            data = await fetch_data(f"{BASE_URL}{endpoint}", headers)

            # Create buttons for each item
            keyboard = [
                [InlineKeyboardButton(item['title'], callback_data=f"item_{item['id']}")]
                for item in data
            ] + [[InlineKeyboardButton("Back", callback_data="back_info")]]
            reply_markup = InlineKeyboardMarkup(keyboard)
            await query.edit_message_text("Select an item:", reply_markup=reply_markup)

    # Other handlers here...

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await handle_button_callback(query, context)

def main() -> None:
    init_db()
    application = ApplicationBuilder().token(TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("register", register))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("logout", logout))
    application.add_handler(CommandHandler("info", info))
    # Other handlers here...
    application.add_handler(CallbackQueryHandler(button))

    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
