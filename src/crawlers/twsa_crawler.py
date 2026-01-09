from urllib.parse import quote
from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import re


class TWSA_Crawler(BaseCrawler):
    """Crawler for Taiwan Securities Association (TWSA) website"""
    DISPLAY_NAME = "最新公告 - 中華民國證券商業同業公會全球資訊網"
    BASE_URL = "https://www.twsa.org.tw"
    LIST_URL = "https://www.twsa.org.tw/F01/F011.html"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TWSA website.

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

            # Find announcement sections - look for the "最新公告" sections
            announcement_sections = soup.find('section',class_='lp')\
                .find('tbody').find_all('tr')
            for raw_announcement in announcement_sections[:15]:
                # find date part, title part, url part
                ## date part 
                line = raw_announcement.find('td',class_="num nowrap").get_text()
                # Look for ROC date pattern (e.g., "114年9月18日")
                if '年' in line and '月' in line and '日' in line:
                    # Extract numbers: 114年9月18日 -> 114/9/18
                    match = re.search(r'(\d+)年(\d+)月(\d+)日', line)
                    if match:
                        roc_year, month, day = match.groups()
                        current_date = f"{roc_year}/{month}/{day}"
                else :
                    current_date = "1911/01/01" # Default/fallback date
                date = self.convert_roc_date(current_date)

                ## title part
                title_part = raw_announcement.find('a').get_text()

                ## url part
                link_part = raw_announcement.find('a').get('href')
                if link_part == None:
                    continue
                else:
                    link_part = self.BASE_URL  +link_part[2:]
                announcements.append({
                    'date': date,
                    'title': title_part,
                    'link': link_part
                })

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching TWSA announcements: {e}")
            # raise e

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TWSA announcement detail page.

        Args:
            link (str): Announcement URL (likely the main page)
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

            
            content = soup.find('section', class_="lp")\
                .get_text().strip() 
            # content = "TWSA announcements are listed on the main page. Please visit https://www.twsa.org.tw/F01/F011.html for the latest announcements."

            # Look for any downloadable files (PDFs, docs, etc.)
            attachment_elems = soup.find('section',class_="lp")\
                .find('div',class_="table_list")\
                .find_all('a', class_="auto-style4")
            
            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href').strip()
                attach_name = attach_url.split('/')[-1] 
                attach_name = attach_name if "." in attach_name else default_filename
                attach_url
                if attach_url:
                    attach_url= quote(attach_url)
                    if not attach_url.startswith('http'):
                        attach_url = attach_url.replace("..",self.BASE_URL)
                    # Download attachment
                    state, attach_name = self.download_attachment(attach_url, attachment_folder, attach_name)
                    if state:
                        attachments.append(attach_name)
                    else:
                        self.logger.error(f"Failed to download attachment: {attach_url}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing TWSA announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }