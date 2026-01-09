import configparser

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda

from src.classifier.LLM.boolean_output_parser import BooleanOutputParser

config = configparser.ConfigParser()
config.read('config.ini', encoding='utf-8')

# llm_config_section = 'LLM'
llm_config_section = 'GEMINI'

APIKey = config.get(llm_config_section, 'api_key')
baseURL = config.get(llm_config_section, 'baseurl')
model = config.get(llm_config_section, 'model')
llm = ChatOpenAI(api_key=APIKey, base_url=baseURL, model=model, temperature=0.2)

predictPrompt = ChatPromptTemplate.from_messages([
    ("system", """
     You are an expert at analyzing news articles for a financial institution.
     Your task is to determine whether a new announcement contains information that is 
     valuable to specific departments within the institution based on their unique roles and responsibilities.
        Consider the following departments and their functions:
"""),("human", """
        department descriptions: {department_descriptions}
      #END of department descriptions
        announcement text: {ann_text}
      #END of announcement text
      Please analyze the announcement text in relation to each department's description.
      Answer "True" if the announcement contains information relevant to this department's functions, 
      otherwise answer "False".
      Think carefully and provide your answer.
""")
     ])| llm | BooleanOutputParser(true_val="True", false_val="False")