import streamlit as st
import pandas as pd
import os
import re

# 1. 페이지 설정 (최상단 고정)
st.set_page_config(page_title="대구 동네 정착 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# 2. 데이터 로드 및 자동 융합 함수 (인코딩 방어 적용)
@st.cache_data
def load_and_merge_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_loc_path = os.path.join(current_dir, '대구도시개발공사_사업소재지정보_20230821.csv')
    file_code_path = os.path.join(current_dir, '대구도시개발공사_도시개발사업코드정보_20230821.csv')

    try:
        df_loc = pd.read_csv(file_loc_path, encoding='cp949', encoding_errors='ignore')
        df_code = pd.read_csv(file_code_path, encoding='cp949', encoding_errors='ignore')
    except TypeError:
        try:
            df_loc = pd.read_csv(file_loc_path, encoding='cp949', errors='ignore')
            df_code = pd.read_csv(file_code_path, encoding='cp949', errors='ignore')
        except TypeError:
            try:
                df_loc = pd.read_csv(file_loc_path, encoding='cp949')
                df_code = pd.read_csv(file_code_path, encoding='cp949')
            except Exception:
                df_loc = pd.read_csv(file_loc_path, encoding='utf-8')
                df_code = pd.read_csv(file_code_path, encoding='utf-8')
    except FileNotFoundError as e:
        st.error(f"⚠️ 원본 CSV 파일이 프로젝트 폴더에 없습니다: {e.filename}")
        st.stop()
    except Exception as e:
        st.error(f"데이터를 읽는 중 예측하지 못한 오류가 발생했습니다: {e}")
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
    score_board = pd.DataFrame(0.0, index=gus, columns=['청년점수', '가족점수', '산업점수', '종합_Vibe_Index'])
    
    for idx, row in df_data.iterrows():
        gu = row['gu'] if 'gu' in row else row['구']
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

# [신규 추가] 4-2. 지도 시각화를 위한 대구 구군별 위경도 좌표 데이터 매핑 정의
geo_data = {
    '중구': [35.8693, 128.6062],
    '동구': [35.8864, 128.6355],
    '서구': [35.8718, 128.5592],
    '남구': [35.8463, 128.5911],
    '북구': [35.8920, 128.5830],
    '수성구': [35.8564, 128.6258],
    '달서구': [35.8294, 128.5323],
    '달성군': [35.7746, 128.4312],
    '군위군': [36.2423, 128.5728] # 군위군 데이터 대비 예방용 포함
}

# 지도 전용 데이터프레임 빌딩
map_list = []
for gu_name, score_row in result_index.iterrows():
    if gu_name in geo_data:
        vibe_score = score_row['종합_Vibe_Index']
        map_list.append({
            '구': gu_name,
            'lat': geo_data[gu_name][0],
            'lon': geo_data[gu_name][1],
            # 추천 지수가 높을수록 지도 위의 원 크기를 더 크게 동적으로 조절 (시각 효과)
            '원크기': float(vibe_score * 30 + 500)
        })
df_map = pd.DataFrame(map_list)

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
    
    st.write("")
    st.write("📊 **대구 주요 구·군별 정착 적합도 점수**")
    st.bar_chart(result_index['종합_Vibe_Index'])

with col2:
    st.subheader("🗺️ 대구 라이프스타일 추천 맵")
    st.write("내 성향에 적합한 구역일수록 지도 위에 **더 크고 선명한 원**으로 표시됩니다.")
    
    # Streamlit 내장 위경도 맵 스크린 구현
    if not df_map.empty:
        st.map(df_map, latitude='lat', longitude='lon', size='원크기', color='#FF4B4B')
    else:
        st.warning("지도 표시에 필요한 매칭 데이터가 부족합니다.")

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