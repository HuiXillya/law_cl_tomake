from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class CentralBankLaw_Crawler(BaseCrawler):
    """Crawler for Central Bank Law Query System website"""
    DISPLAY_NAME = "中央銀行 - 法規查詢系統"
    BASE_URL = "https://www.law.cbc.gov.tw"
    LIST_URL = "https://www.law.cbc.gov.tw/"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Central Bank Law website.

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

            # Find the latest news section
            news_section = soup.find(string='最新消息')
            if news_section:
                # Find the announcements table
                table = news_section.find_next('table')
                if table:
                    rows = table.find_all('tr')
                    for row in rows:
                        cols = row.find_all('td')
                        if len(cols) >= 3:
                            # Extract date (ROC format like 114.07.15)
                            roc_date = cols[0].get_text().strip()
                            # Convert ROC date to Gregorian (handle both 113/09/25 and 114.07.15 formats)
                            gregorian_date = self.convert_roc_date(roc_date.replace('.', '/'))

                            # Extract title and link
                            title_cell = cols[2]
                            title_link = title_cell.find('a')
                            if title_link:
                                title = title_link.get_text().strip()
                                link = title_link.get('href')
                                if link and not link.startswith('http'):
                                    link = self.BASE_URL + link

                                # Apply date filter if provided
                                if date_filter and gregorian_date != date_filter:
                                    continue

                                announcements.append({
                                    'date': gregorian_date,
                                    'title': title,
                                    'link': link
                                })

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Central Bank Law announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Central Bank Law announcement detail page.

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
            content_elem = soup.find('div', id='pageMainContent').find('div', class_='rule-page-content')
            # find content
            if content_elem:
                content = content_elem.find('div', class_='jumbotron').get_text().strip()
            # find links 
            
            attachments_elem = content_elem.find('div', class_='rule-reason-group')
            self.logger.debug(f"attachments_elem: {attachments_elem}")
            if attachments_elem:
                attachments_links = attachments_elem.find_all('a')
                self.logger.debug(f"attachments_links: {attachments_links}")
                for a_link in attachments_links:
                    att_title = a_link.get_text().strip()
                    att_href = a_link.get('href')
                    if att_href and not att_href.startswith('http'):
                        att_href = self.BASE_URL + att_href
                    if self.download_attachment(att_href, attachment_folder, att_title):
                        attachments.append(att_title)
            # Find attachments - look for download links
            

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Central Bank Law announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }