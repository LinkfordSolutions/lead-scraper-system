"""
Database models for Lead Scraper System
"""
from datetime import datetime
from sqlalchemy import (
    Column, Integer, BigInteger, String, Float, DateTime, Boolean,
    Text, JSON, ForeignKey, Index, UniqueConstraint
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Category(Base):
    """Business categories/niches"""
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False)
    name_ru = Column(String(255), nullable=False)
    keywords = Column(JSON)  # List of keywords for classification
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    companies = relationship("Company", back_populates="category")

    def __repr__(self):
        return f"<Category(id={self.id}, name='{self.name}')>"


class Company(Base):
    """Company/business information"""
    __tablename__ = 'companies'

    id = Column(Integer, primary_key=True)

    # Basic Information
    name = Column(String(500), nullable=False)
    address = Column(String(1000))
    phone = Column(String(255))
    email = Column(String(255))
    website = Column(String(500))

    # Social Media
    instagram = Column(String(255))
    facebook = Column(String(255))
    vk = Column(String(255))
    telegram = Column(String(255))

    # Category
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship("Category", back_populates="companies")

    # Geographic Data
    city = Column(String(255))
    district = Column(String(255))
    latitude = Column(Float)
    longitude = Column(Float)

    # Analytics
    rating = Column(Float)
    reviews_count = Column(Integer, default=0)
    has_photos = Column(Boolean, default=False)

    # Source Data
    source = Column(String(50))  # yandex_maps, 2gis, instagram, etc.
    source_id = Column(String(255))  # ID from source
    source_url = Column(String(1000))
    raw_data = Column(JSON)  # Full raw data from source

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_scraped_at = Column(DateTime)
    is_active = Column(Boolean, default=True)

    # Deduplication hash
    dedup_hash = Column(String(64))  # MD5/SHA hash for deduplication

    # Relationships
    scrape_results = relationship("ScrapeResult", back_populates="company")

    __table_args__ = (
        Index('idx_company_name', 'name'),
        Index('idx_company_phone', 'phone'),
        Index('idx_company_category', 'category_id'),
        Index('idx_company_city', 'city'),
        Index('idx_company_source', 'source'),
        Index('idx_company_dedup', 'dedup_hash'),
    )

    def __repr__(self):
        return f"<Company(id={self.id}, name='{self.name}', category={self.category})>"


class ScrapeSession(Base):
    """Scraping session information"""
    __tablename__ = 'scrape_sessions'

    id = Column(Integer, primary_key=True)

    source = Column(String(50), nullable=False)
    status = Column(String(50), default='started')  # started, completed, failed

    # Statistics
    total_scraped = Column(Integer, default=0)
    new_companies = Column(Integer, default=0)
    updated_companies = Column(Integer, default=0)
    errors_count = Column(Integer, default=0)

    # Timing
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    duration_seconds = Column(Integer)

    # Error info
    error_message = Column(Text)

    # Metadata
    config = Column(JSON)  # Configuration used for this session

    # Relationships
    results = relationship("ScrapeResult", back_populates="session")

    __table_args__ = (
        Index('idx_session_source', 'source'),
        Index('idx_session_status', 'status'),
        Index('idx_session_started', 'started_at'),
    )

    def __repr__(self):
        return f"<ScrapeSession(id={self.id}, source='{self.source}', status='{self.status}')>"


class ScrapeResult(Base):
    """Individual scrape results linking sessions to companies"""
    __tablename__ = 'scrape_results'

    id = Column(Integer, primary_key=True)

    session_id = Column(Integer, ForeignKey('scrape_sessions.id'), nullable=False)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)

    action = Column(String(50))  # created, updated, skipped
    changes = Column(JSON)  # What was changed

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    session = relationship("ScrapeSession", back_populates="results")
    company = relationship("Company", back_populates="scrape_results")

    __table_args__ = (
        Index('idx_result_session', 'session_id'),
        Index('idx_result_company', 'company_id'),
    )

    def __repr__(self):
        return f"<ScrapeResult(id={self.id}, session={self.session_id}, company={self.company_id})>"


class BotUser(Base):
    """Telegram bot users"""
    __tablename__ = 'bot_users'

    id = Column(Integer, primary_key=True)

    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))

    is_authorized = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)

    # Activity tracking
    last_active_at = Column(DateTime)
    requests_count = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_user_telegram_id', 'telegram_id'),
        Index('idx_user_authorized', 'is_authorized'),
    )

    def __repr__(self):
        return f"<BotUser(id={self.id}, telegram_id={self.telegram_id}, username='{self.username}')>"


class ExportLog(Base):
    """CSV export logs"""
    __tablename__ = 'export_logs'

    id = Column(Integer, primary_key=True)

    file_name = Column(String(500), nullable=False)
    file_path = Column(String(1000), nullable=False)
    file_size = Column(Integer)  # bytes

    records_count = Column(Integer, default=0)
    categories_included = Column(JSON)  # List of category IDs

    created_at = Column(DateTime, default=datetime.utcnow)
    sent_to_users = Column(JSON)  # List of telegram user IDs

    __table_args__ = (
        Index('idx_export_created', 'created_at'),
    )

    def __repr__(self):
        return f"<ExportLog(id={self.id}, file='{self.file_name}', records={self.records_count})>"
