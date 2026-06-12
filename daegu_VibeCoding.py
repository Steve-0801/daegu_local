import streamlit as st  # 👈 이 줄이 반드시 맨 위에 완전히 살아있어야 합니다!
import pandas as pd
import os
import re

# 1. 페이지 설정
st.set_page_config(page_title="대구 동네 정착 시뮬레이터", layout="wide", initial_sidebar_state="expanded")

# 2. 데이터 로드 및 자동 융합 함수 (인코딩 에러 방어 적용)
@st.cache_data
def load_and_merge_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))

    file_loc_path = os.path.join(current_dir, '대구도시개발공사_사업소재지정보_20230821.csv')
    file_code_path = os.path.join(current_dir, '대구도시개발공사_도시개발사업코드정보_20230821.csv')

    # errors='ignore' 또는 encoding_errors='ignore' 옵션을 추가하여 불량 바이트를 강제 패스합니다.
    try:
        df_loc = pd.read_csv(file_loc_path, encoding='cp949', errors='ignore')
        df_code = pd.read_csv(file_code_path, encoding='cp949', errors='ignore')
    except Exception:
        try:
            df_loc = pd.read_csv(file_loc_path, encoding='utf-8', errors='ignore')
            df_code = pd.read_csv(file_code_path, encoding='utf-8', errors='ignore')
        except FileNotFoundError as e:
            st.error(f"원본 CSV 파일이 프로젝트 폴더에 없습니다: {e.filename}")
            st.stop()
        except Exception as e:
            # 최종 예외 상황에서는 유저가 인식할 수 있게 에러 문구 출력
            st.error(f"데이터를 읽는 중 예측하지 못한 인코딩 오류가 발생했습니다: {e}")
            st.stop()

    # (이하 데이터 융합 로직은 동일...)
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