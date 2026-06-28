"""
===================================
  小龙虾股票盯盘系统  🦞
  启动入口 — 直接运行即可
===================================
"""

import time
import sys
import os

# ── 确保控制台输出 UTF-8，避免 emoji 乱码 ──
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from datetime import datetime
from colorama import init, Fore, Back, Style

from config import WATCH_LIST, FETCH_PERIOD, FETCH_INTERVAL, REFRESH_SECONDS
from config import CLEAR_SCREEN, SHOW_TIMESTAMP
from data_fetcher import fetch_all
from strategy import analyze

# ─── 初始化 colorama（Windows 兼容） ───
init(autoreset=True)


# ─── 颜色工具 ───
def color_price(change: float) -> str:
    return Fore.GREEN if change >= 0 else Fore.RED

def color_level(level: str) -> str:
    return {"S": Fore.GREEN + Style.BRIGHT, "A": Fore.CYAN + Style.BRIGHT,
            "B": Fore.YELLOW, "C": Fore.RED + Style.BRIGHT}.get(level, Fore.WHITE)

def color_alert(flag: bool) -> str:
    return (Fore.RED + Style.BRIGHT + Back.YELLOW) if flag else Fore.BLACK + Style.DIM


# ─── 横幅 ───
def print_banner():
    banner = f"""
{Fore.CYAN}{Style.BRIGHT}
╔══════════════════════════════════════════════╗
║        🦞  小龙虾股票盯盘系统  v1.0         ║
║     {Fore.WHITE}Real-time Multi-Stock Watch{Fore.CYAN}               ║
╚══════════════════════════════════════════════╝{Style.RESET_ALL}
"""
    print(banner)


# ─── 单只股票输出 ───
def print_stock(symbol: str, name: str, metrics: dict, analysis: dict):
    """按指定格式输出一只股票的信息"""
    chg      = metrics["change_pct"]
    price    = metrics["price"]
    level    = analysis["level"]
    level_em = analysis["level_emoji"]
    signal   = analysis["signal"]
    alert    = analysis["alert"]
    alert_r  = analysis["alert_reason"]

    clr_price = color_price(chg)
    clr_level = color_level(level)
    clr_alert_bg = Fore.RED + Back.YELLOW + Style.BRIGHT if alert else Fore.GREEN

    print(f"{Fore.WHITE}{Style.BRIGHT}{'='*45}{Style.RESET_ALL}")
    print(f"{Fore.WHITE}  股票：{Fore.YELLOW}{Style.BRIGHT}{symbol}{Style.RESET_ALL}  {Fore.WHITE}{name}")
    print(f"{Fore.WHITE}  价格：{clr_price}{price}")
    print(f"  涨跌：{clr_price}{chg:+.2f}%{Style.RESET_ALL}")
    print(f"  等级：{clr_level}{level_em} {level}级（{analysis['level_label']}）{Style.RESET_ALL}")
    print(f"  信号：{Fore.WHITE}{signal}{Style.RESET_ALL}")
    print(f"  预警：{clr_alert_bg}{'⚠ 是  ' + alert_r if alert else '✔ 否'}{Style.RESET_ALL}")

    # 附加指标（缩进，辅助信息）
    print(f"{Fore.WHITE}  ├─ 最高 {metrics['high']}  /  最低 {metrics['low']}")
    print(f"  ├─ MA5 {metrics['ma5']}  {'📌 站上' if metrics['above_ma5'] else '⬇ 跌破'}")
    print(f"  ├─ 成交量 {_fmt_vol(metrics['volume'])}  /  均值 {_fmt_vol(metrics['volume_mean'])}")
    print(f"  └─ 放量比 {metrics['volume_ratio']:.1f}倍")
    print(f"{Fore.WHITE}{Style.BRIGHT}{'='*45}{Style.RESET_ALL}")
    print()


def _fmt_vol(v: int) -> str:
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:.2f}B"
    if v >= 1_000_000:
        return f"{v/1_000_000:.2f}M"
    if v >= 1_000:
        return f"{v/1_000:.1f}K"
    return str(v)


