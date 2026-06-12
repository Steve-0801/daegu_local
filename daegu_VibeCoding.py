import streamlit as st
import pandas as pd
import os
import re

# 1. ÆäÀÌÁö ¼³Á¤
st.set_page_config(page_title="´ë±¸ µ¿³× Á¤Âø ½Ã¹Ä·¹ÀÌÅÍ", layout="wide", initial_sidebar_state="expanded")

# 2. µ¥ÀÌÅÍ ·Îµå ¹× ÀÚµ¿ À¶ÇÕ ÇÔ¼ö (ÀÎÄÚµù ¿¡·¯ ¹æ¾î Àû¿ë)
@st.cache_data
def load_and_merge_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # À¯Àú´ÔÀÌ °¡Áö°í °è½Å °ø°øµ¥ÀÌÅÍ ¿øº» ÆÄÀÏ 2°³ °æ·Î ¼³Á¤
    file_loc_path = os.path.join(current_dir, '´ë±¸µµ½Ã°³¹ß°ø»ç_»ç¾÷¼ÒÀçÁöÁ¤º¸_20230821.csv')
    file_code_path = os.path.join(current_dir, '´ë±¸µµ½Ã°³¹ß°ø»ç_µµ½Ã°³¹ß»ç¾÷ÄÚµåÁ¤º¸_20230821.csv')
    
    # [ÇÙ½É] CP949 ÀÎÄÚµùÀ¸·Î ¸ÕÀú ½ÃµµÇÏ°í, ½ÇÆĞ ½Ã UTF-8·Î ÀĞµµ·Ï ¹æ¾î ÄÚµù
    try:
        df_loc = pd.read_csv(file_loc_path, encoding='cp949')
        df_code = pd.read_csv(file_code_path, encoding='cp949')
    except (UnicodeDecodeError, TypeError):
        df_loc = pd.read_csv(file_loc_path, encoding='utf-8')
        df_code = pd.read_csv(file_code_path, encoding='utf-8')
    except FileNotFoundError as e:
        st.error(f"?? ¿øº» CSV ÆÄÀÏÀÌ ÇÁ·ÎÁ§Æ® Æú´õ¿¡ ¾ø½À´Ï´Ù: {e.filename}")
        st.info("µÎ °³ÀÇ ¿øº» CSV ÆÄÀÏ¸íÀÌ Á¤È®ÇÑÁö, ÆÄÀÌ½ã ÆÄÀÏ°ú °°Àº Æú´õ¿¡ ÀÖ´ÂÁö È®ÀÎÇØÁÖ¼¼¿ä.")
        st.stop()

    # µÎ µ¥ÀÌÅÍ¸¦ °áÇÕÇÏ°í ÁÖ¼Ò¸¦ Á¤Á¦ÇÏ´Â ÇÁ·Î¼¼½º (ÃÖÃÊ 1È¸¸¸ ½ÇÇà ÈÄ Ä³½ÌµÊ)
    enriched_data = []
    for idx, row in df_loc.iterrows():
        lp = row['»ç¾÷Áö¿ª']
        
        # ÇÁ·ÎÁ§Æ®¸í ¸ÅÄª ¾Ë°í¸®Áò
        c_name, c_type, s_type = "±âÅ¸ °³¹ß»ç¾÷", "±âÅ¸", "±âÅ¸"
        lp_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(lp))
        for _, c_row in df_code.iterrows():
            c_name_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(c_row['»ç¾÷¸í']))
            c_dist_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(c_row['»ç¾÷Áö±¸']))
            if (c_name_clean in lp_clean) or (lp_clean in c_name_clean) or (c_dist_clean in lp_clean) or (lp_clean in c_dist_clean):
                c_name = c_row['»ç¾÷¸í']
                c_type = c_row['»ç¾÷À¯Çü']
                s_type = c_row['°ø±ŞÀ¯Çü']
                break
                
        # ¹ıÁ¤µ¿ ÁÖ¼Ò¿¡¼­ '±¸'¿Í 'µ¿' ºĞ¸® ÃßÃâ
        full_dong = row['¹ıÁ¤µ¿']
        parts = str(full_dong).split()
        gu = parts[1] if len(parts) > 1 else "±âÅ¸"
        dong = " ".join(parts[2:]) if len(parts) > 2 else "±âÅ¸"
        
        enriched_data.append({
            '»ç¾÷Áö¿ª': lp,
            '±¸': gu,
            'µ¿': dong,
            '»ç¾÷¸í_¿¬°è': c_name,
            '»ç¾÷À¯Çü': c_type,
            '°ø±ŞÀ¯Çü': s_type
        })
        
    return pd.DataFrame(enriched_data)

# µ¥ÀÌÅÍ ·Îµå ½ÇÇà
df = load_and_merge_data()

# 3. »çÀÌµå¹Ù - À¯Àú ¼ºÇâ ÀÔ·Â ÀÎÅÍÆäÀÌ½º
st.sidebar.header("?? ³ªÀÇ ¶óÀÌÇÁ½ºÅ¸ÀÏ ¼ºÇâ ¼³Á¤")
st.sidebar.write("´ç½ÅÀÇ °¡Ä¡°ü¿¡ µû¶ó °¡ÁßÄ¡¸¦ Á¶ÀıÇØÁÖ¼¼¿ä.")

vibe_youth = st.sidebar.slider("?? Ã»³â/1ÀÎ °¡±¸ ÁÖ°Å (ÀÓ´ëÁÖÅÃ ÆíÀÇ¼º)", 0, 100, 50)
vibe_family = st.sidebar.slider("?? °¡Á·/³»Áı¸¶·Ã (°ø°øºĞ¾ç, ¾ÆÆÄÆ® ´ÜÁö)", 0, 100, 50)
vibe_job = st.sidebar.slider("?? Á÷ÁÖ±ÙÁ¢/¹Ì·¡°¡Ä¡ (»ê¾÷´ÜÁö, °³¹ßÁö±¸)", 0, 100, 50)

# 4. Local Vibe Index °è»ê ¾Ë°í¸®Áò
def calculate_vibe_index(df_data, w_youth, w_family, w_job):
    gus = df_data['±¸'].unique()
    score_board = pd.DataFrame(0.0, index=gus, columns=['Ã»³âÁ¡¼ö', '°¡Á·Á¡¼ö', '»ê¾÷Á¡¼ö', 'Á¾ÇÕ_Vibe_Index'])
    
    for idx, row in df_data.iterrows():
        gu = row['±¸']
        b_type = row['»ç¾÷À¯Çü']
        p_name = row['»ç¾÷Áö¿ª']
        
        if b_type in ['Çàº¹ÁÖÅÃÀÓ´ë', '´Ù°¡±¸ÀÓ´ë'] or 'ÀÓ´ë' in str(p_name):
            score_board.loc[gu, 'Ã»³âÁ¡¼ö'] += 3.0
        if b_type == '¾ÆÆÄÆ®ºĞ¾ç' or 'Ã»¾Æ¶÷' in str(p_name) or '¾ÆÆÄÆ®' in str(p_name):
            score_board.loc[gu, '°¡Á·Á¡¼ö'] += 3.0
        if '»ê¾÷´ÜÁö' in str(p_name) or 'ÀÇ·áÁö±¸' in str(p_name) or '°úÇĞ»ê¾÷' in str(p_name):
            score_board.loc[gu, '»ê¾÷Á¡¼ö'] += 4.0
        elif b_type == 'ÅÃÁöºĞ¾ç':
            score_board.loc[gu, '»ê¾÷Á¡¼ö'] += 1.5
            
    for col in ['Ã»³âÁ¡¼ö', '°¡Á·Á¡¼ö', '»ê¾÷Á¡¼ö']:
        max_val = score_board[col].max()
        if max_val > 0:
            score_board[col] = (score_board[col] / max_val) * 100
            
    total_w = w_youth + w_family + w_job
    if total_w > 0:
        score_board['Á¾ÇÕ_Vibe_Index'] = (
            (score_board['Ã»³âÁ¡¼ö'] * w_youth) + 
            (score_board['°¡Á·Á¡¼ö'] * w_family) + 
            (score_board['»ê¾÷Á¡¼ö'] * w_job)
        ) / total_w
    else:
        score_board['Á¾ÇÕ_Vibe_Index'] = 0.0
        
    return score_board.sort_values(by='Á¾ÇÕ_Vibe_Index', ascending=False)

result_index = calculate_vibe_index(df, vibe_youth, vibe_family, vibe_job)

# 5. ¸ŞÀÎ È­¸é UI ·¹ÀÌ¾Æ¿ô
st.title("??? ´ë±¸ ·ÎÄÃ ÀÌÁÖÀÚ¸¦ À§ÇÑ 'µ¿³× Á¤Âø ½Ã¹Ä·¹ÀÌÅÍ'")
st.markdown("´ë±¸µµ½Ã°³¹ß°ø»çÀÇ **°ø°ø °³¹ß ¹× ÁÖÅÃ °ø±Ş µ¥ÀÌÅÍ**¸¦ ±â¹İÀ¸·Î ´ç½ÅÀÇ ¶óÀÌÇÁ½ºÅ¸ÀÏ¿¡ °¡Àå Àß ¸Â´Â Áö¿ªÀ» ÃßÃµÇÕ´Ï´Ù.")
st.write("---")

top_gu = result_index.index[0]
top_score = result_index.iloc[0]['Á¾ÇÕ_Vibe_Index']

col1, col2 = st.columns([2, 3])

with col1:
    st.subheader("?? ´ç½ÅÀ» À§ÇÑ ÃÖÀûÀÇ ÃßÃµ Áö¿ª")
    st.metric(label="ÃßÃµ 1¼øÀ§ Áö¿ª±¸", value=f"´ë±¸±¤¿ª½Ã {top_gu}", delta=f"¸ÅÄª Á¡¼ö: {top_score:.1f}Á¡")
    st.write(f"ÇöÀç ¼±ÅÃÇÏ½Å ¼ºÇâ ºĞ¼® °á°ú, ´ë±¸µµ½Ã°³¹ß°ø»ç°¡ ÁøÇàÇÏ´Â °ø°ø ÀÎÇÁ¶ó »ç¾÷ÀÇ ¼º°İÀÌ **{top_gu}**¿Í °¡Àå ÀÏÄ¡ÇÕ´Ï´Ù.")

with col2:
    st.subheader("?? ´ë±¸ ÁÖ¿ä ±¸¡¤±ºº° Á¤Âø ÀûÇÕµµ Á¡¼ö")
    st.bar_chart(result_index['Á¾ÇÕ_Vibe_Index'])

st.write("---")

st.subheader("?? ÃßÃµ Áö¿ª »ó¼¼ µé¿©´Ùº¸±â")
selected_gu = st.selectbox("¾î´À Áö¿ª±¸ÀÇ »ó¼¼ µ¿³× È£Àç¸¦ È®ÀÎÇØº¼±î¿ä?", result_index.index)

gu_details = df[df['±¸'] == selected_gu][['µ¿', '»ç¾÷Áö¿ª', '»ç¾÷À¯Çü', '°ø±ŞÀ¯Çü']].drop_duplicates()

tab1, tab2 = st.tabs(["?? Á¤Âø ÃßÃµ µ¿³× (¹ıÁ¤µ¿)", "??? ÁøÇà ÁßÀÎ °ø°ø °³¹ß »ç¾÷ ¸ñ·Ï"])

with tab1:
    st.write(f"**{selected_gu}** ³»¿¡¼­ ´ë±¸µµ½Ã°³¹ß°ø»çÀÇ ÁÖ¿ä ÇÁ·ÎÁ§Æ®°¡ ÁıÁßµÇ¾î Á¤ÂøÇÏ±â ÁÁÀº ÇÙ½É µ¿³×ÀÔ´Ï´Ù.")
    unique_dongs = gu_details['µ¿'].unique()
    for d in unique_dongs:
        st.markdown(f"- ?? **{d}**")

with tab2:
    st.write(f"ÇöÀç **{selected_gu}**ÀÇ ÁÖ°Å È¯°æÀ» ¹Ù²Û ´ë±¸µµ½Ã°³¹ß°ø»çÀÇ °ø½Ä »ç¾÷ ¸®½ºÆ®ÀÔ´Ï´Ù.")
    st.dataframe(gu_details.rename(columns={
        'µ¿': '´ë»ó µ¿³×',
        '»ç¾÷Áö¿ª': 'ÇÁ·ÎÁ§Æ®¸í(»ç¾÷Áö¿ª)',
        '»ç¾÷À¯Çü': '»ç¾÷ ¼º°İ',
        '°ø±ŞÀ¯Çü': '°ø±Ş ÇüÅÂ'
    }), width='stretch')