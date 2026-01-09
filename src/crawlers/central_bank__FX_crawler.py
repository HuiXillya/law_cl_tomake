from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class CentralBankFX_Crawler(BaseCrawler):
    """Crawler for Central Bank of the Republic of China (Taiwan) website"""
    DISPLAY_NAME = "中央銀行 - 外匯通函彙編"
    BASE_URL = "https://www.cbc.gov.tw"
    LIST_URL = "https://www.cbc.gov.tw/tw/lp-379-1.html"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Central Bank website.

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

            # Find announcement links - they start with /tw/cp-302-
            announcement_links = soup.find_all('a', href=lambda x: x and x.startswith('/tw/cp-379-'))

            for link_elem in announcement_links:
                try:
                    link = link_elem.get('href')
                    if link and not link.startswith('http'):
                        link = self.BASE_URL + link

                    # The date and title are in the parent element's text
                    # Format: "numberYYYY-MM-DDtitle" (no spaces)
                    parent_text = link_elem.parent.get_text().strip() if link_elem.parent else ""

                    # Extract date and title
                    # Look for date pattern YYYY-MM-DD
                    import re
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', parent_text)
                    if date_match:
                        date = date_match.group(1)
                        # Title is the link text
                        title = link_elem.get_text().strip()

                        # Apply date filter if provided
                        if date_filter and date != date_filter:
                            continue

                        announcements.append({
                            'date': date,
                            'title': title,
                            'link': link
                        })

                except Exception as e:
                    self.logger.error(f"Error parsing announcement: {e}")
                    continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Central Bank announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Central Bank announcement detail page.

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

            # Extract main content - look for paragraphs after the title
            # The content appears to be in multiple paragraphs
            content_paragraphs = []

            # Find all paragraphs that contain substantial text
            all_paragraphs = soup.find_all('p')
            for p in all_paragraphs:
                text = p.get_text().strip()
                # Filter out short or navigation text
                if len(text) > 20 and not any(skip in text for skip in ['發布日期', '回上一頁', '友善列印', '網站分享']):
                    content_paragraphs.append(text)

            # Also check for div elements with content
            content_divs = soup.find_all('div', class_=lambda x: x and ('content' in x or 'text' in x))
            for div in content_divs:
                text = div.get_text().strip()
                if len(text) > 20:
                    content_paragraphs.append(text)

            # If still no content, try to get text from the main body
            if not content_paragraphs:
                body = soup.find('body')
                if body:
                    # Remove scripts, styles, nav, etc.
                    for unwanted in body.find_all(['script', 'style', 'nav', 'header', 'footer']):
                        unwanted.decompose()
                    all_text = body.get_text()
                    # Split into lines and filter
                    lines = [line.strip() for line in all_text.split('\n') if line.strip() and len(line.strip()) > 10]
                    # Skip header lines until we find substantial content
                    start_content = False
                    for line in lines:
                        if '發布日期' in line or '新聞稿' in line:
                            start_content = True
                            continue
                        elif start_content and not any(end in line for end in ['展開OPEN', '收合/CLOSE', '聯絡地址']):
                            content_paragraphs.append(line)

            content = '\n'.join(content_paragraphs)

            # Find attachments - look for download links
            attach_elem = soup.find('div', id='center')
            if attach_elem:
                attach_elem = attach_elem.find('div', class_='file_download')
                if attach_elem:
                    attachment_elems = attach_elem.find_all('a', href=lambda x: x and ('/dl-' in x))

                    for attach_elem in attachment_elems:
                        attach_url = attach_elem.get('href')
                        attach_name = default_filename
                        if attach_elem.get('title'):
                            attach_name = attach_elem.get('title')
                        if attach_url:
                            if not attach_url.startswith('http'):
                                attach_url = self.BASE_URL + attach_url

                            # Download attachment
                            state,attach_name = self.download_attachment(attach_url, attachment_folder, attach_name)
                            if state:
                                attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Central Bank announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }