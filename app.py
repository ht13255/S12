import os
import time
import json
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import streamlit as st
from bs4 import BeautifulSoup

# Streamlit 설정
st.title("렌더링된 페이지 그대로 크롤링")
st.write("브라우저로 JavaScript가 렌더링된 페이지를 크롤링하고 PDF와 JSON으로 저장합니다.")

# 기본 다운로드 폴더 설정
output_folder = 'crawled_data'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

# URL 리스트 입력
url_input = st.text_area("크롤링할 블로그 URL을 입력하세요 (줄바꿈으로 구분):")
urls = [url.strip() for url in url_input.splitlines() if url.strip()]

def setup_selenium():
    # Headless Chrome 설정
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
    return driver

def capture_full_page(driver, url, output_folder, page_index):
    """ 전체 페이지 스크린샷과 HTML 추출 """
    driver.get(url)
    time.sleep(3)  # 페이지 로딩 대기

    # 스크린샷 저장
    screenshot_path = os.path.join(output_folder, f"page_{page_index}_screenshot.png")
    driver.save_screenshot(screenshot_path)

    # HTML 소스 가져오기
    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup, screenshot_path

def save_content(soup, screenshot_path, page_index, output_folder):
    """ 텍스트와 이미지를 추출하여 파일에 저장 """
    page_folder = os.path.join(output_folder, f"page_{page_index}")
    os.makedirs(page_folder, exist_ok=True)

    # 텍스트 추출 및 저장
    texts = [p.get_text(strip=True) for p in soup.find_all(['p', 'div', 'span', 'article', 'section', 'blockquote'])]
    with open(os.path.join(page_folder, 'text_content.json'), 'w', encoding='utf-8') as json_file:
        json.dump(texts, json_file, ensure_ascii=False, indent=4)

    # 스크린샷 저장
    screenshot_dest = os.path.join(page_folder, f"page_{page_index}_screenshot.png")
    os.rename(screenshot_path, screenshot_dest)

    # HTML 저장
    html_path = os.path.join(page_folder, f"page_{page_index}.html")
    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write(soup.prettify())

    return {"texts": texts, "screenshot": screenshot_dest, "html": html_path}

def create_pdf_report(data_list):
    """ 크롤링 결과를 PDF로 생성 """
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)
    pdf.set_font("Arial", size=12)

    pdf.cell(200, 10, txt="Crawling Report", ln=True, align='C')
    for i, data in enumerate(data_list, start=1):
        pdf.cell(200, 10, txt=f"Page {i} Texts:", ln=True, align='L')
        for text in data["texts"]:
            pdf.multi_cell(0, 10, txt=text)
        pdf.cell(200, 10, txt=f"Page {i} Screenshot:", ln=True, align='L')
        pdf.image(data["screenshot"], x=10, w=100)

    pdf.output(os.path.join(output_folder, "report.pdf"))

# 크롤링 시작 버튼
if st.button("크롤링 시작"):
    if urls:
        driver = setup_selenium()
        all_data = []

        for idx, url in enumerate(urls, start=1):
            st.write(f"URL 크롤링 중... {url}")
            try:
                soup, screenshot_path = capture_full_page(driver, url, output_folder, idx)
                page_data = save_content(soup, screenshot_path, idx, output_folder)
                all_data.append(page_data)
            except Exception as e:
                st.write(f"크롤링 실패: {url}, 오류: {e}")

        driver.quit()

        # PDF 생성
        create_pdf_report(all_data)
        st.success("크롤링 완료!")
        st.write("크롤링 결과를 다운로드하세요:")

        # PDF 다운로드 링크
        with open(os.path.join(output_folder, "report.pdf"), "rb") as pdf_file:
            st.download_button(label="PDF 다운로드", data=pdf_file, file_name="crawling_report.pdf", mime="application/pdf")
        
    else:
        st.warning("URL을 입력하세요.")
