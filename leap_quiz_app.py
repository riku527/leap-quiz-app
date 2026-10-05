import streamlit as st
import json
import random
import os

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="LEAP 英単語 4択クイズ",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
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

# CSS styling with top padding fix so title is never hidden behind Streamlit header
st.markdown("""
<style>
    /* Ensure enough top padding so header bar does NOT cover the title */
    .block-container {
        padding-top: 4.5rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 680px !important;
    }

    /* Titles */
    .main-title {
        font-size: clamp(1.8rem, 5.5vw, 2.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 0.5rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: clamp(0.85rem, 2.5vw, 1.05rem);
        color: #64748B;
        text-align: center;
        margin-bottom: 1.2rem;
    }

    /* Status badge for range and settings */
    .setting-badge-container {
        display: flex;
        justify-content: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 1.2rem;
    }
    .setting-badge {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        font-size: 0.8rem;
        padding: 4px 12px;
        border-radius: 14px;
        font-weight: 600;
    }

    /* Question Card Box */
    .card-box {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 2px solid #E2E8F0;
        border-radius: 16px;
        padding: clamp(18px, 4vw, 28px);
        margin-bottom: 16px;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
    }
    .q-number {
        font-size: clamp(0.85rem, 2.5vw, 1.0rem);
        font-weight: 700;
        color: #2563EB;
        background-color: #EFF6FF;
        display: inline-block;
        padding: 4px 14px;
        border-radius: 20px;
    }
    .q-prompt {
        font-size: clamp(1.6rem, 6vw, 2.4rem);
        font-weight: 800;
        color: #0F172A;
        margin: 10px 0 4px 0;
        word-break: break-word;
        line-height: 1.3;
    }
    .ipa-text {
        font-size: clamp(0.9rem, 3vw, 1.1rem);
        color: #475569;
        font-family: serif, sans-serif;
        margin-bottom: 10px;
    }
    .mode-badge {
        font-size: clamp(0.75rem, 2vw, 0.85rem);
        color: #059669;
        font-weight: 600;
        background-color: #ECFDF5;
        padding: 3px 10px;
        border-radius: 8px;
        display: inline-block;
    }

    /* Touch-friendly buttons for Mobile & PC */
    .stButton > button {
        border-radius: 12px !important;
        font-size: clamp(0.95rem, 3vw, 1.1rem) !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        min-height: 52px !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Etymology & Trivia Box */
    .etym-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        color: #78350F;
        padding: 12px 16px;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-top: 10px;
        text-align: left;
    }

    /* Score banner */
    .score-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: white;
        padding: clamp(20px, 5vw, 32px);
        border-radius: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
    }
</style>
""", unsafe_allow_html=True)

# Helper function for Speech Synthesis (Audio Playback)
def render_audio_button(text):
    js_code = f"""
    <button onclick="
        const msg = new SpeechSynthesisUtterance('{text}');
        msg.lang = 'en-US';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
    " style="
        background-color: #3B82F6;
        color: white;
        border: none;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        cursor: pointer;
        margin-top: 6px;
        display: inline-flex;
        align-items: center;
        gap: 4px;
    ">
        🔊 発音を聞く
    </button>
    """
    st.components.v1.html(js_code, height=45)

# Smart Distractor Selector Function
def get_similar_distractors(target_no, mode_type, all_vocab, num_distractors=3):
    target_info = all_vocab[target_no]
    target_ja = target_info["ja"]
    candidates = [no for no in all_vocab.keys() if no != target_no]
    
    scored_candidates = []
    for cand_no in candidates:
        cand_info = all_vocab[cand_no]
        cand_ja = cand_info["ja"]
        
        num_diff = abs(target_no - cand_no)
        proximity_score = max(0, 200 - num_diff) / 2.0
        
        overlap_score = 0
        for keyword in ["する", "な", "の", "者", "国", "人", "法", "業", "会", "反", "動", "感"]:
            if (keyword in target_ja) and (keyword in cand_ja):
                overlap_score += 15
                
        target_chars = set(target_ja)
        cand_chars = set(cand_ja)
        common_chars = len(target_chars.intersection(cand_chars))
        
        total_score = proximity_score + overlap_score + (common_chars * 3) + random.uniform(0, 10)
        scored_candidates.append((total_score, cand_no))
        
    scored_candidates.sort(key=lambda x: x[0], reverse=True)
    selected_nos = [item[1] for item in scored_candidates[:num_distractors * 2]]
    distractor_nos = random.sample(selected_nos, min(num_distractors, len(selected_nos)))
    
    if mode_type == "英語 ➔ 日本語":
        correct_option = target_info["ja"]
        distractors = [all_vocab[no]["ja"] for no in distractor_nos]
    else:
        correct_option = target_info["en"]
        distractors = [all_vocab[no]["en"] for no in distractor_nos]
        
    options = [correct_option] + distractors
    random.shuffle(options)
    return correct_option, options

