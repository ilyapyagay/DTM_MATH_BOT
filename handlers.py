import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, InputMediaPhoto
from aiogram.filters import Command, CommandStart
from database import (
    get_user, grant_access, get_random_question, update_user_question, get_question_by_id,
    start_dtm_test_for_user, next_dtm_question_for_user, get_question_by_section, record_dtm_answer
)
from questions_data import SECTION_NAMES
from gemini_helper import explain_solution, clean_explanation_text
from geometry_drawer import generate_geometry_image
from config import SECRET_INVITE_CODE

router = Router()


# ФУНКЦИЯ ДЛЯ РАЗБИЕНИЯ ДЛИННЫХ СООБЩЕНИЙ
async def send_long_message(message_obj, text: str, max_length: int = 4000):
    """Отправляет длинное сообщение частями, если оно превышает лимит Telegram"""
    clean_text = clean_explanation_text(text)
    if len(clean_text) <= max_length:
        await message_obj.answer(clean_text)
        return
    
    parts = []
    current_part = ""
    for line in clean_text.split('\n'):
        if len(current_part) + len(line) + 1 <= max_length:
            current_part += line + '\n'
        else:
            if current_part:
                parts.append(current_part.strip())
            current_part = line + '\n'
    if current_part:
        parts.append(current_part.strip())
    
    for i, part in enumerate(parts):
        if i == 0:
            await message_obj.answer(f"🧑‍🏫 **Объяснение от ИИ-репетитора** (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await message_obj.answer(f"**Продолжение** (часть {i+1}/{len(parts)}):\n\n{part}")


def shuffle_options(question):
    """Перемешивает варианты ответов и распределяет их по кнопкам A, B, C, D"""
    raw_options = {
        'A': question.option_a,
        'B': question.option_b,
        'C': question.option_c,
        ('D'): question.option_d
    }
    correct_text = raw_options.get(question.correct_answer, question.option_b)
    
    texts = [question.option_a, question.option_b, question.option_c, question.option_d]
    random.shuffle(texts)
    
    shuffled_options = []
    new_correct_letter = 'A'
    letters = ['A', 'B', 'C', 'D']
    for i, text in enumerate(texts):
        letter = letters[i]
        shuffled_options.append((letter, text))
        if text == correct_text:
            new_correct_letter = letter
            
    return shuffled_options, new_correct_letter


async def display_question_message(event, header_str: str, question, keyboard):
    """Универсальная функция для отображения задачи с чертежом PNG (для геометрии) или текстом"""
    is_geom = (question and question.section_id == 10)
    
    raw_text = question.text
    if is_geom:
        # Убираем псевдографику ASCII-арта из текста задачи, так как показываем настоящую картинку
        lines = [line for line in raw_text.split('\n') if not any(c in line for c in '┌─│└┐┘╱╲●')]
        raw_text = '\n'.join(lines).strip()
        
    full_caption_or_text = (
        f"{header_str}\n"
        f"📂 **Раздел:** {question.section_name}\n\n"
        f"📝 **Задача:**\n{raw_text}"
    )
    
    if isinstance(event, CallbackQuery):
        msg = event.message
        if is_geom:
            photo_bytes = generate_geometry_image(question.text)
            photo_file = BufferedInputFile(photo_bytes, filename=f"geom_{question.id}.png")
            
            if msg.photo:
                try:
                    await msg.edit_media(
                        media=InputMediaPhoto(media=photo_file, caption=full_caption_or_text),
                        reply_markup=keyboard
                    )
                    return
                except Exception:
                    pass
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer_photo(photo=photo_file, caption=full_caption_or_text, reply_markup=keyboard)
        else:
            if msg.text:
                try:
                    await msg.edit_text(text=full_caption_or_text, reply_markup=keyboard)
                    return
                except Exception:
                    pass
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer(text=full_caption_or_text, reply_markup=keyboard)
    else:
        if is_geom:
            photo_bytes = generate_geometry_image(question.text)
            photo_file = BufferedInputFile(photo_bytes, filename=f"geom_{question.id}.png")
            await event.answer_photo(photo=photo_file, caption=full_caption_or_text, reply_markup=keyboard)
        else:
            await event.answer(text=full_caption_or_text, reply_markup=keyboard)


@router.message(CommandStart())
async def cmd_start(message: Message):
    telegram_id = message.from_user.id
    username = message.from_user.username
    args = message.text.split()
    
    if len(args) > 1:
        invite_code = args[1]
        if invite_code == SECRET_INVITE_CODE:
            await grant_access(telegram_id, username)
            await send_welcome_menu(message)
        else:
            await message.answer(
                "❌ **Неверный инвайт-код.**\n\n"
                "🔒 Доступ к боту ограничен. Получите правильную ссылку-приглашение."
            )
    else:
        user = await get_user(telegram_id)
        if user.has_access:
            await send_welcome_menu(message)
        else:
            await message.answer(
                "🔒 **Доступ ограничен.**\n\n"
                "Этот бот работает только по приглашениям.\n"
                "Получите ссылку-приглашение от администратора."
            )


async def send_welcome_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать тест УзБМБ (10 вопросов)", callback_data="start_dtm_test")],
        [InlineKeyboardButton(text="📚 Тренировка по разделам (1-10)", callback_data="show_topics")],
        [InlineKeyboardButton(text="🎲 Случайная задача из базы", callback_data="random_next")]
    ])
    await message.answer(
        "👋 **Добро пожаловать в тренажёр обязательного (базового) блока по математике УзБМБ!**\n\n"
        "📋 **О формате экзамена:**\n"
        "Обязательный блок математики для поступления в вузы Узбекистана состоит ровно из **10 вопросов**, "
        "проверяющих базовую школьную грамотность по 10 основным разделам строго по порядку:\n"
        "1️⃣ Натуральные числа и арифметика\n"
        "2️⃣ Дроби\n"
        "3️⃣ Пропорции и проценты\n"
        "4️⃣ Степени и корни\n"
        "5️⃣ Алгебраические выражения\n"
        "6️⃣ Уравнения и системы уравнений\n"
        "7️⃣ Неравенства\n"
        "8️⃣ Текстовые задачи\n"
        "9️⃣ Функции и их графики\n"
        "🔟 Основы планиметрии (геометрия с наглядными чертежами)\n\n"
        "💡 **Выберите режим тренировки ниже или используйте команды:**\n"
        "/test — официальный пробный тест из 10 вопросов по порядку\n"
        "/topics — выбор конкретного раздела для тренировки\n"
        "/random — случайная задача из всей базы (515+ задач)\n"
        "/help — справка по работе бота",
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    
    await message.answer(
        "📚 **Справка по боту DTM / УзБМБ Math Trainer**\n\n"
        "**Команды:**\n"
        "/test — запустить пробный тест УзБМБ из 10 вопросов\n"
        "/topics — тренировка задач по выбранной теме\n"
        "/random — решение случайных задач из общей базы\n"
        "/help — эта справка\n\n"
        "**Особенности:**\n"
        "1️⃣ Варианты ответов A, B, C, D каждый раз перемешиваются и равномерно распределяются!\n"
        "2️⃣ Задачи по геометрии сопровождаются наглядными графическими чертежами-картинками (PNG)\n"
        "3️⃣ При нажатии «🤷‍♂️ Объяснить решение (ИИ)» выдается чистое пошаговое объяснение без лишних символов Markdown."
    )


# --- 10-ВОПРОСНЫЙ ТЕСТ УЗБМБ ---

@router.message(Command("test"))
async def cmd_test(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    await run_dtm_test_start(message, user.telegram_id)


@router.callback_query(F.data == "start_dtm_test")
async def cb_start_dtm_test(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    if not user.has_access:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return
    await callback.answer()
    await run_dtm_test_start(callback, user.telegram_id)


async def run_dtm_test_start(event, telegram_id: int):
    question = await start_dtm_test_for_user(telegram_id)
    if not question:
        text = "❌ В базе пока нет вопросов по разделу 1."
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
        else:
            await event.answer(text)
        return
    
    shuffled_options, new_correct = shuffle_options(question)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    header = "🎯 **Обязательный (базовый) блок тестирования УзБМБ**\n📌 **Вопрос 1 из 10**"
    await display_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "dtm_next")
async def cb_dtm_next(callback: CallbackQuery):
    user, question = await next_dtm_question_for_user(callback.from_user.id)
    if not question:
        await callback.answer("❌ Вопросов больше нет", show_alert=True)
        return
    
    shuffled_options, new_correct = shuffle_options(question)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    header = f"🎯 **Обязательный (базовый) блок тестирования УзБМБ**\n📌 **Вопрос {user.dtm_step} из 10**"
    await display_question_message(callback, header, question, keyboard)
    await callback.answer()


@router.callback_query(F.data == "dtm_finish")
async def cb_dtm_finish(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    score = user.dtm_correct
    percent = score * 10
    
    if score >= 9:
        msg = "🏆 **Отличный результат!** Вы блестяще владеете школьной базой и готовы к экзамену!"
    elif score >= 7:
        msg = "👏 **Хороший уровень!** Вы уверенно справляетесь с большинством задач, повторите отдельные темы."
    else:
        msg = "📚 **Требуется повторение!** Рекомендуем отработать базовые разделы в режиме /topics."
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Пройти тест УзБМБ заново (10 вопросов)", callback_data="start_dtm_test")],
        [InlineKeyboardButton(text="📚 Выбрать тему для тренировки", callback_data="show_topics")]
    ])
    
    text = (
        "🏁 **Тестирование УзБМБ (Базовый блок) завершено!**\n\n"
        f"📊 **Ваш итоговый балл:** **{score} из 10** ({percent}%)\n\n"
        f"{msg}\n\n"
        "📌 **Обязательный блок включает ровно 10 разделов:**\n"
        "1️⃣ Натуральные числа и арифметика\n"
        "2️⃣ Дроби\n"
        "3️⃣ Пропорции и проценты\n"
        "4️⃣ Степени и корни\n"
        "5️⃣ Алгебраические выражения\n"
        "6️⃣ Уравнения и системы уравнений\n"
        "7️⃣ Неравенства\n"
        "8️⃣ Текстовые задачи\n"
        "9️⃣ Функции и их графики\n"
        "🔟 Основы планиметрии (геометрия)"
    )
    
    msg_obj = callback.message
    if msg_obj.photo:
        try:
            await msg_obj.delete()
        except Exception:
            pass
        await msg_obj.answer(text=text, reply_markup=keyboard)
    else:
        try:
            await msg_obj.edit_text(text=text, reply_markup=keyboard)
        except Exception:
            await msg_obj.answer(text=text, reply_markup=keyboard)
    await callback.answer()


# --- ОБРАБОТКА ОТВЕТОВ ПОЛЬЗОВАТЕЛЯ ---

@router.callback_query(F.data.startswith("answer_"))
async def process_answer(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    user_answer = data_parts[1]
    question_id = int(data_parts[2])
    correct_answer = data_parts[3]
    
    question = await get_question_by_id(question_id)
    if not question:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    is_correct = (user_answer == correct_answer)
    user = await record_dtm_answer(callback.from_user.id, is_correct)
    
    if is_correct:
        result_text = "✅ **Правильно! Отличная работа!** 🎉"
    else:
        result_text = f"❌ **Неправильно.** Правильный ответ: **{correct_answer}**\n\n💡 Нажмите кнопку ниже, чтобы ИИ-репетитор объяснил решение!"
    
    buttons = [
        [InlineKeyboardButton(text="🤷‍♂️ Объяснить решение (ИИ)", callback_data=f"explain_{question_id}")]
    ]
    
    if user.test_mode == "dtm_10":
        header = f"🎯 **Пробный тест УзБМБ** • Вопрос {user.dtm_step} из 10"
        if user.dtm_step < 10:
            buttons.append([InlineKeyboardButton(text=f"➡️ Следующий вопрос ({user.dtm_step + 1}/10)", callback_data="dtm_next")])
        else:
            buttons.append([InlineKeyboardButton(text="🏁 Завершить тест и посмотреть итоговый балл", callback_data="dtm_finish")])
    elif user.test_mode.startswith("topic_"):
        sec_id = int(user.test_mode.split("_")[1])
        header = f"📚 **Тренировка • Раздел {sec_id}**"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая задача по теме", callback_data=f"topic_select_{sec_id}")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать другую тему", callback_data="show_topics")])
    else:
        header = "🎲 **Случайная задача из базы**"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая случайная задача", callback_data="random_next")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать тему", callback_data="show_topics")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    is_geom = (question.section_id == 10)
    raw_text = question.text
    if is_geom:
        lines = [line for line in raw_text.split('\n') if not any(c in line for c in '┌─│└┐┘╱╲●')]
        raw_text = '\n'.join(lines).strip()
        
    full_text = (
        f"{header}\n"
        f"📂 **Раздел:** {question.section_name}\n\n"
        f"📝 **Задача:**\n{raw_text}\n\n"
        f"{result_text}"
    )
    
    msg = callback.message
    if msg.photo:
        try:
            photo_bytes = generate_geometry_image(question.text)
            photo_file = BufferedInputFile(photo_bytes, filename=f"geom_{question.id}.png")
            await msg.edit_media(
                media=InputMediaPhoto(media=photo_file, caption=full_text),
                reply_markup=keyboard
            )
        except Exception:
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer_photo(
                photo=BufferedInputFile(generate_geometry_image(question.text), filename="geom.png"),
                caption=full_text,
                reply_markup=keyboard
            )
    else:
        try:
            await msg.edit_text(text=full_text, reply_markup=keyboard)
        except Exception:
            await msg.answer(text=full_text, reply_markup=keyboard)
            
    await callback.answer()


