import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time

# 크롬 드라이버 옵션 설정
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  # 브라우저 창 숨김
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# Sofascore 검색 함수
def sofascore_search(criteria):
    driver = init_driver()
    driver.get("https://www.sofascore.com/")
    time.sleep(2)

    # 검색
    search_bar = driver.find_element(By.XPATH, '//input[@placeholder="Search"]')
    search_bar.send_keys(criteria['name'])
    search_bar.send_keys(Keys.RETURN)
    time.sleep(3)

    # 선수 데이터 크롤링
    players_data = []
    players = driver.find_elements(By.CLASS_NAME, "list-item-class")  # HTML 클래스 확인 필요
    for player in players:
        try:
            name = player.find_element(By.CLASS_NAME, "player-name-class").text
            position = player.find_element(By.CLASS_NAME, "player-position-class").text
            nationality = player.find_element(By.CLASS_NAME, "player-nationality-class").text
            players_data.append({"Name": name, "Position": position, "Nationality": nationality})
        except Exception as e:
            print(f"Error extracting player data: {e}")

    driver.quit()
    return players_data

# Transfermarkt 몸값 크롤링 함수
def transfermarkt_value(player_name):
    driver = init_driver()
    driver.get("https://www.transfermarkt.com/")
    time.sleep(2)

    # 검색
    search_bar = driver.find_element(By.ID, "tm-header-search-input")
    search_bar.send_keys(player_name)
    search_bar.send_keys(Keys.RETURN)
    time.sleep(3)

    # 몸값 추출
    try:
        market_value = driver.find_element(By.CLASS_NAME, "data-header__market-value").text
    except Exception:
        market_value = "N/A"

    driver.quit()
    return market_value

# Streamlit UI
def main():
    st.title("Sofascore 및 Transfermarkt 크롤링")

    # 입력 폼
    st.sidebar.header("검색 조건")
    name = st.sidebar.text_input("선수 이름", "Messi")
    position = st.sidebar.text_input("포지션", "FW")
    age = st.sidebar.number_input("나이", min_value=15, max_value=50, value=30)

    criteria = {"name": name, "position": position, "age": age}

    if st.sidebar.button("크롤링 시작"):
        st.write("Sofascore에서 선수 정보 검색 중...")
        players = sofascore_search(criteria)

        st.write("Transfermarkt에서 선수 몸값 가져오는 중...")
        for player in players:
            player['Market Value'] = transfermarkt_value(player['Name'])

        # 데이터프레임 생성
        df = pd.DataFrame(players)
        st.dataframe(df)

        # 엑셀 파일로 저장
        @st.cache_data
        def convert_df_to_excel(dataframe):
            return dataframe.to_excel(index=False, engine='openpyxl')

        excel_file = convert_df_to_excel(df)

        # 다운로드 버튼
        st.download_button(
            label="엑셀 파일 다운로드",
            data=excel_file,
            file_name="players_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()