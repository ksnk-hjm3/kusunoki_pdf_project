from fpdf import FPDF
import pandas as pd
import os

# ============================
# PDFクラス（日本語フォント対応）
# ============================
class PDF(FPDF):
    def header(self):
        # フォントはここで使わない（add_font前に呼ばれるため）
        self.set_text_color(50, 50, 50)
        self.cell(0, 10, "医療企業レポート", ln=True, align="C")
        self.ln(5)

# ============================
# PDF生成関数
# ============================
def generate_pdf(row, output_dir="pdf_reports"):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    pdf = PDF()

    # ① フォント登録（add_page より前）
    pdf.add_font("Noto", "", "NotoSansJP-Regular.ttf", uni=True)
    pdf.set_font("Noto", size=12)

    # ② ページ追加
    pdf.add_page()

    # ----------------------------
    # 表紙
    # ----------------------------
    pdf.set_font("Noto", size=18)
    pdf.cell(0, 10, row["company_name"], ln=True)
    pdf.ln(5)

    pdf.set_font("Noto", size=12)
    pdf.cell(0, 8, f"医療度スコア: {row['total_medical_score']} / 120", ln=True)
    pdf.cell(0, 8, f"医療領域: {row['medical_domains'] or '該当なし'}", ln=True)
    pdf.cell(0, 8, f"公式サイト: {row['official_url']}", ln=True)
    pdf.cell(0, 8, f"採用ページ: {row['recruit_page'] or '未確認'}", ln=True)
    pdf.ln(10)

    # ----------------------------
    # 医療キーワード分析
    # ----------------------------
    pdf.set_font("Noto", size=14)
    pdf.cell(0, 10, "医療キーワード分析", ln=True)
    pdf.set_font("Noto", size=12)

    keywords = row["medical_keywords"] or "なし"
    pdf.multi_cell(0, 8, f"抽出されたキーワード: {keywords}")
    pdf.ln(5)

    # ----------------------------
    # 医療ドメイン分析
    # ----------------------------
    pdf.set_font("Noto", size=14)
    pdf.cell(0, 10, "医療ドメイン分析", ln=True)
    pdf.set_font("Noto", size=12)

    pdf.multi_cell(0, 8, f"該当ドメイン: {row['medical_domains'] or 'なし'}")
    pdf.multi_cell(0, 8, f"ドメインスコア: {row['medical_domain_scores']}")
    pdf.ln(5)

    # ----------------------------
    # 採用ページ評価
    # ----------------------------
    pdf.set_font("Noto", size=14)
    pdf.cell(0, 10, "採用ページ評価", ln=True)
    pdf.set_font("Noto", size=12)

    pdf.multi_cell(0, 8, f"採用ページURL: {row['recruit_page'] or '未確認'}")
    pdf.multi_cell(0, 8, f"医療キーワード数: {row['medical_keyword_count']}")
    pdf.ln(5)

    # ----------------------------
    # 総合評価
    # ----------------------------
    pdf.set_font("Noto", size=14)
    pdf.cell(0, 10, "総合評価", ln=True)
    pdf.set_font("Noto", size=12)

    score = row["total_medical_score"]
    if score >= 80:
        summary = "医療特化企業としての特徴が強く、医療職にとって高い親和性があります。"
    elif score >= 40:
        summary = "医療領域との関わりが明確で、医療職にとって一定の親和性があります。"
    else:
        summary = "医療要素は限定的ですが、一部領域で関わりが見られます。"

    pdf.multi_cell(0, 8, summary)

    # ----------------------------
    # 保存
    # ----------------------------
    filename = f"{output_dir}/{row['company_name']}.pdf"
    pdf.output(filename)

# ============================
# メイン処理
# ============================
def main():
    df = pd.read_csv("company_analysis.csv")

    for _, row in df.iterrows():
        print(f"[PDF] Generating: {row['company_name']}")
        generate_pdf(row)

    print("=== PDF generation completed ===")

if __name__ == "__main__":
    main()
