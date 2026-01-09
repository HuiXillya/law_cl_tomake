
from urllib.parse import quote

from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler

class TPEx_Crawler(BaseCrawler):
    """Crawler for Taipei Exchange (TPEx) website"""
    DISPLAY_NAME = "法規修訂資訊 - 證券櫃檯買賣中心"
    BASE_URL = "https://www.tpex.org.tw"
    LIST_URL = "https://www.tpex.org.tw/zh-tw/announce/law/revised.html"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TPEx website.

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

            # Find announcement table/list
            # TPEx uses a table structure for announcements
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')

                for row in rows[1:]:  # Skip header row
                    cells = row.find_all('td')
                    if len(cells) >= 4:  # Index, Date, Doc Number, Title/Link
                        try:
                            # Extract date (ROC format) - Cell 1
                            date_text = cells[1].get_text().strip()

                            # Extract title and link - Cell 3
                            title_cell = cells[3]
                            title_elem = title_cell.find('a')
                            if title_elem:
                                title = title_elem.get_text().strip()
                                link = title_elem.get('href')

                                if link and not link.startswith('http'):
                                    link = self.BASE_URL + '/zh-tw/announce/law/' + link

                                # Convert ROC date to Gregorian
                                date = self.convert_roc_date(date_text)

                                # Apply date filter if provided
                                if date_filter and date != date_filter:
                                    continue

                                announcements.append({
                                    'date': date,
                                    'title': title,
                                    'link': link
                                })

                        except Exception as e:
                            self.logger.error(f"Error parsing TPEx announcement row: {e}")
                            continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching TPEx announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TPEx announcement detail page.

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

            content_elem = soup.find("div",class_="container fullpage").find("div",id="templates-content")
            content_elem = content_elem.find("div",class_="rwd-table")
            
            for row_x in content_elem.find_all("tr"):
                title_th = row_x.find("th").get_text() if row_x.find("th") else ""
                # find content
                if "公告事項" in title_th:
                    content = row_x.find("div").get_text().strip()

                # Find attachments - look for download links
                elif "附件" in title_th:
                    for attach_elem in row_x.find_all("a"):
                        attach_url = attach_elem.get('href')
                        attach_name = attach_elem.get_text().strip() 
                        if attach_url:
                            if not attach_url.startswith('http'):
                                attach_url = f"{self.BASE_URL}{attach_url}"
                            state,attach_name = self.download_attachment(attach_url, attachment_folder, attach_name)
                            if state:
                                attachments.append(attach_name)
                            else:
                                self.logger.error(f"Failed to download {attach_url}")
            
            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing TPEx announcement {link}: {e}")
            # raise e
        return {
            'content': content,
            'attachments': attachments
        }