import os, asyncio, logging, sys

import pandas as pd
from aiogram import Bot, Dispatcher
from aiogram.types import (
    Message,
    FSInputFile,
    ChatMemberUpdated,
    CallbackQuery,
)
from aiogram.filters import CommandStart, Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database.data import db
from time import perf_counter
from aiogram.exceptions import TelegramRetryAfter
import asyncio


from keyboards.inline_keyboards import (
    admin_keyboard,
    register_confirm_keyboard,
    send_confirm_keyboard,
)
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# BOT TOKEN and other settings
BOT_TOKEN = os.getenv("TOKEN")
# SUPER_ADMIN = 1002999262
SUPER_ADMIN = 5014032073

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

bot_messages = []


class Registration(StatesGroup):
    waiting_for_full_name = State()
    waiting_for_user_id = State()
    waiting_for_confirmation = State()


class PostState(StatesGroup):
    waiting_for_post_content = State()
    waiting_for_confirmation = State()


class AdminDeleteState(StatesGroup):
    waiting_for_user_id = State()


# Start command handler
@dp.message(CommandStart())
async def start_command(message: Message):
    admin = db.get_admin(user_id=message.from_user.id)

    user_id = message.from_user.id

    if not admin is None:
        await message.reply(
            text=(
                "👋 *Assalomu alayikum!* \n\n"
                "✨ *Yangilik Tarqatuvchi BOT*-imizga xush kelibsiz! 🎉\n\n"
                "_Biz bilan yangiliklar va ma'lumotlardan xabardor bo'ling!_ 📢"
            ),
            reply_markup=admin_keyboard(is_admin=True),
            parse_mode="Markdown",
        )

    elif user_id == SUPER_ADMIN:
        await message.reply(
            text=(
                "👋 *Assalomu alayikum!* \n\n"
                "✨ *Yangilik Tarqatuvchi BOT*-imizga xush kelibsiz! 🎉\n\n"
                "_Biz bilan yangiliklar va ma'lumotlardan xabardor bo'ling!_ 📢"
            ),
            reply_markup=admin_keyboard(is_admin=False),
            parse_mode="Markdown",
        )


@dp.callback_query(lambda c: c.data in ["add_admin"])
async def add_admin(query: CallbackQuery, state: FSMContext):
    user_id = query.from_user.id

    await query.message.reply(
        f"""
    ✨ Ro'yxatdan o'tish uchun adminning ism va familyasini quyidagi tartibda kiriting: 

    📜 *Misol*: _Eshmatov Toshmat_ 

    🔍 Iltimos, ma'lumotlarni to'g'ri kiriting! 📝
    """,
        parse_mode="Markdown",
    )

    await state.set_state(Registration.waiting_for_full_name.state)


# Handle full name input
@dp.message(Registration.waiting_for_full_name)
async def handle_full_name(message: Message, state: FSMContext):
    full_name = message.text
    await state.update_data(full_name=full_name)

    await message.reply("Iltimos, Yangi admin ID raqamini kiriting:")
    await state.set_state(Registration.waiting_for_user_id.state)


# Handle user ID input
@dp.message(Registration.waiting_for_user_id)
async def handle_user_id(message: Message, state: FSMContext):
    user_id = message.text
    if not user_id.isdigit():
        await message.reply(
            "Iltimos, Admin ID raqamini to'g'ri formatda kiriting (faqat raqamlar)."
        )
        return

    await state.update_data(user_id=int(user_id))
    data = await state.get_data()
    full_name = data.get("full_name")

    # Use the imported keyboard for confirmation
    keyboard = register_confirm_keyboard()  # Make sure you have this function defined

    await message.reply(
        f"Admin ismini: {full_name}\nAdmin ID raqami: {user_id}\nTasdiqlaysizmi?",
        reply_markup=keyboard,
    )

    await state.set_state(Registration.waiting_for_confirmation.state)


