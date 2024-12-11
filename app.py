import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from statsbombpy import sb
from fpdf import FPDF
from io import BytesIO

# Streamlit 설정
st.title("StatsBomb 선수 분석 대시보드")

# 대회 데이터 로드
st.sidebar.header("설정")
competitions = sb.competitions()
competition_names = competitions["competition_name"].unique()
selected_competition = st.sidebar.selectbox("대회 선택", competition_names)

# 선택된 대회 필터링
filtered_competition = competitions[competitions["competition_name"] == selected_competition]
seasons = filtered_competition["season_name"].unique()
selected_season = st.sidebar.selectbox("시즌 선택", seasons)

# 선택된 시즌에 해당하는 경기 로드
competition_id = filtered_competition[filtered_competition["season_name"] == selected_season]["competition_id"].values[0]
season_id = filtered_competition[filtered_competition["season_name"] == selected_season]["season_id"].values[0]
matches = sb.matches(competition_id=competition_id, season_id=season_id)

# 경기 선택
match_titles = matches["home_team"] + " vs " + matches["away_team"]
selected_match = st.sidebar.selectbox("경기 선택", match_titles)

# 선택된 경기 데이터 로드
selected_match_id = matches[matches["home_team"] + " vs " + matches["away_team"] == selected_match]["match_id"].values[0]
events = sb.events(match_id=selected_match_id)

# 선수 이름 선택
players = events["player"].dropna().unique()
selected_player = st.sidebar.selectbox("선수 선택", players)

# 선택된 선수 데이터 필터링
player_data = events[events["player"] == selected_player]

# 섹션: 선수 데이터 요약
st.header(f"{selected_player} 데이터 요약")
st.write(f"경기 이벤트 데이터 수: {len(player_data)}")
st.write(player_data[["type", "minute", "location"]].head(10))

# 패스 데이터 시각화
st.subheader("패스 분포 시각화")
pass_data = player_data[player_data["type"] == "Pass"]
pass_fig, pass_ax = plt.subplots()
if len(pass_data) > 0:
    for _, row in pass_data.iterrows():
        if isinstance(row["pass_end_location"], list):
            pass_ax.plot(
                [row["location"][0], row["pass_end_location"][0]],
                [row["location"][1], row["pass_end_location"][1]],
                color="blue",
                alpha=0.6,
                linewidth=1,
            )
    pass_ax.set_title(f"{selected_player}의 패스 분포")
    pass_ax.set_xlim([0, 120])
    pass_ax.set_ylim([0, 80])
    pass_ax.set_xlabel("X 좌표")
    pass_ax.set_ylabel("Y 좌표")
    st.pyplot(pass_fig)
else:
    st.write("패스 데이터가 없습니다.")

# 슈팅 데이터 시각화
st.subheader("슈팅 데이터 시각화")
shot_data = player_data[player_data["type"] == "Shot"]
shot_fig, shot_ax = plt.subplots()
if len(shot_data) > 0:
    shot_ax.scatter(
        [loc[0] for loc in shot_data["location"]],
        [loc[1] for loc in shot_data["location"]],
        c="red",
        label="Shot",
    )
    shot_ax.set_title(f"{selected_player}의 슈팅 위치")
    shot_ax.set_xlim([0, 120])
    shot_ax.set_ylim([0, 80])
    shot_ax.set_xlabel("X 좌표")
    shot_ax.set_ylabel("Y 좌표")
    shot_ax.legend()
    st.pyplot(shot_fig)
else:
    st.write("슈팅 데이터가 없습니다.")

# PDF 생성 함수
def create_pdf(player_name, pass_fig, shot_fig, player_summary):
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{player_name} 분석 결과", ln=True, align="C")

    # 선수 데이터 요약
    pdf.set_font("Arial", size=10)
    pdf.multi_cell(0, 10, txt=player_summary)

    # 패스 이미지 추가
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{player_name} 패스 분포", ln=True, align="C")
    pass_img = BytesIO()
    pass_fig.savefig(pass_img, format="png")
    pass_img.seek(0)
    pdf.image(pass_img, x=10, y=30, w=180)

    # 슈팅 이미지 추가
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"{player_name} 슈팅 위치", ln=True, align="C")
    shot_img = BytesIO()
    shot_fig.savefig(shot_img, format="png")
    shot_img.seek(0)
    pdf.image(shot_img, x=10, y=30, w=180)

    return pdf

# PDF 다운로드 버튼
if st.button("PDF 다운로드"):
    player_summary = f"경기 이벤트 데이터 수: {len(player_data)}\n"
    pdf = create_pdf(selected_player, pass_fig, shot_fig, player_summary)
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    pdf_output.seek(0)

    st.download_button(
        label="PDF 다운로드",
        data=pdf_output,
        file_name=f"{selected_player}_분석결과.pdf",
        mime="application/pdf",
    )