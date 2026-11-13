#!/usr/bin/env python3
"""
bing-wallpaper-kde.py
=====================
Descarga y aplica automáticamente el fondo de pantalla del día en KDE Plasma.

Soporta múltiples fuentes y regiones:
- Microsoft Bing (Global 3840x2400 y mercados regionales: España, Japón, Alemania, EE.UU., etc.)
- Google Chromecast (Paisajes y naturaleza seleccionados de Google TV en 4K)
- Wikimedia Commons (Picture of the Day en altísima resolución 4K-8K)
- Wallhaven (Los mejores fondos de escritorio 4K/UHD de la comunidad del día)
- Aleatorio diario (cambia de país o fuente cada día)

Características:
- Funciona online y offline (usa la última imagen en caché si no hay red).
- Se aplica por defecto a todos los usuarios, pero respeta la elección individual:
  si un usuario cambia su fondo de pantalla en KDE por otro, se detecta y no se sobrescribe.
- Cada usuario puede tener su propio país/fuente configurado de forma independiente.
- Selector gráfico interactivo nativo en KDE (kdialog) y en terminal.
- Entrada en el menú de aplicaciones de KDE ("Elegir país o fuente de fondo").
"""

from __future__ import annotations

import argparse
import configparser
import datetime
import hashlib
import json
import logging
import os
import random
import re
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ---------------------------------------------------------------------------
# Catálogo de fuentes, mercados y regiones soportadas
# ---------------------------------------------------------------------------
AVAILABLE_MARKETS: dict[str, dict[str, str]] = {
    # --- Fuentes alternativas de alta calidad ---
    "chromecast": {
        "name": "Google Chromecast",
        "description": "Paisajes y naturaleza de Google TV / Chromecast (4K)",
        "type": "chromecast",
        "group": "Otras fuentes",
    },
    "wikimedia": {
        "name": "Wikimedia Commons (POTD)",
        "description": "Imagen del día destacada de Wikipedia (resolución extrema hasta 6K/8K)",
        "type": "wikimedia",
        "group": "Otras fuentes",
    },
    "wallhaven": {
        "name": "Wallhaven (Top 4K)",
        "description": "Fondos de pantalla 4K/UHD mejor valorados de la comunidad",
        "type": "wallhaven",
        "group": "Otras fuentes",
    },

    # --- Microsoft Bing (Global y Regional) ---
    "global": {
        "name": "Microsoft Bing (Global)",
        "description": "API oficial de Microsoft Bing Wallpaper (Azure CDN, 3840×2400)",
        "type": "bwc",
        "group": "Microsoft Bing",
    },
    "es-ES": {
        "name": "España",
        "description": "Fondo y descripciones en español (España, 4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "en-US": {
        "name": "Estados Unidos / Global UHD",
        "description": "Fondo oficial de EE.UU. / catálogo internacional (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "ja-JP": {
        "name": "Japón",
        "description": "Fondo seleccionado para Japón (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "de-DE": {
        "name": "Alemania",
        "description": "Fondo seleccionado para Alemania (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "en-GB": {
        "name": "Reino Unido",
        "description": "Fondo seleccionado para el Reino Unido (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "fr-FR": {
        "name": "Francia",
        "description": "Fondo seleccionado para Francia (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "it-IT": {
        "name": "Italia",
        "description": "Fondo seleccionado para Italia (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "pt-BR": {
        "name": "Brasil",
        "description": "Fondo seleccionado para Brasil (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "zh-CN": {
        "name": "China",
        "description": "Fondo seleccionado para China (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "en-IN": {
        "name": "India",
        "description": "Fondo seleccionado para India (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "en-CA": {
        "name": "Canadá",
        "description": "Fondo seleccionado para Canadá (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "en-AU": {
        "name": "Australia",
        "description": "Fondo seleccionado para Australia (4K UHD)",
        "type": "regional",
        "group": "Microsoft Bing",
    },
    "random": {
        "name": "Aleatorio diario",
        "description": "Elige una fuente o país diferente cada día (Bing, Chromecast, Wiki, etc.)",
        "type": "special",
        "group": "Modo especial",
    },
}

MARKET_ALIASES: dict[str, str] = {
    # Opción 4: Google Chromecast
    "4": "chromecast",
    "chromecast": "chromecast",
    "google-chromecast": "chromecast",
    "google": "chromecast",
    "cast": "chromecast",

    # Opción 5: Wikimedia Commons POTD
    "5": "wikimedia",
    "wikimedia": "wikimedia",
    "wikipedia": "wikimedia",
    "potd": "wikimedia",
    "commons": "wikimedia",
    "wiki": "wikimedia",

    # Opción 6: Wallhaven
    "6": "wallhaven",
    "wallhaven": "wallhaven",
    "wh": "wallhaven",

    # Bing Global y Regional
    "global": "global",
    "internacional": "global",
    "international": "global",
    "ms": "global",
    "bwc": "global",
    "es": "es-ES",
    "espana": "es-ES",
    "españa": "es-ES",
    "spain": "es-ES",
    "es-es": "es-ES",
    "us": "en-US",
    "usa": "en-US",
    "eeuu": "en-US",
    "en-us": "en-US",
    "uk": "en-GB",
    "gb": "en-GB",
    "reino-unido": "en-GB",
    "en-gb": "en-GB",
    "jp": "ja-JP",
    "japan": "ja-JP",
    "japon": "ja-JP",
    "japón": "ja-JP",
    "ja-jp": "ja-JP",
    "de": "de-DE",
    "germany": "de-DE",
    "alemania": "de-DE",
    "de-de": "de-DE",
    "fr": "fr-FR",
    "france": "fr-FR",
    "francia": "fr-FR",
    "fr-fr": "fr-FR",
    "it": "it-IT",
    "italy": "it-IT",
    "italia": "it-IT",
    "it-it": "it-IT",
    "br": "pt-BR",
    "brazil": "pt-BR",
    "brasil": "pt-BR",
    "pt-br": "pt-BR",
    "cn": "zh-CN",
    "china": "zh-CN",
    "zh-cn": "zh-CN",
    "in": "en-IN",
    "india": "en-IN",
    "en-in": "en-IN",
    "ca": "en-CA",
    "canada": "en-CA",
    "canadá": "en-CA",
    "en-ca": "en-CA",
    "au": "en-AU",
    "australia": "en-AU",
    "en-au": "en-AU",
    "random": "random",
    "azar": "random",
    "aleatorio": "random",
}

