# /web_scraper_app.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
from fpdf import FPDF
import streamlit as st
from urllib.parse import urljoin
import os
import re

# 모든 페이지의 링크를 추출하는 함수
def get_all_links(base_url):
    links = []
    next_page_url = base_url

    while next_page_url:
        response = requests.get(next_page_url)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 현재 페이지의 기사 링크 추출
        page_links = [a['href'] for a in soup.select('a[href]') if 'href' in a.attrs]
        page_links = [urljoin(base_url, link) for link in page_links if link.startswith('/') or link.startswith(base_url)]
        
        # 불필요한 링크 제거
        unwanted_keywords = ["instagram", "subscribe", "ads", "academy"]
        page_links = [link for link in page_links if not any(keyword in link for keyword in unwanted_keywords)]
        
        links.extend(page_links)

        # 다음 페이지 URL 찾기 (예: Next 버튼)
        next_page = soup.find("a", string="Next") or soup.find("a", string="다음")  # "Next"나 "다음"을 기반으로 페이지를 넘김
        next_page_url = urljoin(base_url, next_page['href']) if next_page else None

    return list(set(links))  # 중복 링크 제거

# 기사 본문 추출 함수
def fetch_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 기사 본문 찾기
    paragraphs = soup.find_all("p")
    content = "\n".join([para.get_text() for para in paragraphs])
    return content

# 안전한 파일 이름 생성 함수
def safe_filename(url):
    filename = url.split("/")[-1] or "article"
    filename = re.sub(r'\W+', '_', filename)  # 알파벳, 숫자, 밑줄만 허용
    return f"{filename}.pdf"

# PDF 파일 저장
def save_to_pdf(content, output_path):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    
    # 텍스트 줄 단위로 PDF에 추가
    for line in content.split("\n"):
        pdf.cell(200, 10, txt=line, ln=True)
    
    pdf.output(output_path)

# Streamlit 앱
def main():
    st.title("웹 스크래퍼")

    # URL 입력 받기
    base_url = st.text_input("분석할 웹사이트의 URL을 입력하세요", value="https://learning.coachesvoice.com/category/analysis/")
    if st.button("크롤링 시작"):
        st.write(f"{base_url}에서 모든 페이지의 링크를 분석 중입니다.")
        
        # 모든 페이지의 링크 분석 및 추출
        links = get_all_links(base_url)
        st.write(f"{len(links)}개의 유효한 기사를 찾았습니다.")
        
        # 기사 내용 수집
        data = []
        pdf_files = []
        
        for link in links:
            content = fetch_article_content(link)
            data.append({"url": link, "content": content})
            
            # PDF로 저장
            pdf_filename = safe_filename(link)
            pdf_path = f"articles/{pdf_filename}"
            os.makedirs("articles", exist_ok=True)  # articles 디렉토리 생성
            save_to_pdf(content, pdf_path)
            pdf_files.append(pdf_path)
        
        # CSV로 저장
        csv_path = "articles.csv"
        pd.DataFrame(data).to_csv(csv_path, index=False)

        # 다운로드 링크 제공
        st.write("다운로드 옵션:")
        with open(csv_path, "rb") as f:
            st.download_button("CSV 파일 다운로드", f, file_name="articles.csv")
        
        # PDF 파일을 개별적으로 다운로드 제공
        for pdf_file in pdf_files:
            with open(pdf_file, "rb") as f:
                st.download_button(f"{pdf_file} 다운로드", f, file_name=pdf_file)

# requirements.txt 파일 생성
with open("requirements.txt", "w") as f:
    f.write("requests\nbeautifulsoup4\npandas\nfpdf\nstreamlit\n")

# Streamlit 앱 실행
if __name__ == "__main__":
    main()
