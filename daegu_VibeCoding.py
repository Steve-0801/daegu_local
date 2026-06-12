import streamlit as st
import pandas as pd
import os
import re

# 1. 페이지 설정
st.set_page_config(page_title="대구 동네 정착 시뮬레이터", layout="wide", initial_sidebar_state="expanded")


# 2. 데이터 로드 및 자동 융합 함수 (인코딩 에러 방어 및 불량 바이트 패스 적용)
@st.cache_data
def load_and_merge_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_loc_path = os.path.join(current_dir, '대구도시개발공사_사업소재지정보_20230821.csv')
    file_code_path = os.path.join(current_dir, '대구도시개발공사_도시개발사업코드정보_20230821.csv')

    try:
        df_loc = pd.read_csv(file_loc_path, encoding='cp949', errors='ignore')
        df_code = pd.read_csv(file_code_path, encoding='cp949', errors='ignore')
    except Exception:
        try:
            df_loc = pd.read_csv(file_loc_path, encoding='utf-8', errors='ignore')
            df_code = pd.read_csv(file_code_path, encoding='utf-8', errors='ignore')
        except FileNotFoundError as e:
            st.error(f"⚠️ 원본 CSV 파일이 프로젝트 폴더에 없습니다: {e.filename}")
            st.info("두 개의 원본 CSV 파일명이 정확한지, 파이썬 파일과 같은 폴더에 있는지 확인해주세요.")
            st.stop()
        except Exception as e:
            st.error(f"데이터를 읽는 중 예측하지 못한 인코딩 오류가 발생했습니다: {e}")
            st.stop()

    enriched_data = []
    for idx, row in df_loc.iterrows():
        lp = row['사업지역']
        c_name, c_type, s_type = "기타 개발사업", "기타", "기타"
        lp_clean = re.sub(r'[^가-힣0-9a-zA-Z]', '', str(lp))
        for _, c_row in df_code.iterrows():
            c_name_clean = re.sub(r'[^가-힣0-9a-zA-Z]', '', str(c_row['사업명']))
            c_dist_clean = re.sub(r'[^가-힣0-9a-zA-Z]', '', str(c_row['사업지구']))
            if (c_name_clean in lp_clean) or (lp_clean in c_name_clean) or (c_dist_clean in lp_clean) or (
                    lp_clean in c_dist_clean):
                c_name = c_row['사업명']
                c_type = c_row['사업유형']
                s_type = c_row['공급유형']
                break

        full_dong = row['법정동']
        parts = str(full_dong).split()
        gu = parts[1] if len(parts) > 1 else "기타"
        dong = " ".join(parts[2:]) if len(parts) > 2 else "기타"

        enriched_data.append({
            '사업지역': lp,
            '구': gu,
            '동': dong,
            '사업명_연계': c_name,
            '사업유형': c_type,
            '공급유형': s_type
        })

    return pd.DataFrame(enriched_data)


# 데이터 로드 실행
df = load_and_merge_data()

# 3. 사이드바 - 유저 성향 입력 인터페이스
st.sidebar.header("👤 나의 라이프스타일 성향 설정")
st.sidebar.write("당신의 가치관에 따라 가중치를 조절해주세요.")

vibe_youth = st.sidebar.slider("🎈 청년/1인 가구 주거 (임대주택 편의성)", 0, 100, 50)
vibe_family = st.sidebar.slider("🏠 가족/내집마련 (공공분양, 아파트 단지)", 0, 100, 50)
vibe_job = st.sidebar.slider("🏭 직주근접/미래가치 (산업단지, 개발지구)", 0, 100, 50)


# 4. Local Vibe Index 계산 알고리즘
def calculate_vibe_index(df_data, w_youth, w_family, w_job):
    gus = df_data['구'].unique()
    # 명시적 실수형 구조 정의로 미래 판다스 버전 경고 방지
    score_board = pd.DataFrame(0.0, index=gus, columns=['청년점수', '가족점수', '산업점수', '종합_Vibe_Index'])

    for idx, row in df_data.iterrows():
        gu = row['구']
        b_type = row['사업유형']
        p_name = row['사업지역']

        if b_type in ['행복주택임대', '다가구임대'] or '임대' in str(p_name):
            score_board.loc[gu, '청년점수'] += 3.0
        if b_type == '아파트분양' or '청아람' in str(p_name) or '아파트' in str(p_name):
            score_board.loc[gu, '가족점수'] += 3.0
        if '산업단지' in str(p_name) or '의료지구' in str(p_name) or '과학산업' in str(p_name):
            score_board.loc[gu, '산업점수'] += 4.0
        elif b_type == '택지분양':
            score_board.loc[gu, '산업점수'] += 1.5

    for col in ['청년점수', '가족점수', '산업점수']:
        max_val = score_board[col].max()
        if max_val > 0:
            score_board[col] = (score_board[col] / max_val) * 100

    total_w = w_youth + w_family + w_job
    if total_w > 0:
        score_board['종합_Vibe_Index'] = (
                                               (score_board['청년점수'] * w_youth) +
                                               (score_board['가족점수'] * w_family) +
                                               (score_board['산업점수'] * w_job)
                                       ) / total_w
    else:
        score_board['종합_Vibe_Index'] = 0.0

    return score_board.sort_values(by='종합_Vibe_Index', ascending=False)


result_index = calculate_vibe_index(df, vibe_youth, vibe_family, vibe_job)

# 5. 메인 화면 UI 레이아웃
st.title("🏙️ 대구 로컬 이주자를 위한 '동네 정착 시뮬레이터'")
st.markdown("대구도시개발공사의 **공공 개발 및 주택 공급 데이터**를 기반으로 당신의 라이프스타일에 가장 잘 맞는 지역을 추천합니다.")
st.write("---")

top_gu = result_index.index[0]
top_score = result_index.iloc[0]['종합_Vibe_Index']

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("🎯 당신을 위한 최적의 추천 지역")
    st.metric(label="추천 1순위 지역구", value=f"대구광역시 {top_gu}", delta=f"매칭 점수: {top_score:.1f}점")
    st.write(f"현재 선택하신 성향 분석 결과, 대구도시개발공사가 진행하는 공공 인프라 사업의 성격이 **{top_gu}**와 가장 일치합니다.")

with col2:
    st.subheader("📊 대구 주요 구·군별 정착 적합도 점수")
    st.bar_chart(result_index['종합_Vibe_Index'])

st.write("---")

st.subheader("🔍 추천 지역 상세 들여다보기")
selected_gu = st.selectbox("어느 지역구의 상세 동네 호재를 확인해볼까요?", result_index.index)

gu_details = df[df['구'] == selected_gu][['동', '사업지역', '사업유형', '공급유형']].drop_duplicates()

tab1, tab2 = st.tabs(["🏡 정착 추천 동네 (법정동)", "🏗️ 진행 중인 공공 개발 사업 목록"])

with tab1:
    st.write(f"**{selected_gu}** 내에서 대구도시개발공사의 주요 프로젝트가 집중되어 정착하기 좋은 핵심 동네입니다.")
    unique_dongs = gu_details['동'].unique()
    for d in unique_dongs:
        st.markdown(f"- 📍 **{d}**")

with tab2:
    st.write(f"현재 **{selected_gu}**의 주거 환경을 바꾼 대구도시개발공사의 공식 사업 리스트입니다.")
    st.dataframe(gu_details.rename(columns={
        '동': '대상 동네',
        '사업지역': '프로젝트명(사업지역)',
        '사업유형': '사업 성격',
        '공급유형': '공급 형태'
    }), width='stretch')