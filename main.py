from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/api/rewards")
def get_rewards():
    end_time = datetime.utcnow()
    # ICP主网上线时间
    start_time = datetime(2021, 6, 10)
    #start_time = end_time - timedelta(days=10 * 365)
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    step = 86400  # 每天

    # 原奖励数据
    url_rewards = f"https://ic-api.internetcomputer.org/api/v3/timeseries/reward-node-providers?start={start_ts}&end={end_ts}&step={step}"
    response_rewards = requests.get(url_rewards)
    data_rewards = response_rewards.json()

    # 新增汇率数据
    url_rates = f"https://ic-api.internetcomputer.org/api/v3/timeseries/icp-xdr-conversion-rates?start={start_ts}&end={end_ts}&step={step}"
    response_rates = requests.get(url_rates)
    data_rates = response_rates.json()

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

    # 处理汇率数据
    if "icp_xdr_conversion_rates" in data_rates and len(data_rates["icp_xdr_conversion_rates"]) > 0:
        rates_raw = data_rates["icp_xdr_conversion_rates"]
        rates, rates_timestamps_raw = zip(*rates_raw)
        rates_timestamps = [datetime.utcfromtimestamp(float(ts)).strftime('%Y-%m-%d') for ts in rates_timestamps_raw]
        rates_list = [
            {
                "date": rates_timestamps[i],
                "rate": rates[i]
            }
            for i in range(len(rates_timestamps))
        ]
        result["conversion_rates"] = rates_list
    else:
        result["rates_error"] = "No icp_xdr_conversion_rates data found."
        result["rates_raw"] = data_rates

    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
