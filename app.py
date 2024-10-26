# /dynamic_web_scraper_app.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF
import json
import streamlit as st
from urllib.parse import urljoin
import os
import re

# URL 분석 후 규칙을 설정하여 모든 페이지의 링크를 추출하는 함수
def analyze_and_get_links(base_url):
    links = []
    next_page_url = base_url

    while next_page_url:
        response = requests.get(next_page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재 페이지의 링크 추출
        page_links = [a['href'] for a in soup.select('a[href]') if 'href' in a.attrs]
        page_links = [urljoin(base_url, link) for link in page_links if link.startswith('/') or link.startswith(base_url)]
        
        # 불필요한 링크 제거
        unwanted_selectors = ["instagram", "subscribe", "ads", "academy"]
        page_links = [link for link in page_links if not any(unwanted in link for unwanted in unwanted_selectors)]
        
        # 현재 페이지의 링크를 결과 리스트에 추가
        links.extend(page_links)

        # 다음 페이지 URL을 찾기 (다음/Next 버튼)
        next_page = soup.find("a", string="Next") or soup.find("a", string="다음")  # 페이지 이동 버튼 이름이 다를 경우 조정
        next_page_url = urljoin(base_url, next_page['href']) if next_page else None

    return list(set(links))  # 중복 링크 제거 후 반환

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
    
    # 유니코드 문자 대체
    content = content.encode('latin-1', 'replace').decode('latin-1')
    
    return content

# 안전한 파일 이름 생성 함수
def safe_filename(url):
    # URL에서 파일명 부분 추출하고, 알파벳, 숫자, 밑줄만 남기기
    filename = url.split("/")[-1] or "article"
    filename = re.sub(r'\W+', '_', filename)
    return f"{filename}.pdf"

# FPDF로 PDF 파일 저장
def save_to_pdf(content, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # 긴 텍스트를 여러 줄로 나눠서 PDF에 추가
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    
    pdf.output(output_path)

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
        st.write(f"{base_url}에서 모든 페이지의 링크를 분석 중입니다.")
        
        # 모든 페이지의 링크 분석 및 추출
        links = analyze_and_get_links(base_url)
        st.write(f"{len(links)}개의 유효한 기사를 찾았습니다.")
        
        # 기사 내용 수집
        data = []
        for link in links:
            content = fetch_article_content(link)
            data.append({"url": link, "content": content})
            
            # 안전한 파일 이름 생성
            pdf_path = f"articles/{safe_filename(link)}"
            os.makedirs(os.path.dirname(pdf_path), exist_ok=True)  # 디렉토리 생성
            
            # PDF로 각 기사를 저장
            save_to_pdf(content, pdf_path)
        
        # 다운로드 옵션 제공
        st.write("다운로드 옵션:")
        save_to_ml_file(data, "articles.csv")
        st.download_button("CSV 파일 다운로드", "articles.csv")
        
        st.download_button("PDF 파일 다운로드", pdf_path)

# requirements.txt 파일 생성
with open("requirements.txt", "w") as f:
    f.write("requests\nbeautifulsoup4\npandas\nfpdf\nstreamlit\n")

# Streamlit 앱 실행
if __name__ == "__main__":
    main()