# ---------------------------------------------------------------------------
# Rutas a nivel de sistema y configuración
# ---------------------------------------------------------------------------
SYSTEM_WALLPAPER_PKG_DIR = Path("/usr/share/wallpapers/BingDaily")
SYSTEM_IMAGES_DIR = SYSTEM_WALLPAPER_PKG_DIR / "contents" / "images"
SYSTEM_CACHE_DIR = Path("/var/cache/bing-wallpaper")
SYSTEM_CONFIG_PATH = Path("/etc/bing-wallpaper-kde.conf")
SYSTEM_BIN_PATH = Path("/usr/local/bin/bing-wallpaper-kde")
SYSTEM_AUTOSTART_PATH = Path("/etc/xdg/autostart/bing-wallpaper-kde.desktop")
SYSTEM_SERVICE_PATH = Path("/etc/systemd/system/bing-wallpaper-fetch.service")
SYSTEM_TIMER_PATH = Path("/etc/systemd/system/bing-wallpaper-fetch.timer")
SYSTEM_MENU_APP_PATH = Path("/usr/share/applications/bing-wallpaper-config.desktop")

BING_PATH_MARKERS = (
    "/usr/share/wallpapers/BingDaily",
    "/var/cache/bing-wallpaper",
    "/wallpapers/bing",
)

MAX_CACHED_IMAGES = 24

logging.basicConfig(
    level=logging.INFO,
    format="[bing-wallpaper-kde] %(levelname)s: %(message)s",
)
log = logging.getLogger("bing-wallpaper-kde")


# ---------------------------------------------------------------------------
# Resolución de Mercado / Fuente
# ---------------------------------------------------------------------------
def resolve_market(user_input: str) -> str:
    """Normaliza un alias o código a una fuente o mercado soportado."""
    cleaned = user_input.strip()
    lower = cleaned.lower().replace("_", "-")
    if lower in MARKET_ALIASES:
        return MARKET_ALIASES[lower]
    for code in AVAILABLE_MARKETS:
        if code.lower() == lower:
            return code
    if re.match(r"^[a-z]{2}-[A-Z]{2}$", cleaned, re.IGNORECASE):
        parts = cleaned.split("-")
        return f"{parts[0].lower()}-{parts[1].upper()}"
    return cleaned


def get_effective_market(override: str | None = None) -> str:
    """
    Determina la fuente o mercado a utilizar siguiendo la jerarquía:
    1. Parámetro CLI explícito (--market o --source).
    2. Variable de entorno BING_WALLPAPER_MKT.
    3. Preferencia del usuario (~/.config/bing-wallpaper-kde.json).
    4. Configuración del sistema (/etc/bing-wallpaper-kde.conf).
    5. Por defecto: "es-ES".
    """
    if override:
        return resolve_market(override)

    env_mkt = os.environ.get("BING_WALLPAPER_MKT")
    if env_mkt:
        return resolve_market(env_mkt)

    user_state = load_user_state()
    if user_state.get("market"):
        return resolve_market(user_state["market"])

    if SYSTEM_CONFIG_PATH.is_file():
        try:
            cp = configparser.ConfigParser()
            cp.read(SYSTEM_CONFIG_PATH)
            if cp.has_option("General", "market"):
                return resolve_market(cp.get("General", "market"))
        except Exception:
            pass

    return "es-ES"


def get_concrete_market(effective_market: str, date_str: str | None = None) -> str:
    """
    Si el mercado es 'random', selecciona una fuente o país de forma determinista para la fecha dada.
    """
    if effective_market != "random":
        return effective_market

    if not date_str:
        date_str = time.strftime("%Y%m%d")

    pool = [k for k in AVAILABLE_MARKETS if k != "random"]
    rng = random.Random(f"bing-random-{date_str}")
    chosen = rng.choice(pool)
    log.info("Modo aleatorio: fuente seleccionada para hoy (%s) -> %s", date_str, chosen)
    return chosen


# ---------------------------------------------------------------------------
# Utilidades de rutas y estado por usuario
# ---------------------------------------------------------------------------
def get_user_cache_dir() -> Path:
    xdg_data = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data) if xdg_data else Path.home() / ".local" / "share"
    return base / "wallpapers" / "bing"


def get_user_state_file() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / "bing-wallpaper-kde.json"


def get_kde_appletsrc_path() -> Path:
    xdg_config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg_config) if xdg_config else Path.home() / ".config"
    return base / "plasma-org.kde.plasma.desktop-appletsrc"


def get_writable_storage_dirs() -> list[Path]:
    dirs: list[Path] = []
    if os.geteuid() == 0:
        dirs.extend([SYSTEM_CACHE_DIR, SYSTEM_IMAGES_DIR])
    else:
        for d in (SYSTEM_CACHE_DIR, SYSTEM_IMAGES_DIR):
            if d.exists() and os.access(d, os.W_OK):
                dirs.append(d)
        dirs.append(get_user_cache_dir())
    return dirs


def get_readable_storage_dirs() -> list[Path]:
    dirs: list[Path] = []
    if os.geteuid() != 0:
        dirs.append(get_user_cache_dir())
    dirs.extend([SYSTEM_CACHE_DIR, SYSTEM_IMAGES_DIR])
    return dirs


def load_user_state() -> dict:
    state_file = get_user_state_file()
    if state_file.is_file():
        try:
            return json.loads(state_file.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {}


def save_user_state(state: dict) -> None:
    state_file = get_user_state_file()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")


# ---------------------------------------------------------------------------
# Descargadores especializados por fuente (Bing, Chromecast, Wikimedia, Wallhaven)
# ---------------------------------------------------------------------------
def fetch_chromecast_metadata(date_str: str) -> dict | None:
    """Descarga el catálogo de Google Chromecast y selecciona una imagen determinista para la fecha."""
    url = "https://raw.githubusercontent.com/dconnolly/chromecast-backgrounds/master/backgrounds.json"
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; KDE Plasma)"}
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            items = json.loads(r.read().decode("utf-8"))
        if not items:
            return None
        seed = int(hashlib.md5(f"cc-{date_str}".encode()).hexdigest(), 16)
        item = items[seed % len(items)]
        raw_url = item["url"]
        # Obtener máxima resolución original (sustituir s1920 por s0 en googleusercontent)
        hi_url = re.sub(r"/s\d+[^/]*/", "/s0/", raw_url)
        author = item.get("author", "Google Chromecast")
        location = item.get("location") or author
        return {
            "market": "chromecast",
            "date": date_str,
            "url": hi_url,
            "title": location,
            "copyright": f"{author} (Google Chromecast)",
        }
    except Exception as exc:
        log.warning("Error consultando Google Chromecast (%s).", exc)
        return None


def fetch_wikimedia_metadata(date_str: str) -> dict | None:
    """Obtiene la Imagen del Día (POTD) de Wikimedia Commons en máxima calidad."""
    headers = {"User-Agent": "KDEWallpaperScript/2.1 (https://github.com/user/bing-wallpaper-kde; contact@example.com)"}

    # Método 1: Feed Atom oficial de commons.wikimedia.org (rápido, sin límites 429)
    try:
        import xml.etree.ElementTree as ET
        import html
        feed_url = "https://commons.wikimedia.org/w/api.php?action=featuredfeed&feed=potd&feedformat=atom"
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            xml_data = r.read()

        root = ET.fromstring(xml_data)
        entries = root.findall("{http://www.w3.org/2005/Atom}entry")
        if entries:
            entry = entries[-1]
            summary_elem = entry.find("{http://www.w3.org/2005/Atom}summary")
            if summary_elem is not None and summary_elem.text:
                summary = summary_elem.text
                m_img = re.search(r"<img[^>]+src=[\"\x27](https://[^\s\"\x27]+)[\"\x27]", summary)
                if m_img:
                    raw_src = html.unescape(m_img.group(1))
                    # Convertir miniatura a UHD 3840px
                    hi_url = re.sub(r"/\d+px-([^/?]+).*$", r"/3840px-\1", raw_src)

                    # Extraer título del archivo y descripción
                    m_file = re.search(r"href=[\"\x27]/wiki/(File:[^\"\x27]+)[\"\x27]", summary)
                    file_name = urllib.parse.unquote(m_file.group(1)).replace("File:", "").replace("_", " ") if m_file else "POTD"

                    clean_text = re.sub(r"<table.*?</table>", "", summary, flags=re.DOTALL)
                    clean_text = re.sub(r"<[^>]+>", "", clean_text).strip()
                    title = clean_text[:120] if clean_text else file_name

                    return {
                        "market": "wikimedia",
                        "date": date_str,
                        "url": hi_url,
                        "title": title,
                        "copyright": f"{file_name} (Wikimedia Commons POTD)",
                    }
    except Exception as exc:
        log.debug("Fallback en feed Atom de Wikimedia (%s), probando REST...", exc)

    # Método 2 (Fallback): REST API de Wikipedia
    try:
        dt = datetime.datetime.strptime(date_str, "%Y%m%d")
    except Exception:
        dt = datetime.datetime.now()
    feed_date = dt.strftime("%Y/%m/%d")

    try:
        feed_url = f"https://en.wikipedia.org/api/rest_v1/feed/featured/{feed_date}"
        req = urllib.request.Request(feed_url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            wdata = json.loads(r.read().decode("utf-8"))

        potd = wdata.get("image", {})
        title = potd.get("title", "")
        desc = potd.get("description", {}).get("text", "Wikimedia Commons Picture of the Day")

        api_url = (
            f"https://commons.wikimedia.org/w/api.php?action=query&titles={urllib.parse.quote(title)}"
            f"&prop=imageinfo&iiprop=url|size|mime&iiurlwidth=3840&format=json"
        )
        req2 = urllib.request.Request(api_url, headers=headers)
        with urllib.request.urlopen(req2, timeout=10) as r2:
            cdata = json.loads(r2.read().decode("utf-8"))

        info = next(iter(cdata["query"]["pages"].values()))["imageinfo"][0]
        mime = info.get("mime", "")
        if mime in ("image/jpeg", "image/png") and info.get("width", 0) <= 6000:
            img_url = info["url"]
        else:
            img_url = info.get("thumburl") or info["url"]

        return {
            "market": "wikimedia",
            "date": date_str,
            "url": img_url,
            "title": desc,
            "copyright": f"{title} (Wikimedia Commons POTD)",
        }
    except Exception as exc:
        log.warning("Error consultando Wikimedia Commons POTD (%s).", exc)
        return None


def fetch_wallhaven_metadata(date_str: str) -> dict | None:
    """Obtiene los mejores fondos de pantalla 4K del día desde Wallhaven API."""
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; KDE Plasma)"}
    url = "https://wallhaven.cc/api/v1/search?categories=100&purity=100&sorting=toplist&topRange=1d&atleast=1920x1080"
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=10) as r:
            whdata = json.loads(r.read().decode("utf-8"))
        items = whdata.get("data", [])
        if not items:
            # Fallback a la semana si el ranking diario aún no se ha consolidado
            url_w = "https://wallhaven.cc/api/v1/search?categories=100&purity=100&sorting=toplist&topRange=1w&atleast=1920x1080"
            req_w = urllib.request.Request(url_w, headers=headers)
            with urllib.request.urlopen(req_w, timeout=10) as rw:
                items = json.loads(rw.read().decode("utf-8")).get("data", [])
        if not items:
            return None

        seed = int(hashlib.md5(f"wh-{date_str}".encode()).hexdigest(), 16)
        item = items[seed % min(len(items), 6)]
        resolution = item.get("resolution", "4K")
        item_id = item.get("id", "")
        return {
            "market": "wallhaven",
            "date": date_str,
            "url": item["path"],
            "title": f"Wallhaven Top Wallpaper ({resolution})",
            "copyright": f"Wallhaven #{item_id} (General / 4K UHD)",
        }
    except Exception as exc:
        log.warning("Error consultando Wallhaven (%s).", exc)
        return None


