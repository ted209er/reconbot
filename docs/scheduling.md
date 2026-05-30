# Scheduling Reconbot

Reconbot does not run as a daemon. Use your operating system scheduler to run
the normal CLI command on a cadence.

Always schedule Reconbot only for domains you own or have explicit written
authorization to test.

## Command Shape

Use absolute paths so scheduled jobs do not depend on your interactive shell:

```bash
cd /home/user/Repos/reconbot
.venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name daily
```

`--run-name` is optional metadata stored with the run and shown in reports. Use
short names such as `daily`, `weekly`, or `bug-bounty-baseline`.

## Cron

Edit your crontab:

```bash
crontab -e
```

Run every day at 02:00:

```cron
0 2 * * * cd /home/user/Repos/reconbot && .venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name daily >> logs/scheduled.log 2>&1
```

Run every Sunday at 03:30:

```cron
30 3 * * 0 cd /home/user/Repos/reconbot && .venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name weekly >> logs/scheduled.log 2>&1
```

## Systemd Timer

Create `~/.config/systemd/user/reconbot-example.service`:

```ini
[Unit]
Description=Reconbot scheduled run for example.com

[Service]
Type=oneshot
WorkingDirectory=/home/user/Repos/reconbot
ExecStart=/home/user/Repos/reconbot/.venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name daily
```

Create `~/.config/systemd/user/reconbot-example.timer`:

```ini
[Unit]
Description=Run Reconbot daily for example.com

[Timer]
OnCalendar=*-*-* 02:00:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable the timer:

```bash
systemctl --user daemon-reload
systemctl --user enable --now reconbot-example.timer
systemctl --user list-timers
```

Check logs:

```bash
journalctl --user -u reconbot-example.service
```

## WSL Guidance

For WSL Ubuntu, keep the repo under the Linux filesystem, such as
`~/Repos/reconbot`, and schedule from inside WSL.

Use cron in WSL for simple local scheduling:

```bash
sudo service cron start
crontab -e
```

Example:

```cron
0 2 * * * cd /home/user/Repos/reconbot && .venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name wsl-daily >> logs/scheduled.log 2>&1
```

If WSL is not running at the scheduled time, the job will not run. For more
reliable scheduling on Windows, use Windows Task Scheduler to start WSL and run
the command:

```powershell
wsl.exe -d Ubuntu --cd /home/user/Repos/reconbot -- .venv/bin/reconbot --domain example.com --config configs/default.yaml --run-name daily
```

## Troubleshooting

- Use absolute paths in scheduled commands.
- Confirm `.venv` exists before scheduling: `make check-venv`.
- Confirm external tools are visible to non-interactive shells: `which subfinder`.
- Redirect cron output to a log file under `logs/`.
- Run the exact scheduled command manually before enabling the schedule.
