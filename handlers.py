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
    """Отправляет длинное объяснение ИИ частями с теплым обращением к Викуле"""
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
            await message_obj.answer(f"🧑‍🏫 **Объяснение для Викули** (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await message_obj.answer(f"**Продолжение для Викули** (часть {i+1}/{len(parts)}):\n\n{part}")


def get_options_keyboard(question):
    """Создает клавиатуру с вариантами ответа A, B, C, D точно в соответствии с базой данных"""
    options = [
        ('A', question.option_a),
        ('B', question.option_b),
        ('C', question.option_c),
        ('D', question.option_d)
    ]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"{letter}) {text}", 
            callback_data=f"answer_{letter}_{question.id}_{question.correct_answer}"
        )] for letter, text in options
    ])


def get_option_text(question, letter: str) -> str:
    """Возвращает текст варианта по букве ответа"""
    mapping = {
        'A': question.option_a,
        'B': question.option_b,
        'C': question.option_c,
        'D': question.option_d
    }
    return mapping.get(letter, "")


async def display_question_message(event, header_str: str, question, keyboard):
    """Универсальная функция для отображения задачи с графиком/чертежом PNG или текстом для Викули"""
    is_visual = (question and question.section_id in (9, 10))
    
    raw_text = question.text
    if is_visual:
        # Убираем псевдографику ASCII-арта из текста задачи, так как показываем настоящую картинку
        lines = [line for line in raw_text.split('\n') if not any(c in line for c in '┌─│└┐┘╱╲●')]
        raw_text = '\n'.join(lines).strip()
        
    options_str = (
        f"**Варианты ответа:**\n"
        f"A) {question.option_a}\n"
        f"B) {question.option_b}\n"
        f"C) {question.option_c}\n"
        f"D) {question.option_d}"
    )
        
    full_caption_or_text = (
        f"{header_str}\n"
        f"📂 **Раздел:** {question.section_name}\n\n"
        f"📝 **Задача для Викули:**\n{raw_text}\n\n"
        f"{options_str}"
    )
    
    if isinstance(event, CallbackQuery):
        msg = event.message
        if is_visual:
            photo_bytes = generate_geometry_image(question.text, question.section_id)
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
        if is_visual:
            photo_bytes = generate_geometry_image(question.text, question.section_id)
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
                "🔒 **Доступ к боту ограничен.**\n\n"
                "Этот личный тренажёр создан специально для Викули! 💖\n"
                "Введите секретный инвайт-код."
            )


