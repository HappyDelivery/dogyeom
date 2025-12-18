import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 설정 ---
st.set_page_config(page_title="2학년 공부 짝꿍", page_icon="🐥", layout="centered")

# --- 2. Custom CSS (아이들 눈높이 가독성) ---
st.markdown("""
<style>
    .stApp { background-color: #0e1117; color: #fff; }
    /* 큰 버튼 */
    .stButton > button {
        width: 100%; border-radius: 20px; font-weight: bold;
        background-color: #FFBD45; color: black; height: 3.5em; font-size: 1.2rem !important;
    }
    /* 답변 글자 크게, 간격 넓게 */
    .answer-text { 
        line-height: 2.5; 
        font-size: 1.3rem; 
        word-break: keep-all;
        margin-bottom: 20px;
        color: #f0f0f0;
    }
    .eng-audio-box { 
        background-color: #1e2129; padding: 15px; 
        border-radius: 15px; border: 2px solid #FFBD45;
        margin: 15px 0;
    }
    .stTabs [data-baseweb="tab-list"] { gap: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. 안전한 모델 호출 함수 (404 에러 해결사) ---
def get_safe_model(api_key):
    genai.configure(api_key=api_key)
    # 시도해볼 모델 이름들 (우선순위 순)
    model_names = ["gemini-1.5-flash", "gemini-pro", "gemini-1.5-pro"]
    
    for name in model_names:
        try:
            model = genai.GenerativeModel(name)
            # 테스트 호출로 모델 유효성 확인
            model.generate_content("test", generation_config={"max_output_tokens": 1})
            return name
        except:
            continue
    return "gemini-pro" # 최후의 수단

# --- 4. 영어 발음 생성 함수 ---
def play_eng_sound(text):
    # [ENG]태그 안의 내용에서 영어만 추출
    clean_eng = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_eng:
        try:
            tts = gTTS(text=clean_eng, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
        except:
            st.warning("발음을 준비하지 못했어요 😢")

# --- 5. 메인 로직 ---
st.title("🐥 2학년 공부 짝꿍")

# API Key 확인
api_key = st.secrets.get("GOOGLE_API_KEY")
if not api_key:
    st.error("API Key가 설정되지 않았어요! (Secrets 확인)")
    st.stop()

with st.container():
    subject = st.selectbox("어떤 공부인가요?", ["영어", "수학", "국어", "슬기로운 생활"])
    uploaded_file = st.file_uploader("📸 사진을 찍어서 보여주세요", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("질문을 적어주세요!", placeholder="예: Apple이 왜 사과야?")

    # 2학년 전용 프롬프트 (극단적 개조식)
    system_prompt = f"""
    당신은 초등학교 2학년 학생의 친절한 공부 짝꿍입니다.
    
    [무조건 지킬 규칙]
    1. 답변은 한 줄에 10글자 내외로 아주 짧게 쓰세요.
    2. 모든 문장 뒤에는 줄바꿈을 2번 하세요 (글자 사이를 띄우기 위해).
    3. 영어 문장이 나오면 앞뒤에 [ENG]를 붙이세요. (예: [ENG]Thank you[/ENG])
    4. 어려운 단어는 절대 쓰지 마세요.
    """

if st.button("짝꿍아 알려줘! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        try:
            with st.spinner("짝꿍이 생각 중... 💡"):
                # 안전하게 모델 이름 결정
                target_model_name = get_safe_model(api_key)
                model = genai.GenerativeModel(
                    model_name=target_model_name,
                    system_instruction=system_prompt
                )
                
                # 이미지/텍스트 처리
                content = []
                if user_question: content.append(user_question)
                if uploaded_file: content.append(Image.open(uploaded_file))
                
                response = model.generate_content(content)
                raw_text = response.text

            st.balloons()
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명", "🔍 전체 보기"])
            
            with tab1:
                # 텍스트 분리 및 영어 발음 버튼 생성
                parts = re.split(r'(\[ENG\].*?\[/ENG\])', raw_text, flags=re.DOTALL)
                
                for part in parts:
                    if part.startswith('[ENG]'):
                        eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                        st.markdown(f"**🎧 영어 발음 듣기:**")
                        play_eng_sound(eng_text)
                        st.markdown(f"**` {eng_text} `**")
                    else:
                        clean_part = part.strip()
                        if clean_part:
                            # 개조식 줄바꿈 처리
                            st.markdown(f'<div class="answer-text">{clean_part}</div>', unsafe_allow_html=True)
                
            with tab2:
                st.info(f"사용된 모델: {target_model_name}")
                st.code(raw_text)

        except Exception as e:
            st.error(f"앗! 다시 한 번만 눌러줄래? 💦\n(이유: {str(e)})")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>2학년 친구들을 위한 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
