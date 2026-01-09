from abc import ABC, abstractmethod
import os
import urllib.request
import urllib.error
import urllib.parse
import ssl
import logging
import re
import mimetypes

ssl._create_default_https_context = ssl._create_unverified_context

class BaseCrawler(ABC):
    """Abstract base class for all government website crawlers"""
    DISPLAY_NAME = "未命名網站，請在子類別中設定"
    def __init__(self, browser_context=None):
        """
        Initialize the crawler.

        Args:
            browser_context: Playwright browser context for web scraping
        """
        self.browser = browser_context
        self.logger = logging.getLogger(self.__class__.__name__)

    @abstractmethod
    async def fetch_announcements(self, date_filter=None):
        """
        Fetch all announcements from the website.

        Args:
            date_filter (str, optional): Date filter in YYYY-MM-DD format

        Returns:
            list: List of dicts with keys: 'date', 'title', 'link'
        """
        pass

    @abstractmethod
    async def parse_announcement(self, link, attachment_folder,default_filename=None):
        """
        Parse a specific announcement page.

        Args:
            link (str): URL of the announcement detail page
            attachment_folder (str): Path to folder for downloading attachments

        Returns:
            dict: Dict with keys: 'content', 'attachments' (list of filenames)
        """
        pass

    def convert_roc_date(self, roc_date_str):
        """
        Convert ROC date to Gregorian date.

        ROC dates are in format like '113/09/25' or '114.09.18' (year/month/day)
        Convert year by adding 1911.

        Args:
            roc_date_str (str): ROC date string

        Returns:
            str: Gregorian date in YYYY-MM-DD format
        """
        try:
            # Handle '年', '月', '日' characters
            if '年' in roc_date_str:
                roc_date_str = roc_date_str.replace('年', '/').replace('月', '/').replace('日', '')
            # Handle both '/' and '.' separators
            if '/' in roc_date_str:
                parts = roc_date_str.split('/')
            elif '.' in roc_date_str:
                parts = roc_date_str.split('.')
            else:
                return roc_date_str

            if len(parts) == 3:
                roc_year = int(parts[0])
                month = int(parts[1])
                day = int(parts[2])
                gregorian_year = roc_year + 1911
                return f"{gregorian_year:04d}-{month:02d}-{day:02d}"
            else:
                # If not in expected format, return as-is
                return roc_date_str
        except (ValueError, IndexError):
            return roc_date_str

    def download_attachment(self, url, folder, filename, headers=None) -> tuple[bool, str]:
        """
        Download an attachment to the specified folder with the given filename.

        Args:
            url (str): URL of the attachment
            folder (str): Target folder path
            filename (str): Desired filename
            headers (dict, optional): HTTP headers to send with the request

        Returns:
            bool: True if successful, False otherwise
            str: Final filename used (may differ if extension added)
        """
        self.logger.debug(f"Downloading attachment:\n URL: {url} \n Filename: {filename}")
        try:
            os.makedirs(folder, exist_ok=True)
            
            # Sanitize filename
            filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
            
            # Create request with headers
            req_headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            if headers:
                req_headers.update(headers)

            req = urllib.request.Request(url, headers=req_headers)

            with urllib.request.urlopen(req) as response:
                final_filename = filename
                
                # If no extension provided, try to detect it
                if '.' not in filename:
                    # 1. Try Content-Disposition
                    disposition_filename = response.info().get_filename()
                    if disposition_filename:
                        _, ext = os.path.splitext(disposition_filename)
                        if ext:
                            final_filename = filename + ext
                    self.logger.debug(f"Filename after Content-Disposition check: {final_filename}")
                    # 2. Try Content-Type
                    if '.' not in final_filename:
                        content_type = response.info().get_content_type()
                        ext = mimetypes.guess_extension(content_type)
                        if ext:
                            final_filename = filename + ext
                    self.logger.debug(f"Filename after Content-Type check: {final_filename}")
                    # 3. Try URL path
                    if '.' not in final_filename:
                        path = urllib.parse.urlparse(url).path
                        base = os.path.basename(path)
                        _, ext = os.path.splitext(base)
                        if ext:
                            final_filename = filename + ext
                    self.logger.debug(f"Filename after URL path check: {final_filename}")
                # Handle filename conflicts
                filepath = os.path.join(folder, final_filename)
                base, ext = os.path.splitext(final_filename)
                counter = 1
                while os.path.exists(filepath):
                    filepath = os.path.join(folder, f"{base}({counter}){ext}")
                    final_filename = f"{base}_{counter}{ext}"
                    counter += 1

                # Save file
                with open(filepath, 'wb') as f:
                    while True:
                        chunk = response.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        
            return True,final_filename
        except (urllib.error.URLError, OSError, Exception) as e:
            self.logger.error(f"Failed to download {url}: {e}")
            return False,""