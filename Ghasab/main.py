import flet as ft
import os
import threading
import yt_dlp
import traceback

def main(page: ft.Page):
    # إعدادات الصفحة (ستعمل الآن لأننا سنحدث النسخة)
    page.title = "Ghasab PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.scroll = ft.ScrollMode.AUTO
    page.padding = 20
    page.vertical_alignment = ft.MainAxisAlignment.START

    # --- المتغيرات والدوال المساعدة ---
    state = {
        "path": "/storage/emulated/0/Download/GhasabApp",
        "selected_cookie": None
    }

    # دالة البحث التلقائي عن الكوكيز
    def find_cookies_scan():
        candidates = ["/storage/emulated/0/Download", "/storage/emulated/0/Downloads"]
        found = []
        for p in candidates:
            try:
                if os.path.exists(p):
                    for f in os.listdir(p):
                        if f.endswith((".txt", ".json")) and "cookie" in f.lower():
                            found.append(ft.dropdown.Option(key=os.path.join(p, f), text=f))
            except: pass
        return found

    # --- عناصر الواجهة ---
    
    header = ft.Text("تحميل غصب PRO", size=28, weight="bold", color=ft.Colors.BLUE_400, text_align="center")
    
    url_input = ft.TextField(
        label="رابط الفيديو", 
        hint_text="ألصق الرابط هنا...", 
        prefix_icon=ft.Icons.LINK,
        text_align="right"
    )

    # قائمة الكوكيز
    cookies_dropdown = ft.Dropdown(
        label="الكوكيز المكتشفة",
        options=find_cookies_scan(),
        icon=ft.Icons.COOKIE
    )

    # زر تحديث القائمة
    def refresh_cookies(e):
        cookies_dropdown.options = find_cookies_scan()
        page.snack_bar = ft.SnackBar(ft.Text("تم تحديث القائمة"))
        page.snack_bar.open = True
        page.update()

    refresh_btn = ft.IconButton(ft.Icons.REFRESH, on_click=refresh_cookies)

    # مُنتقي الملفات (FilePicker) - سيعمل الآن بعد التحديث!
    file_picker = ft.FilePicker()
    
    def on_file_picked(e: ft.FilePickerResultEvent):
        if e.files:
            state["selected_cookie"] = e.files[0].path
            manual_cookie_lbl.value = f"تم تحديد: {e.files[0].name}"
            manual_cookie_lbl.color = ft.Colors.GREEN
            cookies_dropdown.value = None # إلغاء القائمة
            page.update()
            
    file_picker.on_result = on_file_picked
    page.overlay.append(file_picker)

    manual_btn = ft.ElevatedButton("اختيار ملف يدوياً", icon=ft.Icons.FOLDER_OPEN, on_click=lambda _: file_picker.pick_files())
    manual_cookie_lbl = ft.Text("", size=12)

    # سجل العمليات
    log_col = ft.Column()
    def log(msg, color="white"):
        log_col.controls.append(ft.Text(f"> {msg}", color=color, font_family="monospace", size=12))
        page.update()

    # منطق التحميل
    def start_download(e):
        if not url_input.value:
            log("❌ الرجاء وضع رابط", "red")
            return

        log("🚀 جاري البدء...", "cyan")
        
        def dl_thread():
            try:
                # إنشاء المجلد
                try: os.makedirs(state["path"], exist_ok=True)
                except: pass

                opts = {
                    'outtmpl': f'{state["path"]}/%(title)s.%(ext)s',
                    'ignoreerrors': True,
                    'nocheckcertificate': True
                }

                # تحديد الكوكيز (اليدوي أولاً ثم القائمة)
                cookie = state["selected_cookie"] or cookies_dropdown.value
                if cookie:
                    opts['cookiefile'] = cookie
                    log(f"🍪 باستخدام كوكيز: {os.path.basename(cookie)}", "green")
                
                with yt_dlp.YoutubeDL(opts) as ydl:
                    log(f"جاري تحميل: {url_input.value} ...", "yellow")
                    ydl.download([url_input.value])
                    log("✅ تم التحميل بنجاح!", "green")
            
            except Exception as ex:
                log(f"❌ خطأ: {str(ex)}", "red")
        
        threading.Thread(target=dl_thread, daemon=True).start()

    dl_btn = ft.FilledButton("تحميل الفيديو", icon=ft.Icons.DOWNLOAD, on_click=start_download, width=200, height=50)

    # التجميع النهائي
    page.add(
        ft.SafeArea(
            ft.Column([
                header,
                ft.Divider(height=20, color="transparent"),
                url_input,
                ft.Row([cookies_dropdown, refresh_btn]),
                ft.Row([manual_btn, manual_cookie_lbl]),
                ft.Divider(),
                ft.Container(dl_btn, alignment=ft.alignment.center),
                ft.Divider(height=20, color="transparent"),
                ft.Container(
                    content=ft.Column([ft.Text("سجل النظام:", weight="bold"), log_col], scroll=ft.ScrollMode.AUTO),
                    bgcolor=ft.Colors.BLACK54,
                    padding=10,
                    border_radius=10,
                    height=200
                )
            ])
        )
    )

ft.app(target=main)
