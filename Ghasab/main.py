import flet as ft
import sys
import traceback
import os

# نضع الاستيرادات الثقيلة داخل دالة main لنمنع انهيار التطبيق عند التشغيل
def main(page: ft.Page):
    # إعدادات الصفحة الأساسية
    page.title = "Ghasab Diagnostic"
    page.theme_mode = ft.ThemeMode.DARK
    page.scroll = ft.ScrollMode.AUTO
    
    # حاوية لعرض الأخطاء
    log_output = ft.Column(spacing=10)
    page.add(ft.Text("Diagnostic Console", size=20, weight="bold"), log_output)

    def log_to_screen(message, color=ft.Colors.WHITE):
        log_output.controls.append(ft.Text(message, color=color, size=12))
        page.update()

    try:
        log_to_screen("1. Starting Python Environment...")
        log_to_screen(f"Python Version: {sys.version}")
        
        log_to_screen("2. Requesting Storage Permission...")
        page.request_permission(ft.PermissionType.STORAGE)
        
        log_to_screen("3. Attempting to import yt-dlp...")
        try:
            import yt_dlp
            log_to_screen("✅ yt-dlp imported successfully!", ft.Colors.GREEN)
        except ImportError as e:
            log_to_screen(f"❌ yt-dlp import failed: {str(e)}", ft.Colors.RED)
            return

        # إذا وصلنا هنا، يعني المحرك سليم، نبدأ ببناء الواجهة الحقيقية
        log_to_screen("4. Building UI components...")
        
        # (ضع هنا بقية كود الواجهة الخاص بك، لكن تأكد أن الاستيرادات داخل main أو محمية بـ try)
        from Ghasab.main_real import build_real_ui # مثال إذا فصلت الكود
        log_to_screen("✅ UI Ready!", ft.Colors.BLUE)

    except Exception as e:
        # التقاط أي خطأ يسبب الشاشة السوداء وعرضه
        error_details = traceback.format_exc()
        log_to_screen("‼️ CRITICAL CRASH ‼️", ft.Colors.RED)
        log_to_screen(error_details, ft.Colors.RED_200)

if __name__ == "__main__":
    ft.app(target=main)