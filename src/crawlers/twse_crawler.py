from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class TWSE_Crawler(BaseCrawler):
    """Crawler for Taiwan Stock Exchange (TWSE) regulation database"""
    DISPLAY_NAME = "近期修訂資訊 - TWSE 臺灣證券交易所"
    BASE_URL = "https://www.twse.com.tw"
    LIST_URL = "https://www.twse.com.tw/zh/focus/law-recent/list.html"

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
            table = (soup.find("div",id='body').find("tbody"))
            if not table:
                raise ValueError(f"{self.LIST_URL}Could not find the table content div")
            rows = table.find_all('tr')
            if not rows:
                raise ValueError(f"{self.LIST_URL}Could not find any rows in the announcements table")
            for row in rows:
                cols = row.find_all('td')
                assert len(cols) == 2, "the website structure has changed, please check"
                try:
                    date_elem = cols[0]
                    title_elem = cols[1].find('a')
                    if date_elem and title_elem:
                        date_text = date_elem.get_text().strip()
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href')
                        if link and not link.startswith('http'):
                            if not link.startswith('/'):
                                link = '/' + link
                            link = self.BASE_URL + '/zh/focus/law-recent' + link
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
            # raise e

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
            content_tbody = soup.find('div', id='body').find('tbody')
            assert content_tbody is not None, "the website structure has changed, please check"
            layers = content_tbody.find_all('td')
            if len(layers) == 9:
                content = layers[7].get_text().strip()
                for attach_elem in layers[8].find_all('a'):
                    attach_url = attach_elem.get('href')
                    name = attach_url.split('/')[-1].split('?')[0]
                    # Download attachment
                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url
                    state,name = self.download_attachment(attach_url, attachment_folder, name)
                    if state:
                        attachments.append(name)
            else:
                raise ValueError("the website structure has changed, please check")
            await page.close()
        except Exception as e:
            self.logger.error(f"Error parsing TWSE announcement {link}: {e}")
            # raise e
        return {
            'content': content,
            'attachments': attachments
        }