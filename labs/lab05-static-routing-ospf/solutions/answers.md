# Lab 05 – Answer Key

## Part 5 – Faults
| Fault | Symptom | Command | Fix |
|-------|---------|---------|-----|
| F1 | No R2–R3 adjacency; log `%OSPF-4-ERRRCV ... mismatched area ID` | `show ip ospf interface g0/0/2` (Area 1) | `ip ospf 10 area 0` |
| F2 | R3 has only one neighbor (R1) | `show ip protocols` → Passive Interface(s) | `no passive-interface g0/0/2` |
| F3 | No R1–R2 adjacency: wildcard 0.0.0.0 matches only the address 10.0.12.0, not the interface address 10.0.12.1, so OSPF is not enabled on G0/0/1 | `show ip ospf interface brief` – G0/0/1 missing | `network 10.0.12.0 0.0.0.3 area 0` (or `network 10.0.12.1 0.0.0.0 area 0`) |
| F4 | `%OSPF-4-DUP_RTRID` messages, unstable routes | `show ip ospf neighbor`, `show ip protocols` | Unique router-id, then `clear ip ospf process` |
| F5 | No `O*E2` route; Internet unreachable from LANs | `show ip route` on R1/R2 | `default-information originate` on R3 |
| F6 | R1–R3 adjacency drops after dead timer | `show ip ospf interface g0/0/1` (Hello 15, Dead 60) | Match timers |
| F7 | On broadcast type: no adjacency (mask mismatch). On point-to-point: adjacency forms but the subnets differ | `show ip interface brief`, `show run int` | Restore `/30` |

## Challenge 2 – OSPFv3 outline
```
ipv6 unicast-routing
ipv6 router ospf 10
 router-id 1.1.1.1
interface g0/0/0
 ipv6 address 2001:db8:acad:1::1/64
 ipv6 ospf 10 area 0
interface g0/0/1
 ipv6 address 2001:db8:acad:12::1/64
 ipv6 ospf 10 area 0
interface g0/0/2
 ipv6 address 2001:db8:acad:13::1/64
 ipv6 ospf 10 area 0
```
Verify with `show ipv6 ospf neighbor` and `show ipv6 route ospf`.

## Review Questions
1. AD is the trustworthiness of a route source (lower = better). It is compared only when routes have the **same prefix length**. A static route (AD 1) beats OSPF (AD 110).
2. On a multi-access network, a route with only an exit interface makes the router ARP for every destination (relying on proxy ARP). A fully specified route names the exit interface **and** the next hop, so no recursive lookup and no proxy ARP is needed. (Packet Tracer 8.2.2 does not accept this form on the ISR4331, which is why the lab uses next-hop routes.)
3. It's a static route configured with an AD higher than the primary route. It is installed only when the primary route is removed from the routing table (e.g. the link goes down).
4. (1) Manually configured `router-id`; (2) highest IPv4 address of any loopback; (3) highest IPv4 address of any active physical interface. A changed RID only takes effect after `clear ip ospf process` or reload.
5. It stops sending OSPF Hellos out of an interface while still advertising its network. Benefits: no unnecessary OSPF traffic on LANs (bandwidth/CPU), and security – nobody on the LAN can form an adjacency and inject routes.
6. With the default 100 Mbps, all links ≥ 100 Mbps have cost 1, so OSPF can't prefer faster links. All routers must use the same value; otherwise costs are inconsistent and paths may be suboptimal or asymmetric.
7. Area ID, subnet and mask (on broadcast networks), hello and dead intervals, network type (compatible), authentication, stub area flag, MTU (for exchange), and unique router IDs.
8. `O` = OSPF, `*` = candidate default route, `E2` = external type 2 (metric does not increase inside the OSPF domain). It was injected by `default-information originate`.