# Quiz Initialization
def prepare_quiz_items(start, end, order, direction, all_vocab, starred_nos=None, filter_starred_only=False, only_target_nos=None):
    if only_target_nos is not None:
        target_numbers = [no for no in only_target_nos if no in all_vocab]
    elif filter_starred_only and starred_nos:
        target_numbers = [no for no in all_vocab.keys() if start <= no <= end and no in starred_nos]
    else:
        target_numbers = [no for no in all_vocab.keys() if start <= no <= end]
    
    if order == "ランダム（網羅的）":
        random.shuffle(target_numbers)
    else:
        target_numbers.sort()
        
    items = []
    for no in target_numbers:
        info = all_vocab[no]
        
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
            "ipa": info.get("ipa", "[ /.../ ]"),
            "etymology": info.get("etymology", "語源: 特別な接頭辞・語根による基本構成単語"),
            "prompt": prompt,
            "correct_ans": correct_ans,
            "options": options,
            "mode": current_mode
        })
    return items

# Initialize Starred List
if "starred_words" not in st.session_state:
    st.session_state.starred_words = set()

# --- Header ---
st.markdown("<div class='main-title'>必携 英単語 LEAP</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>🎯 4択選択式 英単語クイズ & 語源・音声対応</div>", unsafe_allow_html=True)

if not vocab_db:
    st.error("⚠️ 単語データ (leap_words.json) が見つかりません。")
    st.stop()

# Sidebar Configuration
st.sidebar.header("⚙️ 出題条件・設定")
start_no = st.sidebar.number_input("開始番号 (No.)", min_value=1, max_value=2300, value=1451)
end_no = st.sidebar.number_input("終了番号 (No.)", min_value=1, max_value=2300, value=1700)

order_option = st.sidebar.radio("出題順序", ["番号順", "ランダム（網羅的）"])
direction_option = st.sidebar.radio(
    "翻訳・出題モード", 
    ["英語 ➔ 日本語", "日本語 ➔ 英語", "混合（英➔日・日➔英）"]
)

# Feature Toggles
st.sidebar.markdown("---")
st.sidebar.subheader("👁️ 表示オプション")
show_ipa = st.sidebar.checkbox("🔤 発音記号を表示する", value=True)

filter_starred = st.sidebar.checkbox(f"⭐ 要復習（スター選択中 {len(st.session_state.starred_words)}件）のみ", value=False)

if st.sidebar.button("🔄 クイズを再スタート / 設定反映", use_container_width=True):
    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.answered = False
    st.rerun()

# Initialize Session State for Quiz
if "quiz_items" not in st.session_state:
    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.answered = False

quiz_items = st.session_state.quiz_items
total_questions = len(quiz_items)

if total_questions == 0:
    st.warning(f"指定された範囲 (No.{start_no} ～ No.{end_no}) に該当する単語データがありません。設定を確認してください。")
    st.stop()

# Settings Summary Badge
st.markdown(f"""
<div class='setting-badge-container'>
    <span class='setting-badge'>範囲: No.{start_no} ～ No.{end_no}</span>
    <span class='setting-badge'>順序: {order_option}</span>
    <span class='setting-badge'>モード: {direction_option}</span>
</div>
""", unsafe_allow_html=True)

current_idx = st.session_state.current_idx

