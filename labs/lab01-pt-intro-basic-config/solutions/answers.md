# Lab 01 – Answer Key

## Part 2, Step 5 (values depend on PT version)
- IOS: `C2960 Software (C2960-LANBASEK9-M), Version 15.0(2)SE4` (typical), image `c2960-lanbasek9-mz.150-2.SE4.bin`.
- 2960-24TT: 24 FastEthernet ports + 2 GigabitEthernet ports.

## Part 4, Step 6 (Simulation)
At R1 the **source and destination MAC addresses** are rewritten (new Layer 2 frame for the next segment: R1 G0/0/1 MAC → PC2 MAC). **Source and destination IP addresses stay the same**; only the TTL is decremented (and the header checksum recalculated).

## Challenge
1. `line console 0` → `exec-timeout 3 0`.
2. On S2:
   ```
   access-list 10 permit 192.168.10.0 0.0.0.255
   line vty 0 15
    access-class 10 in
   ```
3. `show version` (uptime, "System returned to ROM by...") and `show running-config` header (`! Last configuration change at ...` – shown when the clock is set).

## Review Questions
1. `enable password` is stored in plaintext (or weak type 7 with `service password-encryption`); `enable secret` is stored as a one-way hash (type 5/8/9). If both exist, `enable secret` wins.
2. The SVI is a host interface; to reply to management traffic from other subnets the switch needs to know where to send packets that are not local – the default gateway. Layer 2 switches do not route, so they don't use a routing table for this.
3. `running-config` is the active configuration in RAM (lost on power off). `startup-config` is stored in NVRAM and loaded at boot. Save with `copy running-config startup-config`.
4. SSH encrypts the entire session (including passwords); Telnet sends everything in clear text. Before `crypto key generate rsa` you need a non-default **hostname** and an **ip domain-name**. For `login local` you need at least one **local username**; SSH v2 also requires a key ≥ 768 bits.
5. The Layer 2 source/destination MAC addresses changed (each Ethernet segment uses a new frame). The IP addresses did not change, because Layer 3 addressing is end-to-end.
6. `L` = local route: a /32 host route for the IP address configured on the router's own interface.
