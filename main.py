# Google Trends Keyword Scraper — Ana çalıştırma dosyası
# Her keyword için explore + related searches çağırır, top/rising listelerini biriktirip CSV'ye yazar

import os
import sys

# Windows konsolunda UTF-8 çıktısını zorla (cp1252 unicode karakterlerde patlıyor)
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")
# Encoding ayarı tamamlandı

import config
from modules import trends_client, exporter


def main():
    # Çıktı klasörünü hazırla ve eski failed log'u temizle
    exporter.ensure_dir(config.OUTPUT_DIR)
    failed_log_path = os.path.join(config.OUTPUT_DIR, config.FAILED_LOG)
    exporter.reset_failed_log(failed_log_path)
    # Çıktı hazırlığı tamamlandı

    # Cookie dosyasını oku ve session oluştur
    try:
        cookie_header = trends_client.load_cookies(config.COOKIE_FILE)
    except (FileNotFoundError, ValueError) as e:
        print(f"HATA: {e}", file=sys.stderr)
        sys.exit(1)
    session = trends_client.build_session(cookie_header)
    # Session hazırlandı

    # Biriktirme listeleri ve sayaçlar
    top_rows = []
    rising_rows = []
    failed = []
    total = len(config.KEYWORDS)
    # Sayaçlar sıfırlandı

    # Her keyword için tam akışı uygula
    for index, keyword in enumerate(config.KEYWORDS, start=1):
        print(f"[{index}/{total}] keyword: {keyword}")
        try:
            top, rising = trends_client.fetch_keyword(session, keyword)
            # Sonuçları seed_keyword sütunuyla biriktir
            for query, value in top:
                top_rows.append((keyword, query, value))
            for query, value in rising:
                rising_rows.append((keyword, query, value))
            print(f"  ✓ top: {len(top)}, rising: {len(rising)}")
        except Exception as e:
            # Başarısız keyword'ü log'a ve listeye al
            reason = f"{type(e).__name__}: {e}"
            print(f"  ✗ FAILED: {reason}")
            failed.append((keyword, reason))
            exporter.append_failed(failed_log_path, keyword, reason)
        # Tek keyword işlemi bitti

        # İstekler arası rastgele bekleme (son iterasyonda atla)
        if index < total:
            trends_client.sleep_jittered()
        # Bekleme adımı tamamlandı

    # Toplanan tüm veriyi CSV'lere yaz (overwrite)
    top_csv = os.path.join(config.OUTPUT_DIR, config.TOP_CSV)
    rising_csv = os.path.join(config.OUTPUT_DIR, config.RISING_CSV)
    exporter.write_csv(top_csv, top_rows)
    exporter.write_csv(rising_csv, rising_rows)
    # CSV yazımı tamamlandı

    # Özet rapor
    success_count = total - len(failed)
    print()
    print("=" * 50)
    print(f"Tamamlandı: {success_count}/{total} keyword başarılı")
    print(f"top_queries.csv:    {len(top_rows)} satır → {top_csv}")
    print(f"rising_queries.csv: {len(rising_rows)} satır → {rising_csv}")
    if failed:
        print(f"failed_keywords.log: {len(failed)} kayıt → {failed_log_path}")
    print("=" * 50)
    # Özet basıldı


if __name__ == "__main__":
    main()
