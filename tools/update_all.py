# update_all.py

from src.data_loader import load_companies
from src.pdf_generator import PDFGenerator

def main():
    print("=== PDF 再生成パイプライン開始 ===")

    # 企業データ読み込み
    companies = load_companies()
    print(f"企業データ読み込み完了: {len(companies)} 件")

    # PDF生成器
    generator = PDFGenerator()

    # 各企業のPDFを再生成
    for company in companies:
        path = generator.generate(company)
        print(f"PDF生成完了: {company['name']} → {path}")

    print("=== 全PDFの再生成が完了しました ===")

if __name__ == "__main__":
    main()
