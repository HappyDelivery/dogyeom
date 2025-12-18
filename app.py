import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 및 기본 설정 ---
st.set_page_config(page_title="2학년 공부 짝꿍", page_icon="🐥", layout="centered")

# --- 2. Custom CSS (가독성 최적화) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    .stButton > button {
        width: 100%; border-radius: 15px; font-weight: bold;
        background-color: #FFBD45; color: black; height: 3em;
    }
    .answer-text { line-height: 2.2; font-size: 1.2rem; margin-bottom: 15px; }
    .eng-audio-box { 
        background-color: #262730; padding: 15px; 
        border-radius: 12px; border: 1px solid #FFBD45;
        margin: 10px 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 8px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 모델 동적 로드 함수 (에러 방지 핵심!) ---
def get_best_model():
    try:
        # 사용 가능한 모델 목록을 가져옵니다.
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                # 가장 빠르고 똑똑한 gemini-1.5-flash 시리즈를 우선 선택
                if 'gemini-1.5-flash' in m.name:
                    return m.name
        return "models/gemini-1.5-flash" # 기본값
    except Exception:
        return "gemini-1.5-flash" # 예외 시 문자열로 시도

# --- 4. 영어 발음 생성 함수 ---
def play_eng_sound(text):
    # 영어만 추출 (한글 및 특수문자 제거)
    clean_eng = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_eng:
        tts = gTTS(text=clean_eng, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        st.audio(fp, format='audio/mp3')

# --- 5. API 설정 ---
def configure_genai():
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.warning("🚨 API Key가 필요해요! (secrets.toml 확인)")
        st.stop()
    genai.configure(api_key=api_key)

# --- 6. 메인 UI 구성 ---
st.title("🐥 2학년 공부 짝꿍")
configure_genai()

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어", "수학", "국어", "기타"])
    uploaded_file = st.file_uploader("📸 사진 찍어 올리기", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("질문을 짧게 적어줘요!", placeholder="예: an apple이 왜 맞아?")

    # 2학년 맞춤형 개조식 지시 프롬프트
    system_prompt = f"""
    당신은 초등학교 2학년 학생의 친절한 공부 짝꿍입니다.
    
    [중요 규칙]
    1. 모든 답변은 **짧은 문장**으로 끊어서 쓰세요.
    2. 한 줄에 글자가 많지 않게 **줄바꿈**을 자주 하세요.
    3. 문장 앞에 ✅, ⭐, 📍 같은 기호를 꼭 붙이세요.
    4. 영어 단어나 문장은 반드시 [ENG]문장[/ENG] 태그로 감싸주세요.
    5. 설명은 유치원생도 이해할 만큼 쉽게 하세요.
    """

# --- 7. 실행 로직 ---
if st.button("짝꿍아 알려줘! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("짝꿍이 생각 중이에요... ✨"):
                # 모델을 동적으로 가져와서 404 에러 방지
                model_name = get_best_model()
                model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                
                img = Image.open(uploaded_file) if uploaded_file else None
                content = [user_question] if user_question else []
                if img: content.append(img)
                
                response = model.generate_content(content)
                raw_text = response.text

            st.balloons()
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명", "🔍 전체 보기"])
            
            with tab1:
                # [ENG] 태그로 텍스트 분리 및 발음 버튼 생성
                parts = re.split(r'(\[ENG\].*?\[/ENG\])', raw_text, flags=re.DOTALL)
                
                for part in parts:
                    if part.startswith('[ENG]'):
                        # 영어 발음 박스
                        eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                        st.markdown(f"**🎧 발음 들어보기:** `{eng_text}`")
                        play_eng_sound(eng_text)
                    else:
                        # 일반 설명 (개조식 줄바꿈 적용)
                        clean_part = part.strip()
                        if clean_part:
                            st.markdown(f'<div class="answer-text">{clean_part}</div>', unsafe_allow_html=True)
                
            with tab2:
                st.code(raw_text)

        except Exception as e:
            st.error(f"앗! 오류가 났어요 💦 \n\n 이유: {str(e)}")
            st.info("Tip: API 키가 올바른지, 혹은 인터넷 연결을 확인해 보세요.")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>2학년 친구들을 위한 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
