import random
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base, Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, select
from config import DATABASE_URL
from questions_data import QUESTIONS_DATA, SECTION_NAMES

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    
    telegram_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String, nullable=True)
    has_access: Mapped[bool] = mapped_column(Boolean, default=False)
    current_question_id: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Отслеживание прохождения 10-вопросного теста УзБМБ / ГЦТ
    test_mode: Mapped[str] = mapped_column(String, default="dtm_2025")
    dtm_step: Mapped[int] = mapped_column(Integer, default=1)      # 1..10
    dtm_correct: Mapped[int] = mapped_column(Integer, default=0)


class Question(Base):
    __tablename__ = "questions"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    section_id: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    section_name: Mapped[str] = mapped_column(String, nullable=False)
    subtopic_id: Mapped[str] = mapped_column(String, nullable=False, default="1.1")
    subtopic_name: Mapped[str] = mapped_column(String, nullable=False, default="НОД и НОК")
    year: Mapped[int] = mapped_column(Integer, nullable=False, default=2025)
    text: Mapped[str] = mapped_column(String, nullable=False)
    option_a: Mapped[str] = mapped_column(String, nullable=False)
    option_b: Mapped[str] = mapped_column(String, nullable=False)
    option_c: Mapped[str] = mapped_column(String, nullable=False)
    option_d: Mapped[str] = mapped_column(String, nullable=False)
    correct_answer: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="ru")


async def init_db():
    """Создаем таблицы в БД и заполняем задачами УзБМБ"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async with async_session() as session:
        need_reinit = False
        try:
            result = await session.execute(select(Question))
            questions_in_db = result.scalars().all()
            if len(questions_in_db) < 500:
                need_reinit = True
            else:
                q0 = questions_in_db[0]
                _ = q0.subtopic_id
                _ = q0.year
        except Exception:
            need_reinit = True

        if need_reinit:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)
                await conn.run_sync(Base.metadata.create_all)
            
            async with async_session() as new_session:
                questions = []
                for sec_id, sub_id, sub_name, yr, txt, a, b, c, d, corr in QUESTIONS_DATA:
                    questions.append(
                        Question(
                            section_id=sec_id,
                            section_name=SECTION_NAMES.get(sec_id, f"Раздел {sec_id}"),
                            subtopic_id=sub_id,
                            subtopic_name=sub_name,
                            year=yr,
                            text=txt,
                            option_a=a,
                            option_b=b,
                            option_c=c,
                            option_d=d,
                            correct_answer=corr,
                            language="ru"
                        )
                    )
                new_session.add_all(questions)
                await new_session.commit()
                print(f"✅ База данных успешно обновлена! Загружено {len(questions)} задач для Викули.")


async def get_user(telegram_id: int) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            user = User(telegram_id=telegram_id, has_access=False, test_mode="dtm_2025", dtm_step=1, dtm_correct=0)
            session.add(user)
            await session.commit()
            await session.refresh(user)
        return user


async def grant_access(telegram_id: int, username: str = None):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.has_access = True
            user.username = username
        else:
            user = User(telegram_id=telegram_id, username=username, has_access=True, test_mode="dtm_2025", dtm_step=1, dtm_correct=0)
            session.add(user)
        await session.commit()


async def get_question_by_id(question_id: int) -> Question:
    async with async_session() as session:
        result = await session.execute(select(Question).where(Question.id == question_id))
        return result.scalar_one_or_none()


async def update_user_question(telegram_id: int, question_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.current_question_id = question_id
            await session.commit()


async def get_random_question() -> Question:
    async with async_session() as session:
        result = await session.execute(select(Question))
        questions = result.scalars().all()
        return random.choice(questions) if questions else None


async def get_next_question_for_user(telegram_id: int) -> Question:
    async with async_session() as session:
        result = await session.execute(select(Question))
        questions = result.scalars().all()
        return random.choice(questions) if questions else None


async def start_dtm_test_for_user(telegram_id: int, year: int = 2025) -> Question:
    """Начинает официальный 10-вопросный тест УзБМБ (Шаг 1 - Раздел 1) стандарта заданного года"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.test_mode = f"dtm_{year}"
            user.dtm_step = 1
            user.dtm_correct = 0
            await session.commit()
        
        q_result = await session.execute(select(Question).where(Question.section_id == 1, Question.year == year))
        questions = q_result.scalars().all()
        if not questions:
            q_result = await session.execute(select(Question).where(Question.section_id == 1))
            questions = q_result.scalars().all()
            
        question = random.choice(questions) if questions else None
        if user and question:
            user.current_question_id = question.id
            await session.commit()
            
        return question


async def next_dtm_question_for_user(telegram_id: int) -> tuple[User, Question]:
    """Переходит к следующему шагу (раздели 2..10) теста УзБМБ"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return None, None
        
        if user.dtm_step < 10:
            user.dtm_step += 1
        
        step = user.dtm_step
        mode = user.test_mode
        year = 2024 if "2024" in mode else 2025
        await session.commit()
        
        q_result = await session.execute(select(Question).where(Question.section_id == step, Question.year == year))
        questions = q_result.scalars().all()
        if not questions:
            q_result = await session.execute(select(Question).where(Question.section_id == step))
            questions = q_result.scalars().all()
            
        question = random.choice(questions) if questions else None
        if question:
            user.current_question_id = question.id
            await session.commit()
            
        return user, question


async def get_question_by_section(telegram_id: int, section_id: int) -> Question:
    """Выбрать случайный вопрос по разделу (1-10)"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.test_mode = f"sec_{section_id}"
            await session.commit()
            
        q_result = await session.execute(select(Question).where(Question.section_id == section_id))
        questions = q_result.scalars().all()
        question = random.choice(questions) if questions else None
        
        if user and question:
            user.current_question_id = question.id
            await session.commit()
            
        return question


async def get_question_by_subtopic(telegram_id: int, subtopic_id: str) -> Question:
    """Выбрать случайный вопрос по конкретной подтеме"""
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.test_mode = f"sub_{subtopic_id}"
            await session.commit()
            
        q_result = await session.execute(select(Question).where(Question.subtopic_id == subtopic_id))
        questions = q_result.scalars().all()
        if not questions:
            sec_id = int(subtopic_id.split('.')[0])
            q_result = await session.execute(select(Question).where(Question.section_id == sec_id))
            questions = q_result.scalars().all()
            
        question = random.choice(questions) if questions else None
        if user and question:
            user.current_question_id = question.id
            await session.commit()
            
        return question


async def record_dtm_answer(telegram_id: int, is_correct: bool) -> User:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user and user.test_mode.startswith("dtm_") and is_correct:
            user.dtm_correct += 1
            await session.commit()
            await session.refresh(user)
        return user
