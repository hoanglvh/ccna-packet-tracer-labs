# Lab 06 – End Device and Server Settings

| Device | Mode | IPv4 | Mask | Gateway | DNS |
|--------|------|------|------|---------|-----|
| Admin-PC | Static | 192.168.99.10 | 255.255.255.0 | 192.168.99.1 | 203.0.113.10 |
| PC1, PC2 | DHCP (from R1) | 192.168.10.11+ | | 192.168.10.1 | 203.0.113.10 |
| Guest-Laptop | DHCP (from Int-Server) | 192.168.20.11+ | | 192.168.20.1 | 203.0.113.10 |
| Int-Server | Static | 192.168.30.10 | 255.255.255.0 | 192.168.30.1 | 203.0.113.10 |
| Internet-Web | Static | 203.0.113.10 | 255.255.255.0 | 203.0.113.1 | 203.0.113.10 |
| Rogue-DHCP (Part 2 only) | Static | 192.168.10.250 | 255.255.255.0 | – | – |

## Server services
- **Internet-Web:** HTTP On; DNS On with A record `www.ccna-lab.com → 203.0.113.10`.
- **Int-Server:** HTTP On (index.html text: "Welcome to the CCNA Lab intranet"); DHCP On with pool `GUEST-POOL` (gateway 192.168.20.1, DNS 203.0.113.10, start 192.168.20.11, mask 255.255.255.0, max 100 users).
- **Rogue-DHCP:** removed at the end of Part 2.
