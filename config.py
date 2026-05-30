# Google Trends scraper için tüm konfigürasyon değerleri
# Magic number kullanılmaz; tüm sayısal sabitler burada tanımlanır

# Hedeflenecek ürün keyword'leri (seed listesi)
KEYWORDS = [
    "Camera Bags",
    "Camera Cases",
    "Camera Straps",
    "Screen Protectors",
    "Messenger Bags",
    "Laptop Sleeves",
    "Backpacks",
    "Tote Bags",
    "Duffel Bag",
    "Toiletry Bag",
    "Cosmetic Bags",
    "Mouse Pads",
    "Media Organizers",
    "Leather Trays",
    "Journals and Planners",
    "Coasters",
    "Pencil Cases",
    "Eyeglass Cases",
    "Wine Carriers",
    "Aprons",
    "Airpod Cases",
    "SD Card Holders",
    "Clutches",
    "Passport Holders",
    "Card Holders",
    "Personalized Gifts",
    "Corporate Gifts",
]
# Keyword listesi tanımlandı

# Hedef ülke ve zaman penceresi ayarları
GEO = ""              # Boş string = tüm dünya. Örn: "US", "TR", "GB"
TIMEFRAME = "today 1-m"  # Son 30 gün. Diğer: "today 7-d", "today 3-m", "today 12-m"
# Coğrafya/zaman ayarları tanımlandı

# Locale ve timezone — browser ne gönderiyorsa ona benzet
# hl=en-US ile bazı keyword'lerde Google boş veri döndürüyor; tr-TR ile dönüyor
HL = "tr-TR"
TZ = "-180"   # Türkiye (UTC+3), Google JS konvansiyonu: dakika cinsinden ters işaretli
# Locale/timezone ayarları tanımlandı

# Dosya yolları
COOKIE_FILE = "cookies.json"
OUTPUT_DIR = "./output/"
TOP_CSV = "top_queries.csv"
RISING_CSV = "rising_queries.csv"
FAILED_LOG = "failed_keywords.log"
# Dosya yolları tanımlandı

# İstekler arası bekleme aralığı (saniye, rastgele jitter için)
SLEEP_MIN = 5
SLEEP_MAX = 12
# Rate-limit bekleme aralığı tanımlandı

# 429 sonrası exponential backoff ayarları
MAX_RETRIES = 3
BACKOFF_BASE = 30   # Saniye. Denemeler: 30, 60, 120
# Retry ve backoff parametreleri tanımlandı

# HTTP header tanımları — tarayıcıyı taklit eder
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/131.0.0.0 Safari/537.36"
)

BASE_HEADERS = {
    "User-Agent": USER_AGENT,
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate, br",
    "Referer": "https://trends.google.com/",
}
# HTTP header'ları tanımlandı

# Google Trends API endpoint'leri
EXPLORE_URL = "https://trends.google.com/trends/api/explore"
RELATED_SEARCHES_URL = "https://trends.google.com/trends/api/widgetdata/relatedsearches"
# Endpoint URL'leri tanımlandı
