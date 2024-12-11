import streamlit as st
from statsbombpy import sb
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.patches import Arc
from io import BytesIO
from fpdf import FPDF

# 페이지 설정
st.set_page_config(page_title="StatsBomb 데이터 분석", layout="wide")

# 제목
st.title("StatsBomb 데이터 분석 도구")

# 사이드바 옵션
st.sidebar.header("옵션 선택")
competition = st.sidebar.selectbox(
    "리그를 선택하세요:",
    [comp['competition_name'] for comp in sb.competitions()]
)
selected_season = st.sidebar.selectbox(
    "시즌을 선택하세요:",
    [season['season_name'] for season in sb.competitions() if season['competition_name'] == competition]
)
matches = sb.matches(competition_id=competition, season_id=selected_season)
match_selection = st.sidebar.selectbox(
    "경기를 선택하세요:",
    matches['home_team'] + " vs " + matches['away_team']
)

# 선택한 경기 데이터 가져오기
match_id = matches[matches['home_team'] + " vs " + matches['away_team'] == match_selection]['match_id'].iloc[0]
events = sb.events(match_id=match_id)

# 필드 이미지 위에 슈팅 데이터 표시
def draw_pitch(ax=None):
    """축구 필드 그리기 함수"""
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    # 필드 외곽
    plt.plot([0, 0, 120, 120, 0], [0, 80, 80, 0, 0], color="black", lw=2)
    # 골대
    plt.plot([0, 0], [30, 50], color="black", lw=2)
    plt.plot([120, 120], [30, 50], color="black", lw=2)
    # 페널티 에어리어
    plt.plot([18, 18], [20, 60], color="black", lw=2)
    plt.plot([0, 18], [60, 60], color="black", lw=2)
    plt.plot([0, 18], [20, 20], color="black", lw=2)
    plt.plot([102, 102], [20, 60], color="black", lw=2)
    plt.plot([102, 120], [60, 60], color="black", lw=2)
    plt.plot([102, 120], [20, 20], color="black", lw=2)
    # 중앙 서클
    center_circle = Arc((60, 40), 20, 20, angle=0, theta1=0, theta2=360, color="black", lw=2)
    ax.add_patch(center_circle)
    return ax

st.header(f"{competition} {selected_season} - {match_selection}")
st.write("선택한 경기의 데이터")

st.subheader("슈팅 데이터 (필드 위 시각화)")
shots = events[events['type'] == 'Shot']

fig, ax = plt.subplots(figsize=(12, 8))
ax = draw_pitch(ax)
ax.scatter(shots['x'], shots['y'], c='red', label='슈팅 위치', s=100)
ax.set_title("슈팅 위치 분석")
ax.legend()
st.pyplot(fig)

# 주요 통계 요약
st.subheader("통계 요약")
stats_summary = shots.groupby('team')['shot_outcome'].value_counts().unstack()
st.write(stats_summary)

# PDF 생성 함수
def create_pdf(stats_summary, fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="StatsBomb 경기 분석", ln=True, align='C')
    
    # 통계 데이터 추가
    pdf.cell(200, 10, txt="통계 요약", ln=True, align='L')
    pdf.set_font("Arial", size=10)
    for team, stats in stats_summary.iterrows():
        pdf.cell(200, 10, txt=f"{team}: {stats.to_dict()}", ln=True, align='L')
    
    # 필드 이미지 추가
    pdf.add_page()
    pdf.cell(200, 10, txt="슈팅 위치 시각화", ln=True, align='C')
    buf = BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    pdf.image(buf, x=10, y=20, w=180)
    buf.close()
    
    return pdf.output(dest='S').encode('latin1')

# PDF 다운로드 버튼
if st.sidebar.button("PDF 다운로드"):
    pdf_data = create_pdf(stats_summary, fig)
    st.sidebar.download_button(
        label="PDF 다운로드",
        data=pdf_data,
        file_name="match_analysis.pdf",
        mime="application/pdf",
    )