from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler
import re


class MOEA_Commercial_Crawler(BaseCrawler):
    """Crawler for Ministry of Economic Affairs Commercial Bureau website"""
    DISPLAY_NAME = "經濟部商業發展署 - 商工行政法規檢索系統"
    BASE_URL = "https://gcis.nat.gov.tw"
    LIST_URL = "https://gcis.nat.gov.tw/elaw/"

    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from MOEA Commercial website.

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

            # Find tables containing announcements
            tables = soup.find_all('table')
            
            # If no tables found, try to parse from text content
            if not tables:
                content_text = soup.get_text()
                
                # Look for patterns like "YYYY-MM-DD title category"
                # Pattern for date-title-category entries
                pattern = r'(\d{4}-\d{2}-\d{2})([^\d\n]+?)(法律|法規命令|行政規則|行政函釋)'
                matches = re.findall(pattern, content_text)
                
                for match in matches:
                    date, title, category = match
                    date = date.strip()
                    title = title.strip()
                    category = category.strip()
                    
                    # Apply date filter if provided
                    if date_filter and date != date_filter:
                        continue
                    
                    full_title = f"{title} ({category})"
                    
                    announcements.append({
                        'date': date,
                        'title': full_title,
                        'link': self.LIST_URL  # Use main page as link since no specific links
                    })
            
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 3:  # Expecting date, title, category columns
                        try:
                            # Extract date (might be in YYYY-MM-DD or ROC format)
                            date_elem = cols[0]
                            date_text = date_elem.get_text().strip()
                            
                            # Extract title/subject
                            title_elem = cols[1]
                            title = title_elem.get_text().strip()
                            
                            # Extract category
                            category_elem = cols[2] if len(cols) > 2 else None
                            category = category_elem.get_text().strip() if category_elem else ""
                            
                            # Try to find a link in the title column
                            link_elem = title_elem.find('a')
                            link = link_elem.get('href') if link_elem else None
                            
                            if link and not link.startswith('http'):
                                link = self.BASE_URL + link
                            
                            # Convert ROC dates if needed (check if it contains slashes)
                            if '/' in date_text:
                                date = self.convert_roc_date(date_text)
                            else:
                                date = date_text
                            
                            # Apply date filter if provided
                            if date_filter and date != date_filter:
                                continue
                            
                            # Combine title and category for better identification
                            full_title = f"{title} ({category})" if category else title
                            
                            announcements.append({
                                'date': date,
                                'title': full_title,
                                'link': link or self.LIST_URL  # Use main page if no specific link
                            })
                            
                        except Exception as e:
                            self.logger.error(f"Error parsing table row: {e}")
                            continue

            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching MOEA Commercial announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse MOEA Commercial announcement detail page.

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

            # Extract main content - look for content areas
            content_divs = soup.find_all(['p', 'div'], class_=lambda x: x and ('content' in x or 'text' in x))

            content_parts = []
            for div in content_divs:
                text = div.get_text().strip()
                if text and len(text) > 20:  # Filter out short texts
                    content_parts.append(text)

            # If no specific content divs found, try to get all text from main content area
            if not content_parts:
                main_content = soup.find('div', class_='main') or soup.find('div', id='main')
                if main_content:
                    # Remove navigation, headers, footers
                    for unwanted in main_content.find_all(['nav', 'header', 'footer', 'script', 'style']):
                        unwanted.decompose()
                    content = main_content.get_text().strip()
                else:
                    # Fallback: get all text and try to extract meaningful content
                    all_text = soup.get_text()
                    # Try to find content between title and footer
                    lines = [line.strip() for line in all_text.split('\n') if line.strip()]
                    content_parts = []
                    capture = False
                    for line in lines:
                        if '經濟部商業發展署' in line or '商工行政法規' in line:
                            capture = True
                            continue
                        elif any(footer in line for footer in ['版權所有', '參訪人數', '瀏覽人次']):
                            break
                        elif capture and len(line) > 10:
                            content_parts.append(line)
                    content = '\n'.join(content_parts)
            else:
                content = '\n'.join(content_parts)

            # Find attachments - look for download links
            attachment_elems = soup.find_all('a', href=lambda x: x and ('.pdf' in x or '.doc' in x or '.zip' in x or 'download' in x))

            for attach_elem in attachment_elems:
                attach_url = attach_elem.get('href')
                attach_name = attach_elem.get_text().strip() or attach_url.split('/')[-1]

                if attach_url:
                    if not attach_url.startswith('http'):
                        attach_url = self.BASE_URL + attach_url

                    # Download attachment
                    if self.download_attachment(attach_url, attachment_folder, attach_name):
                        attachments.append(attach_name)

            await page.close()

        except Exception as e:
            self.logger.error(f"Error parsing MOEA Commercial announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }