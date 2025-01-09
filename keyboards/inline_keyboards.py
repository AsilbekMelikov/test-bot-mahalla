from aiogram.utils.keyboard import InlineKeyboardBuilder

def add_to_group():
    builder = InlineKeyboardBuilder()
    builder.button(text="🤝 Guruhga qo'shish", url="https://telegram.me/neighborhood_newsbot?startgroup=start")
    builder.button(text="🔍 Tekshirish", callback_data="check_admin")

    return builder.as_markup()
