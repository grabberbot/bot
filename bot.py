from telegram import Update, ChatMember
from telegram.constants import ParseMode, ChatAction
from telegram.ext import Application, MessageHandler, CommandHandler, filters, CallbackContext, CallbackQueryHandler
from telegram import MessageEntity
import time
import random
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import logging
from telegram import Update
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, Updater
import asyncio

OFFENSIVE_WORDS = ["bsdk", "badword2", "badword3", "offensive_word", "curse_word"]
# Maximum number of warnings before action (e.g., mute or ban)
MAX_WARNINGS = 3
banned_users = set()
captcha_challenges = {}
failed_captcha_users = set()
# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


STAFF_USER_IDS = [5049701020, 2070455089, 5549799274, 6941946403]  # Replace with actual staff user IDs
OWNER_USER_ID = 6977793872, 6998394448
user_warnings = {}

# Your Bot Token
TOKEN = '7741291411:AAG_oqcm1DOKkVZe4oL3-h7mc-4t0A97f5A'
# Anti-flood protection
user_last_message_time = {}

# List of user IDs authorized to use the /broadcast command
AUTHORIZED_USER_IDS = [6977793872, 6998394448, 1087968824]  # Replace with actual user IDs
AUTHORIZED_GROUP_CHAT_IDS = [-1002439648517, -1009876543210]  # Replace with your group chat IDs

# Define a function to send a welcome message with an image
async def welcome(update: Update, context):
    # Get the new user who joined
    new_user = update.message.new_chat_members[0]
    
    # Create a rich HTML welcome message
    welcome_message = f"""
    <b>🎉 Welcome to the Group, {new_user.first_name}!</b> 🎉\n
    <b><i>We are so glad to have you with us. Here's some cool stuff you should know:</i></b>
    
    <blockquote>➡️ <b>Explore the group</b> and chat with awesome people! 🗨️
➡️ <b>Check out our pinned messages</b> for important info 📌
➡️ <b>Enjoy the best memes</b> 🎨</blockquote>
    
    <b>🚀 Let's get started with some cool images!</b>
    
    <i>Don't forget to follow the rules:</i> ⚖️
    📜 <u><a href="https://t.me/GameGivers/358">Group Rules</a> 📜</u>

    <i>Enjoy your stay, {new_user.first_name}! 🌟</i>
    """

    # Send the image with the welcome message as the caption
    image_url = "https://ibb.co/xCk8Gr2"  # Replace with your image URL

    await context.bot.send_photo(
        chat_id=update.message.chat_id,
        photo=image_url,
        caption=welcome_message,
        parse_mode=ParseMode.HTML
    )


# Function to check if user is an admin
async def is_user_admin(update: Update, context):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    return chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

# Define the broadcast command handler
async def broadcast(update: Update, context):
    user_id = update.message.from_user.id
    if user_id not in AUTHORIZED_USER_IDS:
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        message = " ".join(context.args)
        # Iterate through the authorized groups
        for group_chat_id in AUTHORIZED_GROUP_CHAT_IDS:
            await context.bot.send_chat_action(chat_id=group_chat_id, action=ChatAction.TYPING)
            await context.bot.send_message(
                chat_id=group_chat_id,
                text=message,
                parse_mode=ParseMode.HTML  # Enable HTML parsing for the broadcast message
            )
        await update.message.reply_text(f"Message broadcasted to {len(AUTHORIZED_GROUP_CHAT_IDS)} groups.")
    else:
        await update.message.reply_text("Usage: /broadcast <message>")

