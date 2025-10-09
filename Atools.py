import json_repair
from openai import OpenAI
import re
import copy
import requests
import json
import random
from tqdm import trange
import os
import dashscope
import time
from dotenv import load_dotenv
load_dotenv()
import logging
from typing import Any, Dict

from firecrawl.firecrawl import FirecrawlApp
from Aprompts import Quality_sys_prompt, Quality_user_prompt, FACT_CHECK_SYS_PROMPT, FACT_CHECK_USER_PROMPT, REPEATABILITY_SYSTEM_PROMPT, REPEATABILITY_USER_PROMPT

APIKEY = os.environ.get("OPENAI_API_KEY")
APIBASE = os.environ.get("OPENAI_API_BASE")

client = OpenAI(
    api_key=APIKEY,
    base_url=APIBASE,
    timeout=600,
)



class WebScrapingJinaTool:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("JINA_API_KEY")
        if not self.api_key:
            raise ValueError("Jina API key not provided! Please set JINA_API_KEY environment variable.")

    def __call__(self, url: str) -> Dict[str, Any]:
        try:
            jina_url = f'https://r.jina.ai/{url}'
            headers = {
                "Accept": "application/json",
                'Authorization': self.api_key,
                'X-Timeout': "60000",
                "X-With-Generated-Alt": "true",
            }
            response = requests.get(jina_url, headers=headers)

            if response.status_code != 200:
                raise Exception(f"Jina AI Reader Failed for {url}: {response.status_code}")

            response_dict = response.json()

            return {
                'url': response_dict['data']['url'],
                'title': response_dict['data']['title'],
                'description': response_dict['data']['description'],
                'content': response_dict['data']['content'],
                'publish_time': response_dict['data'].get('publishedTime', 'unknown')
            }

        except Exception as e:
            return {
                'url': url,
                'content': '',
                'error': str(e)
            }

MODEL_GENERATION_CONFIG = {
    # "incremental_output": True,
    # "stream": True,
    "temperature": 0.6,
    "top_p": 0.8,
    "top_k": 20,
    # "enable_thinking": True,
    # "thinking_budget": 3000,
    "enable_thinking": False,
}
def load_response(response):
    try:
        return response.choices[0].message.content
    except:
        return response


class SearchAgent:
    def __init__(self, num_limit_pages: int = 3):
        self.NUM_LIMIT_PAGES = num_limit_pages
        self.app = FirecrawlApp(api_key=os.getenv("FIRECRAWL_KEY"))
        self._jina_api_key = os.environ.get("JINA_API_KEY")
        self._jina_tool = None

    def _get_jina_tool(self) -> WebScrapingJinaTool:
        if self._jina_tool is None:
            self._jina_tool = WebScrapingJinaTool(api_key=self._jina_api_key)
        return self._jina_tool

    def search(self, query, provider: str = 'firecrawl'):
        """
        Search for the given query.
        - provider='firecrawl': uses Firecrawl search (default)
        - provider='jina': not supported (returns None)
        """
        if provider != 'firecrawl':
            print("Search with provider '%s' is not supported. Falling back to Firecrawl.", provider)
        try:
            search_results = self.app.search(
                query = query + " site:wikipedia.org",
                params={
                    "limit": self.NUM_LIMIT_PAGES,
                }
            )

            if search_results['success']:
                return search_results
            else:
                return None
        except Exception as e:
            print(f"Error searching {query}: {e}")
            return None

    def scrape(self, url, provider: str = 'firecrawl'):
        """
        Scrape the given URL using the specified provider.
        - provider='firecrawl': use Firecrawl to scrape markdown
        - provider='jina': use Jina Reader to fetch page content
        """
        if provider == 'jina':
            try:
                jina_tool = self._get_jina_tool()
                result = jina_tool(url)
                if 'content' in result and result.get('content'):
                    return result['content']
                return None
            except Exception as e:
                print(f"Error scraping with Jina {url}: {e}")
                return None

        # default: firecrawl
        try:
            result = self.app.scrape_url(
                url,
                params={
                    'formats': ['markdown'],
                    'waitFor': 1000,
                    'timeout': 20000,
                }
            )
            if result['metadata']["statusCode"] == 200:
                return self.remove_markdown_links(result["markdown"])
            else:
                return None
        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return None
    
    def remove_markdown_links(self, markdown_text: str) -> str:
        """
        Remove links from markdown text, keeping only the link text.
        
        Args:
            markdown_text (str): The markdown text to process
            
        Returns:
            str: Markdown text with links removed, preserving only the link text
        """
        
        pattern = r'\((http?://[^)]*)\)'
        cleaned_text = re.sub(pattern, '', markdown_text)
        
        return cleaned_text


def extract_numbered_sentences(text):
    pattern = r'[^。.!?]*\[\[\d+(?:,\d+)*\]\][^。.!?]*[。.!?]'
    sentences = re.findall(pattern, text)
    return sentences

def check_factual(sentence,url_markdown):
    completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": FACT_CHECK_SYS_PROMPT},
                {"role": "user", "content": FACT_CHECK_USER_PROMPT.format(input=sentence,url_markdown=url_markdown)}
            ]
        )
    try:
        result = json_repair.loads(load_response(completion))
        if isinstance(result, list):
            return result[-1]
        return result
    except:
        return {"error": "Failed to parse JSON response", "raw_response": load_response(completion)}


