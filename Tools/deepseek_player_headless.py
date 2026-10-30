"""Controller: play one real match against the in-game CPU opponent.

Constraints (per docs/AI玩家参赛规则与操作要求.md):
  * observe only the game window screenshot;
  * act only with ordinary keyboard/mouse input to the game window;
  * never write to the game, never read game logs / memory / hidden state.

Key handling: the API key is read from %SK% and never printed or written to
any artifact produced by this script (screenshots, JSONL events, md report).
"""
import argparse
import base64
import ctypes as C
from ctypes import wintypes as W
from datetime import datetime
import io
import json
import os
from pathlib import Path
import sys
import time

from PIL import ImageGrab

API_URL = 'https://api.deepseek.com/chat/completions'
ROOT = Path(__file__).resolve().parents[1]
GAME_EXE_NAME = 'beyblade-unreal-prototype\\Binaries\\Win64\\BeybladePrototype.exe'
OUT = ROOT / 'Saved' / 'SelfplayReports'
KEYS = {'space': 0x20, 'e': 0x45, 'r': 0x52, 'q': 0x51, 'a': 0x41, 'd': 0x44,
        'w': 0x57, 's': 0x53, 'shift': 0x10, 'enter': 0x0D, 'esc': 0x1B,
        **{str(i): 0x30 + i for i in range(1, 10)}}
ALLOWED_ACTIONS = ('key', 'hold', 'click', 'wait', 'stop')


# ---------------------------------------------------------------- window I/O
class GameWindow:
    def __init__(self):
        self.u = C.WinDLL('user32', use_last_error=True)
        self.k = C.WinDLL('kernel32', use_last_error=True)
        self.u.GetForegroundWindow.restype = W.HWND
        self.u.FindWindowW.restype = W.HWND
        self.u.FindWindowW.argtypes = (W.LPCWSTR, W.LPCWSTR)
        self.u.GetWindowThreadProcessId.argtypes = (W.HWND, C.POINTER(W.DWORD))
        self.u.GetClientRect.argtypes = (W.HWND, C.POINTER(W.RECT))
        self.u.ClientToScreen.argtypes = (W.HWND, C.POINTER(W.POINT))
        self.u.SetForegroundWindow.argtypes = (W.HWND,)
        self.u.BringWindowToTop.argtypes = (W.HWND,)
        self.u.SetFocus.argtypes = (W.HWND,)
        self.u.AttachThreadInput.argtypes = (W.DWORD, W.DWORD, W.BOOL)
        self.u.AttachThreadInput.restype = W.BOOL
        self.k.GetCurrentThreadId.restype = W.DWORD
        self.u.ShowWindow.argtypes = (W.HWND, C.c_int)
        self.k.OpenProcess.argtypes = (W.DWORD, W.BOOL, W.DWORD)
        self.k.OpenProcess.restype = W.HANDLE
        self.k.QueryFullProcessImageNameW.argtypes = (W.HANDLE, W.DWORD, W.LPWSTR, C.POINTER(W.DWORD))
        self.k.CloseHandle.argtypes = (W.HANDLE,)
        self.hwnd = None

    def locate(self):
        hwnds = []
        proc = C.WINFUNCTYPE(W.BOOL, W.HWND, W.LPARAM)(
            lambda h, _: (hwnds.append(h), True)[1])
        self.u.EnumWindows(proc, 0)
        best = None
        for h in hwnds:
            pid = W.DWORD()
            self.u.GetWindowThreadProcessId(h, C.byref(pid))
            path = self._exe_path(pid.value)
            if path and path.lower().endswith(GAME_EXE_NAME.lower()):
                rect = W.RECT()
                self.u.GetClientRect(h, C.byref(rect))
                area = rect.right * rect.bottom
                if best is None or area > best[1]:
                    best = (h, area, path)
        if best is None:
            raise RuntimeError('没有找到正在运行的 beyblade-unreal-prototype 游戏窗口')
        self.hwnd = best[0]
        return best[2]

    def _exe_path(self, pid):
        handle = self.k.OpenProcess(0x1000, False, pid)
        if not handle:
            return None
        try:
            buf, size = C.create_unicode_buffer(32768), W.DWORD(32768)
            if self.k.QueryFullProcessImageNameW(handle, 0, buf, C.byref(size)):
                return buf.value
            return None
        finally:
            self.k.CloseHandle(handle)

    def focus(self, retries=4):
        if not self.hwnd:
            self.locate()
        for _ in range(retries):
            try:
                self._force_foreground()
            except Exception:
                pass
            if self.is_foreground():
                return True
            time.sleep(0.4)
        return self.is_foreground()

    def _force_foreground(self):
        """SetForegroundWindow can be refused; attach input threads to bypass the lock."""
        hwnd = self.hwnd
        self.u.ShowWindow(hwnd, 9)  # SW_RESTORE
        fg = self.u.GetForegroundWindow()
        fg_thread = self.u.GetWindowThreadProcessId(fg, None)
        cur_thread = self.k.GetCurrentThreadId()
        attached = False
        if fg_thread and fg_thread != cur_thread:
            attached = bool(self.u.AttachThreadInput(cur_thread, fg_thread, True))
        try:
            self.u.BringWindowToTop(hwnd)
            self.u.SetForegroundWindow(hwnd)
            self.u.SetFocus(hwnd)
        finally:
            if attached:
                self.u.AttachThreadInput(cur_thread, fg_thread, False)
        time.sleep(0.25)

    def is_foreground(self):
        return self.u.GetForegroundWindow() == self.hwnd

    def assert_foreground(self):
        if self.is_foreground():
            return
        # A transient window (notification, alt-tab) can steal the foreground;
        # try to win it back before refusing to input anything at all.
        self.note_focus_loss()
        if not self.focus(retries=3):
            raise RuntimeError('游戏窗口失去焦点且无法取回，已停止输入（以免误操作其他窗口）')

    def note_focus_loss(self):
        self.focus_losses = getattr(self, 'focus_losses', 0) + 1

    def client_rect(self):
        rect, pt = W.RECT(), W.POINT()
        if not self.u.GetClientRect(self.hwnd, C.byref(rect)) or not self.u.ClientToScreen(self.hwnd, C.byref(pt)):
            raise RuntimeError('无法读取游戏窗口范围')
        if rect.right < 300 or rect.bottom < 200:
            raise RuntimeError('游戏窗口不可见或尺寸过小')
        return pt.x, pt.y, rect.right, rect.bottom

    def capture(self):
        self.assert_foreground()
        x, y, w, h = self.client_rect()
        image = ImageGrab.grab(bbox=(x, y, x + w, y + h), all_screens=True)
        self.assert_foreground()
        return image

    def press(self, key, hold=0.07):
        self.assert_foreground()
        vk = KEYS[key]
        self.u.keybd_event(vk, 0, 0, 0)
        try:
            time.sleep(hold)
        finally:
            self.u.keybd_event(vk, 0, 2, 0)

    def click(self, rx, ry):
        x, y, w, h = self.client_rect()
        self.assert_foreground()
        self.u.SetCursorPos(x + int(w * rx), y + int(h * ry))
        self.assert_foreground()
        self.u.mouse_event(2, 0, 0, 0, 0)
        try:
            time.sleep(0.05)
        finally:
            self.u.mouse_event(4, 0, 0, 0, 0)


# ---------------------------------------------------------------- validation
def validate(value):
    if not isinstance(value, dict):
        raise ValueError('模型回复不是动作对象')
    action = value.get('action')
    if action not in ALLOWED_ACTIONS:
        raise ValueError('模型请求了未允许的动作: %r' % (action,))
    if action == 'key' and value.get('key') not in KEYS:
        raise ValueError('模型请求了未允许的按键: %r' % (value.get('key'),))
    if action == 'hold':
        if value.get('key') not in KEYS:
            raise ValueError('hold 需要合法 key')
        sec = value.get('seconds', 0.5)
        if type(sec) not in (int, float) or not 0.05 <= sec <= 3.0:
            raise ValueError('hold 时长越界')
    if action == 'click':
        for axis in ('x', 'y'):
            n = value.get(axis)
            if type(n) not in (int, float) or not 0 < n < 1:
                raise ValueError('点击坐标越界')
    if action == 'wait':
        sec = value.get('seconds', 2)
        if type(sec) not in (int, float) or not 0.5 <= sec <= 8:
            raise ValueError('等待时间越界')
    for field in ('observation', 'reason'):
        if not isinstance(value.get(field), str) or not value[field].strip():
            raise ValueError('缺少 observation 或 reason')
    return value


