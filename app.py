import streamlit as st
import pandas as pd
import os

# 1. 웹 페이지 레이아웃 및 테마 설정
st.set_page_config(page_title="대구 정착 시뮬레이터 v2", layout="wide")

st.title("🏗️ 대구 대도시권 도시개발 X 라이프스타일 정착 시뮬레이터")
st.caption("대구도시개발공사 사업 정보와 연령별 인구, 학군 인프라 데이터를 융합한 맞춤형 입지 분석 플랫폼")
st.markdown("---")

# 📂 2. 4대 마스터 데이터 경로 설정
DATA_DIR = "data"
code_path = os.path.join(DATA_DIR, "대구도시개발공사_도시개발사업코드정보_20230821.csv")
loc_path = os.path.join(DATA_DIR, "대구도시개발공사_사업소재지정보_20230821.csv")
pop_path = os.path.join(DATA_DIR, "대구광역시_연령별인구현황(대구기본통계).csv")
school_path = os.path.join(DATA_DIR, "대구광역시교육청 학교현황_20250401.csv")


# 🔄 3. 데이터 로드 및 전처리 (성능 최적화를 위한 캐싱 적용)
@st.cache_data
def load_all_data():
    try:
        # A. 도시개발사업 기본 코드 정보
        df_code = pd.read_csv(code_path, encoding='cp949')

        # B. 사업소재지 정보
        df_loc = pd.read_csv(loc_path, encoding='cp949')

        # C. 연령별 인구현황 데이터 전처리
        df_pop = pd.read_csv(pop_path, encoding='cp949')
        df_pop['구군'] = df_pop['행정기관'].apply(lambda x: x.split()[1] if len(x.split()) > 1 else '')
        df_pop['동'] = df_pop['행정기관'].apply(lambda x: x.split()[2] if len(x.split()) > 2 else '')

        # D. 학교현황 데이터 전처리 및 학교유형 분류
        df_school = pd.read_csv(school_path, encoding='cp949')
        df_school['학교유형'] = '기타'
        df_school.loc[df_school['학교명'].str.contains('초등학교'), '학교유형'] = '초등학교'
        df_school.loc[df_school['학교명'].str.contains('중학교'), '학교유형'] = '중학교'
        df_school.loc[df_school['학교명'].str.contains('고등학교'), '학교유형'] = '고등학교'

        return df_code, df_loc, df_pop, df_school
    except Exception as e:
        st.error(f"데이터 로드 중 오류가 발생했습니다: {e}")
        return None, None, None, None


df_code, df_loc, df_pop, df_school = load_all_data()

