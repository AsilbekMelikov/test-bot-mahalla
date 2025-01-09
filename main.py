import asyncio


from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, BotCommand
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import  ReplyKeyboardRemove
from database.data import db

from environs import Env


from keyboards.reply_keyboards import admin_keyboard,register_confirm_keyboard,send_confirm_keyboard
from keyboards.inline_keyboards import add_to_group

# Load environment variables
env = Env()
env.read_env()


# BOT TOKEN and other settings
BOT_TOKEN = env('BOT_TOKEN')
SUPER_ADMIN = 1130649180


# Initialize Bot and Dispatcher
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

bot_messages = []

# Define registration states
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
@dp.message(Command("start"))
async def start_command(message: Message):
    admin = db.get_admin(user_id=message.from_user.id)
    
    user_id = message.from_user.id


    if admin:
        await message.reply(
            text=(
                "👋 *Assalomu alayikum!* \n\n"
                "✨ *Yangilik Tarqatuvchi BOT*-imizga xush kelibsiz! 🎉\n\n"
                "_Biz bilan yangiliklar va ma'lumotlardan xabardor bo'ling!_ 📢"
            ),
            reply_markup=admin_keyboard(is_admin=True),
            parse_mode="Markdown"  
        )

    elif user_id == SUPER_ADMIN:
        await message.reply(
            text=(
                "👋 *Assalomu alayikum!* \n\n"
                "✨ *Yangilik Tarqatuvchi BOT*-imizga xush kelibsiz! 🎉\n\n"
                "_Biz bilan yangiliklar va ma'lumotlardan xabardor bo'ling!_ 📢"
            ),
            reply_markup=admin_keyboard(is_admin=False),
            parse_mode="Markdown"  
        )
    else:
        await message.answer(text="Botni guruhga qo'shib uni tasdiqlang.", reply_markup=add_to_group())
    

@dp.message(Command("add_group"))
async def add_group(message: Message):
    await message.answer(text="Botni guruhga qo'shib uni tasdiqlang.", reply_markup=add_to_group())

@dp.callback_query(lambda query: query.data == "check_admin")
async def check_group(query: CallbackQuery):
    await query.message.answer(text="Admin qilgan guruhingizdan istalgan habarni menga yuboring!")

    # Foydalanuvchidan xabarni kutish
    @dp.message(lambda message: message.forward_from_chat.id)
    async def handle_message(message: Message):
        # Agar xabar guruh yoki kanalga yuborilgan bo'lsa
        if message.forward_from_chat:
            chat_id = message.forward_from_chat.id

            # Kanal yoki guruhda adminligini tekshirish
            try:
                bot_member = await bot.get_chat_member(chat_id, bot.id)

                # Bot adminligini tekshirish
                if bot_member.status in ['administrator', 'creator']:
                    await bot.send_message(chat_id=message.from_user.id, text="Bot admin qilindi, raxmat!")
                    db.register_groups(group_name=message.forward_from_chat.full_name, group_id=message.forward_from_chat.id)
                else:
                    await bot.send_message(chat_id=message.from_user.id, text="Bot admin qilinmagan.")
            except Exception as e:
                await bot.send_message(chat_id=message.from_user.id, text=f"Bot guruhda admin emas yoki xato yuz berdi. {str(e)}")
        
        else:
            await bot.send_message(chat_id=message.from_user.id, text="Iltimos, kanal yoki guruhdan forward qilingan xabar yuboring.")



@dp.message(lambda message: message.text is not None and "👤 Admin qo'shish" in message.text)
async def add_admin(message: Message, state: FSMContext):
    user_id = message.from_user.id
    # if user_id != 1130649180:
    #     await message.reply("Sizda admin qo'shish huquqi yo'q. ❌")
    #     return

    await message.reply(f"""
    ✨ Ro'yxatdan o'tish uchun adminning ism va familyasini quyidagi tartibda kiriting: 

    📜 *Misol*: _Eshmatov Toshmat_ 

    🔍 Iltimos, ma'lumotlarni to'g'ri kiriting! 📝
    """, parse_mode="Markdown", reply_markup=ReplyKeyboardRemove())

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
        await message.reply("Iltimos, Admin ID raqamini to'g'ri formatda kiriting (faqat raqamlar).")
        return

    await state.update_data(user_id=int(user_id))
    data = await state.get_data()
    full_name = data.get("full_name")

    # Use the imported keyboard for confirmation
    keyboard = register_confirm_keyboard()  # Make sure you have this function defined

    await message.reply(
        f"Admin ismini: {full_name}\nAdmin ID raqami: {user_id}\nTasdiqlaysizmi?",
        reply_markup=keyboard
    )

    await state.set_state(Registration.waiting_for_confirmation.state)


