# Dynamic Daily Wallpaper for KDE Plasma

[![KDE Plasma](https://img.shields.io/badge/KDE-Plasma%205%20%26%206-blue?logo=kde)](https://kde.org/plasma-desktop/)
[![Python 3.9+](https://img.shields.io/badge/Python-3.9%2B-brightgreen?logo=python)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

*Automated 4K UHD daily desktop wallpaper changer for KDE Plasma with multi-source and multi-region support.*

---

**Languages / Idiomas:**  
[🇬🇧 English](#-english) | [🇪🇸 Español](#-español)

---

## 🇬🇧 English

### Overview

**Dynamic Daily Wallpaper for KDE** automatically fetches and applies stunning daily wallpapers in **4K UHD** resolution whenever your system boots or a user logs in.

It works **online and offline**, is enabled by default for all system users, and smartly respects individual choices: if any user manually changes their wallpaper in KDE settings to a personal picture, the script detects it and **will not overwrite** their preference.

### Key Features

* **Multi-Source Catalog:**
  * **Microsoft Bing:** Global 4K feed (`3840×2400`) + 12 regional markets (US, Spain, Japan, Germany, UK, France, Italy, Brazil, China, India, Canada, Australia).
  * **Google Chromecast:** Over 700 curated high-resolution landscape & nature photographs from Google TV.
  * **Wikimedia Commons POTD:** Picture of the Day from Wikipedia and Wikimedia Commons (up to 8K extreme resolution).
  * **Wallhaven (Top 4K):** Highest rated daily wallpapers from the community (100% SFW / Landscapes & Nature).
  * **Daily Random:** Rotates across all sources and countries daily so you discover new photos from around the world without duplicates.
* **Smart Multi-User & Preference Protection:**
  * Active by default across all user accounts upon login.
  * Checks live KDE Plasma desktop containment configurations (`org.kde.plasmashell` via DBus and `plasma-org.kde.plasma.desktop-appletsrc`). If a user selects a custom picture or slideshow, the script automatically backs off.
  * Native KDE Wallpaper Package registered under `/usr/share/wallpapers/BingDaily`, allowing users to restore the daily wallpaper with one click in KDE desktop settings.
* **Offline Fallback:** If internet connection is unavailable at boot, it seamlessly re-applies the latest downloaded image from the shared local cache.
* **KDE GUI Integration:** Includes a native desktop dialog (`kdialog` / `zenity`) accessible from the application launcher menu or terminal.

---

### Supported Sources and Markets

| Code / Alias | Source / Country | Description |
| :--- | :--- | :--- |
| `4`, `chromecast` | **Google Chromecast** | Over 700 curated landscapes from Google TV (4K). |
| `5`, `wikimedia` | **Wikimedia Commons (POTD)** | Picture of the Day from Wikipedia / Wikimedia (up to 8K). |
| `6`, `wallhaven` | **Wallhaven (Top 4K)** | Top community-voted 4K/UHD desktop wallpapers. |
| `global`, `ms` | **Microsoft Bing (Global)** | Official Microsoft Wallpaper feed (`3840×2400` from Azure CDN). |
| `es-ES`, `espana` | **Spain** | Spanish regional feed with localized titles and descriptions. |
| `en-US`, `usa` | **United States / Global** | US international feed in 4K UHD. |
| `ja-JP`, `japon` | **Japan** | Japan-curated regional daily photo (4K UHD). |
| `de-DE`, `alemania` | **Germany** | Germany-curated regional daily photo (4K UHD). |
| `en-GB`, `uk` | **United Kingdom** | UK-curated regional daily photo (4K UHD). |
| `fr-FR`, `francia` | **France** | France-curated regional daily photo (4K UHD). |
| `it-IT`, `italia` | **Italy** | Italy-curated regional daily photo (4K UHD). |
| `pt-BR`, `brasil` | **Brazil** | Brazil-curated regional daily photo (4K UHD). |
| `zh-CN`, `china` | **China** | China-curated regional daily photo (4K UHD). |
| `en-IN`, `india` | **India** | India-curated regional daily photo (4K UHD). |
| `en-CA`, `canada` | **Canada** | Canada-curated regional daily photo (4K UHD). |
| `en-AU`, `australia` | **Australia** | Australia-curated regional daily photo (4K UHD). |
| `random` | **Daily Random** | Rotates daily between different countries and sources. |

---

### Installation

Clone the repository and run the automated installer:

```bash
git clone https://github.com/juananzgz/dynamic-daily-wallpaper-for-kde.git
cd dynamic-daily-wallpaper-for-kde
sudo python3 bing-wallpaper-kde.py --install
```

#### What does the installer do?
1. Installs the executable to `/usr/local/bin/bing-wallpaper-kde`.
2. Creates and enables systemd service & timer (`bing-wallpaper-fetch.timer`) for automatic daily downloads at boot.
3. Configures system-wide XDG Autostart (`/etc/xdg/autostart/bing-wallpaper-kde.desktop`) for KDE Plasma sessions.
4. Registers a native KDE wallpaper package in `/usr/share/wallpapers/BingDaily`.
5. Adds a launcher entry in the KDE Application Menu (**"Choose Wallpaper Source"**).
6. Creates `/etc/bing-wallpaper-kde.conf` for default system-wide configuration.

---

### Usage & Commands

```bash
# 1. Preview today's pictures across sources and countries
bing-wallpaper-kde --today

# 2. Change wallpaper source or country (for current user)
bing-wallpaper-kde --set-source 4            # Google Chromecast
bing-wallpaper-kde --set-source 5            # Wikimedia Commons POTD
bing-wallpaper-kde --set-source 6            # Wallhaven Top 4K
bing-wallpaper-kde --set-source global       # Microsoft Bing Global (3840x2400)
bing-wallpaper-kde --set-source japon        # Bing Japan
bing-wallpaper-kde --set-source alemania     # Bing Germany
bing-wallpaper-kde --set-source random       # Surprise daily rotation

# 3. Open the native KDE graphical selector
bing-wallpaper-kde --select

# 4. Check status for the current user
bing-wallpaper-kde --status

# 5. Re-enable automatic wallpaper (after changing to a personal photo)
bing-wallpaper-kde --enable

# 6. List all available sources and active status
bing-wallpaper-kde --list-sources

# 7. Set default source system-wide for all users (requires sudo)
sudo bing-wallpaper-kde --set-system-source chromecast
```

---

### Uninstallation

To remove all services, timers, shortcuts, and scripts from the system:

```bash
sudo bing-wallpaper-kde --uninstall
```

---

<br>

## 🇪🇸 Español

### Descripción General

**Dynamic Daily Wallpaper for KDE** descarga y aplica automáticamente fondos de pantalla diarios en resolución **4K UHD** cada vez que el equipo arranca o un usuario inicia sesión en **KDE Plasma (Plasma 5 y Plasma 6)**.

Funciona de forma **online y offline**, viene activado por defecto para todos los usuarios del sistema y respeta la elección individual: si cualquier usuario cambia su fondo desde las preferencias de KDE por una foto personal, el script lo detecta y **no lo sobrescribe**.

### Características Destacadas

* **Catálogo Multifuente:**
  * **Microsoft Bing:** Feed oficial Global (`3840×2400`) y 12 mercados regionales (España, Japón, Alemania, EE.UU., Reino Unido, Francia, Italia, Brasil, China, India, Canadá, Australia).
  * **Google Chromecast:** Más de 700 fotografías seleccionadas de viajes, naturaleza y arquitectura de Google TV en 4K.
  * **Wikimedia Commons POTD:** Imagen del día de Wikipedia y Wikimedia Commons (hasta 8K de resolución extrema).
  * **Wallhaven (Top 4K):** Los mejores fondos del día votados por la comunidad de Wallhaven (*SFW* / Paisajes y Naturaleza).
  * **Aleatorio diario:** Rota entre todas las fuentes y países cada día para descubrir fotografías de todo el mundo sin repetir.
* **Soporte Multiusuario y Protección de Personalización:**
  * Activo por defecto para todas las cuentas de usuario al iniciar sesión.
  * Comprueba la configuración de escritorio en vivo de KDE (`org.kde.plasmashell` vía DBus y `plasma-org.kde.plasma.desktop-appletsrc`). Si el usuario cambia a una foto propia o presentación, el script se desactiva solo sin machacar su fondo.
  * Paquete de fondo de pantalla nativo registrado en `/usr/share/wallpapers/BingDaily`, permitiendo reactivarlo con un solo clic en los ajustes de escritorio de KDE.
* **Modo Offline:** Si el equipo arranca sin conexión a Internet, aplica la última foto guardada en la caché local.
* **Integración Gráfica con KDE:** Incluye un selector gráfico (`kdialog` / `zenity`) accesible desde el menú de aplicaciones de KDE o por consola.

---

### Fuentes y Mercados Disponibles

| Código / Alias | Fuente / País | Descripción |
| :--- | :--- | :--- |
| `4`, `chromecast` | **Google Chromecast** | Más de 700 paisajes de Google TV y Chromecast en 4K. |
| `5`, `wikimedia` | **Wikimedia Commons (POTD)** | Imagen del día de Wikipedia / Wikimedia (hasta 8K). |
| `6`, `wallhaven` | **Wallhaven (Top 4K)** | Los mejores fondos panorámicos 4K/UHD de la comunidad. |
| `global`, `ms` | **Microsoft Bing (Global)** | API oficial de Microsoft Wallpaper (`3840×2400` desde Azure CDN). |
| `es-ES`, `espana` | **España** | Fondo oficial para España con títulos y descripciones en español (4K). |
| `en-US`, `usa` | **Estados Unidos / Global** | Catálogo internacional de EE.UU. en 4K UHD. |
| `ja-JP`, `japon` | **Japón** | Fondo diario seleccionado para Japón (4K UHD). |
| `de-DE`, `alemania` | **Alemania** | Fondo diario seleccionado para Alemania (4K UHD). |
| `en-GB`, `uk` | **Reino Unido** | Fondo diario seleccionado para Reino Unido (4K UHD). |
| `fr-FR`, `francia` | **Francia** | Fondo diario seleccionado para Francia (4K UHD). |
| `it-IT`, `italia` | **Italia** | Fondo diario seleccionado para Italia (4K UHD). |
| `pt-BR`, `brasil` | **Brasil** | Fondo diario seleccionado para Brasil (4K UHD). |
| `zh-CN`, `china` | **China** | Fondo diario seleccionado para China (4K UHD). |
| `en-IN`, `india` | **India** | Fondo diario seleccionado para India (4K UHD). |
| `en-CA`, `canada` | **Canadá** | Fondo diario seleccionado para Canadá (4K UHD). |
| `en-AU`, `australia` | **Australia** | Fondo diario seleccionado para Australia (4K UHD). |
| `random` | **Aleatorio diario** | Rota de país y fuente cada día automáticamente. |

---

### Instalación

Clona el repositorio y ejecuta el instalador automático:

```bash
git clone https://github.com/juananzgz/dynamic-daily-wallpaper-for-kde.git
cd dynamic-daily-wallpaper-for-kde
sudo python3 bing-wallpaper-kde.py --install
```

#### ¿Qué hace el instalador?
1. Instala el ejecutable en `/usr/local/bin/bing-wallpaper-kde`.
2. Crea y activa el servicio y temporizador de systemd (`bing-wallpaper-fetch.timer`) para actualizar el fondo diariamente al arrancar con red.
3. Configura la entrada global XDG Autostart (`/etc/xdg/autostart/bing-wallpaper-kde.desktop`) para sesiones de KDE.
4. Registra el paquete nativo de fondo de KDE en `/usr/share/wallpapers/BingDaily`.
5. Añade un acceso directo en el menú de aplicaciones de KDE (**"Elegir país o fuente de fondo"**).
6. Crea el archivo de configuración global `/etc/bing-wallpaper-kde.conf`.

---

### Guía de Uso y Comandos

```bash
# 1. Ver qué imágenes hay hoy en las diferentes fuentes y países
bing-wallpaper-kde --today

# 2. Cambiar de fuente o país (para tu usuario)
bing-wallpaper-kde --set-source 4            # Google Chromecast
bing-wallpaper-kde --set-source 5            # Wikimedia Commons POTD
bing-wallpaper-kde --set-source 6            # Wallhaven Top 4K
bing-wallpaper-kde --set-source global       # Microsoft Bing Global (3840x2400)
bing-wallpaper-kde --set-source japon        # Bing Japón
bing-wallpaper-kde --set-source alemania     # Bing Alemania
bing-wallpaper-kde --set-source random       # Sorpresa diaria

# 3. Abrir el selector gráfico nativo en KDE
bing-wallpaper-kde --select

# 4. Ver el estado del usuario actual
bing-wallpaper-kde --status

# 5. Volver a activar el fondo automático (tras haber puesto un fondo personal)
bing-wallpaper-kde --enable

# 6. Listar todas las fuentes y comprobar cuál está activa
bing-wallpaper-kde --list-sources

# 7. Cambiar la fuente por defecto para todo el equipo (requiere sudo)
sudo bing-wallpaper-kde --set-system-source chromecast
```

---

### Desinstalación

Para retirar todos los servicios, accesos directos y scripts del sistema:

```bash
sudo bing-wallpaper-kde --uninstall
```

---

## License / Licencia

MIT License © 2026 Juanan ([@juananzgz](https://github.com/juananzgz)).
See [LICENSE](LICENSE) for more details.
