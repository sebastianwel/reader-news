import requests
from bs4 import BeautifulSoup
import time

# --- KONFIGURATION & QUELLEN ---
WEATHER_FORECAST_URL = "https://api.open-meteo.com/v1/forecast?latitude=53.5507&longitude=9.9930&current=temperature_2m,weather_code&hourly=temperature_2m,precipitation_probability,weather_code&timezone=Europe%2FBerlin&forecast_days=1"

SOURCES = {
    "TAGESSCHAU TOP-NEWS": "https://www.tagesschau.de/infoservices/alle-meldungen-100~rss2.xml",
    "SPORT (SPORTSCHAU)": "https://www.sportschau.de/index~rss2.xml",
    "TECH (WIRED)": "https://www.wired.com/feed/rss"
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
}

WMO_CODES = {
    0: "Klarer Himmel", 1: "Hauptsächlich klar", 2: "Teilweise bewölkt", 3: "Bedeckt",
    45: "Nebel", 48: "Raureifnebel", 51: "Leichter Nieselregen", 61: "Leichter Regen",
    71: "Leichter Schneefall", 80: "Regenschauer", 95: "Gewitter"
}

# --- NEUE WETTER FUNKTIONEN ---

def get_detailed_weather():
    """Erzeugt einen detaillierten Wetterbericht inkl. Tagesaussicht für Hamburg."""
    try:
        res = requests.get(WEATHER_FORECAST_URL, timeout=10)
        data = res.json()
        
        current = data["current"]
        temp_now = current["temperature_2m"]
        cond_now = WMO_CODES.get(current["weather_code"], "Unbekannt")
        
        hourly = data["hourly"]
        
        def format_hour(hour):
            t = hourly["temperature_2m"][hour]
            prob = hourly["precipitation_probability"][hour]
            code = WMO_CODES.get(hourly["weather_code"][hour], "Unbekannt")
            return f"{hour}:00 Uhr: {t}°C, {code} (Regen: {prob}%)"

        report = (
            f"=== WETTER HAMBURG - {time.strftime('%d.%m.%Y')} ===\n\n"
            f"AKTUELL:\n"
            f"Zustand: {cond_now}\n"
            f"Temperatur: {temp_now}°C\n\n"
            f"TAGESAUSSICHT:\n"
            f"Vormittag  ({format_hour(10)})\n"
            f"Nachmittag ({format_hour(15)})\n"
            f"Abend      ({format_hour(20)})\n\n"
            f"Einen schönen Tag in der Hansestadt! ⚓"
        )
        return report
    except Exception as e:
        return f"Wetter-Update fehlgeschlagen: {e}"

def create_weather_file():
    filename = "pala_hamburg_wetter.txt"
    print("Erstelle Wetter-Datei...")
    with open(filename, "w", encoding="utf-8") as f:
        f.write(get_detailed_weather())
    print(f"Erfolg! '{filename}' wurde erstellt.")

# --- DEINE BESTEHENDE NEWS LOGIK (UNVERÄNDERT) ---

def get_full_article(url):
    """Extrahiert Text von Sportschau, Tagesschau oder Wired."""
    try:
        time.sleep(0.5)
        res = requests.get(url, headers=HEADERS, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        for trash in soup.find_all(['div', 'span', 'a', 'aside', 'nav'], 
                                   class_=['linklist', 'socialmedia', 'infobox', 'more-links', 'advertisement', 'sharing']):
            trash.decompose()

        paragraphs = soup.find_all(['p', 'div'], class_=['text-abschnitt', 'article__bodytext', 'paragraph', 'article__content'])
        
        if not paragraphs:
            paragraphs = soup.find_all('p')
            
        lines = []
        stop_words = ["Mehr zum Thema", "Lesen Sie auch", "Copyright", "Alle Rechte vorbehalten"]
        
        for p in paragraphs:
            text = p.get_text().strip()
            if any(word in text for word in stop_words):
                break
            if len(text) > 50:
                if text.lower().endswith(" mehr"):
                    text = text[:-5].strip()
                lines.append(text)
        
        return "\n\n".join(lines) if lines else "[Inhalt konnte nicht extrahiert werden]"
    except Exception as e:
        return f"[Fehler beim Laden des Volltexts: {e}]"

def create_pala_briefing():
    filename = "pala_top_briefing.txt"
    print("Erstelle News-Briefing...")
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"=== NANOBANANA DAILY BRIEFING - {time.strftime('%d.%m.%Y')} ===\n")
        f.write("Quellen: Tagesschau, Sportschau & Wired Tech\n\n")
        
        for category, rss_url in SOURCES.items():
            print(f"Verarbeite {category}...")
            f.write(f"\n>>> {category} <<<\n\n")
            
            try:
                response = requests.get(rss_url, headers=HEADERS, timeout=10)
                soup = BeautifulSoup(response.content, features="xml")
                items = soup.find_all('item')[:3]

                for i, item in enumerate(items, 1):
                    title = item.find('title').get_text() if item.find('title') else "Kein Titel"
                    link = item.find('link').get_text() if item.find('link') else ""
                    
                    if not link: continue
                    
                    print(f"  - Artikel {i}: {title[:50]}...")
                    f.write(f"[{i}] {title.upper()}\n\n")
                    
                    full_text = get_full_article(link)
                    f.write(full_text)
                    f.write("\n\n" + "-"*40 + "\n\n")

            except Exception as e:
                print(f"  Fehler bei {category}: {e}")
                f.write(f"[Kategorie-Fehler: {e}]\n\n")

    print(f"Erfolg! '{filename}' wurde erstellt.")

# --- EXECUTION ---

if __name__ == "__main__":
    # Erst das Wetter, dann die News
    create_weather_file()
    print("-" * 30)
    create_pala_briefing()