# Cisco IOS Command Cheat Sheet

## CLI Modes

| Mode | Prompt | Enter with | Leave with |
|------|--------|------------|------------|
| User EXEC | `R1>` | (login) | `exit` |
| Privileged EXEC | `R1#` | `enable` | `disable` |
| Global configuration | `R1(config)#` | `configure terminal` | `exit` / `end` / Ctrl+Z |
| Interface configuration | `R1(config-if)#` | `interface g0/0/0` | `exit` |
| Sub-interface | `R1(config-subif)#` | `interface g0/0/1.10` | `exit` |
| Line configuration | `R1(config-line)#` | `line console 0` / `line vty 0 4` | `exit` |
| Router configuration | `R1(config-router)#` | `router ospf 1` | `exit` |
| VLAN configuration | `S1(config-vlan)#` | `vlan 10` | `exit` |

## Editing Keys

| Key | Action |
|-----|--------|
| `?` | Context help |
| Tab | Complete a command |
| ↑ / Ctrl+P | Previous command |
| Ctrl+A / Ctrl+E | Beginning / end of line |
| Ctrl+Shift+6 | Interrupt (ping, traceroute, DNS lookup) |
| Ctrl+Z | Return to privileged EXEC |
| `do <cmd>` | Run an EXEC command from any config mode |

## Basic Device Setup

```
enable
configure terminal
 hostname R1
 no ip domain-lookup
 enable secret class
 service password-encryption
 banner motd #Authorized Access Only!#
 line console 0
  password cisco
  login
  logging synchronous
  exec-timeout 5 0
 line vty 0 4
  password cisco
  login
 end
copy running-config startup-config
```

## SSH

```
ip domain-name ccna-lab.com
username admin secret Cisco123!
crypto key generate rsa general-keys modulus 1024
ip ssh version 2
line vty 0 4
 transport input ssh
 login local
```

## Interfaces

```
interface g0/0/0
 description Link to S1
 ip address 192.168.10.1 255.255.255.0
 ipv6 address 2001:db8:acad:10::1/64
 ipv6 address fe80::1 link-local
 no shutdown
interface range f0/1 - 5
 shutdown
```

## VLANs & Trunks

```
vlan 10
 name SALES
interface f0/6
 switchport mode access
 switchport access vlan 10
interface g0/1
 switchport mode trunk
 switchport trunk native vlan 1000
 switchport trunk allowed vlan 10,20,99,1000
 switchport nonegotiate
```

## STP & EtherChannel

```
spanning-tree mode rapid-pvst
spanning-tree vlan 10 root primary
spanning-tree vlan 20 root secondary
interface f0/6
 spanning-tree portfast
 spanning-tree bpduguard enable
interface range f0/1 - 2
 channel-group 1 mode active      ! LACP (active/passive)
 ! channel-group 1 mode desirable  ! PAgP (desirable/auto)
```

## Port Security

```
interface f0/6
 switchport mode access
 switchport port-security
 switchport port-security maximum 2
 switchport port-security mac-address sticky
 switchport port-security violation restrict
```

## Routing

```
ip route 192.168.2.0 255.255.255.0 10.0.12.2          ! next-hop
ip route 0.0.0.0 0.0.0.0 209.165.200.225              ! default
ip route 192.168.2.0 255.255.255.0 10.0.13.2 5        ! floating (AD 5)
ipv6 unicast-routing
ipv6 route ::/0 2001:db8:acad:ff::1

router ospf 1
 router-id 1.1.1.1
 network 192.168.1.0 0.0.0.255 area 0
 passive-interface g0/0/0
 default-information originate
 auto-cost reference-bandwidth 1000
```

## DHCP, NAT, ACL

```
ip dhcp excluded-address 192.168.10.1 192.168.10.10
ip dhcp pool VLAN10
 network 192.168.10.0 255.255.255.0
 default-router 192.168.10.1
 dns-server 203.0.113.10
interface g0/0/1.20
 ip helper-address 192.168.30.10

ip nat inside source static 192.168.30.10 209.165.200.230
access-list 1 permit 192.168.0.0 0.0.255.255
ip nat inside source list 1 interface g0/0/0 overload
interface g0/0/0
 ip nat outside
interface g0/0/1.10
 ip nat inside

ip access-list standard VTY-ADMIN
 permit 192.168.99.0 0.0.0.255
line vty 0 4
 access-class VTY-ADMIN in
```

## Most Useful show Commands

| Command | Shows |
|---------|-------|
| `show running-config` | Active configuration |
| `show startup-config` | Saved configuration |
| `show version` | IOS version, uptime, interfaces, config register |
| `show ip interface brief` | Interface IP + status summary |
| `show ipv6 interface brief` | IPv6 interface summary |
| `show interfaces <int>` | Detailed L1/L2 statistics |
| `show interfaces status` | Switch port status, VLAN, duplex, speed |
| `show vlan brief` | VLANs and access ports |
| `show interfaces trunk` | Trunk ports, native VLAN, allowed VLANs |
| `show spanning-tree` | STP root, port roles/states |
| `show etherchannel summary` | Port-channel status |
| `show port-security interface <int>` | Port security status |
| `show mac address-table` | Learned MAC addresses |
| `show ip route` | IPv4 routing table |
| `show ipv6 route` | IPv6 routing table |
| `show ip ospf neighbor` | OSPF adjacencies |
| `show ip protocols` | Routing protocol details |
| `show ip dhcp binding` | DHCP leases |
| `show ip nat translations` | NAT table |
| `show access-lists` | ACLs with hit counters |
| `show cdp neighbors detail` | Directly connected Cisco devices |
| `show lldp neighbors` | LLDP neighbors |
| `show arp` / `show ipv6 neighbors` | Address resolution tables |
