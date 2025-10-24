"""
用法：
  1) 安装 cliclick: brew install cliclick
  2) 运行
"""
import subprocess, random, time, sys, shutil, os, signal, threading

# ---------- helper ----------
def find_cliclick():
    p = shutil.which("cliclick")
    if p:
        return p
    for c in ["/opt/homebrew/bin/cliclick", "/usr/local/bin/cliclick"]:
        if os.path.exists(c) and os.access(c, os.X_OK):
            return c
    return None

def get_mouse_pos(cliclick_path):
    try:
        res = subprocess.run([cliclick_path, "p"], capture_output=True, text=True, timeout=1)
        out = res.stdout.strip()
        if not out:
            return None
        parts = out.split(",")
        if len(parts) >= 2:
            return int(parts[0].strip()), int(parts[1].strip())
    except Exception:
        return None

def cliclick_click(cliclick_path, x, y):
    subprocess.run([cliclick_path, f"c:{x},{y}"], timeout=5)

def sample_intervals(n_clicks, min_itv=2.0, max_itv=3.0, total_time=10.0):
    assert n_clicks >= 2
    while True:
        intervals = [random.uniform(min_itv, max_itv) for _ in range(n_clicks - 1)]
        s = sum(intervals)
        if s <= total_time:
            pre_delay = total_time - s
            return intervals, pre_delay

# ---------- stop event ----------
stop_event = threading.Event()

def sigint_handler(sig, frame):
    stop_event.set()
    print("\n收到中断信号 (Ctrl+C)，准备停止...")

signal.signal(signal.SIGINT, sigint_handler)

# ---------- main ----------
def main():
    cliclick = find_cliclick()
    if not cliclick:
        print("未找到 cliclick，请先安装：brew install cliclick")
        sys.exit(1)
    print(f"使用 cliclick 路径: {cliclick}")

    input("步骤1：把鼠标移到你想选的区域左上角，然后按 Enter 以记录该坐标...")
    tl = get_mouse_pos(cliclick)
    if not tl:
        print("无法读取鼠标位置，请确认 cliclick 可用并已授予辅助功能权限（Accessibility）。")
        sys.exit(1)
    print("左上角坐标:", tl)

    input("步骤2：把鼠标移到区域右下角，然后按 Enter 以记录该坐标...")
    br = get_mouse_pos(cliclick)
    if not br:
        print("无法读取鼠标位置，请确认 cliclick 可用并已授予辅助功能权限（Accessibility）。")
        sys.exit(1)
    print("右下角坐标:", br)

    x1,y1 = tl
    x2,y2 = br
    xmin, xmax = min(x1,x2), max(x1,x2)
    ymin, ymax = min(y1,y2), max(y1,y2)
    print(f"区域确认：({xmin},{ymin}) -> ({xmax},{ymax})")

    between_min = float(input("输入 burst 之间等待的最小秒数（默认 1.0，回车使用默认）: ") or "1.0")
    between_max = float(input("输入 burst 之间等待的最大秒数（默认 5.0，回车使用默认）: ") or "5.0")
    repeats = int(input("重复次数（0 表示无限，默认 0）: ") or "0")

    runs = 0
    try:
        while (repeats == 0 or runs < repeats) and not stop_event.is_set():
            runs += 1
            n_clicks = random.choice([4,5])
            intervals, pre_delay = sample_intervals(n_clicks, 0.2, 1.0, total_time=3.0)
            print(f"\nRun {runs}: clicks={n_clicks}, pre_delay={pre_delay:.2f}, intervals={[round(i,2) for i in intervals]}")

            # pre delay with emergency check
            slept = 0.0
            step = 0.1
            while slept < pre_delay and not stop_event.is_set():
                time.sleep(min(step, pre_delay - slept))
                slept += min(step, pre_delay - slept)
                pos = get_mouse_pos(cliclick)
                if pos and pos[0] <= 3 and pos[1] <= 3:
                    print("检测到鼠标在左上角，紧急停止。")
                    stop_event.set()
                    break
            if stop_event.is_set():
                break

            # 执行点击序列
            for i in range(n_clicks):
                if stop_event.is_set():
                    break
                pos = get_mouse_pos(cliclick)
                if pos and pos[0] <= 3 and pos[1] <= 3:
                    print("检测到鼠标在左上角，紧急停止。")
                    stop_event.set()
                    break
                rx = random.randint(xmin, xmax)
                ry = random.randint(ymin, ymax)
                print(f"点击 {i+1}/{n_clicks} -> ({rx},{ry})")
                cliclick_click(cliclick, rx, ry)
                if i < n_clicks - 1:
                    wait = intervals[i]
                    slept2 = 0.0
                    while slept2 < wait and not stop_event.is_set():
                        time.sleep(min(step, wait - slept2))
                        slept2 += min(step, wait - slept2)
                        pos = get_mouse_pos(cliclick)
                        if pos and pos[0] <= 3 and pos[1] <= 3:
                            print("检测到鼠标在左上角，紧急停止。")
                            stop_event.set()
                            break
            if stop_event.is_set():
                break

            print(f"Run {runs} 完成（burst 总时长约 3.0s）")
            if repeats != 0 and runs >= repeats:
                break

            between = random.uniform(between_min, between_max)
            print(f"等待 {between:.2f}s 后开始下一个 burst（或移动鼠标左上角以紧急停止）")
            waited = 0.0
            while waited < between and not stop_event.is_set():
                time.sleep(min(0.1, between - waited))
                waited += min(0.1, between - waited)
                pos = get_mouse_pos(cliclick)
                if pos and pos[0] <= 3 and pos[1] <= 3:
                    print("检测到鼠标在左上角，紧急停止。")
                    stop_event.set()
                    break

        print("\n任务结束。")
    except Exception as e:
        print("运行出错:", e)

if __name__ == "__main__":
    main()

