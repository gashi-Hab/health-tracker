"""
健康管理アプリ - Google Sheets連携版
=====================================
データはGoogleスプレッドシートに保存されます
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta, timezone
import plotly.express as px
import plotly.graph_objects as go
from google.oauth2.service_account import Credentials
import gspread

# ===== 日本時間 =====
JST = timezone(timedelta(hours=9))

def get_japan_time():
    """日本時間を取得"""
    return datetime.now(JST)

# ===== Google Sheets接続 =====

def get_google_connection():
    """Google Sheetsへの接続を取得"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    credentials = Credentials.from_service_account_info(
        st.secrets["gcp_service_account"],
        scopes=scopes
    )
    client = gspread.authorize(credentials)
    return client

def get_spreadsheet():
    """スプレッドシートを取得"""
    client = get_google_connection()
    spreadsheet_url = st.secrets["spreadsheet_url"]
    return client.open_by_url(spreadsheet_url)

# ===== 時間フォーマット関数 =====

def format_time_simple(time_str):
    """時間を「16時10分」形式に変換"""
    try:
        time_obj = datetime.strptime(time_str, "%H:%M:%S")
        hour = time_obj.hour
        minute = time_obj.minute
        return f"{hour}時{minute:02d}分"
    except:
        return time_str

# ===== データ管理関数 =====

def load_pee_data():
    """トイレ記録を読み込む"""
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("トイレ記録")
        records = worksheet.get_all_records()
        return records
    except gspread.exceptions.WorksheetNotFound:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.add_worksheet(title="トイレ記録", rows=1000, cols=3)
        worksheet.append_row(["date", "time", "datetime"])
        return []
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return []

def save_pee_record(record):
    """トイレ記録を1件追加"""
    try:
        spreadsheet = get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet("トイレ記録")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="トイレ記録", rows=1000, cols=3)
            worksheet.append_row(["date", "time", "datetime"])
        
        worksheet.append_row([record["date"], record["time"], record["datetime"]])
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

def load_bp_data():
    """血圧記録を読み込む"""
    try:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.worksheet("血圧記録")
        records = worksheet.get_all_records()
        return records
    except gspread.exceptions.WorksheetNotFound:
        spreadsheet = get_spreadsheet()
        worksheet = spreadsheet.add_worksheet(title="血圧記録", rows=1000, cols=7)
        worksheet.append_row(["date", "time", "datetime", "systolic", "diastolic", "pulse", "memo"])
        return []
    except Exception as e:
        st.error(f"データ読み込みエラー: {e}")
        return []

def save_bp_record(record):
    """血圧記録を1件追加"""
    try:
        spreadsheet = get_spreadsheet()
        try:
            worksheet = spreadsheet.worksheet("血圧記録")
        except gspread.exceptions.WorksheetNotFound:
            worksheet = spreadsheet.add_worksheet(title="血圧記録", rows=1000, cols=7)
            worksheet.append_row(["date", "time", "datetime", "systolic", "diastolic", "pulse", "memo"])
        
        worksheet.append_row([
            record["date"], 
            record["time"], 
            record["datetime"],
            record["systolic"],
            record["diastolic"],
            record["pulse"],
            record["memo"]
        ])
        return True
    except Exception as e:
        st.error(f"保存エラー: {e}")
        return False

# ===== 集計関数 =====

def get_today_pee_count(pee_data):
    """今日のトイレ回数を取得"""
    today = get_japan_time().strftime("%Y-%m-%d")
    return len([r for r in pee_data if r.get("date") == today])