def fetch_bing_metadata(market: str, retries: int = 3, delay: float = 2.0) -> dict | None:
    """Descarga la imagen del día desde las APIs de Microsoft Bing (Global o regional)."""
    headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; KDE Plasma)"}

    # API Global Oficial de Microsoft Bing Wallpaper (Azure Edge CDN, 3840x2400)
    if market == "global":
        bwc_url = "https://bingwallpaper.microsoft.com/api/BWC/getHPImages"
        for attempt in range(1, retries + 1):
            try:
                req = urllib.request.Request(bwc_url, headers=headers)
                with urllib.request.urlopen(req, timeout=10) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    img = data["images"][0]
                    return {
                        "market": "global",
                        "date": img.get("startdate", time.strftime("%Y%m%d")),
                        "url": img["url"],
                        "title": img.get("title", "Microsoft Bing Wallpaper (Global)"),
                        "copyright": img.get("copyright", "Microsoft Bing"),
                    }
            except Exception as exc:
                log.debug("Intento %d/%d fallido en API Global BWC: %s", attempt, retries, exc)
                if attempt < retries:
                    time.sleep(delay)
        market = "en-US"

    # API regional de Bing (4K UHD)
    api_url = f"https://www.bing.com/HPImageArchive.aspx?format=js&idx=0&n=1&mkt={market}"
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(api_url, headers=headers)
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                img = data["images"][0]
                date_str = img["startdate"]
                urlbase = img["urlbase"]
                img_url = f"https://www.bing.com{urlbase}_UHD.jpg"
                return {
                    "market": market,
                    "date": date_str,
                    "url": img_url,
                    "title": img.get("title", "Bing Daily Wallpaper"),
                    "copyright": img.get("copyright", "Microsoft Bing"),
                }
        except Exception as exc:
            log.debug("Intento %d/%d fallido en API regional (%s): %s", attempt, retries, market, exc)
            if attempt < retries:
                time.sleep(delay)

    log.warning("Sin conexión a las APIs de Bing para mercado '%s'.", market)
    return None


def fetch_metadata(market: str, retries: int = 3, delay: float = 2.0) -> dict | None:
    """Enrutador principal para consultar metadatos según la fuente elegida."""
    today_str = time.strftime("%Y%m%d")

    if market == "chromecast":
        return fetch_chromecast_metadata(today_str)
    elif market == "wikimedia":
        return fetch_wikimedia_metadata(today_str)
    elif market == "wallhaven":
        return fetch_wallhaven_metadata(today_str)
    else:
        return fetch_bing_metadata(market, retries=retries, delay=delay)


# ---------------------------------------------------------------------------
# Gestión de Caché y Descarga
# ---------------------------------------------------------------------------
def cleanup_old_images(directory: Path, keep: int = MAX_CACHED_IMAGES) -> None:
    dated_files = sorted(directory.glob("bing_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*.jpg"))
    for old_file in dated_files[:-keep]:
        try:
            old_file.unlink()
        except OSError:
            pass


def find_latest_cached_image(preferred_market: str | None = None) -> Path | None:
    """Busca la última imagen descargada en las cachés locales."""
    market_matches: list[Path] = []
    any_matches: list[Path] = []

    clean_mkt = preferred_market.replace("/", "-") if preferred_market else None

    for directory in get_readable_storage_dirs():
        if not directory.exists():
            continue
        for f in directory.glob("bing_[0-9][0-9][0-9][0-9][0-9][0-9][0-9][0-9]*.jpg"):
            if f.is_file() and f.stat().st_size > 10_000:
                any_matches.append(f)
                if clean_mkt and f"_{clean_mkt}" in f.name:
                    market_matches.append(f)

    if market_matches:
        market_matches.sort(key=lambda p: p.name, reverse=True)
        return market_matches[0]

    if any_matches:
        any_matches.sort(key=lambda p: p.name, reverse=True)
        return any_matches[0]

    pkg_img = SYSTEM_IMAGES_DIR / "3840x2160.jpg"
    if pkg_img.is_file() and pkg_img.stat().st_size > 10_000:
        return pkg_img

    return None


def download_or_get_latest_image(market: str = "es-ES", retries: int = 3) -> Path | None:
    """Descarga la imagen del día según la fuente/mercado elegido o devuelve la última en caché."""
    today_str = time.strftime("%Y%m%d")
    concrete_market = get_concrete_market(market, today_str)

    meta = fetch_metadata(concrete_market, retries=retries)
    writable_dirs = get_writable_storage_dirs()

    if meta:
        date_str = meta["date"]
        actual_market = meta["market"]
        filename = f"bing_{date_str}_{actual_market}.jpg"

        existing_source: Path | None = None
        for d in get_readable_storage_dirs():
            candidate = d / filename
            if candidate.is_file() and candidate.stat().st_size > 10_000:
                existing_source = candidate
                break

        if existing_source is None and writable_dirs:
            primary_dir = writable_dirs[0]
            primary_dir.mkdir(parents=True, exist_ok=True)
            target_path = primary_dir / filename
            tmp_path = primary_dir / f".{filename}.tmp"
            try:
                headers = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64; KDE Plasma)"}
                req = urllib.request.Request(meta["url"], headers=headers)
                with urllib.request.urlopen(req, timeout=30) as resp, open(tmp_path, "wb") as out:
                    shutil.copyfileobj(resp, out)
                if tmp_path.stat().st_size > 10_000:
                    os.chmod(tmp_path, 0o644)
                    tmp_path.replace(target_path)
                    existing_source = target_path
                    log.info(
                        "Descargada imagen (%s / %s): %s - %s",
                        actual_market,
                        date_str,
                        meta["title"],
                        meta["copyright"],
                    )
                else:
                    tmp_path.unlink(missing_ok=True)
            except Exception as exc:
                tmp_path.unlink(missing_ok=True)
                log.warning("Error descargando imagen de %s (%s).", actual_market, exc)

        if existing_source is not None:
            for d in writable_dirs:
                d.mkdir(parents=True, exist_ok=True)
                dest = d / filename
                if dest.resolve() != existing_source.resolve() and not dest.exists():
                    try:
                        shutil.copy2(existing_source, dest)
                        os.chmod(dest, 0o644)
                    except OSError:
                        pass
                cleanup_old_images(d)

            if SYSTEM_IMAGES_DIR in writable_dirs:
                pkg_img = SYSTEM_IMAGES_DIR / "3840x2160.jpg"
                try:
                    shutil.copy2(existing_source, pkg_img)
                    os.chmod(pkg_img, 0o644)
                except OSError:
                    pass

            for d in (SYSTEM_CACHE_DIR, SYSTEM_IMAGES_DIR):
                sys_candidate = d / filename
                if sys_candidate.is_file():
                    return sys_candidate
            return existing_source

    latest = find_latest_cached_image(preferred_market=concrete_market)
    if latest:
        log.info("Usando última imagen en caché (%s): %s", concrete_market, latest)
    else:
        log.error("No hay conexión a Internet ni imágenes en caché para %s.", concrete_market)
    return latest


