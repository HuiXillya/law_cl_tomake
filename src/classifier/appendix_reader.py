

import os
import logging
from markitdown import MarkItDown

logger = logging.getLogger(__name__)

md = MarkItDown(enable_plugins=False)

def appendix_reader(path: str) -> str:
    '''Read the content of an appendix file and return it as text.
    
    Args:
        path (str): The file path to the appendix.
    '''
    if not isinstance(path, str) or not path:
        raise ValueError("path must be a non-empty string.")
    if not os.path.isfile(path):
        raise FileNotFoundError(f"File not found: {path}")
    try:
        if path.endswith('.doc'):
            return ""
        elif path.endswith('.odt'):
            return ""
        elif path.endswith('.ods'):
            return ""
        else:
            result = md.convert(path)
            return result.text_content
    except Exception as e:
        logger.error(f"Error processing file {path}: {e}")
        return ""