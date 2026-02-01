import tkinter as tk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
import cv2
import os

from image_processor import ImageProcessor
from image_history import ImageHistory


class ImageEditorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("HIT137 Image Editor (Tkinter + OpenCV)")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)

        self.image = None
        self.original = None
        self.file_path = None
        self.history = ImageHistory()

        self.create_menu()
        self.build_layout()

    # ================= MENU =================

    def create_menu(self):
        menubar = tk.Menu(self.root)

        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open", command=self.open_image)
        file_menu.add_command(label="Save", command=self.save_image)
        file_menu.add_command(label="Save As", command=self.save_image_as)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="Undo", command=self.undo)
        edit_menu.add_command(label="Redo", command=self.redo)

        menubar.add_cascade(label="File", menu=file_menu)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        self.root.config(menu=menubar)

    # ================= LAYOUT =================

    def build_layout(self):
        container = tk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)

        # -------- Scrollable Left Panel --------
        left_container = tk.Frame(container)
        left_container.pack(side=tk.LEFT, fill=tk.Y)

        canvas = tk.Canvas(left_container, width=260)
        scrollbar = tk.Scrollbar(left_container, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.Y)

        self.controls = tk.Frame(canvas, padx=10, pady=10)
        canvas.create_window((0, 0), window=self.controls, anchor="nw")

        def on_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        self.controls.bind("<Configure>", on_configure)

        def on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", on_mousewheel)
        # --------------------------------------

        # -------- Image Display Area --------
        right = tk.Frame(container, padx=10, pady=10)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)

        self.canvas_img = tk.Label(right, bg="black", bd=2, relief=tk.SUNKEN)
        self.canvas_img.pack(fill=tk.BOTH, expand=True)

        # -------- Status Bar --------
        self.status = tk.Label(self.root, text="No image loaded", bd=1,
                               relief=tk.SUNKEN, anchor=tk.W)
        self.status.pack(side=tk.BOTTOM, fill=tk.X)

        # ================= CONTROLS =================

        tk.Label(self.controls, text="Filters & Effects",
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 10))

        tk.Button(self.controls, text="Grayscale", width=20,
                  command=self.grayscale).pack(pady=3)

        tk.Button(self.controls, text="Edge Detection", width=20,
                  command=self.edge).pack(pady=3)

        tk.Label(self.controls, text="Rotate",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 3))

        tk.Button(self.controls, text="Rotate 90°", width=20,
                  command=lambda: self.rotate(90)).pack(pady=2)
        tk.Button(self.controls, text="Rotate 180°", width=20,
                  command=lambda: self.rotate(180)).pack(pady=2)
        tk.Button(self.controls, text="Rotate 270°", width=20,
                  command=lambda: self.rotate(270)).pack(pady=2)

        tk.Label(self.controls, text="Flip",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 3))

        tk.Button(self.controls, text="Flip Horizontal", width=20,
                  command=lambda: self.flip("horizontal")).pack(pady=2)
        tk.Button(self.controls, text="Flip Vertical", width=20,
                  command=lambda: self.flip("vertical")).pack(pady=2)

        tk.Label(self.controls, text="Adjustments",
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(12, 3))

        self.blur_slider = tk.Scale(self.controls, from_=0, to=10,
                                    orient=tk.HORIZONTAL, label="Blur Intensity")
        self.blur_slider.pack(fill="x")
        tk.Button(self.controls, text="Apply Blur", width=20,
                  command=self.apply_blur).pack(pady=4)

        self.bright_slider = tk.Scale(self.controls, from_=-100, to=100,
                                      orient=tk.HORIZONTAL, label="Brightness")
        self.bright_slider.pack(fill="x")
        tk.Button(self.controls, text="Apply Brightness", width=20,
                  command=self.apply_brightness).pack(pady=4)

        self.contrast_slider = tk.Scale(self.controls, from_=5, to=30,
                                        orient=tk.HORIZONTAL, label="Contrast (x0.1)")
        self.contrast_slider.set(10)
        self.contrast_slider.pack(fill="x")
        tk.Button(self.controls, text="Apply Contrast", width=20,
                  command=self.apply_contrast).pack(pady=4)

        self.resize_slider = tk.Scale(self.controls, from_=50, to=200,
                                      orient=tk.HORIZONTAL, label="Resize (%)")
        self.resize_slider.set(100)
        self.resize_slider.pack(fill="x")
        tk.Button(self.controls, text="Apply Resize", width=20,
                  command=self.apply_resize).pack(pady=4)

        tk.Button(self.controls, text="Reset to Original", width=20,
                  command=self.reset_original).pack(pady=(15, 5))

    # ================= FILE OPS =================

    def open_image(self):
        path = filedialog.askopenfilename(
            filetypes=[("Images", "*.jpg *.jpeg *.png *.bmp")]
        )
        if not path:
            return

        img = cv2.imread(path)
        if img is None:
            messagebox.showerror("Error", "Could not open image.")
            return

        self.file_path = path
        self.original = img.copy()
        self.image = img.copy()
        self.history = ImageHistory()
        self.history.save(self.image)

        self.display()
        self.update_status()

    def save_image(self):
        if self.image is None:
            messagebox.showerror("Error", "No image to save.")
            return

        if not self.file_path:
            self.save_image_as()
            return

        cv2.imwrite(self.file_path, self.ensure_bgr(self.image))
        messagebox.showinfo("Saved", "Image saved successfully.")

    def save_image_as(self):
        if self.image is None:
            messagebox.showerror("Error", "No image to save.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".png",
            filetypes=[("PNG", "*.png"), ("JPG", "*.jpg"), ("BMP", "*.bmp")]
        )
        if not path:
            return

        cv2.imwrite(path, self.ensure_bgr(self.image))
        self.file_path = path
        messagebox.showinfo("Saved", "Image saved successfully.")
        self.update_status()

    # ================= DISPLAY =================

    def ensure_bgr(self, img):
        if img.ndim == 2:
            return cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    def display(self):
        if self.image is None:
            return

        img = self.image
        if img.ndim == 2:
            rgb = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        pil_img = Image.fromarray(rgb)

        max_w = self.root.winfo_width() - 300
        max_h = self.root.winfo_height() - 150
        pil_img.thumbnail((max_w, max_h))

        tk_img = ImageTk.PhotoImage(pil_img)
        self.canvas_img.config(image=tk_img)
        self.canvas_img.image = tk_img

    def update_status(self):
        if self.image is None:
            self.status.config(text="No image loaded")
            return

        h, w = self.image.shape[:2]
        name = os.path.basename(self.file_path) if self.file_path else "Untitled"
        mode = "Grayscale" if self.image.ndim == 2 else "Color"
        self.status.config(text=f"{name} | {w}x{h} | {mode}")

    # ================= HISTORY =================

    def apply(self, new_img):
        self.history.save(self.image)
        self.image = new_img
        self.display()
        self.update_status()

    def undo(self):
        if self.image is None:
            return
        self.image = self.history.undo(self.image)
        self.display()
        self.update_status()

    def redo(self):
        if self.image is None:
            return
        self.image = self.history.redo(self.image)
        self.display()
        self.update_status()

    # ================= EFFECTS =================

    def grayscale(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.grayscale())

    def edge(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.edge_detect())

    def apply_blur(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.blur(self.blur_slider.get()))

    def apply_brightness(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.adjust_brightness(self.bright_slider.get()))

    def apply_contrast(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.adjust_contrast(self.contrast_slider.get() / 10))

    def rotate(self, angle):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.rotate(angle))

    def flip(self, mode):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.flip(mode))

    def apply_resize(self):
        proc = ImageProcessor(self.ensure_bgr(self.image))
        self.apply(proc.resize(self.resize_slider.get() / 100))

    def reset_original(self):
        if self.original is None:
            return
        if messagebox.askyesno("Confirm", "Reset to original image?"):
            self.history.save(self.image)
            self.image = self.original.copy()
            self.display()
            self.update_status()


if __name__ == "__main__":
    root = tk.Tk()
    app = ImageEditorApp(root)
    root.mainloop()
