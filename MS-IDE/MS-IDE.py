#!/usr/bin/env python3
# MS-IDE.py  ——  编辑 + 运行 + 备份一体化
import os
import sys
import shutil
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
from datetime import datetime

# ---------- 翻译器核心 ----------
def run_ms(ms_file):
    ms_dir = os.path.dirname(os.path.abspath(ms_file))
    os.chdir(ms_dir)
    with open(ms_file, encoding='utf-8') as f:
        lines = [l.rstrip() for l in f]

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('新建'):
            path = os.path.join(ms_dir, line[2:].strip())
            os.makedirs(os.path.dirname(path) or ms_dir, exist_ok=True)
            if os.path.splitext(path)[1]:
                open(path, 'w').close()
            else:
                os.makedirs(path, exist_ok=True)

        elif line.startswith('写入 '):
            file_path = line[3:].strip()
            full_path = os.path.join(ms_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            if i + 1 < len(lines) and lines[i + 1] == '"""':
                content_lines, j = [], i + 2
                while j < len(lines) and lines[j] != '"""':
                    content_lines.append(lines[j])
                    j += 1
                content = '\n'.join(content_lines)
                i = j + 1
            else:
                raise ValueError(f"{ms_file}:{i + 1} 写入块必须以 \"\"\" 开始并结束")
            with open(full_path, 'w', encoding='utf-8') as wf:
                wf.write(content)

        elif line.startswith('复制'):
            _, src, dst = line.split(maxsplit=2)
            src = os.path.join(ms_dir, src)
            dst = os.path.join(ms_dir, dst)
            if os.path.isdir(src):
                shutil.copytree(src, dst, dirs_exist_ok=True)
            else:
                shutil.copy2(src, dst)

        elif line.startswith('删除'):
            path = os.path.join(ms_dir, line[2:].strip())
            if os.path.isdir(path):
                shutil.rmtree(path)
            elif os.path.isfile(path):
                os.remove(path)

        elif line.startswith("运行 "):
            cmd = line[2:].strip()
            first = cmd.split()[0]
            if not os.path.isabs(first):
                first = os.path.join(ms_dir, first)
            cwd = os.path.dirname(first) or ms_dir
            proc = subprocess.run(cmd, shell=True, cwd=cwd,
                                  capture_output=True, text=True)
            if proc.returncode:
                raise RuntimeError(proc.stderr or proc.stdout)
        i += 1

# ---------- GUI ----------
class MsIDE(tk.Tk):
    # ---------- 工具 ----------
    def flash_title(self, msg, ms=1500):
        # 取消上一次未完成的定时器（如果有）
        if hasattr(self, "_flash_id"):
            self.after_cancel(self._flash_id)

        # 保存当前正确标题
        if self.ms_path:
            base = os.path.basename(self.ms_path)
            original = f"Manifest Script IDE – {base}{' *' if self._dirty else ''}"
        else:
            original = f"Manifest Script IDE{' *' if self._dirty else ''}"

        self.title(msg)
        # 设置新的定时器并记录 id
        self._flash_id = self.after(ms, lambda: self.title(original))

    def _update_title(self):
        if self.ms_path:
            base = os.path.basename(self.ms_path)
            mark = " *" if self._dirty else ""
            self.title(f"Manifest Script IDE – {base}{mark}")
        else:
            mark = " *" if self._dirty else ""
            self.title(f"Manifest Script IDE{mark}")

    # ---------- 高亮 ----------
    def highlight(self):
        self.editor.tag_remove("kw", "1.0", "end")
        self.editor.tag_remove("str", "1.0", "end")
        keywords = {"新建", "写入", "复制", "删除", "运行"}
        lineno = 1
        for line in self.editor.get("1.0", "end-1c").splitlines(True):
            for kw in keywords:
                idx = 0
                while True:
                    idx = line.find(kw, idx)
                    if idx == -1:
                        break
                    self.editor.tag_add(
                        "kw", f"{lineno}.{idx}", f"{lineno}.{idx + len(kw)}")
                    idx += 1
            if '"""' in line:
                self.editor.tag_add("str", f"{lineno}.0", f"{lineno}.end")
            lineno += 1

    # ---------- 撤销 ----------
    def _push_undo(self, ev=None):
        text = self.editor.get("1.0", "end-1c")
        if self._undo_stack[self._undo_pos] != text:
            self._undo_stack = self._undo_stack[: self._undo_pos + 1]
            self._undo_stack.append(text)
            self._undo_pos += 1
            if ev is None:               # 只标记“已修改”
                self._dirty = True
                self._update_title()

    def _undo(self):
        if self._undo_pos > 0:
            self._undo_pos -= 1
            self._apply_undo_text()
            self.flash_title("已撤销")

    def _redo(self):
        if self._undo_pos < len(self._undo_stack) - 1:
            self._undo_pos += 1
            self._apply_undo_text()
            self.flash_title("已重做")

    def _apply_undo_text(self):
        text = self._undo_stack[self._undo_pos]
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", text)
        self.highlight()

    # ---------- 文件 ----------
    def new_file(self):
        self.ms_path = None
        self._undo_stack.clear()
        self._undo_stack.append("")
        self._undo_pos = 0
        self._dirty = False
        self.editor.delete("1.0", "end")
        self._update_title()
        self.flash_title("新建文件")

    def open_file(self):
        path = filedialog.askopenfilename(filetypes=[("MS 文件", "*.ms")])
        if path:
            self.load_ms(path)
            self.flash_title("已打开")

    def save_file(self):
        if not self.ms_path:
            self.ms_path = filedialog.asksaveasfilename(
                defaultextension=".ms", filetypes=[("MS 文件", "*.ms")])
        if self.ms_path:
            with open(self.ms_path, "w", encoding="utf-8") as f:
                f.write(self.editor.get("1.0", "end").rstrip())
            self._dirty = False
            self._update_title()
            self.flash_title("已保存")

    def run_file(self):
        self.save_file()
        if not self.ms_path:
            return
        try:
            run_ms(self.ms_path)
            self.flash_title("运行成功")
        except Exception as e:
            messagebox.showerror("运行失败", str(e))

    def load_ms(self, path):
        self.ms_path = path
        with open(path, encoding="utf-8") as f:
            content = f.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)

        # 自动保存一份，防止撤销到空
        backup_dir = os.path.join(os.path.dirname(path), "backups")
        os.makedirs(backup_dir, exist_ok=True)
        safe_name = datetime.now().strftime("%Y%m%d_%H%M%S") + "_" + os.path.basename(path)
        with open(os.path.join(backup_dir, safe_name), "w", encoding="utf-8") as bf:
            bf.write(content)

        # 再初始化撤销栈
        self._undo_stack.clear()
        self._undo_stack.append(content)
        self._undo_pos = 0
        self._dirty = False
        self._update_title()
        self.highlight()

    def backup_file(self):
        # 先静默保存
        if not self.ms_path:
            return
        with open(self.ms_path, "w", encoding="utf-8") as f:
            f.write(self.editor.get("1.0", "end").rstrip())

        # 再备份
        src = self.ms_path
        backups = os.path.join(os.path.dirname(src), "backups")
        os.makedirs(backups, exist_ok=True)
        dst = os.path.join(backups,
                           datetime.now().strftime("%Y%m%d_%H%M%S") + ".ms")
        shutil.copy2(src, dst)

        # 只提示“已备份”
        self.flash_title("已备份")

    # ---------- 构造 ----------
    def __init__(self):
        super().__init__()
        self.title("Manifest Script IDE")
        self.geometry("800x600")
        self.ms_path = None
        self._undo_stack = [""]
        self._undo_pos = 0
        self._dirty = False
        self._update_title()

        # 工具栏
        bar = tk.Frame(self)
        bar.pack(fill="x")
        tk.Button(bar, text="新建", command=self.new_file).pack(side="left")
        tk.Button(bar, text="打开", command=self.open_file).pack(side="left")
        tk.Button(bar, text="保存", command=self.save_file).pack(side="left")
        tk.Button(bar, text="运行", command=self.run_file).pack(side="left")
        tk.Button(bar, text="备份", command=self.backup_file).pack(side="left")
        tk.Button(bar, text="回档", command=self.rollback_file).pack(side="left")

        # 编辑区
        self.editor = scrolledtext.ScrolledText(
            self, font=("Consolas", 12), undo=False, maxundo=-1)
        self.editor.pack(fill="both", expand=True)

        # 颜色
        self.editor.tag_configure("kw", foreground="#007acc")
        self.editor.tag_configure("str", foreground="#d75f00")

        # 快捷键
        self.bind_all("<Control-s>",
                      lambda e: (self.save_file(), self.flash_title("已保存")))
        self.bind_all("<Control-z>",      lambda e: self._undo())
        self.bind_all("<Control-Shift-Z>", lambda e: self._redo())

        # 实时高亮
        self.editor.bind("<KeyRelease>", lambda *_: self.highlight())
        self.editor.bind("<Button-1>",   lambda *_: self.highlight())

        # 输入后压栈
        self.editor.bind("<KeyRelease>",
                         lambda ev: self.after_idle(self._push_undo), add=True)

    # ---------- 回档 ----------
    def rollback_file(self):
        if not self.ms_path:
            messagebox.showwarning("无法回档", "请先打开或保存一个文件。")
            return
        backups_dir = os.path.join(os.path.dirname(self.ms_path), "backups")
        if not os.path.isdir(backups_dir) or not os.listdir(backups_dir):
            messagebox.showinfo("无备份", "当前目录下没有备份文件。")
            return

        # 让用户选择备份文件
        backup_path = filedialog.askopenfilename(
            title="选择要回档的备份",
            initialdir=backups_dir,
            filetypes=[("MS 备份", "*.ms")])
        if not backup_path:
            return  # 用户取消

        # 清空并写入备份内容
        with open(backup_path, encoding="utf-8") as bf:
            content = bf.read()
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)

        # 更新撤销栈与标记
        self._undo_stack.clear()
        self._undo_stack.append(content)
        self._undo_pos = 0
        self._dirty = True
        self._update_title()
        self.highlight()
        self.flash_title("已回档")

# ---------- 启动 ----------
if __name__ == '__main__':
    app = MsIDE()
    if len(sys.argv) > 1 and os.path.isfile(sys.argv[1]):
        app.load_ms(sys.argv[1])
    app.mainloop()
