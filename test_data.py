"""
Add test data to database for testing
"""
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from src.database.models import Company, Category
from src.database.db import get_db_session


def add_test_companies():
    """Add test companies to database"""
    with get_db_session() as session:
        # Get categories
        categories = {cat.name: cat for cat in session.query(Category).all()}

        test_companies = [
            {
                'name': 'AutoService Premium',
                'category': categories['auto_service'],
                'address': 'ул. Ленина 10, Минск',
                'city': 'Минск',
                'district': 'Центральный',
                'phone': '+375 29 123-45-67',
                'email': 'info@autoservice.by',
                'website': 'https://autoservice.by',
                'instagram': '@autoservice_premium',
                'rating': 4.8,
                'reviews_count': 125,
                'latitude': 53.9045,
                'longitude': 27.5615,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Мастер на час "Умелые руки"',
                'category': categories['handyman'],
                'address': 'пр. Независимости 45, Минск',
                'city': 'Минск',
                'phone': '+375 29 234-56-78',
                'instagram': '@umelyie_ruki',
                'rating': 4.5,
                'reviews_count': 87,
                'latitude': 53.9168,
                'longitude': 27.5909,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Клининг "Чистый дом"',
                'category': categories['cleaning'],
                'address': 'ул. Я. Коласа 23, Гомель',
                'city': 'Гомель',
                'district': 'Центральный',
                'phone': '+375 29 345-67-89',
                'email': 'clean@chistydom.by',
                'website': 'https://chistydom.by',
                'rating': 4.9,
                'reviews_count': 203,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Грузоперевозки "Быстрый переезд"',
                'category': categories['moving'],
                'address': 'ул. Московская 128, Брест',
                'city': 'Брест',
                'phone': '+375 29 456-78-90',
                'email': 'info@bistro-pereezd.by',
                'telegram': '@bistro_pereezd',
                'rating': 4.6,
                'reviews_count': 156,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Репетиторский центр "Знание"',
                'category': categories['education'],
                'address': 'ул. Советская 34, Гродно',
                'city': 'Гродно',
                'phone': '+375 29 567-89-01',
                'email': 'info@znaniye-grodno.by',
                'website': 'https://znaniye-grodno.by',
                'facebook': 'znaniye.grodno',
                'rating': 4.7,
                'reviews_count': 92,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Фитнес-клуб "Энергия"',
                'category': categories['fitness'],
                'address': 'пр. Ленина 15, Витебск',
                'city': 'Витебск',
                'phone': '+375 29 678-90-12',
                'email': 'info@energiya-fit.by',
                'website': 'https://energiya-fit.by',
                'instagram': '@energiya_fitness',
                'rating': 4.8,
                'reviews_count': 241,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Фотостудия "Момент"',
                'category': categories['photo_video'],
                'address': 'ул. Гагарина 67, Могилев',
                'city': 'Могилев',
                'phone': '+375 29 789-01-23',
                'email': 'photo@moment.by',
                'instagram': '@moment_studio',
                'rating': 4.9,
                'reviews_count': 178,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Юридическая компания "Правовед"',
                'category': categories['legal'],
                'address': 'ул. Кирова 12, Минск',
                'city': 'Минск',
                'phone': '+375 29 890-12-34',
                'email': 'info@pravoved.by',
                'website': 'https://pravoved.by',
                'rating': 4.6,
                'reviews_count': 134,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Психологический центр "Гармония"',
                'category': categories['psychology'],
                'address': 'ул. Фрунзе 89, Минск',
                'city': 'Минск',
                'phone': '+375 29 901-23-45',
                'email': 'info@garmonia-psy.by',
                'website': 'https://garmonia-psy.by',
                'instagram': '@garmonia_psy',
                'rating': 5.0,
                'reviews_count': 67,
                'source': 'test_data',
                'is_active': True
            },
            {
                'name': 'Тату-салон "Ink Masters"',
                'category': categories['tattoo'],
                'address': 'ул. Немига 45, Минск',
                'city': 'Минск',
                'phone': '+375 29 012-34-56',
                'email': 'ink@masters.by',
                'instagram': '@ink_masters_minsk',
                'rating': 4.7,
                'reviews_count': 198,
                'source': 'test_data',
                'is_active': True
            }
        ]

        for company_data in test_companies:
            company = Company(**company_data)
            session.add(company)

        session.commit()
        print(f"✅ Added {len(test_companies)} test companies")

        # Show summary
        for cat_name, cat in categories.items():
            count = session.query(Company).filter(Company.category_id == cat.id).count()
            print(f"  {cat.name_ru}: {count} компаний")


if __name__ == '__main__':
    print("Adding test data...")
    add_test_companies()
    print("Done!")
