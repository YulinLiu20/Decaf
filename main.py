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

    # 获取币安K线数据
    binance_url = "https://api.binance.com/api/v3/klines"
    binance_params = {
        "symbol": "ICPUSDT",
        "interval": "1d",
        "limit": 10000
    }
    binance_resp = requests.get(binance_url, params=binance_params)
    if binance_resp.status_code == 200:
        binance_data = binance_resp.json()
        binance_prices = [
            {
                "date": datetime.utcfromtimestamp(item[0] // 1000).strftime('%Y-%m-%d'),
                "open": float(item[1]),
                "high": float(item[2]),
                "low": float(item[3]),
                "close": float(item[4]),
                "volume": float(item[5])
            }
            for item in binance_data
        ]
        result["binance_prices"] = binance_prices
    else:
        result["binance_error"] = f"Failed to fetch Binance data: {binance_resp.text}"

    # 获取OKX K线数据
    okx_url = "https://www.okx.com/api/v5/market/history-candles"
    okx_params = {
        "instId": "ICP-USDT",
        "bar": "1D",
        "limit": "1000"  # OKX单次最多1000，需分页拉取
    }
    okx_prices = []
    next_after = None
    for _ in range(10):  # 最多拉10页
        if next_after:
            okx_params["after"] = next_after
        okx_resp = requests.get(okx_url, params=okx_params)
        if okx_resp.status_code == 200:
            okx_data = okx_resp.json()
            if okx_data.get("code") == "0" and okx_data.get("data"):
                for item in okx_data["data"]:
                    okx_prices.append({
                        "date": datetime.utcfromtimestamp(int(item[0]) // 1000).strftime('%Y-%m-%d'),
                        "open": float(item[1]),
                        "high": float(item[2]),
                        "low": float(item[3]),
                        "close": float(item[4]),
                        "volume": float(item[5])
                    })
                # OKX返回的数据是倒序排列，获取下一页的after参数
                next_after = okx_data["data"][-1][0]
                if len(okx_data["data"]) < 1000:
                    break
            else:
                break
        else:
            result["okx_error"] = f"Failed to fetch OKX data: {okx_resp.text}"
            break
    result["okx_prices"] = okx_prices[::-1]  # 正序排列

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)