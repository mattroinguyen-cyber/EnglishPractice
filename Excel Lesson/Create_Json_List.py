#!/usr/bin/env python3
import os
import json
import sys

try:
    import tkinter as tk
    from tkinter import filedialog, messagebox
except Exception:
    tk = None


def build_list(lessons_dir):
    entries = []
    # Only consider top-level .json lesson files (exclude mapping_*.json and json_list.json)
    json_files = [f for f in os.listdir(lessons_dir) if f.lower().endswith('.json')]
    for fname in sorted(json_files, key=str.casefold):
        lname = fname.lower()
        if lname == 'json_list.json' or lname.startswith('mapping_'):
            # skip generated index and mapping files
            continue
        base = os.path.splitext(fname)[0]

        # prefer mapping_<base>.json if it exists
        mapping_name = f"mapping_{base}.json"
        mapping_path = os.path.join(lessons_dir, mapping_name)
        mapping = mapping_name if os.path.exists(mapping_path) else ""

        # detect audio folder beside lessons_dir or inside it
        audio_name = f"audio_{base}"
        audio_path1 = os.path.join(lessons_dir, audio_name)
        audio_path2 = os.path.join(os.path.dirname(lessons_dir), audio_name)
        audio = audio_name if os.path.isdir(audio_path1) or os.path.isdir(audio_path2) else ""

        entries.append({
            "name": fname,
            "mapping": mapping,
            "audio": audio
        })
    return {"lessons": entries}


def write_output(data, out_dir):
    out_path = os.path.join(out_dir, 'json_list.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    return out_path


def run_gui():
    if tk is None:
        print('Tkinter is not available in this environment.')
        sys.exit(1)

    root = tk.Tk()
    root.title('Generate json_list.json')
    root.geometry('520x180')
    lessons_dir = tk.StringVar()
    out_dir = tk.StringVar()

    def choose_lessons():
        d = filedialog.askdirectory(title='Select lessons folder')
        if d:
            lessons_dir.set(d)

    def choose_output():
        d = filedialog.askdirectory(title='Select output folder')
        if d:
            out_dir.set(d)

    def generate():
        ld = lessons_dir.get().strip()
        od = out_dir.get().strip()
        if not ld or not os.path.isdir(ld):
            messagebox.showerror('Error', 'Please select a valid lessons folder')
            return
        if not od or not os.path.isdir(od):
            messagebox.showerror('Error', 'Please select a valid output folder')
            return
        data = build_list(ld)
        out_path = write_output(data, od)
        messagebox.showinfo('Done', f'json_list.json written to:\n{out_path}')

    def preview():
        ld = lessons_dir.get().strip()
        if not ld or not os.path.isdir(ld):
            messagebox.showerror('Error', 'Please select a valid lessons folder')
            return
        data = build_list(ld)
        win = tk.Toplevel(root)
        win.title('Preview detected lessons')
        win.geometry('560x320')
        lb = tk.Listbox(win, width=80, height=14)
        lb.pack(padx=8, pady=8, fill='both', expand=True)
        for item in data.get('lessons', []):
            lb.insert(tk.END, f"{item['name']}  |  mapping:{item['mapping']}  |  audio:{item['audio']}")
        def write_from_preview():
            od = out_dir.get().strip()
            if not od or not os.path.isdir(od):
                messagebox.showerror('Error', 'Please select a valid output folder')
                return
            out_path = write_output(data, od)
            messagebox.showinfo('Done', f'json_list.json written to:\n{out_path}')
            win.destroy()
        btn = tk.Button(win, text='Write json_list.json', command=write_from_preview, bg='#4CAF50', fg='white')
        btn.pack(pady=(0,8))

    frame = tk.Frame(root)
    frame.pack(padx=12, pady=12, fill='both', expand=True)

    tk.Label(frame, text='Lessons folder:').grid(row=0, column=0, sticky='w')
    tk.Entry(frame, textvariable=lessons_dir, width=50).grid(row=0, column=1, padx=6)
    tk.Button(frame, text='Browse', command=choose_lessons).grid(row=0, column=2)

    tk.Label(frame, text='Output folder:').grid(row=1, column=0, sticky='w', pady=(8,0))
    tk.Entry(frame, textvariable=out_dir, width=50).grid(row=1, column=1, padx=6, pady=(8,0))
    tk.Button(frame, text='Browse', command=choose_output).grid(row=1, column=2, pady=(8,0))

    btn_frame = tk.Frame(frame)
    btn_frame.grid(row=2, column=0, columnspan=3, pady=16)
    tk.Button(btn_frame, text='Preview', command=preview).pack(side='left', padx=6)
    tk.Button(btn_frame, text='Generate json_list.json', command=generate, bg='#4CAF50', fg='white').pack(side='left', padx=6)

    root.mainloop()


def run_cli(lessons_dir, out_dir):
    dry_run = '--dry-run' in sys.argv or '-n' in sys.argv
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    if not os.path.isdir(lessons_dir):
        print('Lessons folder not found:', lessons_dir)
        sys.exit(1)
    if not os.path.isdir(out_dir):
        print('Output folder not found:', out_dir)
        sys.exit(1)
    data = build_list(lessons_dir)
    if dry_run or verbose:
        print('Detected lessons:')
        for item in data.get('lessons', []):
            print(f"- {item['name']} | mapping={item['mapping']} | audio={item['audio']}")
    if dry_run:
        print('Dry-run: no file written.')
        return
    out_path = write_output(data, out_dir)
    print('Wrote', out_path)


if __name__ == '__main__':
    # If at least two arguments provided, treat as CLI: lessons_dir out_dir [flags]
    if len(sys.argv) >= 3:
        run_cli(sys.argv[1], sys.argv[2])
    else:
        run_gui()
