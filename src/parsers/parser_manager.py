"""
Parser manager - coordinates all parsers and saves data to database
"""
import asyncio
import logging
from typing import List, Dict, Optional
from datetime import datetime
import hashlib

from ..database.models import Company, Category, ScrapeSession, ScrapeResult
from ..database.db import get_db_session
from ..utils.config import config

logger = logging.getLogger(__name__)


class ParserManager:
    """Manages all parsers and database integration"""

    def __init__(self):
        """Initialize parser manager"""
        self.parsers = []
        self.session_id = None

    def register_parser(self, parser):
        """Register a parser"""
        self.parsers.append(parser)
        logger.info(f"Registered parser: {parser.source_name}")

    async def run_all_parsers(self, categories: Optional[List[str]] = None):
        """
        Run all registered parsers

        Args:
            categories: List of category names to scrape (None = all)
        """
        if not categories:
            categories = config.get_enabled_niches()

        logger.info(f"Starting scraping for {len(categories)} categories")

        # Create scraping session
        session_id = self._create_scrape_session('all_sources')

        try:
            for parser in self.parsers:
                await self._run_parser(parser, categories, session_id)

            # Mark session as completed
            self._complete_scrape_session(session_id, 'completed')

        except Exception as e:
            logger.error(f"Scraping error: {e}", exc_info=True)
            self._complete_scrape_session(session_id, 'failed', str(e))

    async def _run_parser(
        self,
        parser,
        categories: List[str],
        session_id: int
    ):
        """
        Run single parser for all categories

        Args:
            parser: Parser instance
            categories: List of categories
            session_id: Scrape session ID
        """
        logger.info(f"Running parser: {parser.source_name}")

        for category in categories:
            try:
                logger.info(f"Scraping category: {category}")

                # Search companies
                companies = await parser.search_by_category(category, limit=100)

                # Save to database
                for company_data in companies:
                    self._save_company(company_data, category, session_id)

                logger.info(
                    f"[{parser.source_name}] Category '{category}': "
                    f"found {len(companies)} companies"
                )

            except Exception as e:
                logger.error(
                    f"Error scraping category '{category}' "
                    f"with {parser.source_name}: {e}"
                )

    def _create_scrape_session(self, source: str) -> int:
        """
        Create a new scraping session

        Args:
            source: Source name

        Returns:
            Session ID
        """
        with get_db_session() as session:
            scrape_session = ScrapeSession(
                source=source,
                status='started',
                started_at=datetime.utcnow()
            )
            session.add(scrape_session)
            session.commit()

            logger.info(f"Created scrape session: {scrape_session.id}")
            return scrape_session.id

    def _complete_scrape_session(
        self,
        session_id: int,
        status: str,
        error_message: Optional[str] = None
    ):
        """
        Mark scraping session as completed

        Args:
            session_id: Session ID
            status: Status ('completed' or 'failed')
            error_message: Error message if failed
        """
        with get_db_session() as session:
            scrape_session = session.query(ScrapeSession).get(session_id)

            if scrape_session:
                scrape_session.status = status
                scrape_session.completed_at = datetime.utcnow()
                scrape_session.error_message = error_message

                # Calculate duration
                if scrape_session.started_at and scrape_session.completed_at:
                    duration = scrape_session.completed_at - scrape_session.started_at
                    scrape_session.duration_seconds = int(duration.total_seconds())

                session.commit()
                logger.info(f"Scrape session {session_id} marked as {status}")

    def _save_company(
        self,
        company_data: Dict,
        category_name: str,
        session_id: int
    ):
        """
        Save company to database

        Args:
            company_data: Company data dictionary
            category_name: Category name
            session_id: Scrape session ID
        """
        with get_db_session() as session:
            # Get category
            category = session.query(Category).filter(
                Category.name == category_name
            ).first()

            if not category:
                logger.warning(f"Category not found: {category_name}")
                return

            # Check if company already exists
            dedup_hash = self._generate_dedup_hash(company_data)

            existing = session.query(Company).filter(
                Company.dedup_hash == dedup_hash
            ).first()

            action = 'skipped'

            if existing:
                # Update existing company
                self._update_company(existing, company_data)
                company_id = existing.id
                action = 'updated'

            else:
                # Create new company
                company = Company(
                    name=company_data.get('name'),
                    address=company_data.get('address'),
                    phone=company_data.get('phone'),
                    email=company_data.get('email'),
                    website=company_data.get('website'),
                    instagram=company_data.get('instagram'),
                    facebook=company_data.get('facebook'),
                    vk=company_data.get('vk'),
                    telegram=company_data.get('telegram'),
                    category_id=category.id,
                    city=company_data.get('city'),
                    district=company_data.get('district'),
                    latitude=company_data.get('latitude'),
                    longitude=company_data.get('longitude'),
                    rating=company_data.get('rating'),
                    reviews_count=company_data.get('reviews_count', 0),
                    source=company_data.get('source'),
                    source_id=company_data.get('source_id'),
                    source_url=company_data.get('source_url'),
                    raw_data=company_data.get('raw_data'),
                    dedup_hash=dedup_hash,
                    last_scraped_at=datetime.utcnow(),
                    is_active=True
                )

                session.add(company)
                session.flush()
                company_id = company.id
                action = 'created'

            # Create scrape result record
            scrape_result = ScrapeResult(
                session_id=session_id,
                company_id=company_id,
                action=action
            )
            session.add(scrape_result)

            # Update session statistics
            scrape_session = session.query(ScrapeSession).get(session_id)
            if scrape_session:
                scrape_session.total_scraped += 1
                if action == 'created':
                    scrape_session.new_companies += 1
                elif action == 'updated':
                    scrape_session.updated_companies += 1

            session.commit()

    def _generate_dedup_hash(self, company_data: Dict) -> str:
        """
        Generate deduplication hash for company

        Args:
            company_data: Company data

        Returns:
            MD5 hash
        """
        # Use phone or name+address for deduplication
        key_parts = []

        if company_data.get('phone'):
            key_parts.append(company_data['phone'])
        else:
            if company_data.get('name'):
                key_parts.append(company_data['name'].lower().strip())
            if company_data.get('address'):
                key_parts.append(company_data['address'].lower().strip())

        if not key_parts:
            # Fallback to source ID
            key_parts.append(company_data.get('source', ''))
            key_parts.append(company_data.get('source_id', ''))

        key = '|'.join(key_parts)
        return hashlib.md5(key.encode()).hexdigest()

    def _update_company(self, company: Company, new_data: Dict):
        """
        Update existing company with new data

        Args:
            company: Existing company
            new_data: New company data
        """
        # Update fields if new data is more complete
        if new_data.get('phone') and not company.phone:
            company.phone = new_data['phone']

        if new_data.get('email') and not company.email:
            company.email = new_data['email']

        if new_data.get('website') and not company.website:
            company.website = new_data['website']

        if new_data.get('instagram') and not company.instagram:
            company.instagram = new_data['instagram']

        if new_data.get('rating'):
            company.rating = new_data['rating']

        if new_data.get('reviews_count'):
            company.reviews_count = new_data['reviews_count']

        company.last_scraped_at = datetime.utcnow()
        company.updated_at = datetime.utcnow()


# Global parser manager instance
parser_manager = ParserManager()
