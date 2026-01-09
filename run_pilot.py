from modules.pdf_extract import extract_paragraphs
from modules.chunker import create_chunks
from modules.summarizer_local import summarize_chunk
from modules.embeddings import make_embedding
from modules.faiss_store import FaissStore
import json, os, time, csv, random

cfg = json.load(open("config.json", "r"))
PDF_DIR = cfg["PDF_DIR"]
OUTPUT_DIR = cfg["OUTPUT_DIR"]
os.makedirs(OUTPUT_DIR, exist_ok=True)

faiss = FaissStore(index_path=os.path.join(OUTPUT_DIR, "faiss.index"))

results = []
start_all = time.time()
for fname in os.listdir(PDF_DIR):
    if not fname.endswith(".pdf"):
        continue
    pdf_path = os.path.join(PDF_DIR, fname)
    paras = extract_paragraphs(pdf_path)
    chunks = create_chunks(paras, cfg["CHUNK_MIN"], cfg["CHUNK_MAX"], cfg["OVERLAP"])
    partials = []
    for c in chunks:
        s = summarize_chunk(c)  # ローカルモデル呼び出し
        emb = make_embedding(c)
        faiss.add(emb, {"pdf": fname, "chunk": c[:80]})
        partials.append(s)
    results.append({"pdf": fname, "chunks": len(chunks), "partials": len(partials)})
    # 進捗ログ保存など
end_all = time.time()
# CSV出力
with open(os.path.join(OUTPUT_DIR, "results.csv"), "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["pdf","chunks","partials"])
    writer.writeheader()
    writer.writerows(results)
print("Done", end_all - start_all)