# ─── 统计摘要栏 ───
def print_summary(results: list[tuple], total: int, ok: int):
    s_count = sum(1 for _, _, a in results if a["level"] == "S")
    a_count = sum(1 for _, _, a in results if a["level"] == "A")
    c_count = sum(1 for _, _, a in results if a["level"] == "C")
    alert_count = sum(1 for _, _, a in results if a["alert"])

    print(f"{Fore.WHITE}📊 市场扫描：{total} 只 / 成功 {ok} 只"
          f"{Style.RESET_ALL}    "
          f"{Fore.GREEN}S {s_count}{Style.RESET_ALL}  "
          f"{Fore.CYAN}A {a_count}{Style.RESET_ALL}  "
          f"{Fore.YELLOW}B {ok - s_count - a_count - c_count}{Style.RESET_ALL}  "
          f"{Fore.RED}C {c_count}{Style.RESET_ALL}")

    if alert_count > 0:
        print(f"{Fore.RED}{Back.YELLOW}{Style.BRIGHT}⚠ 预警股票：{alert_count} 只，请关注！{Style.RESET_ALL}")
    else:
        print(f"{Fore.GREEN}✅ 暂无预警，市场平稳{Style.RESET_ALL}")


# ─── 更新间隔倒计时 ───
def print_footer(timestamp: str, elapsed: int):
    remaining = max(0, REFRESH_SECONDS - elapsed)
    bar_len = 30
    filled = int((elapsed / REFRESH_SECONDS) * bar_len) if REFRESH_SECONDS > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)

    if SHOW_TIMESTAMP:
        print(f"{Fore.WHITE}⏱ 上次更新：{timestamp}  "
              f"[{bar}] ({remaining}s 后刷新){Style.RESET_ALL}")


# ─── 主循环 ───
def main():
    print_banner()
    print(f"{Fore.CYAN}正在启动盯盘系统，首次获取数据...{Style.RESET_ALL}\n")

    symbols   = [s for s, _ in WATCH_LIST]
    name_map  = {s: n for s, n in WATCH_LIST}

    loop_count = 0

    while True:
        loop_count += 1
        start_time  = time.time()
        timestamp   = datetime.now().strftime("%H:%M:%S")

        # ── 拉取数据 ──
        all_metrics = fetch_all(symbols, FETCH_PERIOD, FETCH_INTERVAL)

        # ── 分析 & 输出 ──
        if CLEAR_SCREEN:
            os.system("cls" if os.name == "nt" else "clear")

        print_banner()
        print(f"{Fore.WHITE}{Style.DIM}━━━ 第 {loop_count} 轮扫描  {timestamp} ━━━{Style.RESET_ALL}\n")

        results = []
        ok_count = 0
        total = len(symbols)

        for sym in symbols:
            name = name_map.get(sym, sym)
            metrics = all_metrics.get(sym)

            if metrics is None:
                print(f"{Fore.RED}{Style.DIM}  ✗ {sym:12s}  数据获取失败（跳过）{Style.RESET_ALL}\n")
                continue

            analysis = analyze(metrics)
            results.append((sym, metrics, analysis))
            print_stock(sym, name, metrics, analysis)
            ok_count += 1

        # ── 摘要 ──
        print(f"{Fore.WHITE}{Style.BRIGHT}{'▔'*45}{Style.RESET_ALL}")
        print_summary(results, total, ok_count)

        # ── 底部信息 ──
        elapsed = int(time.time() - start_time)
        print_footer(timestamp, elapsed)

        # ── 等待到下一轮 ──
        sleep_time = max(1, REFRESH_SECONDS - elapsed)
        try:
            time.sleep(sleep_time)
        except KeyboardInterrupt:
            print(f"\n{Fore.RED}盯盘系统已退出。再见！{Style.RESET_ALL}")
            sys.exit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}盯盘系统已退出。再见！{Style.RESET_ALL}")
        sys.exit(0)
    except Exception as e:
        print(f"\n{Fore.RED}系统异常：{e}{Style.RESET_ALL}")
        print(f"{Fore.YELLOW}建议重启或检查网络/代理设置。{Style.RESET_ALL}")
        sys.exit(1)
