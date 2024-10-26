# 파일명: streamlit_app.py

import streamlit as st
from bs4 import BeautifulSoup
import aiohttp
import asyncio
from fpdf import FPDF
import json
import hashlib
from urllib.parse import urljoin

# 광고 및 구독 링크의 필터링 기준 설정
FILTER_KEYWORDS = ["ads", "advertisement", "subscribe", "login", "register"]

def filter_links(links):
    """광고 및 구독 링크를 필터링"""
    return [link for link in links if not any(keyword in link for keyword in FILTER_KEYWORDS)]

async def fetch_content(url):
    """해당 URL의 HTML을 가져와 파싱 및 텍스트, 이미지 크롤링"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 모든 텍스트 수집
                text_content = "\n".join([element.get_text() for element in soup.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'])])
                
                # 이미지 링크 수집
                images = [img['src'] for img in soup.find_all("img") if 'src' in img.attrs]
                return text_content, images

    except Exception as e:
        st.error(f"{url} 크롤링 중 오류 발생: {e}")
        return None, None

async def fetch_main_page_links(url):
    """메인 페이지에서 모든 링크를 가져옴"""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                # 모든 링크 가져오기
                links = [urljoin(url, a['href']) for a in soup.find_all('a', href=True)]
                return filter_links(links)

    except Exception as e:
        st.error(f"메인 페이지에서 링크를 가져오는 중 오류 발생: {e}")
        return []

def create_pdf(content):
    """텍스트와 이미지를 포함한 PDF 파일 생성"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for page, (text, images) in enumerate(content):
        pdf.cell(200, 10, txt=f"Page {page + 1}", ln=True)
        pdf.multi_cell(0, 10, text.encode('latin-1', 'replace').decode('latin-1'))  # UTF-8 문자를 대체하여 처리
        pdf.ln(10)
        
        # 이미지 추가
        for img_url in images:
            pdf.cell(0, 10, img_url.encode('latin-1', 'replace').decode('latin-1'), ln=True)
            pdf.ln(10)
            
    pdf_output = "scraped_content.pdf"
    pdf.output(pdf_output)
    return pdf_output

def create_json(content):
    """크롤링 데이터를 JSON 파일로 저장"""
    json_output = "scraped_content.json"
    with open(json_output, "w", encoding="utf-8") as f:
        json.dump(content, f, ensure_ascii=False, indent=4)
    return json_output

def get_unique_hash(text, images):
    """중복 확인을 위한 고유 해시 생성"""
    combined_content = text + "".join(images)
    return hashlib.md5(combined_content.encode()).hexdigest()

async def scrape_all_links(url):
    """메인 페이지에서 모든 링크를 가져와 각 링크에 직접 접속하여 콘텐츠 크롤링"""
    links = await fetch_main_page_links(url)
    tasks = [fetch_content(link) for link in links]
    results = await asyncio.gather(*tasks)
    
    unique_pages = set()
    scraped_data = []

    for link, (text, images) in zip(links, results):
        if text or images:
            # 중복 확인
            page_hash = get_unique_hash(text, images)
            if page_hash not in unique_pages:
                unique_pages.add(page_hash)
                scraped_data.append({"url": link, "text": text, "images": images})

    return scraped_data

st.title("웹사이트 콘텐츠 크롤러")
st.write("특정 웹사이트의 모든 링크에서 광고 및 구독 링크를 제외한 콘텐츠를 크롤링합니다.")

url = st.text_input("웹사이트 URL을 입력하세요:")
if st.button("크롤링 시작"):
    if url:
        try:
            # 비동기 크롤링 실행
            scraped_data = asyncio.run(scrape_all_links(url))
            
            # PDF 및 JSON 생성
            pdf_path = create_pdf([(data["text"], data["images"]) for data in scraped_data])
            json_path = create_json(scraped_data)
            
            # 다운로드 링크 제공
            st.success("크롤링이 완료되었습니다.")
            st.download_button(label="PDF 다운로드", data=open(pdf_path, "rb"), file_name="scraped_content.pdf", mime="application/pdf")
            st.download_button(label="JSON 다운로드", data=open(json_path, "rb"), file_name="scraped_content.json", mime="application/json")
        
        except Exception as e:
            st.error(f"크롤링에 실패했습니다: {e}")
    else:
        st.warning("유효한 URL을 입력하세요.")
