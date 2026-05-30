# CSV ve failed log çıktısını yazan modül

import csv
import os
from datetime import datetime


def ensure_dir(path):
    """Verilen klasör yoksa oluşturur."""
    # Klasörü oluştur (varsa atla)
    os.makedirs(path, exist_ok=True)
    # Klasör hazır


def write_csv(path, rows):
    """rows = [(seed_keyword, query, value), ...] formatında CSV yazar (overwrite)."""
    # Dosyayı UTF-8 ve newline='' ile aç (Excel uyumu için utf-8-sig de seçilebilir)
    with open(path, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["seed_keyword", "query", "value"])
        writer.writerows(rows)
    # CSV yazımı tamamlandı


def append_failed(path, keyword, reason):
    """failed_keywords.log dosyasına timestamp'li bir satır ekler."""
    # Zaman damgalı satırı dosyaya ekle
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] FAILED: {keyword} — {reason}\n"
    with open(path, "a", encoding="utf-8") as f:
        f.write(line)
    # Failed kayıt eklendi


def reset_failed_log(path):
    """Yeni run başlamadan önce eski failed log dosyasını temizler."""
    # Var olan log'u sil; yeni run temiz başlasın
    if os.path.exists(path):
        os.remove(path)
    # Log temizleme tamamlandı
