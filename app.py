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

# 데이터 유효성 검사
try:
    competitions = sb.competitions()
    if competitions.empty:
        st.error("StatsBomb 데이터가 비어 있습니다. 데이터를 확인하세요.")
        st.stop()
except Exception as e:
    st.error(f"StatsBomb 데이터를 로드하는 중 오류가 발생했습니다: {e}")
    st.stop()

# 사이드바 옵션
st.sidebar.header("옵션 선택")
competition = st.sidebar.selectbox(
    "리그를 선택하세요:",
    competitions['competition_name'].unique() if not competitions.empty else ["데이터 없음"]
)
selected_season = st.sidebar.selectbox(
    "시즌을 선택하세요:",
    competitions[competitions['competition_name'] == competition]['season_name'].unique()
    if competition else ["데이터 없음"]
)

# 선택한 리그와 시즌의 경기 불러오기
try:
    matches = sb.matches(competition_id=competitions[competitions['competition_name'] == competition]['competition_id'].iloc[0],
                         season_id=competitions[competitions['season_name'] == selected_season]['season_id'].iloc[0])
    if matches.empty:
        st.error("선택한 리그와 시즌에 해당하는 경기가 없습니다.")
        st.stop()
except Exception as e:
    st.error(f"경기 데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.stop()

match_selection = st.sidebar.selectbox(
    "경기를 선택하세요:",
    matches['home_team'] + " vs " + matches['away_team']
)

# 선택한 경기 데이터 가져오기
try:
    match_id = matches[matches['home_team'] + " vs " + matches['away_team'] == match_selection]['match_id'].iloc[0]
    events = sb.events(match_id=match_id)
    if events.empty:
        st.error("선택한 경기의 이벤트 데이터가 없습니다.")
        st.stop()
except Exception as e:
    st.error(f"이벤트 데이터를 로드하는 중 오류가 발생했습니다: {e}")
    st.stop()

# 필드 이미지 위에 슈팅 데이터 표시
def draw_pitch(ax=None):
    """축구 필드 그리기 함수"""
    if ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))
    ax.set_xlim(0, 120)
    ax.set_ylim(0, 80)
    plt.plot([0, 0, 120, 120, 0], [0, 80, 80, 0, 0], color="black", lw=2)
    plt.plot([0, 0], [30, 50], color="black", lw=2)
    plt.plot([120, 120], [30, 50], color="black", lw=2)
    plt.plot([18, 18], [20, 60], color="black", lw=2)
    plt.plot([0, 18], [60, 60], color="black", lw=2)
    plt.plot([0, 18], [20, 20], color="black", lw=2)
    plt.plot([102, 102], [20, 60], color="black", lw=2)
    plt.plot([102, 120], [60, 60], color="black", lw=2)
    plt.plot([102, 120], [20, 20], color="black", lw=2)
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

# PDF 생성 함수
def create_pdf(fig):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="StatsBomb 경기 분석", ln=True, align='C')
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
    pdf_data = create_pdf(fig)
    st.sidebar.download_button(
        label="PDF 다운로드",
        data=pdf_data,
        file_name="match_analysis.pdf",
        mime="application/pdf",
    )