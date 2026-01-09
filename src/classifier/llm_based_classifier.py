import os
import logging
from markitdown import MarkItDown
from src.classifier.LLM.read_describe_to_decide_department import read_describe_to_decide_department
from src.classifier.rule_based_classifier import load_all_appendices

logger = logging.getLogger(__name__)

async def classify_dept(title: str, content: str, appendix_paths: list[str]) -> set:
    '''classify announcement to department set using LLM
    title: str
    content: str
    appendix: list of str, paths to appendix files
    '''
    # Combine title and content
    full_text = f"Title: {title}\nContent: {content}\n"
    
    # Process appendices
    appendix_texts = load_all_appendices(appendix_paths)
    for basename, text in appendix_texts.items():
        full_text += f"\nAppendix ({basename}):\n{text}\n"

    # Call LLM classifier
    try:
        classification_results = await read_describe_to_decide_department(full_text)
        
        # Filter departments where result is True
        result_set = {dept for dept, is_relevant in classification_results.items() if is_relevant}
        
        return result_set
    except Exception as e:
        logger.error(f"Error during LLM classification: {e}")
        return set()