async def send_welcome_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Начать тест УзБМБ (10 вопросов)", callback_data="start_dtm_test")],
        [InlineKeyboardButton(text="📚 Тренировка по разделам (1-10)", callback_data="show_topics")],
        [InlineKeyboardButton(text="🎲 Случайная задача для Викули", callback_data="random_next")]
    ])
    await message.answer(
        "👋 **Привет, Викуля! Добро пожаловать в твой личный тренажёр по математике УзБМБ!** 💖✨\n\n"
        "📋 **О формате экзамена:**\n"
        "Обязательный блок математики состоит ровно из **10 вопросов**, проверяющих базовую школьную грамотность строго по порядку:\n"
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
        "🌸 **Викуля, выбери удобный режим тренировки ниже:**\n"
        "/test — пройти пробный тест из 10 вопросов по порядку\n"
        "/topics — выбрать тему для прицельной отработки\n"
        "/random — решить случайную задачку\n"
        "/help — справка",
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ У вас нет доступа к боту.")
        return
    
    await message.answer(
        "💖 **Справка по личному тренажёру для Викули** ✨\n\n"
        "**Команды:**\n"
        "/test — запустить пробный тест УзБМБ из 10 вопросов\n"
        "/topics — тренировка задач по выбранной теме\n"
        "/random — решение случайных задач из общей базы\n"
        "/help — эта справка\n\n"
        "**Особенности бота для Викули:**\n"
        "1️⃣ Варианты ответов A, B, C, D всегда идеально совпадают с объяснением ИИ!\n"
        "2️⃣ Задачи по геометрии и функциям сопровождаются красивыми графиками и чертежами (PNG)\n"
        "3️⃣ ИИ-репетитор лично общается с Викой, подбадривает и даёт полезные лайфхаки! 🌟"
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
    
    keyboard = get_options_keyboard(question)
    header = "🎯 **Обязательный (базовый) блок тестирования УзБМБ**\n📌 **Вопрос 1 из 10 для Викули** 💖"
    await display_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "dtm_next")
async def cb_dtm_next(callback: CallbackQuery):
    user, question = await next_dtm_question_for_user(callback.from_user.id)
    if not question:
        await callback.answer("❌ Вопросов больше нет", show_alert=True)
        return
    
    keyboard = get_options_keyboard(question)
    header = f"🎯 **Обязательный (базовый) блок тестирования УзБМБ**\n📌 **Вопрос {user.dtm_step} из 10 для Викули** 💖"
    await display_question_message(callback, header, question, keyboard)
    await callback.answer()


@router.callback_query(F.data == "dtm_finish")
async def cb_dtm_finish(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    score = user.dtm_correct
    percent = score * 10
    
    if score >= 9:
        msg = "🏆 **Ты просто невероятная умница, Викуля!** 🌟 Отличный результат, ты на 100% готова к экзамену!"
    elif score >= 7:
        msg = "👏 **Очень хороший уровень, Викуля!** 💖 Ты отлично справляешься, осталось повторить совсем немного!"
    else:
        msg = "🌸 **Не переживай, Викуля!** Главное — практика. Давай потренируем отдельные темы, и всё обязательно получится! 💖"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🚀 Пройти тест заново (10 вопросов)", callback_data="start_dtm_test")],
        [InlineKeyboardButton(text="📚 Выбрать тему для тренировки", callback_data="show_topics")]
    ])
    
    text = (
        "🏁 **Тестирование УзБМБ для Викули завершено!** ✨\n\n"
        f"📊 **Твой итоговый балл:** **{score} из 10** ({percent}%)\n\n"
        f"{msg}\n\n"
        "📌 **Обязательный блок включает 10 разделов:**\n"
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
    correct_text = get_option_text(question, correct_answer)
    
    if is_correct:
        result_text = "🎉 **Умница, Викуля! Всё абсолютно правильно! Отличная работа!** 🌟💖"
    else:
        result_text = (
            f"💖 **Не расстраивайся, Викуля!**\n"
            f"Правильный ответ: **{correct_answer}) {correct_text}**\n\n"
            f"💡 Нажми кнопку ниже, чтобы твой личный ИИ-репетитор всё подробно тебе объяснил!"
        )
    
    buttons = [
        [InlineKeyboardButton(text="🤷‍♂️ Объяснить решение для Викули (ИИ)", callback_data=f"explain_{question_id}")]
    ]
    
    if user.test_mode == "dtm_10":
        header = f"🎯 **Пробный тест УзБМБ** • Вопрос {user.dtm_step} из 10"
        if user.dtm_step < 10:
            buttons.append([InlineKeyboardButton(text=f"➡️ Следующий вопрос ({user.dtm_step + 1}/10)", callback_data="dtm_next")])
        else:
            buttons.append([InlineKeyboardButton(text="🏁 Завершить тест и посмотреть итоговый балл", callback_data="dtm_finish")])
    elif user.test_mode.startswith("topic_"):
        sec_id = int(user.test_mode.split("_")[1])
        header = f"📚 **Тренировка для Викули • Раздел {sec_id}**"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая задача по теме", callback_data=f"topic_select_{sec_id}")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать другую тему", callback_data="show_topics")])
    else:
        header = "🎲 **Случайная задача для Викули** 💖"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая случайная задача", callback_data="random_next")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать тему", callback_data="show_topics")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    is_visual = (question.section_id in (9, 10))
    raw_text = question.text
    if is_visual:
        lines = [line for line in raw_text.split('\n') if not any(c in line for c in '┌─│└┐┘╱╲●')]
        raw_text = '\n'.join(lines).strip()
        
    options_str = (
        f"**Варианты ответа:**\n"
        f"A) {question.option_a}\n"
        f"B) {question.option_b}\n"
        f"C) {question.option_c}\n"
        f"D) {question.option_d}"
    )
        
    full_text = (
        f"{header}\n"
        f"📂 **Раздел:** {question.section_name}\n\n"
        f"📝 **Задача для Викули:**\n{raw_text}\n\n"
        f"{options_str}\n\n"
        f"{result_text}"
    )
    
    msg = callback.message
    if msg.photo:
        try:
            photo_bytes = generate_geometry_image(question.text, question.section_id)
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
                photo=BufferedInputFile(generate_geometry_image(question.text, question.section_id), filename="geom.png"),
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
    
    await callback.message.answer("🤔 **Секунду, Викуля!** Твой личный ИИ-репетитор готовит для тебя подробное объяснение... ✨💖")
    
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
        "🌸 **Викуля, выбери раздел для тренировки:** 💖\n\n"
        "Обязательный (базовый) блок по математике включает 10 разделов:\n"
        "Нажми на интересующую тебя тему, чтобы отработать задачи именно по ней:"
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
    
    keyboard = get_options_keyboard(question)
    header = f"📚 **Тренировка для Викули • Раздел {sec_id}** 💖"
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
    
    keyboard = get_options_keyboard(question)
    header = "🎲 **Случайная задача для Викули** 💖"
    await display_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()