# Handle confirmation
@dp.callback_query(Registration.waiting_for_confirmation)
async def handle_confirmation(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")

    if query.data == "confirm_admin":
        user_id = data.get("user_id")  # Get user_id from state data

        if user_id is None:
            await query.message.reply("Xatolik: Foydalanuvchi ID topilmadi.")
            return

        # Register the user in the database
        db.register_admin(full_name=full_name, user_id=user_id)

        await query.message.reply(
            "Muvaffaqiyatli yangi admin qo'shdingiz!",
            reply_markup=admin_keyboard(is_admin=False),
        )

    elif query.data == "cancel_admin":

        user_id = data.get("user_id")
        if user_id is None:
            await query.message.reply(
                "Xatolik: Foydalanuvchi ID topilmadi.",
                reply_markup=admin_keyboard(is_admin=False),
            )
        else:
            await query.message.reply(
                "Ro'yxatdan o'tish bekor qilindi.",
                reply_markup=admin_keyboard(is_admin=False),
            )

    await state.clear()


# Step 1: Request post content
@dp.callback_query(lambda c: c.data in ["send_post"])
async def request_post_source(query: CallbackQuery, state: FSMContext):
    await query.message.reply(
        "Iltimos, yuboriladigan postni kiriting yoki boshqa kanaldan forward qiling:"
    )
    await state.set_state(PostState.waiting_for_post_content.state)


# Step 2: Handle forwarded or text messages
@dp.message(PostState.waiting_for_post_content)
async def handle_post_content(message: Message, state: FSMContext):
    # Check if the message is forwarded or contains any media
    if message.forward_from or message.forward_from_chat or message.from_user:
        # For forwarded messages
        await state.update_data(post_content=message)  # Store the entire message object
        await message.reply(
            "Siz yuborishni tasdiqlaysizmi?\n\n✅ Tasdiqlash yoki ❌ Bekor qilish ni bosing.",
            reply_markup=send_confirm_keyboard(),
        )
        await state.set_state(PostState.waiting_for_confirmation.state)

    elif message.text:
        # For text messages
        await state.update_data(post_content=message)  # Store the entire message object
        await message.reply(
            f"Siz yuborishni tasdiqlaysizmi?\n\nPost:\n{message.text}\n\n✅ Tasdiqlash yoki ❌ Bekor qilish ni bosing.",
            reply_markup=send_confirm_keyboard(),
        )
        await state.set_state(PostState.waiting_for_confirmation.state)

    else:
        await message.reply(
            "Iltimos, to'g'ri formatda post yuboring (matn, rasm, video yoki forward qilingan xabar)."
        )


# @dp.callback_query(
#     PostState.waiting_for_confirmation, lambda c: c.data in ["confirm_post"]
# )
# async def confirm_and_send_post(query: CallbackQuery, state: FSMContext):

#     # Retrieve the stored message
#     data = await state.get_data()
#     post_content = data.get("post_content")
#     admin = query.from_user.id
#     get_admin = db.get_admin(user_id=admin)

#     if not post_content:

#         if get_admin:
#             await query.message.reply(
#                 "Xato: Post ma'lumotlari topilmadi.",
#                 reply_markup=admin_keyboard(is_admin=True),
#             )
#         else:
#             await query.message.reply(
#                 "Xato: Post ma'lumotlari topilmadi.",
#                 reply_markup=admin_keyboard(is_admin=False),
#             )

#         return

#     groups = db.get_groups()

#     # Send the message to all groups
#     total_groups = len(groups)
#     success_count = 0
#     failed_count = 0
#     blocked_count = 0
#     deactivated_count = 0
#     not_found_count = 0
#     failed_groups = []

#     for index, group in enumerate(groups):
#         group_id = group[0]
#         try:
#             # Postni guruhga yuborish
#             await bot.forward_message(
#                 chat_id=group_id,
#                 from_chat_id=post_content.chat.id,
#                 message_id=post_content.message_id,
#             )
#             success_count += 1

#         except Exception as e:
#             print(e)

#             # Xato turini aniqlash
#             if "blocked" in str(e).lower():
#                 blocked_count += 1
#             elif "deactivated" in str(e).lower():
#                 deactivated_count += 1
#             elif "not found" in str(e).lower():
#                 not_found_count += 1
#             else:
#                 failed_count += 1  # Boshqa xatolar

#     # Statistika
#     progress = (success_count / total_groups) * 100 if total_groups > 0 else 0

#     if get_admin:
#         await query.message.reply(
#             f"Progress: {progress:.2f}% ({success_count + failed_count}/{total_groups} chats)\n"
#             f"Success: {success_count}\n"
#             f"Blocked: {blocked_count}\n"
#             f"Deactivated: {deactivated_count}\n"
#             f"Not Found: {not_found_count}\n"
#             f"Failed: {failed_count}",
#             reply_markup=admin_keyboard(is_admin=True),
#         )
#     else:

#         await query.message.reply(
#             f"Progress: {progress:.2f}% ({success_count + failed_count}/{total_groups} chats)\n"
#             f"Success: {success_count}\n"
#             f"Blocked: {blocked_count}\n"
#             f"Deactivated: {deactivated_count}\n"
#             f"Not Found: {not_found_count}\n"
#             f"Failed: {failed_count}",
#             reply_markup=admin_keyboard(is_admin=False),
#         )

#     await state.clear()


@dp.callback_query(
    PostState.waiting_for_confirmation, lambda c: c.data in ["confirm_post"]
)
async def confirm_and_send_post(query: CallbackQuery, state: FSMContext):

    data = await state.get_data()
    post_content = data.get("post_content")
    admin = query.from_user.id
    get_admin = db.get_admin(user_id=admin)

    if not post_content:
        if get_admin:
            await query.message.reply(
                "Xato: Post ma'lumotlari topilmadi.",
                reply_markup=admin_keyboard(is_admin=True),
            )
        else:
            await query.message.reply(
                "Xato: Post ma'lumotlari topilmadi.",
                reply_markup=admin_keyboard(is_admin=False),
            )
        return

    groups = db.get_groups()
    total_groups = len(groups)

    batch_size = 99

    statuses = {
        "total_success": 0,
        "total_blocked": 0,
        "total_failed": 0,
        "total_deactivated": 0,
        "total_not_found": 0,
        "total_not_forwarded": 0,
        "total_not_permitted": 0,
        "failed_groups": []
    }



    t = perf_counter()

    for i in range(0, total_groups, batch_size):
        partial_groups = groups[i: i + batch_size]

        tasks = []

        # for j in partial_groups:
        #    task = asyncio.create_task()
        #    tasks.append(task)
        
        try:
            await asyncio.gather(*[
                send_batch(query.bot, post_content, j[0], statuses) for j in partial_groups
            ])

        except TelegramRetryAfter as e:
            sleeping_time = e.retry_after + 3
            print(sleeping_time)
            await asyncio.sleep(sleeping_time) 
            await asyncio.gather(*[
                send_batch(query.bot, post_content, j[0], statuses) for j in partial_groups
            ])

        if i + batch_size < total_groups:
            print(f"Bot is sleeping 3s ...")
            await asyncio.sleep(3)

    
    diff = perf_counter() - t
    print("With asycio gather, time :{:.2f} s".format(diff))

    progress = (statuses['total_success'] / total_groups) * 100 if total_groups > 0 else 0
    final_report = (
        f"Final Report:{progress:.2f}% ({statuses['total_success'] + statuses['total_failed']}/{total_groups} chats)\n"
        f"Total Groups: {total_groups}\n"
        f"Success: {statuses['total_success']}\n"
        f"Blocked: {statuses['total_blocked']}\n"
        f"Deactivated: {statuses['total_deactivated']}\n"
        f"Not Found: {statuses['total_not_found']}\n"
        f"Failed: {statuses['total_failed']}\n"
        f"Total Not Sent: {statuses['total_not_forwarded']}\n"
        f"Total Not Permitted: {statuses['total_not_permitted']}\n"
        f"Failed Groups: {statuses['failed_groups'] if statuses['failed_groups'] else 'None'}"
    )

    if get_admin:
        await query.message.reply(
            final_report, reply_markup=admin_keyboard(is_admin=True)
        )
    else:
        await query.message.reply(
            final_report, reply_markup=admin_keyboard(is_admin=False)
        )

    # Clear the state
    await state.clear()


async def send_batch(bot: Bot, post_content, group_id, statuses):
    try:
        await bot.forward_message(
            chat_id=group_id,
            from_chat_id=post_content.chat.id,
            message_id=post_content.message_id,
        )
        statuses['total_success'] += 1
    except Exception as e:
        print(f"Error sending to group {group_id}: {e}")
        if "blocked" in str(e).lower():
            statuses['total_blocked'] += 1
        elif "deactivated" in str(e).lower():
            statuses['total_deactivated'] += 1
        elif "not found" in str(e).lower():
            statuses['total_not_found'] += 1
        elif "can't be forwarded" in str(e).lower():
            statuses['total_not_forwarded'] += 1
        elif "administrator rights" in str(e).lower():
            statuses['total_not_permitted'] += 1
        else:
            statuses['total_failed'] += 1
        statuses['failed_groups'].append(group_id)


@dp.callback_query(lambda c: c.data in ["cancel_post"])
async def cancel_post(query: CallbackQuery, state: FSMContext):
    admin = query.from_user.id
    get_admin = db.get_admin(user_id=admin)

    if get_admin:
        await query.message.reply(
            "❌ Post jo'natish bekor qilindi.",
            reply_markup=admin_keyboard(is_admin=True),
        )

    else:
        await query.message.reply(
            "❌ Post jo'natish bekor qilindi.",
            reply_markup=admin_keyboard(is_admin=False),
        )


@dp.message(Command("delete_admin"))
async def start_delete_admin(message: Message, state: FSMContext):

    # Retrieve the list of admins from the database
    admins = db.get_admins()

    if not admins:
        await message.reply("Hozirda hech qanday admin ro'yxatda mavjud emas.")
        return

    response = "👥 **Adminlar ro'yxati:**\n\n"
    for admin in admins:
        admin_id, full_name, user_id, created_at = admin
        response += (
            f"🔹 **Ism:** {full_name}\n"
            f"🔹 **ID:** {user_id}\n"
            f"📅 **Qo'shilgan sana:** {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )

    await message.reply(response, parse_mode="Markdown")

    await message.reply(
        "Iltimos, o'chiriladigan adminning ID raqamini kiriting:",
    )
    await state.set_state(AdminDeleteState.waiting_for_user_id)


# Handle user input for the user_id
@dp.message(AdminDeleteState.waiting_for_user_id)
async def handle_delete_admin_user_id(message: Message, state: FSMContext):
    user_id = message.text.strip()

    if not user_id.isdigit():
        await message.reply(
            "Iltimos, ID raqamini to'g'ri formatda kiriting (faqat raqamlar)."
        )
        return

    user_id = int(user_id)

    try:
        # Perform the deletion in the database
        db.delete_admin(
            user_id=user_id
        )  # Ensure `delete_admin` is implemented in your database class
        await message.reply(f"Admin ID: {user_id} muvaffaqiyatli o'chirildi.")
    except Exception as e:
        await message.reply(f"Xatolik: Admin ID {user_id} o'chirilmadi.\nSabab: {e}")

    # Clear the state
    await state.clear()


@dp.my_chat_member()
async def track_joined_groups(event: ChatMemberUpdated):
    """Track groups the bot joins or leaves."""
    chat = event.chat
    # group_id = str(chat.id)

    if event.new_chat_member.status in [
        "administrator",
    ] and chat.type in [
        "channel",
        "supergroup",
        "group",
    ]:

        # Bot added to a group
        db.register_groups(group_name=chat.title, group_id=chat.id)

    elif event.new_chat_member.status in ["left", "restricted", "kicked"]:

        # Bot removed from a group
        db.delete_group(group_id=chat.id)


@dp.callback_query(lambda c: c.data in ["all_groups"])
async def cancel_post(query: CallbackQuery, state: FSMContext):
    all_groups = db.get_all_groups()  # Fetch groups from the database

    # Convert to DataFrame
    df = pd.DataFrame(all_groups, columns=["ID", "Name", "Group ID", "Created At"])
    df["Created At"] = df["Created At"].apply(lambda x: x.strftime("%Y-%m-%d %H:%M:%S"))
    # Save DataFrame to a CSV file
    csv_file_path = "groups.csv"
    df.to_csv(csv_file_path, index=False)

    # Send the file to the user
    file = FSInputFile(csv_file_path)
    await query.message.answer_document(file)


# Run the bot
async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