def split_paragraphs(markdown_text,regular_expression=r'\n\s*\n'):
    paragraphs = re.split(regular_expression, markdown_text.strip())
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    return paragraphs


def extract_first_level_headings(markdown_content,pattern=r'^## .*$'):
    """
    Extract first-level headings from a markdown text.
    First-level headings are those that start with '# ' followed by the heading text.
    
    Args:
        text (str): The markdown text to process
        
    Returns:
        list: A list of first-level headings
        
    Usage:
        headings, sections, sections_headings, sections_with_headings = extract_first_level_headings(report)
        
    """
    # Pattern to match first-level headings
    # pattern = r'\*\*\d+.*?\*\*'
    # pattern = r'^## .*$'    
    # Find all matches
    headings = re.findall(pattern, markdown_content, re.MULTILINE)
    
    # return headings

    sections = []
    current_pos = 0
    sections_with_headings = []
    sections_headings = []
    first_heading_pos = markdown_content.find(headings[0])
    if first_heading_pos > 0:
        section0 = markdown_content[:first_heading_pos].strip()
        sections.append(section0)
        sections_headings.append("Beginning of the report")
        sections_with_headings.append("Beginning of the report\n" + section0)

    for i, heading in enumerate(headings):
        heading_pos = markdown_content.find(heading, current_pos)
        
        if heading_pos != -1:
            if current_pos > 0:
                section_content = markdown_content[current_pos:heading_pos].strip()
                sections.append(section_content)
                sections_headings.append(headings[i-1])
                sections_with_headings.append(headings[i-1] + "\n" + section_content)
                
            current_pos = heading_pos + len(heading)

    if current_pos < len(markdown_content):
        last_section = markdown_content[current_pos:].strip()
        sections.append(last_section)
        sections_headings.append(headings[-1])
        sections_with_headings.append(headings[-1] + "\n" + last_section)

    return headings, sections, sections_headings, sections_with_headings

def judge_repeatability(markdown_content):

    _, sections, sections_headings, sections_with_headings = extract_first_level_headings(markdown_content)
    passage_list = sections
    assert isinstance(passage_list, list), "input MUST be a list"
    paragraphs_str = ''
    for i in range(len(passage_list)):
        paragraphs_str += f'Paragraph [{str(i)}]:\n'
        paragraphs_str += passage_list[i]
        paragraphs_str += '\n'

    completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
            {"role": "system", "content": REPEATABILITY_SYSTEM_PROMPT},
            {"role": "user", "content": REPEATABILITY_USER_PROMPT.format(input=paragraphs_str)}
        ]
    )


    try:
        result = json_repair.loads(load_response(completion))

        repeat_found = result['repetitions_found']


        if repeat_found is not None:
            try:
                for repeat_item in repeat_found:
                    repeat_content = repeat_item['repeated_content']
                    repeat_paragraphs = repeat_item['paragraphs']
                    
                    repeated_passages = []
                    for para_idx in repeat_paragraphs:
                        if para_idx < len(passage_list):
                            repeated_passages.append(passage_list[para_idx])
                    
                    repeat_item['paragraphs_save'] = repeated_passages
                    if 'repeat_found_save' not in locals():
                        repeat_found_save = []
                    repeat_found_save.append(repeat_item)

                result['repetitions_found'] = repeat_found_save


            except Exception as e:
                print("Error: ",e)
                return {"error": "Failed to parse repeat_found", "raw_response": load_response(completion)}
        


        return result
    except Exception as e:
        return {"error": "Failed to parse JSON response", "raw_response": load_response(completion)}


def judge_repeatability_pair(passage1,passage2):
    completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": REPEATABILITY_SYSTEM_PROMPT},
                {"role": "user", "content": REPEATABILITY_USER_PROMPT.format(para1=passage1,para2=passage2)}
            ]
        )
    try:
        result = json_repair.loads(load_response(completion))
    except:
        try:
            result = json_repair.loads(load_response(completion))['result']
        except:
            print("Error after retry: ",load_response(completion))
            result = None
    return result


def judge_quality(query,markdown_content):
    completion = client.chat.completions.create(
            model="gpt-4o",
            messages=[
            {"role": "system", "content": Quality_sys_prompt},
            {"role": "user", "content": Quality_user_prompt.format(question = query, paragraph = markdown_content)}
        ]
    )
    # print("completion: ",completion)
    result = json_repair.loads(load_response(completion))
    return result


def generate_random_pair_with_label(sections_with_headings_CN,pair_nums = 10):
    """

    """
    length = len(sections_with_headings_CN)
    # Adjust pair_nums to not exceed maximum possible pairs
    max_pairs = (length * (length - 1)) // 2  # Maximum possible pairs for length elements
    pair_nums = min(pair_nums, max_pairs)
    # Generate all possible pairs where a < b < length
    all_possible_pairs = []
    for a in range(length-1):
        for b in range(a+1, length):
            all_possible_pairs.append((a,b))
            
    # Randomly sample pair_nums pairs if we have enough pairs
    results = []
    if len(all_possible_pairs) > pair_nums:
        sampled_pairs = random.sample(all_possible_pairs, pair_nums)
        for pair in sampled_pairs:
            results.append((pair, -2, []))
    else:
        # If we don't have enough pairs, use all available pairs
        for pair in all_possible_pairs:
            results.append((pair, -2, []))
    
    return results

