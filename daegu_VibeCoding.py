@st.cache_data
def load_and_merge_data():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    file_loc_path = os.path.join(current_dir, '´ë±¸µµ½Ã°³¹ß°ø»ç_»ç¾÷¼ÒÀçÁöÁ¤º¸_20230821.csv')
    file_code_path = os.path.join(current_dir, '´ë±¸µµ½Ã°³¹ß°ø»ç_µµ½Ã°³¹ß»ç¾÷ÄÚµåÁ¤º¸_20230821.csv')
    
    # errors='ignore' ¶Ç´Â encoding_errors='ignore' ¿É¼ÇÀ» Ãß°¡ÇÏ¿© ºÒ·® ¹ÙÀÌÆ®¸¦ °­Á¦ ÆÐ½ºÇÕ´Ï´Ù.
    try:
        df_loc = pd.read_csv(file_loc_path, encoding='cp949', errors='ignore')
        df_code = pd.read_csv(file_code_path, encoding='cp949', errors='ignore')
    except Exception:
        try:
            df_loc = pd.read_csv(file_loc_path, encoding='utf-8', errors='ignore')
            df_code = pd.read_csv(file_code_path, encoding='utf-8', errors='ignore')
        except FileNotFoundError as e:
            st.error(f"?? ¿øº» CSV ÆÄÀÏÀÌ ÇÁ·ÎÁ§Æ® Æú´õ¿¡ ¾ø½À´Ï´Ù: {e.filename}")
            st.stop()
        except Exception as e:
            # ÃÖÁ¾ ¿¹¿Ü »óÈ²¿¡¼­´Â À¯Àú°¡ ÀÎ½ÄÇÒ ¼ö ÀÖ°Ô ¿¡·¯ ¹®±¸ Ãâ·Â
            st.error(f"µ¥ÀÌÅÍ¸¦ ÀÐ´Â Áß ¿¹ÃøÇÏÁö ¸øÇÑ ÀÎÄÚµù ¿À·ù°¡ ¹ß»ýÇß½À´Ï´Ù: {e}")
            st.stop()

    # (ÀÌÇÏ µ¥ÀÌÅÍ À¶ÇÕ ·ÎÁ÷Àº µ¿ÀÏ...)
    enriched_data = []
    for idx, row in df_loc.iterrows():
        lp = row['»ç¾÷Áö¿ª']
        c_name, c_type, s_type = "±âÅ¸ °³¹ß»ç¾÷", "±âÅ¸", "±âÅ¸"
        lp_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(lp))
        for _, c_row in df_code.iterrows():
            c_name_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(c_row['»ç¾÷¸í']))
            c_dist_clean = re.sub(r'[^°¡-ÆR0-9a-zA-Z]', '', str(c_row['»ç¾÷Áö±¸']))
            if (c_name_clean in lp_clean) or (lp_clean in c_name_clean) or (c_dist_clean in lp_clean) or (lp_clean in c_dist_clean):
                c_name = c_row['»ç¾÷¸í']
                c_type = c_row['»ç¾÷À¯Çü']
                s_type = c_row['°ø±ÞÀ¯Çü']
                break
                
        full_dong = row['¹ýÁ¤µ¿']
        parts = str(full_dong).split()
        gu = parts[1] if len(parts) > 1 else "±âÅ¸"
        dong = " ".join(parts[2:]) if len(parts) > 2 else "±âÅ¸"
        
        enriched_data.append({
            '»ç¾÷Áö¿ª': lp,
            '±¸': gu,
            'µ¿': dong,
            '»ç¾÷¸í_¿¬°è': c_name,
            '»ç¾÷À¯Çü': c_type,
            '°ø±ÞÀ¯Çü': s_type
        })
        
    return pd.DataFrame(enriched_data)