"""
Statistics and search functionality
"""
from typing import Optional, List, Dict
from sqlalchemy import func, or_
from ..database.models import Company, Category, ScrapeSession, ScrapeResult
from ..database.db import get_db_session


class Stats:
    """Statistics functionality"""

    @staticmethod
    def get_database_stats() -> Dict:
        """
        Get overall database statistics

        Returns:
            dict: Statistics
        """
        with get_db_session() as session:
            # Total companies
            total_companies = session.query(Company).filter(Company.is_active == True).count()

            # Companies by category
            by_category = session.query(
                Category.name_ru,
                func.count(Company.id)
            ).join(Company).filter(
                Company.is_active == True
            ).group_by(Category.name_ru).all()

            # Companies by source
            by_source = session.query(
                Company.source,
                func.count(Company.id)
            ).filter(
                Company.is_active == True
            ).group_by(Company.source).all()

            # Companies by city (top 10)
            by_city = session.query(
                Company.city,
                func.count(Company.id)
            ).filter(
                Company.is_active == True,
                Company.city.isnot(None)
            ).group_by(Company.city).order_by(
                func.count(Company.id).desc()
            ).limit(10).all()

            # Companies with contacts
            with_phone = session.query(Company).filter(
                Company.is_active == True,
                Company.phone.isnot(None)
            ).count()

            with_email = session.query(Company).filter(
                Company.is_active == True,
                Company.email.isnot(None)
            ).count()

            with_website = session.query(Company).filter(
                Company.is_active == True,
                Company.website.isnot(None)
            ).count()

            with_instagram = session.query(Company).filter(
                Company.is_active == True,
                Company.instagram.isnot(None)
            ).count()

            # Last scrape session
            last_session = session.query(ScrapeSession).order_by(
                ScrapeSession.started_at.desc()
            ).first()

            last_scrape_info = None
            if last_session:
                last_scrape_info = {
                    'started_at': last_session.started_at,
                    'finished_at': last_session.finished_at,
                    'total_found': last_session.total_found,
                    'new_added': last_session.new_added,
                    'updated': last_session.updated,
                    'status': last_session.status
                }

            return {
                'total_companies': total_companies,
                'by_category': dict(by_category),
                'by_source': dict(by_source),
                'by_city': dict(by_city),
                'contacts': {
                    'with_phone': with_phone,
                    'with_email': with_email,
                    'with_website': with_website,
                    'with_instagram': with_instagram
                },
                'last_scrape': last_scrape_info
            }

    @staticmethod
    def search_companies(
        query: str,
        limit: int = 20
    ) -> List[Company]:
        """
        Search companies by name, phone, or address

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            List of companies
        """
        with get_db_session() as session:
            search_pattern = f'%{query}%'

            companies = session.query(Company).filter(
                Company.is_active == True,
                or_(
                    Company.name.ilike(search_pattern),
                    Company.phone.ilike(search_pattern),
                    Company.address.ilike(search_pattern),
                    Company.city.ilike(search_pattern)
                )
            ).limit(limit).all()

            return companies

    @staticmethod
    def format_stats_message(stats: Dict) -> str:
        """
        Format statistics as Telegram message

        Args:
            stats: Statistics dictionary

        Returns:
            Formatted message
        """
        msg = "📊 **Статистика базы данных**\n\n"

        # Total
        msg += f"📈 **Всего компаний:** {stats['total_companies']}\n\n"

        # By category
        if stats['by_category']:
            msg += "**По категориям:**\n"
            for cat, count in sorted(stats['by_category'].items(), key=lambda x: x[1], reverse=True):
                msg += f"  • {cat}: {count}\n"
            msg += "\n"

        # By source
        if stats['by_source']:
            msg += "**По источникам:**\n"
            for source, count in sorted(stats['by_source'].items(), key=lambda x: x[1], reverse=True):
                msg += f"  • {source or 'Неизвестно'}: {count}\n"
            msg += "\n"

        # By city (top 10)
        if stats['by_city']:
            msg += "**Топ-10 городов:**\n"
            for city, count in stats['by_city']:
                msg += f"  • {city}: {count}\n"
            msg += "\n"

        # Contacts
        if stats['contacts']:
            contacts = stats['contacts']
            total = stats['total_companies']
            msg += "**Наличие контактов:**\n"
            msg += f"  📞 Телефон: {contacts['with_phone']} ({contacts['with_phone']/total*100:.1f}%)\n"
            msg += f"  📧 Email: {contacts['with_email']} ({contacts['with_email']/total*100:.1f}%)\n"
            msg += f"  🌐 Сайт: {contacts['with_website']} ({contacts['with_website']/total*100:.1f}%)\n"
            msg += f"  📸 Instagram: {contacts['with_instagram']} ({contacts['with_instagram']/total*100:.1f}%)\n"
            msg += "\n"

        # Last scrape
        if stats['last_scrape']:
            scrape = stats['last_scrape']
            msg += "**Последний парсинг:**\n"
            msg += f"  🕐 Дата: {scrape['started_at'].strftime('%Y-%m-%d %H:%M')}\n"
            msg += f"  ✅ Найдено: {scrape['total_found']}\n"
            msg += f"  ➕ Добавлено: {scrape['new_added']}\n"
            msg += f"  🔄 Обновлено: {scrape['updated']}\n"
            msg += f"  📊 Статус: {scrape['status']}\n"

        return msg

    @staticmethod
    def format_search_results(companies: List[Company]) -> str:
        """
        Format search results as Telegram message

        Args:
            companies: List of companies

        Returns:
            Formatted message
        """
        if not companies:
            return "❌ Ничего не найдено"

        msg = f"🔍 **Найдено компаний: {len(companies)}**\n\n"

        for i, company in enumerate(companies, 1):
            msg += f"**{i}. {company.name}**\n"

            if company.category:
                msg += f"   📂 {company.category.name_ru}\n"

            if company.phone:
                msg += f"   📞 {company.phone}\n"

            if company.address:
                address = company.address[:60] + "..." if len(company.address) > 60 else company.address
                msg += f"   📍 {address}\n"

            if company.website:
                msg += f"   🌐 {company.website}\n"

            msg += "\n"

        return msg


# Singleton instance
stats = Stats()
