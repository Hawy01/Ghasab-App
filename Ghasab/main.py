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
    
    # حاوية للتشخيص (تظهر في حال وجود خطأ فقط)
    diag_container = ft.Column(visible=True, horizontal_alignment="center")
    page.add(diag_container)

    def diag_log(msg, color=ft.Colors.WHITE):
        diag_container.controls.append(ft.Text(msg, color=color, size=12))
        page.update()

    try:
        diag_log("🚀 جاري فحص المحرك...")
        
        # طلب الصلاحيات بطريقة آمنة لتجنب الانهيار السابق
        try:
            if hasattr(page, "request_permission"):
                from flet import PermissionType
                page.request_permission(PermissionType.STORAGE)
                diag_log("✅ تم فحص نظام الصلاحيات")
            else:
                diag_log("ℹ️ تجاوز طلب الصلاحية اليدوي (سيتم الاعتماد على إعدادات الـ APK)")
        except:
            diag_log("⚠️ الصلاحيات البرمجية غير مدعومة")

        # فحص مكتبة yt-dlp
        import yt_dlp
        diag_log("✅ مكتبة التحميل جاهزة", ft.Colors.GREEN)

        # مسار الحفظ الافتراضي
        state = {"path": "/storage/emulated/0/Download/GhasabApp"}

        # --- عناصر الواجهة ---
        url_input = ft.TextField(
            label="روابط الفيديو", 
            multiline=True, 
            border_radius=12, 
            hint_text="ضع الروابط هنا..."
        )
        path_input = ft.TextField(label="مسار الحفظ", value=state["path"], expand=True)
        
        # تم إصلاح الخطأ هنا بإضافة src افتراضي
        video_thumbnail = ft.Image(
            src="https://flet.dev/img/pages/quickstart/flet-app-icons.png", 
            visible=False, 
            border_radius=10, 
            height=150
        )
        
        progress_bar = ft.ProgressBar(value=0, expand=True, color=ft.Colors.BLUE_400)
        progress_text = ft.Text("التقدم: 0%", size=12)
        log_list = ft.ListView(expand=True, spacing=5)

        def append_log(msg):
            log_list.controls.append(ft.Text(msg, size=11, color=ft.Colors.GREY_300))
            page.update()

        def update_progress(d):
            if d['status'] == 'downloading':
                try:
                    p_raw = d.get('_percent_str', '0%').replace('%','').strip()
                    progress_bar.value = float(p_raw) / 100
                    progress_text.value = f"جاري التحميل: {p_raw}%"
                    page.update()
                except: pass

        def start_download(e):
            urls = [u.strip() for u in url_input.value.split('\n') if u.strip()]
            if not urls: return
            
            mode = e.control.data 
            
            def dl_thread():
                try:
                    os.makedirs(state["path"], exist_ok=True)
                    for url in urls:
                        append_log(f"🔍 فحص: {url}")
                        opts = {
                            'outtmpl': f"{state['path']}/%(title)s.%(ext)s",
                            'format': 'bestvideo+bestaudio/best' if mode == 'video' else 'bestaudio/best',
                            'progress_hooks': [update_progress],
                        }
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            video_thumbnail.src = info.get('thumbnail', video_thumbnail.src)
                            video_thumbnail.visible = True
                        append_log("✅ تم بنجاح")
                except Exception as ex:
                    append_log(f"❌ خطأ: {str(ex)[:50]}")
                page.update()

            threading.Thread(target=dl_thread, daemon=True).start()

        # --- بناء واجهة التطبيق الحقيقية ---
        main_ui = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("تحميل غصب PRO", size=26, weight="bold", color=ft.Colors.BLUE_400),
                video_thumbnail,
                url_input,
                ft.Row([path_input]),
                ft.Row([
                    ft.FilledButton("فيديو", data="video", on_click=start_download, expand=True),
                    ft.FilledButton("صوت", data="audio", on_click=start_download, expand=True, bgcolor=ft.Colors.GREEN_800),
                ]),
                progress_bar, progress_text,
                ft.Container(content=log_list, height=150, bgcolor=ft.Colors.BLACK_26, padding=10, border_radius=12)
            ], horizontal_alignment="center")
        )

        # إخفاء التشخيص وإظهار الواجهة
        diag_container.visible = False
        page.add(main_ui)
        page.update()

    except Exception as e:
        diag_log("‼️ خطأ في التشغيل ‼️", ft.Colors.RED)
        diag_log(traceback.format_exc(), ft.Colors.RED_200)

if __name__ == "__main__":
    ft.app(target=main)
 
