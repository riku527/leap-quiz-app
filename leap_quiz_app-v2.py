import streamlit as st
import json
import random
import os
import streamlit.components.v1 as components

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
    if not os.path.exists(json_path):
        json_path = "/workspace/scratch/leap_words.json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            return {int(k): v for k, v in data.items()}
    return {}

vocab_db = load_vocab_data()

# Initialize Global Starred Session State
if "starred_words" not in st.session_state:
    st.session_state.starred_words = set()

# CSS Styling
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 2rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 680px !important;
    }

    .main-title {
        font-size: clamp(1.6rem, 5vw, 2.3rem);
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: clamp(0.85rem, 2.5vw, 1.0rem);
        color: #64748B;
        text-align: center;
        margin-bottom: 1.0rem;
    }

    .setting-badge-container {
        display: flex;
        justify-content: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 1rem;
    }
    .setting-badge {
        background-color: #F1F5F9;
        color: #334155;
        border: 1px solid #CBD5E1;
        font-size: 0.8rem;
        padding: 3px 10px;
        border-radius: 12px;
        font-weight: 600;
    }

    .card-box {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 2px solid #E2E8F0;
        border-radius: 16px;
        padding: clamp(16px, 4vw, 24px);
        margin-bottom: 16px;
        text-align: center;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.04), 0 4px 6px -2px rgba(0, 0, 0, 0.02);
        position: relative;
    }
    .q-number {
        font-size: clamp(0.85rem, 2.5vw, 0.95rem);
        font-weight: 700;
        color: #2563EB;
        background-color: #EFF6FF;
        display: inline-block;
        padding: 4px 12px;
        border-radius: 20px;
    }
    .q-prompt {
        font-size: clamp(1.6rem, 6.5vw, 2.4rem);
        font-weight: 800;
        color: #0F172A;
        margin: 10px 0 4px 0;
        word-break: break-word;
        line-height: 1.25;
    }
    .ipa-text {
        font-size: clamp(0.95rem, 3vw, 1.15rem);
        color: #475569;
        font-family: "Courier New", Courier, monospace;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .mode-badge {
        font-size: clamp(0.75rem, 2vw, 0.85rem);
        color: #059669;
        font-weight: 600;
        background-color: #ECFDF5;
        padding: 2px 8px;
        border-radius: 6px;
        display: inline-block;
    }

    .etym-box {
        background-color: #FEF3C7;
        border-left: 4px solid #F59E0B;
        color: #78350F;
        padding: 12px 14px;
        border-radius: 8px;
        font-size: 0.9rem;
        margin-top: 10px;
        margin-bottom: 15px;
        text-align: left;
        line-height: 1.45;
    }

    .stButton > button {
        border-radius: 12px !important;
        font-size: clamp(0.95rem, 3vw, 1.1rem) !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        min-height: 50px !important;
        transition: all 0.15s ease-in-out !important;
    }

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

# Helper function to trigger speech synthesis
def trigger_speech(text_to_speak):
    js_code = f"""
    <script>
        var msg = new SpeechSynthesisUtterance("{text_to_speak}");
        msg.lang = 'en-US';
        msg.rate = 0.9;
        window.speechSynthesis.speak(msg);
    </script>
    """
    components.html(js_code, height=0, width=0)

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
def prepare_quiz_items(start, end, order, direction, all_vocab, only_target_nos=None):
    if only_target_nos is not None:
        target_numbers = [no for no in only_target_nos if no in all_vocab]
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
            "ipa": info.get("ipa", f"/{info['en']}/"),
            "etymology": info.get("etymology", "語源・イメージを意識して覚えましょう。"),
            "prompt": prompt,
            "correct_ans": correct_ans,
            "options": options,
            "mode": current_mode
        })
    return items

# --- Header ---
st.markdown("<div class='main-title'>必携 英単語 LEAP</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>🎯 4択英単語クイズ（語源・発音機能付き）</div>", unsafe_allow_html=True)

if not vocab_db:
    st.error("⚠️ 単語データ (leap_words.json) が見つかりません。")
    st.stop()

# Sidebar Configuration
st.sidebar.header("⚙️ 出題条件・表示設定")

# Target Range or Star Filter
target_filter = st.sidebar.radio("出題対象", ["指定範囲の全単語", "⭐ 要復習（スター選択中）のみ"])

start_no = st.sidebar.number_input("開始番号 (No.)", min_value=1, max_value=2300, value=1451)
end_no = st.sidebar.number_input("終了番号 (No.)", min_value=1, max_value=2300, value=1700)

