from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class BankingLaw_Crawler(BaseCrawler):
    """Crawler for Banking Bureau Law website"""
    DISPLAY_NAME = "金管會 - 銀行局 - 最新消息"
    BASE_URL = "https://law.banking.gov.tw"
    LIST_URL = "https://law.banking.gov.tw/Chi/default.aspx"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Banking Bureau Law website.

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

            # Find announcement table rows
            rows = soup.find_all('tr')

            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 3:
                    try:
                        # Extract date (ROC format like 114.09.24)
                        date_text = cells[1].get_text().strip()
                        # Extract title and link
                        title_cell = cells[3] if len(cells) > 3 else cells[2]
                        title_link = title_cell.find('a') if title_cell else None

                        if title_link and date_text:
                            title = title_link.get_text().strip()
                            link = title_link.get('href')

                            if link and not link.startswith('http'):
                                link = self.BASE_URL + "/Chi/" + link

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
            self.logger.error(f"Error fetching Banking Law announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Banking Law announcement detail page.

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

            # Extract main content from the page
            main_area = soup.find('div', id='main').find('div', id='Law-Content') 

            if main_area:
                # Remove navigation and unwanted elements
                for unwanted in main_area.find_all(['nav', 'header', 'footer', 'script', 'style']):
                    unwanted.decompose()

                content = main_area.get_text().strip()
            else:
                # Fallback: extract content from the body
                body = soup.find('body')
                if body:
                    # Try to find content between specific markers
                    all_text = body.get_text()
                    # Look for content after the title
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                    content_parts = []
                    capture = False
                    for line in lines:
                        if '最新訊息' in line or '發文機關' in line:
                            capture = True
                            continue
                        elif any(footer in line for footer in ['瀏覽人次', '隱私權政策', '版權所有']):
                            break
                        elif capture and len(line) > 5:
                            content_parts.append(line)

                    content = '\n'.join(content_parts)

            # Find attachments - look for download links
            attachment_elems = soup.find_all('a', href=lambda x: x and (
                '.pdf' in x.lower() or '.doc' in x.lower() or '.docx' in x.lower() or
                '.zip' in x.lower() or 'download' in x.lower() or 'getfile' in x.lower()
            ))

            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href')
                self.logger.debug(f"Found attachment URL: {attach_url}")
                attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]
                if "getFile.ashx?out=1" in attach_url :
                    continue 
                if attach_url:
                    if not attach_url.startswith('http') and not "/Chi/" in attach_url:
                        attach_url = self.BASE_URL +"/Chi/" + attach_url
                    self.logger.debug(f"Downloading attachment: {attach_name} from {attach_url}")
                    # Download attachment
                    state,attach_name = self.download_attachment(attach_url, attachment_folder, attach_name)
                    if state:
                        attachments.append(attach_name)
                    else:
                        self.logger.error(f"Failed to download attachment: {attach_url}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Banking Law announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }