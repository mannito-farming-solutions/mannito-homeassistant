# Mannito für Home Assistant

Diese Integration holt eine Mannito-Platine (Grow-Controller) über die Mannito-Cloud in Home Assistant. Du siehst die Sensoren,
das Klima und die Bewässerung deiner Grow-Bereiche, schaltest Lampe, Lüfter, Steckdosen und Ventile und änderst Klimaregelung und
Bewässerung. Die Platine regelt weiterhin selbst. Home Assistant liest mit und greift nur ein, wenn du es willst.

## Voraussetzungen

- Home Assistant 2026.9 oder neuer
- eine Mannito-Platine, die in der Mannito-Cloud eingerichtet ist
- ein **API-Token** dieser Platine

### API-Token erstellen

1. In der Mannito-Cloud die Seite der Platine öffnen.
2. In der Karte **„API-Zugänge“** auf **„Token erstellen“** klicken. Nur Admins der Organisation sehen diese Karte.
3. Einen Namen vergeben, zum Beispiel „Home Assistant“, und die Rechte wählen:
   - **Lesen** ist immer dabei: alle Werte und Zustände.
   - **Steuern**: Geräte von Hand schalten, zurück auf Automatik, Ventile kurz öffnen.
   - **Konfigurieren**: Grow-Bereich an oder aus, Klimaregelung, Bewässerung, Wachstumsphase, Firmware der Platine.
4. Den Token kopieren. Er beginnt mit `mnt_` und wird **nur einmal** angezeigt.

Ein Token gilt nur für **eine** Platine. Für andere Platinen und für die KI-Schnittstelle (MCP) taugt er nicht. In der Karte
siehst du, wann ein Token zuletzt benutzt wurde, und kannst ihn jederzeit widerrufen.

## Installation

### Manuell (solange das Repository privat ist)

1. Den Ordner `custom_components/mannito` nach `config/custom_components/mannito` deiner Home-Assistant-Installation
   kopieren, zum Beispiel mit dem File-Editor- oder Samba-Add-on.
2. Home Assistant neu starten.

### Über HACS / Marketplace (sobald das Repository öffentlich ist)

1. In HACS oder im Marketplace dieses Repository als benutzerdefiniertes Repository vom Typ „Integration“ hinzufügen.
2. **Mannito** installieren und Home Assistant neu starten.

### Einrichten

**Einstellungen → Geräte & Dienste → Integration hinzufügen → Mannito**, dann eingeben:

| Feld | Bedeutung |
| --- | --- |
| Cloud-Adresse | Adresse der Mannito-Cloud, meist `https://mannito.de` |
| API-Token | der Token der Platine (`mnt_…`) |

Die Integration prüft den Token sofort. Jede Platine wird ein eigener Eintrag. Cloud-Adresse und Token lassen sich später über
**„Neu konfigurieren“** ändern. Trägst du dort einen neuen Token ein, widerruft die Integration den alten in der Cloud. Wird ein
Token widerrufen oder läuft er ab, fragt Home Assistant von selbst nach einem neuen.

## Was in Home Assistant erscheint

Die Platine ist ein Gerät. Darunter hängen je ein Gerät pro Grow-Bereich und pro Bus-Modul, zum Beispiel das VPD-Modul.

**Platine**
- Online-Status, letzter Kontakt, offene Änderungen
- alle Sensoren der Platine und der Bus-Module mit ihrem Namen aus der Cloud
- Ausgänge (mit dem Recht **Steuern**):
  - Lampe als Licht, dimmbar mit 0–10-V-Kanal
  - Lüfter mit Drehzahl in Prozent
  - Steckdosen und Relais als Schalter
  - Magnetventile als Ventil
- je Ausgang eine Taste **„… Automatik“** (gibt ihn an die Regelung zurück) und ein Diagnose-Sensor **„… Handbetrieb“**
- Firmware-Update der Platine; Installieren nur mit dem Recht **Konfigurieren**

**Grow-Bereich**
- Klima: Temperatur, Luftfeuchte, VPD, Blatttemperatur, CO₂ (falls vorhanden), Zuluft, dazu die Sollwerte
- Status (in Ordnung, Achtung, Problem …), Tag/Nacht, Notbetrieb
- Wachstumsphase, Tag des Grows, Tag der Phase
- Bewässerung: Phase P0–P3, Substratfeuchte, Tageshoch, Dryback, Shots und Wasser pro Topf heute, letzter und nächster Shot,
  Feldkapazität, Tankinhalt und -füllstand
- **Kalender „Wachstumsphasen“**: abgeschlossene, laufende und geplante Phasen des Grow-Zyklus
- mit dem Recht **Konfigurieren**:
  - **Sollwerte der laufenden Phase**: Tag-/Nacht-Temperatur, VPD Tag/Nacht (oder Luftfeuchte), Lichtstärke, Umluft, CO₂
  - **Licht an** als Uhrzeit, der ganze Tag des Grow-Zyklus verschiebt sich mit
  - Taste **„Feldkapazität aus aktuellem Wert“**, nach dem Durchnässen und Abtropfen drücken
  - Schalter **„Regelung“**
  - Auswahl **Klimaregelung** (Fuzzy, Fuzzy + PI, MPC), **Bewässerung** (Aus, Zeitplan, Dryback) und **Dryback-Steuerung**
  - Zahlenfelder für alle Dryback-Werte und die Tageslimits

