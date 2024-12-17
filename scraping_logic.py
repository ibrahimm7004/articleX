import os
import random
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
from newspaper import Article, ArticleException
import re

# List of user agents to rotate to avoid being blocked by Google:
user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.101 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.64",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 OPR/77.0.4054.277"
]


def get_domain(url):
    parsed_url = urlparse(url)
    return parsed_url.netloc


def get_search_results(topic, num_results=5):
    search_results = []
    headers = {'User-Agent': random.choice(user_agents)}
    base_url = "https://www.google.com/search"
    params = {'q': topic, 'num': num_results}

    response = requests.get(base_url, params=params, headers=headers)

    if response.status_code == 200:
        soup = BeautifulSoup(response.content, 'html.parser')
        links = soup.select('div.tF2Cxc a')

        for link in links:
            url = link['href']
            if len(search_results) < num_results:
                if check_article_existence(url):
                    search_results.append(url)

    return search_results[:num_results]


def check_article_existence(url):
    try:
        article = Article(url)
        article.download()
        article.parse()
        return url if article.is_parsed else None
    except ArticleException:
        return None


def get_first_paragraph(url, min_words=20):
    irrelevant_strings = [
        "dont have permission", "don't have permission", "JavaScript and cookies", "<<", ">>",
        "403 - Forbidden", "Access to this page is forbidden", "It looks like you",
        "could not be decoded", "site requires", "gateway", "terms & conditions"
    ]
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')
    paragraphs = soup.find_all('p')

    for paragraph in paragraphs:
        text = paragraph.get_text().strip()
        if len(text.split()) >= min_words and is_xml_compatible(text):
            if not any(irrelevant_str.lower() in text.lower() for irrelevant_str in irrelevant_strings):
                return text

    return None


def is_xml_compatible(text):
    return all(32 <= ord(char) <= 126 for char in text)


def replace_spaces(input_string, c):
    return ''.join(c if char == ' ' else char for char in input_string)


def create_folder():
    folder_path = os.path.join(os.getcwd(), 'scraped_content')
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
    return folder_path


def create_pdf_file(topic, file_directory):
    base_filename = replace_spaces(topic, '_')
    pdf_file_path = os.path.join(file_directory, f"{base_filename}.pdf")

    count = 0
    while os.path.exists(pdf_file_path):
        count += 1
        pdf_file_path = os.path.join(
            file_directory, f"{base_filename}[{count}].pdf")

    return pdf_file_path


def append_to_pdf(paras, pdf, results):
    pdf.set_font("Arial", size=12)
    for i, url in enumerate(results, start=1):
        if check_article_existence(url):
            first_paragraph = get_first_paragraph(url)
            if first_paragraph and first_paragraph not in paras:
                cleaned_paragraph = re.sub(
                    r'\[.*?\]|<.*?>', '', first_paragraph)

                if not contains_invalid_characters(cleaned_paragraph) and not contains_high_digit_percentage(cleaned_paragraph):
                    pdf.set_font("Arial", "B", 12)
                    pdf.multi_cell(0, 10, f"URL {i}:", align='L')
                    pdf.set_text_color(0, 0, 255)
                    pdf.set_font("Arial", "U", 12)
                    pdf.multi_cell(0, 10, url, align='L')
                    pdf.set_text_color(0, 0, 0)
                    pdf.set_font("Arial", size=12)
                    pdf.multi_cell(0, 10, cleaned_paragraph, align='L')
                    paras.add(cleaned_paragraph)
                    pdf.ln(10)


def contains_invalid_characters(para):
    return (
        para.count('<') > 1 or para.count('>') > 1 or para.count('#') > 1 or
        para.count(
            '/') > 2 or para.count('\\') > 2 or para.count('[') > 2 or para.count(']') > 2
    )


def contains_high_digit_percentage(para):
    total_chars = len(para)
    digit_chars = sum(char.isdigit() for char in para)
    return (digit_chars / total_chars * 100) >= 30 if total_chars > 0 else False
