from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class TWSE_regulation_Crawler(BaseCrawler):
    """Crawler for Taiwan Stock Exchange (TWSE) regulation database"""
    DISPLAY_NAME = "臺灣證券交易所 法規分享知識庫"
    BASE_URL = "https://twse-regulation.twse.com.tw"
    LIST_URL = "https://twse-regulation.twse.com.tw/TW/Default.aspx"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TWSE regulation database.

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

            # Find the table with announcements
            # The announcements are in a table with class or structure containing the list
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:  # Serial, Date, Action, Title
                        try:
                            date_elem = cols[1]
                            title_elem = cols[3].find('a')

                            if date_elem and title_elem:
                                date_text = date_elem.get_text().strip()
                                title = title_elem.get_text().strip()
                                link = title_elem.get('href')

                                if link and not link.startswith('http'):
                                    if not link.startswith('/'):
                                        link = '/' + link
                                    link = self.BASE_URL + link

                                # Convert ROC date to Gregorian
                                date = self.convert_roc_date(date_text.replace('.', '/'))

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
            self.logger.error(f"Error fetching TWSE announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TWSE announcement detail page.

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

            # Extract main content
            # Look for content in specific divs or sections
            content_div = soup.find('div', class_='content') or soup.find('div', id='content')
            if content_div:
                content = content_div.get_text().strip()
            else:
                # Fallback: find the main text content
                # Remove headers, footers, navigation
                for unwanted in soup.find_all(['nav', 'header', 'footer', 'script', 'style']):
                    unwanted.decompose()

                # Try to find content in paragraphs or main div
                paragraphs = soup.find_all('p')
                if paragraphs:
                    content_parts = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    content = '\n'.join(content_parts)
                else:
                    # Last resort: get all text
                    content = soup.get_text().strip()

            # Find attachments - look for download links
            attachment_elems = soup.find_all('a', href=lambda x: x and ('.pdf' in x or '.doc' in x or '.zip' in x or 'download' in x))

            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href')
                attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]

                if attach_url:
                    if not attach_url.startswith('http'):
                        attach_url = self.BASE_URL + attach_url

                    # Download attachment
                    if self.download_attachment(attach_url, attachment_folder, attach_name):
                        attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing TWSE announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }