"""
Video Pleyer - Python Tkinter + OpenCV + pygame
Ishlatish:
    pip install opencv-python pillow pygame
    python video_player.py
"""

import tkinter as tk
from tkinter import filedialog, ttk
import threading
import time
import os

try:
    import cv2
    from PIL import Image, ImageTk
    import pygame
    DEPS_OK = True
except ImportError:
    DEPS_OK = False


class VideoPleyer:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 Video Pleyer")
        self.root.geometry("900x620")
        self.root.configure(bg="#1a1a2e")
        self.root.resizable(True, True)

        # Holat
        self.cap = None
        self.ijro_etilmoqda = False
        self.toxtатилди = False
        self.joriy_kadr = 0
        self.jami_kadrlar = 0
        self.fps = 30
        self.fayl_yoli = None
        self.ovoz_darajasi = 0.8
        self.tezlik = 1.0
        self.toʻliq_ekran = False
        self._thread = None

        # pygame ovoz
        if DEPS_OK:
            pygame.mixer.init()

        self._interfeys_yasash()
        self.root.protocol("WM_DELETE_WINDOW", self._yopish)
        self.root.bind("<space>", lambda e: self.ijro_toʻxtat())
        self.root.bind("<Left>", lambda e: self._oldinga_orqaga(-5))
        self.root.bind("<Right>", lambda e: self._oldinga_orqaga(5))
        self.root.bind("<Up>", lambda e: self._ovoz_sozla(0.1))
        self.root.bind("<Down>", lambda e: self._ovoz_sozla(-0.1))
        self.root.bind("f", lambda e: self._toʻliq_ekran())
        self.root.bind("<Escape>", lambda e: self._toʻliq_ekrandan_chiq())

    def _interfeys_yasash(self):
        # Sarlavha paneli
        sarlavha = tk.Frame(self.root, bg="#16213e", height=45)
        sarlavha.pack(fill=tk.X)
        sarlavha.pack_propagate(False)

        tk.Label(sarlavha, text="  🎬  VIDEO PLEYER",
                 bg="#16213e", fg="#e94560",
                 font=("Helvetica", 13, "bold")).pack(side=tk.LEFT, padx=10, pady=8)

        self.fayl_label = tk.Label(sarlavha, text="Fayl tanlanmagan",
                                   bg="#16213e", fg="#aaaaaa",
                                   font=("Helvetica", 10))
        self.fayl_label.pack(side=tk.LEFT, padx=20)

        # Video ekran
        self.canvas = tk.Canvas(self.root, bg="#0a0a0a",
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=10, pady=(8, 0))

        # Boshlash xabari
        self._xabar_korsат("📂  Fayl oching yoki pastdagi tugmani bosing")

        # Progress bar
        progress_frame = tk.Frame(self.root, bg="#1a1a2e")
        progress_frame.pack(fill=tk.X, padx=10, pady=(6, 0))

        self.vaqt_label = tk.Label(progress_frame, text="0:00 / 0:00",
                                   bg="#1a1a2e", fg="#888888",
                                   font=("Courier", 9))
        self.vaqt_label.pack(side=tk.LEFT)

        self.progress_var = tk.DoubleVar()
        self.progress = ttk.Scale(progress_frame, from_=0, to=100,
                                  variable=self.progress_var,
                                  orient=tk.HORIZONTAL,
                                  command=self._progress_oʻzgardi)
        self.progress.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=10)

        # Boshqaruv paneli
        kontrol = tk.Frame(self.root, bg="#16213e", height=70)
        kontrol.pack(fill=tk.X, pady=(6, 0))
        kontrol.pack_propagate(False)

        # Chap — asosiy tugmalar
        chap = tk.Frame(kontrol, bg="#16213e")
        chap.pack(side=tk.LEFT, padx=16, pady=10)

        self.btn_fayl = self._tugma(chap, "📂 Fayl", self._fayl_och, "#0f3460")
        self.btn_fayl.pack(side=tk.LEFT, padx=4)

        self.btn_orqaga = self._tugma(chap, "⏮ -5s", lambda: self._oldinga_orqaga(-5), "#0f3460")
        self.btn_orqaga.pack(side=tk.LEFT, padx=4)

        self.btn_ijro = self._tugma(chap, "▶  Ijro", self.ijro_toʻxtat, "#e94560", "#fff")
        self.btn_ijro.pack(side=tk.LEFT, padx=4)

        self.btn_oldinga = self._tugma(chap, "+5s ⏭", lambda: self._oldinga_orqaga(5), "#0f3460")
        self.btn_oldinga.pack(side=tk.LEFT, padx=4)

        self.btn_toʻxtat = self._tugma(chap, "⏹ Stop", self._stop, "#0f3460")
        self.btn_toʻxtat.pack(side=tk.LEFT, padx=4)

        # Oʻng — ovoz va tezlik
        oʻng = tk.Frame(kontrol, bg="#16213e")
        oʻng.pack(side=tk.RIGHT, padx=16, pady=10)

        tk.Label(oʻng, text="🔊", bg="#16213e", fg="#aaa",
                 font=("Helvetica", 12)).pack(side=tk.LEFT)
        self.ovoz_var = tk.DoubleVar(value=80)
        ovoz_slider = ttk.Scale(oʻng, from_=0, to=100,
                                variable=self.ovoz_var,
                                orient=tk.HORIZONTAL, length=90,
                                command=self._ovoz_oʻzgardi)
        ovoz_slider.pack(side=tk.LEFT, padx=6)

        tk.Label(oʻng, text="Tezlik:", bg="#16213e", fg="#aaa",
                 font=("Helvetica", 9)).pack(side=tk.LEFT, padx=(12, 4))
        self.tezlik_var = tk.StringVar(value="1.0×")
        tezlik_menu = tk.OptionMenu(oʻng, self.tezlik_var,
                                    "0.5×", "0.75×", "1.0×", "1.25×", "1.5×", "2.0×",
                                    command=self._tezlik_oʻzgardi)
        tezlik_menu.config(bg="#0f3460", fg="white", activebackground="#e94560",
                           font=("Helvetica", 9), relief="flat", bd=0, width=5)
        tezlik_menu["menu"].config(bg="#16213e", fg="white")
        tezlik_menu.pack(side=tk.LEFT)

        btn_fs = self._tugma(oʻng, "⛶", self._toʻliq_ekran, "#0f3460")
        btn_fs.pack(side=tk.LEFT, padx=(10, 0))

        # Pastki status
        self.status = tk.Label(self.root, text="Tayyor  |  [Space] Ijro/Toʻxtat  |  [←→] 5s  |  [F] Toʻliq ekran",
                               bg="#1a1a2e", fg="#555555",
                               font=("Helvetica", 8))
        self.status.pack(pady=(2, 6))

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Horizontal.TScale",
                        background="#16213e",
                        troughcolor="#2a2a4a",
                        sliderlength=14,
                        sliderrelief="flat")

    def _tugma(self, parent, matn, komanda, rang="#0f3460", fg_rang="#dddddd"):
        b = tk.Button(parent, text=matn, command=komanda,
                      bg=rang, fg=fg_rang,
                      font=("Helvetica", 9, "bold"),
                      relief="flat", bd=0, padx=10, pady=5,
                      cursor="hand2",
                      activebackground="#e94560", activeforeground="white")
        b.bind("<Enter>", lambda e: b.config(bg="#e94560", fg="white"))
        b.bind("<Leave>", lambda e: b.config(bg=rang, fg=fg_rang))
        return b

    def _xabar_korsат(self, matn):
        w = self.canvas.winfo_width() or 880
        h = self.canvas.winfo_height() or 450
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, w, h, fill="#0a0a0a", outline="")
        self.canvas.create_text(w // 2, h // 2, text=matn,
                                fill="#444466", font=("Helvetica", 14))

    def _fayl_och(self):
        yol = filedialog.askopenfilename(
            title="Video tanlang",
            filetypes=[("Video fayllar", "*.mp4 *.avi *.mov *.mkv *.wmv *.flv *.webm"),
                       ("Barcha fayllar", "*.*")])
        if not yol:
            return
        self._video_yuklash(yol)

    def _video_yuklash(self, yol):
        self._stop()
        if self.cap:
            self.cap.release()

        self.cap = cv2.VideoCapture(yol)
        if not self.cap.isOpened():
            self._xabar_korsат("❌  Fayl ochilmadi")
            return

        self.fayl_yoli = yol
        self.jami_kadrlar = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.fps = self.cap.get(cv2.CAP_PROP_FPS) or 30
        self.joriy_kadr = 0

        nom = os.path.basename(yol)
        self.fayl_label.config(text=nom[:55])
        self.root.title(f"🎬 {nom}")
        self.status.config(text=f"Yuklandi: {nom}")

        # Ovoz
        try:
            pygame.mixer.music.load(yol)
            pygame.mixer.music.set_volume(self.ovoz_var.get() / 100)
        except Exception:
            pass

        # Birinchi kadrni koʻrsat
        ret, kadr = self.cap.read()
        if ret:
            self._kadrni_korsат(kadr)
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)

    def _kadrni_korsат(self, kadr):
        w = self.canvas.winfo_width() or 880
        h = self.canvas.winfo_height() or 450
        kadr_rgb = cv2.cvtColor(kadr, cv2.COLOR_BGR2RGB)
        rasm = Image.fromarray(kadr_rgb)
        rasm.thumbnail((w, h), Image.LANCZOS)
        photo = ImageTk.PhotoImage(rasm)
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 0, w, h, fill="#0a0a0a", outline="")
        self.canvas.create_image(w // 2, h // 2, image=photo, anchor=tk.CENTER)
        self.canvas._photo = photo  # yo'qolmaslik uchun

    def _ijro_qilish(self):
        try:
            pygame.mixer.music.play(start=self.joriy_kadr / self.fps)
        except Exception:
            pass

        delay = 1.0 / (self.fps * self.tezlik)
        while self.ijro_etilmoqda and self.cap:
            ret, kadr = self.cap.read()
            if not ret:
                self.ijro_etilmoqda = False
                break
            self.joriy_kadr = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
            self.canvas.after(0, self._kadrni_korsат, kadr)
            self._progress_yangilash()
            time.sleep(delay)

        if not self.ijro_etilmoqda:
            try:
                pygame.mixer.music.pause()
            except Exception:
                pass

    def ijro_toʻxtat(self):
        if not self.cap:
            self._fayl_och()
            return
        if self.ijro_etilmoqda:
            self.ijro_etilmoqda = False
            self.btn_ijro.config(text="▶  Ijro")
        else:
            self.ijro_etilmoqda = True
            self.btn_ijro.config(text="⏸  Toʻxtat")
            self._thread = threading.Thread(target=self._ijro_qilish, daemon=True)
            self._thread.start()

    def _stop(self):
        self.ijro_etilmoqda = False
        self.btn_ijro.config(text="▶  Ijro")
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
            self.joriy_kadr = 0
        self.progress_var.set(0)
        self.vaqt_label.config(text="0:00 / 0:00")
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self._xabar_korsат("⏹  Toʻxtatildi")

    def _oldinga_orqaga(self, soniya):
        if not self.cap:
            return
        yangi = self.joriy_kadr + int(soniya * self.fps)
        yangi = max(0, min(yangi, self.jami_kadrlar - 1))
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, yangi)
        self.joriy_kadr = yangi
        try:
            pygame.mixer.music.play(start=yangi / self.fps)
            if not self.ijro_etilmoqda:
                pygame.mixer.music.pause()
        except Exception:
            pass

    def _progress_yangilash(self):
        if self.jami_kadrlar > 0:
            pct = (self.joriy_kadr / self.jami_kadrlar) * 100
            self.progress_var.set(pct)
            joriy_s = int(self.joriy_kadr / self.fps)
            jami_s = int(self.jami_kadrlar / self.fps)
            vaqt = f"{joriy_s // 60}:{joriy_s % 60:02d} / {jami_s // 60}:{jami_s % 60:02d}"
            self.vaqt_label.config(text=vaqt)

    def _progress_oʻzgardi(self, val):
        if self.cap and self.jami_kadrlar > 0:
            yangi = int((float(val) / 100) * self.jami_kadrlar)
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, yangi)
            self.joriy_kadr = yangi

    def _ovoz_oʻzgardi(self, val):
        try:
            pygame.mixer.music.set_volume(float(val) / 100)
        except Exception:
            pass

    def _ovoz_sozla(self, delta):
        yangi = max(0, min(100, self.ovoz_var.get() + delta * 100))
        self.ovoz_var.set(yangi)
        self._ovoz_oʻzgardi(yangi)

    def _tezlik_oʻzgardi(self, val):
        self.tezlik = float(val.replace("×", ""))

    def _toʻliq_ekran(self):
        self.root.attributes("-fullscreen", True)

    def _toʻliq_ekrandan_chiq(self):
        self.root.attributes("-fullscreen", False)

    def _yopish(self):
        self.ijro_etilmoqda = False
        if self.cap:
            self.cap.release()
        try:
            pygame.mixer.quit()
        except Exception:
            pass
        self.root.destroy()


def main():
    if not DEPS_OK:
        import tkinter.messagebox as mb
        root = tk.Tk()
        root.withdraw()
        mb.showerror("Kutubxona topilmadi",
                     "Quyidagi kutubxonalarni o'rnating:\n\n"
                     "pip install opencv-python pillow pygame\n\n"
                     "So'ng dasturni qayta ishga tushiring.")
        root.destroy()
        return

    root = tk.Tk()
    app = VideoPleyer(root)
    root.mainloop()


if __name__ == "__main__":
    main()