# ---------------------------------------------------------------------------
# Detección de configuración de KDE Plasma y preferencia del usuario
# ---------------------------------------------------------------------------
def normalize_wallpaper_path(uri_or_path: str) -> str:
    val = uri_or_path.strip()
    if val.startswith("file://"):
        val = val[len("file://") :]
    return val.rstrip("/")


def is_bing_wallpaper_path(uri_or_path: str, last_applied: str | None = None) -> bool:
    if not uri_or_path:
        return False
    norm = normalize_wallpaper_path(uri_or_path)
    if last_applied and norm == normalize_wallpaper_path(last_applied):
        return True
    for marker in BING_PATH_MARKERS:
        if marker in norm:
            return True
    if re.search(r"bing_\d{8}.*\.jpg$", norm):
        return True
    return False


def get_current_kde_wallpapers() -> list[tuple[str, str]]:
    results: list[tuple[str, str]] = []

    js_query = (
        "var allDesktops = desktops();"
        "var out = [];"
        "for (var i = 0; i < allDesktops.length; i++) {"
        "  var d = allDesktops[i];"
        "  d.currentConfigGroup = Array('Wallpaper', d.wallpaperPlugin, 'General');"
        "  out.push(d.wallpaperPlugin + ':::' + d.readConfig('Image'));"
        "}"
        "print(out.join('\\n'));"
    )
    for cmd in (
        ["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js_query],
        ["qdbus", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js_query],
    ):
        if shutil.which(cmd[0]):
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0 and ":::" in res.stdout:
                for line in res.stdout.strip().splitlines():
                    if ":::" in line:
                        wplugin, _, img = line.partition(":::")
                        results.append((wplugin.strip(), img.strip()))
                if results:
                    return results
            break

    appletsrc = get_kde_appletsrc_path()
    if not appletsrc.is_file():
        return results

    content = appletsrc.read_text(encoding="utf-8", errors="ignore")

    containment_plugins: dict[str, str] = {}
    containment_images: dict[tuple[str, str], str] = {}

    current_section = ""
    for raw_line in content.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current_section = line[1:-1]
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip()

        m_cont = re.match(r"^Containments\]\[(\d+)$", current_section)
        if m_cont and key == "wallpaperplugin":
            containment_plugins[m_cont.group(1)] = value

        m_wall = re.match(
            r"^Containments\]\[(\d+)\]\[Wallpaper\]\[([^\]]+)\]\[General$",
            current_section,
        )
        if m_wall and key in ("Image", "PreviewImage"):
            cid, wplugin = m_wall.group(1), m_wall.group(2)
            if key == "Image" or (cid, wplugin) not in containment_images:
                containment_images[(cid, wplugin)] = value

    for cid, wplugin in containment_plugins.items():
        img = containment_images.get((cid, wplugin), "")
        if img or wplugin != "org.kde.image":
            results.append((wplugin, img))

    if not results:
        for (cid, wplugin), img in containment_images.items():
            results.append((wplugin, img))

    return results


def should_apply_for_current_user(force_enable: bool = False) -> tuple[bool, str]:
    if force_enable:
        return True, "Reactivado explícitamente por el usuario (--enable o cambio de fuente)."

    state = load_user_state()
    if not state.get("initialized", False):
        return True, "Primera ejecución para este usuario (activo por defecto)."

    last_applied = state.get("last_applied_image")
    wallpapers = get_current_kde_wallpapers()

    if not wallpapers:
        return True, "Configuración de Plasma aún sin fondos personalizados."

    for wplugin, img_path in wallpapers:
        if wplugin == "org.kde.image" and is_bing_wallpaper_path(img_path, last_applied):
            return True, "El usuario mantiene el fondo automático activo."

    return (
        False,
        "El usuario cambió su fondo de pantalla en KDE a otro personalizado; se respeta su elección.",
    )


# ---------------------------------------------------------------------------
# Aplicación del fondo de pantalla en KDE Plasma
# ---------------------------------------------------------------------------
def wait_for_plasmashell(timeout: int = 25) -> bool:
    if not (os.environ.get("DBUS_SESSION_BUS_ADDRESS") or os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        return False

    deadline = time.time() + timeout
    while time.time() < deadline:
        dbus_checked = False
        for cmd in (
            ["gdbus", "call", "--session", "--dest", "org.freedesktop.DBus",
             "--object-path", "/org/freedesktop/DBus", "--method",
             "org.freedesktop.DBus.NameHasOwner", "org.kde.plasmashell"],
            ["dbus-send", "--session", "--dest=org.freedesktop.DBus",
             "--type=method_call", "--print-reply", "/org/freedesktop/DBus",
             "org.freedesktop.DBus.NameHasOwner", "string:org.kde.plasmashell"],
        ):
            if shutil.which(cmd[0]):
                dbus_checked = True
                res = subprocess.run(cmd, capture_output=True, text=True)
                if res.returncode == 0 and "true" in res.stdout.lower():
                    return True
                if res.returncode != 0 and ("cannot autolaunch" in res.stderr.lower() or "failed to connect" in res.stderr.lower()):
                    return False
                break
        if not dbus_checked:
            return False
        time.sleep(1.0)
    return False


def apply_kde_wallpaper(image_path: Path, market_tag: str | None = None) -> bool:
    abs_path = str(image_path.resolve())
    file_uri = f"file://{abs_path}"

    wait_for_plasmashell(timeout=20)
    applied = False

    js_script = (
        "var allDesktops = desktops();"
        "for (var i = 0; i < allDesktops.length; i++) {"
        "  var d = allDesktops[i];"
        "  d.wallpaperPlugin = 'org.kde.image';"
        "  d.currentConfigGroup = Array('Wallpaper', 'org.kde.image', 'General');"
        f"  d.writeConfig('Image', '{file_uri}');"
        "}"
    )

    dbus_commands = [
        [
            "gdbus", "call", "--session", "--dest", "org.kde.plasmashell",
            "--object-path", "/PlasmaShell", "--method",
            "org.kde.PlasmaShell.evaluateScript", js_script,
        ],
        ["qdbus6", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js_script],
        ["qdbus", "org.kde.plasmashell", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript", js_script],
        [
            "dbus-send", "--session", "--dest=org.kde.plasmashell",
            "--type=method_call", "/PlasmaShell", "org.kde.PlasmaShell.evaluateScript",
            f"string:{js_script}",
        ],
    ]

    for cmd in dbus_commands:
        if shutil.which(cmd[0]):
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                applied = True
                break

    if not applied and shutil.which("plasma-apply-wallpaperimage"):
        res = subprocess.run(
            ["plasma-apply-wallpaperimage", abs_path],
            capture_output=True,
            text=True,
        )
        if res.returncode == 0:
            applied = True

    if applied:
        state = load_user_state()
        state.update({
            "initialized": True,
            "last_applied_image": abs_path,
            "updated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        })
        if market_tag:
            state["market"] = market_tag
        save_user_state(state)
        log.info("Fondo de escritorio KDE aplicado: %s", abs_path)
    else:
        log.warning("No se pudo aplicar a plasmashell (¿está la sesión gráfica de KDE abierta?).")
    return applied


# ---------------------------------------------------------------------------
# Gestión de Configuración (Usuario y Sistema)
# ---------------------------------------------------------------------------
def set_user_market(market_str: str) -> int:
    resolved = resolve_market(market_str)
    state = load_user_state()
    state["market"] = resolved
    state["initialized"] = True
    save_user_state(state)
    m_info = AVAILABLE_MARKETS.get(resolved, {"name": resolved, "description": ""})
    print(f"✓ Configuración de usuario actualizada: Fuente/Mercado = {resolved} ({m_info['name']})")

    print("Descargando y aplicando el fondo de esta fuente...")
    img = download_or_get_latest_image(resolved, retries=3)
    if img:
        apply_kde_wallpaper(img, market_tag=resolved)
        print(f"✓ Fondo aplicado correctamente: {img}")
        return 0
    return 1


def set_system_market(market_str: str) -> int:
    if os.geteuid() != 0:
        log.error("Configurar a nivel de sistema requiere permisos de root (usa sudo).")
        return 1
    resolved = resolve_market(market_str)
    SYSTEM_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    cp = configparser.ConfigParser()
    if SYSTEM_CONFIG_PATH.is_file():
        cp.read(SYSTEM_CONFIG_PATH)
    if not cp.has_section("General"):
        cp.add_section("General")
    cp.set("General", "market", resolved)
    with open(SYSTEM_CONFIG_PATH, "w", encoding="utf-8") as f:
        cp.write(f)
    os.chmod(SYSTEM_CONFIG_PATH, 0o644)
    m_info = AVAILABLE_MARKETS.get(resolved, {"name": resolved, "description": ""})
    print(f"✓ Configuración del sistema guardada en {SYSTEM_CONFIG_PATH}:")
    print(f"  Fuente por defecto para todos los usuarios = {resolved} ({m_info['name']})")
    return 0


def print_markets_table() -> None:
    current_user_mkt = load_user_state().get("market")
    system_mkt = None
    if SYSTEM_CONFIG_PATH.is_file():
        try:
            cp = configparser.ConfigParser()
            cp.read(SYSTEM_CONFIG_PATH)
            system_mkt = cp.get("General", "market", fallback=None)
        except Exception:
            pass

    effective = get_effective_market()

    print("\n" + "=" * 85)
    print(" FUENTES Y MERCADOS DISPONIBLES PARA EL FONDO DE ESCRITORIO")
    print("=" * 85)
    print(f"{'Código / Alias':<18} {'Nombre / Fuente':<26} {'Descripción':<30} {'Estado'}")
    print("-" * 85)

    current_group = ""
    for code, info in AVAILABLE_MARKETS.items():
        grp = info.get("group", "")
        if grp != current_group:
            current_group = grp
            print(f"\n--- {current_group.upper()} ---")

        badges = []
        if code == effective:
            badges.append("ACTIVO")
        if code == current_user_mkt:
            badges.append("usuario")
        if code == system_mkt:
            badges.append("sistema")
        badge_str = f"[{' / '.join(badges)}]" if badges else ""
        print(f"{code:<18} {info['name']:<26} {info['description'][:28]:<30} {badge_str}")

    print("\n" + "-" * 85)
    print(f"Fuente actualmente efectiva: {effective}")
    print("\nEjemplos para cambiar:")
    print("  bing-wallpaper-kde --set-source chromecast   # Google Chromecast (Opción 4)")
    print("  bing-wallpaper-kde --set-source wikimedia    # Wikimedia Commons POTD (Opción 5)")
    print("  bing-wallpaper-kde --set-source wallhaven    # Wallhaven Top 4K (Opción 6)")
    print("  bing-wallpaper-kde --set-source global       # Microsoft Bing Global")
    print("  bing-wallpaper-kde --set-source ja-JP        # Bing Japón")
    print("  bing-wallpaper-kde --set-source random       # Aleatorio diario (rota fuentes y países)")
    print("=" * 85 + "\n")


def explore_today_images() -> None:
    """Muestra qué imagen tiene disponible cada fuente hoy en día."""
    sources_to_check = [
        "chromecast",
        "wikimedia",
        "wallhaven",
        "global",
        "es-ES",
        "ja-JP",
        "de-DE",
        "en-US",
    ]
    print("\nConsultando imágenes de hoy en las diferentes fuentes y mercados...\n")
    print(f"{'Fuente/Código':<14} {'Nombre':<24} {'Título de la imagen'}")
    print("-" * 85)
    for s in sources_to_check:
        meta = fetch_metadata(s, retries=1)
        name = AVAILABLE_MARKETS.get(s, {}).get("name", s)
        if meta:
            title = meta.get("title", "")
            if len(title) > 45:
                title = title[:42] + "..."
            print(f"{s:<14} {name:<24} {title}")
        else:
            print(f"{s:<14} {name:<24} (No disponible o sin red)")
    print("-" * 85)
    print("Para aplicar cualquiera de ellos ahora: bing-wallpaper-kde --set-source <código>\n")


def launch_gui_selector() -> int:
    """Abre un diálogo nativo en KDE (kdialog) o menú interactivo para elegir fuente."""
    effective = get_effective_market()

    if shutil.which("kdialog"):
        items: list[str] = []
        for code, info in AVAILABLE_MARKETS.items():
            state = "on" if code == effective else "off"
            label = f"[{info.get('group', '')}] {info['name']} - {info['description'][:38]}"
            items.extend([code, label, state])

        cmd = [
            "kdialog",
            "--radiolist",
            "Selecciona la fuente o país para el fondo de pantalla:",
        ] + items
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            selected = res.stdout.strip()
            return set_user_market(selected)
        return 0

    if shutil.which("zenity"):
        items = []
        for code, info in AVAILABLE_MARKETS.items():
            checked = "TRUE" if code == effective else "FALSE"
            items.extend([checked, code, info["name"], info["description"]])

        cmd = [
            "zenity",
            "--list",
            "--radiolist",
            "--title=Fondo de pantalla",
            "--text=Elige la fuente o país para la imagen del día:",
            "--column=",
            "--column=Código",
            "--column=Fuente/País",
            "--column=Descripción",
        ] + items
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0 and res.stdout.strip():
            selected = res.stdout.strip()
            return set_user_market(selected)
        return 0

    # Menú interactivo en consola si no hay entorno de ventanas
    print("\n--- Selecciona una Fuente o Mercado ---")
    keys = list(AVAILABLE_MARKETS.keys())
    for idx, code in enumerate(keys, 1):
        mark = " (*)" if code == effective else ""
        info = AVAILABLE_MARKETS[code]
        print(f" {idx:2d}) {code:<12} - {info['name']}{mark}")
    try:
        choice = input(f"\nElige una opción (1-{len(keys)}) [Actual: {effective}]: ").strip()
        if not choice:
            return 0
        if choice.isdigit() and 1 <= int(choice) <= len(keys):
            selected = keys[int(choice) - 1]
            return set_user_market(selected)
        else:
            resolved = resolve_market(choice)
            return set_user_market(resolved)
    except (KeyboardInterrupt, EOFError):
        print()
        return 0


# ---------------------------------------------------------------------------
# Instalación a nivel de sistema (todos los usuarios)
# ---------------------------------------------------------------------------
def create_kde_wallpaper_package() -> None:
    SYSTEM_IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    metadata = {
        "KPlugin": {
            "Authors": [{"Name": "Microsoft Bing / KDE Wallpaper"}],
            "Id": "BingDaily",
            "License": "CC0-1.0",
            "Name": "Daily Wallpaper (Bing & Curated)",
            "Name[es]": "Fondo de pantalla diario (Bing y colecciones)",
        }
    }
    metadata_path = SYSTEM_WALLPAPER_PKG_DIR / "metadata.json"
    metadata_path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    os.chmod(metadata_path, 0o644)


def install_system_wide() -> int:
    if os.geteuid() != 0:
        log.error("La instalación a nivel de sistema requiere permisos de root (usa sudo).")
        return 1

    # 1. Copiar script ejecutable en /usr/local/bin
    SYSTEM_BIN_PATH.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(Path(__file__).resolve(), SYSTEM_BIN_PATH)
    os.chmod(SYSTEM_BIN_PATH, 0o755)
    log.info("Script instalado en %s", SYSTEM_BIN_PATH)

    # 2. Configuración global por defecto
    if not SYSTEM_CONFIG_PATH.exists():
        SYSTEM_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        SYSTEM_CONFIG_PATH.write_text(
            "# Configuración global de bing-wallpaper-kde\n[General]\nmarket = es-ES\n",
            encoding="utf-8",
        )
        os.chmod(SYSTEM_CONFIG_PATH, 0o644)

    # 3. Directorio de caché y paquete de fondo para la interfaz de KDE
    SYSTEM_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    os.chmod(SYSTEM_CACHE_DIR, 0o755)
    create_kde_wallpaper_package()
    log.info("Paquete de fondo KDE registrado en %s", SYSTEM_WALLPAPER_PKG_DIR)

    # 4. Servicio y temporizador systemd al arrancar
    service_content = f"""[Unit]
Description=Descargar fondo de pantalla diario al iniciar el equipo
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
ExecStart={SYSTEM_BIN_PATH} --fetch-only
Nice=10
"""
    timer_content = """[Unit]
Description=Actualización diaria del fondo de pantalla

[Timer]
OnBootSec=30sec
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
"""
    SYSTEM_SERVICE_PATH.write_text(service_content, encoding="utf-8")
    SYSTEM_TIMER_PATH.write_text(timer_content, encoding="utf-8")

    subprocess.run(["systemctl", "daemon-reload"], check=False)
    subprocess.run(
        ["systemctl", "enable", "--now", "bing-wallpaper-fetch.timer"], check=False
    )
    log.info("Servicio y timer systemd activados (bing-wallpaper-fetch.timer).")

    # 5. Entrada XDG Autostart para la sesión de cada usuario
    SYSTEM_AUTOSTART_PATH.parent.mkdir(parents=True, exist_ok=True)
    desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Daily Wallpaper (KDE)
Name[es]=Fondo de pantalla diario (KDE)
Comment=Aplica el fondo del día si el usuario no ha cambiado a otro personalizado
Exec={SYSTEM_BIN_PATH} --session
Icon=preferences-desktop-wallpaper
Terminal=false
OnlyShowIn=KDE;
X-KDE-Autostart-Phase=2
"""
    SYSTEM_AUTOSTART_PATH.write_text(desktop_entry, encoding="utf-8")
    os.chmod(SYSTEM_AUTOSTART_PATH, 0o644)

    # 6. Acceso directo en el menú de aplicaciones de KDE
    SYSTEM_MENU_APP_PATH.parent.mkdir(parents=True, exist_ok=True)
    menu_desktop_entry = f"""[Desktop Entry]
Type=Application
Name=Wallpaper Source Selector
Name[es]=Elegir país o fuente de fondo
Comment=Seleccionar la fuente o país del fondo de pantalla (Bing, Chromecast, Wikimedia, Wallhaven)
Exec={SYSTEM_BIN_PATH} --select
Icon=preferences-desktop-wallpaper
Terminal=false
Categories=Settings;DesktopSettings;Qt;KDE;
"""
    SYSTEM_MENU_APP_PATH.write_text(menu_desktop_entry, encoding="utf-8")
    os.chmod(SYSTEM_MENU_APP_PATH, 0o644)
    log.info("Acceso directo añadido al menú de KDE en %s", SYSTEM_MENU_APP_PATH)

    # 7. Descargar la primera imagen para dejar la caché lista
    effective = get_effective_market()
    download_or_get_latest_image(effective, retries=2)
    log.info("Instalación completada con éxito.")
    return 0


def uninstall_system_wide() -> int:
    if os.geteuid() != 0:
        log.error("La desinstalación del sistema requiere permisos de root (usa sudo).")
        return 1

    subprocess.run(
        ["systemctl", "disable", "--now", "bing-wallpaper-fetch.timer"], check=False
    )
    for path in (
        SYSTEM_AUTOSTART_PATH,
        SYSTEM_SERVICE_PATH,
        SYSTEM_TIMER_PATH,
        SYSTEM_BIN_PATH,
        SYSTEM_MENU_APP_PATH,
        SYSTEM_CONFIG_PATH,
    ):
        if path.exists():
            path.unlink()
            log.info("Eliminado %s", path)

    subprocess.run(["systemctl", "daemon-reload"], check=False)
    log.info("Desinstalación completada.")
    return 0


# ---------------------------------------------------------------------------
# Punto de entrada CLI
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fondo de pantalla diario para KDE Plasma (Bing, Chromecast, Wikimedia, Wallhaven y multirregión)."
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--install",
        action="store_true",
        help="Instala a nivel de sistema (systemd + autostart KDE + menú para todos los usuarios).",
    )
    group.add_argument(
        "--uninstall",
        action="store_true",
        help="Desinstala del sistema.",
    )
    group.add_argument(
        "--fetch-only",
        action="store_true",
        help="Solo descarga la imagen en caché compartida (usado por systemd al arrancar).",
    )
    group.add_argument(
        "--session",
        action="store_true",
        help="Ejecuta en la sesión KDE del usuario (comprueba y aplica el fondo si corresponde).",
    )
    group.add_argument(
        "--enable",
        action="store_true",
        help="Fuerza la reactivación del fondo automático para el usuario actual.",
    )
    group.add_argument(
        "--status",
        action="store_true",
        help="Muestra el estado actual del usuario (fuente/mercado activo, última imagen, etc.).",
    )
    group.add_argument(
        "--set-market",
        "--set-source",
        dest="set_market",
        metavar="FUENTE",
        help="Configura la fuente o país (ej. 'chromecast', 'wikimedia', 'wallhaven', 'global', 'ja-JP', 'random').",
    )
    group.add_argument(
        "--set-system-market",
        "--set-system-source",
        dest="set_system_market",
        metavar="FUENTE",
        help="Configura la fuente por defecto para todo el sistema en /etc/bing-wallpaper-kde.conf (requiere sudo).",
    )
    group.add_argument(
        "--list-markets",
        "--list-sources",
        dest="list_markets",
        action="store_true",
        help="Lista todas las fuentes y regiones disponibles con sus códigos y estado.",
    )
    group.add_argument(
        "--today",
        "--explore",
        dest="today",
        action="store_true",
        help="Explora y muestra qué imágenes hay hoy en las distintas fuentes y países.",
    )
    group.add_argument(
        "--select",
        "--gui",
        dest="select",
        action="store_true",
        help="Abre una ventana gráfica interactiva en KDE para elegir la fuente con un click.",
    )

    parser.add_argument(
        "--market",
        "--source",
        dest="market",
        metavar="FUENTE",
        help="Fuente o mercado temporal para esta ejecución (sin guardar como configuración permanente).",
    )

    args = parser.parse_args()

    if args.install:
        return install_system_wide()

    if args.uninstall:
        return uninstall_system_wide()

    if getattr(args, "list_markets", False):
        print_markets_table()
        return 0

    if getattr(args, "today", False):
        explore_today_images()
        return 0

    if getattr(args, "set_market", None):
        return set_user_market(args.set_market)

    if getattr(args, "set_system_market", None):
        return set_system_market(args.set_system_market)

    if getattr(args, "select", False):
        return launch_gui_selector()

    market = get_effective_market(override=args.market)

    if args.fetch_only:
        img = download_or_get_latest_image(market=market, retries=4)
        return 0 if img else 1

    if args.status:
        should_apply, reason = should_apply_for_current_user(force_enable=False)
        latest = find_latest_cached_image(preferred_market=market)
        m_info = AVAILABLE_MARKETS.get(market, {"name": market, "description": ""})
        print(f"Estado para el usuario '{os.environ.get('USER', 'actual')}':")
        print(f"  Fuente/País configurado: {market} ({m_info['name']})")
        print(f"  ¿Aplicar automáticamente?: {'SÍ' if should_apply else 'NO (Desactivado por el usuario)'}")
        print(f"  Motivo: {reason}")
        print(f"  Última imagen en caché: {latest or 'Ninguna'}")
        return 0

    should_apply, reason = should_apply_for_current_user(force_enable=args.enable)
    log.info(reason)
    if not should_apply:
        return 0

    image_path = download_or_get_latest_image(market=market, retries=3)
    if not image_path:
        return 1

    ok = apply_kde_wallpaper(image_path, market_tag=market)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
