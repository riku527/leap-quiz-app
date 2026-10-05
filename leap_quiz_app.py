import streamlit as st
import json
import random
import os

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="LEAP 英単語 4択クイズアプリ",
    page_icon="🎯",
    layout="centered"
)

# Load Vocabulary Data from JSON
@st.cache_data
def load_vocab_data():
    json_path = "leap_words.json"
    if not os.path.exists(json_path):
        json_path = os.path.join(os.path.dirname(__file__), "leap_words.json")
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

vocab_db = load_vocab_data()

# Custom CSS styling for card UI and buttons
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 800;
        color: #1E3A8A;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-title {
        font-size: 1.0rem;
        color: #4B5563;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    .card-box {
        background-color: #F8FAFC;
        border: 2px solid #E2E8F0;
        border-radius: 12px;
        padding: 24px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .q-number {
        font-size: 1.1rem;
        font-weight: 700;
        color: #2563EB;
        background-color: #EFF6FF;
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
        margin-bottom: 10px;
    }
    .q-prompt {
        font-size: 2.0rem;
        font-weight: 700;
        color: #1F2937;
        margin: 15px 0;
    }
    .mode-badge {
        font-size: 0.85rem;
        color: #059669;
        font-weight: 600;
    }
    .score-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        color: white;
        padding: 30px;
        border-radius: 16px;
        text-align: center;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Smart Distractor Selector Function
def get_similar_distractors(target_no, mode_type, all_vocab, num_distractors=3):
    """
    Selects 3 distractors from all_vocab that are similar in context/theme or close in range.
    Uses LEAP number proximity (since adjacent numbers belong to same category) and Japanese keyword overlap.
    """
    target_info = all_vocab[target_no]
    target_ja = target_info["ja"]
    
    candidates = [no for no in all_vocab.keys() if no != target_no]
    
    scored_candidates = []
    for cand_no in candidates:
        cand_info = all_vocab[cand_no]
        cand_ja = cand_info["ja"]
        
        # 1. Proximity score (LEAP words close in number share thematic category)
        num_diff = abs(target_no - cand_no)
        proximity_score = max(0, 200 - num_diff) / 2.0
        
        # 2. Definition keyword / grammatical similarity score
        overlap_score = 0
        # Common grammatical markers or keywords
        for keyword in ["する", "な", "の", "者", "国", "人", "法", "業", "会", "反", "動", "感"]:
            if (keyword in target_ja) and (keyword in cand_ja):
                overlap_score += 15
                
        # Character set overlap
        target_chars = set(target_ja)
        cand_chars = set(cand_ja)
        common_chars = len(target_chars.intersection(cand_chars))
        
        total_score = proximity_score + overlap_score + (common_chars * 3) + random.uniform(0, 10)
        scored_candidates.append((total_score, cand_no))
        
    # Sort by score descending and take top candidates
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    selected_nos = [item[1] for item in scored_candidates[:num_distractors * 2]]
    
    # Randomly sample from top similar candidates to keep it fresh
    distractor_nos = random.sample(selected_nos, min(num_distractors, len(selected_nos)))
    
    # Format options according to mode_type
    if mode_type == "英語 ➔ 日本語":
        # Options are Japanese definitions
        correct_option = target_info["ja"]
        distractors = [all_vocab[no]["ja"] for no in distractor_nos]
    else:
        # Options are English words
        correct_option = target_info["en"]
        distractors = [all_vocab[no]["en"] for no in distractor_nos]
        
    options = [correct_option] + distractors
    random.shuffle(options)
    return correct_option, options

# Quiz Initialization Function
def prepare_quiz_items(start, end, order, direction, all_vocab):
    target_numbers = [no for no in all_vocab.keys() if start <= no <= end]
    
    if order == "ランダム（網羅的）":
        random.shuffle(target_numbers)
    else:
        target_numbers.sort()
        
    items = []
    for no in target_numbers:
        info = all_vocab[no]
        
        # Determine mode for this question
        current_mode = direction
        if direction.startswith("混合"):
            current_mode = random.choice(["英語 ➔ 日本語", "日本語 ➔ 英語"])
            
        if current_mode == "英語 ➔ 日本語":
            prompt = info["en"]
            correct_ans, options = get_similar_distractors(no, "英語 ➔ 日本語", all_vocab)
        else:
            prompt = info["ja"]
            correct_ans, options = get_similar_distractors(no, "日本語 ➔ 英語", all_vocab)
            
        items.append({
            "no": no,
            "en": info["en"],
            "ja": info["ja"],
            "prompt": prompt,
            "correct_ans": correct_ans,
            "options": options,
            "mode": current_mode
        })
    return items

