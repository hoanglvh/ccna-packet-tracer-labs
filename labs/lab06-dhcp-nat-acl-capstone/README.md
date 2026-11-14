# Lab 06 – DHCP, NAT, ACLs & Capstone

**Session 6 · Periods 26–30 · 225 minutes**

## Objectives

- Configure a Cisco router as a DHCPv4 server.
- Relay DHCP requests to a central server with `ip helper-address`; protect DHCP with DHCP snooping.
- Translate private addresses with static NAT and PAT (NAT overload).
- Filter traffic with standard and extended ACLs and secure VTY access.
- Integrate and verify every technology from the course in a final practical assessment.

## Required Resources

| Qty | Device | Model |
|-----|--------|-------|
| 2 | Router | ISR4331 (R1, ISP) |
| 1 | Switch | 2960-24TT (S1) |
| 3 | PC / Laptop | PC1, PC2 (Users), Guest-Laptop |
| 1 | PC | Admin-PC |
| 3 | Server | Int-Server, Internet-Web, Rogue-DHCP (Part 2) |

## Topology

```
                                          Internet-Web 203.0.113.10
                                                   |  (HTTP + DNS)
                                                G0/0/1  203.0.113.0/24
                                                +-----+
                                                | ISP |
                                                +-----+
                                                G0/0/0  .225
                                                   |    209.165.200.224/29
                                                G0/0/0  .226   (NAT outside)
                                                +-----+
                                                | R1  |  DHCP server (VLAN 10), NAT, ACLs
                                                +-----+
                                                G0/0/1  (trunk, NAT inside subinterfaces)
                                                   |
                                                 G0/1
                    +----------------------------------------------------------+
                    |                           S1                             |
                    +----------------------------------------------------------+
                   F0/2       F0/6      F0/7       F0/11        F0/24      F0/8
                    |          |         |           |            |          |
                Admin-PC      PC1       PC2     Guest-Laptop  Int-Server  Rogue-DHCP
                (VLAN 99)  (VLAN 10) (VLAN 10)   (VLAN 20)    (VLAN 30)   (VLAN 10, Part 2)
```

## VLAN and Addressing Table

| VLAN | Name | Subnet | Gateway (R1) | Addressing |
|------|------|--------|--------------|------------|
| 10 | USERS | 192.168.10.0/24 | G0/0/1.10 – 192.168.10.1 | DHCP from **R1** |
| 20 | GUEST | 192.168.20.0/24 | G0/0/1.20 – 192.168.20.1 | DHCP from **Int-Server** (relay) |
| 30 | SERVERS | 192.168.30.0/24 | G0/0/1.30 – 192.168.30.1 | Static |
| 99 | MANAGEMENT | 192.168.99.0/24 | G0/0/1.99 – 192.168.99.1 | Static |
| 999 | PARKING | – | – | Unused ports |
| 1000 | NATIVE | – | G0/0/1.1000 (no IP) | – |

| Device | Interface | IPv4 Address | Subnet Mask | Default Gateway | DNS |
|--------|-----------|--------------|-------------|-----------------|-----|
| R1 | G0/0/0 | 209.165.200.226 | 255.255.255.248 | – | – |
| ISP | G0/0/0 | 209.165.200.225 | 255.255.255.248 | – | – |
| ISP | G0/0/1 | 203.0.113.1 | 255.255.255.0 | – | – |
| S1 | VLAN 99 | 192.168.99.11 | 255.255.255.0 | 192.168.99.1 | – |
| Admin-PC | NIC | 192.168.99.10 | 255.255.255.0 | 192.168.99.1 | 203.0.113.10 |
| Int-Server | NIC | 192.168.30.10 | 255.255.255.0 | 192.168.30.1 | 203.0.113.10 |
| Internet-Web | NIC | 203.0.113.10 | 255.255.255.0 | 203.0.113.1 | 203.0.113.10 |
| PC1, PC2 | NIC | DHCP | | | |
| Guest-Laptop | NIC | DHCP | | | |

Public addresses (209.165.200.224/29 assigned by the ISP):

