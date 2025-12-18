import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re
import time

# --- 1. 페이지 설정 (도겸이 전용) ---
st.set_page_config(
    page_title="도겸이의 학습 도우미",
    page_icon="🐣",
    layout="centered"
)

# --- 2. Custom CSS (아이들을 위한 디자인) ---
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0e1117; color: #fff; }
    
    /* 제목 스타일 */
    h1 { 
        color: #FFD700 !important; 
        text-align: center; 
        font-family: 'Comic Sans MS', sans-serif;
        text-shadow: 2px 2px #333;
    }
    
    /* 큰 버튼 */
    .stButton > button {
        width: 100%; border-radius: 30px; font-weight: bold;
        background: linear-gradient(45deg, #FFBD45, #FFD54F);
        color: black; height: 3.5em; font-size: 1.3rem !important;
        border: none; box-shadow: 0px 4px 15px rgba(255, 189, 69, 0.4);
    }
    
    /* 답변 박스 디자인 */
    .answer-text { 
        line-height: 2.8; 
        font-size: 1.4rem; 
        word-break: keep-all;
        margin-bottom: 25px;
        color: #ffffff;
        background: #1e2129;
        padding: 25px;
        border-radius: 20px;
        border-left: 5px solid #FFBD45;
    }
    
    /* 영어 발음 박스 */
    .eng-box {
        background-color: #2E3440; padding: 20px; 
        border-radius: 20px; border: 2px dashed #81A1C1;
        margin: 20px 0;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. [핵심] 작동하는 모델 자동 찾기 함수 ---
def get_working_model():
    """
    여러 모델 이름 후보 중 실제로 에러 없이 작동하는 것을 찾아냅니다.
    404 에러를 방지하는 최후의 수단입니다.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("API Key가 없어요! 설정(Secrets)을 확인해주세요.")
        st.stop()
    
    genai.configure(api_key=api_key)
    
    # 시도해볼 모델 후보군 (우선순위 순서)
    # models/ 접두사가 있는 것과 없는 것을 모두 테스트합니다.
    candidates = [
        "gemini-1.5-flash",
        "models/gemini-1.5-flash",
        "gemini-1.5-flash-latest",
        "gemini-1.5-pro",
        "gemini-pro",
        "gemini-1.0-pro"
    ]
    
    for model_name in candidates:
        try:
            # 모델을 연결하고 아주 간단한 테스트를 해봅니다.
            model = genai.GenerativeModel(model_name)
            # 1토큰만 생성해보고 에러가 안 나면 이 모델 당첨!
            model.generate_content("Hi", generation_config={'max_output_tokens': 1})
            return model_name # 성공한 모델 이름 반환
        except Exception:
            continue # 실패하면 다음 후보로 넘어감
            
    # 모든 후보가 실패했을 때
    return None

# --- 4. 영어 발음 듣기 ---
def play_eng_audio(text):
    clean_text = re.sub(r'[^a-zA-Z\s]', '', text).strip()
    if clean_text:
        try:
            tts = gTTS(text=clean_text, lang='en')
            fp = io.BytesIO()
            tts.write_to_fp(fp)
            st.audio(fp, format='audio/mp3')
        except:
            pass

# --- 5. UI 메인 화면 ---
st.title("🐣 도겸이의 학습 도우미 ✏️")
st.markdown("<div style='text-align: center; color: #aaa; margin-bottom: 20px;'>모르는 건 짝꿍에게 물어봐!</div>", unsafe_allow_html=True)

with st.container():
    col1, col2 = st.columns([1, 2])
    
    subject = st.selectbox("어떤 공부인가요?", ["영어 🅰️", "수학 🔢", "국어 📖", "기타 🌈"], index=0)
    uploaded_file = st.file_uploader("📸 사진을 보여줄까요?", type=["jpg", "png", "jpeg"])
    user_question = st.text_input("궁금한 걸 적어주세요!", placeholder="예: apple이 뭐야?")

    # 도겸이(2학년) 맞춤형 프롬프트
    system_instruction = f"""
    당신은 '도겸'이라는 초등학교 2학년 학생의 가장 친한 AI 단짝 친구입니다.
    
    [도겸이를 위한 답변 규칙]
    1. 답변은 무조건 **짧게 끊어서** 말해주세요. (긴 글은 읽기 힘들어요)
    2. 문장 사이에는 줄바꿈을 2번씩 해서 **간격을 넓혀주세요.**
    3. **영어 단어/문장**이 나오면 반드시 [ENG]영어[/ENG] 형태로 감싸주세요.
    4. 말투: "~했어?", "~란다", "도겸아, 이건 말이야~" 처럼 다정하게 이름을 불러주세요.
    5. 칭찬을 많이 해주세요.
    """

if st.button("도겸이 궁금증 해결! 🚀", use_container_width=True):
    if user_question or uploaded_file:
        status_container = st.empty() # 상태 메시지용 컨테이너
        
        try:
            status_container.info("🧠 짝꿍이 뇌를 깨우는 중... (모델 찾는 중)")
            
            # 1. 작동하는 모델 찾기
            best_model_name = get_working_model()
            
            if not best_model_name:
                status_container.error("😢 모든 AI 모델이 잠들어 있어요. API 키를 확인하거나 잠시 후 다시 시도해주세요.")
            else:
                status_container.info(f"✨ {best_model_name} 모델로 생각하는 중...")
                
                # 2. 모델 설정 및 호출
                model = genai.GenerativeModel(
                    model_name=best_model_name,
                    system_instruction=system_instruction
                )
                
                inputs = []
                if user_question: inputs.append(user_question)
                if uploaded_file: inputs.append(Image.open(uploaded_file))
                
                response = model.generate_content(inputs)
                answer = response.text
                
                status_container.empty() # 상태 메시지 지우기
                st.balloons()
                
                # 3. 결과 출력
                tab1, tab2 = st.tabs(["🎈 도겸이의 대답", "🔍 엄마/아빠 확인용"])
                
                with tab1:
                    # [ENG] 태그 파싱 및 출력
                    parts = re.split(r'(\[ENG\].*?\[/ENG\])', answer, flags=re.DOTALL)
                    for part in parts:
                        if part.startswith('[ENG]'):
                            eng_text = part.replace('[ENG]', '').replace('[/ENG]', '')
                            st.markdown(f'<div class="eng-box"><b>🎧 영어 듣기</b>', unsafe_allow_html=True)
                            play_eng_audio(eng_text)
                            st.markdown(f'<span style="font-size: 1.8rem; color: #88C0D0;"><b>{eng_text}</b></span></div>', unsafe_allow_html=True)
                        else:
                            if part.strip():
                                st.markdown(f'<div class="answer-text">{part.strip()}</div>', unsafe_allow_html=True)
                
                with tab2:
                    st.success(f"연결 성공! 사용된 모델: {best_model_name}")
                    st.code(answer)

        except Exception as e:
            st.error("앗! AI 친구가 잠깐 쉬고 싶대요. 1분 뒤에 다시 물어봐 줄래요? 😴")
            st.caption(f"Error Details: {e}")
    else:
        st.warning("질문을 적거나 사진을 올려주세요! 😉")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #666;'>도겸이를 위한 특별한 학습 도우미 ❤️</div>", unsafe_allow_html=True)
