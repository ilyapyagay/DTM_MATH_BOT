import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, BufferedInputFile, InputMediaPhoto
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from database import (
    get_user, grant_access, get_random_question, update_user_question, get_question_by_id,
    start_dtm_test_for_user, next_dtm_question_for_user, get_question_by_section, get_question_by_subtopic, record_dtm_answer
)
from questions_data import SECTION_NAMES, SUBTOPICS
from gemini_helper import explain_solution, answer_followup_question, clean_explanation_text
from geometry_drawer import generate_geometry_image
from config import SECRET_INVITE_CODE

router = Router()


class AskAIState(StatesGroup):
    waiting_for_question = State()


# ФУНКЦИЯ ДЛЯ РАЗБИЕНИЯ ДЛИННЫХ СООБЩЕНИЙ
async def send_long_message(message_obj, text: str, max_length: int = 4000, reply_markup=None):
    """Отправляет длинное объяснение ИИ частями с теплым обращением к Викуле"""
    clean_text = clean_explanation_text(text)
    if len(clean_text) <= max_length:
        await message_obj.answer(clean_text, reply_markup=reply_markup)
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
        elif i == len(parts) - 1:
            await message_obj.answer(f"**Продолжение для Викули** (часть {i+1}/{len(parts)}):\n\n{part}", reply_markup=reply_markup)
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
    mapping = {
        'A': question.option_a,
        'B': question.option_b,
        'C': question.option_c,
        'D': question.option_d
    }
    return mapping.get(letter, "")


async def send_fresh_question_message(event_or_msg, header_str: str, question, keyboard):
    """Отправляет НОВОЕ сообщение с задачей В САМЫЙ НИЗ чата, удаляя или скрывая старое"""
    is_visual = (question and question.section_id in (9, 10))
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
        f"{header_str}\n"
        f"📂 **Раздел:** {question.section_name}\n"
        f"📌 **Подтема:** {question.subtopic_name} (Стандарт {question.year})\n\n"
        f"📝 **Задача для Викули:**\n{raw_text}\n\n"
        f"{options_str}"
    )
    
    # Если мы вызваны по нажатию кнопки — удаляем старое сообщение, чтобы новое было строго внизу
    if isinstance(event_or_msg, CallbackQuery):
        try:
            await event_or_msg.message.delete()
        except Exception:
            try:
                await event_or_msg.message.edit_reply_markup(reply_markup=None)
            except Exception:
                pass
        target_msg = event_or_msg.message
    else:
        target_msg = event_or_msg
        
    if is_visual:
        photo_bytes = generate_geometry_image(question.text, question.section_id)
        photo_file = BufferedInputFile(photo_bytes, filename=f"geom_{question.id}.png")
        await target_msg.answer_photo(photo=photo_file, caption=full_text, reply_markup=keyboard)
    else:
        await target_msg.answer(text=full_text, reply_markup=keyboard)


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
                "🔒 Доступ к боту ограничен. Введите правильный пароль."
            )
    else:
        user = await get_user(telegram_id)
        if user.has_access:
            await send_welcome_menu(message)
        else:
            await message.answer(
                "🔒 **Доступ к боту ограничен.**\n\n"
                "Этот личный тренажёр создан специально для Викули! 💖\n"
                "Введите секретный пароль вместе с командой, например:\n"
                "`/start dtm2026Vikulya`"
            )


