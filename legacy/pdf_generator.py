from fpdf import FPDF
import os


def generate_pdf(result_text: str, recommendations: list, output_path: str):
    # 出力フォルダが無ければ作成
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    pdf = FPDF()
    pdf.add_page()

    # 日本語フォント（NotoSansJP）を使用
    font_path = "fonts/NotoSansJP-Regular.ttf"
    if os.path.exists(font_path):
        pdf.add_font("Noto", "", font_path, uni=True)
        pdf.set_font("Noto", size=12)
    else:
        pdf.set_font("Arial", size=12)

    # タイトル
    pdf.set_font_size(16)
    pdf.cell(0, 10, "医療キャリア診断レポート", ln=True)

    pdf.ln(5)
    pdf.set_font_size(12)

    # 診断結果
    pdf.multi_cell(0, 8, result_text)

    pdf.ln(5)
    pdf.set_font_size(14)
    pdf.cell(0, 10, "おすすめ企業一覧", ln=True)

    pdf.set_font_size(12)
    for c in recommendations:
        pdf.cell(0, 8, f"・{c}", ln=True)

    # PDF保存
    pdf.output(output_path)
