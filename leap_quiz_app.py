import streamlit as st
import json
import random
import os

# Streamlit Page Configuration
st.set_page_config(
    page_title="LEAP 英単語 4択クイズ & 苦手分析",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Persistent Storage Helpers
STAR_FILE = "starred_words.json"
PROGRESS_FILE = "quiz_progress.json"
MISTAKES_FILE = "mistake_history.json"

def load_starred_words():
    starred = set()
    if os.path.exists(STAR_FILE):
        try:
            with open(STAR_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                starred = set(data.get("starred", []))
        except Exception:
            pass
    return starred

def save_starred_words(starred_set):
    try:
        with open(STAR_FILE, "w", encoding="utf-8") as f:
            json.dump({"starred": list(starred_set)}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def save_progress(data):
    try:
        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def load_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None

def clear_progress():
    if os.path.exists(PROGRESS_FILE):
        try:
            os.remove(PROGRESS_FILE)
        except Exception:
            pass

def load_mistakes():
    if os.path.exists(MISTAKES_FILE):
        try:
            with open(MISTAKES_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except Exception:
            pass
    return {}

def save_mistakes(data):
    try:
        with open(MISTAKES_FILE, "w", encoding="utf-8") as f:
            json.dump({str(k): v for k, v in data.items()}, f, ensure_ascii=False, indent=2)
    except Exception:
        pass

def record_answer_history(word_no, is_correct):
    mistakes = load_mistakes()
    if word_no not in mistakes:
        mistakes[word_no] = {"wrong": 0, "total": 0}
    
    mistakes[word_no]["total"] += 1
    if not is_correct:
        mistakes[word_no]["wrong"] += 1
        
    save_mistakes(mistakes)

def clear_mistakes_history():
    if os.path.exists(MISTAKES_FILE):
        try:
            os.remove(MISTAKES_FILE)
        except Exception:
            pass

# Initialize Starred List with Persistence
if "starred_words" not in st.session_state:
    st.session_state.starred_words = load_starred_words()

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

# Custom CSS Styling
st.markdown("""
<style>
    /* Top padding to prevent header overlap */
    .block-container {
        padding-top: 4.2rem !important;
        padding-bottom: 2.5rem !important;
        padding-left: 1rem !important;
        padding-right: 1rem !important;
        max-width: 680px !important;
    }

    /* Main Titles */
    .main-title {
        font-size: clamp(1.8rem, 5.5vw, 2.5rem);
        font-weight: 800;
        background: linear-gradient(135deg, #1E3A8A 0%, #3B82F6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-top: 0.2rem;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        font-size: clamp(0.85rem, 2.5vw, 1.05rem);
        color: #64748B;
        text-align: center;
        margin-bottom: 1.2rem;
    }

    /* Badges & Resume Box */
    .setting-badge-container {
        display: flex;
        justify-content: center;
        gap: 6px;
        flex-wrap: wrap;
        margin-bottom: 1.0rem;
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

    .resume-box {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        border: 2px solid #3B82F6;
        border-radius: 16px;
        padding: 20px;
        margin-bottom: 20px;
        text-align: center;
        box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
    }

    /* Question Card Box */
    .card-box {
        background: linear-gradient(145deg, #ffffff, #f8fafc);
        border: 2px solid #E2E8F0;
        border-radius: 16px;
        padding: 16px 20px;
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
        margin: 8px 0 4px 0;
        word-break: break-word;
        line-height: 1.25;
    }
    .ipa-text {
        font-size: clamp(0.9rem, 3vw, 1.1rem);
        color: #475569;
        font-family: serif, sans-serif;
        margin-top: 2px;
        margin-bottom: 4px;
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

    /* Touch Buttons */
    .stButton > button {
        border-radius: 12px !important;
        font-size: clamp(0.95rem, 3vw, 1.1rem) !important;
        font-weight: 600 !important;
        padding: 12px 16px !important;
        min-height: 52px !important;
        transition: all 0.15s ease-in-out !important;
    }

    /* Score & Stats Cards */
    .score-banner {
        background: linear-gradient(135deg, #1E3A8A 0%, #2563EB 100%);
        color: white;
        padding: clamp(20px, 5vw, 32px);
        border-radius: 18px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 10px 20px rgba(37, 99, 235, 0.2);
    }

    .stat-card {
        background-color: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 14px;
        text-align: center;
        margin-bottom: 10px;
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 800;
        color: #2563EB;
    }
    .stat-label {
        font-size: 0.85rem;
        color: #64748B;
        font-weight: 600;
    }
</style>
""", unsafe_allow_html=True)

# Audio button helper
def render_audio_button(text):
    js_code = f"""
    <div style="display: flex; justify-content: center; margin-top: 4px; margin-bottom: 8px;">
        <button onclick="
            const msg = new SpeechSynthesisUtterance('{text}');
            msg.lang = 'en-US';
            msg.rate = 0.9;
            window.speechSynthesis.speak(msg);
        " style="
            background-color: #3B82F6;
            color: white;
            border: none;
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            cursor: pointer;
            display: inline-flex;
            align-items: center;
            gap: 4px;
        ">
            🔊 発音を聞く
        </button>
    </div>
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
            "prompt": prompt,
            "correct_ans": correct_ans,
            "options": options,
            "mode": current_mode
        })
    return items

# Header
st.markdown("<div class='main-title'>必携 英単語 LEAP</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-title'>🎯 4択英単語クイズ & 📊 苦手データ分析機能</div>", unsafe_allow_html=True)

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

st.sidebar.markdown("---")
st.sidebar.subheader("👁️ 表示・復習オプション")
show_ipa = st.sidebar.checkbox("🔤 発音記号を表示する", value=True)
filter_starred = st.sidebar.checkbox(f"⭐ 要復習（スター選択中 {len(st.session_state.starred_words)}件）のみ", value=False)

if st.sidebar.button("🔄 クイズを再スタート / 設定反映", use_container_width=True):
    clear_progress()
    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
    st.session_state.current_idx = 0
    st.session_state.score = 0
    st.session_state.user_answers = {}
    st.session_state.quiz_started = True
    st.rerun()

# --- Tab Layout: Quiz vs Analytics ---
tab_quiz, tab_analytics = st.tabs(["🎯 クイズを解く", "📊 苦手分析・統計"])

with tab_quiz:
    # Check for Saved Progress File on Disk
    saved_progress = load_progress()

    # If quiz has not been loaded into session_state yet AND saved progress exists:
    if "quiz_items" not in st.session_state and saved_progress:
        saved_items = saved_progress.get("quiz_items", [])
        saved_idx = saved_progress.get("current_idx", 0)
        saved_score = saved_progress.get("score", 0)
        saved_total = len(saved_items)
        saved_settings = saved_progress.get("settings", {})
        saved_mode = saved_settings.get("direction_option", direction_option)
        saved_range = f"No.{saved_settings.get('start_no', start_no)} ～ No.{saved_settings.get('end_no', end_no)}"
        
        if 0 <= saved_idx < saved_total:
            st.markdown(f"""
            <div class='resume-box'>
                <h3 style='margin: 0 0 10px 0; color: #1E3A8A;'>⏯️ 前回の解き途中データがあります</h3>
                <div style='text-align: left; background: white; padding: 12px; border-radius: 10px; margin-bottom: 14px; font-size: 0.95rem; color: #334155;'>
                    ・<b>出題モード</b>: {saved_mode}<br>
                    ・<b>出題範囲</b>: {saved_range}<br>
                    ・<b>現在の進捗</b>: 第 <b>{saved_idx + 1}</b> 問 / 全 {saved_total} 問 (現在 <b>{saved_score}</b> 問正解)
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_res1, col_res2 = st.columns(2)
            with col_res1:
                if st.button("🚀 前回の途中から始める", type="primary", use_container_width=True):
                    st.session_state.quiz_items = saved_items
                    st.session_state.current_idx = saved_idx
                    st.session_state.score = saved_score
                    st.session_state.user_answers = {int(k): v for k, v in saved_progress.get("user_answers", {}).items()}
                    st.session_state.quiz_started = True
                    st.rerun()
            with col_res2:
                if st.button("🆕 最初からやり直す", use_container_width=True):
                    clear_progress()
                    st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
                    st.session_state.current_idx = 0
                    st.session_state.score = 0
                    st.session_state.user_answers = {}
                    st.session_state.quiz_started = True
                    st.rerun()
            
            # STOP here so Streamlit waits for user selection instead of auto-initializing a new quiz
            st.stop()

    # Default Session State Initialization if no saved progress or user opted for new start
    if "quiz_items" not in st.session_state:
        st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, st.session_state.starred_words, filter_starred)
        st.session_state.current_idx = 0
        st.session_state.score = 0
        st.session_state.user_answers = {}
        st.session_state.quiz_started = True

    quiz_items = st.session_state.quiz_items
    total_questions = len(quiz_items)

    if total_questions == 0:
        st.warning(f"指定された範囲 (No.{start_no} ～ No.{end_no}) に該当する単語データがありません。設定を確認してください。")
    else:
        # Settings summary badge
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
            clear_progress()
            accuracy = (st.session_state.score / total_questions) * 100 if total_questions > 0 else 0
            st.markdown(f"""
            <div class='score-banner'>
                <h2 style='font-size: clamp(1.4rem, 4vw, 2.0rem); margin-bottom: 8px;'>🎉 全問題が終了しました！</h2>
                <p style='font-size: clamp(1.1rem, 3vw, 1.5rem); margin: 0;'>正解率: <b>{accuracy:.1f}%</b> ({st.session_state.score} / {total_questions} 問)</p>
            </div>
            """, unsafe_allow_html=True)
            
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
                    st.rerun()
                    
            with col2:
                if wrong_item_nos:
                    if st.button(f"🔥 間違えた{len(wrong_item_nos)}問を解き直す", use_container_width=True):
                        st.session_state.quiz_items = prepare_quiz_items(start_no, end_no, order_option, direction_option, vocab_db, only_target_nos=wrong_item_nos)
                        st.session_state.current_idx = 0
                        st.session_state.score = 0
                        st.session_state.user_answers = {}
                        st.rerun()

            st.markdown("---")
            st.subheader("📊 回答結果一覧")
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

        else:
            # Quiz In-Progress Screen
            item = quiz_items[current_idx]
            is_answered = (current_idx in st.session_state.user_answers)
            
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
                    save_starred_words(st.session_state.starred_words)
                    st.rerun()

            # IPA HTML rendered INSIDE the card box
            ipa_display_html = f"<div class='ipa-text'>[ {item['ipa']} ]</div>" if (show_ipa and item["mode"] == "英語 ➔ 日本語") else ""

            # Question Card Box
            st.markdown(f"""
            <div class='card-box'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span class='q-number'>No. {item['no']}</span>
                    <span class='mode-badge'>{item['mode']}</span>
                </div>
                <div class='q-prompt'>{item['prompt']}</div>
                {ipa_display_html}
            </div>
            """, unsafe_allow_html=True)

            # Audio playback button
            text_to_speak = item["en"] if "en" in item else item["prompt"]
            render_audio_button(text_to_speak)

            st.write("▼ 正しい選択肢をタップしてください：")

            # Option Buttons
            for opt_idx, option_text in enumerate(item["options"]):
                btn_key = f"opt_{current_idx}_{opt_idx}"
                label = f"{opt_idx + 1}. {option_text}"
                
                # Options disabled if this question has been answered
                if st.button(label, key=btn_key, disabled=is_answered, use_container_width=True):
                    is_correct = (option_text == item["correct_ans"])
                    
                    # Record mistake analytics
                    record_answer_history(item["no"], is_correct)
                    
                    if is_correct:
                        st.session_state.score += 1
                    else:
                        # 間違えた問題は自動的にスター（要復習）に追加
                        st.session_state.starred_words.add(item["no"])
                        save_starred_words(st.session_state.starred_words)
                        
                    st.session_state.user_answers[current_idx] = {
                        "choice": option_text,
                        "is_correct": is_correct
                    }
                    
                    # Save progress for resume feature with full settings metadata
                    progress_data = {
                        "quiz_items": st.session_state.quiz_items,
                        "current_idx": st.session_state.current_idx,
                        "score": st.session_state.score,
                        "user_answers": {str(k): v for k, v in st.session_state.user_answers.items()},
                        "settings": {
                            "start_no": start_no,
                            "end_no": end_no,
                            "order_option": order_option,
                            "direction_option": direction_option,
                            "filter_starred": filter_starred
                        }
                    }
                    save_progress(progress_data)
                    st.rerun()

            # Feedback & Navigation Controls
            if is_answered:
                user_res = st.session_state.user_answers[current_idx]
                if user_res["is_correct"]:
                    st.success("⭕ **正解です！ Great job!**")
                else:
                    st.error(f"❌ **不正解...** 正解は **「 {item['correct_ans']} 」** です。")
                    
                with st.info("📖 **単語解説**"):
                    st.write(f"・**単語 (No.{item['no']})**: **{item['en']}**")
                    if show_ipa:
                        st.write(f"・**発音記号**: {item['ipa']}")
                    st.write(f"・**意味**: {item['ja']}")

            # Navigation Buttons (Previous & Next)
            col_nav1, col_nav2 = st.columns(2)
            with col_nav1:
                if current_idx > 0:
                    if st.button("⬅️ 前の問題へ", use_container_width=True):
                        st.session_state.current_idx -= 1
                        progress_data = {
                            "quiz_items": st.session_state.quiz_items,
                            "current_idx": st.session_state.current_idx,
                            "score": st.session_state.score,
                            "user_answers": {str(k): v for k, v in st.session_state.user_answers.items()},
                            "settings": {
                                "start_no": start_no,
                                "end_no": end_no,
                                "order_option": order_option,
                                "direction_option": direction_option,
                                "filter_starred": filter_starred
                            }
                        }
                        save_progress(progress_data)
                        st.rerun()

            with col_nav2:
                if is_answered:
                    next_btn_label = "次の問題へ ➔" if current_idx < total_questions - 1 else "🎉 結果を見る ➔"
                    if st.button(next_btn_label, type="primary", use_container_width=True):
                        st.session_state.current_idx += 1
                        progress_data = {
                            "quiz_items": st.session_state.quiz_items,
                            "current_idx": st.session_state.current_idx,
                            "score": st.session_state.score,
                            "user_answers": {str(k): v for k, v in st.session_state.user_answers.items()},
                            "settings": {
                                "start_no": start_no,
                                "end_no": end_no,
                                "order_option": order_option,
                                "direction_option": direction_option,
                                "filter_starred": filter_starred
                            }
                        }
                        save_progress(progress_data)
                        st.rerun()

# --- Tab 2: Analytics & Weakness Dashboard ---
with tab_analytics:
    st.subheader("📊 苦手データ分析・学習記録")
    
    mistakes_data = load_mistakes()
    
    if not mistakes_data:
        st.info("💡 まだ問題の解答記録がありません。クイズを解くと自動的に苦手単語データが集計されます！")
    else:
        total_attempts_all = sum(v["total"] for v in mistakes_data.values())
        total_wrong_all = sum(v["wrong"] for v in mistakes_data.values())
        total_correct_all = total_attempts_all - total_wrong_all
        overall_accuracy = (total_correct_all / total_attempts_all * 100) if total_attempts_all > 0 else 0
        
        # Summary Metrics
        col_m1, col_m2, col_m3 = st.columns(3)
        with col_m1:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value'>{total_attempts_all}</div>
                <div class='stat-label'>総解答数</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m2:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value' style='color:#DC2626;'>{len([k for k, v in mistakes_data.items() if v['wrong'] > 0])}</div>
                <div class='stat-label'>苦手登録単語数</div>
            </div>
            """, unsafe_allow_html=True)
        with col_m3:
            st.markdown(f"""
            <div class='stat-card'>
                <div class='stat-value' style='color:#059669;'>{overall_accuracy:.1f}%</div>
                <div class='stat-label'>通算正解率</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        st.subheader("🔥 苦手単語ワーストランキング")
        
        # Sort words by wrong count descending
        sorted_mistakes = sorted(
            [item for item in mistakes_data.items() if item["wrong"] > 0],
            key=lambda x: (x["wrong"], x["wrong"] / x["total"]),
            reverse=True
        )
        
        if not sorted_mistakes:
            st.success("🎉 素晴らしい！現在、間違えたままになっている苦手単語はありません。")
        else:
            top_wrong_nos = [item[0] for item in sorted_mistakes[:10]]
            
            # Button to start quiz with top worst words directly
            if st.button(f"🔥 苦手ワースト単語（上位{len(top_wrong_nos)}問）を集中テストする", type="primary", use_container_width=True):
                st.session_state.quiz_items = prepare_quiz_items(
                    start_no, end_no, order_option, direction_option, vocab_db, only_target_nos=top_wrong_nos
                )
                st.session_state.current_idx = 0
                st.session_state.score = 0
                st.session_state.user_answers = {}
                clear_progress()
                st.success("🎯 苦手ワースト単語のテストをセットしました！「🎯 クイズを解く」タブを開いてスタートしてください。")

            st.write("")
            for rank, (word_no, stats) in enumerate(sorted_mistakes[:15], 1):
                if word_no in vocab_db:
                    info = vocab_db[word_no]
                    wrong_cnt = stats["wrong"]
                    total_cnt = stats["total"]
                    err_rate = (wrong_cnt / total_cnt) * 100
                    ipa_str = f" [ {info.get('ipa', '')} ]" if info.get('ipa') else ""
                    
                    st.markdown(f"""
                    <div style='background-color:#FFF5F5; border-left:4px solid #EF4444; padding:10px 14px; border-radius:8px; margin-bottom:8px;'>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <b style='color:#991B1B;'>第 {rank} 位 (No.{word_no}) : {info['en']}{ipa_str}</b>
                            <span style='background-color:#FEE2E2; color:#991B1B; padding:2px 8px; border-radius:12px; font-size:0.8rem; font-weight:700;'>ミス {wrong_cnt} 回</span>
                        </div>
                        <div style='color:#4B5563; font-size:0.9rem; margin-top:4px;'>意味: {info['ja']}</div>
                        <div style='color:#6B7280; font-size:0.8rem; margin-top:2px;'>誤答率: {err_rate:.0f}% ({wrong_cnt}/{total_cnt}回)</div>
                    </div>
                    """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("🗑️ 苦手・解答データをリセットする", use_container_width=True):
            clear_mistakes_history()
            st.success("統計データをクリアしました。")
            st.rerun()
