from flask import Flask, request, jsonify
from pytrends.request import TrendReq

app = Flask(__name__)

@app.route("/trends", methods=["POST"])
def trends():
    data = request.get_json(force=True)

    keywords = data.get("keywords", [])
    geo = data.get("geo", "ZA")
    timeframe = data.get("timeframe", "today 3-m")

    pytrends = TrendReq(hl="en-US", tz=360)
    pytrends.build_payload(
        kw_list=keywords,
        timeframe=timeframe,
        geo=geo
    )

    df = pytrends.interest_over_time()

    if df.empty:
        return jsonify({"geo": geo, "timeframe": timeframe, "series": []})

    result = []

    for kw in keywords:
        points = []
        for idx, val in df[kw].items():
            points.append({
                "date": idx.strftime("%Y-%m-%d"),
                "value": int(val)
            })

        result.append({
            "keyword": kw,
            "points": points
        })

    return jsonify({
        "geo": geo,
        "timeframe": timeframe,
        "series": result
    })

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