**Pflanzen**: Jede Pflanze, die in einem Grow-Bereich steht, ist ein eigenes Gerät, zum Beispiel „Green Poison #3“. Sie hat:
- **Höhe** (letzte Messung, in cm) und wann zuletzt gemessen wurde
- **Alter** in Tagen, **Sorte**, **Standort** (Topf/Abschnitt und Platz)

Der Grow-Bereich zeigt die Zahl der **offenen Probleme** seiner Pflanzungen.

Schaltest du einen Ausgang, zeigt Home Assistant den neuen Zustand sofort an. Die Platine bestätigt ihn wenige Sekunden später.

Neue Ausgänge, Sensoren, Grow-Bereiche, Pflanzen und Bus-Module erscheinen von selbst. Was du in der Cloud löschst oder ausblendest,
verschwindet wieder, ebenso geerntete Pflanzen. Hat ein neuer Token weniger Rechte, entfernt die Integration die Schalter und
Einstellungen, die er nicht mehr darf. Es bleiben keine Entitäten „nicht mehr verfügbar“ zurück.

## Die Mannito-Karte

Die Integration bringt eine eigene Dashboard-Karte mit. Sie lädt automatisch, eine Ressource musst du nicht anlegen. Eine Karte
zeigt einen Grow-Bereich auf drei Reitern:

- **Übersicht**
  - Zeitachse der Wachstumsphasen mit „Heute“-Markierung
  - Klima gegen Soll (Temperatur, Feuchte, VPD, CO₂) mit Abweichungsanzeige, Blatt und Zuluft
  - Substratfeuchte auf einer Skala mit Tageshoch, Feldkapazität, P2-Auslöser und Notfall-Grenze
  - Shots und Wasser heute, Dryback, nächster oder letzter Shot, Tankfüllstand
  - Tankbuch mit einem Klick: nachgefüllt, frisch angemischt, Füllstand (Liter)
  - Taste „Ventile 10 s“
- **Pflanzen**
  - jede Pflanze mit Höhe, Alter und wann zuletzt gemessen
  - Höhe eintragen und Beobachtungen festhalten, wahlweise als Problem
- **Geräte**
  - die Geräte des Bereichs mit Schieber (dimmbare Lampe, Lüfter), Schalter oder „10 s öffnen“ (Ventile)
  - Hinweis „Hand“ bei Handbetrieb und eine Automatik-Taste je Gerät
- **Einstellungen**
  - Sollwerte der Phase (Licht an, Temperaturen, VPD, Lichtstärke, Umluft)
  - Regelung, Klimaregelung, Bewässerung, Dryback-Steuerung und alle Dryback-Werte, Feldkapazität messen
  - Grow-Zyklus: Licht-an-Zeit, Verschieben, nächste Phase, Phase bestätigen
  - Firmware der Platine

So fügst du sie hinzu: Dashboard bearbeiten → **Karte hinzufügen → „Mannito Grow-Bereich“** und den Grow-Bereich wählen. In YAML:

```yaml
type: custom:mannito-card
device: <Geräte-ID des Grow-Bereichs>
show_all_devices: false   # true: auch Ausgänge der Platine, die dem Bereich nicht zugeordnet sind
```

Was ein Token nicht darf, zeigt die Karte nicht an. Ohne das Recht **Konfigurieren** fehlt der Reiter „Einstellungen“. Ohne
das Recht **Steuern** sind die Geräte nur zu sehen, nicht zu schalten.

## Aktionen

| Aktion | Zweck |
| --- | --- |
| `mannito.open_valve` | Ein Ventil 1–60 Sekunden öffnen. Danach schließt es von selbst. |
| `mannito.run_valves` | Alle Ventile eines Grow-Bereichs nacheinander öffnen: Sekunden (Durchfluss messen) oder ml pro Topf (Test-Shot). Jedes Ventil höchstens 60 Sekunden. |
| `mannito.grow_cycle_action` | Phase bestätigen, nächste Phase starten, Phase verschieben, Licht-an-Zeit setzen, CO₂ an oder aus |
| `mannito.record_measurement` | Messung einer Pflanze eintragen: Höhe (cm), Stammdicke, Blattgröße, Gewicht, Optik, Farbe |
| `mannito.record_note` | Beobachtung zu einer Pflanze eintragen, wahlweise als offenes Problem |
| `mannito.tank_entry` | Tankbuch: frisch angemischt, nachgefüllt, entnommen, Füllstand geprüft (Liter) |
| `mannito.tank_reading` | EC, pH oder Temperatur im Tank eintragen |

Messung und Beobachtung nehmen eine Pflanze. Hat ein Grow-Bereich nur eine Pflanzung, geht auch der Grow-Bereich, dann gilt der
Eintrag für alle seine Pflanzen. Einträge brauchen das Recht **Steuern**.

