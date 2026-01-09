import re 
from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class SELAW_Crawler(BaseCrawler):
    """Crawler for Securities and Futures Law Query System (SELAW) website"""
    DISPLAY_NAME = "證券暨期貨法令盼解查詢系統 - 最新消息"
    BASE_URL = "https://www.selaw.com.tw"
    LAW_URL = "https://www.selaw.com.tw/Chinese/RegulatoryInformation?maintainValue=Law"
    AD_URL = "https://www.selaw.com.tw/Chinese/RegulatoryInformation?maintainValue=Ad"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from SELAW website (both Law and Administrative orders).

        Args:
            date_filter (str, optional): Target date in YYYY-MM-DD format

        Returns:
            list: List of dicts with 'date', 'title', 'link'
        """
        announcements = []

        urls_to_crawl = [
            (self.LAW_URL, "Law"),
            (self.AD_URL, "Administrative Order")
        ]

        for url, category in urls_to_crawl:
            try:
                page = await self.browser.new_page()

                # Set user agent
                await page.set_extra_http_headers({
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                })

                await page.goto(url)
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(3000)

                # Get page content
                content = await page.content()
                soup = BeautifulSoup(content, 'html.parser')

                # Find the announcements table
                table = soup.find('table', class_='table con-table-index01')
                if table:
                    rows = table.find_all('tr')

                    # Skip the header row
                    for row in rows[1:]:
                        cells = row.find_all('td')
                        if len(cells) >= 5:
                            # Extract data: seq, authority, empty, date, title
                            authority = cells[1].get_text().strip()
                            date_roc = cells[3].get_text().strip()
                            title_cell = cells[4]

                            # Find the link in the title cell
                            link_elem = title_cell.find('a')
                            if link_elem:
                                title = link_elem.get_text().strip()
                                href = link_elem.get('href')

                                if href:
                                    if not href.startswith('http'):
                                        link = self.BASE_URL + href
                                    else:
                                        link = href

                                    # Convert ROC date to Gregorian
                                    date = self.convert_roc_date(date_roc)

                                    # Apply date filter if provided
                                    if date_filter and date != date_filter:
                                        continue

                                    announcements.append({
                                        'date': date,
                                        'title': f"[{category}] {title}",
                                        'link': link
                                    })

                await page.close()

            except Exception as e:
                self.logger.error(f"Error fetching SELAW {category} announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse SELAW announcement detail page.

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
            await page.wait_for_timeout(2000)
            
            try:
                # Try to click attachment download button if it exists
                # Using try-except because it might not exist or might fail
                await page.get_by_role('button', name=re.compile("附件下載", re.IGNORECASE)).click(timeout=5000)
                await page.wait_for_load_state('domcontentloaded')
                await page.wait_for_timeout(2000)
            except Exception:
                # Button might not exist, continue
                pass

            # Get content page 
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Try to find content 
            content_container = soup.find('main').find('div', class_='con-top')
            content = content_container.get_text(separator='\n').strip() if content_container else ""
            # Find attachments links 

            main_content = soup.find('main').find('div', class_='content')
            attachment_elems = []
            if main_content:
                attachment_elems = main_content.find_all('a', href=lambda x: x and any(ext in x.lower() for ext in ['.pdf', '.doc', '.docx', '.zip', 'download']))

            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href')
                attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]
                attach_name = re.sub(r'[\\/*?:"<>|]', "_", attach_name)  
                attach_name = attach_name.replace('.', '')  
                if attach_url:
                    if not attach_url.startswith('http'):
                        attach_url = self.BASE_URL + attach_url

                    # Download attachment
                    state,attach_name =  self.download_attachment(attach_url, attachment_folder, attach_name)
                    if state:
                        attachments.append(attach_name)
                    else:
                        self.logger.error(f"Failed to download attachment: {attach_url}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing SELAW announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }