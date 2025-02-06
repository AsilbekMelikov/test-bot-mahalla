from aiogram.utils.keyboard import InlineKeyboardBuilder



def admin_keyboard(is_admin):
    builder = InlineKeyboardBuilder()
    if is_admin:
        builder.button(text="📨 Post jo'natish", callback_data="send_post")
    else:
        builder.button(text="📨 Post jo'natish", callback_data="send_post")
        builder.button(text="👤 Admin qo'shish", callback_data="add_admin")
        builder.button(text="📋Barcha Guruhlar", callback_data="all_groups")
        builder.adjust(2)

    return builder.as_markup()

def send_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash Post", callback_data="confirm_post")
    builder.button(text="❌ Bekor qilish Post", callback_data="cancel_post")
    builder.adjust(2)

    return builder.as_markup()


def register_confirm_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Tasdiqlash Admin", callback_data="confirm_admin")
    builder.button(text="❌ Bekor qilish Admin", callback_data="cancel_admin")
    builder.adjust(2)

    return builder.as_markup()