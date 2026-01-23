import os
from flask import Flask, request, jsonify
from pytrends.request import TrendReq

app = Flask(__name__)

@app.get("/")
def health():
    return "OK", 200

@app.post("/trends")
def trends():
    try:
        data = request.get_json(silent=True) or {}

        keywords = data.get("keywords", [])
        geo = data.get("geo", "ZA")
        timeframe = data.get("timeframe", "today 3-m")

        # Accept keywords as comma-separated string too (just in case)
        if isinstance(keywords, str):
            keywords = [k.strip() for k in keywords.split(",") if k.strip()]

        if not isinstance(keywords, list) or len(keywords) == 0:
            return jsonify({
                "error": "keywords must be a non-empty list (or comma-separated string)",
                "received_type": str(type(data.get("keywords"))),
                "received_value_preview": str(data.get("keywords"))[:200]
            }), 400

        # Build trends request
        pytrends = TrendReq(hl="en-US", tz=360, retries=2, backoff_factor=0.2)
        pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)

        df = pytrends.interest_over_time()

        if df is None or df.empty:
            return jsonify({"geo": geo, "timeframe": timeframe, "series": []}), 200

        result = []
        for kw in keywords:
            if kw not in df.columns:
                continue

            points = []
            for idx, val in df[kw].items():
                points.append({
                    "date": idx.strftime("%Y-%m-%d"),
                    "value": int(val)
                })

            result.append({"keyword": kw, "points": points})

        return jsonify({"geo": geo, "timeframe": timeframe, "series": result}), 200

    except Exception as e:
        # Return the error so you can debug (instead of generic 500)
        return jsonify({
            "error": "collector_failed",
            "message": str(e)
        }), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)
