from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import urllib.request
import urllib.error
import os


class MOJ_Law_Crawler(BaseCrawler):
    """Crawler for Ministry of Justice Law Database website"""
    DISPLAY_NAME = "全國法規資料庫 - 最新消息"
    BASE_URL = "https://law.moj.gov.tw"
    LIST_URL = "https://law.moj.gov.tw/News/NewsList.aspx?type=all"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from MOJ Law Database website.

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

            # Find the news table
            # The announcements are in a table with class or id containing news
            news_table = soup.find('table')
            if news_table:
                rows = news_table.find_all('tr')

                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 4:  # Number, Date, Type, Title
                        try:
                            # Extract date (ROC format like 114-09-25)
                            date_td = cols[1]
                            date_text = date_td.get_text().strip()
                            if date_text:
                                # Convert ROC date (replace - with / for conversion)
                                date = self.convert_roc_date(date_text.replace('-', '/'))

                            # Extract title and link
                            title_td = cols[3]
                            title_link = title_td.find('a')
                            if title_link:
                                title = title_link.get_text().strip()
                                link = title_link.get('href')
                                if link and not link.startswith('http'):
                                    link = self.BASE_URL + '/' + link.lstrip('/')

                                if date and title and link:
                                    # Apply date filter if provided
                                    if date_filter and date != date_filter:
                                        continue

                                    announcements.append({
                                        'date': date,
                                        'title': title,
                                        'link': link
                                    })

                        except Exception as e:
                            self.logger.error(f"Error parsing announcement row: {e}")
                            continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching MOJ Law announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse MOJ Law Database announcement detail page.

        Args:
            link (str): Announcement URL
            attachment_folder (str): Folder for attachments

        Returns:
            dict: {'content': str, 'attachments': list}
        """
        content = ""
        attachments = []
        if not "https://gazette.nat.gov.tw" in link :
            return {'content': f"不支援此網頁:{link}，請改為手動", 'attachments': attachments}
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
            # Look for content in main content area
            content_div = soup.find('div', class_='content') or soup.find('div', id='content')
            

            # Find attachments - look for PDF links in the page
            pdf_links = soup.find_all('a', href=lambda x: x and '.pdf' in x.lower())
            for link_elem in pdf_links:
                attach_src = link_elem.get('href')
                if attach_src:
                    if not attach_src.startswith('http'):
                        attach_src = "https://gazette.nat.gov.tw" + attach_src

                    # Extract filename from URL
                    # filename = attach_src.split('/')[-1]
                    filename = default_filename
                    if not filename.lower().endswith('.pdf'):
                        filename += '.pdf'

                    # Download attachment
                    state,filename = self.download_attachment(attach_src, attachment_folder, filename, headers={'Referer': 'https://gazette.nat.gov.tw/egFront/'})
                    if state:
                        attachments.append(filename)
                    else:
                        self.logger.error(f"Failed to download attachment: {attach_src}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing MOJ Law announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }