"""
CSV export functionality
"""
import os
import csv
from datetime import datetime
from typing import List, Optional
import pandas as pd

from ..database.models import Company, Category, ExportLog
from ..database.db import get_db_session
from ..utils.config import config


class CSVExporter:
    """Export leads to CSV files"""

    @staticmethod
    def export_leads(
        category_ids: Optional[List[int]] = None,
        include_inactive: bool = False
    ) -> tuple[str, dict]:
        """
        Export leads to CSV file

        Args:
            category_ids: Optional list of category IDs to filter
            include_inactive: Whether to include inactive companies

        Returns:
            tuple: (file_path, stats_dict)
        """
        with get_db_session() as session:
            # Build query
            query = session.query(Company).join(Category)

            if category_ids:
                query = query.filter(Company.category_id.in_(category_ids))

            if not include_inactive:
                query = query.filter(Company.is_active == True)

            # Order by category and name
            companies = query.order_by(Category.name, Company.name).all()

            if not companies:
                return None, {'total': 0, 'by_category': {}}

            # Prepare data
            data = []
            for company in companies:
                data.append({
                    'Название': company.name or '',
                    'Категория': company.category.name_ru if company.category else '',
                    'Адрес': company.address or '',
                    'Город': company.city or '',
                    'Район': company.district or '',
                    'Телефон': company.phone or '',
                    'Email': company.email or '',
                    'Сайт': company.website or '',
                    'Instagram': company.instagram or '',
                    'Facebook': company.facebook or '',
                    'VK': company.vk or '',
                    'Telegram': company.telegram or '',
                    'Рейтинг': company.rating if company.rating else '',
                    'Отзывов': company.reviews_count or 0,
                    'Широта': company.latitude if company.latitude else '',
                    'Долгота': company.longitude if company.longitude else '',
                    'Источник': company.source or '',
                    'Дата обновления': company.updated_at.strftime('%Y-%m-%d') if company.updated_at else ''
                })

            # Create pandas DataFrame
            df = pd.DataFrame(data)

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'leads_belarus_{timestamp}.csv'
            output_dir = config.CSV_OUTPUT_DIR

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            file_path = os.path.join(output_dir, filename)

            # Export to CSV
            df.to_csv(
                file_path,
                index=False,
                encoding=config.CSV_ENCODING,
                quoting=csv.QUOTE_ALL
            )

            # Calculate stats
            stats = {
                'total': len(companies),
                'by_category': {}
            }

            for company in companies:
                cat_name = company.category.name_ru if company.category else 'Без категории'
                stats['by_category'][cat_name] = stats['by_category'].get(cat_name, 0) + 1

            # Log export
            file_size = os.path.getsize(file_path)
            export_log = ExportLog(
                file_name=filename,
                file_path=file_path,
                file_size=file_size,
                records_count=len(companies),
                categories_included=category_ids or []
            )
            session.add(export_log)
            session.commit()

            return file_path, stats

    @staticmethod
    def get_latest_export() -> Optional[dict]:
        """
        Get information about the latest export

        Returns:
            dict: Export info or None
        """
        with get_db_session() as session:
            export = session.query(ExportLog).order_by(
                ExportLog.created_at.desc()
            ).first()

            if not export:
                return None

            return {
                'id': export.id,
                'file_name': export.file_name,
                'file_path': export.file_path,
                'file_size': export.file_size,
                'records_count': export.records_count,
                'created_at': export.created_at
            }

    @staticmethod
    def export_leads_excel(
        category_ids: Optional[List[int]] = None,
        include_inactive: bool = False
    ) -> tuple[str, dict]:
        """
        Export leads to Excel file

        Args:
            category_ids: Optional list of category IDs to filter
            include_inactive: Whether to include inactive companies

        Returns:
            tuple: (file_path, stats_dict)
        """
        with get_db_session() as session:
            # Build query (same as CSV export)
            query = session.query(Company).join(Category)

            if category_ids:
                query = query.filter(Company.category_id.in_(category_ids))

            if not include_inactive:
                query = query.filter(Company.is_active == True)

            # Order by category and name
            companies = query.order_by(Category.name, Company.name).all()

            if not companies:
                return None, {'total': 0, 'by_category': {}}

            # Prepare data
            data = []
            for company in companies:
                data.append({
                    'Название': company.name or '',
                    'Категория': company.category.name_ru if company.category else '',
                    'Адрес': company.address or '',
                    'Город': company.city or '',
                    'Район': company.district or '',
                    'Телефон': company.phone or '',
                    'Email': company.email or '',
                    'Сайт': company.website or '',
                    'Instagram': company.instagram or '',
                    'Facebook': company.facebook or '',
                    'VK': company.vk or '',
                    'Telegram': company.telegram or '',
                    'Рейтинг': company.rating if company.rating else '',
                    'Отзывов': company.reviews_count or 0,
                    'Широта': company.latitude if company.latitude else '',
                    'Долгота': company.longitude if company.longitude else '',
                    'Источник': company.source or '',
                    'Дата обновления': company.updated_at.strftime('%Y-%m-%d') if company.updated_at else ''
                })

            # Create pandas DataFrame
            df = pd.DataFrame(data)

            # Generate filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'leads_belarus_{timestamp}.xlsx'
            output_dir = config.CSV_OUTPUT_DIR

            # Ensure output directory exists
            os.makedirs(output_dir, exist_ok=True)

            file_path = os.path.join(output_dir, filename)

            # Export to Excel with formatting
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Лиды')

                # Get the workbook and worksheet
                workbook = writer.book
                worksheet = writer.sheets['Лиды']

                # Auto-adjust column widths
                for column in worksheet.columns:
                    max_length = 0
                    column_letter = column[0].column_letter
                    for cell in column:
                        try:
                            if len(str(cell.value)) > max_length:
                                max_length = len(str(cell.value))
                        except:
                            pass
                    adjusted_width = min(max_length + 2, 50)
                    worksheet.column_dimensions[column_letter].width = adjusted_width

            # Calculate stats
            stats = {
                'total': len(companies),
                'by_category': {}
            }

            for company in companies:
                cat_name = company.category.name_ru if company.category else 'Без категории'
                stats['by_category'][cat_name] = stats['by_category'].get(cat_name, 0) + 1

            # Log export
            file_size = os.path.getsize(file_path)
            export_log = ExportLog(
                file_name=filename,
                file_path=file_path,
                file_size=file_size,
                records_count=len(companies),
                categories_included=category_ids or []
            )
            session.add(export_log)
            session.commit()

            return file_path, stats

    @staticmethod
    def format_file_size(size_bytes: int) -> str:
        """
        Format file size in human-readable format

        Args:
            size_bytes: Size in bytes

        Returns:
            str: Formatted size
        """
        for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} ТБ"


# Create singleton instance
csv_exporter = CSVExporter()