# Completion Screen
if current_idx >= total_questions:
    accuracy = (st.session_state.score / total_questions) * 100 if total_questions > 0 else 0
    st.markdown(f"""
    <div class='score-banner'>
        <h2 style='font-size: clamp(1.4rem, 4vw, 2.0rem); margin-bottom: 8px;'>🎉 全問題が終了しました！</h2>
        <p style='font-size: clamp(1.1rem, 3vw, 1.5rem); margin: 0;'>正解率: <b>{accuracy:.1f}%</b> ({st.session_state.score} / {total_questions} 問)</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Collect missed questions
    wrong_item_nos = []
    for idx, item in enumerate(quiz_items):
        if not st.session_state.user_answers.get(idx, {}).get("is_correct", False):
            wrong_item_nos.append(item["no"])
            
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 同じ条件で再挑戦", use_container_width=True, type="primary"):
            st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
            st.session_state.current_idx = 0
            st.session_state.score = 0
            st.session_state.user_answers = {}
            st.session_state.answered = False
            st.rerun()
            
    with col2:
        if wrong_item_nos:
            if st.button(f"🔥 間違えた{len(wrong_item_nos)}問を解き直す", use_container_width=True):
                st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, only_target_nos=wrong_item_nos)
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.user_answers = {}
                st.session_state.answered = False
                st.rerun()

    st.markdown("---")
    st.subheader("📊 回答結果・語源解説一覧")
    for idx, item in enumerate(quiz_items):
        is_correct = st.session_state.user_answers.get(idx, {}).get("is_correct", False)
        user_choice = st.session_state.user_answers.get(idx, {}).get("choice", "未回答")
        icon = "✅ 正解" if is_correct else "❌ 不正解"
        
        with st.expander(f"{icon} | No.{item['no']} : {item['en']} ({item['ja']})"):
            st.write(f"・**問題**: {item['prompt']}")
            st.write(f"・**あなたの回答**: {user_choice}")
            st.write(f"・**正解**: {item['correct_ans']}")
            if show_ipa:
                st.write(f"・**発音記号**: {item['ipa']}")
            st.write(f"・**語源・雑学**: {item['etymology']}")

else:
    # Quiz In-Progress Screen
    item = quiz_items[current_idx]
    
    # Progress Bar
    progress_val = (current_idx) / total_questions
    st.progress(progress_val)
    st.caption(f"第 {current_idx + 1} 問 / 全 {total_questions} 問  ｜  現在の正解数: {st.session_state.score} 問")

    # Star Button Toggle Top Bar
    is_starred = item["no"] in st.session_state.starred_words
    star_label = "⭐ 要復習から外す" if is_starred else "☆ スターを付ける (要復習)"
    
    col_star1, col_star2 = st.columns([3, 1])
    with col_star2:
        if st.button(star_label, key=f"star_btn_{item['no']}"):
            if is_starred:
                st.session_state.starred_words.remove(item["no"])
            else:
                st.session_state.starred_words.add(item["no"])
            st.rerun()

    # Question Card
    st.markdown(f"""
    <div class='card-box'>
        <div style='display: flex; justify-content: space-between; align-items: center;'>
            <span class='q-number'>No. {item['no']}</span>
            <span class='mode-badge'>{item['mode']}</span>
        </div>
        <div class='q-prompt'>{item['prompt']}</div>
    </div>
    """, unsafe_allow_html=True)

    # Display IPA if enabled & Mode is EN -> JA
    if show_ipa and item["mode"] == "英語 ➔ 日本語":
        st.markdown(f"<div style='text-align: center; margin-top:-10px; margin-bottom:10px;' class='ipa-text'>発音: [ {item['ipa']} ]</div>", unsafe_allow_html=True)

    # Render Audio Playback Button for EN prompt
    if item["mode"] == "英語 ➔ 日本語":
        render_audio_button(item["prompt"])

    st.write("▼ 正しい選択肢をタップしてください：")

    # Option Buttons
    for opt_idx, option_text in enumerate(item["options"]):
        btn_key = f"opt_{current_idx}_{opt_idx}"
        label = f"{opt_idx + 1}. {option_text}"
        
        if st.button(label, key=btn_key, disabled=st.session_state.answered, use_container_width=True):
            st.session_state.answered = True
            is_correct = (option_text == item["correct_ans"])
            if is_correct:
                st.session_state.score += 1
            st.session_state.user_answers[current_idx] = {
                "choice": option_text,
                "is_correct": is_correct
            }
            st.rerun()

    # Feedback & Navigation
    if st.session_state.answered:
        user_res = st.session_state.user_answers[current_idx]
        if user_res["is_correct"]:
            st.success("⭕ **正解です！ Great job!**")
        else:
            st.error(f"❌ **不正解...** 正解は **「 {item['correct_ans']} 」** です。")
            
        with st.info("📖 **単語解説 & 語源**"):
            st.write(f"・**単語 (No.{item['no']})**: **{item['en']}**")
            if show_ipa:
                st.write(f"・**発音記号**: {item['ipa']}")
            st.write(f"・**意味**: {item['ja']}")
            st.markdown(f"""
            <div class='etym-box'>
                💡 <b>語源・成り立ち・雑学:</b><br>{item['etymology']}
            </div>
            """, unsafe_allow_html=True)

        if st.button("次の問題へ ➔", type="primary", use_container_width=True):
            st.session_state.current_idx += 1
            st.session_state.answered = False
            st.rerun()
