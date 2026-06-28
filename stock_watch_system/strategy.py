"""
=====================
  策略层
  交易信号评分 & 预警判断
=====================
"""

from config import CHANGE_THRESHOLD, VOLUME_MULTIPLIER
from config import ALERT_CHANGE, ALERT_VOLUME, ALERT_BREAKOUT


def score_signal(change_pct: float, volume_ratio: float, above_ma5: bool) -> int:
    """
    评分规则：
      + 涨 > 2%          → +1
      + 跌 < -2%         → -1
      + 放量(>2倍均值)   → +1
      + 突破均线(上穿)   → +1
    """
    score = 0

    if change_pct > CHANGE_THRESHOLD:
        score += 1
    elif change_pct < -CHANGE_THRESHOLD:
        score -= 1

    if volume_ratio > VOLUME_MULTIPLIER:
        score += 1

    if above_ma5:
        score += 1

    return score


def level_from_score(score: int) -> tuple[str, str]:
    """
    等级映射：
      >= 3  → S级（强势）
      = 2   → A级（上涨）
      = 0~1 → B级（震荡）
      <= -1 → C级（弱势）
    """
    if score >= 3:
        return "S", "强势"
    elif score == 2:
        return "A", "上涨"
    elif 0 <= score <= 1:
        return "B", "震荡"
    else:
        return "C", "弱势"


def level_emoji(level: str) -> str:
    return {"S": "🔥", "A": "📈", "B": "➖", "C": "📉"}.get(level, "➖")


def signal_text(change_pct: float, volume_ratio: float, above_ma5: bool, score: int) -> str:
    """生成可读的信号描述"""
    parts = []
    if abs(change_pct) > CHANGE_THRESHOLD:
        direction = "大涨" if change_pct > 0 else "大跌"
        parts.append(direction)
    if volume_ratio > VOLUME_MULTIPLIER:
        parts.append("放量")
    if above_ma5 and score > 0:
        parts.append("站上均线")
    if not above_ma5 and change_pct < -CHANGE_THRESHOLD:
        parts.append("跌破均线")
    return "，".join(parts) if parts else "正常波动"


def need_alert(change_pct: float, volume_ratio: float, above_ma5: bool, score: int) -> tuple[bool, str]:
    """
    预警判断：
      - 涨跌幅 > 2%
      - 放量 > 2倍均值
      - 明显突破/跌破
    """
    reasons = []
    if abs(change_pct) > ALERT_CHANGE:
        reasons.append(f"涨跌幅 {change_pct:+.2f}%")
    if volume_ratio > ALERT_VOLUME:
        reasons.append(f"放量 {volume_ratio:.1f}倍")
    if ALERT_BREAKOUT:
        if above_ma5 and score >= 2:
            reasons.append("突破均线")
        elif not above_ma5 and change_pct < -ALERT_CHANGE:
            reasons.append("跌破均线")

    if reasons:
        return True, "；".join(reasons)
    return False, ""


def analyze(metrics: dict) -> dict:
    """
    对单只股票的指标执行完整分析。
    返回含信号、等级、预警的报告 dict。
    """
    chg  = metrics["change_pct"]
    vol_ratio = metrics["volume_ratio"]
    ma5  = metrics["above_ma5"]

    score = score_signal(chg, vol_ratio, ma5)
    level, level_label = level_from_score(score)
    sig   = signal_text(chg, vol_ratio, ma5, score)
    alert, alert_reason = need_alert(chg, vol_ratio, ma5, score)

    return {
        "score":        score,
        "level":        level,
        "level_label":  level_label,
        "level_emoji":  level_emoji(level),
        "signal":       sig,
        "alert":        alert,
        "alert_reason": alert_reason,
    }
