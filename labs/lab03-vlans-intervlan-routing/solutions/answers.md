# Lab 03 – Answer Key

## Part 3, Step 6
A packet from PC3 (VLAN 10) to PC2 (VLAN 20) crosses the S1–R1 trunk **twice**: once up tagged VLAN 10, once back down tagged VLAN 20. This "hairpin" is why Router-on-a-Stick is bandwidth-limited.

## Part 5 – Fault diagnosis
| Fault | Symptom | Command | Fix |
|-------|---------|---------|-----|
| F1 | PC4 can't reach its gateway / anything | `show vlan brief` on S2 | `switchport access vlan 20` on F0/11 |
| F2 | PC5 isolated | `show interfaces trunk` – VLAN 30 missing on S1 Fa0/1 | `switchport trunk allowed vlan add 30` |
| F3 | `%CDP-4-NATIVE_VLAN_MISMATCH` messages | `show interfaces trunk` (native 1 vs 1000) | `switchport trunk native vlan 1000` |
| F4 | VLAN 20 hosts can't reach gateway | `show running-config | include encapsulation` on R1 | `encapsulation dot1Q 20` |
| F5 | PC4 isolated, F0/11 missing from `show vlan brief` | `show interfaces f0/11 switchport` → "Access Mode VLAN: 20 (Inactive)" | `vlan 20` → `name ENGINEERING` |
| F6 | No inter-VLAN routing at all | `show interfaces trunk` – G0/1 missing | `switchport mode trunk` + native/allowed settings |
| F7 | PC6 ↔ PC7 fails, gateways pingable | `show ip route` – "IP routing not enabled" | `ip routing` |

## Challenge
1. On **S1 and S2**: `vlan 40` / `name GUEST`. S1 F0/20: `switchport mode access`, `switchport access vlan 40`, `no shutdown`. On every trunk (S1 F0/1, S1 G0/1, S2 F0/1): `switchport trunk allowed vlan add 40`. On R1:
   ```
   interface g0/0/1.40
    encapsulation dot1Q 40
    ip address 192.168.40.1 255.255.255.0
   ```
   (VLAN 40 only needs to exist on S2 if S2 should forward it; adding it on both keeps the databases consistent.)
2. On S3: `interface vlan 10` → `ip address 172.16.10.11 255.255.255.0` → `no shutdown`; `ip default-gateway 172.16.10.1`.

## Review Questions
1. Smaller broadcast domains (better performance), improved security (segmentation by function), easier management/flexibility (users grouped logically regardless of location), cost reduction.
2. Attacks such as double-tagging rely on the attacker's access VLAN being the trunk's native VLAN (VLAN 1 by default). A dedicated, unused native VLAN defeats this. `nonegotiate` disables DTP so an attacker cannot negotiate a trunk (switch spoofing).
3. They are placed in the trunk's **native VLAN**.
4. ROAS: cheap (one router port), but all inter-VLAN traffic shares one link and is routed in software – suitable for small networks. L3 switch: routing in hardware at wire speed, many SVIs, no single link bottleneck, scales to enterprise; higher cost.
5. Create the SVIs (`interface vlan X` + IP + `no shutdown`, with the VLAN existing and an active port in it) and `ip routing`. `no switchport` converts a switch port into a Layer 3 routed port.
6. The physical interface carries tagged frames for several VLANs; IP addresses belong on the subinterfaces, one per VLAN. (An IP on the physical interface would belong to the untagged/native VLAN – here we use a native subinterface without IP instead.)
