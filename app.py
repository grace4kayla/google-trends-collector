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

        keywords = data.get("keywords", [])import os
import time
import random
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

        # IMPORTANT: reduce load to avoid Google 429s (batch in n8n if you need more)
        keywords = keywords[:2]

        # Build trends request
        pytrends = TrendReq(hl="en-US", tz=360, retries=0)
        pytrends.build_payload(kw_list=keywords, timeframe=timeframe, geo=geo)

        # Retry loop for Google Trends 429 rate limits
        df = None
        last_err = None
        for attempt in range(6):
            try:
                df = pytrends.interest_over_time()
                last_err = None
                break
            except Exception as e:
                last_err = e
                # If it's not a rate limit, fail fast
                if "429" not in str(e):
                    raise

                # Exponential backoff + small jitter (max 60s)
                sleep_s = min(60, (2 ** attempt) + random.random() * 2)
                time.sleep(sleep_s)

        if last_err:
            raise last_err

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
        msg = str(e)
        status = 500
        if "429" in msg or "too many" in msg.lower():
            status = 429

        return jsonify({
            "error": "collector_failed",
            "message": msg
        }), status

if __name__ == "__main__":
    port = int(os.environ.get("PORT", "10000"))
    app.run(host="0.0.0.0", port=port)

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
