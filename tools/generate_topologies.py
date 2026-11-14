import sys
sys.path.insert(0, __import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from topo import render

REPO = sys.argv[1] if len(sys.argv) > 1 else __import__('os').path.dirname(__import__('os').path.dirname(__import__('os').path.abspath(__file__)))


def D(id, type, model, x, y, info=(), name=None, **kw):
    d = dict(id=id, type=type, model=model, name=name or id, x=x, y=y, info=list(info))
    d.update(kw)
    return d


def Lk(a, b, pa='', pb='', cable='straight', **kw):
    d = dict(a=a, b=b, pa=pa, pb=pb, cable=cable)
    d.update(kw)
    return d


specs = {}

specs['lab01-pt-intro-basic-config'] = dict(
    size=(940, 360), title='Lab 01 – Basic Device Configuration',
    devices=[
        D('PC1', 'pc', 'PC-PT', 80, 130, ['192.168.10.10/24', 'GW 192.168.10.1']),
        D('S1', 'switch', '2960-24TT', 270, 130, ['VLAN1 192.168.10.11']),
        D('R1', 'router', 'ISR4331', 470, 130, ['G0/0/0 192.168.10.1', 'G0/0/1 192.168.20.1']),
        D('S2', 'switch', '2960-24TT', 670, 130, ['VLAN1 192.168.20.11']),
        D('PC2', 'pc', 'PC-PT', 860, 130, ['192.168.20.10/24', 'GW 192.168.20.1']),
    ],
    links=[
        Lk('PC1', 'S1', 'Fa0', 'F0/6'),
        Lk('S1', 'R1', 'G0/1', 'G0/0/0', label='192.168.10.0/24', label_off=-30),
        Lk('R1', 'S2', 'G0/0/1', 'G0/1', label='192.168.20.0/24', label_off=-30),
        Lk('S2', 'PC2', 'F0/6', 'Fa0'),
        Lk('PC1', 'R1', 'RS-232', 'Console', cable='console', bend=260),
    ])

specs['lab02-ipv4-subnetting-ipv6'] = dict(
    size=(1040, 500), title='Lab 02 – IPv4 VLSM & IPv6 Addressing',
    devices=[
        D('PC-A', 'pc', 'PC-PT', 60, 120, ['192.168.1.126/25', 'IPv6: SLAAC']),
        D('SW-A', 'switch', '2960-24TT', 230, 120),
        D('PC-B', 'pc', 'PC-PT', 60, 330, ['192.168.1.190/26', '2001:db8:acad:b::10']),
        D('SW-B', 'switch', '2960-24TT', 230, 330),
        D('R1', 'router', 'ISR4331', 420, 225, ['.1 / .129 / .225', 'fe80::1'], label='above'),
        D('R2', 'router', 'ISR4331', 680, 225, ['.193 / .226', 'fe80::2']),
        D('SW-C', 'switch', '2960-24TT', 840, 225),
        D('PC-C', 'pc', 'PC-PT', 980, 225, ['192.168.1.222/27', 'IPv6: SLAAC']),
    ],
    links=[
        Lk('PC-A', 'SW-A', 'Fa0', 'F0/1'),
        Lk('SW-A', 'R1', 'G0/1', 'G0/0/0'),
        Lk('PC-B', 'SW-B', 'Fa0', 'F0/1'),
        Lk('SW-B', 'R1', 'G0/1', 'G0/0/1', side=-1),
        Lk('R1', 'R2', 'G0/0/2', 'G0/0/2', cable='cross', label='WAN 192.168.1.224/30 · 2001:db8:acad:ff::/64', label_off=34),
        Lk('R2', 'SW-C', 'G0/0/0', 'G0/1'),
        Lk('SW-C', 'PC-C', 'F0/1', 'Fa0'),
    ],
    notes=[(150, 58, 'LAN-A: 100 hosts · 2001:db8:acad:a::/64'),
           (150, 452, 'LAN-B: 50 hosts · 2001:db8:acad:b::/64'),
           (905, 150, 'LAN-C: 20 hosts · 2001:db8:acad:c::/64')])

specs['lab03-vlans-intervlan-routing'] = dict(
    size=(1040, 560), title='Lab 03 – VLANs, Trunking & Inter-VLAN Routing',
    zones=[(20, 40, 640, 490, 'Part A – Router-on-a-Stick'), (680, 40, 340, 490, 'Part B – Layer 3 switch')],
    devices=[
        D('R1', 'router', 'ISR4331', 200, 120, ['Subinterfaces', '.10 .20 .30 .99 .1000'], label='left'),
        D('S1', 'switch', '2960-24TT', 200, 280, ['VLAN99 192.168.99.11'], label='left'),
        D('S2', 'switch', '2960-24TT', 470, 280, ['VLAN99 192.168.99.12'], label='right'),
        D('PC1', 'pc', 'PC-PT', 90, 430, ['VLAN 10', '192.168.10.10']),
        D('PC2', 'pc', 'PC-PT', 230, 430, ['VLAN 20', '192.168.20.10']),
        D('PC3', 'pc', 'PC-PT', 370, 430, ['VLAN 10', '192.168.10.11']),
        D('PC4', 'pc', 'PC-PT', 480, 430, ['VLAN 20', '192.168.20.11']),
        D('PC5', 'pc', 'PC-PT', 590, 430, ['VLAN 30', '192.168.30.10']),
        D('MLS1', 'mls', '3650-24PS', 850, 120, ['SVI 172.16.10.1', 'SVI 172.16.20.1'], label='right'),
        D('S3', 'switch', '2960-24TT', 850, 280, label='right'),
        D('PC6', 'pc', 'PC-PT', 770, 430, ['VLAN 10', '172.16.10.10']),
        D('PC7', 'pc', 'PC-PT', 930, 430, ['VLAN 20', '172.16.20.10']),
    ],
    links=[
        Lk('R1', 'S1', 'G0/0/1', 'G0/1', label='802.1Q trunk', label_off=-40),
        Lk('S1', 'S2', 'F0/1', 'F0/1', cable='cross', label='trunk (native 1000)', label_off=-26),
        Lk('S1', 'PC1', 'F0/6', 'Fa0'), Lk('S1', 'PC2', 'F0/11', 'Fa0', side=-1),
        Lk('S2', 'PC3', 'F0/6', 'Fa0'), Lk('S2', 'PC4', 'F0/11', 'Fa0', side=-1),
        Lk('S2', 'PC5', 'F0/18', 'Fa0', side=-1),
        Lk('R1', 'MLS1', 'G0/0/2', 'G1/0/24', label='routed link 10.0.0.0/30', label_off=-16),
        Lk('MLS1', 'S3', 'G1/0/1', 'G0/1', label='trunk', label_off=-30),
        Lk('S3', 'PC6', 'F0/6', 'Fa0'), Lk('S3', 'PC7', 'F0/11', 'Fa0', side=-1),
    ])

specs['lab04-stp-etherchannel-port-security'] = dict(
    size=(960, 680), title='Lab 04 – STP, EtherChannel & Port Security',
    devices=[
        D('S1', 'switch', '2960-24TT', 470, 140, ['VLAN99 192.168.99.1'], label='above'),
        D('S2', 'switch', '2960-24TT', 230, 380, ['VLAN99 192.168.99.2'], label='left'),
        D('S3', 'switch', '2960-24TT', 710, 380, ['VLAN99 192.168.99.3'], label='right'),
        D('PC1', 'pc', 'PC-PT', 780, 140, ['VLAN 10', '192.168.10.11'], label='right'),
        D('PC2', 'pc', 'PC-PT', 230, 530, ['VLAN 20', '192.168.20.12']),
        D('PC3', 'pc', 'PC-PT', 620, 530, ['VLAN 10', '192.168.10.13']),
        D('PC4', 'pc', 'PC-PT', 800, 530, ['VLAN 20', '192.168.20.14']),
    ],
    links=[
        Lk('S1', 'S2', 'F0/1', 'F0/1', cable='cross', offset=-8, side=-1, pd=34),
        Lk('S1', 'S2', 'F0/2', 'F0/2', cable='cross', offset=8, side=1, pd=34),
        Lk('S1', 'S3', 'F0/3', 'F0/3', cable='cross', offset=-8, side=-1, pd=34),
        Lk('S1', 'S3', 'F0/4', 'F0/4', cable='cross', offset=8, side=1, pd=34),
        Lk('S2', 'S3', 'F0/3', 'F0/1', cable='cross', offset=-8, side=-1, pd=34),
        Lk('S2', 'S3', 'F0/4', 'F0/2', cable='cross', offset=8, side=1, pd=34),
        Lk('S1', 'PC1', 'F0/6', 'Fa0'),
        Lk('S2', 'PC2', 'F0/18', 'Fa0'),
        Lk('S3', 'PC3', 'F0/6', 'Fa0'), Lk('S3', 'PC4', 'F0/18', 'Fa0', side=-1),
    ],
    ellipses=[(350, 260, 30, 16, -45, 'Po1 · LACP', 285, 250),
              (590, 260, 30, 16, 45, 'Po2 · LACP', 655, 250),
              (470, 380, 30, 16, 0, 'Po3 · PAgP', 470, 414)])

specs['lab05-static-routing-ospf'] = dict(
    size=(1060, 640), title='Lab 05 – Static Routing & Single-Area OSPFv2',
    devices=[
        D('PC1', 'pc', 'PC-PT', 50, 140, ['192.168.1.10/24']),
        D('S1', 'switch', '2960-24TT', 200, 140),
        D('R1', 'router', 'ISR4331', 370, 140, ['RID 1.1.1.1'], label='above'),
        D('R2', 'router', 'ISR4331', 690, 140, ['RID 2.2.2.2'], label='above'),
        D('S2', 'switch', '2960-24TT', 860, 140),
        D('PC2', 'pc', 'PC-PT', 1010, 140, ['192.168.2.10/24']),
        D('R3', 'router', 'ISR4331', 530, 330, ['RID 3.3.3.3', 'Lo0 192.168.3.1/24'], label='right'),
        D('ISP', 'router', 'ISR4331', 530, 500, label='left'),
        D('Web-Server', 'server', 'Server-PT', 800, 500, ['203.0.113.10']),
    ],
    links=[
        Lk('PC1', 'S1', 'Fa0', 'F0/1', pd=14),
        Lk('S1', 'R1', 'G0/1', 'G0/0/0', label='192.168.1.0/24', label_off=-30, pd=16),
        Lk('R1', 'R2', 'G0/0/1', 'G0/0/1', cable='cross', label='10.0.12.0/30', label_off=-16),
        Lk('R2', 'S2', 'G0/0/0', 'G0/1', label='192.168.2.0/24', label_off=-30, pd=16),
        Lk('S2', 'PC2', 'F0/1', 'Fa0', pd=14),
        Lk('R1', 'R3', 'G0/0/2', 'G0/0/1', cable='cross', label='10.0.13.0/30', label_off=18),
        Lk('R2', 'R3', 'G0/0/2', 'G0/0/2', cable='cross', label='10.0.23.0/30', label_off=-18, side=-1),
        Lk('R3', 'ISP', 'G0/0/0', 'G0/0/0', cable='cross', label='209.165.200.224/30', label_off=-70, pd=20),
        Lk('ISP', 'Web-Server', 'G0/0/1', 'Fa0', cable='cross', label='203.0.113.0/24', label_off=-16),
    ],
    notes=[(530, 225, 'OSPF Area 0'), (530, 600, 'Internet (not in OSPF)')])

specs['lab06-dhcp-nat-acl-capstone'] = dict(
    size=(1060, 760), title='Lab 06 – DHCP, NAT, ACLs & Capstone',
    devices=[
        D('Internet-Web', 'server', 'Server-PT', 800, 100, ['203.0.113.10', 'HTTP + DNS']),
        D('ISP', 'router', 'ISR4331', 530, 100, label='left'),
        D('R1', 'router', 'ISR4331', 530, 260, ['DHCP · NAT · ACL'], label='left'),
        D('S1', 'switch', '2960-24TT', 530, 410, ['VLAN99 192.168.99.11'], label='right'),
        D('Admin-PC', 'pc', 'PC-PT', 110, 630, ['VLAN 99', '192.168.99.10']),
        D('PC1', 'pc', 'PC-PT', 270, 630, ['VLAN 10', 'DHCP']),
        D('PC2', 'pc', 'PC-PT', 420, 630, ['VLAN 10', 'DHCP']),
        D('Guest-Laptop', 'laptop', 'Laptop-PT', 590, 630, ['VLAN 20', 'DHCP (relay)']),
        D('Int-Server', 'server', 'Server-PT', 760, 630, ['VLAN 30', '192.168.30.10']),
        D('Rogue-DHCP', 'server', 'Server-PT', 940, 630, ['VLAN 10 · Part 2', '192.168.10.250'], rogue=True),
    ],
    links=[
        Lk('ISP', 'Internet-Web', 'G0/0/1', 'Fa0', cable='cross', label='203.0.113.0/24', label_off=-16),
        Lk('ISP', 'R1', 'G0/0/0', 'G0/0/0', cable='cross', label='209.165.200.224/29 (NAT outside)', label_off=-110, pd=18),
        Lk('R1', 'S1', 'G0/0/1', 'G0/1', label='trunk · NAT inside', label_off=-75, pd=18),
        Lk('S1', 'Admin-PC', 'F0/2', 'Fa0', pd=40),
        Lk('S1', 'PC1', 'F0/6', 'Fa0', pd=40),
        Lk('S1', 'PC2', 'F0/7', 'Fa0', pd=40),
        Lk('S1', 'Guest-Laptop', 'F0/11', 'Fa0', side=-1, pd=40),
        Lk('S1', 'Int-Server', 'F0/24', 'Fa0', side=-1, pd=40),
        Lk('S1', 'Rogue-DHCP', 'F0/8', 'Fa0', side=-1, pd=40),
    ])

for lab, spec in specs.items():
    render(spec, f'{REPO}/labs/{lab}/images/topology.svg')
    print('wrote', lab)
