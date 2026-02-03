import flet as ft
import os
import threading
import yt_dlp
import re
import traceback
import sys

# ---------- وظائف مساعدة ----------
def find_cookie_files():
    # البحث عن ملفات الكوكيز في مجلد التنزيلات بالجوال
    candidates = ["/storage/emulated/0/Download", "/sdcard/Download", os.path.expanduser("~/downloads")]
    out = []
    for path in candidates:
        try:
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if ("cookie" in f.lower()) and f.endswith((".txt", ".json")):
                        out.append(os.path.join(path, f))
        except: pass
    return sorted(list(set(out)))

def main(page: ft.Page):
    # إعدادات الصفحة الأساسية
    page.title = "تحميل غصب PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 15
    page.scroll = ft.ScrollMode.AUTO

    # حاوية للتشخيص (تظهر فقط في حال وجود خلل لبدء تشغيل التطبيق)
    diag_container = ft.Column(visible=True, horizontal_alignment="center")
    page.add(diag_container)

    def diag_log(msg, color=ft.Colors.WHITE):
        diag_container.controls.append(ft.Text(msg, color=color, size=12))
        page.update()

    try:
        diag_log("🚀 جاري فحص بيئة العمل...")
        
        # 1. معالجة الصلاحيات بشكل مرن (حل مشكلة AttributeError السابقة)
        try:
            if hasattr(page, "request_permission"):
                # نطلب صلاحية التخزين فقط إذا كان الأمر مدعومًا في النسخة الحالية
                from flet import PermissionType
                page.request_permission(PermissionType.STORAGE)
                diag_log("✅ تم إرسال طلب الصلاحيات.")
            else:
                diag_log("ℹ️ تم تجاوز طلب الصلاحية اليدوي (مدعوم عبر APK).")
        except Exception as pe:
            diag_log(f"⚠️ تنبيه الصلاحيات: {str(pe)}")

        # 2. التأكد من وجود مكتبة التحميل
        import yt_dlp
        diag_log("✅ محرك yt-dlp جاهز.")

        # ---------- إعداد مسار الحفظ ----------
        default_path = "/storage/emulated/0/Download/GhasabApp"
        # إذا لم يكن المسار متاحًا (في بعض الأنظمة) نستخدم مساراً داخلياً
        if not os.path.exists("/storage/emulated/0"):
             default_path = os.path.join(os.getcwd(), "downloads")

        state = {"path": default_path}

        # ---------- عناصر واجهة التطبيق ----------
        url_input = ft.TextField(
            label="روابط الفيديو (رابط في كل سطر)",
            multiline=True,
            min_lines=1,
            max_lines=3,
            border_radius=12,
            hint_text="انسخ الرابط هنا..."
        )

        path_input = ft.TextField(
            label="مسار الحفظ",
            value=state["path"],
            border_radius=10,
            text_size=12,
            expand=True
        )

        video_thumbnail = ft.Image(
            visible=False,
            width=300,
            height=180,
            fit="contain",
            border_radius=10
        )

        cookies_dropdown = ft.Dropdown(
            label="ملف الكوكيز (اختياري)",
            options=[ft.dropdown.Option(key=f, text=os.path.basename(f)) for f in find_cookie_files()],
            expand=True
        )

        progress_bar = ft.ProgressBar(value=0, expand=True, color=ft.Colors.BLUE_400)
        progress_text = ft.Text("التقدم: 0%", size=12)
        log_list = ft.ListView(expand=True, spacing=5, auto_scroll=True)
        status_text = ft.Text("جاهز للتحميل", weight="bold")

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
            if not urls:
                page.snack_bar = ft.SnackBar(ft.Text("❌ يرجى إضافة رابط أولاً"))
                page.snack_bar.open = True
                page.update()
                return
            
            mode = e.control.data 
            cookie_file = cookies_dropdown.value
            
            def dl_thread():
                try:
                    save_path = state["path"]
                    if not os.path.exists(save_path):
                        os.makedirs(save_path, exist_ok=True)

                    for url in urls:
                        append_log(f"🔍 فحص: {url}")
                        
                        opts = {
                            'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                            'format': 'bestvideo+bestaudio/best' if mode == 'video' else 'bestaudio/best',
                            'progress_hooks': [update_progress],
                            'cookiefile': cookie_file,
                        }
                        
                        with yt_dlp.YoutubeDL(opts) as ydl:
                            info = ydl.extract_info(url, download=True)
                            if 'thumbnail' in info:
                                video_thumbnail.src = info['thumbnail']
                                video_thumbnail.visible = True
                        
                        append_log(f"✅ اكتمل تحميل: {url[:30]}...")
                    
                    status_text.value = "اكتملت جميع العمليات!"
                except Exception as ex:
                    append_log(f"❌ خطأ: {str(ex)[:60]}")
                
                progress_bar.value = 0
                page.update()

            threading.Thread(target=dl_thread, daemon=True).start()

        # ---------- تجميع الواجهة الرئيسية ----------
        main_ui = ft.Container(
            padding=10,
            content=ft.Column([
                ft.Text("تحميل غصب PRO", size=28, weight="bold", color=ft.Colors.BLUE_400),
                ft.Row([video_thumbnail], alignment="center"),
                url_input,
                ft.Row([
                    path_input,
                    ft.IconButton(ft.Icons.SAVE, tooltip="حفظ المسار", on_click=lambda _: page.show_snack_bar(ft.SnackBar(ft.Text("تم تحديث المسار"))))
                ]),
                cookies_dropdown,
                ft.Row([
                    ft.FilledButton("فيديو", data="video", icon=ft.Icons.DOWNLOAD, on_click=start_download, expand=True),
                    ft.FilledButton("صوت", data="audio", icon=ft.Icons.MUSIC_NOTE, on_click=start_download, expand=True, bgcolor=ft.Colors.GREEN_800),
                ]),
                ft.Divider(height=20, color=ft.Colors.TRANSPARENT),
                status_text,
                progress_bar,
                progress_text,
                ft.Container(
                    content=log_list,
                    height=180,
                    bgcolor=ft.Colors.BLACK_26,
                    padding=10,
                    border_radius=12,
                    border=ft.border.all(1, ft.Colors.GREY_900)
                ),
            ], horizontal_alignment="center")
        )

        # إذا وصلنا هنا بنجاح، نخفي شاشة التشخيص ونعرض الواجهة
        diag_container.visible = False
        page.add(main_ui)
        page.update()

    except Exception as global_ex:
        # في حال حدوث خطأ فادح يمنع تشغيل التطبيق، نعرضه هنا
        diag_log("‼️ خطأ فادح في التشغيل ‼️", ft.Colors.RED)
        diag_log(traceback.format_exc(), ft.Colors.RED_200)

if __name__ == "__main__":
    # تشغيل التطبيق كـ APK
    ft.app(target=main)
