"""
Instagram parser - Business accounts search
"""
import aiohttp
import asyncio
import logging
import json
import re
from typing import List, Dict, Optional
from .base import BaseParser

logger = logging.getLogger(__name__)


class InstagramParser(BaseParser):
    """Parser for Instagram business accounts"""

    # Category to hashtag mappings
    CATEGORY_HASHTAGS = {
        'auto_service': ['автосервисминск', 'автосервисбеларусь', 'автомойкаминск', 'детейлингминск'],
        'handyman': ['мастернадомминск', 'ремонтминск', 'мастернадомбеларусь'],
        'cleaning': ['клинингминск', 'уборкаминск', 'клинингбеларусь'],
        'moving': ['грузоперевозкиминск', 'переездминск', 'грузоперевозкибеларусь'],
        'education': ['репетиторминск', 'курсыминск', 'репетиторбеларусь'],
        'fitness': ['фитнесминск', 'спортминск', 'тренерминск'],
        'photo_video': ['фотографминск', 'фотографбеларусь', 'видеографминск'],
        'legal': ['юристминск', 'юристбеларусь', 'адвокатминск'],
        'psychology': ['психологминск', 'психологбеларусь', 'психотерапевтминск'],
        'tattoo': ['татуминск', 'татубеларусь', 'tattoominsk']
    }

    # Belarus cities for location search
    BELARUS_CITIES = [
        'Минск', 'Гомель', 'Могилев', 'Витебск', 'Гродно', 'Брест',
        'Бобруйск', 'Барановичи', 'Борисов', 'Пинск'
    ]

    def __init__(self, session_id: Optional[str] = None):
        """
        Initialize Instagram parser

        Args:
            session_id: Instagram session ID (optional, for authenticated requests)
        """
        super().__init__('instagram')
        self.session_id = session_id
        self.base_url = 'https://www.instagram.com'
        self.session = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session"""
        if self.session is None or self.session.closed:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml',
                'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
                'X-Requested-With': 'XMLHttpRequest'
            }

            if self.session_id:
                headers['Cookie'] = f'sessionid={self.session_id}'

            self.session = aiohttp.ClientSession(headers=headers)
        return self.session

    async def close(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()

    async def search_by_category(
        self,
        category: str,
        city: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """
        Search Instagram accounts by category

        Args:
            category: Category name
            city: City name (optional)
            limit: Maximum number of results

        Returns:
            List of business account dictionaries
        """
        results = []

        # Get hashtags for category
        hashtags = self.CATEGORY_HASHTAGS.get(category, [])

        # Search each hashtag
        for hashtag in hashtags:
            try:
                accounts = await self._search_hashtag(hashtag, limit // len(hashtags))
                results.extend(accounts)
                self.stats['total_found'] += len(accounts)

                # Rate limiting (Instagram is strict!)
                await asyncio.sleep(3.0)

            except Exception as e:
                self.log_error(f"Search error for hashtag '#{hashtag}': {e}")

        # Filter by city if specified
        if city and results:
            results = [r for r in results if self._matches_city(r, city)]

        logger.info(f"[Instagram] Found {len(results)} accounts for category '{category}'")
        return results

    async def _search_hashtag(
        self,
        hashtag: str,
        limit: int = 50
    ) -> List[Dict]:
        """
        Search accounts by hashtag

        Args:
            hashtag: Hashtag to search (without #)
            limit: Max results

        Returns:
            List of accounts
        """
        accounts = []
        session = await self._get_session()

        # Clean hashtag
        hashtag = hashtag.replace('#', '').strip()

        url = f"{self.base_url}/explore/tags/{hashtag}/"

        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    html = await response.text()

                    # Extract JSON data from page
                    json_data = self._extract_json_data(html)

                    if json_data:
                        # Parse posts from hashtag
                        posts = self._extract_posts_from_json(json_data)

                        # Extract unique accounts from posts
                        seen_usernames = set()

                        for post in posts[:limit]:
                            try:
                                account = self._parse_post_account(post)
                                if account and account['username'] not in seen_usernames:
                                    accounts.append(account)
                                    seen_usernames.add(account['username'])
                                    self.stats['successful'] += 1

                                    if len(accounts) >= limit:
                                        break

                            except Exception as e:
                                self.log_error(f"Parse post error: {e}")
                                self.stats['failed'] += 1

                elif response.status == 429:
                    logger.warning("[Instagram] Rate limited")
                    await asyncio.sleep(10)
                else:
                    logger.warning(f"[Instagram] Page returned status {response.status}")

        except asyncio.TimeoutError:
            logger.warning(f"[Instagram] Request timeout for #{hashtag}")
        except Exception as e:
            logger.error(f"[Instagram] Request error: {e}")

        return accounts

    def _extract_json_data(self, html: str) -> Optional[Dict]:
        """Extract JSON data from Instagram page HTML"""
        try:
            # Instagram embeds data in script tags
            pattern = r'window\._sharedData\s*=\s*({.+?});'
            match = re.search(pattern, html)

            if match:
                json_str = match.group(1)
                return json.loads(json_str)

        except Exception as e:
            logger.error(f"[Instagram] JSON extraction error: {e}")

        return None

    def _extract_posts_from_json(self, data: Dict) -> List[Dict]:
        """Extract posts from Instagram JSON data"""
        posts = []

        try:
            # Navigate through Instagram's data structure
            entry_data = data.get('entry_data', {})
            tag_page = entry_data.get('TagPage', [{}])[0]
            graphql = tag_page.get('graphql', {})
            hashtag = graphql.get('hashtag', {})
            edge_hashtag_to_media = hashtag.get('edge_hashtag_to_media', {})
            edges = edge_hashtag_to_media.get('edges', [])

            for edge in edges:
                node = edge.get('node', {})
                if node:
                    posts.append(node)

        except Exception as e:
            logger.error(f"[Instagram] Posts extraction error: {e}")

        return posts

    def _parse_post_account(self, post: Dict) -> Optional[Dict]:
        """
        Parse account info from post

        Args:
            post: Post node from Instagram JSON

        Returns:
            Account dictionary
        """
        try:
            # Get account owner
            owner = post.get('owner', {})
            username = owner.get('username', '').strip()

            if not username:
                return None

            # Get post caption (may contain contact info)
            caption_edges = post.get('edge_media_to_caption', {}).get('edges', [])
            caption = ''
            if caption_edges:
                caption = caption_edges[0].get('node', {}).get('text', '')

            # Try to extract phone from caption
            phone = self._extract_phone(caption)

            # Build profile URL
            profile_url = f"{self.base_url}/{username}/"

            # Build account dict
            account = {
                'name': username,
                'username': username,
                'instagram': profile_url,
                'phone': phone,
                'bio': caption[:200] if caption else None,  # First 200 chars
                'source': self.source_name,
                'raw_data': {
                    'username': username,
                    'profile_url': profile_url,
                    'post_caption': caption
                }
            }

            return account

        except Exception as e:
            logger.error(f"[Instagram] Parse account error: {e}")
            return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract Belarus phone number from text"""
        if not text:
            return None

        # Belarus phone patterns
        patterns = [
            r'\+375\s?\(?\d{2}\)?\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'80\d{2}\s?\d{3}[-\s]?\d{2}[-\s]?\d{2}',
            r'\d{2}[-\s]?\d{3}[-\s]?\d{2}[-\s]?\d{2}'
        ]

        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                phone = match.group(0)
                return self.normalize_phone(phone)

        return None

    def _matches_city(self, account: Dict, city: str) -> bool:
        """Check if account is from specified city"""
        city_lower = city.lower()

        # Check in username
        username = account.get('username', '').lower()
        if city_lower in username:
            return True

        # Check in bio
        bio = account.get('bio', '')
        if bio and city_lower in bio.lower():
            return True

        return False

    async def get_company_details(self, company_id: str) -> Optional[Dict]:
        """
        Get account details by username

        Args:
            company_id: Instagram username

        Returns:
            Account details or None
        """
        session = await self._get_session()

        username = company_id.replace('@', '').strip()
        url = f"{self.base_url}/{username}/?__a=1"

        try:
            async with session.get(url, timeout=30) as response:
                if response.status == 200:
                    data = await response.json()

                    # Extract account info
                    graphql = data.get('graphql', {})
                    user = graphql.get('user', {})

                    full_name = user.get('full_name', '')
                    biography = user.get('biography', '')
                    website = user.get('external_url', '')

                    phone = self._extract_phone(biography)

                    return {
                        'name': full_name or username,
                        'username': username,
                        'bio': biography,
                        'website': website,
                        'phone': phone,
                        'instagram': f"{self.base_url}/{username}/",
                        'source': self.source_name
                    }

        except Exception as e:
            logger.error(f"[Instagram] Get details error: {e}")

        return None