async def send_welcome_menu(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📘 Решать тесты УзБМБ 2024 (10 вопросов)", callback_data="start_dtm_2024")],
        [InlineKeyboardButton(text="🔥 Решать тесты УзБМБ 2025 (10 вопросов)", callback_data="start_dtm_2025")],
        [InlineKeyboardButton(text="📚 Тестирование по разделам и подтемам", callback_data="show_topics")],
        [InlineKeyboardButton(text="🎲 Случайная задача для Викули", callback_data="random_next")]
    ])
    await message.answer(
        "👋 **Привет, Викуля! Добро пожаловать в твой личный тренажёр по математике УзБМБ!** 💖✨\n\n"
        "📋 **О формате экзаменов 2024 и 2025:**\n"
        "Обязательный блок математики состоит ровно из **10 вопросов** по 10 разделам школьной программы:\n"
        "🔸 **Стандарт 2024 года:** акцент на классические базовые формулы, прямые вычисления и простые уравнения.\n"
        "🔸 **Стандарт 2025 года:** практический и аналитический уклон (многоэтапные проценты, логические текстовые задачи, анализ графиков и чертежей).\n\n"
        "🌸 **Викуля, выбери режим тренировки ниже:**\n"
        "/test2024 — пробный тест стандарта 2024 (10 вопросов)\n"
        "/test2025 — пробный тест стандарта 2025 (10 вопросов)\n"
        "/topics — тренировка по конкретным темам и подтемам\n"
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
    await send_welcome_menu(message)


# --- ТЕСТЫ УЗБМБ 2024 И 2025 ---

@router.message(Command("test"))
@router.message(Command("test2025"))
async def cmd_test2025(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ Нет доступа.")
        return
    await run_dtm_test_start(message, user.telegram_id, year=2025)


@router.message(Command("test2024"))
async def cmd_test2024(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ Нет доступа.")
        return
    await run_dtm_test_start(message, user.telegram_id, year=2024)


@router.callback_query(F.data == "start_dtm_2025")
async def cb_start_dtm_2025(callback: CallbackQuery):
    await callback.answer()
    await run_dtm_test_start(callback, callback.from_user.id, year=2025)


@router.callback_query(F.data == "start_dtm_2024")
async def cb_start_dtm_2024(callback: CallbackQuery):
    await callback.answer()
    await run_dtm_test_start(callback, callback.from_user.id, year=2024)


async def run_dtm_test_start(event, telegram_id: int, year: int = 2025):
    question = await start_dtm_test_for_user(telegram_id, year=year)
    if not question:
        text = f"❌ В базе пока нет вопросов стандарта {year}."
        if isinstance(event, CallbackQuery):
            await event.message.answer(text)
        else:
            await event.answer(text)
        return
    
    keyboard = get_options_keyboard(question)
    header = f"🎯 **Тест УзБМБ {year}** • Вопрос 1 из 10 для Викули 💖"
    await send_fresh_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "dtm_next")
async def cb_dtm_next(callback: CallbackQuery):
    user, question = await next_dtm_question_for_user(callback.from_user.id)
    if not question:
        await callback.answer("❌ Вопросов больше нет", show_alert=True)
        return
    
    year = 2024 if "2024" in user.test_mode else 2025
    keyboard = get_options_keyboard(question)
    header = f"🎯 **Тест УзБМБ {year}** • Вопрос {user.dtm_step} из 10 для Викули 💖"
    await send_fresh_question_message(callback, header, question, keyboard)
    await callback.answer()


@router.callback_query(F.data == "dtm_finish")
async def cb_dtm_finish(callback: CallbackQuery):
    user = await get_user(callback.from_user.id)
    score = user.dtm_correct
    percent = score * 10
    year = 2024 if "2024" in user.test_mode else 2025
    
    if score >= 9:
        msg = "🏆 **Ты просто невероятная умница, Викуля!** 🌟 Отличный результат, ты на 100% готова к экзамену!"
    elif score >= 7:
        msg = "👏 **Очень хороший уровень, Викуля!** 💖 Ты отлично справляешься, осталось повторить совсем немного!"
    else:
        msg = "🌸 **Не переживай, Викуля!** Главное — практика. Давай потренируем отдельные темы, и всё обязательно получится! 💖"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"🚀 Пройти тест УзБМБ {year} заново", callback_data=f"start_dtm_{year}")],
        [InlineKeyboardButton(text="📚 Выбрать тему для тренировки", callback_data="show_topics")]
    ])
    
    text = (
        f"🏁 **Тестирование УзБМБ {year} для Викули завершено!** ✨\n\n"
        f"📊 **Твой итоговый балл:** **{score} из 10** ({percent}%)\n\n"
        f"{msg}\n\n"
        "🌸 Выбери следующее действие ниже:"
    )
    
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text=text, reply_markup=keyboard)
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
    
    if user.test_mode.startswith("dtm_"):
        year = 2024 if "2024" in user.test_mode else 2025
        header = f"🎯 **Тест УзБМБ {year}** • Вопрос {user.dtm_step} из 10"
        if user.dtm_step < 10:
            buttons.append([InlineKeyboardButton(text=f"➡️ Следующий вопрос ({user.dtm_step + 1}/10)", callback_data="dtm_next")])
        else:
            buttons.append([InlineKeyboardButton(text="🏁 Завершить тест и посмотреть итоговый балл", callback_data="dtm_finish")])
    elif user.test_mode.startswith("sub_"):
        sub_id = user.test_mode.split("_")[1]
        header = f"📚 **Тренировка для Викули • Подтема {sub_id}**"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая задача в подтеме", callback_data=f"subtopic_run_{sub_id}")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать другую тему", callback_data="show_topics")])
    elif user.test_mode.startswith("sec_"):
        sec_id = int(user.test_mode.split("_")[1])
        header = f"📚 **Тренировка для Викули • Раздел {sec_id}**"
        buttons.append([InlineKeyboardButton(text="➡️ Следующая задача в разделе", callback_data=f"sec_run_{sec_id}")])
        buttons.append([InlineKeyboardButton(text="📚 Выбрать другой раздел", callback_data="show_topics")])
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
        f"📂 **Раздел:** {question.section_name}\n"
        f"📌 **Подтема:** {question.subtopic_name} (Стандарт {question.year})\n\n"
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
    user = await get_user(callback.from_user.id)
    
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
    
    # Кнопка для задания вопроса ИИ + кнопка перехода к следующему вопросу вниз чата
    next_btn = []
    if user.test_mode.startswith("dtm_"):
        if user.dtm_step < 10:
            next_btn.append(InlineKeyboardButton(text=f"➡️ Следующий вопрос ({user.dtm_step + 1}/10)", callback_data="dtm_next"))
        else:
            next_btn.append(InlineKeyboardButton(text="🏁 Завершить тест и посмотреть итог", callback_data="dtm_finish"))
    elif user.test_mode.startswith("sub_"):
        sub_id = user.test_mode.split("_")[1]
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая задача в подтеме", callback_data=f"subtopic_run_{sub_id}"))
    elif user.test_mode.startswith("sec_"):
        sec_id = int(user.test_mode.split("_")[1])
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая задача в разделе", callback_data=f"sec_run_{sec_id}"))
    else:
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая случайная задача", callback_data="random_next"))

    followup_kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Спросить ИИ про непонятный момент", callback_data=f"askai_{question_id}")],
        next_btn
    ])
    
    await send_long_message(callback.message, explanation, reply_markup=followup_kb)
    await callback.answer()


