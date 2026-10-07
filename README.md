# CDN Page Scanner

Scannt öffentlich erreichbare Seiten nach dem Schema:

https://cigaedu22.github.io/g{g}/class-{c}/

- g: 5-100
- class: 1-1000
- maximal 96.000 Kombinationen
- prüft nur HTTP 2xx
- liest den HTML-`<title>`
- sucht nicht nach iframe/embed-Inhalten
- speichert als normale TXT-Liste
- speichert regelmäßig Zwischenstände
- setzt nach einem Abbruch mit `gefunden_partial.txt` fort

## Codespaces

```bash
python3 main.py
```

Abbrechen mit `Ctrl+C`. Der aktuelle Stand wird trotzdem gespeichert.

Keine externen Python-Pakete erforderlich.