# ---------------------------------------------------------------- model call
PROMPT = '''你是 DeepSeek，作为参赛玩家体验一款 Unreal 陀螺对战游戏。你的对手是本机游戏内电脑。
只能依据下方这张游戏窗口截图行动，通过普通键盘鼠标操作，一次只做一个动作。
绝对不允许提出修改游戏、读内存/日志、开控制台、暂停或加速游戏的要求；你只能像普通玩家一样玩。

可用输入：
- key：短按一个键。key 只能取 space,e,r,q,a,d,w,s,shift,enter,esc,1~9
- hold：按住一个键若干秒（seconds 0.05~3.0），例如蓄力或移动
- click：点击截图中相对坐标 x,y（0~1 之间；左上角是 0,0，右下角是 1,1）
- wait：原地等待 seconds 秒（0.5~8），用于看动画
- stop：本局结束、无法操作或界面异常时结束体验，并在 observation/reason 写明原因

玩法要点（以画面实际情况为准）：
- 抢 8 分。常规选螺界面从八只陀螺里选三只并确定上场顺序；准备阶段 A/D 调发射角度（-45°~+45°），W/S 调力度（70%~120%，每次 5）；之后发射开打。
- 战斗中技能就绪按 Q 或点技能按钮；局间按提示继续/盲选/锁定/揭晓；比赛结束看结算。
- 每次动作后必须等下一张截图确认结果，不要连续盲点；不确定时用 wait。

回复要求：只输出一个 JSON 对象，不要任何多余文字。字段：
{"action":"key|hold|click|wait|stop","key":"space","seconds":1,"x":0.5,"y":0.5,
 "observation":"你在这张截图里实际看到的界面、文字、按钮、比分等","reason":"为什么做这个动作"}
observation 必须写你真实看到的内容，不能编造未执行的动作。
'''


def _strip_fences(text):
    text = text.strip()
    if text.startswith('```'):
        text = text.split('\n', 1)[1] if '\n' in text else text
        if text.rstrip().endswith('```'):
            text = text.rstrip()[:-3]
    start, end = text.find('{'), text.rfind('}')
    if start >= 0 and end > start:
        text = text[start:end + 1]
    return text.strip()


