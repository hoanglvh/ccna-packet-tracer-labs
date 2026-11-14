# Syllabus – CCNA Practical Labs (30 Periods)

## Course Information

- **Format:** 6 practical sessions × 5 periods (45 min each) = 30 periods (22.5 hours)
- **Environment:** Cisco Packet Tracer 8.2+
- **Prerequisites:** Basic computer skills; OSI/TCP-IP model theory; binary ↔ decimal conversion
- **Alignment:** Cisco CCNA 200-301 exam topics (Network Fundamentals, Network Access, IP Connectivity, IP Services, Security Fundamentals)

## Learning Outcomes

By the end of the course students will be able to:

1. Build, cable and document a small enterprise network in Packet Tracer.
2. Perform initial and secure (SSH) configuration of Cisco routers and switches.
3. Design an IPv4 VLSM addressing plan and configure IPv4 and IPv6 interfaces.
4. Segment a LAN with VLANs and 802.1Q trunks and route between VLANs.
5. Build a redundant, loop-free Layer 2 network using STP and EtherChannel, and secure access ports.
6. Configure static, default, floating static and single-area OSPFv2 routing.
7. Provide IP services (DHCPv4, NAT/PAT) and filter traffic with ACLs.
8. Verify and troubleshoot every technology above using `show`, `debug`, `ping` and `traceroute`.

---

## Period-by-Period Plan

### Session 1 – Packet Tracer Intro & Basic Device Configuration

| Period | Content | Lab Part |
|--------|---------|----------|
| 1 | Packet Tracer interface, device library, cabling, Simulation mode | Part 1 |
| 2 | Cisco IOS CLI: modes, help, editing keys, `show` commands | Part 2 |
| 3 | Basic switch config: hostname, passwords, banner, SVI, save | Part 3 |
| 4 | Basic router config: interfaces, descriptions; PC addressing; end-to-end ping | Part 4 |
| 5 | Secure remote access with SSH; backup configs; challenge | Part 5 |

### Session 2 – IPv4 Subnetting, VLSM & IPv6 Addressing

| Period | Content | Lab Part |
|--------|---------|----------|
| 6 | Subnetting drill (paper + calculator-free) | Part 1 |
| 7 | VLSM design for a given scenario; build topology | Part 2 |
| 8 | Configure and verify the IPv4 VLSM plan; static routes preview | Part 3 |
| 9 | IPv6 addressing: GUA, link-local, SLAAC, IPv6 static routes | Part 4 |
| 10 | Verification tools: CDP, LLDP, ARP, IPv6 neighbors, ping, traceroute; troubleshooting | Part 5 |

### Session 3 – VLANs, Trunking & Inter-VLAN Routing

| Period | Content | Lab Part |
|--------|---------|----------|
| 11 | Create and name VLANs; assign access ports | Part 1 |
| 12 | 802.1Q trunks, native VLAN, allowed VLANs, DTP | Part 2 |
| 13 | Router-on-a-Stick inter-VLAN routing | Part 3 |
| 14 | Inter-VLAN routing with a Layer 3 switch (SVIs, `ip routing`) | Part 4 |
| 15 | Troubleshooting VLAN/trunk faults; review | Part 5 |

### Session 4 – STP, EtherChannel & Port Security

| Period | Content | Lab Part |
|--------|---------|----------|
| 16 | Observe PVST+: root bridge, port roles and states | Part 1 |
| 17 | Tune STP: root primary/secondary, cost, Rapid PVST+, PortFast, BPDU Guard | Part 2 |
| 18 | EtherChannel: LACP and PAgP; verification | Part 3 |
| 19 | Port security: max MAC, sticky, violation modes; unused ports | Part 4 |
| 20 | Layer 2 troubleshooting challenge; review | Part 5 |

### Session 5 – Static Routing & Single-Area OSPFv2

| Period | Content | Lab Part |
|--------|---------|----------|
| 21 | Build topology; read the routing table; connected & local routes | Part 1 |
| 22 | Static, default and floating static routes | Part 2 |
| 23 | Single-area OSPFv2: router ID, network statements, passive interfaces | Part 3 |
| 24 | OSPF tuning: default route propagation, cost, reference bandwidth, DR/BDR, point-to-point | Part 4 |
| 25 | OSPF troubleshooting challenge; review | Part 5 |

### Session 6 – DHCP, NAT, ACLs & Capstone

| Period | Content | Lab Part |
|--------|---------|----------|
| 26 | DHCPv4 server on a router | Part 1 |
| 27 | DHCP relay (`ip helper-address`) and DHCP snooping | Part 2 |
| 28 | Static NAT and PAT | Part 3 |
| 29 | Standard and extended ACLs; securing VTY lines | Part 4 |
| 30 | Capstone verification, troubleshooting and practical assessment | Part 5 |

---

## Assessment

| Component | Weight | Description |
|-----------|--------|-------------|
| Lab reports (Labs 1–5) | 50 % | 10 % each – `.pkt` file + completed report template |
| Lab 6 capstone | 30 % | Practical, graded with the checklist in Lab 6 Part 5 |
| In-lab participation / checkpoints | 20 % | Instructor verifies ✅ checkpoints during class |

Grading rubric details: [docs/instructor-guide.md](docs/instructor-guide.md).