| Public IP | Use |
|-----------|-----|
| 209.165.200.225 | ISP router |
| 209.165.200.226 | R1 G0/0/0 – PAT for all inside users |
| 209.165.200.230 | Static NAT for Int-Server |

---

## Period 26 – Part 1: Build the Network and Configure a DHCPv4 Server on R1

> 💡 Steps 1–4 review Labs 1 and 3. Your instructor may give you a starter file with these steps already done so you can focus on new topics.

### Step 1: Build and cable

| From | Port | To | Port | Cable |
|------|------|----|------|-------|
| ISP | G0/0/1 | Internet-Web | Fa0 | Cross-Over |
| ISP | G0/0/0 | R1 | G0/0/0 | Cross-Over |
| R1 | G0/0/1 | S1 | G0/1 | Straight |
| Admin-PC | Fa0 | S1 | F0/2 | Straight |
| PC1 | Fa0 | S1 | F0/6 | Straight |
| PC2 | Fa0 | S1 | F0/7 | Straight |
| Guest-Laptop | Fa0 | S1 | F0/11 | Straight |
| Int-Server | Fa0 | S1 | F0/24 | Straight |

Configure Admin-PC, Int-Server and Internet-Web with static IP settings. Set PC1, PC2 and Guest-Laptop to **DHCP** (they will show 169.254.x.x for now).

### Step 2: ISP router

```
Router(config)# hostname ISP
ISP(config)# interface g0/0/0
ISP(config-if)# ip address 209.165.200.225 255.255.255.248
ISP(config-if)# no shutdown
ISP(config-if)# interface g0/0/1
ISP(config-if)# ip address 203.0.113.1 255.255.255.0
ISP(config-if)# no shutdown
```

> 💡 The ISP has **no routes** to 192.168.x.x – like a real ISP. Only NAT will make inside hosts reachable.

On **Internet-Web**: **Services → DNS** → On; add record **Name** `www.ccna-lab.com`, **Type** A Record, **Address** `203.0.113.10` → **Add**. Make sure **HTTP** is On.

### Step 3: S1 – VLANs, access ports, trunk, management

```
Switch(config)# hostname S1
S1(config)# no ip domain-lookup
S1(config)# enable secret class
S1(config)# vlan 10
S1(config-vlan)# name USERS
S1(config-vlan)# vlan 20
S1(config-vlan)# name GUEST
S1(config-vlan)# vlan 30
S1(config-vlan)# name SERVERS
S1(config-vlan)# vlan 99
S1(config-vlan)# name MANAGEMENT
S1(config-vlan)# vlan 999
S1(config-vlan)# name PARKING
S1(config-vlan)# vlan 1000
S1(config-vlan)# name NATIVE
S1(config-vlan)# exit
S1(config)# interface f0/2
S1(config-if)# switchport mode access
S1(config-if)# switchport access vlan 99
S1(config-if)# interface range f0/6 - 8
S1(config-if-range)# switchport mode access
S1(config-if-range)# switchport access vlan 10
S1(config-if-range)# spanning-tree portfast
S1(config-if-range)# interface f0/11
S1(config-if)# switchport mode access
S1(config-if)# switchport access vlan 20
S1(config-if)# spanning-tree portfast
S1(config-if)# interface f0/24
S1(config-if)# switchport mode access
S1(config-if)# switchport access vlan 30
S1(config-if)# interface g0/1
S1(config-if)# switchport mode trunk
S1(config-if)# switchport trunk native vlan 1000
S1(config-if)# switchport trunk allowed vlan 10,20,30,99,1000
S1(config-if)# switchport nonegotiate
S1(config-if)# interface range f0/1 , f0/3 - 5 , f0/9 - 10 , f0/12 - 23 , g0/2
S1(config-if-range)# switchport mode access
S1(config-if-range)# switchport access vlan 999
S1(config-if-range)# shutdown
S1(config-if-range)# interface vlan 99
S1(config-if)# ip address 192.168.99.11 255.255.255.0
S1(config-if)# no shutdown
S1(config-if)# exit
S1(config)# ip default-gateway 192.168.99.1
```