@router.callback_query(F.data.startswith("askai_"))
async def cb_ask_ai(callback: CallbackQuery, state: FSMContext):
    question_id = int(callback.data.split("_")[1])
    await state.set_state(AskAIState.waiting_for_question)
    await state.update_data(question_id=question_id)
    
    await callback.message.answer(
        "💬 **Викуля, напиши свой вопрос прямо в чат!** 🌸✨\n\n"
        "Что именно в этой задачке тебе хотелось бы уточнить или разобрать подробнее? Твой личный ИИ-репетитор готов объяснить всё простыми словами!"
    )
    await callback.answer()


@router.message(AskAIState.waiting_for_question)
async def process_vika_question(message: Message, state: FSMContext):
    data = await state.get_data()
    question_id = data.get("question_id")
    question = await get_question_by_id(question_id)
    user = await get_user(message.from_user.id)
    
    await state.clear()
    
    if not question:
        await message.answer("❌ Задача не найдена.")
        return
        
    await message.answer("🤔 **Секунду, Викуля!** ИИ-репетитор думает над твоим вопросом... 🌸")
    
    reply_text = await answer_followup_question(question.text, question.correct_answer, message.text)
    
    next_btn = []
    if user.test_mode.startswith("dtm_"):
        if user.dtm_step < 10:
            next_btn.append(InlineKeyboardButton(text=f"➡️ Следующий вопрос ({user.dtm_step + 1}/10)", callback_data="dtm_next"))
        else:
            next_btn.append(InlineKeyboardButton(text="🏁 Завершить тест и посмотреть итог", callback_data="dtm_finish"))
    elif user.test_mode.startswith("sub_"):
        sub_id = user.test_mode.split("_")[1]
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая задача в подтеме", callback_data=f"subtopic_run_{sub_id}"))
    elif user.test_mode.startswith("sec_"):
        sec_id = int(user.test_mode.split("_")[1])
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая задача в разделе", callback_data=f"sec_run_{sec_id}"))
    else:
        next_btn.append(InlineKeyboardButton(text="➡️ Следующая случайная задача", callback_data="random_next"))

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💬 Спросить ИИ ещё раз", callback_data=f"askai_{question.id}")],
        next_btn
    ])
    await send_long_message(message, reply_text, reply_markup=kb)


