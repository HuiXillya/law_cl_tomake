from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import re


class LawBank_Crawler(BaseCrawler):
    """Crawler for Law Bank website"""
    DISPLAY_NAME = "法律法源資訊網"
    BASE_URL = "http://www.lawbank.com.tw"
    NEWS_URLS = {
        "legal_news": "https://www.lawbank.com.tw/schedule/News1.htm",  # 法律新聞
        "regulation_news": "https://www.lawbank.com.tw/schedule/News19.htm",  # 法規新訊
        "judicial_news": "https://www.lawbank.com.tw/schedule/News20.htm",  # 判解新訊
        "interpretation_news": "https://www.lawbank.com.tw/schedule/News21.htm",  # 函釋新訊
        "draft_news": "https://www.lawbank.com.tw/schedule/News22.htm"  # 草案新訊
    }
    
    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Law Bank website.

        Args:
            date_filter (str, optional): Target date in YYYY-MM-DD format

        Returns:
            list: List of dicts with 'date', 'title', 'link'
        """
        announcements = []

        try:
            page = await self.browser.new_page()

            # Set user agent
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            # Process each news category
            for category_name, url in self.NEWS_URLS.items():
                try:
                    await page.goto(url)
                    await page.wait_for_load_state('domcontentloaded')

                    # Wait for dynamic content
                    await page.wait_for_timeout(3000)

                    # Get page content
                    content = await page.content()
                    soup = BeautifulSoup(content, 'html.parser')
                    matches = soup.find_all("tbody")[0].find_all('tr')

                    for match in matches:
                        td_list = match.find_all('td')
                        date_str = td_list[0].get_text(strip=True)
                        title = td_list[2].get_text(strip=True)
                        link = td_list[2].find('a')['href'] if td_list[2].find('a') else ''

                        # Convert date if needed (though it appears to already be in YYYY-MM-DD format)
                        date = date_str

                        # Apply date filter if provided
                        if date_filter and date != date_filter:
                            continue

                        # Ensure link is absolute
                        if not link.startswith('http'):
                            link = self.BASE_URL + link

                        announcements.append({
                            'date': date,
                            'title': f"{title}",
                            'link': link
                        })

                except Exception as e:
                    self.logger.error(f"Error fetching {category_name} from Law Bank: {e}")
                    # raise e # Don't raise, continue to next category
                    continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Law Bank announcements: {e}")
            # raise e
        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Law Bank announcement detail page.

        Args:
            link (str): Announcement URL
            attachment_folder (str): Folder for attachments

        Returns:
            dict: {'content': str, 'attachments': list}
        """
        content = ""
        attachments = []

        try:
            page = await self.browser.new_page()

            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            await page.goto(link)
            await page.wait_for_load_state('domcontentloaded')

            # Wait for dynamic content
            await page.wait_for_timeout(2000)

            # Check if this is a direct PDF link
            if link.lower().endswith('.pdf'):
                # If it's a direct PDF link, download it as attachment
                filename = link.split('/')[-1]
                if not filename:
                    filename = "announcement.pdf"

                if self.download_attachment(link, attachment_folder, filename):
                    attachments.append(filename)
                await page.close()
                return {
                    'content': "PDF document - content available in attachment",
                    'attachments': attachments
                }

            # Get page content
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Try to extract main content
            # Look for content in common containers
            content_selectors = [
                'div.content',
                'div.main-content',
                'div.article-content',
                'div.news-content',
                '#content',
                '.content'
            ]

            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove scripts, styles, and navigation
                    for unwanted in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        unwanted.decompose()
                    content = content_elem.get_text().strip()
                    break

            # If no specific content container found, extract from body
            if not content:
                body = soup.find('body')
                if body:
                    # Remove unwanted elements
                    for unwanted in body.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside']):
                        unwanted.decompose()
                    content = body.get_text().strip()

            # Clean up content - remove excessive whitespace
            content = re.sub(r'\n\s*\n', '\n\n', content)
            content = re.sub(r'\s+', ' ', content)

            # Find attachments - look for PDF and document links
            attachment_selectors = [
                'a[href$=".pdf"]',
                'a[href$=".doc"]',
                'a[href$=".docx"]',
                'a[href*="download"]'
            ]

            for selector in attachment_selectors:
                attach_elems = soup.select(selector)
                for attach_elem in attach_elems:
                    attach_url = attach_elem.get('href')
                    attach_name = attach_elem.get_text().strip()

                    if not attach_name:
                        # Use filename from URL
                        attach_name = attach_url.split('/')[-1] if attach_url else "attachment.pdf"

                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url

                        # Download attachment
                        if self.download_attachment(attach_url, attachment_folder, attach_name):
                            attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Law Bank announcement {link}: {e}")
        
        return {
            'content': content,
            'attachments': attachments
        }

        return {
            'content': content,
            'attachments': attachments
        }