> 💡 F0/8 is in VLAN 10 but has nothing connected yet – the Rogue-DHCP server will be plugged in there in Part 2.

### Step 4: R1 – basic settings, SSH, router-on-a-stick, default route

```
Router(config)# hostname R1
R1(config)# no ip domain-lookup
R1(config)# enable secret class
R1(config)# ip domain-name ccna-lab.com
R1(config)# username admin secret Cisco123!
R1(config)# crypto key generate rsa general-keys modulus 1024
R1(config)# ip ssh version 2
R1(config)# line vty 0 4
R1(config-line)# transport input ssh
R1(config-line)# login local
R1(config-line)# exit
R1(config)# interface g0/0/0
R1(config-if)# description To ISP
R1(config-if)# ip address 209.165.200.226 255.255.255.248
R1(config-if)# no shutdown
R1(config-if)# interface g0/0/1
R1(config-if)# no shutdown
R1(config-if)# interface g0/0/1.10
R1(config-subif)# encapsulation dot1Q 10
R1(config-subif)# ip address 192.168.10.1 255.255.255.0
R1(config-subif)# interface g0/0/1.20
R1(config-subif)# encapsulation dot1Q 20
R1(config-subif)# ip address 192.168.20.1 255.255.255.0
R1(config-subif)# interface g0/0/1.30
R1(config-subif)# encapsulation dot1Q 30
R1(config-subif)# ip address 192.168.30.1 255.255.255.0
R1(config-subif)# interface g0/0/1.99
R1(config-subif)# encapsulation dot1Q 99
R1(config-subif)# ip address 192.168.99.1 255.255.255.0
R1(config-subif)# interface g0/0/1.1000
R1(config-subif)# encapsulation dot1Q 1000 native
R1(config-subif)# exit
R1(config)# ip route 0.0.0.0 0.0.0.0 209.165.200.225
```

Test: Admin-PC → `ping 192.168.30.10` ✅. Admin-PC → `ping 203.0.113.10` ❌ (ISP has no route back – NAT comes in Part 3).

### Step 5: Configure R1 as DHCP server for VLAN 10

**Exclude** addresses reserved for static use first:

```
R1(config)# ip dhcp excluded-address 192.168.10.1 192.168.10.10
```

Create the pool:

```
R1(config)# ip dhcp pool USERS
R1(dhcp-config)# network 192.168.10.0 255.255.255.0
R1(dhcp-config)# default-router 192.168.10.1
R1(dhcp-config)# dns-server 203.0.113.10
R1(dhcp-config)# domain-name ccna-lab.com
R1(dhcp-config)# lease 2
R1(dhcp-config)# exit
```

> 💡 DHCP **DORA**: Discover (broadcast) → Offer → Request (broadcast) → Acknowledge. The router answers Discovers arriving on G0/0/1.10 because that subinterface's subnet matches the pool network.
>
> ⚠️ `domain-name` and `lease` may not be supported in some Packet Tracer versions – skip them if rejected.

### Step 6: Verify

On PC1 → **IP Configuration** → click **Static** then **DHCP** again:

```
DHCP request successful.
IPv4 Address ........: 192.168.10.11
Default Gateway .....: 192.168.10.1
DNS Server ..........: 203.0.113.10
```

```
R1# show ip dhcp binding
IP address       Client-ID/              Lease expiration        Type
                 Hardware address
192.168.10.11    0001.6411.xxxx          --                      Automatic
192.168.10.12    0060.5c2b.xxxx          --                      Automatic
R1# show ip dhcp pool
R1# show ip dhcp server statistics
```

Optional – watch DORA in **Simulation** mode with the **DHCP** filter while PC2 renews.

✅ **Checkpoint 1:** PC1 and PC2 receive addresses from `192.168.10.11` upwards; `show ip dhcp binding` lists both.

---

## Period 27 – Part 2: DHCP Relay and DHCP Snooping

### Step 1: Configure the DHCP service on Int-Server

