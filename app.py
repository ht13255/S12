import os
import time
import json
from fpdf import FPDF
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import streamlit as st
from bs4 import BeautifulSoup

# Streamlit 설정
st.title("렌더링된 페이지 그대로 크롤링")
st.write("브라우저로 JavaScript가 렌더링된 페이지를 크롤링하고 PDF와 JSON으로 저장합니다.")

output_folder = 'crawled_data'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

url_input = st.text_area("크롤링할 블로그 URL을 입력하세요 (줄바꿈으로 구분):")
urls = [url.strip() for url in url_input.splitlines() if url.strip()]

def setup_selenium():
    # Chrome 옵션 설정
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    options.binary_location = "/usr/bin/chromium-browser"  # Docker 또는 특정 환경에서의 Chrome 위치

    # 드라이버 설치 및 실행
    driver_path = ChromeDriverManager().install()
    service = Service(driver_path)
    driver = webdriver.Chrome(service=service, options=options)
    return driver

def capture_full_page(driver, url, output_folder, page_index):
    driver.get(url)
    time.sleep(3)  # 페이지 로딩 대기

    screenshot_path = os.path.join(output_folder, f"page_{page_index}_screenshot.png")
    driver.save_screenshot(screenshot_path)

    html = driver.page_source
    soup = BeautifulSoup(html, 'html.parser')
    return soup, screenshot_path

def save_content(soup, screenshot_path, page_index, output_folder):
    page_folder = os.path.join(output_folder, f"page_{page_index}")
    os.makedirs(page_folder, exist_ok=True)

    texts = [p.get_text(strip=True) for p in soup.find_all(['p', 'div', 'span', 'article', 'section', 'blockquote'])]
    with open(os.path.join(page_folder, 'text_content.json'), 'w', encoding='utf-8') as json_file:
        json.dump(texts, json_file, ensure_ascii=False, indent=4)

    screenshot_dest = os.path.join(page_folder, f"page_{page_index}_screenshot.png")
    os.rename(screenshot_path, screenshot_dest)

    html_path = os.path.join(page_folder, f"page_{page_index}.html")
    with open(html_path, 'w', encoding='utf-8') as html_file:
        html_file.write(soup.prettify())

    return {"texts": texts, "screenshot": screenshot_dest, "html": html_path}

def create_pdf_report(data_list):
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

if st.button("크롤링 시작"):
    if urls:
        try:
            driver = setup_selenium()
            all_data = []
            for idx, url in enumerate(urls, start=1):
                st.write(f"URL 크롤링 중... {url}")
                soup, screenshot_path = capture_full_page(driver, url, output_folder, idx)
                page_data = save_content(soup, screenshot_path, idx, output_folder)
                all_data.append(page_data)
            driver.quit()

            create_pdf_report(all_data)
            st.success("크롤링 완료!")
            st.write("크롤링 결과를 다운로드하세요:")
            with open(os.path.join(output_folder, "report.pdf"), "rb") as pdf_file:
                st.download_button(label="PDF 다운로드", data=pdf_file, file_name="crawling_report.pdf", mime="application/pdf")
        except Exception as e:
            st.error(f"크롤링 중 오류 발생: {e}")
    else:
        st.warning("URL을 입력하세요.")
