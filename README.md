# motion-checker

Execute InfluxQL query and notify to Telegram chat 

## Environment

```
nano secret.env
```

```env
INFLUXDB_URL=http://INFLUX_HOST:8086
INFLUXDB_TOKEN=A_LONG_STRING_HERE
INFLUXDB_ORG=sample
INFLUXDB_BUCKET=mqtt

TELEGRAM_BOT_TOKEN=TELEGRAM_TOKEN_HERE
TELEGRAM_CHAT_ID=CHAT_ID_HERE

```


## Systemd unit

```bash
sudo tee /etc/systemd/system/motion-checker.service > /dev/null << 'EOF' && sudo systemctl daemon-reload && sudo systemctl enable motion-checker.service --now && systemctl status motion-checker.service
[Unit]
Description=Motion Checker
After=network-online.target docker.service
Wants=network-online.target

[Service]
Type=oneshot
User=superadmin
Group=superadmin
WorkingDirectory=/opt/motion-checker/
ExecStart=/opt/motion-checker/venv/bin/python /opt/motion-checker/main.py

[Install]
WantedBy=multi-user.target

EOF
```


```bash
sudo tee /etc/systemd/system/motion-checker.timer > /dev/null << 'EOF' && sudo systemctl daemon-reload && sudo systemctl enable motion-checker.timer --now && systemctl list-timers --all
[Unit]
Description=Start motion-checker

[Timer]
OnCalendar=11:00
OnCalendar=11:30
OnCalendar=11:45
OnCalendar=12:00

Unit=motion-checker.service
RandomizedDelaySec=3m

[Install]
WantedBy=timers.target

EOF
```