# Handle confirmation
@dp.message(Registration.waiting_for_confirmation)
async def handle_confirmation(message: Message, state: FSMContext):
    data = await state.get_data()
    full_name = data.get("full_name")
    
    if message.text == "✅ Tasdiqlash Admin":
        user_id = data.get("user_id")  # Get user_id from state data

        if user_id is None:
            await message.reply("Xatolik: Foydalanuvchi ID topilmadi.")
            return

        # Register the user in the database
        db.register_admin(full_name=full_name, user_id=user_id)

        await message.reply(
            "Muvaffaqiyatli yangi admin qo'shdingiz!",
            reply_markup=admin_keyboard(is_admin=False)
        )

    elif message.text == "❌ Bekor qilish Admin":
      
        user_id = data.get("user_id")
        if user_id is None:
            await message.reply("Xatolik: Foydalanuvchi ID topilmadi.", reply_markup=admin_keyboard(is_admin=False))
        else:
            await message.reply("Ro'yxatdan o'tish bekor qilindi.",reply_markup=admin_keyboard(is_admin=False))
        
    
    await state.clear()


# Step 1: Request post content
@dp.message(lambda message: message.text is not  None and "📨 Post jo'natish" in message.text)
async def request_post_source(message: Message, state: FSMContext):
    await message.reply("Iltimos, yuboriladigan postni kiriting yoki boshqa kanaldan forward qiling:")
    await state.set_state(PostState.waiting_for_post_content.state)


# Step 2: Handle forwarded or text messages
@dp.message(PostState.waiting_for_post_content)
async def handle_post_content(message: Message, state: FSMContext):
    # Check if the message is forwarded or contains any media
    if message.forward_from or message.forward_from_chat:
        # For forwarded messages
        await state.update_data(post_content=message)  # Store the entire message object
        await message.reply(
            "Siz yuborishni tasdiqlaysizmi?\n\n✅ Tasdiqlash yoki ❌ Bekor qilish ni bosing.",
            reply_markup=send_confirm_keyboard()
        )
        await state.set_state(PostState.waiting_for_confirmation.state)
    elif message.text:
        # For text messages
        await state.update_data(post_content=message)  # Store the entire message object
        await message.reply(
            f"Siz yuborishni tasdiqlaysizmi?\n\nPost:\n{message.text}\n\n✅ Tasdiqlash yoki ❌ Bekor qilish ni bosing.",
            reply_markup=send_confirm_keyboard()
        )
        await state.set_state(PostState.waiting_for_confirmation.state)
    else:
        await message.reply("Iltimos, to'g'ri formatda post yuboring (matn, rasm, video yoki forward qilingan xabar).")