order_option = st.sidebar.radio("出題順序", ["番号順", "ランダム（網羅的）"])
direction_option = st.sidebar.radio(
    "翻訳・出題モード", 
    ["英語 ➔ 日本語", "日本語 ➔ 英語", "混合（英➔日・日➔英）"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("🔤 表示設定")
show_ipa = st.sidebar.checkbox("発音記号を表示する", value=True)

if st.sidebar.button("🔄 クイズを再スタート / 設定反映", use_container_width=True):
    st.session_state.quiz_items = None
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.answered = False
    st.rerun()

# Determine Quiz Target List
if target_filter == "⭐ 要復習（スター選択中）のみ":
    target_nos = list(st.session_state.starred_words)
else:
    target_nos = None

# Initialize Session State
if ("quiz_items" not in st.session_state) or (st.session_state.quiz_items is None):
    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, only_target_nos=target_nos)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.answered = False

quiz_items = st.session_state.quiz_items
total_questions = len(quiz_items)

if total_questions == 0:
    if target_filter == "⭐ 要復習（スター選択中）のみ":
        st.warning("現在スター（⭐）が付けられている単語がありません。問題解く際にスターボタンを押して追加してください。")
    else:
        st.warning(f"指定範囲 (No.{start_no} ～ No.{end_no}) に該当する単語がありません。")
    st.stop()

# Settings Badge
st.markdown(f"""
<div class='setting-badge-container'>
    <span class='setting-badge'>範囲: No.{start_no} ～ No.{end_no}</span>
    <span class='setting-badge'>出題: {target_filter}</span>
    <span class='setting-badge'>モード: {direction_option}</span>
    <span class='setting-badge'>発音記号: {"表示 ON" if show_ipa else "非表示 OFF"}</span>
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
    
    wrong_item_nos = [item["no"] for idx, item in enumerate(quiz_items) if not st.session_state.user_answers.get(idx, {}).get("is_correct", False)]
            
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🚀 同じ条件で再挑戦", use_container_width=True, type="primary"):
            st.session_state.quiz_items = None
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
    st.subheader("📊 回答結果・解説一覧")
    for idx, item in enumerate(quiz_items):
        is_correct = st.session_state.user_answers.get(idx, {}).get("is_correct", False)
        user_choice = st.session_state.user_answers.get(idx, {}).get("choice", "未回答")
        icon = "✅ 正解" if is_correct else "❌ 不正解"
        ipa_disp = f"[{item['ipa']}] " if show_ipa else ""
        
        with st.expander(f"{icon} | No.{item['no']} : {item['en']} {ipa_disp}({item['ja']})"):
            st.write(f"・**問題**: {item['prompt']}")
            st.write(f"・**あなたの回答**: {user_choice}")
            st.write(f"・**正解**: {item['correct_ans']}")
            st.markdown(f"<div class='etym-box'>{item['etymology']}</div>", unsafe_allow_html=True)

else:
    # Quiz In-Progress Screen
    item = quiz_items[current_idx]
    
    progress_val = (current_idx) / total_questions
    st.progress(progress_val)
    st.caption(f"第 {current_idx + 1} 問 / 全 {total_questions} 問  ｜  現在の正解数: {st.session_state.score} 問")

    # Star Toggle Logic
    is_starred = item["no"] in st.session_state.starred_words
    
    # Question Card Layout
    col_top1, col_top2 = st.columns([3, 1])
    with col_top1:
        st.markdown(f"<span class='q-number'>No. {item['no']}</span> <span class='mode-badge'>{item['mode']}</span>", unsafe_allow_html=True)
    with col_top2:
        star_label = "⭐ 要復習" if is_starred else "☆ スター"
        if st.button(star_label, key=f"star_btn_{item['no']}"):
            if is_starred:
                st.session_state.starred_words.remove(item["no"])
            else:
                st.session_state.starred_words.add(item["no"])
            st.rerun()

    # Question Display & Phonetic symbol toggle
    prompt_html = f"<div class='q-prompt'>{item['prompt']}</div>"
    if show_ipa and item["mode"] == "英語 ➔ 日本語":
        prompt_html += f"<div class='ipa-text'>[ {item['ipa']} ]</div>"
    st.markdown(f"<div class='card-box'>{prompt_html}</div>", unsafe_allow_html=True)

    # Audio Playback Button (Plays on click only)
    col_audio, _ = st.columns([1, 1])
    with col_audio:
        if st.button("🔊 発音を聞く (音声再生)", key=f"speech_{current_idx}"):
            trigger_speech(item["en"])

    st.write("▼ 正しい選択肢をタップしてください：")

    # Option buttons
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

    # Feedback & Explanation Box
    if st.session_state.answered:
        user_res = st.session_state.user_answers[current_idx]
        if user_res["is_correct"]:
            st.success("⭕ **正解です！ Great job!**")
        else:
            st.error(f"❌ **不正解...** 正解は **「 {item['correct_ans']} 」** です。")
            
        # Etymology & Trivia Explanation Box
        ipa_info = f" [{item['ipa']}]" if show_ipa else ""
        st.markdown(f"""
        <div class='etym-box'>
            <b>📖 単語解説 & 語源・雑学:</b><br>
            ・<b>No.{item['no']} {item['en']}</b>{ipa_info} : {item['ja']}<br>
            ・{item['etymology']}
        </div>
        """, unsafe_allow_html=True)

        if st.button("次の問題へ ➔", type="primary", use_container_width=True):
            st.session_state.current_idx += 1
            st.session_state.answered = False
            st.rerun()
