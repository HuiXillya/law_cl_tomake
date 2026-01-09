"""
Custom Boolean Output Parser for LangChain Core

This module provides a BooleanOutputParser class that's compatible with langchain_core,
since langchain_core doesn't include a built-in BooleanOutputParser.
"""

from langchain_core.output_parsers import BaseOutputParser
from langchain_core.exceptions import OutputParserException
from typing import Any
from pydantic import Field


class BooleanOutputParser(BaseOutputParser[bool]):
    """
    Custom boolean output parser for langchain_core.
    
    Parses LLM output text into boolean values based on specified true/false strings.
    """
    
    true_val: str = Field(default="True")
    false_val: str = Field(default="False")
    
    def __init__(self, true_val: str = "True", false_val: str = "False"):
        """
        Initialize the BooleanOutputParser.
        
        Args:
            true_val (str): String that represents True. Default is "True".
            false_val (str): String that represents False. Default is "False".
        """
        super().__init__()
        self.true_val = true_val
        self.false_val = false_val

    def parse(self, text: str) -> bool:
        """
        Parse a string into a boolean value.
        
        Args:
            text (str): The text to parse.
            
        Returns:
            bool: True if text matches true_val, False if text matches false_val.
            
        Raises:
            OutputParserException: If text doesn't match either true_val or false_val.
        """
        cleaned_text = text.strip().upper()
        true_upper = self.true_val.upper()
        false_upper = self.false_val.upper()
        
        if  (true_upper in cleaned_text and false_upper in cleaned_text)\
            or (true_upper not in cleaned_text and false_upper not in cleaned_text):
            raise OutputParserException(
                f"BooleanOutputParser expected output value to either be "
                f"'{self.true_val}' or '{self.false_val}' (case-insensitive). "
                f"\n Received '{text.strip()}'."
            )
        
        return true_upper in cleaned_text

    @property
    def _type(self) -> str:
        """Return the type identifier for this parser."""
        return "boolean_output_parser"

    def get_format_instructions(self) -> str:
        """
        Get format instructions for the LLM to follow.
        
        Returns:
            str: Instructions for the LLM on how to format boolean output.
        """
        return (
            f"Your output should be exactly '{self.true_val}' for true "
            f"or '{self.false_val}' for false. Do not include any other text."
        )