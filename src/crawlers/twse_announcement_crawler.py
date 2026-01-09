from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class TWSE_announcement_Crawler(BaseCrawler):
    """Crawler for Taiwan Stock Exchange (TWSE) regulation database"""
    DISPLAY_NAME = "公文公告 - TWSE 臺灣證券交易所"
    BASE_URL = "https://www.twse.com.tw"
    LIST_URL = "https://www.twse.com.tw/zh/announcement/announcement/list.html"

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
            table_elem = (soup.find("div",id="body").find('main')
                          .find("tbody"))
            if table_elem is None:
                self.logger.error("the website structure has changed, please check")
                await page.close()
                return announcements

            row_elems = table_elem.find_all("tr")
            if not row_elems:
                self.logger.error(f"{self.LIST_URL}Could not find any rows in the announcements table")
                await page.close()
                return announcements

            for row in row_elems:
                td_elems = row.find_all('td')
                if len(td_elems) != 4:
                    self.logger.error("the website structure has changed, please check")
                    continue

                date_str = td_elems[1].get_text().strip().replace("中華民國",'')
                date = self.convert_roc_date(date_str)
                if date_filter and date != date_filter:
                            continue
                title = td_elems[3].get_text().strip()

                link = row.find_all('a')[0].get('href')
                if not link.startswith('http'):
                    link = f"{self.BASE_URL}/zh/announcement/announcement/{link}"
                
                # Append to announcements list
                announcements.append({
                    'date': date,
                    'title': title,
                    'link': link
                })
            
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
            content_tbody = soup.find('main').find('table')
            if content_tbody is None:
                self.logger.error("the website structure has changed, please check")
                await page.close()
                return {'content': content, 'attachments': attachments}

            idx_names = [x.split(': ')[1].replace("'","") for x in content_tbody.get('style').split(';')[:-1]]
            layers = content_tbody.find_all('td')
            for idx_name,layer in zip(idx_names,layers):
                if '公告事項' in idx_name:
                    content = layer.find('div').get_text().strip()
                if '附件' in idx_name:
                    for attach_elem in layer.find_all('a'):
                        attach_url = attach_elem.get('href')
                        if attach_url is None:
                            self.logger.error("cannot find attachment link")
                            continue
                        name = attach_url.split('/')[-1]
                        # Download attachment
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url
                        state,name = self.download_attachment(attach_url, attachment_folder, name)
                        if state:
                            attachments.append(name)
                        else:
                            self.logger.error(f"failed to download attachment: {attach_url}")
            
            await page.close()
        except Exception as e:
            self.logger.error(f"Error parsing TWSE announcement {link}: {e}")
            # raise e
        return {
            'content': content,
            'attachments': attachments
        }