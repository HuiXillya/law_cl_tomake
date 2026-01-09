from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import urllib.request
import urllib.error
import os
import re


class GAZETTE_Crawler(BaseCrawler):
    """Crawler for Executive Yuan Gazette website"""
    DISPLAY_NAME = "行政院公報資訊網 - 財政經濟篇" 
    BASE_URL = "https://gazette.nat.gov.tw"
    LIST_URL = "https://gazette.nat.gov.tw/egFront/advancedSearchResult.do?action=doQuery&chapter=4&log=browseLog&clickfunc=020"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Executive Yuan Gazette website.

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

            # Find all announcement entries
            # Each announcement is in a <p> tag containing an <a> with detail.do
            table = soup.find('div', class_='List')
            announcement_paragraphs = table.find_all('div', class_='row')
            self.logger.debug(f"Found {len(announcement_paragraphs)} announcement_paragraphs")
            for para in announcement_paragraphs:
                try:
                    date,title,link = None,None,None
                    # Check if this paragraph contains a detail link
                    link_elem = para.find('a', href=lambda x: x and 'detail.do' in x)
                    if not link_elem:
                        continue
                    title = link_elem.get_text().strip()
                    self.logger.debug(f"Title: {title}")
                    link = link_elem.get('href')

                    if link and not link.startswith('http'):
                        link = self.BASE_URL + '/egFront/' + link
                    self.logger.debug(f"Link: {link}")
                    # Find the date - it's usually in a nearby element
                    # Check siblings and ancestors for date
                    date_str = para.find('h4').get_text().strip()
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                    if date_match:
                        date = date_match.group(1)
                    self.logger.debug(f"Date: {date}")
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
                    self.logger.error(f"Error parsing announcement: {e}")
                    continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Executive Yuan Gazette announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Executive Yuan Gazette announcement detail page.

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
            # but now we just leed content be ''
            content = '<the data is in attachment>'

            # Find attachments - look for iframe with class="embed-responsive-item"
            iframe_elem = soup.find('iframe', class_='embed-responsive-item')
            if iframe_elem:
                attach_src = iframe_elem.get('src')
                if attach_src:
                    if not attach_src.startswith('http'):
                        attach_src = self.BASE_URL + attach_src

                    # Use default filename, let download_attachment handle extension
                    filename = default_filename

                    # Download attachment with Referer header
                    state,filename= self.download_attachment(attach_src, attachment_folder, filename, headers={'Referer': 'https://gazette.nat.gov.tw/egFront/'})
                    if state:
                        attachments.append(filename)
                    else:
                        self.logger.error(f"Failed to download attachment: {attach_src}")

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing Executive Yuan Gazette announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }