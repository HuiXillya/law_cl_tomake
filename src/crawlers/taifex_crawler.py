from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
from urllib.parse import quote


class TAIFEX_Crawler(BaseCrawler):
    """Crawler for Taiwan Futures Exchange (TAIFEX) website"""
    DISPLAY_NAME = "台灣期貨交易所 - 最新消息 - 公告"
    BASE_URL = "https://www.taifex.com.tw"
    LIST_URL = "https://www.taifex.com.tw/cht/11/announcement"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TAIFEX website.

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

            # Find the announcement table/list
            # The announcements are in a table with dates and titles
            table = soup.find('table')
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all('td')
                    if len(cells) >= 2:
                        date_cell = cells[0]
                        title_cell = cells[1]

                        date_text = date_cell.get_text().strip()
                        title_elem = title_cell.find('a')

                        if title_elem:
                            title = title_elem.get_text().strip()
                            link = title_elem.get('href')

                            if link:
                                if not link.startswith('http'):
                                    link = self.BASE_URL + link

                                # Convert date format from YYYY/MM/DD to YYYY-MM-DD
                                if '/' in date_text:
                                    date_parts = date_text.split('/')
                                    if len(date_parts) == 3:
                                        date = f"{date_parts[0]}-{date_parts[1].zfill(2)}-{date_parts[2].zfill(2)}"
                                    else:
                                        date = date_text
                                else:
                                    date = date_text

                                # Apply date filter if provided
                                if date_filter and date != date_filter:
                                    continue

                                announcements.append({
                                    'date': date,
                                    'title': title,
                                    'link': link
                                })

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching TAIFEX announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TAIFEX announcement detail page.

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

            # Check if the link is directly to a PDF
            if link.lower().endswith('.pdf'):
                # Download the PDF directly
                filename = link.split('/')[-1]
                if self.download_attachment(link, attachment_folder, filename):
                    attachments.append(filename)
                content = "PDF attachment"
            else:
                # Parse the page content
                page_content = await page.content()
                soup = BeautifulSoup(page_content, 'html.parser')

                # Extract main content
                # Look for content in divs or paragraphs
                content_divs = soup.find_all(['div', 'p'], class_=lambda x: x and any(keyword in x for keyword in ['content', 'text', 'main']))
                
                content_parts = []
                for div in content_divs:
                    text = div.get_text().strip()
                    if text and len(text) > 10:
                        content_parts.append(text)
                
                if not content_parts:
                    # Fallback: get all text from body
                    body = soup.find('body')
                    if body:
                        content = body.get_text().strip()
                    else:
                        content = soup.get_text().strip()
                else:
                    content = '\n'.join(content_parts)

                # Find attachments - look for PDF links
                attachment_elems = soup.find_all('a', href=lambda x: x and x.lower().endswith('.pdf'))
                
                for attach_elem in attachment_elems:
                    attach_url = attach_elem.get('href')
                    attach_name = attach_url.split('/')[-1]

                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url
                        attach_url = quote(attach_url)
                        # Download attachment
                        if self.download_attachment(attach_url, attachment_folder, attach_name):
                            attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing TAIFEX announcement {link}: {e}")
            # raise e # Don't raise, just log
        
        return {
            'content': content,
            'attachments': attachments
        }