def _request(key, model, data_url, recent, max_tokens):
    payload = {
        'model': model,
        'max_tokens': max_tokens,
        'response_format': {'type': 'json_object'},
        'messages': [
            {'role': 'system', 'content': PROMPT},
            {'role': 'user', 'content': [
                {'type': 'text', 'text': '最近已执行的动作：' + json.dumps(recent, ensure_ascii=False)
                 + '\n这是当前游戏画面截图（窗口内坐标）。请决定下一个动作。'},
                {'type': 'image_url', 'image_url': {'url': data_url}}]}],
    }
    req = urllib.request.Request(
        API_URL, data=json.dumps(payload).encode(),
        headers={'Authorization': 'Bearer ' + key, 'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as error:
        raise RuntimeError('DeepSeek HTTP %d（请检查密钥/余额/模型名）' % error.code) from None
    except (urllib.error.URLError, TimeoutError):
        raise RuntimeError('DeepSeek 网络失败或超时') from None


def ask_model(key, model, image, history, max_tokens=2000, max_edge=1280):
    buf = io.BytesIO()
    if max(image.size) > max_edge:
        probe = image.copy()
        probe.thumbnail((max_edge, max_edge))
        probe.save(buf, format='PNG')
    else:
        image.save(buf, format='PNG')
    data_url = 'data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode('ascii')
    recent = [{k: a.get(k) for k in ('action', 'key', 'x', 'y', 'seconds')} for a in history[-6:]]

    # deepseek-flash is a thinking model: reasoning_content shares max_tokens with
    # the answer. If the budget is exhausted the JSON comes back empty, so escalate.
    budget = max_tokens
    last = None
    for attempt in range(3):
        data = _request(key, model, data_url, recent, budget)
        choice = data['choices'][0]
        message = choice.get('message', {})
        content = (message.get('content') or '').strip()
        finish = choice.get('finish_reason')
        if content:
            try:
                return validate(json.loads(_strip_fences(content)))
            except (ValueError, json.JSONDecodeError) as error:
                last = error
        else:
            last = RuntimeError('JSON 为空（finish=%s）' % finish)
        if finish == 'length' or not content:
            budget = min(budget * 2, 8192)
            continue
        break
    raise RuntimeError('模型没有返回可用动作：%s' % last)


import urllib.error  # noqa: E402  (used inside ask_model)
import urllib.request  # noqa: E402


# ---------------------------------------------------------------- session
class Session:
    def __init__(self, model, max_steps, deadline_min, stamp):
        self.model = model
        self.max_steps = max_steps
        self.deadline = time.monotonic() + deadline_min * 60
        self.folder = OUT / stamp
        self.folder.mkdir(parents=True, exist_ok=True)
        self.events = (self.folder / 'events.jsonl').open('w', encoding='utf-8')
        self.window = GameWindow()
        self.exe = self.window.locate()
        self.start = datetime.now()
        self.note('session_start', exe=self.exe, model=model, max_steps=max_steps,
                  deadline_min=deadline_min)

    def note(self, kind, **fields):
        rec = {'t': datetime.now().isoformat(timespec='seconds'), 'kind': kind, **fields}
        self.events.write(json.dumps(rec, ensure_ascii=False) + '\n')
        self.events.flush()

    def run(self, key):
        history = []
        outcome = 'reached_step_limit'
        step = 0
        try:
            if not self.window.focus():
                raise RuntimeError('无法把游戏窗口切到前台')
            self.note('focused', foreground=self.window.is_foreground())
            for step in range(1, self.max_steps + 1):
                if time.monotonic() >= self.deadline:
                    outcome = 'deadline_reached'
                    break
                image = self.window.capture()
                shot = self.folder / ('%03d-before.png' % step)
                image.save(shot)
                self.note('screenshot', step=step, file=shot.name, size=image.size)
                started = time.monotonic()
                action = ask_model(key, self.model, image, history)
                latency = round(time.monotonic() - started, 2)
                self.note('model_action', step=step, latency_s=latency, **action)
                if action['action'] == 'stop':
                    outcome = 'model_stop'
                    break
                self.window.act_action(action)
                self.note('executed', step=step, action=action['action'],
                          key=action.get('key'), x=action.get('x'), y=action.get('y'),
                          seconds=action.get('seconds'))
                history.append(action)
                self.window.wait_for_settle(action)
            else:
                outcome = 'reached_step_limit'
        except Exception as error:  # keep message free of any secret
            outcome = 'error:%s:%s' % (type(error).__name__, error)
            self.note('error', message=str(error))
            raise
        finally:
            final = None
            try:
                final = self.window.capture()
                final.save(self.folder / 'zzz-final.png')
            except Exception:
                pass
            self.note('session_end', outcome=outcome, steps=step,
                      seconds=round((datetime.now() - self.start).total_seconds(), 1))
            self.events.close()
        return outcome, step


# attach input helpers after class definition (keeps them tidy)
def _act_action(self, action):
    kind = action['action']
    if kind == 'key':
        self.press(action['key'])
    elif kind == 'hold':
        self.press(action['key'], hold=float(action.get('seconds', 0.5)))
    elif kind == 'click':
        self.click(float(action['x']), float(action['y']))
    elif kind == 'wait':
        pass


def _wait_for_settle(self, action):
    kind = action['action']
    if kind == 'wait':
        time.sleep(float(action.get('seconds', 2)))
    elif kind == 'hold':
        time.sleep(0.35 + float(action.get('seconds', 0.5)) * 0.5)
    else:
        time.sleep(0.9)


GameWindow.act_action = _act_action
GameWindow.wait_for_settle = _wait_for_settle


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--model', default='deepseek-flash')
    parser.add_argument('--max-steps', type=int, default=200)
    parser.add_argument('--deadline-min', type=float, default=20)
    parser.add_argument('--stamp', default=datetime.now().strftime('%Y%m%d-%H%M%S'))
    args = parser.parse_args()
    key = os.environ.get('SK', '').strip()
    if not key:
        print('ERROR: %SK% 环境变量里没有 API 密钥', file=sys.stderr)
        return 2
    C.windll.user32.SetProcessDPIAware()
    session = Session(args.model, args.max_steps, args.deadline_min, args.stamp)
    print('report folder:', session.folder, flush=True)
    try:
        outcome, steps = session.run(key)
    finally:
        key = ''
        os.environ.pop('SK', None)
    print('OUTCOME:', outcome, 'STEPS:', steps, flush=True)
    print('FOLDER:', session.folder, flush=True)
    return 0


if __name__ == '__main__':
    sys.exit(main())
