from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import re


class TFutures_Crawler(BaseCrawler):
    """Crawler for Taiwan Futures Exchange (TFutures) website"""
    DISPLAY_NAME = "現行規章-中華民國期貨業商業同業公會"
    BASE_URL = "https://www.futures.org.tw"
    LIST_URL = "https://www.futures.org.tw/zh-tw/law/latest"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from TFutures website.

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

            # Find all title elements
            title_elements = soup.find_all('div', class_='title')
            
            for title_elem in title_elements:
                title_text = title_elem.get_text().strip()
                
                # Find the corresponding date - look backwards for time element
                date_elem = None
                current = title_elem.previous_sibling
                
                while current and not date_elem:
                    if hasattr(current, 'find'):
                        time_elem = current.find('time')
                        if time_elem:
                            date_elem = time_elem
                            break
                    if hasattr(current, 'name') and current.name == 'time':
                        date_elem = current
                        break
                    current = current.previous_sibling
                
                if not date_elem:
                    # Try looking in parent elements
                    parent = title_elem.parent
                    while parent and not date_elem:
                        time_elem = parent.find('time')
                        if time_elem:
                            date_elem = time_elem
                            break
                        parent = parent.parent
                
                if date_elem:
                    date_text = date_elem.get_text().strip()
                    
                    # Apply date filter if provided
                    if date_filter and date_text != date_filter:
                        continue
                    
                    # Look for attachment links in the next div sibling
                    attachment_links = []
                    
                    # The attachments are in the next div sibling after the title
                    current = title_elem.next_sibling
                    while current:
                        if hasattr(current, 'name') and current.name == 'div':
                            # Found a div, look for links inside it
                            links = current.find_all('a', href=True)
                            for link in links:
                                href = link.get('href')
                                if href and ('/file/attachmentStatic/' in href or '/file/' in href):
                                    attachment_links.append(link)
                            break  # Only check the first div after title
                        current = current.next_sibling
                    
                    if attachment_links:
                        # If there are attachments, create separate entries for each
                        for idx, link_elem in enumerate(attachment_links, 1):
                            attach_url = link_elem.get('href')
                            if attach_url:
                                if not attach_url.startswith('http'):
                                    attach_url = self.BASE_URL + attach_url
                                # Create title with attachment index if multiple
                                final_title = link_elem.get_text()
                                
                                announcements.append({
                                    'date': date_text,
                                    'title': final_title,
                                    'link': attach_url
                                })
                    else:
                        # No attachments found, still add the entry
                        announcements.append({
                            'date': date_text,
                            'title': title_text,
                            'link': self.LIST_URL  # Link back to list page
                        })

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching TFutures announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse TFutures announcement.

        Since TFutures lists attachments directly on the main page,
        the link parameter is already the attachment download URL.

        Args:
            link (str): Attachment download URL
            attachment_folder (str): Folder for attachments

        Returns:
            dict: {'content': str, 'attachments': list}
        """
        content = ""
        attachments = []
        filename = default_filename
        try:
            # If the link is an attachment URL, download it directly
            if filename :
                # Download the attachment
                state,filename =  self.download_attachment(link, attachment_folder, filename)
                if state:
                    attachments.append(filename)
                    content = f"Attachment downloaded: {filename}"
                else:
                    content = "Failed to download attachment"
            else:
                # If not an attachment link, content is minimal
                content = ""
                self.logger.error(f"No default filename provided for attachment link: {link}")
                raise Exception("No default filename provided for attachment link")
        except Exception as e:
            self.logger.error(f"Error parsing TFutures announcement {link}: {e}")
            content = f"Error: {str(e)}"

        return {
            'content': content,
            'attachments': attachments
        }