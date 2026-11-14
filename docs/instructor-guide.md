# Instructor Guide

## 1. Session Timing (5 × 45 min)

Each lab guide is written so that **one Part ≈ one period**. A suggested breakdown for every period:

| Minutes | Activity |
|---------|----------|
| 0 – 5 | Recap / short theory reminder (use the 💡 boxes in the guide) |
| 5 – 35 | Students work through the Steps |
| 35 – 42 | Checkpoint verification – walk around and check ✅ items |
| 42 – 45 | Save `.pkt`, quick Q&A |

> 💡 Ask students to save a separate file at the end of each period (`lab03-p2.pkt`, ...). If a file becomes corrupted or a student falls behind, they can restart from the previous period, or you can share your reference file.

## 2. Building Reference Files Quickly

Each `solutions/` folder contains the **final running configuration** for every device. To create a reference `.pkt`:

1. Build the topology from the lab guide.
2. Open each device's CLI, enter `enable` → `configure terminal`, and paste the configuration.
3. Configure end devices by hand (IP Configuration dialog).
4. `copy running-config startup-config` on each device.

> ⚠️ Commands such as `crypto key generate rsa` are interactive in some versions. The solution files use the non-interactive form `crypto key generate rsa general-keys modulus 1024`.

## 3. Grading Rubric (per lab, 10 points)

| Criterion | Points | Full marks when… |
|-----------|--------|------------------|
| Topology & cabling | 1 | Correct devices, ports and cable types; labels match the guide |
| Addressing | 1 | All interfaces/end devices match the addressing table |
| Core configuration | 4 | All required features configured as specified |
| Verification | 2 | All ✅ checkpoints pass; evidence included in report |
| Challenge task | 1 | Challenge completed and explained |
| Review questions | 1 | Correct, concise answers |

## 4. Most Common Student Mistakes

| Lab | Symptom | Usual cause |
|-----|---------|-------------|
| All | Configuration lost after closing PT | Did not save `.pkt` (or `copy run start` for device restarts) |
| All | Router interface red | Forgot `no shutdown` |
| All | `Translating "xyz"...domain server` | Typo in EXEC mode, `no ip domain-lookup` missing |
| 1 | Cannot SSH | Missing `ip domain-name`, RSA key < 768 bits, `login local` without a username |
| 2 | Hosts can ping gateway but not remote LAN | Missing/incorrect static route, wrong mask |
| 2 | IPv6 ping fails between routers | `ipv6 unicast-routing` missing |
| 3 | PC can't reach other VLAN | Subinterface `encapsulation dot1Q` VLAN ID mismatch; trunk doesn't allow VLAN |
| 3 | Native VLAN mismatch messages | Native VLAN configured on only one side of the trunk |
| 3 | 3650 won't power on | AC power supply module not inserted |
| 4 | EtherChannel stays down (`SD`/`s`) | Mismatched modes (passive+passive, auto+auto) or mismatched port settings |
| 4 | Port goes err-disabled | BPDU Guard / port security violation – `shutdown` then `no shutdown` |
| 5 | OSPF neighbors not forming | Mismatched area, subnet, hello/dead timers, or passive interface on the link |
| 5 | Default route not propagated | `default-information originate` missing or no default route on that router |
| 6 | Clients get 169.254.x.x | DHCP pool network wrong, helper-address missing, DHCP snooping trust missing |
| 6 | NAT not translating | `ip nat inside/outside` on the wrong interfaces; ACL doesn't match inside hosts |
| 6 | ACL blocks everything | Forgot implicit `deny any`; wrong direction; wrong wildcard mask |

## 5. Using the Troubleshooting Sections

Each lab's Part 5 contains a fault list. For extra difficulty, the instructor can secretly introduce 2–3 faults from that list into a student's working file, then ask them to find and fix the faults within 20 minutes using only `show` commands.
