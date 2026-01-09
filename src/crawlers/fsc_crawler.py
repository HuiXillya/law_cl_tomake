from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class FSC_Crawler(BaseCrawler):
    """Crawler for Financial Supervisory Commission (FSC) website"""
    DISPLAY_NAME = "金管會 - 最新法令函釋"
    BASE_URL = "https://www.fsc.gov.tw"
    LIST_URL = "https://www.fsc.gov.tw/ch/home.jsp?id=2&parentpath=0"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from FSC website.

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
            # Find announcement list
            newslist = soup.find('div', class_='newslist')
            if newslist:
                rows = newslist.find_all('li', role='row')
                
                # Skip the header row (first li)
                for row in rows[1:]:
                    try:
                        date_elem = row.find('span', class_='date')
                        title_elem = row.find('span', class_='title').find('a') if row.find('span', class_='title') else None

                        if date_elem and title_elem:
                            date_text = date_elem.get_text().strip()
                            title = title_elem.get_text().strip()
                            link = title_elem.get('href')

                            if link and not link.startswith('http'):
                                if link.startswith('/'):
                                    link = self.BASE_URL + link
                                else:
                                    link = self.BASE_URL + '/ch/' + link

                            # Dates are already in YYYY-MM-DD format
                            date = date_text

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
            self.logger.error(f"Error fetching FSC announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse FSC announcement detail page.

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

            # Extract main content - look for content after the title
            # The content seems to be in paragraphs or text blocks

            content_elems = soup.find('div', id='container').find('div', class_='content')
            if content_elems:
                if content_elems.find('div', class_='main-a_03') == None:
                    content = content_elems.find('div', class_='maincontent').get_text().strip()
                else:
                    content = content_elems.find('div', class_='main-a_03').get_text().strip()

            # Find attachments - look for download links
            if content_elems.find('div', class_="acces"):
                attachment_elems = content_elems.find('div', class_="acces").find_all('a', href=lambda x: x and any(ext in x.lower() for ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.zip', '.ods']))
                for attach_elem in attachment_elems:
                    attach_url = attach_elem.get('href')
                    attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]
                    attach_name = attach_name.replace('/', '_').replace('\\', '_').replace('.', '_')
                    self.logger.debug(f"Attachment name before check: {attach_name}")
                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url
                        # Download attachment
                        state,attach_name = self.download_attachment(attach_url, attachment_folder, attach_name)
                        if state:
                            attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing FSC announcement {link}: {e}")
            raise e
        return {
            'content': content,
            'attachments': attachments
        }