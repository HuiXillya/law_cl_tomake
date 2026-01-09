from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class TDCC_Crawler(BaseCrawler):
    """Crawler for Taiwan Depository & Clearing Corporation (TDCC) website"""
    DISPLAY_NAME = "公告事項-TDCC 臺灣集中保管結算所"
    BASE_URL = "https://www.tdcc.com.tw"
    LIST_URL = "https://www.tdcc.com.tw/portal/zh/news/list"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TDCC website.

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

            # Skip the header row (first row)
            for row in rows[1:]:
                try:
                    # Extract date
                    date_elem = row.find('span', string=lambda x: x and '/' in str(x))
                    if date_elem:
                        date_text = date_elem.get_text().strip()
                        # Convert YYYY/MM/DD to YYYY-MM-DD
                        if '/' in date_text:
                            parts = date_text.split('/')
                            if len(parts) == 3:
                                date = f"{parts[0]}-{parts[1].zfill(2)}-{parts[2].zfill(2)}"
                            else:
                                date = date_text
                        else:
                            date = date_text
                    else:
                        continue

                    # Extract title and link
                    title_elem = row.find('a', class_='ta-l')
                    if title_elem:
                        title = title_elem.get_text().strip()
                        link = title_elem.get('href')

                        if link:
                            if link.startswith('/'):
                                link = self.BASE_URL + link
                            elif not link.startswith('http'):
                                link = self.BASE_URL + '/' + link

                            # Apply date filter if provided
                            if date_filter and date != date_filter:
                                continue

                            announcements.append({
                                'date': date,
                                'title': title,
                                'link': link
                            })

                except Exception as e:
                    self.logger.error(f"Error parsing TDCC announcement row: {e}")
                    continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching TDCC announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TDCC announcement detail page.

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

            # Extract content from paragraphs
            paragraphs = soup.find_all('p')
            content_parts = []

            for p in paragraphs:
                text = p.get_text().strip()
                # Skip JavaScript warning and very short texts
                if text and len(text) > 20 and 'JavaScript' not in text:
                    content_parts.append(text)

            content = '\n'.join(content_parts)

            content_soup = soup.find('div',id='layout').find('div', id="body").find('main')
            # Look for attachments - check for links to PDFs or documents
            # TDCC seems to have general footer attachments, but check for news-specific ones
            attach_elems = content_soup.find_all('a', href=lambda x: x and (
                '.pdf' in x.lower() or '.doc' in x.lower() or '.zip' in x.lower()
            ))

            for attach_elem in attach_elems:
                attach_url = attach_elem.get('href')
                attach_text = attach_elem.get_text().strip()

                # Skip general footer links (privacy policy, etc.)
                if attach_text and not any(general in attach_text for general in [
                    '隱私權', '資通安全', '個人資料', '檢舉制度', '業務手冊'
                ]):
                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url

                        # Use link text as filename, or extract from URL
                        filename = attach_text or attach_url.split('/')[-1]

                        # Download attachment
                        state,filename = self.download_attachment(attach_url, attachment_folder, filename)
                        if state:
                            attachments.append(filename)
                        else:
                            self.logger.error(f"failed to download attachment: {attach_url}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing TDCC announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }