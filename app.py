import streamlit as st
import google.generativeai as genai
from PIL import Image
from gtts import gTTS
import io
import re

# --- 1. 페이지 설정 ---
st.set_page_config(
    page_title="도겸이의 학습 도우미",
    page_icon="🐣",
    layout="centered"
)

# --- 2. CSS 스타일 (가독성 및 디자인) ---
st.markdown("""
<style>
    .stApp { background-color: #121212; color: #fff; }
    
    /* 제목 */
    h1 { color: #FFD700 !important; font-family: 'Comic Sans MS', sans-serif; text-align: center; margin-bottom: 20px; }
    
    /* 과목 선택 라디오 버튼 (가로형 + 줄바꿈 최적화) */
    .stRadio [role=radiogroup] {
        display: flex;
        flex-wrap: wrap; /* 화면 좁으면 줄바꿈 */
        justify-content: center;
        gap: 15px;
        font-size: 1.1rem;
        background-color: #1e1e1e;
        padding: 15px;
        border-radius: 15px;
        border: 1px solid #333;
    }
    
    /* 실행 버튼 */
    .stButton > button {
        width: 100%; border-radius: 15px; font-weight: bold;
        background: linear-gradient(90deg, #03C75A, #02b350);
        color: white; height: 3.5em; font-size: 1.2rem !important; border: none;
        margin-top: 20px;
    }
    
    /* 설명 박스 */
    .chat-box {
        background-color: #2b2b2b; color: #e0e0e0;
        padding: 25px; border-radius: 20px;
        line-height: 2.0; font-size: 1.3rem;
        margin-bottom: 20px; border-left: 5px solid #FFD700;
    }
    
    /* 영어 사전 카드 */
    .dic-card {
        background-color: #1e1e1e; border: 2px solid #03C75A;
        border-radius: 15px; padding: 25px; margin-top: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.5);
    }
    .dic-title { font-size: 0.9rem; color: #03C75A; margin-bottom: 5px; font-weight: bold; }
    .dic-english { font-size: 2.2rem; font-weight: bold; color: #fff; margin-bottom: 5px; }
    .dic-pronoun { font-size: 1.1rem; color: #aaa; margin-bottom: 15px; }
    .dic-meaning { font-size: 1.5rem; font-weight: bold; color: #FFD700; border-top: 1px solid #444; padding-top: 15px; margin-top: 10px; }
</style>
""", unsafe_allow_html=True)

# --- 3. [핵심] 절대 실패하지 않는 모델 찾기 함수 ---
def get_best_model():
    """
    내 API 키로 사용할 수 있는 모델 목록을 직접 조회해서,
    가장 적합한 모델의 '정확한 이름'을 반환합니다.
    """
    api_key = st.secrets.get("GOOGLE_API_KEY")
    if not api_key:
        return None, "API 키가 없습니다."

    try:
        genai.configure(api_key=api_key)
        
        # 1. 사용 가능한 모델 리스트 조회
        available_models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m)
        
        if not available_models:
            return None, "사용 가능한 모델이 없습니다. (API 키 권한 확인 필요)"

        # 2. 우선순위: Flash > Pro > 아무거나
        # 이름에 'flash'가 들어가는 최신 모델을 찾습니다.
        target_model = None
        for m in available_models:
            if 'flash' in m.name:
                target_model = m.name
                break
        
        # Flash가 없으면 Pro를 찾습니다.
        if not target_model:
            for m in available_models:
                if 'pro' in m.name:
                    target_model = m.name
                    break
        
        # 그것도 없으면 리스트의 첫 번째 모델을 씁니다.
        if not target_model:
            target_model = available_models[0].name
            
        return target_model, None # 성공 시 모델명 반환

    except Exception as e:
        return None, f"구글 서버 연결 실패: {str(e)}"

# --- 4. 오디오 생성 ---
def generate_audio(text):
    if not text: return None
    try:
        tts = gTTS(text=text, lang='en')
        fp = io.BytesIO()
        tts.write_to_fp(fp)
        return fp
    except: return None

# --- 5. UI 메인 ---
st.title("🐣 도겸이의 학습 도우미 ✏️")

# 과목 선택 (6개 과목, 가로형)
subject = st.radio(
    "어떤 공부를 할까요?",
    ["국어 📖", "영어 🅰️", "수학 🔢", "사회 🏘️", "과학 🧪", "기타 🌈"],
    horizontal=True,
    index=2 # 기본값: 수학
)

