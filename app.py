# /dynamic_web_scraper_app.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import pdfkit
import json
import streamlit as st
from urllib.parse import urljoin
import os

# wkhtmltopdf 경로 설정
# 로컬 실행 시에는 시스템 경로를 사용하고, GitHub에서는 특정 경로로 설정할 수 있도록 합니다.
if os.path.exists("/usr/local/bin/wkhtmltopdf"):
    pdfkit_config = pdfkit.configuration(wkhtmltopdf="/usr/local/bin/wkhtmltopdf")
else:
    pdfkit_config = None  # 로컬 환경에서 wkhtmltopdf가 PATH에 있을 경우 사용

# URL 분석 후 규칙을 설정하여 링크를 추출하는 함수
def analyze_and_get_links(base_url):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 기본 링크 추출 규칙 설정
    link_selector = 'a[href]'
    
    # 사이트별 패턴을 확인하고 설정
    if "coachesvoice" in base_url:
        unwanted_selectors = ["instagram", "subscribe", "ads", "academy"]
    elif "the-footballanalyst" in base_url:
        unwanted_selectors = ["instagram", "subscribe", "ads"]
    else:
        unwanted_selectors = ["instagram", "subscribe", "ads"]
    
    # 스크래핑된 링크를 필터링하여 유효한 링크만 남기기
    links = [a['href'] for a in soup.select(link_selector) if 'href' in a.attrs]
    links = [urljoin(base_url, link) for link in links if link.startswith('/') or link.startswith(base_url)]
    links = [link for link in links if not any(unwanted in link for unwanted in unwanted_selectors)]
    
    return links

# 기사 본문을 추출하는 함수
def fetch_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 주요 기사 내용을 포함하는 태그 추출
    article_tags = soup.find_all(["article", "div", "section"], recursive=True)
    content = ""
    
    for tag in article_tags:
        paragraphs = tag.find_all("p")
        if len(paragraphs) > 3:  # 실제 기사 내용을 가진 경우
            content = "\n".join([para.text for para in paragraphs])
            break
    
    return content

# PDF로 저장
def save_to_pdf(content, output_path):
    # wkhtmltopdf 경로가 지정된 경우에만 config 인자를 전달합니다.
    pdfkit.from_string(content, output_path, configuration=pdfkit_config)

# CSV 또는 JSON으로 저장
def save_to_ml_file(data, output_path, format="csv"):
    if format == "csv":
        pd.DataFrame(data).to_csv(output_path, index=False)
    elif format == "json":
        with open(output_path, 'w') as f:
            json.dump(data, f)

# Streamlit 앱
def main():
    st.title("동적 웹 스크래퍼")
    
    # URL 입력 받기
    base_url = st.text_input("분석할 웹사이트의 URL을 입력하세요", value="https://learning.coachesvoice.com/category/analysis/")
    if st.button("크롤링 시작"):
        st.write(f"{base_url}에서 링크를 분석 중입니다.")
        
        # 링크 분석 및 추출
        links = analyze_and_get_links(base_url)
        st.write(f"{len(links)}개의 유효한 기사를 찾았습니다.")
        
        # 기사 내용 수집
        data = []
        for link in links:
            content = fetch_article_content(link)
            data.append({"url": link, "content": content})
            
            # PDF로 각 기사를 저장
            pdf_path = f"articles/{link.split('/')[-1]}.pdf"
            save_to_pdf(content, pdf_path)
        
        # 다운로드 옵션 제공
        st.write("다운로드 옵션:")
        save_to_ml_file(data, "articles.csv")
        st.download_button("CSV 파일 다운로드", "articles.csv")
        
        st.download_button("PDF 파일 다운로드", pdf_path)

# requirements.txt 파일 생성
with open("requirements.txt", "w") as f:
    f.write("requests\nbeautifulsoup4\npandas\npdfkit\nstreamlit\n")

# Streamlit 앱 실행
if __name__ == "__main__":
    main()

