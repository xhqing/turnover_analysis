import akshare as ak
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
import sys
import time

# ================= 彩色打印函数 =================
def print_red(text):
    print(f"\033[91m{text}\033[0m")

def print_green(text):
    print(f"\033[92m{text}\033[0m")

def print_yellow(text):
    print(f"\033[93m{text}\033[0m")

def print_blue(text):
    print(f"\033[94m{text}\033[0m")

# ================= 1. 设置时间范围 =================
end_date = datetime.today().strftime('%Y%m%d')
start_date = '20240101'
print_blue(f"数据时间范围：{start_date} 至 {end_date}")

# ================= 2. 多重数据源获取数据 =================
print_blue("\n正在获取阿里巴巴 (BABA) 的历史数据...")

df_final = None
data_source = ""

def fetch_from_eastmoney():
    """数据源1: 东方财富（含真实成交额）"""
    try:
        print_yellow("尝试数据源1: 东方财富 (stock_us_hist)...")
        df = ak.stock_us_hist(
            symbol='BABA', 
            period='daily', 
            start_date=start_date, 
            end_date=end_date, 
            adjust='qfq'
        )
        if df is not None and not df.empty and '成交额' in df.columns:
            print_green("✅ 数据源1成功，包含真实成交额")
            df.rename(columns={
                '日期': 'date', '开盘': 'open', '收盘': 'close',
                '最高': 'high', '最低': 'low', '成交量': 'volume', '成交额': 'amount'
            }, inplace=True)
            return df, "东方财富 (真实成交额)"
    except Exception as e:
        print_yellow(f"   数据源1失败: {e}")
    return None, None

def fetch_from_sina():
    """数据源2: 新浪财经（无成交额，但有成交量）"""
    try:
        print_yellow("尝试数据源2: 新浪财经 (stock_us_daily)...")
        df = ak.stock_us_daily(symbol='BABA', adjust='qfq')
        if df is not None and not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df[(df['date'] >= pd.to_datetime(start_date)) & 
                    (df['date'] <= pd.to_datetime(end_date))]
            if not df.empty:
                print_green("✅ 数据源2成功，但无成交额数据")
                df.rename(columns={
                    'date': 'date', 'open': 'open', 'close': 'close',
                    'high': 'high', 'low': 'low', 'volume': 'volume'
                }, inplace=True)
                return df, "新浪财经 (无成交额)"
    except Exception as e:
        print_yellow(f"   数据源2失败: {e}")
    return None, None

# 尝试所有数据源
for fetch_func in [fetch_from_eastmoney, fetch_from_sina]:
    df, source = fetch_func()
    if df is not None:
        df_final = df
        data_source = source
        break
    time.sleep(2)

if df_final is None:
    print_red("❌ 所有数据源均失败，无法获取数据")
    sys.exit(1)

# ================= 3. 数据预处理 =================
df_final.set_index('date', inplace=True)
df_final.sort_index(inplace=True)

print_blue(f"\n数据概览：")
print(f"  数据条数: {len(df_final)}")
print(f"  日期范围: {df_final.index[0].date()} 至 {df_final.index[-1].date()}")

# ================= 4. 成交额处理（仅用于保存） =================
if 'amount' not in df_final.columns:
    print_yellow("⚠️ 未获取到真实成交额，将估算并保存")
    df_final['amount_estimated'] = df_final['volume'] * df_final['close']
    has_real_amount = False
else:
    has_real_amount = True

# ================= 5. 保存原始数据 =================
output_cols = ['close', 'volume']
if 'amount' in df_final.columns:
    output_cols.append('amount')
else:
    output_cols.append('amount_estimated')
csv_file = 'baba_data.csv'
df_final[output_cols].to_csv(csv_file)
print_green(f"✅ 原始数据已保存至：{csv_file}")

# ================= 6. 绘制成交量曲线图（深色主题）=================
fig = go.Figure()

fig.add_trace(go.Scatter(
    x=df_final.index,
    y=df_final['volume'],
    mode='lines',
    name='成交量',
    line=dict(width=2.5, color='#00FF00')  # 亮绿色曲线
))

fig.update_layout(
    title={
        'text': '阿里巴巴 (BABA) 成交量日线图',
        'x': 0.5,
        'xanchor': 'center',
        'font': dict(size=20, family='Arial Black', color='white')
    },
    xaxis_title='日期',
    yaxis_title='成交量 (股)',
    hovermode='x unified',
    legend=dict(yanchor="top", y=0.99, xanchor="center", x=0.5, font=dict(color='white')),
    template='plotly_dark',
    autosize=True,
    margin=dict(l=40, r=40, t=80, b=40),
    annotations=[
        dict(
            x=0.02, y=0.98, xref="paper", yref="paper",
            text=f"数据来源: {data_source}", showarrow=False,
            font=dict(size=10, color="lightgray")
        )
    ]
)

# ================= 7. 保存HTML文件 =================
html_file = 'baba_volume.html'
fig.write_html(html_file)
print_green(f"✅ 图表已保存至：{html_file}")

# ================= 8. 统计摘要 =================
print_blue("\n📊 数据统计摘要：")
print(f"  成交量范围: {df_final['volume'].min():,.0f} - {df_final['volume'].max():,.0f}")
if not has_real_amount:
    print(f"  估算成交额范围: {df_final['amount_estimated'].min():,.0f} - {df_final['amount_estimated'].max():,.0f}")

print_green(f"\n✅ 处理完成！请用浏览器打开 {html_file} 查看图表")
if not has_real_amount:
    print_yellow("\n⚠️ 注：未能获取真实成交额，但已估算并保存在CSV中。")