with st.container():
    col1, col2 = st.columns([3, 1])
    with col1:
        user_question = st.text_input("궁금한 내용을 적어봐!", placeholder="예: 135*125 / 나비의 한살이")
    with col2:
        uploaded_file = st.file_uploader("📷", type=["jpg", "png"], label_visibility="collapsed")

    # --- 프롬프트 설정 (과목별 로직) ---
    base_prompt = """
    당신은 초등학교 2학년 '도겸'이의 세상에서 제일 친절한 AI 선생님입니다.
    어려운 단어는 절대 쓰지 말고, "~해요", "~란다" 처럼 부드럽게 말하세요.
    글을 읽기 편하게 줄바꿈을 아주 자주 하세요.
    """
    
    system_instruction = base_prompt
    
    if "영어" in subject:
        system_instruction += """
        [영어 규칙]
        1. 질문에 대해 한국어로 먼저 설명하세요.
        2. 마지막에 **오늘의 단어/문장**을 아래 카드로 만드세요.
        ///DIC_START///
        영어문장
        한국어발음
        한국어뜻
        ///DIC_END///
        """
    elif "수학" in subject:
        system_instruction += """
        [수학 규칙]
        1. 답만 띡 알려주지 마세요.
        2. **풀이 과정**을 차근차근 단계별로 보여주세요.
        3. 곱셈은 숫자를 쪼개서 설명하거나(예: 100을 곱하고...), 세로셈 방법을 말로 풀어서 설명하세요.
        """
    elif "과학" in subject or "사회" in subject:
        system_instruction += """
        [과학/사회 규칙]
        1. "왜 그럴까?"에 대해 재미있는 이야기처럼 설명하세요.
        2. 주변에서 볼 수 있는 예시(학교, 집, 공원)를 들어주세요.
        """

# --- 실행 로직 ---
if st.button("도겸이 궁금증 해결! 🔍", use_container_width=True):
    if user_question or uploaded_file:
        with st.spinner("AI 짝꿍이 찾아보고 있어요... 🧠"):
            # 1. 모델 이름 가져오기 (동적 할당)
            model_name, error_msg = get_best_model()
            
            if error_msg:
                st.error("🚫 연결 실패")
                st.info(f"이유: {error_msg}")
            else:
                try:
                    # 2. 진짜 모델 연결
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_instruction
                    )
                    
                    inputs = [user_question] if user_question else []
                    if uploaded_file: inputs.append(Image.open(uploaded_file))
                    
                    # 3. 답변 생성
                    response = model.generate_content(inputs)
                    full_text = response.text
                    
                    # 4. 결과 파싱
                    explanation = full_text
                    card_data = None
                    
                    if "영어" in subject and "///DIC_START///" in full_text:
                        pattern = r"///DIC_START///(.*?)///DIC_END///"
                        match = re.search(pattern, full_text, re.DOTALL)
                        if match:
                            explanation = full_text.replace(match.group(0), "").strip()
                            lines = match.group(1).strip().split('\n')
                            card_data = [line.strip() for line in lines if line.strip()]
                    
                    # 5. 화면 출력
                    if explanation:
                        st.markdown(f'<div class="chat-box">{explanation}</div>', unsafe_allow_html=True)
                    
                    if card_data and len(card_data) >= 3:
                        eng_text, pronoun, meaning = card_data[0], card_data[1], card_data[2]
                        st.markdown(f"""
                        <div class="dic-card">
                            <div class="dic-title">Today's English</div>
                            <div class="dic-english">{eng_text}</div>
                            <div class="dic-pronoun">[{pronoun}]</div>
                        """, unsafe_allow_html=True)
                        
                        audio_fp = generate_audio(eng_text)
                        if audio_fp: st.audio(audio_fp, format='audio/mp3')
                        
                        st.markdown(f"""
                            <div class="dic-meaning">{meaning}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                except Exception as e:
                    # 모델 호출 중 에러 (429 등)
                    if "429" in str(e):
                        st.warning("친구가 너무 바빠서 잠깐 쉬고 싶대요. 1분만 있다가 다시 물어봐요! 😴")
                    else:
                        st.error("답변을 만드는 중에 실수가 있었어요. 다시 한 번 눌러주세요!")
                        st.caption(f"Error: {e}")
    else:
        st.warning("질문을 입력하거나 사진을 올려주세요!")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #555;'>도겸이를 위한 똑똑한 AI 친구 🐣</div>", unsafe_allow_html=True)
