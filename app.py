import streamlit as st
from bs4 import BeautifulSoup
from requests_html import HTMLSession
from fpdf import FPDF
import json
import concurrent.futures
import hashlib
import time
import asyncio

# 광고 및 구독 링크의 필터링 기준 설정
FILTER_KEYWORDS = ["ads", "advertisement", "subscribe", "login", "register"]

# HTMLSession 사용을 위한 초기 설정
session = HTMLSession()

def filter_links(links):
    """광고 및 구독 링크를 필터링"""
    return [link for link in links if not any(keyword in link for keyword in FILTER_KEYWORDS)]

def scrape_content(url, retries=3):
    """해당 URL의 텍스트와 이미지 내용 크롤링, 실패 시 최대 3번까지 재시도"""
    for attempt in range(retries):
        try:
            response = session.get(url)

            # 이벤트 루프 생성 또는 기존 이벤트 루프 사용
            if not asyncio.get_event_loop().is_running():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response.html.render(timeout=20)
            else:
                response.html.render(timeout=20)

            soup = BeautifulSoup(response.html.html, 'html.parser')
            
            # 텍스트 수집
            text_content = " ".join([p.get_text() for p in soup.find_all("p")])
            
            # 이미지 링크 수집
            images = [img['src'] for img in soup.find_all("img") if 'src' in img.attrs]
            return text_content, images

        except Exception as e:
            if attempt < retries - 1:
                time.sleep(2)  # 재시도 전 대기 시간 설정
            else:
                st.error(f"{url} 크롤링 중 오류 발생: {e}")
                return None, None

def create_pdf(content):
    """텍스트와 이미지를 포함한 PDF 파일 생성"""
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    
    for page, (text, images) in enumerate(content):
        pdf.cell(200, 10, txt=f"Page {page + 1}", ln=True)
        pdf.multi_cell(0, 10, text)
        pdf.ln(10)
        
        # 이미지 추가
        for img_url in images:
            pdf.cell(0, 10, img_url, ln=True)
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

st.title("웹사이트 콘텐츠 크롤러")
st.write("특정 웹사이트의 모든 링크에서 광고 및 구독 링크를 제외한 콘텐츠를 크롤링합니다.")

url = st.text_input("웹사이트 URL을 입력하세요:")
if st.button("크롤링 시작"):
    if url:
        try:
            # 입력 URL의 모든 링크 크롤링
            main_page = session.get(url)
            main_page.html.render(timeout=20)
            soup = BeautifulSoup(main_page.html.html, 'html.parser')
            
            # 모든 링크 가져오기
            links = [a['href'] for a in soup.find_all('a', href=True)]
            links = filter_links(links)
            unique_pages = set()  # 중복 확인을 위한 집합
            
            scraped_data = []
            
            # 병렬 크롤링 수행
            with concurrent.futures.ThreadPoolExecutor() as executor:
                futures = {executor.submit(scrape_content, link if link.startswith("http") else url + link): link for link in links}
                for future in concurrent.futures.as_completed(futures):
                    link = futures[future]
                    try:
                        text, images = future.result()
                        if text or images:
                            # 중복 확인
                            page_hash = get_unique_hash(text, images)
                            if page_hash not in unique_pages:
                                unique_pages.add(page_hash)
                                scraped_data.append({"url": link, "text": text, "images": images})
                    except Exception as e:
                        st.error(f"링크 {link} 크롤링 실패: {e}")
            
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
