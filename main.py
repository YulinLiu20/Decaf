from flask import Flask, jsonify
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/api/rewards")
def get_rewards():
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=10 * 365)
    start_ts = int(start_time.timestamp())
    end_ts = int(end_time.timestamp())
    step = 86400  # 每天

    url = f"https://ic-api.internetcomputer.org/api/v3/timeseries/reward-node-providers?start={start_ts}&end={end_ts}&step={step}"
    response = requests.get(url)
    data = response.json()

    if "reward_node_providers" in data and len(data["reward_node_providers"]) > 0:
        raw = data["reward_node_providers"]
        values_raw, timestamps_raw = zip(*raw)
        values = [float(v) / 1e8 for v in values_raw]
        timestamps = [datetime.utcfromtimestamp(float(ts)).strftime('%Y-%m-%d') for ts in timestamps_raw]

        cumulative = []
        total = 0
        for v in values:
            total += v
            cumulative.append(total)

        result = [
            {
                "date": timestamps[i],
                "monthly": values[i],
                "cumulative": cumulative[i]
            }
            for i in range(len(timestamps))
        ]
        return jsonify({"data": result})
    else:
        return jsonify({"error": "No reward_node_providers data found.", "raw": data})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)