1. **Int-Server → Services → DHCP** → set **Service** to **On**.
2. Create a pool for the guests:

| Field | Value |
|-------|-------|
| Pool Name | `GUEST-POOL` |
| Default Gateway | `192.168.20.1` |
| DNS Server | `203.0.113.10` |
| Start IP Address | `192.168.20.11` |
| Subnet Mask | `255.255.255.0` |
| Maximum Number of Users | `100` |

3. Click **Add**. (Leave the default `serverPool` in place – the server chooses the pool that matches the relay agent's address.)

Guest-Laptop → DHCP → ❌ still fails. Why? *Broadcasts do not cross routers.*

### Step 2: Configure the relay agent on R1

```
R1(config)# interface g0/0/1.20
R1(config-subif)# ip helper-address 192.168.30.10
R1(config-subif)# end
```

> 💡 The router receives the broadcast Discover on G0/0/1.20, and forwards it as a **unicast** to 192.168.30.10, filling the **giaddr** field with 192.168.20.1. The server uses giaddr to choose the right pool.

Guest-Laptop → DHCP → ✅ address `192.168.20.11`, gateway `192.168.20.1`.

### Step 3: Attack – add a rogue DHCP server

1. Add a **Server** named **Rogue-DHCP**, static IP `192.168.10.250/24`, connect it to **S1 F0/8** and `no shutdown` the port if necessary.
2. **Services → DHCP → On**, edit `serverPool`: Default Gateway `192.168.10.250`, DNS `192.168.10.250`, Start IP `192.168.10.100`, mask `255.255.255.0` → **Save**.
3. Renew PC2 several times (Static → DHCP). Sometimes PC2 gets a **192.168.10.100+** address with gateway .250 – a **man-in-the-middle** attack!

### Step 4: Enable DHCP snooping on S1

```
S1(config)# ip dhcp snooping
S1(config)# ip dhcp snooping vlan 10,20
S1(config)# no ip dhcp snooping information option
S1(config)# interface g0/1
S1(config-if)# ip dhcp snooping trust
S1(config-if)# exit
S1(config)# interface range f0/6 - 8 , f0/11
S1(config-if-range)# ip dhcp snooping limit rate 10
S1(config-if-range)# end
```

> 💡 Only **trusted** ports may send DHCP server messages (Offer/Ack). The uplink to R1 is trusted because both R1's own DHCP server and the relayed replies arrive through it. All access ports remain untrusted.
>
> ⚠️ `no ip dhcp snooping information option` stops the switch from inserting Option 82, which would otherwise cause R1 to drop the requests (giaddr 0.0.0.0 + option 82).
>
> 💡 VLAN 30 is not snooped: Int-Server's replies to the relay are unicast in VLAN 30 and must not be blocked.

### Step 5: Verify

Renew PC2 several times – it always receives a 192.168.10.x address from R1 now.

```
S1# show ip dhcp snooping
Switch DHCP snooping is enabled
DHCP snooping is configured on following VLANs:
10,20
Interface                  Trusted     Rate limit (pps)
-----------------------    -------     ----------------
GigabitEthernet0/1         yes         unlimited
FastEthernet0/6            no          10
...
S1# show ip dhcp snooping binding
```

Finally, **remove Rogue-DHCP** and shut down S1 F0/8.

✅ **Checkpoint 2:** Guest-Laptop gets an address from Int-Server via relay; the rogue server is blocked by DHCP snooping.

---

## Period 28 – Part 3: Configure NAT

> 💡 Terms: **inside local** = private address of the inside host; **inside global** = public address that represents it; **outside global** = address of the outside host.

### Step 1: Prove the problem

PC1 → `ping 203.0.113.10` ❌. The ping reaches the ISP, but the ISP has no route to 192.168.10.0/24, so the reply is dropped.

### Step 2: Define inside and outside interfaces

```
R1(config)# interface g0/0/0
R1(config-if)# ip nat outside
R1(config-if)# interface g0/0/1.10
R1(config-subif)# ip nat inside
R1(config-subif)# interface g0/0/1.20
R1(config-subif)# ip nat inside
R1(config-subif)# interface g0/0/1.30
R1(config-subif)# ip nat inside
R1(config-subif)# exit
```

### Step 3: Static NAT for the internal server

Int-Server must be reachable from the Internet at `209.165.200.230`:

```
R1(config)# ip nat inside source static 192.168.30.10 209.165.200.230
```

Configure a web page on Int-Server: **Services → HTTP → index.html → Edit**, change the text to *"Welcome to the CCNA Lab intranet"* and **Save**.

Test from **Internet-Web** → **Desktop → Web Browser** → `http://209.165.200.230` → the intranet page loads ✅.

```
R1# show ip nat translations
Pro  Inside global      Inside local       Outside local      Outside global
---  209.165.200.230    192.168.30.10      ---                ---
tcp  209.165.200.230:80 192.168.30.10:80   203.0.113.10:1025  203.0.113.10:1025
```

### Step 4: PAT (NAT overload) for users and guests

```
R1(config)# access-list 1 remark Inside hosts allowed to use PAT
R1(config)# access-list 1 permit 192.168.10.0 0.0.0.255
R1(config)# access-list 1 permit 192.168.20.0 0.0.0.255
R1(config)# ip nat inside source list 1 interface g0/0/0 overload
```

> 💡 `overload` = PAT: many inside hosts share **one** public IP, distinguished by **port numbers**. Using `interface g0/0/0` means "use the address of that interface".

### Step 5: Verify NAT

From PC1, PC2 and Guest-Laptop: `ping 203.0.113.10`, and open `http://www.ccna-lab.com` in the web browser.

```
R1# show ip nat translations
Pro  Inside global          Inside local        Outside local       Outside global
icmp 209.165.200.226:1      192.168.10.11:1     203.0.113.10:1      203.0.113.10:1
tcp  209.165.200.226:1025   192.168.10.11:1025  203.0.113.10:80     203.0.113.10:80
tcp  209.165.200.226:1026   192.168.20.11:1025  203.0.113.10:80     203.0.113.10:80
...
R1# show ip nat statistics
Outside interfaces: GigabitEthernet0/0/0
Inside interfaces: GigabitEthernet0/0/1.10, GigabitEthernet0/0/1.20, GigabitEthernet0/0/1.30
Hits: 42  Misses: 12
R1# clear ip nat translation *
```

> 💡 Optional: a **dynamic NAT pool** would look like
> `ip nat pool PUBLIC 209.165.200.227 209.165.200.229 netmask 255.255.255.248` +
> `ip nat inside source list 1 pool PUBLIC` – but with only 3 addresses, the 4th simultaneous user would fail. That's why PAT is used.

✅ **Checkpoint 3:** All inside hosts reach `www.ccna-lab.com`; Internet-Web reaches the intranet via `209.165.200.230`.

---

## Period 29 – Part 4: Access Control Lists

> 💡 ACL rules of thumb:
> - Processed **top-down**, first match wins, **implicit `deny any`** at the end.
> - **Standard** ACLs (1–99, named) match **source only** → place **close to the destination**.
> - **Extended** ACLs (100–199, named) match protocol, source, destination, ports → place **close to the source**.
> - One ACL per interface, per direction, per protocol.

### Step 1: Standard named ACL – restrict SSH to the management VLAN

```
R1(config)# ip access-list standard VTY-ADMIN
R1(config-std-nacl)# remark Only management VLAN may manage R1
R1(config-std-nacl)# permit 192.168.99.0 0.0.0.255
R1(config-std-nacl)# exit
R1(config)# line vty 0 4
R1(config-line)# access-class VTY-ADMIN in
R1(config-line)# end
```

Test:

| From | Command | Expected |
|------|---------|----------|
| Admin-PC | `ssh -l admin 192.168.99.1` | ✅ login prompt |
| PC1 | `ssh -l admin 192.168.10.1` | ❌ connection refused |

### Step 2: Extended named ACL – guest isolation

Policy for VLAN 20 (GUEST):

- ✅ DHCP (to get an address) and DNS.
- ❌ No access to **any** internal network (192.168.0.0/16).
- ✅ Web (HTTP/HTTPS) and ping to the Internet.
- ❌ Everything else.

```
R1(config)# ip access-list extended GUEST-POLICY
R1(config-ext-nacl)# remark Guest VLAN 20 - Internet only
R1(config-ext-nacl)# permit udp any any eq bootps
R1(config-ext-nacl)# permit udp 192.168.20.0 0.0.0.255 any eq domain
R1(config-ext-nacl)# deny ip 192.168.20.0 0.0.0.255 192.168.0.0 0.0.255.255
R1(config-ext-nacl)# permit tcp 192.168.20.0 0.0.0.255 any eq www
R1(config-ext-nacl)# permit tcp 192.168.20.0 0.0.0.255 any eq 443
R1(config-ext-nacl)# permit icmp 192.168.20.0 0.0.0.255 any echo
R1(config-ext-nacl)# exit
R1(config)# interface g0/0/1.20
R1(config-subif)# ip access-group GUEST-POLICY in
R1(config-subif)# end
```

> ⚠️ The `permit udp any any eq bootps` line must be **first**: DHCP Discovers have source 0.0.0.0, which does not match 192.168.20.0/24.
>
> 💡 Applied **inbound** on G0/0/1.20, as close as possible to the guests (the source).

Test from Guest-Laptop:

| Test | Expected |
|------|----------|
| Renew DHCP | ✅ |
| `ping 203.0.113.10` | ✅ |
| Browser `http://www.ccna-lab.com` | ✅ |
| `ping 192.168.10.11` (PC1) | ❌ |
| `ping 192.168.30.10` / browser `http://192.168.30.10` | ❌ |
| `ping 192.168.20.1` (own gateway) | ❌ (matches the deny line – acceptable for guests) |

```
R1# show access-lists
Standard IP access list 1
    10 permit 192.168.10.0 0.0.0.255 (24 match(es))
    20 permit 192.168.20.0 0.0.0.255 (8 match(es))
Standard IP access list VTY-ADMIN
    10 permit 192.168.99.0 0.0.0.255 (2 match(es))
Extended IP access list GUEST-POLICY
    10 permit udp any any eq bootps (4 match(es))
    20 permit udp 192.168.20.0 0.0.0.255 any eq domain (2 match(es))
    30 deny ip 192.168.20.0 0.0.0.255 192.168.0.0 0.0.255.255 (8 match(es))
    40 permit tcp 192.168.20.0 0.0.0.255 any eq www (12 match(es))
    ...
```

### Step 3: Extended ACL – protect the server VLAN

Policy for traffic **to** VLAN 30:

- ✅ HTTP to Int-Server from anywhere (including the Internet via static NAT).
- ✅ Ping to Int-Server from USERS (VLAN 10).
- ✅ Anything from MANAGEMENT (VLAN 99).
- ❌ Everything else.

```
R1(config)# ip access-list extended SERVER-PROTECT
R1(config-ext-nacl)# permit tcp any host 192.168.30.10 eq www
R1(config-ext-nacl)# permit icmp 192.168.10.0 0.0.0.255 host 192.168.30.10 echo
R1(config-ext-nacl)# permit ip 192.168.99.0 0.0.0.255 192.168.30.0 0.0.0.255
R1(config-ext-nacl)# deny ip any any
R1(config-ext-nacl)# exit
R1(config)# interface g0/0/1.30
R1(config-subif)# ip access-group SERVER-PROTECT out
```

> 💡 Here the ACL is **outbound** toward the servers, because traffic comes from many sources (several VLANs and the Internet). Packets generated by R1 itself (e.g. relayed DHCP to the server) are **not** filtered by an outbound ACL.

Test:

| From | Test | Expected |
|------|------|----------|
| PC1 | `ping 192.168.30.10`, browser `http://192.168.30.10` | ✅ ✅ |
| Internet-Web | browser `http://209.165.200.230` | ✅ |
| Internet-Web | `ping 209.165.200.230` | ❌ |
| Admin-PC | `ping 192.168.30.10` | ✅ |
| Guest-Laptop | renew DHCP (relay to server) | ✅ |

### Step 4: Edit an ACL with sequence numbers

Insert a rule that also allows HTTPS to the server, **before** the deny:

```
R1(config)# ip access-list extended SERVER-PROTECT
R1(config-ext-nacl)# 15 permit tcp any host 192.168.30.10 eq 443
R1(config-ext-nacl)# end
R1# show access-lists SERVER-PROTECT
```

✅ **Checkpoint 4:** All ACL tests in Steps 1–3 give the expected results.

---

## Period 30 – Part 5: Capstone – Verification, Troubleshooting & Assessment

### Step 1: Final verification checklist (60 points)

Demonstrate each item to the instructor using the indicated command.

| # | Requirement | Verify with | Points |
|---|-------------|-------------|--------|
| 1 | All VLANs exist with correct names and ports | `show vlan brief` | 5 |
| 2 | Trunk with native VLAN 1000 and allowed list | `show interfaces trunk` | 5 |
| 3 | Unused ports parked in VLAN 999 and shut down | `show interfaces status` | 3 |
| 4 | All R1 subinterfaces up/up with correct IPs | `show ip interface brief` | 5 |
| 5 | Users get DHCP from R1 | `show ip dhcp binding` | 5 |
| 6 | Guests get DHCP from Int-Server via relay | Guest `ipconfig /all` | 5 |
| 7 | DHCP snooping enabled; uplink trusted | `show ip dhcp snooping` | 5 |
| 8 | PAT works for VLAN 10 and 20 | `show ip nat translations` | 6 |
| 9 | Static NAT for the intranet server | Internet-Web browser | 5 |
| 10 | SSH only from VLAN 99 | Admin-PC vs PC1 | 5 |
| 11 | Guest isolation policy | Guest tests (Part 4 Step 2) | 6 |
| 12 | Server protection policy | Tests (Part 4 Step 3) | 5 |

### Step 2: Troubleshooting under time pressure (30 points)

The instructor introduces **3** faults (10 points each, 20 minutes in total). Record: symptom → command → cause → fix.

| # | Possible fault |
|---|----------------|
| F1 | `ip nat inside` removed from G0/0/1.10 |
| F2 | `ip helper-address` points to `192.168.30.11` |
| F3 | DHCP snooping `trust` removed from S1 G0/1 |
| F4 | Guest ACL applied `out` instead of `in` |
| F5 | DHCP pool `default-router 192.168.10.254` |
| F6 | Default route on R1 removed |
| F7 | VLAN 20 removed from the trunk allowed list |
| F8 | ACL 1 changed to `permit 192.168.10.0 0.0.0.0` |

### Step 3: Oral defense (10 points)

Be prepared to answer two questions chosen by the instructor from the review questions of Labs 1–6.

### Capstone Challenge (Extra credit)

1. Add **IPv6** to VLAN 10 (`2001:db8:acad:10::1/64`) and give PCs addresses using **stateless DHCPv6** (`ipv6 nd other-config-flag` + `ipv6 dhcp pool`).
2. Configure **NTP** (R1 as client of ISP, `ntp server 209.165.200.225`) and **Syslog** to Int-Server (`logging host 192.168.30.10`), then view the logs in **Int-Server → Services → SYSLOG**.
3. Replace `access-list 1` with a named standard ACL `NAT-INSIDE` and explain why NAT still works.

## Review Questions

1. Describe the four DHCPv4 messages (DORA) and whether each is unicast or broadcast.
2. Why is `ip helper-address` needed, and on which interface is it configured?
3. Which attacks does DHCP snooping prevent? Which ports should be trusted?
4. Explain inside local, inside global, outside local and outside global using the translations you captured.
5. Why is PAT used much more often than dynamic NAT with a pool?
6. Where should standard and extended ACLs be placed? Why?
7. Why was the guest ACL's first line `permit udp any any eq bootps`?
8. What is the difference between `ip access-group` and `access-class`?

Answers and final configurations: [solutions/](solutions/).
