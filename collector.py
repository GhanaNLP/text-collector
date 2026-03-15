#!/usr/bin/env python3
"""
Twi Text Collector — Volunteer App
===================================
Collects Twi text generated via Gemini from assigned English news paragraphs.
Pushes to HuggingFace as a structured dataset (not raw text files).
"""

import base64
import hashlib
import json
import os
import re
import sys
import time
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext, messagebox, font as tkfont

HF_OUTPUT_REPO = "ghananlpcommunity/prestine-twi"
HF_INPUT_REPO = "ghananlpcommunity/twi-english-paragraph-dataset_news"
HF_TOKEN_B64 = "aGZfam5YTndBYlR6WmNtYlZ6d1ByUW16RnlJbURNakFMRkdH"  # encoded token
PUSH_EVERY = 10

# Expected character range for 4-part text (~500 words each = ~2000 words total)
# 1 word ≈ 6 chars in Twi, so 2000 words ≈ 12,000 chars
# Allow reasonable variance: 8,000 - 18,000 chars
MIN_CHARS = 8000
MAX_CHARS = 18000


def remove_consecutive_repetitions(text):
    """Remove consecutive repeated sentences (adapted from transcriber.py)"""
    parts = re.split(r'(\s*[.!?\n]+\s*)', text)
    sentences = []
    for i in range(0, len(parts) - 1, 2):
        s = parts[i].strip()
        delim = parts[i+1] if i+1 < len(parts) else " "
        if s:
            sentences.append((s, delim))
    if parts and parts[-1].strip():
        sentences.append((parts[-1].strip(), ""))

    if not sentences:
        return text, 0

    cleaned = [sentences[0]]
    removed = 0

    i = 1
    while i < len(sentences):
        matched = False
        max_block = (len(sentences) - i) // 2
        for k in range(min(max_block, 10), 0, -1):
            block = [s for s, _ in sentences[i:i+k]]
            prev_block = [s for s, _ in cleaned[-k:]] if len(cleaned) >= k else None
            if prev_block and [s.lower() for s in block] == [s.lower() for s in prev_block]:
                removed += k
                i += k
                matched = True
                break
        if not matched:
            cleaned.append(sentences[i])
            i += 1

    result = " ".join(s + d for s, d in cleaned).strip()
    return result, removed


class CollectorApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Twi Text Collector")
        self.root.geometry("900x700")
        
        self.config = None
        self.vol_hash = None
        self.paragraphs = []
        self.current_idx = 0
        self.collected_indices = []
        self.collected_texts = set()  # For duplicate detection
        self.pending_push = []
        self.texts_dir = None
        self.skipped_log = None
        
        if self.load_config():
            self.init_main_ui()
        else:
            self.init_setup_ui()
    
    def load_config(self):
        """Load existing config if present"""
        if not Path("collector_config.json").exists():
            return False
        try:
            with open("collector_config.json") as f:
                self.config = json.load(f)
            self.vol_hash = self.config["vol_hash"]
            self.texts_dir = Path(f"texts_{self.vol_hash}")
            self.skipped_log = self.texts_dir / "skipped.log"
            self.texts_dir.mkdir(exist_ok=True)
            self.load_paragraphs()
            return True
        except:
            return False
    
    def init_setup_ui(self):
        """Setup screen for new volunteers"""
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.pack(expand=True, fill="both")
        
        title = tk.Label(frame, text="Twi Text Collector — Setup", 
                        font=("Arial", 18, "bold"))
        title.pack(pady=(0, 20))
        
        info = tk.Label(frame, text="Paste your volunteer code below:", 
                       font=("Arial", 11))
        info.pack(pady=(0, 10))
        
        self.code_entry = tk.Entry(frame, width=60, font=("Arial", 11))
        self.code_entry.pack(pady=(0, 20))
        
        btn = tk.Button(frame, text="Download & Start →", 
                       command=self.setup_volunteer,
                       font=("Arial", 12, "bold"), 
                       bg="#4CAF50", fg="white",
                       padx=20, pady=10)
        btn.pack()
        
        self.status_label = tk.Label(frame, text="", font=("Arial", 10))
        self.status_label.pack(pady=(20, 0))
    
    def setup_volunteer(self):
        """Decode code and download paragraphs"""
        code = self.code_entry.get().strip()
        if not code:
            messagebox.showerror("Error", "Please enter your code")
            return
        
        try:
            # Decode volunteer code
            padding = "=" * (4 - len(code) % 4)
            decoded = base64.urlsafe_b64decode(code + padding).decode()
            config = json.loads(decoded)
            
            # Validate structure
            if not all(k in config for k in ["repo", "indices"]):
                raise ValueError("Invalid code format")
            
            # Generate volunteer hash
            self.vol_hash = hashlib.sha256(code.encode()).hexdigest()[:8]
            self.texts_dir = Path(f"texts_{self.vol_hash}")
            self.texts_dir.mkdir(exist_ok=True)
            self.skipped_log = self.texts_dir / "skipped.log"
            
            # Save config
            config["vol_hash"] = self.vol_hash
            self.config = config
            with open("collector_config.json", "w") as f:
                json.dump(config, f, indent=2)
            
            self.status_label.config(text="Downloading paragraphs...")
            self.root.update()
            
            # Download dataset
            self.download_paragraphs()
            
            # Switch to main UI
            for widget in self.root.winfo_children():
                widget.destroy()
            self.init_main_ui()
            
        except Exception as e:
            messagebox.showerror("Error", f"Invalid code: {e}")
    
    def download_paragraphs(self):
        """Download assigned paragraphs from HuggingFace"""
        try:
            from huggingface_hub import hf_hub_download
            import pandas as pd
        except ImportError:
            messagebox.showerror("Error", 
                "Install dependencies: pip install huggingface_hub pandas")
            sys.exit(1)
        
        # Download dataset
        file = hf_hub_download(repo_id=HF_INPUT_REPO, 
                              filename="train.parquet",
                              repo_type="dataset")
        df = pd.read_parquet(file)
        
        # Extract assigned paragraphs
        indices = self.config["indices"]
        self.paragraphs = df.iloc[indices]["ENGLISH"].tolist()
        
        # Save locally
        with open(self.texts_dir / "paragraphs.json", "w") as f:
            json.dump(self.paragraphs, f, indent=2)
    
    def load_paragraphs(self):
        """Load paragraphs from local cache"""
        para_file = self.texts_dir / "paragraphs.json"
        if para_file.exists():
            with open(para_file) as f:
                self.paragraphs = json.load(f)
        
        # Load already collected indices and texts
        for f in self.texts_dir.glob("*.txt"):
            idx = int(f.stem.split("_")[0])
            if idx not in self.collected_indices:
                self.collected_indices.append(idx)
                # Load text content for duplicate detection
                try:
                    with open(f, encoding="utf-8") as tf:
                        self.collected_texts.add(tf.read().strip())
                except:
                    pass
        
        # Load skipped
        if self.skipped_log.exists():
            with open(self.skipped_log) as f:
                for line in f:
                    idx = int(line.strip())
                    if idx not in self.collected_indices:
                        self.collected_indices.append(idx)
        
        # Find next uncollected
        for i, _ in enumerate(self.paragraphs):
            if i not in self.collected_indices:
                self.current_idx = i
                break
        else:
            self.current_idx = 0  # All done, will show completion
    
    def init_main_ui(self):
        """Main collection interface"""
        # Toolbar
        toolbar = tk.Frame(self.root, bg="#2c3e50", height=50)
        toolbar.pack(side="top", fill="x")
        
        progress_text = f"{len(self.collected_indices)}/{len(self.paragraphs)}"
        tk.Label(toolbar, text=progress_text, 
                font=("Arial", 11, "bold"),
                bg="#2c3e50", fg="white").pack(side="left", padx=15)
        
        tk.Button(toolbar, text="⬆ Push Now", command=self.manual_push,
                 bg="#3498db", fg="white", relief="flat",
                 font=("Arial", 9, "bold")).pack(side="right", padx=5, pady=8)
        
        # Main area
        main = tk.Frame(self.root, padx=20, pady=20)
        main.pack(expand=True, fill="both")
        
        # Check if all done
        if len(self.collected_indices) >= len(self.paragraphs):
            self.show_completion(main)
            return
        
        # Source paragraph section
        tk.Label(main, text="English Paragraph:", 
                font=("Arial", 10, "bold")).pack(anchor="w")
        
        para_frame = tk.Frame(main, bg="#ecf0f1", relief="solid", bd=1)
        para_frame.pack(fill="both", pady=(5, 15), ipady=10, ipadx=10)
        
        para_text = tk.Text(para_frame, height=6, wrap="word", 
                           font=("Arial", 10), bg="#ecf0f1",
                           relief="flat")
        para_text.pack(fill="both", expand=True)
        para_text.insert("1.0", self.paragraphs[self.current_idx])
        para_text.config(state="disabled")
        
        # Copy buttons
        btn_frame = tk.Frame(main)
        btn_frame.pack(fill="x", pady=(0, 15))
        
        tk.Button(btn_frame, text="✦ Gemini Prompt", 
                 command=self.copy_prompt,
                 bg="#9b59b6", fg="white", font=("Arial", 10, "bold"),
                 relief="flat", padx=15, pady=8).pack(side="left", padx=(0, 10))
        
        tk.Button(btn_frame, text="⎘ Copy Paragraph", 
                 command=self.copy_paragraph,
                 bg="#34495e", fg="white", font=("Arial", 10, "bold"),
                 relief="flat", padx=15, pady=8).pack(side="left")
        
        # Twi text input
        tk.Label(main, text="Paste Twi Text from Gemini:", 
                font=("Arial", 10, "bold")).pack(anchor="w", pady=(0, 5))
        
        self.text_input = scrolledtext.ScrolledText(main, height=15, 
                                                    font=("Arial", 10),
                                                    wrap="word")
        self.text_input.pack(fill="both", expand=True, pady=(0, 15))
        self.text_input.bind("<KeyRelease>", self.validate_text)
        
        # Status and action buttons
        self.status_bar = tk.Label(main, text="", font=("Arial", 9),
                                  fg="#7f8c8d")
        self.status_bar.pack(fill="x", pady=(0, 10))
        
        action_frame = tk.Frame(main)
        action_frame.pack(fill="x")
        
        self.skip_btn = tk.Button(action_frame, text="Skip ⇥", 
                                 command=self.skip_current,
                                 bg="#95a5a6", fg="white",
                                 font=("Arial", 10), relief="flat",
                                 padx=15, pady=8)
        self.skip_btn.pack(side="left")
        
        self.save_btn = tk.Button(action_frame, text="Save & Next →", 
                                 command=self.save_and_next,
                                 bg="#27ae60", fg="white",
                                 font=("Arial", 10, "bold"),
                                 relief="flat", padx=20, pady=8,
                                 state="disabled")
        self.save_btn.pack(side="right")
    
    def show_completion(self, parent):
        """Show completion screen"""
        tk.Label(parent, text="🎉 All Done!", 
                font=("Arial", 20, "bold"),
                fg="#27ae60").pack(pady=(100, 20))
        
        tk.Label(parent, 
                text=f"You've collected {len(self.collected_indices)} texts.\nThank you!",
                font=("Arial", 12)).pack()
        
        # Final push if needed
        if self.pending_push:
            self.push_to_hf()
    
    def copy_prompt(self):
        """Copy Gemini prompt to clipboard"""
        para = self.paragraphs[self.current_idx]
        prompt = f"""Generate Twi text in 4 parts (each ~500 words) - monologue, narrative, dialogue, storyful. 
Use this as inspiration: {para}

Mix English words naturally as done in spoken Twi. Return ONLY the Twi text, no preamble or markdown."""
        
        self.root.clipboard_clear()
        self.root.clipboard_append(prompt)
        self.status_bar.config(text="✓ Prompt copied! Paste in Gemini.", 
                              fg="#27ae60")
    
    def copy_paragraph(self):
        """Copy source paragraph to clipboard"""
        self.root.clipboard_clear()
        self.root.clipboard_append(self.paragraphs[self.current_idx])
        self.status_bar.config(text="✓ Paragraph copied!", fg="#27ae60")
    
    def validate_text(self, event=None):
        """Validate pasted Twi text - check length and repetitions"""
        text = self.text_input.get("1.0", "end-1c").strip()
        
        if not text:
            self.save_btn.config(state="disabled")
            self.status_bar.config(text="", fg="#7f8c8d")
            return
        
        # Remove consecutive repetitions
        cleaned, n_removed = remove_consecutive_repetitions(text)
        char_count = len(cleaned)
        
        # Build status message
        warnings = []
        
        if n_removed > 0:
            warnings.append(f"⚠ {n_removed} repeated sentence(s) will be auto-removed")
        
        if char_count < MIN_CHARS:
            warnings.append(f"Too short: {char_count:,} chars (need ≥{MIN_CHARS:,})")
            self.save_btn.config(state="disabled")
        elif char_count > MAX_CHARS:
            warnings.append(f"Too long: {char_count:,} chars (need ≤{MAX_CHARS:,})")
            self.save_btn.config(state="disabled")
        else:
            if warnings:
                self.status_bar.config(
                    text=" | ".join(warnings) + f" | {char_count:,} chars ✓",
                    fg="#e67e22")
            else:
                self.status_bar.config(
                    text=f"✓ Looks good ({char_count:,} chars)",
                    fg="#27ae60")
            self.save_btn.config(state="normal")
            return
        
        # If we get here, there are blocking errors
        self.status_bar.config(
            text=" | ".join(warnings),
            fg="#e67e22")
    
    def skip_current(self):
        """Skip current paragraph"""
        with open(self.skipped_log, "a") as f:
            f.write(f"{self.current_idx}\n")
        
        self.collected_indices.append(self.current_idx)
        self.next_paragraph()
    
    def save_and_next(self):
        """Save current text and move to next"""
        text = self.text_input.get("1.0", "end-1c").strip()
        
        if not text:
            return
        
        # Remove consecutive repetitions
        cleaned, n_removed = remove_consecutive_repetitions(text)
        
        # Check for duplicates
        if cleaned in self.collected_texts:
            messagebox.showwarning(
                "Duplicate",
                "This text already exists in your collected data.\nNot saved."
            )
            return
        
        # Save locally with cleaned text
        filename = f"{self.current_idx:05d}_{self.vol_hash}.txt"
        filepath = self.texts_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(cleaned)
        
        # Track for push
        self.collected_indices.append(self.current_idx)
        self.collected_texts.add(cleaned)
        self.pending_push.append({
            "index": self.current_idx,
            "text": cleaned,
            "source_paragraph": self.paragraphs[self.current_idx],
            "filename": filename,
            "repetitions_removed": n_removed
        })
        
        # Auto-push every N texts
        if len(self.pending_push) >= PUSH_EVERY:
            self.push_to_hf()
        
        self.next_paragraph()
    
    def next_paragraph(self):
        """Load next uncollected paragraph"""
        # Find next
        for i, _ in enumerate(self.paragraphs):
            if i not in self.collected_indices:
                self.current_idx = i
                break
        else:
            # All done
            if self.pending_push:
                self.push_to_hf()
            
            for widget in self.root.winfo_children():
                widget.destroy()
            main = tk.Frame(self.root, padx=20, pady=20)
            main.pack(expand=True, fill="both")
            self.show_completion(main)
            return
        
        # Rebuild UI
        for widget in self.root.winfo_children():
            widget.destroy()
        self.init_main_ui()
    
    def manual_push(self):
        """Manual push trigger"""
        if not self.pending_push:
            messagebox.showinfo("Info", "Nothing to push yet")
            return
        self.push_to_hf()
    
    def push_to_hf(self):
        """Push collected texts to HuggingFace as structured dataset"""
        if not self.pending_push:
            return
        
        try:
            from huggingface_hub import HfApi
            import pandas as pd
        except ImportError:
            messagebox.showerror("Error", 
                "Install: pip install huggingface_hub pandas")
            return
        
        token = base64.b64decode(HF_TOKEN_B64).decode()
        api = HfApi(token=token)
        
        try:
            # Ensure repo exists
            api.create_repo(repo_id=HF_OUTPUT_REPO, 
                           repo_type="dataset", 
                           exist_ok=True)
            
            # Load existing dataset if it exists
            try:
                from huggingface_hub import hf_hub_download
                existing_file = hf_hub_download(
                    repo_id=HF_OUTPUT_REPO,
                    filename="data.parquet",
                    repo_type="dataset",
                    token=token
                )
                existing_df = pd.read_parquet(existing_file)
            except:
                existing_df = pd.DataFrame(columns=[
                    "id", "volunteer_hash", "source_paragraph", 
                    "twi_text", "char_count", "repetitions_removed", "timestamp"
                ])
            
            # Prepare new rows
            new_rows = []
            for item in self.pending_push:
                new_rows.append({
                    "id": f"{item['index']:05d}_{self.vol_hash}",
                    "volunteer_hash": self.vol_hash,
                    "source_paragraph": item["source_paragraph"],
                    "twi_text": item["text"],
                    "char_count": len(item["text"]),
                    "repetitions_removed": item["repetitions_removed"],
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
                })
            
            # Append new data
            new_df = pd.DataFrame(new_rows)
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            
            # Save as parquet
            temp_file = self.texts_dir / "temp_data.parquet"
            combined_df.to_parquet(temp_file, index=False)
            
            # Upload to HF
            api.upload_file(
                path_or_fileobj=str(temp_file),
                path_in_repo="data.parquet",
                repo_id=HF_OUTPUT_REPO,
                repo_type="dataset",
                commit_message=f"Volunteer {self.vol_hash}: +{len(new_rows)} text(s)"
            )
            
            # Clean up temp file
            temp_file.unlink()
            
            count = len(self.pending_push)
            self.pending_push = []
            
            if hasattr(self, 'status_bar'):
                self.status_bar.config(
                    text=f"✓ Pushed {count} text(s) to HuggingFace",
                    fg="#27ae60")
            
        except Exception as e:
            # Keep in pending for retry
            if hasattr(self, 'status_bar'):
                self.status_bar.config(
                    text=f"⚠ Push failed: {e}. Will retry.",
                    fg="#e74c3c")
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = CollectorApp()
    app.run()