### Beispiele

Benachrichtigung bei Notbetrieb:

```yaml
automation:
  - alias: "Zelt im Notbetrieb"
    triggers:
      - trigger: state
        entity_id: binary_sensor.green_poison_notbetrieb
        to: "on"
    actions:
      - action: notify.mobile_app_handy
        data:
          message: "Das Zelt läuft im Notbetrieb – bitte nachsehen."
```

Höhe jeden Sonntag per Benachrichtigung abfragen und eintragen lassen (Beispiel mit festem Wert):

```yaml
action: mannito.record_measurement
data:
  target: <Geräte-ID der Pflanze>
  measurement: height
  value: 42
```

Tank fast leer:

```yaml
automation:
  - alias: "Tank nachfüllen"
    triggers:
      - trigger: numeric_state
        entity_id: sensor.green_poison_tankinhalt
        below: 2
    actions:
      - action: notify.mobile_app_handy
        data:
          message: "Im Tank sind nur noch {{ states('sensor.green_poison_tankinhalt') }} l."
```

## Wie die Daten kommen

Home Assistant fragt die Cloud alle **30 Sekunden** ab, nach einer Einstellung sofort und nach einem Schaltbefehl nach wenigen
Sekunden, sobald die Platine ihn bestätigt hat. Die Platine meldet ihre Werte etwa einmal pro
Minute an die Cloud. Ein Wert kann also bis zu anderthalb Minuten alt sein.

## Grenzen

- Ein Befehl von Hand nimmt den Ausgang aus der Automatik, bis du **„… Automatik“** drückst. Das ist dasselbe Verhalten wie in der
  Cloud.
- Ventile öffnen aus Home Assistant **höchstens 60 Sekunden**. So kann eine fehlerhafte Automation das Zelt nicht fluten.
- Bus-Module (zum Beispiel das VPD-Modul) bekommen aus Home Assistant **keine** Firmware. Das geht nur über die Cloud oder per USB.
- Ein Grow-Zyklus lässt sich aus Home Assistant nicht beenden. Das geht nur auf der Seite des Grow-Bereichs.
- Lichter eines blühenden Grow-Bereichs lehnt die Platine in der geschützten Nacht ab.
- Ohne Internet bleibt die Platine handlungsfähig, Home Assistant sieht dann aber nichts mehr.

## Fehlersuche

| Meldung | Ursache und Abhilfe |
| --- | --- |
| „Der Token ist unbekannt, widerrufen oder abgelaufen“ | In der Cloud einen neuen Token erstellen und über die Reparatur-Meldung eintragen. |
| „Dem API-Token fehlt das Recht dafür“ | Einen Token mit dem Recht **Steuern** oder **Konfigurieren** erstellen und über „Neu konfigurieren“ eintragen. |
| „Die Mannito-Cloud hat abgelehnt: …“ | Die Cloud nennt den Grund, zum Beispiel Platine offline oder Ventil länger als 60 s. |
| „Zu viele Anfragen“ in den Protokollen | Ein Token darf 120 Anfragen pro Minute stellen. Mehrere Home-Assistant-Installationen mit demselben Token teilen sich das; gib jeder ihren eigenen Token. |
| Ein Sensor der Platine zeigt „Unbekannt“ | Sein letzter Wert ist älter als 15 Minuten: Sonde abgesteckt oder Bus-Modul offline. |
| Alle Entitäten nicht verfügbar | Platine offline oder Cloud nicht erreichbar. Den Online-Status der Platine prüfen. |

Für Fehlerberichte bitte die **Diagnose** des Eintrags herunterladen. Sie enthält keinen Token.

## Entfernen

**Einstellungen → Geräte & Dienste → Mannito → ⋮ → Löschen.** Dabei passiert von selbst:

- Geräte und Entitäten der Platine verschwinden aus Home Assistant.
- Die Integration widerruft ihren Token in der Cloud; unter **„API-Zugänge“** steht er danach als widerrufen. War die Cloud
  gerade nicht erreichbar, steht ein Hinweis im Protokoll. Dann den Token dort von Hand widerrufen.
- Nach der letzten Platine lädt Home Assistant die Mannito-Karte nicht mehr. Dashboards, auf denen sie noch liegt, zeigen dort
  einen Fehler, bis du die Karte aus dem Dashboard nimmst.

Bei manueller Installation zum Schluss den Ordner `custom_components/mannito` löschen und Home Assistant neu starten; über HACS
die Integration dort entfernen.

Willst du die Platine wieder hinzufügen, erstelle in der Cloud einen neuen Token: der alte ist widerrufen.

## Entwicklung

```bash
# Tests in Linux (Home Assistant läuft nicht unter Windows)
docker run --rm -v "$PWD:/src" -w /src python:3.14-slim sh -c \
  "pip install -q uv && uv pip install --system -q -r requirements_test.txt && pytest"
```

Die Texte liegen in `script/translations.py`. Danach `python script/translations.py custom_components/mannito` ausführen; das
erzeugt `strings.json`, `translations/en.json` und `translations/de.json`.
