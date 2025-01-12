from aiogram.types import ReplyKeyboardMarkup, KeyboardButton




def admin_keyboard(is_admin):
    # Create the "Admin qo'shish" button
    if is_admin:
        post_button = KeyboardButton(text="📨 Post jo'natish")
        keyboard = ReplyKeyboardMarkup(keyboard=[[post_button]], resize_keyboard=True)

    else:
        post_button = KeyboardButton(text="📨 Post jo'natish")
        admin_add_button = KeyboardButton(text="👤 Admin qo'shish")
        see_groups_button = KeyboardButton(text="📋Barcha Guruhlar")
        # Add the buttons to the keyboard
        keyboard = ReplyKeyboardMarkup(keyboard=[[admin_add_button, post_button], [see_groups_button]], resize_keyboard=True)

    return keyboard





def send_confirm_keyboard():
    # Create confirmation buttons
    confirm_button = KeyboardButton(text="✅ Tasdiqlash Post")
    cancel_button = KeyboardButton(text="❌ Bekor qilish Post")
    keyboard = ReplyKeyboardMarkup(keyboard=[[confirm_button,cancel_button]], resize_keyboard=True)

    return keyboard


def register_confirm_keyboard():
    # Create confirmation buttons
    confirm_button = KeyboardButton(text="✅ Tasdiqlash Admin")
    cancel_button = KeyboardButton(text="❌ Bekor qilish Admin")
    keyboard = ReplyKeyboardMarkup(keyboard=[[confirm_button,cancel_button]], resize_keyboard=True)

    return keyboard