# Step 3: Confirm and send the post
@dp.message(PostState.waiting_for_confirmation, F.text == "✅ Tasdiqlash Post")
async def confirm_and_send_post(message: Message, state: FSMContext):
    # Retrieve the stored message
    data = await state.get_data()
    post_content = data.get("post_content")
    admin = message.from_user.id
    get_admin = db.get_admin(user_id=admin)

    if not post_content:

        if get_admin:
            await message.reply("Xato: Post ma'lumotlari topilmadi.", reply_markup=admin_keyboard(is_admin=True))
        else:
            await message.reply("Xato: Post ma'lumotlari topilmadi.", reply_markup=admin_keyboard(is_admin=False))

        return

    groups = db.get_groups()
    # Send the message to all groups
    total_groups = len(groups)
    success_count = 0
    failed_count = 0
    blocked_count = 0  # Yuborishda bloklangan guruhlar
    deactivated_count = 0  # O'chirilgan guruhlar
    not_found_count = 0  # Topilmagan guruhlar
    failed_groups = [] 

    # Har bir guruhga xabar yuborish
    for group in groups:
        group_id = group[2]
        group_name = group[1] 
        try:
            # Postni guruhga yuborish
            await bot.forward_message(
                chat_id=group_id,
                from_chat_id=post_content.chat.id,
                message_id=post_content.message_id
            )
            success_count += 1  # Yuborilgan guruhlar sonini oshirish
        except Exception as e:
            failed_groups.append(group_name) 

            # Xato turini aniqlash
            if "blocked" in str(e).lower():
                blocked_count += 1
            elif "deactivated" in str(e).lower():
                deactivated_count += 1
            elif "not found" in str(e).lower():
                not_found_count += 1
            else:
                failed_count += 1  # Boshqa xatolar

    # Statistika
    progress = (success_count / total_groups) * 100 if total_groups > 0 else 0


    if get_admin:
        await message.reply(
        f"Progress: {progress:.2f}% ({success_count + failed_count}/{total_groups} chats)\n"
        f"Success: {success_count}\n"
        f"Blocked: {blocked_count}\n"
        f"Deactivated: {deactivated_count}\n"
        f"Not Found: {not_found_count}\n"
        f"Failed: {failed_count}",
        reply_markup=admin_keyboard(is_admin=True)
    )
    else:
        await message.reply(
        f"Progress: {progress:.2f}% ({success_count + failed_count}/{total_groups} chats)\n"
        f"Success: {success_count}\n"
        f"Blocked: {blocked_count}\n"
        f"Deactivated: {deactivated_count}\n"
        f"Not Found: {not_found_count}\n"
        f"Failed: {failed_count}",
        reply_markup=admin_keyboard(is_admin=False)
    )
        
    if failed_groups:
        result_message = "Yuborilmagan guruhlar:\n"
        for index, group_name in enumerate(failed_groups, start=1):
            result_message += f"{index}. {group_name}\n"
        await message.answer(text=result_message)



@dp.message(F.text == "❌ Bekor qilish Post")
async def cancel_post(message: Message, state: FSMContext):
    admin = message.from_user.id
    get_admin = db.get_admin(user_id=admin)

    if get_admin:
        await message.reply("❌ Post jo'natish bekor qilindi.", reply_markup=admin_keyboard(is_admin=True))
        
    else:
        await message.reply("❌ Post jo'natish bekor qilindi.", reply_markup=admin_keyboard(is_admin=False))






@dp.message(Command("delete_admin"))
async def start_delete_admin(message: Message, state: FSMContext):
    

    # Check if the user is the super admin
    if message.from_user.id != SUPER_ADMIN:
        await message.reply("Faqat super admin adminlarni o'chirishi mumkin.")
        return

    # Retrieve the list of admins from the database
    admins = db.get_admins()

    if not admins:
        await message.reply("Hozirda hech qanday admin ro'yxatda mavjud emas.")
        return

    response = "👥 **Adminlar ro'yxati:**\n\n"
    for admin in admins:
        admin_id, full_name, user_id, created_at = admin
        response += f"🔹 **Ism:** {full_name}\n" \
                    f"🔹 **ID:** {user_id}\n" \
                    f"📅 **Qo'shilgan sana:** {created_at.strftime('%Y-%m-%d %H:%M:%S')}\n\n"

    await message.reply(response, parse_mode="Markdown")
    
    await message.reply(
        "Iltimos, o'chiriladigan adminning ID raqamini kiriting:",
        reply_markup=ReplyKeyboardRemove()
    )
    await state.set_state(AdminDeleteState.waiting_for_user_id)



# Handle user input for the user_id
@dp.message(AdminDeleteState.waiting_for_user_id)
async def handle_delete_admin_user_id(message: Message, state: FSMContext):
    user_id = message.text.strip()

    if not user_id.isdigit():
        await message.reply("Iltimos, ID raqamini to'g'ri formatda kiriting (faqat raqamlar).")
        return

    user_id = int(user_id)

    try:
        # Perform the deletion in the database
        db.delete_admin(user_id=user_id)  # Ensure `delete_admin` is implemented in your database class
        await message.reply(f"Admin ID: {user_id} muvaffaqiyatli o'chirildi.")
    except Exception as e:
        await message.reply(f"Xatolik: Admin ID {user_id} o'chirilmadi.\nSabab: {e}")

    # Clear the state
    await state.clear()


# Run the bot
async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
