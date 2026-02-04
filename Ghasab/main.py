import flet as ft
import sys

# ملاحظة: وضعنا الاستيرادات داخل دالة مح محمية لضمان عدم الانهيار عند بدء التشغيل
def main(page: ft.Page):
    page.title = "Ghasab Safe Mode"
    page.theme_mode = ft.ThemeMode.DARK
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    
    status_text = ft.Text("جاري فحص النظام...", size=20)
    error_text = ft.Text("", color=ft.colors.RED_400, size=12)
    page.add(status_text, error_text)

    try:
        # 1. فحص نسخة بايثون في الجوال
        status_text.value = f"بايثون يعمل: {sys.version[:10]}"
        page.update()

        # 2. محاولة استيراد المكتبات الثقيلة داخل الدالة
        try:
            import yt_dlp
            status_text.value = "✅ المحرك سليم والمكتبات محملة"
            status_text.color = ft.colors.GREEN_400
        except ImportError as e:
            status_text.value = "❌ مكتبة yt-dlp مفقودة"
            error_text.value = str(e)
            
        # 3. عرض زر بسيط للتأكد من الواجهة
        page.add(ft.ElevatedButton("تشغيل الواجهة الحقيقية", on_click=lambda _: print("OK")))

    except Exception as e:
        status_text.value = "‼️ خطأ فادح في النظام"
        error_text.value = str(e)
    
    page.update()

if __name__ == "__main__":
    ft.app(target=main)