# --- ТРЕНИРОВКА ПО РАЗДЕЛАМ И ПОДТЕМАМ (/topics) ---

@router.message(Command("topics"))
async def cmd_topics(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ Нет доступа.")
        return
    await send_topics_list(message)


@router.callback_query(F.data == "show_topics")
async def cb_show_topics(callback: CallbackQuery):
    await send_topics_list(callback)
    await callback.answer()


async def send_topics_list(event):
    buttons = []
    for sec_id in range(1, 11):
        sec_name = SECTION_NAMES.get(sec_id, f"Раздел {sec_id}")
        buttons.append([InlineKeyboardButton(text=sec_name, callback_data=f"sec_menu_{sec_id}")])
    
    buttons.append([InlineKeyboardButton(text="📘 Полный тест УзБМБ 2024", callback_data="start_dtm_2024")])
    buttons.append([InlineKeyboardButton(text="🔥 Полный тест УзБМБ 2025", callback_data="start_dtm_2025")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = (
        "🌸 **Викуля, выбери основной раздел для тренировки:** 💖\n\n"
        "Обязательный (базовый) блок по математике включает 10 разделов.\n"
        "Нажми на интересующую тему, чтобы увидеть список её конкретных подтем:"
    )
    
    if isinstance(event, CallbackQuery):
        try:
            await event.message.delete()
        except Exception:
            pass
        await event.message.answer(text=text, reply_markup=keyboard)
    else:
        await event.answer(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith("sec_menu_"))
async def cb_sec_menu(callback: CallbackQuery):
    sec_id = int(callback.data.split("_")[2])
    sec_name = SECTION_NAMES.get(sec_id, f"Раздел {sec_id}")
    subs = SUBTOPICS.get(sec_id, [])
    
    buttons = []
    for sub_id, sub_title in subs:
        buttons.append([InlineKeyboardButton(text=f"🔸 {sub_id} {sub_title}", callback_data=f"subtopic_run_{sub_id}")])
        
    buttons.append([InlineKeyboardButton(text=f"🎲 Все темы раздела {sec_id} вразброс", callback_data=f"sec_run_{sec_id}")])
    buttons.append([InlineKeyboardButton(text="⬅️ Назад ко всем разделам", callback_data="show_topics")])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    text = f"📂 **{sec_name}**\n\n🌸 **Викуля, выбери конкретную подтему:**"
    try:
        await callback.message.delete()
    except Exception:
        pass
    await callback.message.answer(text, reply_markup=keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("subtopic_run_"))
async def cb_subtopic_run(callback: CallbackQuery):
    sub_id = callback.data.split("_")[2]
    question = await get_question_by_subtopic(callback.from_user.id, sub_id)
    if not question:
        await callback.answer("❌ В этой подтеме пока нет задач", show_alert=True)
        return
    
    keyboard = get_options_keyboard(question)
    header = f"📚 **Тренировка для Викули • Подтема {sub_id}** 💖"
    await send_fresh_question_message(callback, header, question, keyboard)
    await callback.answer()


@router.callback_query(F.data.startswith("sec_run_"))
async def cb_sec_run(callback: CallbackQuery):
    sec_id = int(callback.data.split("_")[2])
    question = await get_question_by_section(callback.from_user.id, sec_id)
    if not question:
        await callback.answer("❌ В этом разделе пока нет задач", show_alert=True)
        return
    
    keyboard = get_options_keyboard(question)
    header = f"📚 **Тренировка для Викули • Раздел {sec_id}** 💖"
    await send_fresh_question_message(callback, header, question, keyboard)
    await callback.answer()


# --- РЕЖИМ СЛУЧАЙНЫХ ЗАДАЧ (/random) ---

@router.message(Command("random"))
async def cmd_random(message: Message):
    user = await get_user(message.from_user.id)
    if not user.has_access:
        await message.answer("❌ Нет доступа.")
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
    await send_fresh_question_message(event, header, question, keyboard)


@router.callback_query(F.data == "ignore")
async def ignore_callback(callback: CallbackQuery):
    await callback.answer()
