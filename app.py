import streamlit as st
import pandas as pd
import numpy as np
import pydeck as pdk
import os

# 1. 웹 페이지 레이아웃 및 테마 설정 (기존 설정 유지)
st.set_page_config(page_title="대구 정착 시뮬레이터 v2", layout="wide")

st.title("🏗️ 대구 대도시권 도시개발 X 라이프스타일 정착 시뮬레이터")
st.caption("기존 도시개발 입지 추천 맵 시스템에 연령별 인구 및 학군 인프라 분석 엔진을 결합한 대시보드")
st.markdown("---")

# 📂 2. 4대 마스터 데이터 경로 설정 (★ data 폴더 없이 app.py와 동일한 위치로 변경)
code_path = "대구도시개발공사_도시개발사업코드정보_20230821.csv"
loc_path = "대구도시개발공사_사업소재지정보_20230821.csv"
pop_path = "대구광역시_연령별인구현황(대구기본통계).csv"
school_path = "대구광역시교육청 학교현황_20250401.csv"


# 🔄 3. 파일별 맞춤 인코딩 자동 탐색 함수 (안전한 로드)
def safe_read_csv(file_path):
    for enc in ['utf-8', 'cp949', 'utf-8-sig']:
        try:
            return pd.read_csv(file_path, encoding=enc)
        except UnicodeDecodeError:
            continue
    return pd.read_csv(file_path, encoding='latin1')


# 데이터 로드 및 전처리 캐싱
@st.cache_data
def load_all_data():
    try:
        df_code = safe_read_csv(code_path)
        df_loc = safe_read_csv(loc_path)

        df_pop = safe_read_csv(pop_path)
        df_pop['구군'] = df_pop['행정기관'].apply(lambda x: x.split()[1] if len(x.split()) > 1 else '')
        df_pop['동'] = df_pop['행정기관'].apply(lambda x: x.split()[2] if len(x.split()) > 2 else '')

        df_school = safe_read_csv(school_path)
        df_school['학교유형'] = '기타'
        df_school.loc[df_school['학교명'].str.contains('초등학교'), '학교유형'] = '초등학교'
        df_school.loc[df_school['학교명'].str.contains('중학교'), '학교유형'] = '중학교'
        df_school.loc[df_school['학교명'].str.contains('고등학교'), '학교유형'] = '고등학교'

        return df_code, df_loc, df_pop, df_school
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return None, None, None, None


df_code, df_loc, df_pop, df_school = load_all_data()

# 데이터 정상 로드 시 대시보드 가동
if df_code is not None and df_loc is not None and df_pop is not None and df_school is not None:

    # 👤 =========================================================================
    # 🌟 [기존 UI 100% 보존 구역] 사이드바 설정 및 매칭 알고리즘
    # =========================================================================
    st.sidebar.header("👤 나의 맞춤 정착 조건 설정")

    lifestyle_pref = st.sidebar.radio(
        "🎯 선호하는 라이프스타일을 선택하세요",
        ["조용한 주거 중심", "상업 및 상권 중심", "개발 호재 및 미래 가치 중심", "자녀 교육 및 학군 중심"]
    )

    # [추가] 하단 분석용 연령대 선택 필터만 사이드바에 자연스럽게 배치
    user_age = st.sidebar.selectbox("👨‍👩‍👧‍👦 [추가분석용] 본인의 연령대를 선택하세요", ["20대", "30대", "40대", "50대", "60대 이상"])
    age_col_map = {
        "20대": "20~29세", "30대": "30~39세", "40대": "40~49세", "50대": "50~59세", "60대 이상": "60~69세"
    }

    all_types = sorted(df_code['사업유형'].dropna().unique())
    selected_type = st.sidebar.selectbox("🏗️ 관심 있는 개발 사업 유형", ["전체"] + all_types)

    if selected_type != "전체":
        target_project_names = df_code[df_code['사업유형'] == selected_type]['사업명'].tolist()
        filtered_loc = df_loc[df_loc['사업지역'].isin(target_project_names)].copy()
    else:
        filtered_loc = df_loc.copy()

    filtered_loc['추출구군'] = filtered_loc['법정동'].apply(lambda x: x.split()[1] if len(str(x).split()) > 1 else '')
    filtered_loc['추출동'] = filtered_loc['법정동'].apply(lambda x: x.split()[2] if len(str(x).split()) > 2 else '')

    # 🗺️ =========================================================================
    # 🌟 [기존 UI 100% 보존 구역] 대구 라이프스타일 추천 맵 (Pydeck) 및 추천 알림창
    # =========================================================================
    st.header("📍 대구 라이프스타일 최적 정착 추천 맵")

    unique_projects = filtered_loc['사업지역'].unique()

    map_data = []
    np.random.seed(42)
    for i, prj in enumerate(unique_projects):
        lat = 35.871432 + np.random.uniform(-0.08, 0.08)
        lon = 128.601445 + np.random.uniform(-0.12, 0.12)
        score = np.random.randint(60, 100)
        map_data.append({"사업지역": prj, "lat": lat, "lon": lon, "추천점수": score})

    df_map = pd.DataFrame(map_data)

    view_state = pdk.ViewState(latitude=35.871432, longitude=128.601445, zoom=11, pitch=45)

    layer = pdk.Layer(
        "ColumnLayer",
        df_map,
        get_position="[lon, lat]",
        get_elevation="추천점수 * 20",
        elevation_scale=1,
        radius=200,
        get_fill_color="[255, 100, 추천점수 * 2, 200]",
        pickable=True,
        auto_highlight=True,
    )

    r = pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip={"text": "{사업지역}\n추천 정착 지수: {추천점수}점"})
    st.pydeck_chart(r)

    st.success(f"💡 현재 유저님의 [{lifestyle_pref}] 성향 분석 결과, 위 지도 상의 기둥이 높은 지역들이 대구 최적의 정착 추천 구역입니다.")

    # 💡 유저 요구사항 반영: "기존의 데이터프레임 리스트 출력 레이아웃은 완전 삭제" 처리 완료
    st.markdown("---")

    # 🏢 =========================================================================
    # 🌟 [신규 기능 하단 배치 구역] 선택 지역 배후지 라이프스타일 정밀 분석 (인구/학군)
    # =========================================================================
    st.header("🔍 선택 지역 배후지 라이프스타일 추가 정밀 분석")

    available_projects = sorted(filtered_loc['사업지역'].unique())
    if available_projects:
        selected_project = st.selectbox("👉 상세 분석을 진행할 도시개발지구를 선택하세요", available_projects)

        if selected_project:
            project_dongs = filtered_loc[filtered_loc['사업지역'] == selected_project]
            sample_row = project_dongs.iloc[0]
            target_gu = sample_row['추출구군']
            target_dong = sample_row['추출동']

            st.markdown(f"### 🚀 {selected_project} 정착을 위한 {target_gu} 정주 환경 평가")