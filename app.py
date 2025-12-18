import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="2학년 공부 짝꿍", page_icon="🐥", layout="centered")

# --- 2. Custom CSS (줄 간격 및 가독성) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton > button {
        width: 100%; border-radius: 15px; font-weight: bold;
        background-color: #FFBD45; color: black;
    }
    .answer-text { line-height: 2.0; font-size: 1.15rem; }
    .eng-box { 
        background-color: #1e2129; padding: 10px; 
        border-radius: 10px; border-left: 5px solid #FFBD45;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 영어 발음 생성 함수 ---
def play_eng_sound(text, index):
    # 영어만 추출 (한글 발음 기호 제외)
    clean_eng = re.sub(r'[ㄱ-ㅎㅏ-ㅣ가-힣]', '', text).replace('[', '').replace(']', '').strip()
    if clean_eng:
        tts = gTTS(text=clean_eng, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')

# --- 4. API 설정 ---
def configure_genai():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.warning("🚨 API Key가 필요해요!")
        st.stop()
    genai.configure(api_key=api_key)

# --- 5. 메인 UI ---
st.title("🐥 2학년 공부 짝꿍")
configure_genai()

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어", "수학", "국어", "기타"])
    uploaded_file = st.file_uploader("📸 사진 찍어 올리기", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("질문을 짧게 적어줘요!", placeholder="예: an apple이 왜 맞아?")

    # 시스템 프롬프트: 개조식 및 특수 태그 사용 지시
    system_prompt = f"""
    당신은 초등학교 2학년 튜터입니다.
    
    [답변 규칙]
    1. 모든 답변은 한 줄에 15자 내외의 **짧은 개조식**으로 작성하세요.
    2. 문장마다 앞에 이모지(✅, 📍, ⭐)를 붙이고 반드시 **줄바꿈**을 하세요.
    3. 영어 문장은 반드시 [ENG]문장[/ENG] 태그로 감싸주세요. (예: [ENG]an apple[/ENG])
    4. 영어 옆에는 한글 발음을 써주세요.
    
    [출력 예시]
    🎈 정말 멋진 질문이야!
    
    ✅ **정답: an apple 이 맞아요.**
    
    📍 **이유를 알아봐요:**
    - a, e, i, o, u 소리로 시작하면
    - 'a' 대신 'an'을 써요.
    
    🎧 **발음을 들어봐요:**
    [ENG]an apple[/ENG] [언 애-플]
    """

if st.button("짝꿍아 알려줘! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("생각 중... ✨"):
                model = genai.GenerativeModel("gemini-1.5-flash", system_instruction=system_prompt)
                img = Image.open(uploaded_file) if uploaded_file else None
                content = [user_question] if user_question else []
                if img: content.append(img)
                
                response = model.generate_content(content)
                raw_text = response.text

            st.balloons()
            
            # --- 결과 파싱 및 출력 ---
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명", "🔍 전체 보기"])
            
            with tab1:
                # 1. [ENG] 태그를 기준으로 텍스트 분리
                parts = re.split(r'(\[ENG\].*?\[/ENG\])', raw_text, flags=re.DOTALL)
                
                for idx, part in enumerate(parts):
                    if part.startswith('[ENG]'):
                        # 영어 부분 처리
                        eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                        st.markdown(f"**🎧 발음 연습:** `{eng_text}`")
                        play_eng_sound(eng_text, idx) # 해당 부분만 오디오 생성
                    else:
                        # 일반 텍스트 처리 (불필요한 공백 제거 및 줄바꿈 강조)
                        clean_part = part.strip()
                        if clean_part:
                            st.markdown(f'<div class="answer-text">{clean_part}</div>', unsafe_allow_html=True)
                
            with tab2:
                st.code(raw_text)

        except Exception as e:
            st.error(f"에러가 났어요 💦 {e}")
