# Deploying ACM LetterForge on Oracle Cloud Always Free (Docker)

> **The Docker container is disposable. `/data` is the persistent application data.**
> SQLite + local files are used on purpose, so run exactly **one** container against `/data`. Never scale it out.

```
Internet → HTTPS :443 → Caddy (on the VM) → 127.0.0.1:8000 → LetterForge container (FastAPI + React)
                                                                     │
                                          /opt/letterforge-data  ⇄  /data  (letterforge.db, storage/)
```

## 0. What you need
- An Oracle Cloud Always Free account.
- A hostname that points at the VM (required for HTTPS). Free option: a subdomain from **duckdns.org** (e.g. `acmletters.duckdns.org`).
- Your Groq API key.

## 1. Create the VM
Compute → Instances → Create:
- Image: **Ubuntu 22.04 or 24.04** (aarch64).
- Shape: **VM.Standard.A1.Flex** (Ampere ARM). 2 OCPU / 12 GB is plenty (free limit: 4 OCPU / 24 GB total). If ARM is out of capacity, try again later or use `VM.Standard.E2.1.Micro` (x86, 1 GB, slow but works).
- Boot volume: 50 GB. Add your SSH public key. Note the **public IP**.
- Point your DuckDNS name at that IP.

## 2. Open only ports 80 and 443
**Oracle console:** Networking → your VCN → Security List → add Ingress Rules (source `0.0.0.0/0`, TCP) for ports **80** and **443**. Do **not** open 8000.

