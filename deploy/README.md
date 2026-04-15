# Anomyze Deployment-Vorlagen

Dieses Verzeichnis enthält die Bausteine, die auf einer Behörden-Zielmaschine
um den gehärteten Anomyze-Container herum installiert werden müssen, damit er
tatsächlich produktionsreif betrieben werden kann. Jede Datei ist **eine
Vorlage** — ENV-Variablen und Platzhalter (`{{…}}`) müssen durch die
Betriebsmannschaft ersetzt werden.

## Layer-Übersicht

```
     +---------------------------+
     | Endbenutzer (Behörde)     |
     +---------------------------+
                 | HTTPS (TLS 1.3)
                 v
     +---------------------------+
     | nginx / Traefik           |  deploy/nginx/anomyze.conf
     | - TLS-Terminierung        |
     | - Client-Cert optional    |
     +---------------------------+
                 | HTTP
                 v
     +---------------------------+
     | oauth2-proxy              |  deploy/oauth2-proxy/config.cfg
     | - OIDC gegen Portalverbund|
     | - Bearer-Token an Upstream|
     +---------------------------+
                 | HTTP
                 v
     +---------------------------+
     | Anomyze Container         |  docker-compose.yml
     | - read_only, cap_drop ALL |
     | - nur 127.0.0.1 hört      |
     +---------------------------+
```

Neben der Request-Kette laufen:

* **systemd-Timer** für Retention + Audit-Backup (`deploy/systemd/`)
* **Prometheus-Scraper** auf `/metrics`
* **Log-Ingestion** (Loki / Graylog) aus stdout

## Komponenten

| Datei | Zweck |
|---|---|
| `env/anomyze.env.example` | Alle ENV-Vars mit Default + Empfehlung |
| `nginx/anomyze.conf` | Reverse-Proxy, TLS-Terminierung |
| `oauth2-proxy/config.cfg` | OIDC-Middleware gegen Portalverbund / Keycloak |
| `systemd/anomyze-retention.*` | Täglicher Retention-Cron (Art. 5 DSGVO) |
| `systemd/anomyze-audit-backup.*` | Täglicher GPG-verschlüsselter Audit-Backup |
| `scripts/backup-audit.sh` | Backup-Skript (wird vom Timer gerufen) |
| `scripts/restore-audit.sh` | Restore inkl. Retention-Reenforcement |

## Minimaler Rollout-Ablauf

1. Linux-Host vorbereiten (RHEL 9 / Ubuntu 22.04 LTS, ≥ 16 vCPU / 32 GB RAM).
2. Docker + docker-compose-plugin installieren.
3. Anomyze-Repo klonen, `config/model_hashes.json` committet lassen.
4. Modelle prefetchen (`scripts/prefetch_models.py`) — ggf. in einem Build-Host
   mit Internet-Zugang; danach `~/.cache/huggingface` auf Zielhost kopieren.
5. `.env` aus `deploy/env/anomyze.env.example` ableiten, Secrets (GPG-Key,
   OIDC-Secret, Model-Revision-SHAs) füllen.
6. Reverse-Proxy-Konfig (`deploy/nginx/anomyze.conf`) mit TLS-Zertifikat
   und Hostname anpassen.
7. oauth2-proxy-Konfig (`deploy/oauth2-proxy/config.cfg`) mit OIDC-Issuer,
   Client-ID/-Secret füllen.
8. systemd-Timer installieren (`sudo cp deploy/systemd/*.{service,timer}
   /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl
   enable --now anomyze-retention.timer anomyze-audit-backup.timer`).
9. `docker compose up -d` auf Zielhost.
10. Prometheus-Scrape-Target anpassen, Grafana-Dashboard importieren.
11. DSB-Abnahme: DPIA, AVV, ROPA (siehe `docs/compliance/`) freigeben.

## Was NICHT hier ist

Keine Entscheidungen, die der betreibenden Behörde obliegen:

* TLS-Zertifikate (interne CA / Let's-Encrypt? — extern)
* OIDC-Provider-Konfiguration (Portalverbund, Keycloak, andere?)
* Backup-Ziel (NAS-Pfad, Retention der Sicherungen)
* Monitoring-Stack (Prometheus-Instanz, Dashboards, Alerts — Behörden-intern)
* Rechtliche Freigaben (Compliance-Dokumente sind Templates in `docs/compliance/`)
