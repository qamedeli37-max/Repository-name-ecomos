"""
启动入口 — 检查依赖并启动 Streamlit
"""
import sys
import os
import subprocess

# 确保终端 UTF-8 编码
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

REQUIRED_PACKAGES = ["streamlit", "yfinance", "pandas"]


def check_dependencies() -> bool:
    missing = []
    for pkg in REQUIRED_PACKAGES:
        try:
            __import__(pkg)
        except ImportError:
            missing.append(pkg)
    if missing:
        print(f"[依赖缺失] 请先安装: pip install {' '.join(missing)}")
        return False
    return True


def main():
    if not check_dependencies():
        sys.exit(1)

    dashboard_path = os.path.join(os.path.dirname(__file__), "dashboard.py")
    print("[启动] 正在启动小龙虾实时盯盘系统...")

    env = os.environ.copy()
    env["STREAMLIT_CONSOLE_EMAIL"] = ""
    env["PYTHONIOENCODING"] = "utf-8"

    # subprocess 启动，stdin 传回车跳过 Streamlit 邮箱提示
    proc = subprocess.Popen(
        ["py", "-m", "streamlit", "run", dashboard_path],
        stdin=subprocess.PIPE,
        stdout=sys.stdout,
        stderr=sys.stderr,
        env=env,
    )
    # 发送回车跳过首次运行的邮箱输入
    proc.stdin.write(b"\n")
    proc.stdin.flush()

    try:
        proc.wait()
    except KeyboardInterrupt:
        proc.terminate()


if __name__ == "__main__":
    main()
