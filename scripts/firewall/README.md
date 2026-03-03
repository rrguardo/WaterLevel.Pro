# Firewall automation scripts (VPS host)

These scripts are intended for the VPS host firewall (`firewalld`), not inside Docker containers.

## Scripts

- `sync_cloudflare_firewalld.sh`
  - Syncs Cloudflare IPv4/IPv6 ranges into host `firewalld` ipsets.
  - Restricts inbound `80/443` to Cloudflare ranges.
  - Keeps `22` open.

- `install_cloudflare_firewalld_timer.sh`
  - Installs a weekly `systemd` timer to re-run Cloudflare IP sync.

- `install_fail2ban_ssh_firewalld.sh`
  - Installs and configures `fail2ban` for SSH brute-force protection using `firewalld` actions.
  - Default behavior: ban after `4` failed attempts within `10m`, for `24h`.

## Typical usage

```bash
sudo bash scripts/firewall/sync_cloudflare_firewalld.sh --zone public
sudo bash scripts/firewall/install_cloudflare_firewalld_timer.sh --zone public
sudo bash scripts/firewall/install_fail2ban_ssh_firewalld.sh --maxretry 4 --findtime 10m --bantime 24h
```

## Optional ICMP hardening

```bash
sudo firewall-cmd --permanent --zone=public --add-rich-rule='rule protocol value=icmp drop'
sudo firewall-cmd --permanent --zone=public --add-rich-rule='rule protocol value=ipv6-icmp drop'
sudo firewall-cmd --reload
```

## Verification

```bash
firewall-cmd --zone=public --list-rich-rules
systemctl status wlp-cloudflare-firewall-sync.timer --no-pager
systemctl status wlp-cloudflare-firewall-sync.service --no-pager
fail2ban-client status sshd
```