# 데이터가 모두 정상적으로 로드되었을 때 시뮬레이터 가동
if df_code is not None and df_loc is not None and df_pop is not None and df_school is not None:

    # 👤 4. 사이드바: 유저 라이프스타일 맞춤형 필터 구성
    st.sidebar.header("👤 나의 맞춤 정착 조건 필터")

    # 조건 필터 1: 사업유형 선택 (도시개발공사 데이터 소스)
    all_types = sorted(df_code['사업유형'].dropna().unique())
    selected_type = st.sidebar.selectbox("🏗️ 관심 있는 개발 사업 유형", ["전체"] + all_types)

    # 조건 필터 2: 유저 연령대 선택 (대구인구통계 데이터 소스 매핑)
    user_age = st.sidebar.selectbox("👨‍👩‍👧‍👦 본인의 연령대를 선택하세요", ["20대", "30대", "40대", "50대", "60대 이상"])
    age_col_map = {
        "20대": "20~29세", "30대": "30~39세", "40대": "40~49세", "50대": "50~59세", "60대 이상": "60~69세"
    }

    # 🔄 5. 기존 바이브코딩 핵심 로직: 사업유형에 따른 소재지 데이터 필터링 연산
    if selected_type != "전체":
        # 코드 정보에서 선택된 유형의 사업명 리스트 추출
        target_project_names = df_code[df_code['사업유형'] == selected_type]['사업명'].tolist()
        filtered_loc = df_loc[df_loc['사업지역'].isin(target_project_names)].copy()
    else:
        filtered_loc = df_loc.copy()

    # 소재지 법정동 주소에서 구군 및 동 분리 가공
    filtered_loc['추출구군'] = filtered_loc['법정동'].apply(lambda x: x.split()[1] if len(str(x).split()) > 1 else '')
    filtered_loc['추출동'] = filtered_loc['법정동'].apply(lambda x: x.split()[2] if len(str(x).split()) > 2 else '')

    # 🏢 6. 메인 화면: 도시개발지구 선택 인터페이스
    available_projects = sorted(filtered_loc['사업지역'].unique())

    if available_projects:
        selected_project = st.selectbox("👉 상세 분석 및 라이프스타일 시뮬레이션을 진행할 도시개발지구를 선택하세요", available_projects)

        if selected_project:
            # 선택된 사업의 소재지 행 매칭
            project_dongs = filtered_loc[filtered_loc['사업지역'] == selected_project]
            sample_row = project_dongs.iloc[0]
            target_gu = sample_row['추출구군']
            target_dong = sample_row['추출동']

            # 메인 레이아웃 상단: 도시개발공사 마스터 정보 브리핑
            st.markdown(f"### 📍 {selected_project} 사업 마스터 정보")

            # 카드 레이아웃으로 주요 지표 시각화
            m1, m2, m3 = st.columns(3)
            with m1:
                st.metric("소재지 관할 구/군", target_gu)
            with m2:
                st.metric("대표 법정동 위치", target_dong)
            with m3:
                # 코드 테이블에서 사업유형 가져오기
                prj_type_info = df_code[df_code['사업명'] == selected_project]['사업유형'].values
                st.metric("사업 공식 유형", prj_type_info[0] if len(prj_type_info) > 0 else "기타")

            # 기존 daegu_VibeCoding.py 데이터 상세 표출부 이식
            st.write("▼ 대구도시개발공사 등록 사업 세부 내역")
            st.dataframe(df_code[df_code['사업명'] == selected_project].reset_index(drop=True), use_container_width=True)

            st.markdown("---")

            # 메인 레이아웃 하단: 신규 융합 데이터(학군/인구) 배후지 입지 시뮬레이션
            st.markdown(f"### 📊 {selected_project} 정착을 위한 배후지 라이프스타일 환경 분석")
            st.caption(f"선택하신 사업지 관할인 [{target_gu}]의 실제 정주 여건 통계 자료입니다.")

            col1, col2 = st.columns(2)

            with col1:
                st.sub_header(f"🏫 {target_gu} 지역 학군 인프라 (초/중/고 분포)")
                # 해당 구군에 속한 학교 필터링
                gu_schools = df_school[df_school['관할구군청'].str.contains(target_gu, na=False)]

                if not gu_schools.empty:
                    school_counts = gu_schools.groupby('학교유형').size().reset_index(name='학교 수')
                    # 막대 차트 시각화
                    st.bar_chart(data=school_counts, x='학교유형', y='학교 수', color='#4F8BF9')
                    # 데이터프레임 상세 리스트 표출
                    st.dataframe(gu_schools[['학교명', '학교유형', '주소']].reset_index(drop=True), use_container_width=True,
                                 height=250)
                else:
                    st.info("해당 구군의 학교 현황 데이터가 존재하지 않습니다.")

            with col2:
                st.sub_header(f"👨‍👩‍👧‍👦 {target_gu} 동별 [{user_age}] 이웃 인구 분포")
                # 해당 구군의 인구 데이터 필터링
                gu_pops = df_pop[df_pop['구군'] == target_gu].copy()
                age_col = age_col_map[user_age]

                if not gu_pops.empty:
                    # 천 단위 콤마(,) 제거 후 정수형 변환 연산
                    gu_pops[age_col] = gu_pops[age_col].astype(str).str.replace(',', '').astype(int)
                    top_dongs = gu_pops.sort_values(by=age_col, ascending=False)[['동', age_col]].head(10)

                    # 막대 차트 시각화
                    st.bar_chart(data=top_dongs, x='동', y=age_col, color='#FF4B4B')

                    # 🎯 매치 메이킹 점수 힌트: 현재 개발 사업지와 유저 연령 이웃 연동성 지표
                    # 행정동과 법정동 명칭 매칭 보정 (앞 두 글자 기준)
                    is_pop_exist = gu_pops[gu_pops['동'].str.contains(target_dong[:2], na=False)]
                    if not is_pop_exist.empty:
                        current_dong_pop = is_pop_exist.iloc[0][age_col]
                        st.metric(label=f"🎯 현재 사업지 주변({target_dong})의 실제 {user_age} 거주인구수",
                                  value=f"{current_dong_pop:,} 명")
                    else:
                        st.info("💡 본 개발 구역은 현재 인구 갱신 구역이거나 대규모 신규 입주 예정 부지입니다.")
                else:
                    st.info("해당 구군의 인구 현황 통계가 존재하지 않습니다.")

            # 📋 7. 시뮬레이터 종합 입지 평가 종합 피드백
            st.markdown("---")
            st.subheader("📋 공공데이터 융합 입지 시뮬레이션 결과 리포트")
            total_schools = len(gu_schools)
            st.write(
                f"1. **학군 여건:** 선택하신 **{selected_project}** 주변 관할 구역에는 총 **{total_schools}개**의 초/중/고등학교 학군 인프라가 배치되어 있습니다.")
            st.write(
                f"2. **소셜 인프라 매칭:** 현재 오른쪽 차트에서 **{target_gu}** 내의 동네별 **{user_age}** 또래 인구 거주 순위를 확인하신 후, 정착 준공 시 시너지 효과를 분석해 보세요.")
    else:
        st.warning("⚠️ 필터 조건에 부합하는 도시개발사업이 없습니다. 사이드바의 사업 유형을 조정해 주세요.")

else:
    st.error("❌ data/ 폴더 내에 4개의 마스터 CSV 파일이 모두 완벽하게 보관되어 있는지 파일명을 확인해 주세요.")