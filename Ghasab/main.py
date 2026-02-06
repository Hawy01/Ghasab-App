import flet as ft
import os
import threading
import yt_dlp
import traceback

# ---------- وظائف مساعدة ----------
def get_android_download_folder():
    """محاولة الحصول على مسار التنزيلات الصحيح للأندرويد"""
    try:
        # الطريقة القياسية
        return "/storage/emulated/0/Download"
    except:
        return os.path.join(os.getcwd(), "downloads")

def find_cookie_files_scan():
    """فحص المجلدات بحثاً عن ملفات كوكيز"""
    candidates = [
        "/storage/emulated/0/Download",
        "/storage/emulated/0/Downloads",
        "/sdcard/Download",
    ]
    out = []
    for path in candidates:
        try:
            if os.path.isdir(path):
                for f in os.listdir(path):
                    if ("cookie" in f.lower()) and f.endswith((".txt", ".json")):
                        full_path = os.path.join(path, f)
                        out.append(full_path)
        except Exception as e:
            print(f"Error scanning {path}: {e}")
    return sorted(list(set(out)))

def main(page: ft.Page):
    # إعدادات الصفحة
    page.title = "تحميل غصب PRO"
    page.theme_mode = ft.ThemeMode.DARK
    page.rtl = True
    page.padding = 20
    page.scroll = ft.ScrollMode.AUTO

    # طلب الصلاحيات عند البدء
    try:
        page.request_permission(ft.PermissionType.STORAGE)
    except:
        pass

    # متغيرات الحالة
    state = {
        "path": os.path.join(get_android_download_folder(), "GhasabApp"),
        "selected_cookie": None
    }

    # ----- عناصر الواجهة -----
    
    # 1. قسم العنوان
    header = ft.Text("تحميل غصب PRO", size=28, weight="bold", color=ft.Colors.BLUE_400, text_align="center")

    # 2. إدخال الروابط
    url_input = ft.TextField(
        label="رابط الفيديو",
        hint_text="ألصق الرابط هنا...",
        prefix_icon=ft.Icons.LINK,
        border_radius=12,
        multiline=True,
        min_lines=1, 
        max_lines=3
    )

    # 3. قسم الكوكيز (القائمة + زر التحديث + اختيار يدوي)
    cookies_dropdown = ft.Dropdown(
        label="اختر ملف الكوكيز المكتشف",
        expand=True,
        hint_text="لم يتم اكتشاف ملفات بعد",
        icon=ft.Icons.COOKIE
    )

    def refresh_cookies_click(e):
        """تحديث القائمة عند الضغط"""
        files = find_cookie_files_scan()
        cookies_dropdown.options = []
        if files:
            for f in files:
                cookies_dropdown.options.append(ft.dropdown.Option(key=f, text=os.path.basename(f)))
            cookies_dropdown.hint_text = "اختر الملف"
            page.snack_bar = ft.SnackBar(ft.Text(f"✅ تم اكتشاف {len(files)} ملفات"))
        else:
            cookies_dropdown.hint_text = "لم يتم العثور على ملفات تلقائياً"
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ لم يتم العثور على ملفات، جرب الاختيار اليدوي"))
        page.snack_bar.open = True
        page.update()

    refresh_btn = ft.IconButton(icon=ft.Icons.REFRESH, on_click=refresh_cookies_click, tooltip="إعادة فحص المجلدات")

    # منتقي الملفات اليدوي (File Picker) - الحل الأضمن
    file_picker = ft.FilePicker(on_result=lambda e: manual_cookie_selected(e))
    page.overlay.append(file_picker)

    def manual_cookie_selected(e: ft.FilePickerResultEvent):
        if e.files:
            path = e.files[0].path
            state["selected_cookie"] = path
            manual_cookie_text.value = f"تم تحديد: {os.path.basename(path)}"
            manual_cookie_text.color = ft.Colors.GREEN_400
            # نلغي تحديد القائمة المنسدلة
            cookies_dropdown.value = None
            page.update()

    manual_cookie_btn = ft.ElevatedButton(
        "اختيار ملف كوكيز يدوياً",
        icon=ft.Icons.FILE_OPEN,
        on_click=lambda _: file_picker.pick_files(allowed_extensions=["txt", "json"]),
        bgcolor=ft.Colors.BLUE_GREY_900
    )
    manual_cookie_text = ft.Text("لم يتم اختيار ملف يدوي", size=12, color=ft.Colors.GREY)

    # 4. سجل العمليات (Log)
    log_list = ft.ListView(expand=True, spacing=2, auto_scroll=True, height=150)
    log_container = ft.Container(
        content=log_list,
        bgcolor=ft.Colors.BLACK45,
        border_radius=10,
        padding=10,
        border=ft.border.all(1, ft.Colors.GREY_800)
    )

    def log(msg, color=ft.Colors.WHITE):
        log_list.controls.append(ft.Text(f"> {msg}", color=color, size=13, font_family="monospace"))
        page.update()

    # 5. منطق التحميل
    progress_bar = ft.ProgressBar(value=0, visible=False, color=ft.Colors.GREEN)
    progress_label = ft.Text("", size=12)

    def update_progress(d):
        if d['status'] == 'downloading':
            try:
                p = d.get('_percent_str', '').replace('%','')
                progress_label.value = f"جاري التحميل: {p}%"
                page.update()
            except: pass

    def start_download(e):
        urls = [u.strip() for u in url_input.value.split('\n') if u.strip()]
        if not urls:
            log("❌ الرجاء وضع رابط فيديو", ft.Colors.RED)
            return

        # تحديد ملف الكوكيز (اليدوي أولاً، ثم القائمة)
        cookie_file = state["selected_cookie"]
        if not cookie_file and cookies_dropdown.value:
            cookie_file = cookies_dropdown.value
        
        if cookie_file:
            log(f"🍪 استخدام الكوكيز: {os.path.basename(cookie_file)}", ft.Colors.CYAN)
        else:
            log("⚠️ جاري التحميل بدون كوكيز", ft.Colors.ORANGE)

        progress_bar.visible = True
        progress_bar.value = None # وضع غير محدد (loading)
        page.update()

        def dl_thread():
            try:
                save_path = state["path"]
                # محاولة إنشاء المجلد
                try:
                    os.makedirs(save_path, exist_ok=True)
                except Exception as perm_err:
                    log(f"❌ مشكلة صلاحيات المجلد: {perm_err}", ft.Colors.RED)
                    # محاولة استخدام مجلد داخلي بديل
                    save_path = os.path.join(page.internal_storage_path or "", "GhasabDownloads")
                    os.makedirs(save_path, exist_ok=True)
                    log(f"🔄 تم تحويل المسار إلى: {save_path}", ft.Colors.YELLOW)

                ydl_opts = {
                    'outtmpl': f"{save_path}/%(title)s.%(ext)s",
                    'progress_hooks': [update_progress],
                    'ignoreerrors': True,
                    'nocheckcertificate': True,
                }
                
                if cookie_file:
                    ydl_opts['cookiefile'] = cookie_file

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    for url in urls:
                        log(f"⏳ بدء: {url}", ft.Colors.BLUE)
                        ydl.download([url])
                        log(f"✅ تم الانتهاء من الرابط", ft.Colors.GREEN)

            except Exception as ex:
                full_error = traceback.format_exc()
                log(f"❌ خطأ فادح: {str(ex)}", ft.Colors.RED)
                print(full_error) # يظهر في التيرمنال للمطور
            
            progress_bar.visible = False
            progress_label.value = "انتهت العملية"
            page.update()

        threading.Thread(target=dl_thread, daemon=True).start()

    # تجميع الواجهة
    page.add(
        ft.SafeArea(
            ft.Column([
                header,
                ft.Divider(height=20, color="transparent"),
                url_input,
                ft.Row([cookies_dropdown, refresh_btn], alignment="center"),
                manual_cookie_btn,
                manual_cookie_text,
                ft.Divider(),
                ft.Row([
                    ft.FilledButton("تحميل فيديو", icon=ft.Icons.VIDEO_LIBRARY, on_click=start_download, expand=True, height=50),
                    # يمكن إضافة زر صوت هنا
                ]),
                ft.Divider(height=10, color="transparent"),
                progress_bar,
                progress_label,
                log_container
            ])
        )
    )

if __name__ == "__main__":
    ft.app(target=main)
