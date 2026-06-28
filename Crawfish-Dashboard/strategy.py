"""
策略层 — 信号评分 & 等级判定
"""


def signal_scorer(row: dict) -> dict:
    """
    评分规则:
      - 涨跌幅 > 2% → +1
      - 涨跌幅 < -2% → -1
      - 成交量 > 均值 × 2 → +1
      - 现价 > MA5 → +1

    返回:
      { "score": int, "level": str, "level_label": str,
        "signal_detail": str, "need_alert": bool, "alert_reason": str }
    """
    change_pct = row.get("Change_Pct", 0.0)
    volume = row.get("Volume", 0)
    avg_vol = row.get("Avg_Volume", 1)
    ma5 = row.get("MA5", 0.0)
    price = row.get("Current_Price", 0.0)

    score = 0
    detail_parts = []
    alert_reasons = []

    # 涨跌评分
    if change_pct > 2.0:
        score += 1
        detail_parts.append("+1(涨跌)")
        alert_reasons.append(f"涨幅 {change_pct:+.2f}%")
    elif change_pct < -2.0:
        score -= 1
        detail_parts.append("-1(涨跌)")
        alert_reasons.append(f"跌幅 {change_pct:+.2f}%")

    # 放量评分
    vol_ratio = volume / avg_vol if avg_vol > 0 else 1.0
    if vol_ratio > 2.0:
        score += 1
        detail_parts.append("+1(放量)")
        alert_reasons.append(f"放量 {vol_ratio:.1f}倍")

    # 均线评分
    if price > ma5 and ma5 > 0:
        score += 1
        detail_parts.append("+1(均线)")
    elif price < ma5 and ma5 > 0:
        detail_parts.append("+0(均线下)")

    # 等级映射
    if score >= 3:
        level, label = "S", "强势"
    elif score == 2:
        level, label = "A", "上涨"
    elif 0 <= score <= 1:
        level, label = "B", "震荡"
    else:
        level, label = "C", "弱势"

    # 预警判断
    need_alert = bool(alert_reasons)

    return {
        "score": score,
        "level": level,
        "level_label": label,
        "signal_detail": "".join(detail_parts) if detail_parts else "0(正常)",
        "need_alert": need_alert,
        "alert_reason": "；".join(alert_reasons) if alert_reasons else "",
        "vol_ratio": round(vol_ratio, 2),
    }