**On the VM** (Oracle's Ubuntu images also block traffic with iptables):
```bash
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 80  -j ACCEPT
sudo iptables -I INPUT 6 -m state --state NEW -p tcp --dport 443 -j ACCEPT
sudo apt-get update && sudo apt-get install -y iptables-persistent   # answer Yes to save current rules
sudo netfilter-persistent save
```

## 3. Install Docker
```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
exit    # log out and SSH back in so the group applies
docker --version && docker compose version
```

## 4. Get the code
```bash
sudo mkdir -p /opt/letterforge && sudo chown $USER:$USER /opt/letterforge
git clone https://github.com/hasnainkhan87/acm_letterforge.git /opt/letterforge
cd /opt/letterforge
```
Private repository: use a GitHub personal access token as the password when asked, or add a read-only deploy key.

## 5. Configure
```bash
cp .env.example .env
nano .env
```
Fill in `GROQ_API_KEY`, `GROQ_MODEL` and a strong `APP_PASSWORD`. Leave `DATA_DIR=/opt/letterforge-data` and `BIND_ADDR=127.0.0.1`. `.env` is never committed.

## 6. Create the persistent data folder
```bash
sudo mkdir -p /opt/letterforge-data
sudo chown -R 1000:1000 /opt/letterforge-data     # the container runs as uid 1000 (non-root)
```
Keep this folder on the VM's boot/block volume. It is **not** inside the container and is never touched by rebuilds.

## 7. Start the app
```bash
cd /opt/letterforge
docker compose up -d --build
docker compose ps                  # STATUS should become "healthy" after ~40 s
curl -s http://127.0.0.1:8000/health       # {"status":"ok"}
docker compose logs -f --tail=50           # Ctrl+C to leave
```
First start creates `/opt/letterforge-data/letterforge.db`, the `storage/` folders, and copies the official letterhead templates shipped with the code (existing files are never overwritten).

## 8. HTTPS with Caddy (automatic Let's Encrypt)
```bash
sudo apt-get install -y debian-keyring debian-archive-keyring apt-transport-https curl
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/gpg.key' | sudo gpg --dearmor -o /usr/share/keyrings/caddy-stable-archive-keyring.gpg
curl -1sLf 'https://dl.cloudsmith.io/public/caddy/stable/debian.deb.txt' | sudo tee /etc/apt/sources.list.d/caddy-stable.list
sudo apt-get update && sudo apt-get install -y caddy
```
Replace the contents of `/etc/caddy/Caddyfile` (use your hostname):
```
acmletters.duckdns.org {
    encode gzip
    request_body {
        max_size 12MB
    }
    reverse_proxy 127.0.0.1:8000
}
```
```bash
sudo systemctl reload caddy
```
Open `https://acmletters.duckdns.org`. The browser asks for a username (anything) and your `APP_PASSWORD`. On a phone: browser menu → **Install app / Add to Home screen**.

## 9. Verify
1. Page loads over HTTPS and the password prompt appears.
2. Add a signatory with a signature image, then generate a letter and export **DOCX** and **PDF** (the PDF should show the full letterhead).
3. Persistence check:
   ```bash
   cd /opt/letterforge
   docker compose down && docker compose up -d     # data still there
   docker rm -f letterforge && docker compose up -d   # container replaced, data still there
   ls -la /opt/letterforge-data /opt/letterforge-data/storage
   ```

## 10. Update workflow (safe)
```bash
cd /opt/letterforge
ls -la /opt/letterforge-data/letterforge.db      # confirm the database is present
./scripts/backup.sh                              # optional but recommended
git pull
docker compose build
docker compose up -d
docker image prune -f
```
Rebuilding replaces only the container. `/opt/letterforge-data` is outside it and is never deleted. Do **not** run `docker compose down -v` with a named volume, and never delete `/opt/letterforge-data`.

## 11. Backups
Everything that matters is `/opt/letterforge-data/letterforge.db` and `/opt/letterforge-data/storage/`.

**Manual backup (consistent even while running):**
```bash
cd /opt/letterforge && ./scripts/backup.sh       # → /opt/letterforge-backups/letterforge-<timestamp>.tar.gz (keeps newest 14)
```
**Simple alternative (stop the app first):**
```bash
docker compose stop && sudo tar -czf ~/letterforge-backup.tar.gz -C /opt letterforge-data && docker compose start
```
**Weekly automatic backup (free, stays on the VM):**
```bash
( crontab -l 2>/dev/null; echo "0 3 * * 0 cd /opt/letterforge && ./scripts/backup.sh >> /opt/letterforge-backups/cron.log 2>&1" ) | crontab -
```
**Copy a backup off the VM** (do this regularly; a backup only on the VM dies with the VM):
```bash
scp ubuntu@YOUR_VM_IP:/opt/letterforge-backups/letterforge-*.tar.gz .
```
**Restore:**
```bash
cd /opt/letterforge && docker compose stop
mkdir /tmp/restore && tar -xzf letterforge-YYYYMMDD-HHMMSS.tar.gz -C /tmp/restore
sudo mv /opt/letterforge-data /opt/letterforge-data.before-restore
sudo mkdir -p /opt/letterforge-data
sudo cp /tmp/restore/letterforge.db /opt/letterforge-data/
sudo cp -a /tmp/restore/storage /opt/letterforge-data/
sudo chown -R 1000:1000 /opt/letterforge-data
docker compose up -d
```

## 12. Migrating data from the old Render/Railway deployment
You need a copy of the old `letterforge.db` and the old `storage/` folder (from the old host's shell or volume, or your PC if you ran it locally). Paths inside the database are relative (`signatures/...`, `templates/...`), so they work unchanged.

```bash
# On your PC: upload the files
scp letterforge.db ubuntu@YOUR_VM_IP:/tmp/letterforge.db
scp -r storage ubuntu@YOUR_VM_IP:/tmp/storage-import

# On the VM:
cd /opt/letterforge && docker compose stop
./scripts/backup.sh 2>/dev/null || true                        # back up whatever exists now
if [ -e /opt/letterforge-data/letterforge.db ]; then
  echo "A database already exists. Move the EMPTY first-run one aside (only if you have no real data in it):"
  echo "  sudo mv /opt/letterforge-data/letterforge.db /opt/letterforge-data/letterforge.db.empty"
else
  sudo cp /tmp/letterforge.db /opt/letterforge-data/letterforge.db
fi
sudo mkdir -p /opt/letterforge-data/storage
sudo cp -rn /tmp/storage-import/. /opt/letterforge-data/storage/   # -n: never overwrite existing files
sudo chown -R 1000:1000 /opt/letterforge-data
docker compose up -d
```
Never copy over a database that already holds real data without a backup.

## 13. Troubleshooting
| Symptom | Fix |
|---|---|
| `permission denied` writing `/data` | `sudo chown -R 1000:1000 /opt/letterforge-data` |
| Site does not open | Check both the Oracle security list **and** the iptables rules in step 2; `sudo systemctl status caddy` |
| Caddy cannot get a certificate | The hostname must point at the VM's public IP and ports 80/443 must be open |
| PDF is a plain text layout | LibreOffice failed; `docker compose logs letterforge \| grep "PDF conversion"` |
| AI error 404 | Wrong `GROQ_MODEL`; see console.groq.com/docs/models, edit `.env`, `docker compose up -d` |
| Container `unhealthy` | `docker compose logs --tail=100 letterforge` |

## 14. Limitations
- Single instance by design (SQLite). One VM = one point of failure, so keep off-VM copies of backups.
- Exports are generated on demand from saved letters and are not stored as files (`storage/generated/` is reserved for the future).
- The first build on ARM downloads LibreOffice and takes several minutes.
- One shared password for everyone; there are no per-user accounts yet.