# Define the /id command handler with HTML parsing
async def id_command(update: Update, context):
    if update.message.reply_to_message:
        # If the user replied to a message, get the user ID of the person they replied to
        replied_user = update.message.reply_to_message.from_user
        id_message = f"""
        <b>User ID of the replied user:</b>\n
        <b>Name:</b> {replied_user.first_name} {replied_user.last_name if replied_user.last_name else ''}
        <b>Username:</b> @{replied_user.username if replied_user.username else 'N/A'}
        <b>User ID:</b> <code>{replied_user.id}</code>
        """
        await update.message.reply_text(id_message, parse_mode=ParseMode.HTML)
    
    elif context.args:
        # If the user sends /id <username>
        username = context.args[0]
        user = None
        # Search for the user in the group
        members = await context.bot.get_chat_member(update.message.chat_id)
        for member in members:
            if member.user.username == username:
                user = member.user
                break
        if user:
            id_message = f"""
            <b>User ID for @{username}:</b>\n
            <b>Name:</b> {user.first_name} {user.last_name if user.last_name else ''}
            <b>Username:</b> @{user.username}
            <b>User ID:</b> <code>{user.id}</code>
            """
            await update.message.reply_text(id_message, parse_mode=ParseMode.HTML)
        else:
            await update.message.reply_text(f"User @{username} not found in the group.", parse_mode=ParseMode.HTML)
    else:
        # If the user sends /id, return the group chat ID
        id_message = f"""
        <b>Group Chat ID:</b> <code>{update.message.chat_id}</code>
        """
        await update.message.reply_text(id_message, parse_mode=ParseMode.HTML)


# Mute command
async def mute(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to mute
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id,
            permissions={"can_send_messages": False}
        )
        await update.message.reply_text(f"User {user_id} has been muted.")
    else:
        await update.message.reply_text("Usage: /mute <user_id>")

