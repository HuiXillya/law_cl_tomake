from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import re


class Trust_Crawler(BaseCrawler):
    """Crawler for Trust Association of the Republic of China website"""
    DISPLAY_NAME = "最新消息 - 中華民國信託業商業同業公會"
    BASE_URL = "https://www.trust.org.tw"
    LIST_URL = "https://www.trust.org.tw/tw/news"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Trust Association website.

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

            await page.goto(self.LIST_URL)
            await page.wait_for_load_state('domcontentloaded')

            # Wait for dynamic content
            await page.wait_for_timeout(3000)

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Get all news links
            links = soup.find_all('a', href=lambda x: x and x.startswith('/tw/news/') and x != '/tw/news')

            # Get dates from the text content
            all_text = soup.get_text()
            date_title_section = all_text.split('日期主題')[1].split('會員入會須知')[0]

            # Parse dates and titles from text
            text_items = re.findall(r'(\d{3}/\d{1,2}/\d{1,2})([^0-9]+)', date_title_section)

            # Combine links with dates
            for link_elem, (roc_date, _) in zip(links, text_items):
                href = link_elem.get('href')
                title = link_elem.get_text().strip()

                if not title or len(title) < 10:
                    continue

                # Convert ROC date to Gregorian
                parts = roc_date.split('/')
                year = int(parts[0]) + 1911
                month = int(parts[1])
                day = int(parts[2])
                date = f"{year:04d}-{month:02d}-{day:02d}"

                # Apply date filter if provided
                if date_filter and date != date_filter:
                    continue

                link = self.BASE_URL + href if href.startswith('/') else href

                announcements.append({
                    'date': date,
                    'title': title,
                    'link': link
                })

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Trust Association announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Trust Association announcement detail page.

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

            # Get page content
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Extract content from paragraphs
            paragraphs = soup.find_all('p')
            content_parts = []

            for p in paragraphs:
                text = p.get_text().strip()
                if text and len(text) > 10:  # Filter out short texts
                    content_parts.append(text)

            content = '\n'.join(content_parts)

            # Find attachments - look for download links
            attachment_elems = soup.find_all('a', href=lambda x: x and ('.pdf' in x or '.doc' in x or '.zip' in x or 'download' in x))

            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href')
                attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]
                if not "." in attach_name and default_filename:
                    for ext in ['.pdf', '.doc', '.zip']:
                        if ext in attach_url:
                            attach_name = attach_name + ext
                if attach_url:
                    if not attach_url.startswith('http'):
                        attach_url = self.BASE_URL + attach_url

                    # Download attachment
                    if self.download_attachment(attach_url, attachment_folder, attach_name):
                        attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Trust Association announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }