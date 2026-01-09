from fpdf import FPDF
import os

class TestPDF(FPDF):
    pass

def create_test_pdf():
    # srcフォルダの絶対パス
    base = os.path.dirname(os.path.abspath(__file__))

    # 各ディレクトリ
    font_dir = os.path.join(base, "..", "fonts")
    asset_dir = os.path.join(base, "..", "assets")
    output_dir = os.path.join(base, "..", "output")

    # フォントパス
    serif_path = os.path.join(font_dir, "ipaexm.ttf")
    sans_path = os.path.join(font_dir, "ipaexg.ttf")

    pdf = TestPDF(format="A4")
    pdf.set_auto_page_break(auto=False)

    pdf.add_font("JPSerif", "", serif_path)
    pdf.add_font("JPSerif", "B", serif_path)
    pdf.add_font("JPSans", "", sans_path)

    pdf.add_page()

    # 背景（白）
    pdf.set_fill_color(255, 255, 255)
    pdf.rect(0, 0, 210, 297, "F")

    # アイコン（重心補正）
    try:
        pdf.image(os.path.join(asset_dir, "kusunoki_icon.png"), x=138, y=16.3, w=56)
    except Exception as e:
        print("Icon load error:", e)

    page_w = pdf.w

    # タイトル（視覚中央補正 + 位置調整）
    pdf.set_font("JPSerif", "", 22)
    pdf.set_text_color(42, 42, 42)

    title = "医療キャリア診断レポート"
    title_w = pdf.get_string_width(title)
    x_title = (page_w - title_w) / 2 + 5.5  # 視覚中央補正

    pdf.set_xy(x_title, 127)
    pdf.cell(title_w, 12, title)

    # 下部ライン
    pdf.set_draw_color(220, 220, 220)
    pdf.set_line_width(0.3)
    pdf.line(55, 250, 155, 250)

    # サブタイトル（視覚中央補正 + 文字間 + 行間調整）
    pdf.set_font("JPSans", "", 15)
    pdf.set_text_color(85, 85, 85)

    subtitle = "Medical Career Insight Report"
    subtitle_w = pdf.get_string_width(subtitle)
    x_sub = (page_w - subtitle_w) / 2 + 5.5

    pdf.set_char_spacing(0.6)
    pdf.set_xy(x_sub, 257)
    pdf.cell(subtitle_w, 10, subtitle)

    # 保存
    output_path = os.path.join(output_dir, "test_output.pdf")
    print(">>> Saving PDF to:", output_path)
    pdf.output(output_path)

if __name__ == "__main__":
    create_test_pdf()