# --- Main App Execution ---
st.markdown("<div class='main-title'>必携 英単語 LEAP</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>🎯 4択選択式 英単語クイズ（同一・類似カテゴリ単語から厳選）</div>", unsafe_allow_html=True)

if not vocab_db:
    st.error("⚠️ 単語データ (leap_words.json) が見つかりません。")
    st.stop()

# Available range bounds
all_nos = sorted(list(vocab_db.keys()))
min_no, max_no = min(all_nos), max(all_nos)

# Sidebar Configuration
st.sidebar.header("⚙️ 出題条件・設定")
start_no = st.sidebar.number_input("開始番号 (No.)", min_value=1, max_value=2300, value=1451)
end_no = st.sidebar.number_input("終了番号 (No.)", min_value=1, max_value=2300, value=1700)

order_option = st.sidebar.radio("出題順序", ["番号順", "ランダム（網羅的）"])
direction_option = st.sidebar.radio(
    "翻訳・出題モード", 
    ["英語 ➔ 日本語", "日本語 ➔ 英語", "混合（英➔日・日➔英）"]
)

if st.sidebar.button("🔄 クイズを再スタート / 設定反映"):
    st.session_state.clear()
    st.rerun()

# Initialize Session State for Quiz
if "quiz_items" not in st.session_state:
    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.answered = False

quiz_items = st.session_state.quiz_items
total_questions = len(quiz_items)

if total_questions == 0:
    st.warning(f"指定された範囲 (No.{start_no} ～ No.{end_no}) に該当する単語データがありません。範囲を変更してください。")
    st.stop()

current_idx = st.session_state.current_idx

# Completion Screen
if current_idx >= total_questions:
    accuracy = (st.session_state.score / total_questions) * 100
    st.markdown(f"""
    <div class='score-banner'>
        <h2>🎉 クイズ修了！ お疲れ様でした！</h2>
        <p style='font-size: 1.5rem; margin-top: 10px;'>正解数: <b>{st.session_state.score} / {total_questions} 問</b> ({accuracy:.1f}%)</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.subheader("📊 結果一覧")
    for idx, item in enumerate(quiz_items):
        is_correct = st.session_state.user_answers.get(idx, {}).get("is_correct", False)
        user_choice = st.session_state.user_answers.get(idx, {}).get("choice", "未回答")
        icon = "✅" if is_correct else "❌"
        
        with st.expander(f"{icon} No.{item['no']} : {item['en']} ({item['ja']})"):
            st.write(f"**問題**: {item['prompt']}")
            st.write(f"**あなたの回答**: {user_choice}")
            st.write(f"**正解**: {item['correct_ans']}")

    if st.button("🚀 もう一度同じ条件で挑戦する", use_container_width=True):
        st.session_state.clear()
        st.rerun()

else:
    # Quiz In-Progress Screen
    item = quiz_items[current_idx]
    
    # Progress Bar
    progress_val = (current_idx) / total_questions
    st.progress(progress_val)
    st.caption(f"問題 {current_idx + 1} / {total_questions} 問  |  正解数: {st.session_state.score} 問")

    # Question Card
    st.markdown(f"""
    <div class='card-box'>
        <div class='q-number'>No. {item['no']}</div>
        <div class='mode-badge'>モード: {item['mode']}</div>
        <div class='q-prompt'>{item['prompt']}</div>
    </div>
    """, unsafe_allow_html=True)

    st.write("▼ 正しい選択肢を選んでください（※類似の意味を持つ単語からの出題です）：")

    # Options Display
    for opt_idx, option_text in enumerate(item["options"]):
        btn_key = f"opt_{current_idx}_{opt_idx}"
        
        # Disabled after answering current question
        if st.button(option_text, key=btn_key, disabled=st.session_state.answered, use_container_width=True):
            st.session_state.answered = True
            is_correct = (option_text == item["correct_ans"])
            if is_correct:
                st.session_state.score += 1
            st.session_state.user_answers[current_idx] = {
                "choice": option_text,
                "is_correct": is_correct
            }
            st.rerun()

    # Feedback and Navigation
    if st.session_state.answered:
        user_res = st.session_state.user_answers[current_idx]
        if user_res["is_correct"]:
            st.success("⭕ **正解です！ Great job!**")
        else:
            st.error(f"❌ **不正解...**  正解は **「 {item['correct_ans']} 」** です。")
            
        with st.info("📖 **単語詳細解説**"):
            st.write(f"・**No.{item['no']}**: **{item['en']}**")
            st.write(f"・**意味**: {item['ja']}")

        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("次の問題へ ➔", type="primary", use_container_width=True):
                st.session_state.current_idx += 1
                st.session_state.answered = False
                st.rerun()
