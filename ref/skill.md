# Claude-Skill "swb-buchsuche"

Persoenlicher Claude-Code-Skill, der Literaturanfragen in natuerlicher Sprache
("such mir ein Buch zu X", "welche Bibliothek hat Y") ueber die global
installierte `swb`-CLI beantwortet.

- **Datei**: `~/.claude/skills/swb-buchsuche/SKILL.md` (nicht Teil dieses Repos)
- **Vorlage**: aufgebaut nach dem Muster des cinemaquery-Skills (CLI-Tool +
  Workflow + Trigger in der description)
- **Voraussetzung**: `swb` global via `uv tool install` (liegt in `~/.local/bin`)

## Was der Skill aktuell macht

### Trigger
Fragen nach Buechern/Literatur zu einem Thema, Verfuegbarkeit in Bibliotheken,
ISBN/ISSN-Lookups, aktuelle Neuerscheinungen.

### Workflow (in dieser Reihenfolge)

1. **Grundsuche**: `swb -q search "<Begriffe>" --max 10`, bei aktueller
   Literatur mit `--sort-by year`. Da das SRU-Relevanzranking schwach ist,
   werden bei duennen Treffern 2-3 Query-Varianten probiert (Synonyme,
   deutsch/englisch); Freitext funktioniert besser als `--index title` bei
   Mehrwort-Phrasen.
2. **Gezielte Suche**: `swb -q isbn/issn <Nr>`, `--index author|subject`,
   `swb -q scan "pica.tit=<Praefix>"` fuers Browsing.
3. **Katalogwahl**: Default SWB; `--profile k10plus` fuer bundesweite Treffer,
   `--profile dnb` fuer die Nationalbibliografie (seit dem Fix in ca00130
   funktionsfaehig: MARC21-xml-Schema + WOE/TIT/PER/SW/NUM-Indizes).
4. **Verfuegbarkeit**: `--holdings` liefert die Library-Spalte, die der Skill
   so interpretiert:
   - `Name (DE-xxx)` — verifizierte Bibliothek
   - `Onleihe (DE-M504xxx)` — digitale Ausleihe
   - `Kostenfreie elektronische Ressource (LFER)` — Open Access
   - nackter Code — unbekannt, ISIL-Lookup unter sigel.staatsbibliothek-berlin.de
   Bei Plattform-Detailfragen (z.B. PDF-Download ja/nein) wird zusaetzlich die
   Access-URL ausgewertet: `learning.oreilly.com` = Streaming ohne PDF-Export,
   ProQuest/ebcentral = begrenzter PDF-Download mit DRM.
5. **Aufbereitung**: kompakte Markdown-Tabellen (Titel, Autor, Jahr, ISBN,
   OPAC-Link), thematisch gruppiert; Verfuegbarkeit nach Zugangsart sortiert
   (Open Access, dann Onleihe, dann Print); Antwort in der Sprache des Users,
   keine Emojis.

### Ergaenzende Wege ausserhalb der CLI

- **VLB** hat keine offene SRU-Schnittstelle; Lieferbarkeitsfragen beantwortet
  der Skill per Web-Recherche (z.B. utb.de, Verlagsseiten, buchhandel.de).
- Lokale Kontexte (User an der Uni Stuttgart): Hinweise auf Katalog plus
  (https://rds-stg.ibs-bw.de/opac/), WLB Stuttgart, Fernleihe,
  Anschaffungsvorschlag.

## Bisher bewaehrte Einsatzfaelle (aus realen Sessions)

| Anfrage | Vorgehen |
|---------|----------|
| "Buch zum Thema Making" | Freitext-Varianten, Treffer "Handbuch Fab Labs" (Open Access via LFER) |
| "Literatur zu ADHS" | Freitext + `--sort-by year`, thematisch gruppierte Auswahl |
| "Verfuegbarkeit von X" | `isbn --holdings` in SWB + K10plus, Zugangsart-Gruppierung |
| "Python und KI" | Zwei parallele Query-Varianten (deutsch/englisch) |
| "Gibt es PDF-Download?" | Access-URLs der Holdings auswerten (O'Reilly vs. ProQuest) |

## Wartung

- Nach Aenderungen am swb-Code: `uv tool install --force /Users/java/src_own/swb`
  (steht auch im Skill selbst) — sonst nutzt der Skill eine veraltete Version.
- Skill-Aenderungen: direkt `~/.claude/skills/swb-buchsuche/SKILL.md` editieren;
  neue Sessions laden ihn automatisch.
