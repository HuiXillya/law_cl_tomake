from bs4 import BeautifulSoup
from src.base_crawler import BaseCrawler


class Law_Lib_Crawler(BaseCrawler):
    """Crawler for Law Library (Mainland China Laws) website"""
    DISPLAY_NAME = "法律圖書館 (杭州星法科技有限公司 中國法規)"
    BASE_URL = "http://www.law-lib.com"
    LIST_URL = "http://www.law-lib.com/law/"
    cookies = None
    
    async def fetch_announcements(self, date_filter=None):
        """
        Fetch announcements from Law Library website.

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
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/140.0.0.0 Safari/537.36",
                    'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Cookie': 'ASPSESSIONIDACBDDQBA=EKAMGOBBMGEFEPDCPBLMAACL'
            })

            await page.goto(self.LIST_URL, timeout=60000)
            await page.wait_for_load_state('domcontentloaded')

            # Wait for dynamic content
            await page.wait_for_timeout(3000)

            # Get page content
            content = await page.content()
            soup = BeautifulSoup(content, 'html.parser')
            # Find announcement sections - look for the main content areas
            # The site has multiple sections: latest national laws, local regulations, etc.
            sections = soup.find('body').find('div',class_='w').find('ul',class_='line2')

            # Also look for direct links in the HTML
            law_links = sections.find_all('a', href=lambda x: x and 'law_view.asp?id=' in x)

            processed_links = set()

            for link_elem in law_links:
                try:
                    link = link_elem.get('href')
                    if link and 'law_view.asp?id=' in link:
                        if not link.startswith('http'):
                            link = self.BASE_URL + '/law/' + link.lstrip('/')

                        if link in processed_links:
                            continue
                        processed_links.add(link)

                        # Get the text content around this link
                        parent = link_elem.parent
                        if parent:
                            text_content = parent.get_text().strip()
                            lines = [line.strip() for line in text_content.split('\n') if line.strip()]

                            # Extract title, date, and issuing unit
                            title = link_elem.get_text().strip()
                            date = None
                            issuing_unit = None

                            # Look for date pattern (YYYY-MM-DD or YYYY-M-D)
                            for line in lines:
                                if '—' in line:
                                    line = line.split('—')[-1].strip()
                                if '-' in line and len(line.split('-')) >= 3:
                                    try:
                                        # Validate date format
                                        date_parts = line.split('-')
                                        if len(date_parts) == 3:
                                            year, month, day = date_parts
                                            if len(year) == 4 and year.isdigit() and month.isdigit() and day.isdigit():
                                                date = f"{year}-{int(month):02d}-{int(day):02d}"
                                                break
                                        elif len(date_parts) == 4:
                                            _, year, month, day = date_parts
                                            if len(year) == 4 and year.isdigit() and month.isdigit() and day.isdigit():
                                                date = f"{year}-{int(month):02d}-{int(day):02d}"
                                                break
                                    except:
                                        continue

                            # Extract issuing unit (usually appears after date)
                            if date and len(lines) > 1:
                                for i, line in enumerate(lines):
                                    if date in line:
                                        # Look for the next line that might contain the issuing unit
                                        if i + 1 < len(lines):
                                            next_line = lines[i + 1]
                                            if next_line and not next_line.replace('-', '').replace('/', '').isdigit():
                                                issuing_unit = next_line
                                                break

                            # If we couldn't extract from surrounding text, try to get from the link text
                            if not title or title == link:
                                # Look for the actual title in the parent element
                                title_elem = parent.find('a')
                                if title_elem:
                                    title = title_elem.get_text().strip()

                            # Apply date filter if provided
                            if date_filter and date != date_filter:
                                continue

                            if title and date:
                                announcements.append({
                                    'date': date,
                                    'title': title,
                                    'link': link
                                })

                except Exception as e:
                    self.logger.error(f"Error parsing announcement link: {e}")
                    continue
            
            # self.cookies = await context.cookies() # Context is shared, no need to save manually unless needed elsewhere
            await page.close()

        except Exception as e:
            self.logger.error(f"Error fetching Law Library announcements: {e}")

        return announcements

    async def parse_announcement(self, link, attachment_folder, default_filename=None):
        """
        Parse Law Library announcement detail page.

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

            await page.goto(link, timeout=60000)
            await page.wait_for_load_state('domcontentloaded')

            # Wait for dynamic content
            await page.wait_for_timeout(2000)

            # Get page content
            page_content = await page.content()
            soup = BeautifulSoup(page_content, 'html.parser')

            # Extract the main content - look for the regulation text
            # The content is usually in a div or directly in the body
            content_div = soup.find('div', class_=lambda x: x and ('content' in x or 'main' in x))
            if not content_div:
                # Look for any div with substantial text content
                all_divs = soup.find_all('div')
                for div in all_divs:
                    text = div.get_text().strip()
                    if len(text) > 500:  # Substantial content
                        content_div = div
                        break

            if content_div:
                # Remove navigation, headers, footers
                for unwanted in content_div.find_all(['nav', 'header', 'footer', 'script', 'style', 'a']):
                    if unwanted.name == 'a' and 'href' in unwanted.attrs:
                        # Keep links that might be part of content, but remove navigation links
                        href = unwanted.get('href', '')
                        if href.startswith('javascript') or href.startswith('#') or 'law-lib.com' not in href:
                            unwanted.decompose()
                        else:
                            # Replace with text only
                            unwanted.replace_with(unwanted.get_text())
                    else:
                        unwanted.decompose()

                content = content_div.get_text().strip()
            else:
                # Fallback: extract from body
                body = soup.find('body')
                if body:
                    # Remove scripts, styles, and navigation
                    for script in body.find_all(['script', 'style']):
                        script.decompose()

                    # Try to find the main content area
                    text_blocks = []
                    for element in body.find_all(['p', 'div', 'span']):
                        text = element.get_text().strip()
                        if len(text) > 50:  # Meaningful text blocks
                            text_blocks.append(text)

                    content = '\n\n'.join(text_blocks)

            # Look for attachments - the site might have download links
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
            self.logger.error(f"Error parsing Law Library announcement {link}: {e}")

        return {
            'content': content,
            'attachments': attachments
        }