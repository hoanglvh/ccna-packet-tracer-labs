# Lab 02 – Answer Key

## Part 1, Step 1

| Prefix | Subnet mask | Wildcard | Block size | Usable hosts |
|--------|-------------|----------|------------|--------------|
| /24 | 255.255.255.0 | 0.0.0.255 | 256 (4th octet) | 254 |
| /25 | 255.255.255.128 | 0.0.0.127 | 128 | 126 |
| /26 | 255.255.255.192 | 0.0.0.63 | 64 | 62 |
| /27 | 255.255.255.224 | 0.0.0.31 | 32 | 30 |
| /28 | 255.255.255.240 | 0.0.0.15 | 16 | 14 |
| /29 | 255.255.255.248 | 0.0.0.7 | 8 | 6 |
| /30 | 255.255.255.252 | 0.0.0.3 | 4 | 2 |
| /23 | 255.255.254.0 | 0.0.1.255 | 2 (3rd octet) | 510 |
| /20 | 255.255.240.0 | 0.0.15.255 | 16 (3rd octet) | 4094 |

## Part 1, Step 2

| # | Address | Network | First host | Last host | Broadcast | Hosts |
|---|---------|---------|-----------|-----------|-----------|-------|
| 1 | 192.168.100.77/27 | 192.168.100.64 | .65 | .94 | .95 | 30 |
| 2 | 192.168.1.200/26 | 192.168.1.192 | .193 | .254 | .255 | 62 |
| 3 | 172.30.1.33/30 | 172.30.1.32 | .33 | .34 | .35 | 2 |
| 4 | 172.16.35.123/20 | 172.16.32.0 | 172.16.32.1 | 172.16.47.254 | 172.16.47.255 | 4094 |
| 5 | 10.10.10.10/14 | 10.8.0.0 | 10.8.0.1 | 10.11.255.254 | 10.11.255.255 | 262 142 |

## Part 1, Step 3
1. Borrow 3 bits → **/27** (2³ = 8 subnets ≥ 6), 30 hosts each: 192.168.50.0/27, 192.168.50.32/27, 192.168.50.64/27.
2. 500 hosts → **/23** (510 hosts). 2 hosts → **/30** (or /31 on point-to-point links, RFC 3021).
3. **No.** With /25 the block size is 128: .100 is in 10.1.1.0/25, .130 is in 10.1.1.128/25.
4. 4 × /26 in a /24; 16 × /30 in a /26.

## Part 2 – VLSM
See the table in the `<details>` block of the lab guide. Free space after the design: 192.168.1.228 – 192.168.1.255.

## Part 5 – Troubleshooting faults (how to find them)
| Fault | Symptom | Detection |
|-------|---------|-----------|
| F1 | PC-B can't reach PC-A or PC-C: it treats all of 192.168.1.0/24 as local and ARPs for them instead of using its gateway | `ipconfig` on PC-B |
| F2 | LAN-C can't reach anything beyond R2 | `show ip route` on R2 – no `S*` |
| F3 | PC-C can't leave its LAN | `ipconfig` on PC-C vs. `show ip int brief` on R2 |
| F4 | R1–R2 ping fails (different subnets); R1's static route via .226 is withdrawn because the next hop is no longer on a connected subnet | `show ip int brief`, `show ip route` |
| F5 | IPv6 SLAAC on PC-C fails, IPv6 transit through R2 fails | `show running-config \| include ipv6 unicast` |
| F6 | LAN-B unreachable | `show ip int brief` → `administratively down` |

## Challenge – LAN-D (10 hosts)
- Use **192.168.1.240/28** (14 hosts; .232/29 only gives 6). R2 G0/0/1 = 192.168.1.241, a PC = 192.168.1.254.
- IPv6: R2 G0/0/1 `2001:db8:acad:d::1/64`, `fe80::2 link-local`.
- R1: `ip route 192.168.1.240 255.255.255.240 192.168.1.226` and `ipv6 route 2001:db8:acad:d::/64 2001:db8:acad:ff::2`.
  (Alternative: replace both IPv4 routes on R1 with a summary `ip route 192.168.1.192 255.255.255.192 192.168.1.226` – the connected /30 is more specific and still wins.)
- R2 needs no change (it already has a default route).

## Review Questions
1. Large subnets have the strictest boundaries (a /25 must start at .0 or .128). Allocating them first prevents small subnets from fragmenting the space and leaves contiguous free blocks.
2. LAN-A 126 − 100 = 26; LAN-B 62 − 50 = 12; LAN-C 30 − 20 = 10; WAN 2 − 2 = 0. Using /25 everywhere would need 4 × 128 = 512 addresses – it doesn't even fit in a /24.
3. Link-local addresses (FE80::/10) are used for communication on a single link: Neighbor Discovery, Router Advertisements, routing protocol neighbors and as the default-gateway address. Routers never forward packets with a link-local source or destination to another link.
4. Only with `ipv6 unicast-routing` does the router join FF02::2 and send Router Advertisements containing the prefix that hosts use for SLAAC.
5. CDP is Cisco proprietary and enabled by default; LLDP (IEEE 802.1AB) is vendor-neutral and disabled by default on Cisco devices (`lldp run`). Both are Layer 2 discovery protocols.
6. The first packet waits for ARP resolution (on PC-A for its gateway, and on R1/R2 for the next hop and destination); the ping timeout expires before ARP completes.
