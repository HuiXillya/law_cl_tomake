from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class TWSE_dsp_Crawler(BaseCrawler):
    """Crawler for Taiwan Stock Exchange (TWSE) regulation database"""
    DISPLAY_NAME = "公文通函查詢 - 國內業務宣導 - TWSE 臺灣證券交易所"
    BASE_URL = "https://dsp.twse.com.tw"
    LIST_URL = "https://dsp.twse.com.tw/official/search#"

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
            # click "尋找近一個月" link
            await page.locator("id=buttom_form3").click()
            await page.wait_for_load_state('domcontentloaded')
            await page.wait_for_timeout(3000)
            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            table_elem = soup.find("table",class_="grid")
            if table_elem is None:
                self.logger.error("the website structure has changed, please check")
                await page.close()
                return announcements

            row_elems = table_elem.find("tbody").find_all("tr")
            if not row_elems:
                self.logger.error(f"{self.LIST_URL}Could not find any rows in the announcements table")
                await page.close()
                return announcements

            for row in row_elems[:10]:
                td_elems = row.find_all('td')
                if len(td_elems) != 6:
                    self.logger.error("the website structure has changed, please check")
                    continue

                date_str = td_elems[1].get_text().strip()
                date = self.convert_roc_date(date_str)
                if date_filter and date != date_filter:
                            continue
                title = td_elems[4].get_text().strip()

                link_suffix = row.get('id')
                link = f"{self.BASE_URL}/official/showDetail/{link_suffix}"
                
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
            content_tbody = soup.find('div', id='wrapper').find('tbody')
            if content_tbody is None:
                self.logger.error("the website structure has changed, please check")
                await page.close()
                return {'content': content, 'attachments': attachments}

            layers = content_tbody.find_all('tr')
            for layer in layers:
                row_name = layer.find_all('td')[0].get_text()
                if '說明' in row_name:
                    content = layer.find_all('td')[1].get_text().strip()
                if '附件' in row_name:
                    for attach_elem in layer.find_all('td')[1].find_all('a'):
                        attach_url = attach_elem.get('href')
                        if attach_url is None:
                            self.logger.error("cannot find attachment link")
                            continue
                        name = attach_url.split('/')[-1].split('?')[0]
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