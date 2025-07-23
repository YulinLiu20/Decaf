from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/api/rewards")
def get_rewards():
    end_time = datetime.utcnow()
    start_time = datetime(2021, 6, 10)
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    step = 86400  # 每天

    # 原奖励数据
    url_rewards = f"https://ic-api.internetcomputer.org/api/v3/timeseries/reward-node-providers?start={start_ts}&end={end_ts}&step={step}"
    response_rewards = requests.get(url_rewards)
    data_rewards = response_rewards.json()

    result = {}

    # 处理奖励数据
    if "reward_node_providers" in data_rewards and len(data_rewards["reward_node_providers"]) > 0:
        raw = data_rewards["reward_node_providers"]
        values_raw, timestamps_raw = zip(*raw)
        values = [float(v) / 1e8 for v in values_raw]
        timestamps = [datetime.utcfromtimestamp(float(ts)).strftime('%Y-%m-%d') for ts in timestamps_raw]

        cumulative = []
        total = 0
        for v in values:
            total += v
            cumulative.append(total)

        rewards_list = [
            {
                "date": timestamps[i],
                "monthly": values[i],
                "cumulative": cumulative[i]
            }
            for i in range(len(timestamps))
        ]
        result["rewards"] = rewards_list
    else:
        result["rewards_error"] = "No reward_node_providers data found."
        result["rewards_raw"] = data_rewards

    # 获取币安K线数据（注意：2025年1月1日后open_time为微秒，需除以1000）
    binance_url = "https://api.binance.com/api/v3/klines"
    binance_params = {
        "symbol": "ICPUSDT",
        "interval": "1d",
        "limit": 1000
    }
    binance_resp = requests.get(binance_url, params=binance_params)
    binance_prices = []
    if binance_resp.status_code == 200:
        binance_data = binance_resp.json()
        for item in binance_data:
            open_time = item[0]
            # Binance官方已公告：2025年1月1日后open_time为微秒（16位），否则为毫秒（13位）
            # 这里自动判断长度，若为16位则除以1000
            if len(str(open_time)) >= 16:
                fixed_open_time = open_time // 1000
            else:
                fixed_open_time = open_time
            date_str = datetime.utcfromtimestamp(fixed_open_time / 1000).strftime('%Y-%m-%d')
            binance_prices.append({
                "date": date_str,
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            })
        result["binance_prices"] = binance_prices
    else:
        result["binance_error"] = f"Failed to fetch Binance data: {binance_resp.text}"

    # 备注：自2025年1月1日起，Binance返回的open_time字段单