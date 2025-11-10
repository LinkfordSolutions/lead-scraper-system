"""
Database connection and utilities
"""
import os
from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv

from .models import Base, Category

# Load environment variables
load_dotenv()

# Database connection
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://lead_scraper:lead_scraper_pass_2025@localhost:5432/lead_scraper_db')

# Create engine
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # Verify connections before using
    echo=False  # Set to True for SQL debugging
)

# Session factory
session_factory = sessionmaker(bind=engine)
Session = scoped_session(session_factory)


@contextmanager
def get_db_session():
    """
    Provide a transactional scope around a series of operations.

    Usage:
        with get_db_session() as session:
            user = session.query(User).first()
    """
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_database():
    """
    Initialize database: create all tables and seed initial data
    """
    # Create all tables
    Base.metadata.create_all(engine)
    print("✅ Database tables created")

    # Seed categories
    seed_categories()


def seed_categories():
    """
    Seed initial category data
    """
    with get_db_session() as session:
        # Check if categories already exist
        if session.query(Category).count() > 0:
            print("⚠️  Categories already exist, skipping seeding")
            return

        categories_data = [
            {
                'name': 'auto_service',
                'name_ru': 'СТО/детейлинг/шиномонтаж',
                'keywords': [
                    'сто', 'автосервис', 'детейлинг', 'шиномонтаж', 'автомойка',
                    'ремонт авто', 'техосмотр', 'диагностика авто', 'замена масла',
                    'автосервіс', 'аўтасэрвіс', 'шынамантаж'
                ]
            },
            {
                'name': 'handyman',
                'name_ru': 'Мастер на час / электрик / сантехник',
                'keywords': [
                    'мастер на час', 'электрик', 'сантехник', 'муж на час',
                    'ремонт бытовой техники', 'сборка мебели', 'бытовой ремонт',
                    'электромонтаж', 'сантехработы', 'майстар', 'электрык', 'сантэхнік'
                ]
            },
            {
                'name': 'cleaning',
                'name_ru': 'Клининговые услуги',
                'keywords': [
                    'клининг', 'уборка', 'химчистка', 'мойка окон',
                    'генеральная уборка', 'уборка квартир', 'клининговые услуги',
                    'чистка мебели', 'прибирання', 'прыбіранне'
                ]
            },
            {
                'name': 'moving',
                'name_ru': 'Грузоперевозки/переезды',
                'keywords': [
                    'грузоперевозки', 'переезд', 'грузчики', 'грузовое такси',
                    'транспортные услуги', 'доставка', 'перевозка мебели',
                    'квартирный переезд', 'офисный переезд', 'пераезд', 'грузаперавозкі'
                ]
            },
            {
                'name': 'education',
                'name_ru': 'Учителя/репетиторы/курсы',
                'keywords': [
                    'репетитор', 'курсы', 'обучение', 'учитель', 'преподаватель',
                    'языковые курсы', 'подготовка к экзаменам', 'онлайн обучение',
                    'математика', 'английский', 'рэпетытар', 'курси'
                ]
            },
            {
                'name': 'fitness',
                'name_ru': 'Фитнес/йога/танцы/ЕМС-студии',
                'keywords': [
                    'фитнес', 'йога', 'танцы', 'ems', 'спортзал', 'тренажерный зал',
                    'фитнес клуб', 'персональный тренер', 'групповые занятия',
                    'пилатес', 'зумба', 'фітнес', 'йога-студыя'
                ]
            },
            {
                'name': 'photo_video',
                'name_ru': 'Фото/видео-студии, фотографы',
                'keywords': [
                    'фотограф', 'фотостудия', 'видеосъемка', 'видеограф',
                    'свадебная фотосъемка', 'детская фотосессия', 'студийная фотосъемка',
                    'видеомонтаж', 'фотосессия', 'фатаграф', 'фотасэсія'
                ]
            },
            {
                'name': 'legal',
                'name_ru': 'Нотариус/юристы/консалтинг',
                'keywords': [
                    'нотариус', 'юрист', 'адвокат', 'юридические услуги',
                    'консалтинг', 'правовая помощь', 'юридическая консультация',
                    'нотариальные услуги', 'бухгалтерские услуги', 'натарыус', 'юрыст'
                ]
            },
            {
                'name': 'psychology',
                'name_ru': 'Психологи/коучи',
                'keywords': [
                    'психолог', 'психотерапевт', 'коуч', 'психологическая помощь',
                    'консультация психолога', 'семейный психолог', 'детский психолог',
                    'онлайн психолог', 'коучинг', 'псіхолаг', 'псіхатэрапеўт'
                ]
            },
            {
                'name': 'tattoo',
                'name_ru': 'Тату/перманент/пирсинг',
                'keywords': [
                    'тату', 'татуировка', 'тату салон', 'пирсинг', 'перманентный макияж',
                    'татуаж', 'микроблейдинг', 'удаление тату', 'художественная татуировка',
                    'татуіроўка', 'пірсінг', 'перманентны макіяж'
                ]
            }
        ]

        for cat_data in categories_data:
            category = Category(**cat_data)
            session.add(category)

        session.commit()
        print(f"✅ Seeded {len(categories_data)} categories")


def drop_all_tables():
    """
    Drop all tables (use with caution!)
    """
    Base.metadata.drop_all(engine)
    print("⚠️  All tables dropped")


def reset_database():
    """
    Reset database: drop and recreate all tables
    """
    drop_all_tables()
    init_database()
    print("✅ Database reset complete")


if __name__ == '__main__':
    # Initialize database when run directly
    print("Initializing database...")
    init_database()
    print("Done!")