# Unmute command
async def unmute(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to unmute
        await context.bot.restrict_chat_member(
            chat_id=update.message.chat_id,
            user_id=user_id,
            permissions={"can_send_messages": True}
        )
        await update.message.reply_text(f"User {user_id} has been unmuted.")
    else:
        await update.message.reply_text("Usage: /unmute <user_id>")

# Warn command
async def warn(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to warn
        if user_id not in user_warnings:
            user_warnings[user_id] = 0
        user_warnings[user_id] += 1
        
        # Check if the user has exceeded 3 warnings
        if user_warnings[user_id] >= 3:
            await mute_user(update, context, user_id)
            await update.message.reply_text(f"User {user_id} has been muted due to exceeding 3 warnings.")
        else:
            await update.message.reply_text(f"User {user_id} has been warned. Total warnings: {user_warnings[user_id]}")
    else:
        await update.message.reply_text("Usage: /warn <user_id>")

# Function to mute the user after exceeding 3 warnings
async def mute_user(update: Update, context: CallbackContext, user_id: int):
    await context.bot.restrict_chat_member(
        chat_id=update.message.chat_id,
        user_id=user_id,
        permissions={"can_send_messages": False}
    )

# Remove a warning from a user
async def removewarn(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to remove the warning from
        if user_id in user_warnings and user_warnings[user_id] > 0:
            user_warnings[user_id] -= 1
            await update.message.reply_text(f"One warning removed from user {user_id}. Total warnings: {user_warnings[user_id]}")
        else:
            await update.message.reply_text(f"User {user_id} has no warnings.")
    else:
        await update.message.reply_text("Usage: /removewarn <user_id>")

# Ban command
async def ban(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to ban
        await context.bot.ban_chat_member(chat_id=update.message.chat_id, user_id=user_id)
        await update.message.reply_text(f"User {user_id} has been banned.")
    else:
        await update.message.reply_text("Usage: /ban <user_id>")

# /unban command: Unban a user by their user ID
async def unban(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    # Check if the user is an admin
    if user_id not in context.bot.get_chat_administrators(chat_id):
        await update.message.reply_text("You are not an admin. Only admins can unban users.")
        return

    if len(context.args) == 0:
        await update.message.reply_text("Please provide the user ID to unban.")
        return

    target_user_id = int(context.args[0])

    # Check if the user is banned
    if target_user_id not in banned_users:
        await update.message.reply_text("This user is not banned.")
        return

    # Unban the user
    await context.bot.unban_chat_member(chat_id, target_user_id)
    banned_users.remove(target_user_id)  # Remove from banned users list
    await update.message.reply_text(f"User {target_user_id} has been unbanned.")

# Kick command
async def kick(update: Update, context: CallbackContext):
    if not await is_user_admin(update, context):
        await update.message.reply_text("You are not authorized to use this command.")
        return

    if context.args:
        user_id = int(context.args[0])  # User ID to kick
        await context.bot.kick_chat_member(chat_id=update.message.chat_id, user_id=user_id)
        await update.message.reply_text(f"User {user_id} has been kicked.")
    else:
        await update.message.reply_text("Usage: /kick <user_id>")


# Admin tag command
# /admin command to tag staff members (excluding owners)
async def admin(update: Update, context: CallbackContext):
    # Check if the user is an admin
    if await is_user_admin(update, context):
        chat_id = update.message.chat_id

        # Get the list of admins in the group
        admins = await context.bot.get_chat_administrators(chat_id)
        
        # Filter out staff members from the admin list
        staff_mentions = []
        for admin in admins:
            if admin.user.id in STAFF_USER_IDS and admin.user.id != OWNER_USER_ID:
                # Add staff members to the mention list
                staff_mentions.append(f"@{admin.user.username}" if admin.user.username else f"{admin.user.first_name}")

        # Send the list of staff mentions
        if staff_mentions:
            staff_tag_message = "Tagging all staff members: " + " ".join(staff_mentions)
            await update.message.reply_text(staff_tag_message)
        else:
            await update.message.reply_text("No staff members found in the group.")
    else:
        await update.message.reply_text("You are not authorized to use this command.")



# Handle mentions of admins
async def handle_mentions(update: Update, context: CallbackContext):
    # Get the text entities (mentions)
    entities = update.message.entities
    chat_id = update.message.chat_id
    user_id = update.message.from_user.id

    # Get the list of admins
    admins = await context.bot.get_chat_administrators(chat_id)
    admin_usernames = [admin.user.username for admin in admins if admin.user.username]

    # Check if the message sender is an admin
    sender_is_admin = any(admin.user.id == user_id for admin in admins)

    # Check if the message contains any mentions of admins
    for entity in entities:
        if entity.type == MessageEntity.MENTION:
            mentioned_username = update.message.text[entity.offset + 1: entity.offset + entity.length]  # Extract the mentioned username
            if mentioned_username in admin_usernames:
                # If an admin is mentioned and the sender is not an admin, warn the user
                if not sender_is_admin:
                    await update.message.reply_text(f"Please do not tag admins! You have been warned. If you continue, you will be muted. Use /admin to mention admins", parse_mode=ParseMode.HTML)
                    
                    # Add a warning to the user
                    if user_id not in user_warnings:
                        user_warnings[user_id] = 0
                    user_warnings[user_id] += 1
                    
                    # Mute the user if they have 3 or more warnings
                    if user_warnings[user_id] >= 3:
                        await mute_user(update, context, user_id)
                        await update.message.reply_text(f"User {user_id} has been muted due to exceeding 3 warnings.")
                break

# Function to handle message deletion attempts by non-admins
async def prevent_message_deletion(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    if not await is_user_admin(update, context):
        await update.message.reply_text("Only admins can delete messages.")
        return

# Function to check if a user is an admin
async def is_user_admin(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id

    chat_member = await context.bot.get_chat_member(chat_id, user_id)
    return chat_member.status in [ChatMember.ADMINISTRATOR, ChatMember.OWNER]

# Anti-flood protection: If user sends more than 5 messages within 5 seconds, mute them.
async def check_message_rate(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    current_time = time.time()

    # Initialize the last message time for the user if it doesn't exist
    if user_id not in user_last_message_time:
        user_last_message_time[user_id] = []

    # Remove messages older than 5 seconds
    user_last_message_time[user_id] = [timestamp for timestamp in user_last_message_time[user_id] if current_time - timestamp < 5]

    # Add the current message time
    user_last_message_time[user_id].append(current_time)

    # If there are more than 5 messages in the last 5 seconds, mute the user
    if len(user_last_message_time[user_id]) > 5:
        await mute_user(update, context, user_id)

# Function to mute a user and notify them about spamming
async def mute_user(update: Update, context: CallbackContext, user_id: int):
    chat_id = update.message.chat_id
    # Mute the user by restricting their permissions
    await context.bot.restrict_chat_member(chat_id, user_id, permissions={'can_send_messages': False})
    
    # Notify the user that they have been muted for spamming
    await context.bot.send_message(
        chat_id=chat_id,
        text=f"<b>You have been muted due to spamming. Please avoid flooding the chat with multiple messages in a short time.</b>",
        parse_mode=ParseMode.HTML
    )

    # Notify the group that the user was muted
    await update.message.reply_text(f"User {user_id} has been muted for spamming.")


# Anti-join flood protection
join_times = {}

async def check_join_rate(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    current_time = time.time()

    # Initialize the join time for the user if it doesn't exist
    if user_id not in join_times:
        join_times[user_id] = []

    # Remove joins older than 10 seconds
    join_times[user_id] = [timestamp for timestamp in join_times[user_id] if current_time - timestamp < 10]

    # Add the current join time
    join_times[user_id].append(current_time)

    # If there are more than 3 joins in the last 10 seconds, kick the user
    if len(join_times[user_id]) > 3:
        await context.bot.kick_chat_member(chat_id, user_id)
        await update.message.reply_text(f"User {user_id} has been kicked for join spamming.")

# Activity monitoring
async def log_activity(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    chat_id = update.message.chat_id
    message = update.message.text

    logger.info(f"User {user_id} sent a message in chat {chat_id}: {message}")


# Function to check if a message contains offensive language
def contains_offensive_language(message_text: str) -> bool:
    message_text = message_text.lower()  # Convert to lowercase for case-insensitive comparison
    for word in OFFENSIVE_WORDS:
        if word in message_text:
            return True
    return False

# Function to handle offensive language and issue warnings
async def handle_bad_words(update: Update, context: CallbackContext):
    # Ensure the update contains a message
    if update.message:
        user_id = update.message.from_user.id
        user_name = update.message.from_user.username
        message_text = update.message.text

        # Check if the message contains offensive language
        if contains_offensive_language(message_text):
            # Increment user's warning count
            if user_id in user_warnings:
                user_warnings[user_id] += 1
            else:
                user_warnings[user_id] = 1
            
            # Send warning message
            await update.message.reply(f"⚠️ Hey @{user_name}, please refrain from using offensive language! You have been warned. ({user_warnings[user_id]}/{MAX_WARNINGS})")

            # If the user exceeds the warning limit, mute or ban them
            if user_warnings[user_id] >= MAX_WARNINGS:
                await update.message.reply("⚠️ You have reached the maximum warnings. You will be muted for using offensive language.")
                await context.bot.restrict_chat_member(update.message.chat.id, user_id, can_send_messages=False)  # Mute user


# Function to handle the /flip command with simulated animation
async def flip_coin(update: Update, context: CallbackContext):
    # List of possible outcomes
    outcomes = ["Heads", "Tails"]
    
    # Send initial message (no HTML parsing)
    msg = await update.message.reply_text("Flipping the coin... 🪙")
    
    # Simulate spinning animation with multiple stages
    spinning_texts = [
        "Flipping the coin... 🪙",
        "Spinning... 🔄",
        "Spinning faster... ⏳",
        "Almost there... 🔄",
        "The coin is spinning... 🌀"
    ]
    
    # Loop through spinning stages and update message
    for text in spinning_texts:
        # Only update if the new text differs from the current one
        if msg.text != text:
            await msg.edit_text(text)
        await asyncio.sleep(0.5)  # Short delay to simulate spinning
    
    # Randomly choose an outcome
    result = random.choice(outcomes)
    
    # Send the final result with HTML formatting
    final_text = f"And the result is:\n <blockquote><u><b>{result}</b></u> 🎉</blockquote>"
    
    # Only edit if the final text differs from the current message
    if msg.text != final_text:
        await msg.edit_text(final_text, parse_mode="HTML")


# Store active giveaways and participants
active_giveaways = {}  # chat_id -> giveaway details
participants = {}  # chat_id -> list of participants
giveaway_expiration = {}  # chat_id -> expiration time

# Function to start the giveaway (only accessible by admins or bot with ID 1087968824)
async def start_giveaway(update: Update, context: CallbackContext):
    message = update.message

    # Get chat admins
    admins = await message.chat.get_administrators()

    # Check if the user is an admin or has the specific bot ID
    if message.from_user.id not in [admin.user.id for admin in admins] and message.from_user.id != 1087968824:
        await message.chat.send_message("Sorry, <b>only admins</b> or the bot with ID 1087968824 can start a giveaway.", parse_mode='HTML')
        return

    # Check if there's already an active giveaway
    if message.chat.id in active_giveaways and active_giveaways[message.chat.id]['status'] == "active":
        await message.chat.send_message("A giveaway is already ongoing! Try again later.", parse_mode='HTML')
        return

    # Retrieve the giveaway details from the command arguments
    args = context.args
    if len(args) < 3:
        await message.chat.send_message("Please provide <b>description</b>, <b>prize pool</b>, and <b>requirements</b>.", parse_mode='HTML')
        return

    prize_pool = args[0].replace("_", " ")  # Replacing underscores with spaces
    description = args[1].replace("_", " ")  # Replacing underscores with spaces
    requirements = args[2].replace("_", " ")  # Replacing underscores with spaces

    # Set the active giveaway details
    active_giveaways[message.chat.id] = {
        'prize_pool': prize_pool,
        'description': description,
        'requirements': requirements,
        'participants': [],
        'status': 'active',
        'winner': None
    }

    # Set expiration time (e.g., 24 hours)
    expiration_time = asyncio.get_event_loop().time() + 86400  # 24 hours from now
    giveaway_expiration[message.chat.id] = expiration_time

    # Create the "Join Giveaway" button
    keyboard = [
        [InlineKeyboardButton("Join Giveaway 🎉", callback_data="join_giveaway")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    # Send the giveaway message with all the details
    try:
        await message.chat.send_message(
            f"🎉 <b>Giveaway Started!</b> 🎉\n\n"
            f"<blockquote><b>Prize Pool:</b> {prize_pool}\n"
            f"<b>Description:</b> {description}\n"
            f"<b>Requirements:</b> {requirements}\n"
            f"<b>Total Participants:</b> {len(active_giveaways[message.chat.id]['participants'])}\n"
            f"<b>Winner:</b> None</blockquote>\n\n"
            f"<b><u>Click the button below to participate:</u></b>",
            parse_mode='HTML', reply_markup=reply_markup
        )
    except Exception as e:
        print(f"Error sending message: {e}")

    # Start a background task to close the giveaway after expiration
    context.job_queue.run_once(close_giveaway, 86400, chat_id=message.chat.id)  # Close after 24 hours

# Function to handle the button press (participating in the giveaway)
async def join_giveaway(update: Update, context: CallbackContext):
    callback_query = update.callback_query
    message = callback_query.message
    user_id = callback_query.from_user.id

    # Check if the giveaway is still active
    if message.chat.id not in active_giveaways or active_giveaways[message.chat.id]['status'] == 'inactive':
        await callback_query.answer("This giveaway has ended.", show_alert=True)
        return

    # Check if the user has already joined
    if user_id in active_giveaways[message.chat.id]['participants']:
        await callback_query.answer("You have already joined the giveaway!", show_alert=True)
        return

    # Add user to the list of participants
    active_giveaways[message.chat.id]['participants'].append(user_id)

    # Update the total participants in the message
    total_participants = len(active_giveaways[message.chat.id]['participants'])
    await callback_query.answer("You have successfully joined the giveaway! 🎉", show_alert=True)

    # Send a separate message to notify the group that the user joined the giveaway
    try:
        await message.chat.send_message(
            f"User <b>{callback_query.from_user.first_name}</b> has joined the giveaway! 🎉\n"
            f"<b>Total Participants:</b> {total_participants}",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending message: {e}")

# Function to randomly select a winner from the participants
async def select_winner(chat_id, context: CallbackContext):
    if chat_id not in active_giveaways or active_giveaways[chat_id]['status'] == 'inactive':
        return

    # Randomly select a winner
    winner_id = random.choice(active_giveaways[chat_id]['participants'])
    winner = await context.bot.get_chat_member(chat_id, winner_id)

    # Update the winner in the giveaway details
    active_giveaways[chat_id]['winner'] = winner.user.first_name

    # Notify the group of the winner
    await context.bot.send_message(
        chat_id,
        f"🎉 Congratulations! <b>{winner.user.first_name}</b> has won the giveaway! 🎉",
        parse_mode='HTML'
    )

    # DM the winner with their prize notification
    try:
        await context.bot.send_message(
            winner.user.id,
            f"🎉 Congratulations, <b>{winner.user.first_name}</b>! You have won the giveaway! 🎉",
            parse_mode='HTML'
        )
    except Exception as e:
        print(f"Error sending direct message to winner: {e}")

# Function to close the giveaway after expiration
async def close_giveaway(context: CallbackContext):
    chat_id = context.job.chat_id

    if chat_id in active_giveaways and active_giveaways[chat_id]['status'] == 'active':
        # Automatically select a winner
        await select_winner(chat_id, context)

        # Announce that the giveaway is closed
        await context.bot.send_message(chat_id, "⏳ The giveaway has ended. No more entries will be accepted.")
        
        # Reset giveaway status
        active_giveaways[chat_id]['status'] = 'inactive'

        # Update the giveaway message with winner details
        await context.bot.send_message(
            chat_id,
            f"🎉 The giveaway has ended! 🎉\n"
            f"<blockquote><b>Prize Pool:</b> {active_giveaways[chat_id]['prize_pool']}\n"
            f"<b>Description:</b> {active_giveaways[chat_id]['description']}\n"
            f"<b>Requirements:</b> {active_giveaways[chat_id]['requirements']}\n"
            f"<b>Total Participants:</b> {len(active_giveaways[chat_id]['participants'])}\n"
            f"<b>Winner:</b> {active_giveaways[chat_id]['winner']}</blockquote>",
            parse_mode='HTML'
        )

# Function to manually end the giveaway
async def end_giveaway(update: Update, context: CallbackContext):
    message = update.message

    # Get chat admins
    admins = await message.chat.get_administrators()

    # Check if the user is an admin
    if message.from_user.id not in [admin.user.id for admin in admins]:
        await message.chat.send_message("Sorry, <b>only admins</b> can end a giveaway.", parse_mode='HTML')
        return

    # Check if there is an active giveaway
    if message.chat.id not in active_giveaways or active_giveaways[message.chat.id]['status'] == 'inactive':
        await message.chat.send_message("No active giveaway to end.", parse_mode='HTML')
        return

    # Select the winner manually
    await select_winner(message.chat.id, context)

    # Announce the closure of the giveaway
    await message.chat.send_message("⏳ The giveaway has been manually ended. No more entries will be accepted.")

    # Update giveaway message with final details
    await context.bot.send_message(
        message.chat.id,
        f"🎉 The giveaway has ended! 🎉\n"
        f"<blockquote><b>Prize Pool:</b> {active_giveaways[message.chat.id]['prize_pool']}\n"
        f"<b>Description:</b> {active_giveaways[message.chat.id]['description']}\n"
        f"<b>Requirements:</b> {active_giveaways[message.chat.id]['requirements']}\n"
        f"<b>Total Participants:</b> {len(active_giveaways[message.chat.id]['participants'])}\n"
        f"<b>Winner:</b> {active_giveaways[message.chat.id]['winner']}</blockquote>",
        parse_mode='HTML'
    )

    # Reset giveaway status
    active_giveaways[message.chat.id] = None
    participants[message.chat.id] = []


# Function to handle errors globally
async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error occurred: {context.error}")

# Refactored handler functions
def add_command_handlers(application):
    commands = {
        "/flip": flip_coin,
        "/broadcast": broadcast,
        "/id": id_command,
        "/unban": unban,
        "/staff": admin,
        "/mute": mute,
        "/unmute": unmute,
        "/warn": warn,
        "/removewarn": removewarn,
        "/ban": ban,
        "/kick": kick,
        "/gw": start_giveaway,
        "/endgw": end_giveaway,
    }

    for command, handler in commands.items():
        application.add_handler(CommandHandler(command.lstrip("/"), handler))

def add_message_handlers(application):
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bad_words))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex(r'@'), handle_mentions))
    application.add_handler(MessageHandler(filters.TEXT, check_message_rate))
    application.add_handler(MessageHandler(filters.TEXT, log_activity))
    

def add_status_handlers(application):
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, check_join_rate))

def add_callback_query_handlers(application):
    application.add_handler(CallbackQueryHandler(join_giveaway, pattern="join_giveaway"))

def main():
    application = Application.builder().token(TOKEN).build()

    

    # Add all command, message, and status handlers
    add_command_handlers(application)
    add_message_handlers(application)
    add_status_handlers(application)
    add_callback_query_handlers(application)

    # Error handling
    application.add_error_handler(error_handler)

    # Start the bot
    application.run_polling()

if __name__ == "__main__":
    main()