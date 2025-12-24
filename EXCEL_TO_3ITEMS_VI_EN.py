import os
import pandas as pd
from gtts import gTTS
import json
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter.ttk import Progressbar
import threading

class LessonGenerator:
    def __init__(self, root):
        self.root = root
        self.root.title("Tạo Bài Học Chuẩn - Vi/En")
        self.root.geometry("650x400")
        
        # Cấu hình chuẩn theo hệ thống hiện tại
        self.config = {
            "columns": {
                "en": 0,    # Tiếng Anh
                "ipa": 1,   # IPA
                "vi": 2,    # Tiếng Việt
                "ex_en": 3, # Ví dụ Anh
                "ex_ipa": 4,# Ví dụ IPA
                "ex_vi": 5  # Ví dụ Việt
            },
            "output_structure": {
                "lesson_dir": "LESSON",
                "audio_subdir": "audio_{lesson_name}",
                "lesson_file": "{lesson_name}.json",
                "mapping_file": "mapping_{lesson_name}.json"
            }
        }
        
        self.setup_ui()
    
    def setup_ui(self):
        # Frame chọn file
        tk.Label(self.root, text="Chọn file Excel (6 cột chuẩn):").pack(pady=5)
        self.frame_file = tk.Frame(self.root)
        self.frame_file.pack()
        self.entry_file = tk.Entry(self.frame_file, width=70)
        self.entry_file.pack(side=tk.LEFT, padx=5)
        tk.Button(self.frame_file, text="Duyệt", command=self.select_file).pack(side=tk.LEFT)
        
        # Frame tùy chọn
        self.frame_options = tk.LabelFrame(self.root, text="Tùy Chọn Âm Thanh", padx=10, pady=10)
        self.frame_options.pack(pady=10, fill=tk.X)
        
        self.var_gen_en = tk.BooleanVar(value=True)
        self.var_gen_vi = tk.BooleanVar(value=False)
        
        tk.Checkbutton(self.frame_options, text="Tạo âm thanh tiếng Anh (Cột 0 & 3)",
                      variable=self.var_gen_en).pack(anchor=tk.W)
        tk.Checkbutton(self.frame_options, text="Tạo âm thanh tiếng Việt (Cột 2 & 5)",
                      variable=self.var_gen_vi).pack(anchor=tk.W)
        
        # Progress bar
        self.progress = Progressbar(self.root, orient=tk.HORIZONTAL, length=500, mode='determinate')
        self.progress.pack(pady=10)
        
        # Nút thực hiện
        tk.Button(self.root, text="TẠO BÀI HỌC CHUẨN", 
                 command=self.start_generation,
                 bg="#0066CC", fg="white", font=('Arial', 10, 'bold')).pack(pady=10)
    
    def select_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Excel files", "*.xlsx *.xls")])
        if file_path:
            self.entry_file.delete(0, tk.END)
            self.entry_file.insert(0, file_path)
    
    def generate_audio(self, text, output_path, lang='en'):
        try:
            if not text.strip():
                return False
                
            tts = gTTS(text=text, lang=lang, slow=False)
            tts.save(output_path)
            return True
        except Exception as e:
            print(f"Lỗi khi tạo âm thanh: {str(e)}")
            return False
    
    def create_lesson(self):
        excel_path = self.entry_file.get()
        if not excel_path:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn file Excel!")
            return False
        
        try:
            # Đọc file Excel
            df = pd.read_excel(excel_path)
            if df.shape[1] < 6:
                messagebox.showerror("Lỗi", "File Excel phải có đúng 6 cột theo chuẩn!")
                return False
            
            lesson_name = os.path.splitext(os.path.basename(excel_path))[0]
            output_cfg = self.config["output_structure"]
            
            # Tạo thư mục LESSON nếu chưa có
            lesson_dir = output_cfg["lesson_dir"]
            os.makedirs(lesson_dir, exist_ok=True)
            
            # Tạo thư mục audio
            audio_dir = os.path.join(
                lesson_dir,
                output_cfg["audio_subdir"].format(lesson_name=lesson_name)
            )
            os.makedirs(audio_dir, exist_ok=True)
            
            # Chuẩn bị dữ liệu
            vocab_list = []
            audio_mapping = []
            total_items = (self.var_gen_en.get() * 2) + (self.var_gen_vi.get() * 2)
            processed = 0
            
            for idx, row in df.iterrows():
                # Chuẩn hóa dữ liệu
                row_data = [
                    str(row[self.config["columns"]["en"]]).replace("’", "'"),
                    str(row[self.config["columns"]["ipa"]]),
                    str(row[self.config["columns"]["vi"]]),
                    str(row[self.config["columns"]["ex_en"]]).replace("’", "'"),
                    str(row[self.config["columns"]["ex_ipa"]]),
                    str(row[self.config["columns"]["ex_vi"]])
                ]
                vocab_list.append(row_data)
                
                # Tạo âm thanh tiếng Anh
                if self.var_gen_en.get():
                    # Câu tiếng Anh chính
                    en_audio = f"en_{idx}.mp3"
                    if self.generate_audio(
                        row_data[0], 
                        os.path.join(audio_dir, en_audio),
                        'en'
                    ):
                        audio_mapping.append({
                            "text": row_data[0],
                            "file": os.path.join(output_cfg["audio_subdir"].format(lesson_name=lesson_name), en_audio),
                            "type": "en"
                        })
                    
                    # Ví dụ tiếng Anh
                    ex_en_audio = f"ex_en_{idx}.mp3"
                    if self.generate_audio(
                        row_data[3], 
                        os.path.join(audio_dir, ex_en_audio),
                        'en'
                    ):
                        audio_mapping.append({
                            "text": row_data[3],
                            "file": os.path.join(output_cfg["audio_subdir"].format(lesson_name=lesson_name), ex_en_audio),
                            "type": "ex_en"
                        })
                    
                    processed += 2
                    self.progress['value'] = (processed / (len(df) * total_items)) * 100
                    self.root.update_idletasks()
                
                # Tạo âm thanh tiếng Việt
                if self.var_gen_vi.get():
                    # Câu tiếng Việt chính
                    vi_audio = f"vi_{idx}.mp3"
                    if self.generate_audio(
                        row_data[2], 
                        os.path.join(audio_dir, vi_audio),
                        'vi'
                    ):
                        audio_mapping.append({
                            "text": row_data[2],
                            "file": os.path.join(output_cfg["audio_subdir"].format(lesson_name=lesson_name), vi_audio),
                            "type": "vi"
                        })
                    
                    # Ví dụ tiếng Việt
                    ex_vi_audio = f"ex_vi_{idx}.mp3"
                    if self.generate_audio(
                        row_data[5], 
                        os.path.join(audio_dir, ex_vi_audio),
                        'vi'
                    ):
                        audio_mapping.append({
                            "text": row_data[5],
                            "file": os.path.join(output_cfg["audio_subdir"].format(lesson_name=lesson_name), ex_vi_audio),
                            "type": "ex_vi"
                        })
                    
                    processed += 2
                    self.progress['value'] = (processed / (len(df) * total_items)) * 100
                    self.root.update_idletasks()
            
            # Lưu file bài học
            lesson_file = os.path.join(
                lesson_dir,
                output_cfg["lesson_file"].format(lesson_name=lesson_name)
            )
            with open(lesson_file, 'w', encoding='utf-8') as f:
                json.dump(vocab_list, f, ensure_ascii=False, indent=4)
            
            # Lưu file mapping
            mapping_file = os.path.join(
                lesson_dir,
                output_cfg["mapping_file"].format(lesson_name=lesson_name)
            )
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(audio_mapping, f, ensure_ascii=False, indent=4)
            
            messagebox.showinfo(
                "Thành công",
                f"Đã tạo bài học thành công!\n"
                f"Thư mục: {lesson_dir}\n"
                f"• File bài học: {lesson_file}\n"
                f"• File ánh xạ: {mapping_file}\n"
                f"• Thư mục âm thanh: {audio_dir}"
            )
            return True
            
        except Exception as e:
            messagebox.showerror("Lỗi", f"Có lỗi xảy ra: {str(e)}")
            return False
        finally:
            self.progress['value'] = 0
    
    def start_generation(self):
        threading.Thread(target=self.create_lesson, daemon=True).start()

if __name__ == "__main__":
    root = tk.Tk()
    app = LessonGenerator(root)
    root.mainloop()