def get_weekly_pee_data(pee_data):
    """過去7日間のトイレデータを集計"""
    today = get_japan_time().date()
    weekly_data = {}
    
    for i in range(6, -1, -1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        weekly_data[date] = 0
    
    for record in pee_data:
        date = record.get("date", "")
        if date in weekly_data:
            weekly_data[date] += 1
    
    return weekly_data

# ===== ページ設定 =====
st.set_page_config(
    page_title="健康管理",
    page_icon="H",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ===== スマホ向けCSS =====
st.markdown("""
<style>
    .stButton > button {
        height: 80px;
        font-size: 20px;
        font-weight: bold;
    }
    
    [data-testid="stMetricValue"] {
        font-size: 36px;
    }
    
    .block-container {
        padding-top: 1rem;
        padding-bottom: 1rem;
    }
    
    .stTabs [data-baseweb="tab"] {
        font-size: 16px;
        padding: 10px 20px;
    }
    
    /* 記録リストの時間を大きく表示 */
    .time-display {
        font-size: 24px;
        font-weight: bold;
        padding: 12px 0;
        border-bottom: 1px solid #eee;
    }
    
    .time-number {
        font-size: 20px;
        color: #666;
        margin-right: 10px;
    }
</style>
""", unsafe_allow_html=True)

# ===== メイン画面 =====
st.title("健康管理")

# タブで機能を分ける
tab1, tab2 = st.tabs(["トイレ記録", "血圧記録"])

# ===== タブ1: トイレ記録 =====
with tab1:
    pee_data = load_pee_data()
    
    # 記録ボタン
    if st.button("トイレに行った", use_container_width=True, type="primary"):
        now = get_japan_time()
        new_record = {
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S")
        }
        if save_pee_record(new_record):
            st.success(f"記録しました ({now.strftime('%H')}時{now.strftime('%M')}分)")
            st.rerun()
    
    st.markdown("---")
    
    # 今日の回数
    today_count = get_today_pee_count(pee_data)
    st.metric(label="今日の回数", value=f"{today_count} 回")
    
    # 今日の記録一覧
    st.subheader("今日の記録")
    today = get_japan_time().strftime("%Y-%m-%d")
    today_records = [r for r in pee_data if r.get("date") == today]
    
    if today_records:
        for i, record in enumerate(today_records, 1):
            time_str = record.get('time', '')
            formatted_time = format_time_simple(time_str)
            st.markdown(
                f'<div class="time-display">'
                f'<span class="time-number">{i}.</span>{formatted_time}'
                f'</div>', 
                unsafe_allow_html=True
            )
    else:
        st.info("まだ記録がありません")
    
    st.markdown("---")
    
    # 一週間のグラフ
    st.subheader("過去7日間")
    
    weekly_data = get_weekly_pee_data(pee_data)
    
    df_weekly = pd.DataFrame({
        "日付": list(weekly_data.keys()),
        "回数": list(weekly_data.values())
    })
    df_weekly["表示日付"] = pd.to_datetime(df_weekly["日付"]).dt.strftime("%m/%d")
    
    fig = px.bar(
        df_weekly,
        x="表示日付",
        y="回数",
        color="回数",
        color_continuous_scale="Blues"
    )
    fig.update_layout(
        xaxis_title="",
        yaxis_title="回数",
        showlegend=False,
        coloraxis_showscale=False,
        margin=dict(l=20, r=20, t=20, b=20),
        height=250
    )
    fig.update_traces(texttemplate='%{y}', textposition='outside')
    
    st.plotly_chart(fig, use_container_width=True)
    
    # 統計情報
    col1, col2 = st.columns(2)
    with col1:
        st.metric("週間合計", f"{sum(weekly_data.values())} 回")
    with col2:
        avg = sum(weekly_data.values()) / 7
        st.metric("1日平均", f"{avg:.1f} 回")

# ===== タブ2: 血圧記録 =====
with tab2:
    bp_data = load_bp_data()
    
    st.subheader("血圧を記録")
    
    with st.form("bp_form"):
        systolic = st.number_input(
            "収縮期血圧（上）mmHg",
            min_value=60,
            max_value=250,
            value=120
        )
        diastolic = st.number_input(
            "拡張期血圧（下）mmHg",
            min_value=40,
            max_value=150,
            value=80
        )
        pulse = st.number_input(
            "脈拍（回/分）",
            min_value=40,
            max_value=200,
            value=70
        )
        memo = st.text_input("メモ（任意）", "")
        
        submitted = st.form_submit_button("記録する", use_container_width=True)
        
        if submitted:
            now = get_japan_time()
            new_record = {
                "date": now.strftime("%Y-%m-%d"),
                "time": now.strftime("%H:%M:%S"),
                "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
                "systolic": systolic,
                "diastolic": diastolic,
                "pulse": pulse,
                "memo": memo
            }
            if save_bp_record(new_record):
                st.success(f"記録しました ({systolic}/{diastolic} mmHg)")
                st.rerun()
    
    st.markdown("---")
    
    if bp_data:
        # 最新の記録
        st.subheader("最新の記録")
        latest = bp_data[-1]
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("上", f"{latest.get('systolic', '-')}")
        with col2:
            st.metric("下", f"{latest.get('diastolic', '-')}")
        with col3:
            st.metric("脈拍", f"{latest.get('pulse', '-')}")
        
        st.markdown("---")
        
        # 推移グラフ
        st.subheader("推移グラフ")
        
        df_bp = pd.DataFrame(bp_data)
        df_recent = df_bp.tail(10).copy()
        df_recent["表示日時"] = pd.to_datetime(df_recent["datetime"]).dt.strftime("%m/%d")
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=df_recent["表示日時"],
            y=df_recent["systolic"],
            mode='lines+markers',
            name='上',
            line=dict(color='#ff6b6b', width=2),
            marker=dict(size=8)
        ))
        fig.add_trace(go.Scatter(
            x=df_recent["表示日時"],
            y=df_recent["diastolic"],
            mode='lines+markers',
            name='下',
            line=dict(color='#4dabf7', width=2),
            marker=dict(size=8)
        ))
        fig.update_layout(
            xaxis_title="",
            yaxis_title="mmHg",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
            margin=dict(l=20, r=20, t=40, b=20),
            height=250
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        # 記録一覧
        st.subheader("記録一覧")
        df_display = df_bp[["datetime", "systolic", "diastolic", "pulse"]].copy()
        df_display.columns = ["日時", "上", "下", "脈拍"]
        st.dataframe(df_display.iloc[::-1].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("まだ血圧の記録がありません")
