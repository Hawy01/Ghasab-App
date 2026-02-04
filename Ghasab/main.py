import flet as ft
import os
import threading
import yt_dlp
import traceback
import platform
from android_notify import Notification

# البحث عن الكوكيز في التنزيلات
def find_cookie_files():
    paths = ["/storage/emulated/0/Download", "/sdcard/Download"]
    cookie_files = []
    for p in paths:
        try:
            if os.path.exists(p):
                for f in os.listdir(p):
                    if "cookie" in f.lower() and f.endswith((".txt", ".json")):
                        cookie_files.append(os.path.join(p, f))
        except: pass
    return sorted(list(set(cookie_files)))

def main(page: ft.Page):
    page.title = "تحميل غصب PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 20

    # دالة إرسال الإشعارات (متوافقة مع أندرويد 10)
    def notify(title, msg, progress=None):
        try:
            n = Notification(title=title, message=msg, identifier="ghasab_channel")
            if progress is not None:
                n.send(progress=int(float(progress)))
            else:
                n.send()
        except: pass

    # طلب الصلاحيات (مع استثناء أندرويد 10 من إذن الإشعارات)
    if hasattr(page, "request_permission"):
        page.request_permission(ft.PermissionType.STORAGE)
        # لا نطلب POST_NOTIFICATIONS لأن أندرويد 10 لا يحتاجه

    save_dir = "/storage/emulated/0/Download/GhasabApp"
    
    url_input = ft.TextField(label="روابط الفيديو", multiline=True, prefix_icon=ft.icons.LINK)
    path_input = ft.TextField(label="مسار الحفظ", value=save_dir, expand=True, prefix_icon=ft.icons.FOLDER)
    
    cookies_list = find_cookie_files()
    cookies_dropdown = ft.Dropdown(
        label="ملف الكوكيز (اختياري)",
        prefix_icon=ft.icons.COOKIE,
        expand=True,
        options=[ft.dropdown.Option(key=f, text=os.path.basename(f)) for f in cookies_list]
    )
    
    progress_bar = ft.ProgressBar(value=0, expand=True, color=ft.colors.BLUE_400)
    progress_text = ft.Text("التقدم: 0%", size=12)
    log_list = ft.ListView(expand=True, spacing=5, height=180)

    def append_log(msg, is_error=False):
        log_list.controls.append(ft.Text(msg, size=11, color=ft.colors.RED_400 if is_error else ft.colors.GREY_300))
        page.update()

    def update_progress(d):
        if d['status'] == 'downloading':
            try:
                p_raw = d.get('_percent_str', '0%').replace('%','').strip()
                progress_bar.value = float(p_raw) / 100
                progress_text.value = f"جاري التحميل: {p_raw}%"
                notify("جاري التحميل بأعلى جودة", f"التقدم: {p_raw}%", progress=p_raw)
                page.update()
            except: pass

    def start_download(e):
        urls = [u.strip() for u in url_input.value.split('\n') if u.strip()]
        if not urls: return
        
        mode = e.control.data 
        selected_cookie = cookies_dropdown.value
        
        def dl_thread():
            try:
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                
                notify("بدأ التحميل", "جاري جلب أفضل جودة متاحة...")
                
                for url in urls:
                    append_log(f"🔍 فحص: {url}")
                    opts = {
                        'outtmpl': f"{save_dir}/%(title)s.%(ext)s",
                        'progress_hooks': [update_progress],
                        'cookiefile': selected_cookie,
                        # 'best' تجلب أعلى جودة (حتى 1080p) في ملف واحد لتجنب خطأ الدمج
                        'format': 'best' if mode == 'video' else 'bestaudio/best', 
                    }
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                
                append_log("✅ اكتمل التحميل بنجاح")
                notify("تم التحميل ✅", "الملفات موجودة في مجلد GhasabApp")
            except Exception as ex:
                append_log(f"❌ خطأ: {str(ex)[:100]}", True)
                notify("خطأ في التحميل ❌", str(ex)[:30])
            page.update()

        threading.Thread(target=dl_thread, daemon=True).start()

    page.add(
        ft.Column([
            ft.Text("تحميل غصب PRO", size=28, weight="bold", color=ft.colors.BLUE_400),
            url_input,
            ft.Row([path_input]),
            ft.Row([cookies_dropdown]),
            ft.Row([
                ft.ElevatedButton("تحميل فيديو", icon=ft.icons.VIDEO_LIBRARY, data="video", on_click=start_download, expand=True),
                ft.ElevatedButton("صوت فقط", icon=ft.icons.AUDIO_FILE, data="audio", on_click=start_download, expand=True, bgcolor=ft.colors.GREEN_800),
            ]),
            ft.Divider(height=10),
            progress_text, progress_bar,
            ft.Container(content=log_list, bgcolor=ft.colors.BLACK_26, padding=10, border_radius=12)
        ], horizontal_alignment="center")
    )

if __name__ == "__main__":
    ft.app(target=main)
