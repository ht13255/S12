import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
import pandas as pd
import time

# 크롬 드라이버 설정 함수
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    return webdriver.Chrome(options=options)

# Sofascore에서 선수 정보를 검색하는 함수
def sofascore_search(criteria):
    driver = init_driver()
    driver.get("https://www.sofascore.com/")
    time.sleep(2)

    # 검색창 입력
    search_bar = driver.find_element(By.XPATH, '//input[@placeholder="Search"]')
    search_bar.send_keys(criteria['name'])
    search_bar.send_keys(Keys.RETURN)
    time.sleep(3)

    players_data = []
    try:
        players = driver.find_elements(By.CLASS_NAME, "sc-c-text")  # Sofascore HTML 구조 확인 필요
        for player in players:
            try:
                name = player.find_element(By.CLASS_NAME, "sc-c-player-name").text
                position = player.find_element(By.CLASS_NAME, "sc-c-player-position").text
                nationality = player.find_element(By.CLASS_NAME, "sc-c-player-nationality").text
                matches_played = int(player.find_element(By.CLASS_NAME, "sc-c-matches-played").text)
                preferred_foot = player.find_element(By.CLASS_NAME, "sc-c-preferred-foot").text

                # 조건 필터링
                if criteria['position'] and criteria['position'] not in position:
                    continue
                if criteria['nationality'] and criteria['nationality'] not in nationality:
                    continue
                if criteria['min_matches'] and matches_played < criteria['min_matches']:
                    continue
                if criteria['preferred_foot'] and criteria['preferred_foot'] not in preferred_foot:
                    continue

                players_data.append({
                    "Name": name,
                    "Position": position,
                    "Nationality": nationality,
                    "Matches Played": matches_played,
                    "Preferred Foot": preferred_foot
                })
            except Exception as e:
                st.warning(f"선수 데이터를 처리하는 중 오류 발생: {e}")

    except Exception as e:
        st.error(f"Sofascore 데이터를 가져오는 중 오류 발생: {e}")

    driver.quit()
    return players_data

# Transfermarkt에서 선수 몸값 검색
def transfermarkt_value(player_name):
    driver = init_driver()
    driver.get("https://www.transfermarkt.com/")
    time.sleep(2)

    try:
        search_bar = driver.find_element(By.ID, "tm-header-search-input")
        search_bar.send_keys(player_name)
        search_bar.send_keys(Keys.RETURN)
        time.sleep(3)
        market_value = driver.find_element(By.CLASS_NAME, "data-header__market-value").text
    except Exception:
        market_value = "N/A"

    driver.quit()
    return market_value

# Streamlit UI
def main():
    st.title("축구 선수 크롤링 - Sofascore & Transfermarkt")

    st.sidebar.header("검색 조건")
    name = st.sidebar.text_input("선수 이름", "")
    position = st.sidebar.selectbox(
        "포지션",
        options=[
            "", "ST", "LW", "RW", "CM", "CAM", "CDM", "LM", "RM", 
            "CB", "LB", "RB", "LWB", "RWB", "GK"
        ]
    )
    nationality = st.sidebar.text_input("국적 (예: Brazil, Germany)", "")
    min_age = st.sidebar.number_input("최소 나이", min_value=0, max_value=50, value=0)
    max_age = st.sidebar.number_input("최대 나이", min_value=0, max_value=50, value=50)
    min_matches = st.sidebar.number_input("최소 경기 수", min_value=0, value=0)
    preferred_foot = st.sidebar.selectbox("주발", options=["", "Right", "Left"])

    criteria = {
        "name": name,
        "position": position,
        "nationality": nationality,
        "min_age": min_age,
        "max_age": max_age,
        "min_matches": min_matches,
        "preferred_foot": preferred_foot
    }

    if st.sidebar.button("크롤링 시작"):
        st.write("Sofascore에서 데이터 가져오는 중...")
        players = sofascore_search(criteria)

        st.write("Transfermarkt에서 선수 몸값 가져오는 중...")
        for player in players:
            player['Market Value'] = transfermarkt_value(player['Name'])

        df = pd.DataFrame(players)

        @st.cache_data
        def convert_df_to_excel(dataframe):
            return dataframe.to_excel(index=False, engine='openpyxl')

        excel_file = convert_df_to_excel(df)

        st.dataframe(df)
        st.download_button(
            label="엑셀 파일 다운로드",
            data=excel_file,
            file_name="players_data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

if __name__ == "__main__":
    main()