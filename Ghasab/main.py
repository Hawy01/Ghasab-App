import flet as ft
import os
import threading
import yt_dlp
import traceback

def main(page: ft.Page):
    page.title = "تحميل غصب PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # حاوية للتشخيص (مخفية)
    diag_container = ft.Column(visible=False)
    page.add(diag_container)

    # مسار الحفظ الافتراضي (تأكد من وجود المجلد)
    save_dir = "/storage/emulated/0/Download/GhasabApp"
    
    # --- عناصر الواجهة ---
    url_input = ft.TextField(
        label="روابط الفيديو", 
        multiline=True, 
        border_radius=12, 
        hint_text="ضع الرابط هنا...",
        prefix_icon=ft.icons.LINK
    )
    
    path_input = ft.TextField(
        label="مسار الحفظ", 
        value=save_dir, 
        expand=True,
        prefix_icon=ft.icons.FOLDER_OPEN
    )
    
    progress_bar = ft.ProgressBar(value=0, expand=True, color=ft.colors.BLUE_400)
    progress_text = ft.Text("التقدم: 0%", size=12)
    log_list = ft.ListView(expand=True, spacing=5, height=200)

    def append_log(msg, is_error=False):
        log_list.controls.append(
            ft.Text(msg, size=11, color=ft.colors.RED_400 if is_error else ft.colors.GREY_300)
        )
        page.update()

    def update_progress(d):
        if d['status'] == 'downloading':
            try:
                p_raw = d.get('_percent_str', '0%').replace('%','').strip()
                progress_bar.value = float(p_raw) / 100
                progress_text.value = f"التقدم: {p_raw}%"
                page.update()
            except: pass

    def start_download(e):
        urls = [u.strip() for u in url_input.value.split('\n') if u.strip()]
        if not urls:
            append_log("❌ يرجى وضع رابط أولاً", True)
            return
        
        mode = e.control.data 
        
        def dl_thread():
            try:
                # إنشاء المجلد إذا لم يكن موجوداً
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir, exist_ok=True)
                
                for url in urls:
                    append_log(f"🔍 جاري فحص الرابط...")
                    
                    # إعدادات التحميل (تعديل 'format' لتجنب الحاجة لـ FFmpeg)
                    opts = {
                        'outtmpl': f"{save_dir}/%(title)s.%(ext)s",
                        'progress_hooks': [update_progress],
                        # اختيار 'best' مباشرة يحمل ملف واحد مدمج جاهز ولا يحتاج FFmpeg
                        'format': 'best' if mode == 'video' else 'bestaudio/best',
                    }
                    
                    with yt_dlp.YoutubeDL(opts) as ydl:
                        ydl.download([url])
                    
                    append_log(f"✅ تم تحميل الملف بنجاح في مجلد Downloads")
            except Exception as ex:
                append_log(f"❌ خطأ: {str(ex)}", True)
            
            progress_bar.value = 0
            page.update()

    # --- بناء الواجهة ---
    page.add(
        ft.Column([
            ft.Text("تحميل غصب PRO", size=28, weight="bold", color=ft.colors.BLUE_400),
            url_input,
            ft.Row([path_input]),
            ft.Row([
                ft.ElevatedButton(
                    "تحميل فيديو", 
                    icon=ft.icons.DOWNLOAD, 
                    data="video", 
                    on_click=start_download, 
                    expand=True,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.ElevatedButton(
                    "تحميل صوت", 
                    icon=ft.icons.MUSIC_NOTE, 
                    data="audio", 
                    on_click=start_download, 
                    expand=True, 
                    bgcolor=ft.colors.GREEN_800,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
            ]),
            ft.Divider(height=20),
            progress_text,
            progress_bar,
            ft.Container(
                content=log_list, 
                bgcolor=ft.colors.BLACK_26, 
                padding=10, 
                border_radius=12,
                border=ft.border.all(1, ft.colors.GREY_800)
            )
        ], horizontal_alignment="center")
    )

if __name__ == "__main__":
    ft.app(target=main)
 
