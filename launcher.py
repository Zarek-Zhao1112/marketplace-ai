import subprocess
import sys
from pathlib import Path

if sys.stdout.encoding and sys.stdout.encoding.lower() not in ("utf-8", "utf8"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE = Path(__file__).resolve().parent
VENV_DIR = BASE / ".venv"
VENV_PY = VENV_DIR / "Scripts" / "python.exe"
BROWSER_FLAG = VENV_DIR / ".browsers_ok"


def banner(title: str):
    width = 46
    line = "=" * width
    print(line)
    print(f"{title:^{width}}")
    print(line)


def wait_exit():
    try:
        input("按回车键退出...")
    except EOFError:
        pass
    sys.exit(1)


def run_step(step: str, args: list):
    print(f"[{step}]")
    proc = subprocess.run(args)
    if proc.returncode != 0:
        print("[错误] 上一步执行失败，请检查网络或重试。")
        wait_exit()


def main():
    banner("Newegg 运营工具 - 一键启动")

    if sys.version_info < (3, 10):
        print("[错误] 需要 Python 3.10 及以上版本。")
        wait_exit()

    if not VENV_PY.exists():
        print("[1/3] 首次运行，正在创建虚拟环境（约 1 分钟）...")
        run_step("1/3 创建虚拟环境", [sys.executable, "-m", "venv", str(VENV_DIR)])
    else:
        print("[1/3] 虚拟环境已存在，跳过。")

    print("[2/3] 检查依赖（已安装的会自动跳过）...")
    run_step(
        "2/3 安装依赖",
        [str(VENV_PY), "-m", "pip", "install", "-q", "--disable-pip-version-check", "-r", str(BASE / "requirements.txt")],
    )

    if not BROWSER_FLAG.exists():
        print("[3/3] 首次运行，正在下载浏览器组件（约 1-2 分钟）...")
        try:
            proc = subprocess.run([str(VENV_PY), "-m", "playwright", "install", "chromium"])
            if proc.returncode == 0:
                BROWSER_FLAG.write_text("done", encoding="utf-8")
            else:
                print("[警告] 浏览器组件下载失败，爬虫功能可能不可用，其他功能不受影响。")
        except Exception:
            print("[警告] 浏览器组件下载失败，爬虫功能可能不可用，其他功能不受影响。")
    else:
        print("[3/3] 浏览器组件已就绪。")

    banner("启动成功！浏览器将自动打开（端口 8502）")
    print("关闭本窗口即停止运行")
    print()

    sys.exit(
        subprocess.run(
            [str(VENV_PY), "-m", "streamlit", "run", str(BASE / "app.py"), "--server.port", "8502"]
        ).returncode
    )


if __name__ == "__main__":
    main()
