from database import get_user, grant_access, get_random_question, update_user_question, get_question_by_id, get_next_question_for_user
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command, CommandStart
from database import get_user, grant_access, get_random_question, update_user_question, get_question_by_id
from gemini_helper import explain_solution
from config import SECRET_INVITE_CODE
import random

router = Router()


# ФУНКЦИЯ ДЛЯ РАЗБИЕНИЯ ДЛИННЫХ СООБЩЕНИЙ
async def send_long_message(message_obj, text: str, max_length: int = 4000):
    """Отправляет длинное сообщение частями, если оно превышает лимит Telegram"""
    if len(text) <= max_length:
        await message_obj.answer(text)
        return
    
    # Разбиваем текст на части
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + '\n'
        else:
            if current_part:
                parts.append(current_part)
            current_part = line + '\n'
    
    if current_part:
        parts.append(current_part)
    
    # Отправляем по частям
    for i, part in enumerate(parts):
        if i == 0:
            await message_obj.answer(f"🧑‍🏫 **Объяснение от ИИ-репетитора** (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await message_obj.answer(f"**Продолжение** (часть {i+1}/{len(parts)}):\n\n{part}")


def shuffle_options(question):
    """Перемешивает варианты ответов и возвращает их в новом порядке"""
    options = [
        ('A', question.option_a),
        ('B', question.option_b),
        ('C', question.option_c),
        ('D', question.option_d)
    ]
    
    # Запоминаем правильный ответ
    correct_text = None
    for letter, text in options:
        if letter == question.correct_answer:
            correct_text = text
            break
    
    # Перемешиваем варианты
    random.shuffle(options)
    
    # Находим новую букву правильного ответа
    new_correct_letter = None
    for letter, text in options:
        if text == correct_text:
            new_correct_letter = letter
            break
    
    return options, new_correct_letter


@router.message(CommandStart())
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    
    args = message.text.split()
    
    if len(args) > 1:
        invite_code = args[1]
        
        if invite_code == SECRET_INVITE_CODE:
            await grant_access(telegram_id, username)
            await message.answer(
                "✅ **Доступ предоставлен!**\n\n"
                "🎓 Добро пожаловать в DTM Math Trainer!\n\n"
                "📚 Используй команды:\n"
                "/test — начать решение задач\n"
                "/help — помощь"
            )
        else:
            await message.answer(
                "❌ **Неверный инвайт-код.**\n\n"
                "🔒 Доступ к боту ограничен. Получите правильную ссылку-приглашение."
            )
    else:
        user = await get_user(telegram_id)
        
        if user.has_access:
            await message.answer(
                "👋 **С возвращением!**\n\n"
                "📚 Используй команды:\n"
                "/test — начать решение задач\n"
                "/help — помощь"
            )
        else:
            await message.answer(
                "🔒 **Доступ ограничен.**\n\n"
                "Этот бот работает только по приглашениям.\n"
                "Получите ссылку-приглашение от администратора."
            )


@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await get_user(message.from_user.id)
    
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    
    await message.answer(
        "📚 **Справка по боту DTM Math Trainer**\n\n"
        "**Команды:**\n"
        "/test — начать решение задач\n"
        "/help — эта справка\n\n"
        "**Как работает:**\n"
        "1️⃣ Бот присылает задачу с 4 вариантами ответа\n"
        "2️⃣ Нажми на кнопку с правильным ответом\n"
        "3️⃣ Если не понятно — нажми '🤷‍♂️ Объяснить' и ИИ-репетитор подробно объяснит решение!\n\n"
        "💡 Варианты ответов каждый раз перемешиваются — учи материал, а не расположение кнопок! 😉"
    )


@router.message(Command("test"))
@router.message(Command("test"))
async def cmd_test(message: Message):
    user = await get_user(message.from_user.id)
    
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    
    # Получаем следующий вопрос для этого пользователя
    question = await get_next_question_for_user(user.telegram_id)
    
    if not question:
        await message.answer("❌ В базе пока нет вопросов.")
        return
    
    await update_user_question(user.telegram_id, question.id)
    
    # Перемешиваем варианты ответов
    shuffled_options, new_correct = shuffle_options(question)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    await message.answer(
        f"📝 **Задача:**\n\n{question.text}",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    # Получаем следующий вопрос
    question = await get_next_question_for_user(user.telegram_id)
    
    if not question:
        await callback.answer("❌ В базе нет вопросов", show_alert=True)
        return
    
    await update_user_question(user.telegram_id, question.id)
    
    # Перемешиваем варианты
    shuffled_options, new_correct = shuffle_options(question)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    await callback.message.edit_text(
        f"📝 **Задача:**\n\n{question.text}",
        reply_markup=keyboard
    )
    
    await callback.answer()

@router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery):
    # Парсим данные: answer_B_15_C -> выбор=B, вопрос_id=15, правильный=C
    data_parts = callback.data.split("_")
    user_answer = data_parts[1]
    question_id = int(data_parts[2])
    correct_answer = data_parts[3]
    
    question = await get_question_by_id(question_id)
    
    if not question:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    # Проверяем правильность ответа
    is_correct = (user_answer == correct_answer)
    
    if is_correct:
        result_text = "✅ **Правильно! Отличная работа!** 🎉"
    else:
        result_text = f"❌ **Неправильно.** Правильный ответ: **{correct_answer}**\n\n💡 Нажми «Объяснить», чтобы разобраться!"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🤷‍♂️ Объяснить решение", callback_data=f"explain_{question_id}")],
        [InlineKeyboardButton(text="➡️ Следующий вопрос", callback_data="next_question")]
    ])
    
    await callback.message.edit_text(
        f"📝 **Задача:**\n\n{question.text}\n\n{result_text}",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("explain_"))
async def explain_question(callback: CallbackQuery):
    question_id = int(callback.data.split("_")[1])
    question = await get_question_by_id(question_id)
    
    if not question:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    await callback.message.answer("🤔 Секунду, ИИ-репетитор готовит подробное объяснение...")
    
    explanation = await explain_solution(
        question.text,
        question.correct_answer,
        question.option_a,
        question.option_b,
        question.option_c,
        question.option_d
    )
    
    # Используем функцию для отправки длинных сообщений
    await send_long_message(
        callback.message,
        explanation
    )
    
    await callback.answer()


@router.callback_query(F.data == "next_question")
async def next_question(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    
    question = await get_random_question()
    
    if not question:
        await callback.answer("❌ В базе нет вопросов", show_alert=True)
        return
    
    await update_user_question(user.telegram_id, question.id)
    
    # Перемешиваем варианты ответов
    shuffled_options, new_correct = shuffle_options(question)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    await callback.message.edit_text(
        f"📝 **Задача:**\n\n{question.text}",
        reply_markup=keyboard
    )
    
    await callback.answer()


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()