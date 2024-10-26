# /web_scraper_app.py
import requests
from bs4 import BeautifulSoup
import pandas as pd
import pdfkit
import json
import streamlit as st

# 각 웹사이트에서 기사의 링크를 가져오는 함수
def get_article_links(base_url, link_selector, unwanted_selectors):
    response = requests.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 기사 링크 추출
    links = [a['href'] for a in soup.select(link_selector)]
    
    # 불필요한 링크 필터링 (광고, 구독 등)
    for unwanted in unwanted_selectors:
        links = [link for link in links if unwanted not in link]
    
    return links

# 링크에서 기사 내용을 가져오는 함수
def fetch_article_content(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 기사의 본문이 포함된 article 태그 추출
    article = soup.find("article")
    paragraphs = article.find_all("p") if article else []
    content = "\n".join([para.text for para in paragraphs])
    
    return content

# PDF로 저장
def save_to_pdf(content, output_path):
    pdfkit.from_string(content, output_path)

# 머신러닝 학습 파일로 저장 (CSV/JSON)
def save_to_ml_file(data, output_path, format="csv"):
    if format == "csv":
        pd.DataFrame(data).to_csv(output_path, index=False)
    elif format == "json":
        with open(output_path, 'w') as f:
            json.dump(data, f)

# Streamlit 앱
def main():
    st.title("축구 분석 웹 스크래퍼")
    
    # 웹사이트 정보
    websites = {
        "Coaches' Voice": {
            "base_url": "https://learning.coachesvoice.com/category/analysis/",
            "link_selector": "a[href]",
            "unwanted_selectors": ["instagram", "subscribe", "ads"]
        },
        "The Football Analyst": {
            "base_url": "https://the-footballanalyst.com/",
            "link_selector": "a[href]",
            "unwanted_selectors": ["instagram", "subscribe", "ads"]
        }
    }
    
    # 웹사이트 선택
    choice = st.selectbox("스크랩할 웹사이트를 선택하세요", list(websites.keys()))
    st.write(f"{choice}에서 콘텐츠를 가져옵니다.")
    
    # 스크래핑 프로세스
    site = websites[choice]
    links = get_article_links(site["base_url"], site["link_selector"], site["unwanted_selectors"])
    st.write(f"{len(links)}개의 기사를 찾았습니다.")
    
    # 기사 내용 수집 및 처리
    data = []
    for link in links:
        content = fetch_article_content(link)
        data.append({"url": link, "content": content})
        
        # PDF로 각 기사를 저장
        pdf_path = f"articles/{link.split('/')[-1]}.pdf"
        save_to_pdf(content, pdf_path)
        
    # 다운로드 옵션 제공
    st.write("다운로드 옵션:")
    st.download_button("PDF 파일 다운로드", pdf_path)
    save_to_ml_file(data, "articles.csv")
    st.download_button("CSV 파일 다운로드", "articles.csv")
    
# Streamlit 진입점
if __name__ == "__main__":
    main()
