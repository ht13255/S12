import os
import asyncio
import aiohttp
import json
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from fpdf import FPDF
import streamlit as st
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
import xml.etree.ElementTree as ET

st.title("고급 블로그 크롤링 앱 (비동기 지원)")
st.write("다수의 블로그 URL을 입력하여 텍스트와 이미지를 크롤링하고 PDF 리포트를 생성합니다.")

output_folder = 'crawled_data'
if not os.path.exists(output_folder):
    os.makedirs(output_folder)

url_input = st.text_area("크롤링할 블로그 URL을 입력하세요 (줄바꿈으로 구분):")
urls = [url.strip() for url in url_input.splitlines() if url.strip()]

async def fetch_page(session, url):
    """ 비동기적으로 페이지 HTML 요청 """
    try:
        async with session.get(url, timeout=10) as response:
            response.raise_for_status()
            return await response.text(), "requests"
    except Exception as e:
        st.write(f"요청 실패 ({url}): {e}")
        return None, "failed"

def fetch_sitemap_urls(base_url):
    """ 사이트맵에서 URL 추출 """
    sitemap_url = urljoin(base_url, "/sitemap.xml")
    page_urls = []

    try:
        response = requests.get(sitemap_url)
        response.raise_for_status()
        tree = ET.fromstring(response.content)
        for url_element in tree.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
            page_urls.append(url_element.text)
        st.write(f"사이트맵에서 {len(page_urls)}개의 URL 발견")
    except requests.RequestException as e:
        st.write(f"사이트맵 접근 실패: {e}")

    return page_urls or [base_url]

def detect_api_endpoints(soup, base_url):
    """ 스크립트 태그에서 API 엔드포인트 감지 """
    api_urls = set()
    for script in soup.find_all("script"):
        if script.string and "fetch" in script.string:
            fetch_urls = [url.split('\'')[1] for url in script.string.split('fetch(')[1:]]
            api_urls.update(urljoin(base_url, url) for url in fetch_urls)
    return list(api_urls)

async def download_image(session, img_url, img_path):
    """ 비동기 이미지 다운로드 """
    try:
        async with session.get(img_url) as response:
            response.raise_for_status()
            with open(img_path, 'wb') as f:
                f.write(await response.read())
    except Exception as e:
        st.write(f"이미지 다운로드 실패: {img_url}, 오류: {e}")

async def save_content(session, soup, base_url, page_index):
    """ 페이지 텍스트, 이미지 및 API 데이터 저장 """
    data = {"texts": [p.get_text(strip=True) for p in soup.find_all(['p', 'div', 'span', 'article', 'section', 'blockquote']) if p.get_text(strip=True)], "images": []}
    page_folder = os.path.join(output_folder, f"page_{page_index}")
    os.makedirs(page_folder, exist_ok=True)

    # 이미지 다운로드
    for img in soup.find_all('img'):
        img_url = urljoin(base_url, img.get('src') or img.get('data-src', ''))
        img_name = os.path.basename(urlparse(img_url).path)
        img_path = os.path.join(page_folder, img_name)
        await download_image(session, img_url, img_path)
        data["images"].append(img_name)

    # API 데이터 가져오기
    for api_url in detect_api_endpoints(soup, base_url):
        try:
            async with session.get(api_url) as response:
                data["api_data"] = await response.json()
        except Exception as e:
            st.write(f"API 요청 실패: {api_url}, 오류: {e}")

    with open(os.path.join(page_folder, 'data.json'), 'w', encoding='utf-8') as json_file:
        json.dump(data, json_file, ensure_ascii=False, indent=4)
    return data

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

        pdf.cell(200, 10, txt=f"Page {i} Images:", ln=True, align='L')
        for image in data["images"]:
            pdf.cell(200, 10, txt=image, ln=True)

    pdf.output(os.path.join(output_folder, "report.pdf"))

async def main(urls):
    async with aiohttp.ClientSession() as session:
        all_data = []
        for idx, url in enumerate(urls, start=1):
            st.write(f"URL 크롤링 중... {url}")
            page_urls = fetch_sitemap_urls(url)

            for page_url in page_urls:
                st.write(f"페이지 처리 중... {page_url}")
                html, method = await fetch_page(session, page_url)
                if html:
                    soup = BeautifulSoup(html, 'html.parser')
                    page_data = await save_content(session, soup, page_url, idx)
                    all_data.append(page_data)
                else:
                    st.write(f"크롤링 실패: {page_url}")

        create_pdf_report(all_data)
        st.success("크롤링 완료!")
        st.write("크롤링 결과를 다운로드하세요:")
        with open(os.path.join(output_folder, "report.pdf"), "rb") as pdf_file:
            st.download_button(label="PDF 다운로드", data=pdf_file, file_name="crawling_report.pdf", mime="application/pdf")
        
        with open(os.path.join(output_folder, "data.json"), "w", encoding="utf-8") as json_file:
            json.dump(all_data, json_file, ensure_ascii=False, indent=4)
        with open(os.path.join(output_folder, "data.json"), "rb") as json_file:
            st.download_button(label="JSON 다운로드", data=json_file, file_name="crawling_data.json", mime="application/json")

# 실행 버튼
if st.button("크롤링 시작"):
    if urls:
        asyncio.run(main(urls))
    else:
        st.warning("URL을 입력하세요.")
