import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import pdfkit
import tempfile
import os

# Streamlit 앱 제목
st.title("웹 페이지 크롤러 (텍스트와 이미지 포함)")
st.write("URL을 입력하여 모든 링크에 접속하고 페이지 내용을 PDF와 JSON으로 저장합니다.")

# wkhtmltopdf 경로 설정 - 시스템에 맞게 자동 감지 또는 환경 변수 사용 안내
def get_wkhtmltopdf_path():
    # 환경 변수에서 경로 확인
    wkhtmltopdf_path = os.getenv("WKHTMLTOPDF_PATH")
    if wkhtmltopdf_path and os.path.exists(wkhtmltopdf_path):
        return wkhtmltopdf_path
    
    # 일반적인 시스템 경로 확인 (Ubuntu 및 macOS)
    paths = ["/usr/local/bin/wkhtmltopdf", "/usr/bin/wkhtmltopdf"]
    for path in paths:
        if os.path.exists(path):
            return path

    # 경로가 없는 경우 안내 메시지
    st.warning(
        "wkhtmltopdf 경로를 찾을 수 없습니다. "
        "환경 변수 'WKHTMLTOPDF_PATH'에 wkhtmltopdf 설치 경로를 설정하고 다시 실행하세요. "
        "Windows 사용자는 'C:/Program Files/wkhtmltopdf/bin/wkhtmltopdf.exe' 경로를 지정할 수 있습니다."
    )
    return None

# 경로 설정 함수 호출
wkhtmltopdf_path = get_wkhtmltopdf_path()
if wkhtmltopdf_path:
    config = pdfkit.configuration(wkhtmltopdf=wkhtmltopdf_path)
else:
    st.stop()  # wkhtmltopdf 경로가 없으면 앱을 중지

# URL 입력
url = st.text_input("URL을 입력하세요:", "https://www.web2pdfconvert.com/")

if url:
    try:
        # 기본 페이지 요청
        response = requests.get(url)
        response.raise_for_status()  # 요청 실패 시 오류 발생
        soup = BeautifulSoup(response.text, 'html.parser')

        # 페이지 제목 및 모든 링크 수집
        title = soup.find('title').text if soup.find('title') else "No Title"
        st.write("### 페이지 제목:", title)

        # 모든 링크 크롤링 (광고 및 구독 링크 제외)
        all_links = {link.text.strip(): link.get('href') for link in soup.find_all('a') if link.get('href')}
        content_links = {text: href for text, href in all_links.items() if 'ad' not in href.lower() and 'subscribe' not in href.lower()}

        # JSON 데이터 수집용 딕셔너리
        all_data = {}

        # 임시 디렉터리 생성
        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_files = []

            # 각 링크에 접근하여 콘텐츠 추출 및 변환
            for text, link in content_links.items():
                full_link = link if link.startswith("http") else url + link  # 상대 링크 처리
                try:
                    sub_response = requests.get(full_link)
                    sub_response.raise_for_status()
                    sub_soup = BeautifulSoup(sub_response.text, 'html.parser')

                    # HTML 형식의 내용과 이미지 URL을 포함한 텍스트 추출
                    page_content = str(sub_soup)  # HTML 전체 내용 그대로 저장
                    images = [img['src'] if img['src'].startswith("http") else url + img['src'] for img in sub_soup.find_all("img") if img.get('src')]

                    # JSON 데이터에 추가
                    all_data[full_link] = {
                        "title": text,
                        "html_content": page_content,
                        "images": images
                    }

                    # PDF 파일로 저장
                    pdf_file_path = os.path.join(temp_dir, f"{text[:50]}.pdf")
                    pdfkit.from_string(page_content, pdf_file_path, configuration=config)  # HTML 콘텐츠를 PDF로 변환
                    pdf_files.append(pdf_file_path)
                    st.write(f"{pdf_file_path} 파일로 저장 완료")

                except requests.exceptions.RequestException as e:
                    st.warning(f"{full_link}에 접근할 수 없습니다: {e}")
                except Exception as e:
                    st.warning(f"오류 발생: {e}")

            # JSON 파일로 저장
            json_file_name = os.path.join(temp_dir, "web_content.json")
            with open(json_file_name, "w", encoding="utf-8") as json_file:
                json.dump(all_data, json_file, ensure_ascii=False, indent=4)
            st.write("JSON 파일 저장 완료")

            # PDF와 JSON 파일 다운로드 링크 제공
            st.download_button("JSON 파일 다운로드", data=open(json_file_name, "rb"), file_name="web_content.json")

            for pdf_file in pdf_files:
                with open(pdf_file, "rb") as file:
                    st.download_button(f"{os.path.basename(pdf_file)} 다운로드", data=file, file_name=os.path.basename(pdf_file))

    except requests.exceptions.RequestException as e:
        st.error(f"URL 요청에 실패했습니다: {e}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
