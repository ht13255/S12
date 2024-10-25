import streamlit as st
import requests
from bs4 import BeautifulSoup
import pdfkit

# wkhtmltopdf의 경로 설정 (필요한 경우)
path_to_wkhtmltopdf = '/usr/local/bin/wkhtmltopdf'  # 자신의 시스템에 맞게 경로 설정 (Windows의 경우 실행 파일 경로)
config = pdfkit.configuration(wkhtmltopdf=path_to_wkhtmltopdf)

# Streamlit 웹페이지 타이틀
st.title("웹 페이지 크롤링 및 PDF 변환기")

# 사용자로부터 URL 입력받기
url = st.text_input("크롤링할 웹 페이지의 URL을 입력하세요:")

# PDF 변환 및 다운로드 함수
def save_pdf(html_content, filename="output.pdf"):
    pdfkit.from_string(html_content, filename, configuration=config)
    with open(filename, "rb") as pdf_file:
        st.download_button(
            label="PDF 다운로드",
            data=pdf_file,
            file_name=filename,
            mime="application/pdf"
        )

# 크롤링 버튼
if st.button("크롤링 시작"):
    if url:
        try:
            # 1. 웹 페이지 요청
            response = requests.get(url)
            if response.status_code == 200:
                # 2. HTML 파싱
                soup = BeautifulSoup(response.text, 'html.parser')

                # 3. 모든 링크와 이미지 추출
                data = "<h1>크롤링 결과</h1>\n"
                
                # 링크 추출
                links = soup.find_all('a')
                data += "<h2>링크 목록</h2>\n<ul>"
                for link in links:
                    href = link.get('href')
                    text = link.text.strip()
                    if href and text:
                        data += f"<li><a href='{href}'>{text}</a> - {href}</li>\n"
                data += "</ul>"

                # 이미지 추출
                images = soup.find_all('img')
                data += "<h2>이미지 목록</h2>\n<ul>"
                for img in images:
                    img_src = img.get('src')
                    if img_src:
                        data += f"<li><img src='{img_src}' width='200px'> - {img_src}</li>\n"
                data += "</ul>"

                # 4. 크롤링 결과 출력
                st.markdown(data, unsafe_allow_html=True)

                # 5. PDF 파일로 저장 및 다운로드 버튼 표시
                save_pdf(data)
            else:
                st.error(f"웹 페이지를 불러오는 데 실패했습니다. 상태 코드: {response.status_code}")
        except Exception as e:
            st.error(f"오류가 발생했습니다: {str(e)}")
    else:
        st.warning("유효한 URL을 입력하세요.")