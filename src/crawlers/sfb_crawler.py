from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import urllib.parse

class SFB_Crawler(BaseCrawler):
    """Crawler for Securities and Futures Bureau (SFB) website"""
    DISPLAY_NAME = "證期局 - 最新法令函釋"
    BASE_URL = "https://www.sfb.gov.tw"
    LIST_URL = "https://www.sfb.gov.tw/ch/home.jsp?id=88&parentpath=0,3"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from SFB website.

        Args:
            date_filter (str, optional): Target date in YYYY-MM-DD format

        Returns:
            list: List of dicts with 'date', 'title', 'link'
        """
        announcements = []

        try:
            page = await self.browser.new_page()
            await page.set_extra_http_headers({
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })

            await page.goto(self.LIST_URL)
            await page.wait_for_load_state('domcontentloaded')

            # Wait for dynamic content to load
            await page.wait_for_timeout(5000)

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')

            # Find main content area
            maincontent = soup.find('div', id='maincontent')
            if maincontent:
                # Extract announcements from the structured data
                all_text = maincontent.get_text()
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                # Find links in maincontent
                links = maincontent.find_all('a', href=True)
                link_dict = {}
                for link in links:
                    href = link.get('href')
                    text = link.get_text().strip()
                    if text and href and 'lawnews_view.jsp' in href:
                        link_dict[text] = href

                # Parse announcements from the text lines
                i = 0
                while i < len(lines):
                    line = lines[i]
                    if line.isdigit() and len(line) <= 3:  # Announcement number
                        number = line
                        title = ""
                        date = ""
                        category = ""

                        # Find title (next line with substantial content)
                        j = i + 1
                        while j < len(lines) and not title:
                            next_line = lines[j]
                            if (next_line and len(next_line) > 10 and
                                not next_line.isdigit() and
                                '日期' not in next_line and
                                '性質別' not in next_line and
                                '編號' not in next_line and
                                '標題' not in next_line):
                                title = next_line
                            j += 1

                        # Find date (YYYY-MM-DD format)
                        while j < len(lines) and not date:
                            next_line = lines[j]
                            if (next_line and len(next_line) == 10 and
                                next_line.count('-') == 2 and
                                next_line.replace('-', '').isdigit()):
                                date = next_line
                            j += 1

                        # Find category
                        while j < len(lines) and not category:
                            next_line = lines[j]
                            if (next_line and len(next_line) > 2 and
                                next_line not in ['編號', '標題', '日期', '性質別'] and
                                not next_line.isdigit()):
                                category = next_line
                            j += 1

                        # Get link for this title
                        link = ""
                        if title in link_dict:
                            link = link_dict[title]
                            if not link.startswith('http'):
                                link = self.BASE_URL + '/ch/' + link

                        if title and date:
                            # Apply date filter if provided
                            if date_filter and date != date_filter:
                                i = j
                                continue

                            announcements.append({
                                'date': date,
                                'title': title,
                                'link': link
                            })

                        i = j
                    else:
                        i += 1

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching SFB announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse SFB announcement detail page.

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
            await page.wait_for_timeout(3000)

            # Get page content
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Find main content area
            maincontent = soup.find('div', id='maincontent')
            if maincontent:
                # Extract the main text content
                # Remove navigation, headers, footers
                for unwanted in maincontent.find_all(['nav', 'header', 'footer', 'script', 'style']):
                    unwanted.decompose()

                # Get all text and clean it up
                all_text = maincontent.get_text()
                lines = [line.strip() for line in all_text.split('\n') if line.strip()]

                # Find the main content (skip title, date, category headers)
                content_lines = []
                in_content = False
                for line in lines:
                    if '性質別：' in line:
                        in_content = True
                        continue
                    elif any(skip in line for skip in ['瀏覽人次：', '更新日期：', '相關附件']):
                        break
                    elif in_content and line and len(line) > 5:
                        content_lines.append(line)

                content = '\n'.join(content_lines)

                # Find attachments
                attachment_links = maincontent.find_all('a', href=lambda x: x and ('uploaddowndoc' in x or '.pdf' in x or '.doc' in x))
                for attach_elem in attachment_links:
                    attach_url = attach_elem.get('href')
                    attach_name = attach_elem.get_text().strip()

                    if attach_url:
                        if not attach_url.startswith('http'):
                            attach_url = self.BASE_URL + attach_url

                        # Clean up filename
                        if not attach_name and 'filedisplay=' in attach_url:
                            # Extract filename from URL parameter
                            parsed = urllib.parse.urlparse(attach_url)
                            query = urllib.parse.parse_qs(parsed.query)
                            if 'filedisplay' in query:
                                attach_name = query['filedisplay'][0]
                        attach_name = attach_name.replace('/','_').replace('.','')
                        if attach_name:
                            # Download attachment
                            state,attach_name =  self.download_attachment(attach_url, attachment_folder, attach_name)
                            if state:
                                attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing SFB announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }