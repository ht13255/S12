# /web_scraper_app.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF
import streamlit as st
from urllib.parse import urljoin
import os
import re

# 모든 페이지를 탐색하여 기사 링크를 수집하는 함수
def get_all_article_links(base_url, session):
    all_links = []
    next_page_url = base_url

    while next_page_url:
        response = session.get(next_page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재 페이지의 모든 기사 링크 수집
        page_links = [a['href'] for a in soup.select('a[href]') if 'href' in a.attrs]
        page_links = [urljoin(base_url, link) for link in page_links if link.startswith('/') or link.startswith(base_url)]
        
        # 불필요한 링크 제거
        unwanted_keywords = ["instagram", "subscribe", "ads", "academy"]
        page_links = [link for link in page_links if not any(keyword in link for keyword in unwanted_keywords)]
        
        all_links.extend(page_links)

        # 다음 페이지 URL 찾기
        next_page = soup.find("a", string="Next") or soup.find("a", string="다음")  # "Next"나 "다음"을 기반으로 페이지를 넘김
        next_page_url = urljoin(base_url, next_page['href']) if next_page else None

    return list(set(all_links))  # 중복 링크 제거

# 각 기사 본문을 추출하는 함수
def fetch_article_content(url, session):
    response = session.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 기사 본문 찾기
    paragraphs = soup.find_all("p")
    content = "\n".join([para.get_text() for para in paragraphs])
    return content

# PDF 파일 저장 (UTF-8 지원)
def save_to_pdf(contents, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)

    # 모든 기사 내용을 PDF에 추가
    for content in contents:
        for line in content.split("\n"):
            pdf.cell(200, 10, txt=line.encode('latin-1', 'replace').decode('latin-1'), ln=True)
        pdf.ln(10)  # 기사 간 간격 추가

    pdf.output(output_path)

# Streamlit 앱
def main():
    st.title("웹 스크래퍼 (모든 페이지 크롤링)")

    # URL 입력 받기
    base_url = st.text_input("분석할 웹사이트의 URL을 입력하세요", value="https://learning.coachesvoice.com/category/analysis/")
    if st.button("크롤링 시작"):
        st.write(f"{base_url}에서 모든 페이지의 링크를 분석 중입니다.")
        
        # 세션을 통한 쿠키 우회 설정
        session = requests.Session()
        session.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36"})
        
        # 모든 페이지의 링크 분석 및 추출
        article_links = get_all_article_links(base_url, session)
        st.write(f"{len(article_links)}개의 유효한 기사를 찾았습니다.")
        
        # 기사 내용 수집
        data = []
        contents = []
        
        for link in article_links:
            content = fetch_article_content(link, session)
            data.append({"url": link, "content": content})
            contents.append(content)  # PDF로 결합할 내용 저장
        
        # 모든 기사 내용을 하나의 PDF로 저장
        pdf_path = "all_articles.pdf"
        save_to_pdf(contents, pdf_path)

        # CSV로 저장
        csv_path = "articles.csv"
        pd.DataFrame(data).to_csv(csv_path, index=False)

        # 다운로드 링크 제공
        st.write("다운로드 옵션:")
        with open(csv_path, "rb") as f:
            st.download_button("CSV 파일 다운로드", f, file_name="articles.csv")

        with open(pdf_path, "rb") as f:
            st.download_button("전체 PDF 파일 다운로드", f, file_name="all_articles.pdf")

# requirements.txt 파일 생성
with open("requirements.txt", "w") as f:
    f.write("requests\nbeautifulsoup4\npandas\nfpdf\nstreamlit\n")

# Streamlit 앱 실행
if __name__ == "__main__":
    main()