@router.callback_query(F.data.startswith("explain_"))
async def explain_question_handler(callback: CallbackQuery):
    question_id = int(callback.data.split("_")[1])
    question = await get_question_by_id(question_id)
    
    if not question:
        await callback.answer("❌ Вопрос не найден", show_alert=True)
        return
    
    await callback.message.answer("🤔 Секунду, ИИ-репетитор готовит подробное пошаговое объяснение...")
    
    explanation = await explain_solution(
        question.text,
        question.correct_answer,
        question.option_a,
        question.option_b,
        question.option_c,
        question.option_d
    )
    
    await send_long_message(callback.message, explanation)
    await callback.answer()


# --- ТРЕНИРОВКА ПО РАЗДЕЛАМ (/topics) ---

@router.message(Command("topics"))
async def cmd_topics(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    await send_topics_list(message)


@router.callback_query(F.data == "show_topics")
async def cb_show_topics(callback: CallbackQuery):
    await send_topics_list(callback, is_edit=True)
    await callback.answer()


async def send_topics_list(event, is_edit: bool = False):
    buttons = []
    for sec_id in range(1, 11):
        sec_name = SECTION_NAMES.get(sec_id, f"Раздел {sec_id}")
        buttons.append([InlineKeyboardButton(text=sec_name, callback_data=f"topic_select_{sec_id}")])
    
    buttons.append([InlineKeyboardButton(text="🚀 Начать полный тест УзБМБ (10 вопросов)", callback_data="start_dtm_test")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = (
        "📚 **Выбор раздела для тренировки**\n\n"
        "Обязательный (базовый) блок по математике включает 10 разделов:\n"
        "Выберите тему, чтобы отработать задачи именно этого раздела:"
    )
    if isinstance(event, CallbackQuery):
        msg = event.message
        if msg.photo:
            try:
                await msg.delete()
            except Exception:
                pass
            await msg.answer(text=text, reply_markup=keyboard)
        else:
            try:
                await msg.edit_text(text, reply_markup=keyboard)
            except Exception:
                await msg.answer(text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("topic_select_"))
async def cb_topic_select(callback: CallbackQuery):
    sec_id = int(callback.data.split("_")[2])
    question = await get_question_by_section(callback.from_user.id, sec_id)
    
    if not question:
        await callback.answer("❌ В этом разделе пока нет задач", show_alert=True)
        return
    
    shuffled_options, new_correct = shuffle_options(question)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    header = f"📚 **Тренировка • Раздел {sec_id}**"
    await display_question_message(callback, header, question, keyboard)
    await callback.answer()


# --- РЕЖИМ СЛУЧАЙНЫХ ЗАДАЧ (/random) ---

@router.message(Command("random"))
async def cmd_random(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    await send_random_question(message, user.telegram_id)


@router.callback_query(F.data == "random_next")
async def cb_random_next(callback: CallbackQuery):
    await send_random_question(callback, callback.from_user.id)
    await callback.answer()


async def send_random_question(event, telegram_id: int):
    user = await get_user(telegram_id)
    user.test_mode = "random"
    await update_user_question(telegram_id, user.current_question_id)
    
    question = await get_random_question()
    if not question:
        text = "❌ В базе нет вопросов."
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
        else:
            await event.answer(text)
        return
    
    shuffled_options, new_correct = shuffle_options(question)
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{new_correct}"
        )] for letter, text in shuffled_options
    ])
    
    header = "🎲 **Случайная задача из базы УзБМБ**"
    await display_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()
