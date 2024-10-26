import streamlit as st
import requests
from bs4 import BeautifulSoup
import json
import tempfile
import os
from weasyprint import HTML, CSS
from weasyprint.text import fonts

# Streamlit 앱 제목
st.title("웹 페이지 크롤러 (텍스트와 이미지 포함)")
st.write("URL을 입력하여 모든 링크에 접속하고 페이지 내용을 PDF와 JSON으로 저장합니다.")

# Pango 설치 확인
try:
    fonts.find_font("Pango")
except OSError:
    st.error(
        "Pango 라이브러리를 찾을 수 없습니다. "
        "Pango는 WeasyPrint에서 PDF 생성을 위해 필요합니다. "
        "운영체제에 맞게 설치해 주세요:\n\n"
        "- **Linux**: `sudo apt install -y libpango-1.0-0`\n"
        "- **macOS**: `brew install pango`\n"
        "- **Windows**: [GTK+ for Windows 설치](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases) 후 PATH 환경 변수에 GTK 설치 경로 추가"
    )
    st.stop()

# URL 입력
url = st.text_input("URL을 입력하세요:", "https://www.web2pdfconvert.com/")

if url:
    try:
        # 기본 페이지 요청
        response = requests.get(url)
        response.raise_for_status()
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
                full_link = link if link.startswith("http") else url + link
                try:
                    sub_response = requests.get(full_link)
                    sub_response.raise_for_status()
                    sub_soup = BeautifulSoup(sub_response.text, 'html.parser')

                    # HTML 형식의 내용과 이미지 URL을 포함한 텍스트 추출
                    page_content = str(sub_soup)
                    images = [img['src'] if img['src'].startswith("http") else url + img['src'] for img in sub_soup.find_all("img") if img.get('src')]

                    # JSON 데이터에 추가
                    all_data[full_link] = {
                        "title": text,
                        "html_content": page_content,
                        "images": images
                    }

                    # PDF 파일로 저장
                    pdf_file_path = os.path.join(temp_dir, f"{text[:50]}.pdf")
                    HTML(string=page_content).write_pdf(pdf_file_path)
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
