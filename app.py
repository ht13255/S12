# app.py

import streamlit as st
import requests
from bs4 import BeautifulSoup

# Streamlit 앱 제목
st.title("Web2PDFConvert 사이트 크롤러")
st.write("URL을 입력하여 광고와 구독 링크를 제외한 모든 링크를 크롤링합니다.")

# URL 입력
url = st.text_input("URL을 입력하세요:", "https://www.web2pdfconvert.com/")

if url:
    try:
        # 웹 페이지 요청
        response = requests.get(url)
        response.raise_for_status()  # 요청 실패 시 오류 발생

        # HTML 내용 파싱
        soup = BeautifulSoup(response.text, 'html.parser')

        # 페이지 제목 추출
        title = soup.find('title').text
        st.write("### 페이지 제목:", title)

        # 모든 링크 크롤링 (광고 및 구독 링크 제외)
        all_links = {link.text.strip(): link.get('href') for link in soup.find_all('a') if link.get('href')}
        content_links = {text: href for text, href in all_links.items() if 'ad' not in href.lower() and 'subscribe' not in href.lower()}
        ad_subscribe_links = {text: href for text, href in all_links.items() if 'ad' in href.lower() or 'subscribe' in href.lower()}

        # 광고 및 구독 링크 제외한 링크 출력
        st.write("### 콘텐츠 링크 (광고 및 구독 제외):")
        for text, href in content_links.items():
            st.write(f"- [{text}]({href})")

        # 광고 및 구독 링크 출력
        st.write("### 광고 및 구독 관련 링크:")
        for text, href in ad_subscribe_links.items():
            st.write(f"- [{text}]({href})")

    except requests.exceptions.RequestException as e:
        st.error(f"URL 요청에 실패했습니다: {e}")
    except Exception as e:
        st.error(f"오류가 발생했습니다: {e}")
