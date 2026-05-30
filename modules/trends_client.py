# Google Trends arka uç API'lerine HTTP istekleri atan modül
# Cookie tabanlı oturum, explore + related searches çağrıları, retry/backoff

import json
import random
import time
from pathlib import Path

import requests

import config


# --- Cookie yönetimi ---

def load_cookies(path):
    """cookies.json'u okuyup 'name=val; name=val; ...' header string'ine çevirir."""
    # Dosya varlığı kontrolü; yoksa anlamlı hata
    cookie_path = Path(path)
    if not cookie_path.exists():
        raise FileNotFoundError(
            f"Cookie dosyası bulunamadı: {path}. "
            "EditThisCookie / Cookie-Editor ile export edip proje köküne koy."
        )
    # Dosya kontrolü tamamlandı

    # JSON oku ve cookie listesini header string'e dönüştür
    with cookie_path.open("r", encoding="utf-8") as f:
        cookies = json.load(f)
    cookie_pairs = [f"{c['name']}={c['value']}" for c in cookies if "name" in c and "value" in c]
    if not cookie_pairs:
        raise ValueError(f"Cookie dosyası boş veya geçersiz format: {path}")
    return "; ".join(cookie_pairs)
    # Cookie string üretimi tamamlandı


def build_session(cookie_header):
    """BASE_HEADERS + Cookie header bağlı requests.Session döner."""
    # Session ve header'ları hazırla
    session = requests.Session()
    session.headers.update(config.BASE_HEADERS)
    session.headers["Cookie"] = cookie_header
    return session
    # Session hazırlığı tamamlandı


# --- JSON temizleme ---

def _clean_json(text):
    """Google Trends yanıtları )]}', öneki ile başlar; striple ve parse et."""
    # XSSI prefix'ini ayıkla
    stripped = text.lstrip()
    if stripped.startswith(")]}'"):
        stripped = stripped.split("\n", 1)[1] if "\n" in stripped else stripped[5:]
    return json.loads(stripped)
    # Temiz JSON döndürüldü


# --- Explore endpoint (token üretici) ---

def get_explore_payload(session, keyword):
    """Explore endpoint'i çağırır, related queries widget'ının token + request'ini döner."""
    # Keyword'ü lowercase gönder — Google case-sensitive davranıyor, "Camera Bags" boş dönüyor "camera bags" doluyor
    keyword_normalized = keyword.lower()
    # Keyword normalize edildi

    # Explore request gövdesini hazırla
    req_body = {
        "comparisonItem": [
            {"keyword": keyword_normalized, "geo": config.GEO, "time": config.TIMEFRAME}
        ],
        "category": 0,
        "property": "",
    }
    params = {
        "hl": config.HL,
        "tz": config.TZ,
        "req": json.dumps(req_body, separators=(",", ":")),
    }
    # Explore parametreleri hazır

    # İsteği at ve doğrula
    resp = session.get(config.EXPLORE_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = _clean_json(resp.text)
    # Yanıt JSON olarak parse edildi

    # Widget listesinden RELATED_QUERIES olanı bul
    for widget in data.get("widgets", []):
        widget_id = widget.get("id", "")
        if widget_id == "RELATED_QUERIES":
            token = widget.get("token")
            req = widget.get("request")
            if token and req:
                return token, req
    return None, None
    # Token bulunamadıysa (None, None) dönülür


# --- Related searches endpoint (asıl veri) ---

def get_related_searches(session, token, req):
    """Token ile related searches endpoint'i çağırır; (top, rising) listelerini döner."""
    # Request parametrelerini hazırla
    params = {
        "hl": config.HL,
        "tz": config.TZ,
        "req": json.dumps(req, separators=(",", ":")),
        "token": token,
    }
    # Parametreler hazır

    # İsteği at ve parse et
    resp = session.get(config.RELATED_SEARCHES_URL, params=params, timeout=30)
    resp.raise_for_status()
    data = _clean_json(resp.text)
    # Yanıt parse edildi

    # rankedList[0] = top, rankedList[1] = rising — her ikisini de güvenli şekilde çek
    ranked_lists = data.get("default", {}).get("rankedList", [])
    top = _extract_keywords(ranked_lists, 0)
    rising = _extract_keywords(ranked_lists, 1)
    return top, rising
    # Top ve rising listeleri ayrıştırıldı


def _extract_keywords(ranked_lists, index):
    """rankedList[index].rankedKeyword içinden (query, value) tuple listesi üretir."""
    # İndex sınırı kontrolü
    if len(ranked_lists) <= index:
        return []
    items = ranked_lists[index].get("rankedKeyword", [])
    # Liste mevcut

    # value alanı sayı (top için) veya "Breakout" stringi (rising için) olabilir → string'e cast
    result = []
    for item in items:
        query = item.get("query", "")
        raw_value = item.get("value", item.get("formattedValue", ""))
        result.append((query, str(raw_value)))
    return result
    # Tuple listesi hazır


# --- Tek keyword için tam akış + retry/backoff ---

def fetch_keyword(session, keyword):
    """Tek keyword için explore → related searches akışı; 429 sonrası exponential backoff."""
    # Denemeler arası backoff uygula
    last_error = None
    for attempt in range(config.MAX_RETRIES):
        try:
            # Explore ile token al
            token, req = get_explore_payload(session, keyword)
            if not token or not req:
                raise RuntimeError("Related queries widget token bulunamadı")
            # Token alındı

            # İstekler arası kısa bekleme (Google insanlığı sever)
            sleep_jittered()

            # Related searches'i çek
            top, rising = get_related_searches(session, token, req)
            if not top and not rising:
                raise RuntimeError("Boş veri döndü (top ve rising her ikisi de boş)")
            return top, rising
            # Başarılı dönüş

        except requests.HTTPError as e:
            # 429 ise backoff uygula, diğer HTTP hatalarını direkt fırlat
            status = e.response.status_code if e.response is not None else None
            if status == 429 and attempt < config.MAX_RETRIES - 1:
                wait = config.BACKOFF_BASE * (2 ** attempt)
                print(f"  ⚠ 429 alındı, {wait}s bekleniyor (deneme {attempt + 1}/{config.MAX_RETRIES})")
                time.sleep(wait)
                last_error = e
                continue
            raise
            # HTTP hata yönetimi tamamlandı

        except (RuntimeError, ValueError, KeyError) as e:
            # Parse/veri hataları — retry'e değmez, direkt fırlat
            raise

    # Tüm denemeler tükendi
    raise RuntimeError(f"{config.MAX_RETRIES} denemede başarısız: {last_error}")
    # fetch_keyword sonu


# --- Rastgele jitter sleep ---

def sleep_jittered():
    """SLEEP_MIN ile SLEEP_MAX arasında rastgele saniye bekler."""
    # Tek satır jitter
    time.sleep(random.uniform(config.SLEEP_MIN, config.SLEEP_MAX))
    # Bekleme tamamlandı
