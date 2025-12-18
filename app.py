import streamlit as st
import google.generativeai as genai
from PIL import Image
import os

# --- 1. 페이지 및 기본 설정 (귀여운 아이콘 적용) ---
st.set_page_config(
    page_title="2학년 공부 짝꿍",
    page_icon="🐥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# --- 2. Custom CSS (더 크고 둥근 UI, 따뜻한 느낌) ---
st.markdown("""
<style>
    /* 전체 폰트 및 배경 조정 */
    .stApp {
        background-color: #0e1117;
        color: #fff;
    }
    /* 버튼: 아이들이 누르기 쉽게 아주 크고 눈에 띄게 */
    .stButton > button {
        width: 100%;
        border-radius: 20px;
        height: 3.5em;
        font-size: 1.2rem !important;
        font-weight: bold;
        background-color: #FFBD45; /* 노란색 계열로 변경 */
        color: black;
        border: none;
    }
    .stButton > button:hover {
        background-color: #FFD54F;
    }
    /* 헤더 스타일 */
    h1 {
        font-size: 1.8rem !important;
        text-align: center;
        color: #FFBD45 !important;
        margin-bottom: 0.5rem;
    }
    .subtitle {
        text-align: center;
        color: #ddd;
        font-size: 1.0rem;
        margin-bottom: 2rem;
    }
    /* 입력창 라벨 크기 키우기 */
    .stSelectbox label, .stFileUploader label, .stTextArea label {
        font-size: 1.1rem !important;
    }
</style>
""", unsafe_allow_html=True)

# --- 3. API Key 및 모델 설정 로직 (기존과 동일) ---

def configure_genai():
    api_key = None
    if "GOOGLE_API_KEY" in st.secrets:
        api_key = st.secrets["GOOGLE_API_KEY"]
    
    if not api_key:
        with st.sidebar:
            st.warning("⚠️ 비밀번호(API Key)가 필요해요.")
            api_key = st.text_input("API Key 입력", type="password")
            
    if not api_key:
        st.warning("🚨 선생님을 부르려면 열쇠(Key)가 필요해요.")
        st.stop()
        
    genai.configure(api_key=api_key)
    return True

def get_available_models():
    try:
        models = []
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                models.append(m.name)
        models.sort(key=lambda x: 'flash' not in x)
        return models
    except Exception:
        return ["models/gemini-1.5-flash"]

# --- 4. 메인 UI 구성 (어린이 눈높이 용어) ---

st.title("🐥 2학년 공부 짝꿍")
st.markdown('<p class="subtitle">어려운 문제가 있나요?<br>사진을 찍거나 물어보면 친절하게 알려줄게요!</p>', unsafe_allow_html=True)

configure_genai()

with st.container():
    # 과목 선택
    subject = st.selectbox(
        "어떤 공부를 하고 있나요? 📚",
        ["수학 (덧셈, 뺄셈, 구구단)", "국어 (받아쓰기, 읽기)", "영어 (ABC, 단어)", "슬기로운 생활 (학교, 봄여름가을겨울)", "기타"],
        index=0
    )

    # 이미지 업로드
    uploaded_file = st.file_uploader("📸 문제 사진을 찰칵! 찍어 올려주세요", type=["jpg", "jpeg", "png", "webp"])
    
    image_display = None
    if uploaded_file is not None:
        image_display = Image.open(uploaded_file)
        st.image(image_display, caption="친구의 질문 사진", use_container_width=True)

    # 텍스트 질문
    user_question = st.text_area(
        "글로 물어봐도 돼요 ✏️",
        placeholder="예: 구구단 3단이 너무 어려워 / 사과(Apple)는 어떻게 읽어?",
        height=100
    )

    # 설정 숨김 (부모님용)
    with st.expander("🔒 부모님/선생님 설정 메뉴"):
        model_options = get_available_models()
        selected_model = st.selectbox("AI 모델", model_options, index=0)
        temperature = st.slider("창의성", 0.0, 1.0, 0.3)
        
        # --- [핵심] 2학년 맞춤형 프롬프트 ---
        system_prompt = f"""
        당신은 초등학교 2학년(만 8세) 아이들을 정말 사랑하는 친절한 AI 공부 짝꿍입니다.
        현재 과목은 '{subject}'입니다.

        [말투 가이드]
        1. 절대 어려운 단어를 쓰지 마세요. (예: '정의', '개념', '도출' -> 사용 금지 ❌)
        2. 유치원 선생님처럼 상냥하고 부드럽게 말해주세요. ("~했니?", "~란다", "~해보자! 🎈")
        3. 칭찬을 많이 해주세요. ("와! 정말 좋은 질문이야!", "대단해! 👍")

        [과목별 설명 가이드]
        1. 수학: 
           - 숫자만으로 설명하지 말고 '사과', '사탕', '강아지' 같은 구체적인 물건으로 비유해서 이야기해주세요.
           - 곱셈구구(구구단)는 노래하듯이 리듬감 있게 설명해주세요.
        2. 국어:
           - 맞춤법을 설명할 때는 왜 틀리기 쉬운지 재미있는 예시를 들어주세요.
        3. 영어:
           - 문법 용어(주어, 명사, 동사 등)는 절대 쓰지 마세요.
           - **반드시 한글로 발음을 적어주세요.** (예: Apple -> [애-플])
           - 뜻은 가장 쉬운 단어 하나만 알려주세요.
        
        [출력 형식]
        - 답변은 너무 길지 않게, 3~4문장 단위로 끊어서 보여주세요.
        - 이모지를 풍부하게 사용하세요 (🌟, 🍎, 🐶, 🎉).
        """

# --- 5. 응답 생성 ---

submit_btn = st.button("알려줘! 🚀", use_container_width=True)

if submit_btn:
    if not user_question and not uploaded_file:
        st.warning("질문을 쓰거나 사진을 올려줘야 대답할 수 있어! 😉")
    else:
        try:
            with st.spinner("짝꿍이 생각하고 있어요... 뇌가 반짝반짝! ✨"):
                model = genai.GenerativeModel(
                    model_name=selected_model,
                    system_instruction=system_prompt
                )
                
                content_input = []
                if user_question:
                    content_input.append(user_question)
                if image_display:
                    content_input.append(image_display)
                
                response = model.generate_content(
                    content_input,
                    generation_config=genai.types.GenerationConfig(
                        temperature=temperature
                    )
                )
                result_text = response.text

            # --- 결과 출력 ---
            st.balloons() # 2학년 아이들을 위한 풍선 효과 추가
            st.success("짜잔! 대답이 나왔어! 🎉")
            
            tab1, tab2 = st.tabs(["🎈 짝꿍의 설명", "👀 부모님 확인용"])
            
            with tab1:
                st.markdown(result_text)
                st.info("💡 이해가 안 가면 또 물어봐! 난 언제나 여기 있어.")
                
            with tab2:
                st.text(f"모델: {selected_model}")
                st.caption("AI 답변입니다. 아이가 이해하기 쉬운 비유가 사용되었습니다.")
                st.code(result_text, language='markdown')

        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg:
                st.error("앗! 친구들이 너무 많이 물어봐서 잠깐 쉬어야 해. 1분만 기다려줘! 💦")
            else:
                st.error(f"어라? 문제가 생겼어. 부모님께 보여드려: {e}")

st.markdown("---")
st.markdown("<div style='text-align: center; color: #888; font-size: 0.8rem;'>2학년 친구들을 위한 AI 짝꿍 ❤️</div>", unsafe_allow_html=True)
