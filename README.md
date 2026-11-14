# CCNA Hands-On Labs with Cisco Packet Tracer

A complete, step-by-step **practical lab course** for the Cisco CCNA (200-301) curriculum, built entirely on **Cisco Packet Tracer**.

| Item | Value |
|------|-------|
| Number of sessions | **6** |
| Periods per session | **5** (1 period = 45 minutes) |
| Total practical periods | **30** |
| Tool | Cisco Packet Tracer 8.2 or later |
| Language | English |
| Level | CCNA (beginner → intermediate) |

---

## Course Map

| Session | Lab | Topics | Periods |
|---------|-----|--------|---------|
| 1 | [Lab 01 – Packet Tracer Intro & Basic Device Configuration](labs/lab01-pt-intro-basic-config/README.md) | Packet Tracer UI, cabling, IOS CLI modes, hostname, passwords, banner, SVI, router interfaces, SSH | 1 – 5 |
| 2 | [Lab 02 – IPv4 Subnetting, VLSM & IPv6 Addressing](labs/lab02-ipv4-subnetting-ipv6/README.md) | Subnetting, VLSM design, IPv4 & IPv6 interface addressing, SLAAC, CDP/LLDP, ARP, ping/traceroute | 6 – 10 |
| 3 | [Lab 03 – VLANs, Trunking & Inter-VLAN Routing](labs/lab03-vlans-intervlan-routing/README.md) | VLAN creation, access ports, 802.1Q trunks, native VLAN, DTP, Router-on-a-Stick, Layer 3 switch SVIs | 11 – 15 |
| 4 | [Lab 04 – STP, EtherChannel & Port Security](labs/lab04-stp-etherchannel-port-security/README.md) | PVST+/Rapid PVST+, root bridge election, PortFast, BPDU Guard, LACP/PAgP EtherChannel, port security | 16 – 20 |
| 5 | [Lab 05 – Static Routing & Single-Area OSPFv2](labs/lab05-static-routing-ospf/README.md) | Routing table, static/default/floating routes, OSPFv2 single area, router ID, passive interfaces, cost, DR/BDR | 21 – 25 |
| 6 | [Lab 06 – DHCP, NAT, ACLs & Capstone](labs/lab06-dhcp-nat-acl-capstone/README.md) | DHCPv4 server & relay, DHCP snooping, static NAT, PAT, standard & extended ACLs, final assessment | 26 – 30 |

See [SYLLABUS.md](SYLLABUS.md) for the full period-by-period plan.

---

## Repository Structure

```
ccna-packet-tracer-labs/
├── README.md                     ← you are here
├── SYLLABUS.md                   ← 30-period schedule, outcomes, assessment
├── docs/
│   ├── packet-tracer-quickstart.md   ← install & UI tour
│   ├── ios-command-cheatsheet.md     ← most-used IOS commands
│   ├── lab-report-template.md        ← template students submit
│   └── instructor-guide.md           ← timing, grading rubric, common errors
└── labs/
    ├── lab01-pt-intro-basic-config/
    │   ├── README.md             ← step-by-step lab guide
    │   ├── images/topology.svg   ← Packet-Tracer-style topology diagram
    │   └── solutions/            ← final device configs + answer key
    ├── lab02-ipv4-subnetting-ipv6/
    ├── lab03-vlans-intervlan-routing/
    ├── lab04-stp-etherchannel-port-security/
    ├── lab05-static-routing-ospf/
    └── lab06-dhcp-nat-acl-capstone/

tools/generate_topologies.py      ← regenerates every labs/*/images/topology.svg
tools/verify_solutions.py         ← offline simulator that checks every solution config
```

Each lab guide contains:

1. **Objectives** and required devices
2. **Topology diagram** (Packet-Tracer-style device icons, ports, cables, link lights) and **addressing table**
3. **Five periods**, each split into numbered *Parts* and *Steps* with exact commands
4. **Verification** commands with the expected output to look for
5. **Troubleshooting** tips and a **challenge** task
6. **Review questions** (answers in `solutions/answers.md`)

---

## How to Use This Repository

### Students

1. Install Packet Tracer (see [docs/packet-tracer-quickstart.md](docs/packet-tracer-quickstart.md)).
2. Open the lab guide for the current session and **build the topology yourself** – this is part of the learning.
3. Type every command by hand. Do not copy/paste from the solutions folder.
4. Save your work frequently as `labXX-<your-name>.pkt`.
5. Fill in the [lab report template](docs/lab-report-template.md) and submit it with your `.pkt` file.

### Instructors

- Read [docs/instructor-guide.md](docs/instructor-guide.md) for timing, grading rubric, and the most common student mistakes.
- Final configurations for every device are in each lab's `solutions/` folder. You can paste them into a device's CLI to build a reference `.pkt` quickly.
- After editing a solution, run `python3 tools/verify_solutions.py` (or e.g. `python3 tools/verify_solutions.py 6` for one lab). It rebuilds each topology offline and simulates VLANs, trunks, EtherChannel, STP root election, static routing, OSPF, NAT/PAT, ACLs, DHCP and SSH, then runs the connectivity tests promised by the guides. It does not replace a final check in Packet Tracer (it cannot detect commands that a specific PT version rejects).

---

## Conventions Used in the Guides

| Convention | Meaning |
|------------|---------|
| `R1>` / `R1#` / `R1(config)#` | The prompt shows which device and which mode you must be in |
| **Bold** | Something you click in the Packet Tracer GUI |
| `monospace` | Commands you type |
| ✅ | Checkpoint – verify before you continue |
| ⚠️ | Common mistake / warning |
| 💡 | Tip or background theory |

Default lab credentials (lab use only – never in production):

| Purpose | Value |
|---------|-------|
| Console / VTY password | `cisco` |
| Enable secret | `class` |
| Local SSH user | `admin` / `Cisco123!` |
| Domain name | `ccna-lab.com` |

---

## Device Models

All labs use models available in every Packet Tracer 8.x installation:

| Role | Model | Interfaces used |
|------|-------|-----------------|
| Router | **ISR4331** | `G0/0/0`, `G0/0/1`, `G0/0/2` |
| Access switch | **2960-24TT** | `F0/1-24`, `G0/1-2` |
| Multilayer switch | **3650-24PS** | `G1/0/1-24` (needs a power supply module – see Lab 3) |
| End devices | PC-PT, Server-PT, Laptop-PT | `Fa0` |

### Tested in Packet Tracer 8.2.2

Every command in the `solutions/` configs (plus the challenge and `show` commands used in the guides) was pasted into a real ISR4331, 2960-24TT and 3650-24PS in Packet Tracer 8.2.2. Commands that PT 8.2.2 rejects were removed or replaced, and the guides point them out:

| Rejected by PT 8.2.2 | Used instead |
|----------------------|--------------|
| `ip route <net> <mask> <interface> <next-hop>` (fully specified) | next-hop static route |
| `switchport trunk encapsulation dot1q` on the 3650 | `switchport mode trunk` alone |
| `lease` in a DHCP pool, `errdisable recovery ...` | omitted (mentioned as real-IOS only) |
| `show vlans`, `show interfaces description`, `show ip dhcp server statistics`, `show mac address-table vlan N`, `show interfaces status err-disabled` | equivalent commands that PT supports |
| `\| include` after most `show` commands | full output (pipes work after `show running-config`) |

> 💡 If your Packet Tracer version uses a different router model (e.g. 2911 with `G0/0`, `G0/1`, `G0/2`), simply replace the interface names.
