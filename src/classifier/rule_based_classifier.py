# Import packages
import pandas as pd
import re
import os
import logging
from collections import Counter, defaultdict
from markitdown import MarkItDown
from src.logging_config import setup_logging

# Initialize logging
setup_logging()

logger = logging.getLogger(__name__)

# ====================
# 設定參數
# ====================
# input_file = "法令變動情形彙整表_23&24年含內文0707.xlsx"
# output_file = "分類結果_2023_2025.xlsx"
rule_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'static', 'knowledge', 'rule.xlsx'))
if not os.path.isfile(rule_file):
    raise FileNotFoundError(f"Rule file not found: {rule_file}")
# sheet_years = ['2023', '2024', '2025']
exclude_depts = {
    '總公司', '稽核部', '6050HA0000', '陳淑芳', '元大保經', '全公司',
    '各部室', '張詩雅', '6010J003', 'Yuanta', 'ttss888', '總公司各部室'
}
# '法務部', '計量交易部', '會計部', '分公司業代'

# ====================
# 載入關鍵字與部門對應規則
# ====================

# 關鍵字對照表
keyword_dict = pd.read_excel(rule_file, sheet_name="manual_dict")
keyword_dict = keyword_dict[keyword_dict['Enable'] == 1]  # 只取 Enable=1 的列
content_keywords = defaultdict(set)
for _, row in keyword_dict.iterrows():
    k = row['關鍵字']
    v = row['相關部門']
    if pd.notna(k) and pd.notna(v):
        content_keywords[k].add(v)
md = MarkItDown(enable_plugins=False)

# 分類內文主旨至對應部門
async def classify_dept(title: str, content: str, appendix_paths: list[str]) -> set:
    '''classify announcement to department set
    title: str
    content: str
    appendix: list of str, paths to appendix files

    return: set of department
    '''
    appendix_texts = load_all_appendices(appendix_paths)
    appendix_text = '\n'.join([f"{basename}:\n{text}" for basename, text in appendix_texts.items()])
    return await _classify_ann(title, content, appendix_text)
async def _dept_by_content(text: str) -> set:
    if not isinstance(text, str):
        raise ValueError("Input text must be a string.")
    result = set()
    for keyword, depts in content_keywords.items():
        if keyword in text:
            result.update(depts)
    return result

# 根據額外規則補齊部門
def _post_process_dept_result(dept_set: set) -> set:
    """根據規則補齊部門"""
    result = dept_set.copy()
    if '財富管理部' in result:
        result.add('國際金融業務部')
    if '分公司財副' in result:
        result.update(['分公司經理人', '財務督導'])
    if '分公司業副' in result:
        result.update(['分公司經理人', '業務督導', '分公司業代'])
    return result

# 接口
async def _classify_ann(title: str, content: str, appendix: str) -> set:
    '''classify announcement to department set
    title: str
    content: str
    appendix: str 

    return: set of department
    '''
    assert isinstance(title, str) 
    assert isinstance(content, str) or isinstance(appendix, str)
    assert not ((content == '' or content == None) and appendix == ''), "content and appendix cannot be both empty"
    combined_text = f"{title}\n{content}\n{appendix}"
    raw_result = await _dept_by_content(combined_text)
    return _post_process_dept_result(raw_result)
def load_appendix_text(file_path: str) -> str:
    '''load appendix file and extract text
    file_path: str, path to the file

    return: str, extracted text
    '''
    if not isinstance(file_path, str) or not file_path:
        raise ValueError("file_path must be a non-empty string.")
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")
    try:
        if file_path.endswith('.doc'):
            return ""
        elif file_path.endswith('.odt'):
            return ""
        elif file_path.endswith('.ods'):
            return ""
        else:
            result = md.convert(file_path)
            return result.text_content
    except Exception as e:
        logger.error(f"Error processing file {file_path}: {e}")
        return ""

def load_all_appendices(file_paths: list) -> dict:
    '''load all appendix files and extract text
    file_paths: list of str, paths to the files

    return: dict, {basename: extracted_text}
    '''
    if not isinstance(file_paths, list) or not all(isinstance(p, str) for p in file_paths):
        raise ValueError("file_paths must be a list of strings.")
    result = {}
    for file_path in file_paths:
        text = load_appendix_text(file_path)
        if text:
            basename = os.path.basename(file_path)
            result[basename] = text
    return result