#!/usr/bin/env python3
"""Offline verifier for the lab solution configs.

It parses every device configuration in labs/*/solutions, rebuilds the lab
topology, and simulates the network (Layer 2 VLANs/trunks/EtherChannel,
IPv4/IPv6 routing, static routes, OSPF, NAT/PAT, ACLs, DHCP, SSH). Then it runs
the connectivity and policy tests that the lab guides promise.

It is not Packet Tracer: it models the behaviour the labs depend on, so it
catches addressing, routing, VLAN, NAT and ACL mistakes, as well as commands
that are not in the known-command list. Always do a final check in Packet Tracer.

Usage:  python3 tools/verify_solutions.py [lab-number ...]
"""
import heapq
import ipaddress as ipa
import itertools
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Interface names
# ---------------------------------------------------------------------------
PREFIX = {
    'f': 'FastEthernet', 'fa': 'FastEthernet', 'fastethernet': 'FastEthernet',
    'g': 'GigabitEthernet', 'gi': 'GigabitEthernet', 'gig': 'GigabitEthernet',
    'gigabitethernet': 'GigabitEthernet',
    'po': 'Port-channel', 'port-channel': 'Port-channel',
    'vlan': 'Vlan', 'lo': 'Loopback', 'loopback': 'Loopback',
}


def norm(name):
    name = name.strip()
    m = re.match(r'([A-Za-z\-]+)\s*([\d/\.]+)$', name)
    if not m:
        raise ValueError(f'bad interface name {name!r}')
    p = PREFIX.get(m.group(1).lower())
    if not p:
        raise ValueError(f'unknown interface type {name!r}')
    return p + m.group(2)


def expand_range(spec):
    out = []
    for part in spec.split(','):
        part = part.strip()
        m = re.match(r'(.+?)(\d+)\s*-\s*(\d+)$', part)
        if m:
            base = norm(m.group(1) + m.group(2))
            stem = base[: len(base) - len(m.group(2))]
            for i in range(int(m.group(2)), int(m.group(3)) + 1):
                out.append(f'{stem}{i}')
        else:
            out.append(norm(part))
    return out


MODEL_PORTS = {
    '2960': [f'FastEthernet0/{i}' for i in range(1, 25)] + ['GigabitEthernet0/1', 'GigabitEthernet0/2'],
    '3650': [f'GigabitEthernet1/0/{i}' for i in range(1, 25)] + [f'GigabitEthernet1/1/{i}' for i in range(1, 5)],
    '4331': ['GigabitEthernet0/0/0', 'GigabitEthernet0/0/1', 'GigabitEthernet0/0/2'],
}


def port_bw(name):  # Mbps
    if name.startswith('FastEthernet'):
        return 100
    if name.startswith('Loopback'):
        return 8000
    return 1000

# ---------------------------------------------------------------------------
# Known command patterns (anything else is reported)
# ---------------------------------------------------------------------------
GLOBAL_CMDS = [
    r'hostname \S+', r'no ip domain-lookup', r'ip domain-name \S+', r'enable secret \S+',
    r'service password-encryption', r'security passwords min-length \d+',
    r'username \S+ secret \S+', r'login block-for \d+ attempts \d+ within \d+', r'banner motd #.*#',
    r'crypto key generate rsa general-keys modulus \d+', r'ip ssh version 2', r'ip ssh time-out \d+',
    r'ip ssh authentication-retries \d+', r'ip default-gateway \S+', r'ip route .+', r'ipv6 route .+',
    r'ipv6 unicast-routing', r'lldp run', r'ip routing', r'spanning-tree mode (rapid-pvst|pvst)',
    r'spanning-tree vlan [\d,\-]+ (root (primary|secondary)|priority \d+)',
    r'port-channel load-balance \S+', r'ip dhcp excluded-address \S+( \S+)?',
    r'access-list \d+ (permit|deny) .+', r'access-list \d+ remark .+',
    r'ip nat inside source static \S+ \S+', r'ip nat inside source list \S+ interface \S+ overload',
    r'ip dhcp snooping', r'ip dhcp snooping vlan [\d,\-]+', r'no ip dhcp snooping information option',
    r'end', r'exit', r'copy running-config startup-config',
]
IF_CMDS = [
    r'description .+', r'ip address \S+ \S+', r'ipv6 address \S+( link-local)?', r'(no )?shutdown',
    r'switchport mode (access|trunk|dynamic auto|dynamic desirable)', r'switchport access vlan \d+',
    r'switchport trunk native vlan \d+', r'switchport trunk allowed vlan (add )?[\d,\-]+',
    r'switchport trunk encapsulation dot1q', r'switchport nonegotiate', r'no switchport',
    r'switchport port-security', r'switchport port-security maximum \d+',
    r'switchport port-security mac-address sticky', r'switchport port-security violation (protect|restrict|shutdown)',
    r'switchport port-security aging time \d+', r'encapsulation dot1Q \d+( native)?',
    r'channel-group \d+ mode (active|passive|desirable|auto|on)', r'spanning-tree portfast',
    r'spanning-tree bpduguard enable', r'ip ospf \d+ area \d+', r'ip ospf network point-to-point',
    r'ip ospf cost \d+', r'ip ospf hello-interval \d+', r'ip ospf dead-interval \d+', r'ip ospf priority \d+',
    r'ip nat (inside|outside)', r'ip helper-address \S+', r'ip access-group \S+ (in|out)',
    r'ip dhcp snooping trust', r'ip dhcp snooping limit rate \d+', r'exit',
]
LINE_CMDS = [r'password \S+', r'login( local)?', r'logging synchronous', r'exec-timeout \d+ \d+',
             r'transport input ssh', r'access-class \S+ in', r'exit']
OSPF_CMDS = [r'router-id \S+', r'network \S+ \S+ area \d+', r'passive-interface \S+',
             r'auto-cost reference-bandwidth \d+', r'default-information originate', r'exit']
VLAN_CMDS = [r'name \S+', r'exit']
POOL_CMDS = [r'network \S+ \S+', r'default-router \S+', r'dns-server \S+', r'domain-name \S+',
             r'lease \d+', r'exit']
ACL_CMDS = [r'(\d+ )?(permit|deny) .+', r'remark .+', r'exit']


def known(cmds, line):
    return any(re.fullmatch(c, line) for c in cmds)

# ---------------------------------------------------------------------------
# Config parser
# ---------------------------------------------------------------------------


class Iface:
    def __init__(self, name):
        self.name = name
        self.desc = ''
        self.ip = None            # ipaddress.IPv4Interface
        self.ipv6 = []            # list of IPv6Interface (global)
        self.lla = None           # IPv6Address
        self.shutdown = None      # None = default
        self.sw = {}              # switchport settings
        self.routed = False       # "no switchport"
        self.dot1q = None         # (vid, native)
        self.channel = None       # (group, mode)
        self.ospf = {}            # process/area/network/cost/hello/dead
        self.nat = None
        self.helper = None
        self.acl_in = None
        self.acl_out = None
        self.portsec = {}
        self.stp = set()
        self.snoop_trust = False


class Config:
    def __init__(self, text, fname):
        self.fname = fname
        self.hostname = None
        self.ifs = {}
        self.routes = []          # (network, nexthop|None, exit_if|None, ad)
        self.routes6 = []
        self.default_gw = None
        self.vlans = {1: 'default'}
        self.ospf = None
        self.ip_routing = False
        self.ipv6_routing = False
        self.users = {}
        self.domain = None
        self.rsa = False
        self.ssh_v2 = False
        self.lines = {}
        self.stp_prio = {}
        self.stp_mode = 'pvst'
        self.dhcp_excl = []
        self.pools = {}
        self.acls = {}
        self.nat_static = []
        self.nat_pat = []
        self.snooping = False
        self.snoop_vlans = set()
        self.snoop_opt82 = True
        self.unknown = []
        self._ctx = (None, None)
        self.parse(text)

    def iface(self, name):
        if name not in self.ifs:
            self.ifs[name] = Iface(name)
        return self.ifs[name]

    def parse(self, text):
        ctx, target = None, None
        for n, raw in enumerate(text.splitlines(), 1):
            s = raw.strip()
            if not s or s.startswith('!'):
                continue
            if ctx and raw[0] == ' ':
                self.sub(ctx, target, s, n)
                continue
            self.glob(s, n)
            ctx, target = self._ctx

    def glob(self, s, n):
        self._ctx = (None, None)
        w = s.split()
        if s.startswith('interface range '):
            names = expand_range(s[len('interface range '):])
            self._ctx = ('if', [self.iface(x) for x in names])
            return
        if w[0] == 'interface':
            self._ctx = ('if', [self.iface(norm(' '.join(w[1:])))])
            return
        if w[0] == 'line':
            key = 'console' if w[1] == 'console' else 'vty'
            self.lines.setdefault(key, {})
            self._ctx = ('line', self.lines[key])
            return
        if s.startswith('router ospf'):
            self.ospf = dict(pid=int(w[2]), rid=None, networks=[], passive=set(), refbw=100, dio=False)
            self._ctx = ('ospf', self.ospf)
            return
        if w[0] == 'vlan' and len(w) == 2 and w[1].isdigit():
            self.vlans[int(w[1])] = ''
            self._ctx = ('vlan', int(w[1]))
            return
        if s.startswith('ip dhcp pool '):
            pool = self.pools.setdefault(w[3], {})
            self._ctx = ('pool', pool)
            return
        if s.startswith('ip access-list '):
            acl = dict(type=w[2], entries=[])
            self.acls[w[3]] = acl
            self._ctx = ('acl', acl)
            return
        if not known(GLOBAL_CMDS, s):
            self.unknown.append((n, s))
            return
        if w[0] == 'hostname':
            self.hostname = w[1]
        elif s.startswith('ip domain-name'):
            self.domain = w[2]
        elif w[0] == 'username':
            self.users[w[1]] = w[3]
        elif s.startswith('crypto key generate rsa'):
            self.rsa = int(w[-1])
        elif s == 'ip ssh version 2':
            self.ssh_v2 = True
        elif s.startswith('ip default-gateway'):
            self.default_gw = ipa.ip_address(w[2])
        elif w[:2] == ['ip', 'route']:
            self.routes.append(self._route(w[2:], v6=False))
        elif w[:2] == ['ipv6', 'route']:
            self.routes6.append(self._route(w[2:], v6=True))
        elif s == 'ipv6 unicast-routing':
            self.ipv6_routing = True
        elif s == 'ip routing':
            self.ip_routing = True
        elif s.startswith('spanning-tree mode'):
            self.stp_mode = w[2]
        elif s.startswith('spanning-tree vlan'):
            prio = {'primary': 24576, 'secondary': 28672}.get(w[-1]) if w[3] == 'root' else int(w[-1])
            for v in parse_vlan_list(w[2]):
                self.stp_prio[v] = prio
        elif s.startswith('ip dhcp excluded-address'):
            lo = ipa.ip_address(w[3])
            hi = ipa.ip_address(w[4]) if len(w) > 4 else lo
            self.dhcp_excl.append((lo, hi))
        elif w[0] == 'access-list' and w[2] != 'remark':
            acl = self.acls.setdefault(w[1], dict(type='standard', entries=[]))
            acl['entries'].append(parse_ace('standard', w[2:]))
        elif s.startswith('ip nat inside source static'):
            self.nat_static.append((ipa.ip_address(w[5]), ipa.ip_address(w[6])))
        elif s.startswith('ip nat inside source list'):
            self.nat_pat.append((w[5], norm(w[7])))
        elif s == 'ip dhcp snooping':
            self.snooping = True
        elif s.startswith('ip dhcp snooping vlan'):
            self.snoop_vlans |= set(parse_vlan_list(w[4]))
        elif s == 'no ip dhcp snooping information option':
            self.snoop_opt82 = False

    def _route(self, a, v6):
        if v6:
            net = ipa.ip_network(a[0])
            rest = a[1:]
        else:
            net = ipa.ip_network(f'{a[0]}/{a[1]}')
            rest = a[2:]
        nh, exitif, ad = None, None, 1
        for t in rest:
            if re.fullmatch(r'\d+', t):
                ad = int(t)
            elif re.match(r'^[A-Za-z]', t):
                exitif = norm(t)
            else:
                nh = ipa.ip_address(t)
        return (net, nh, exitif, ad)

    def sub(self, ctx, target, s, n):
        w = s.split()
        if ctx == 'if':
            if not known(IF_CMDS, s):
                self.unknown.append((n, s))
                return
            for i in target:
                self.if_cmd(i, s, w)
        elif ctx == 'line':
            if not known(LINE_CMDS, s):
                self.unknown.append((n, s))
                return
            if w[0] == 'transport':
                target['transport'] = w[2]
            elif s == 'login local':
                target['login'] = 'local'
            elif s == 'login':
                target['login'] = 'line'
            elif w[0] == 'access-class':
                target['access_class'] = w[1]
            elif w[0] == 'password':
                target['password'] = w[1]
        elif ctx == 'ospf':
            if not known(OSPF_CMDS, s):
                self.unknown.append((n, s))
                return
            if w[0] == 'router-id':
                target['rid'] = w[1]
            elif w[0] == 'network':
                target['networks'].append((ipa.ip_address(w[1]), ipa.ip_address(w[2]), int(w[4])))
            elif w[0] == 'passive-interface':
                target['passive'].add(norm(w[1]))
            elif w[0] == 'auto-cost':
                target['refbw'] = int(w[2])
            elif s == 'default-information originate':
                target['dio'] = True
        elif ctx == 'vlan':
            if not known(VLAN_CMDS, s):
                self.unknown.append((n, s))
            elif w[0] == 'name':
                self.vlans[target] = w[1]
        elif ctx == 'pool':
            if not known(POOL_CMDS, s):
                self.unknown.append((n, s))
            elif w[0] == 'network':
                target['network'] = ipa.ip_network(f'{w[1]}/{w[2]}')
            elif w[0] == 'default-router':
                target['gw'] = ipa.ip_address(w[1])
            elif w[0] == 'dns-server':
                target['dns'] = ipa.ip_address(w[1])
        elif ctx == 'acl':
            if not known(ACL_CMDS, s):
                self.unknown.append((n, s))
            elif w[0] not in ('remark', 'exit'):
                if w[0].isdigit():
                    w = w[1:]
                target['entries'].append(parse_ace(target['type'], w))

    def if_cmd(self, i, s, w):
        if w[0] == 'description':
            i.desc = s[12:]
        elif w[:2] == ['ip', 'address']:
            i.ip = ipa.ip_interface(f'{w[2]}/{w[3]}')
        elif w[:2] == ['ipv6', 'address']:
            if w[-1] == 'link-local':
                i.lla = ipa.ip_address(w[2])
            else:
                i.ipv6.append(ipa.ip_interface(w[2]))
        elif s == 'shutdown':
            i.shutdown = True
        elif s == 'no shutdown':
            i.shutdown = False
        elif s == 'no switchport':
            i.routed = True
        elif w[0] == 'switchport':
            if w[1] == 'mode':
                i.sw['mode'] = ' '.join(w[2:])
            elif w[1] == 'access':
                i.sw['access'] = int(w[3])
            elif w[1:4] == ['trunk', 'native', 'vlan']:
                i.sw['native'] = int(w[4])
            elif w[1:4] == ['trunk', 'allowed', 'vlan']:
                if w[4] == 'add':
                    i.sw['allowed'] = sorted(set(i.sw.get('allowed', [])) | set(parse_vlan_list(w[5])))
                else:
                    i.sw['allowed'] = parse_vlan_list(w[4])
            elif w[1:3] == ['trunk', 'encapsulation']:
                i.sw['encap'] = w[3]
            elif w[1] == 'nonegotiate':
                i.sw['noneg'] = True
            elif w[1] == 'port-security':
                key = w[2] if len(w) > 2 else 'enabled'
                i.portsec[key] = w[3:] or True
        elif w[0] == 'encapsulation':
            i.dot1q = (int(w[2]), len(w) > 3)
        elif w[0] == 'channel-group':
            i.channel = (int(w[1]), w[3])
        elif w[0] == 'spanning-tree':
            i.stp.add(w[1])
        elif w[:2] == ['ip', 'ospf']:
            if w[2].isdigit():
                i.ospf['area'] = int(w[4])
                i.ospf['pid'] = int(w[2])
            elif w[2] == 'network':
                i.ospf['p2p'] = True
            else:
                i.ospf[w[2]] = int(w[3])
        elif w[:2] == ['ip', 'nat']:
            i.nat = w[2]
        elif w[:2] == ['ip', 'helper-address']:
            i.helper = ipa.ip_address(w[2])
        elif w[:2] == ['ip', 'access-group']:
            setattr(i, 'acl_in' if w[3] == 'in' else 'acl_out', w[2])
        elif w[:3] == ['ip', 'dhcp', 'snooping'] and w[3] == 'trust':
            i.snoop_trust = True


def parse_vlan_list(s):
    out = []
    for p in s.split(','):
        if '-' in p:
            a, b = p.split('-')
            out += range(int(a), int(b) + 1)
        else:
            out.append(int(p))
    return out


PORTS = {'www': 80, 'bootps': 67, 'bootpc': 68, 'domain': 53, 'telnet': 23}


def parse_addr(tokens):
    if tokens[0] == 'any':
        return ipa.ip_network('0.0.0.0/0'), tokens[1:]
    if tokens[0] == 'host':
        return ipa.ip_network(tokens[1] + '/32'), tokens[2:]
    if len(tokens) > 1 and re.fullmatch(r'[\d\.]+', tokens[1]):
        wild = int(ipa.ip_address(tokens[1]))
        mask = (~wild) & 0xFFFFFFFF
        return (tokens[0], mask), tokens[2:]   # address + wildcard
    return ipa.ip_network(tokens[0] + '/32'), tokens[1:]


def addr_match(spec, ip):
    if ip.version != 4:
        return False
    if isinstance(spec, tuple):
        base, mask = spec
        return (int(ip) & mask) == (int(ipa.ip_address(base)) & mask)
    return ip in spec


def parse_ace(kind, w):
    act = w[0]
    if kind == 'standard':
        src, _ = parse_addr(w[1:])
        return dict(act=act, proto='ip', src=src, dst=None, sport=None, dport=None, icmp=None)
    proto = w[1]
    src, rest = parse_addr(w[2:])
    sport = None
    if rest and rest[0] == 'eq' and proto in ('tcp', 'udp'):
        sport, rest = PORTS.get(rest[1]) or int(rest[1]), rest[2:]
    dst, rest = parse_addr(rest)
    dport, icmp = None, None
    if rest and rest[0] == 'eq':
        dport = PORTS.get(rest[1]) or int(rest[1])
    elif rest and proto == 'icmp':
        icmp = rest[0]
    return dict(act=act, proto=proto, src=src, sport=sport, dst=dst, dport=dport, icmp=icmp)


def acl_permits(acl, pkt):
    if acl is None:
        return True
    for e in acl['entries']:
        if e['proto'] != 'ip' and e['proto'] != pkt['proto']:
            continue
        if not addr_match(e['src'], pkt['src']):
            continue
        if e['dst'] is not None and not addr_match(e['dst'], pkt['dst']):
            continue
        if e['sport'] and pkt.get('sport') != e['sport']:
            continue
        if e['dport'] and pkt.get('dport') != e['dport']:
            continue
        if e['icmp'] and pkt.get('icmp') != e['icmp']:
            continue
        return e['act'] == 'permit'
    return False   # implicit deny

# ---------------------------------------------------------------------------
# Network model
# ---------------------------------------------------------------------------


class UF:
    def __init__(self):
        self.p = {}

    def find(self, x):
        self.p.setdefault(x, x)
        while self.p[x] != x:
            self.p[x] = self.p[self.p[x]]
            x = self.p[x]
        return x

    def union(self, a, b):
        self.p[self.find(a)] = self.find(b)


class Device:
    def __init__(self, name, kind, model=None, cfg=None, host=None):
        self.name, self.kind, self.model = name, kind, model
        self.cfg = cfg or Config('', name)
        self.host = host or {}


class Net:
    def __init__(self, devices, links):
        self.dev = {d.name: d for d in devices}
        self.links = links      # list of ((devA, portA), (devB, portB))
        self.errors, self.warnings = [], []
        self.ospf_nbrs = {}
        self.peer = {}
        for (a, pa), (b, pb) in links:
            self.peer[(a, pa)] = (b, pb)
            self.peer[(b, pb)] = (a, pa)
        self.check_ports()
        self.build_l2()
        self.build_l3()

    # ---- helpers ---------------------------------------------------------
    def is_switch(self, d):
        return d.kind in ('switch', 'mls')

    def port_cfg(self, d, port):
        """(member iface, iface whose switchport settings apply)."""
        i = d.cfg.ifs.get(port) or Iface(port)
        if i.channel:
            pc = d.cfg.ifs.get(f'Port-channel{i.channel[0]}')
            if pc:
                return i, pc
        return i, i

    def admin_up(self, d, port):
        if d.kind == 'host':
            return True
        i = d.cfg.ifs.get(port)
        if d.kind == 'router':
            return bool(i and i.shutdown is False)
        return not (i and i.shutdown)

    def check_ports(self):
        for d in self.dev.values():
            if d.model in MODEL_PORTS:
                valid = set(MODEL_PORTS[d.model])
                for name in d.cfg.ifs:
                    base = name.split('.')[0]
                    if base.startswith(('Vlan', 'Loopback', 'Port-channel')):
                        continue
                    if base not in valid:
                        self.errors.append(f'{d.name}: interface {name} does not exist on a {d.model}')
            for n, s in d.cfg.unknown:
                self.errors.append(f'{d.cfg.fname}:{n}: unrecognised command "{s}"')
        for (a, pa), (b, pb) in self.links:
            for dn, p in ((a, pa), (b, pb)):
                if not self.admin_up(self.dev[dn], p):
                    self.errors.append(f'{dn} {p} is connected but shut down')

    # ---- Layer 2 ---------------------------------------------------------
    def op_mode(self, d, port, peer):
        _, c = self.port_cfg(d, port)
        mode = c.sw.get('mode', 'dynamic auto')
        if c.routed:
            return 'routed'
        if mode in ('access', 'trunk'):
            return mode
        pd, pp = peer
        pdev = self.dev[pd]
        if not self.is_switch(pdev):
            return 'access'
        _, pc = self.port_cfg(pdev, pp)
        pmode = pc.sw.get('mode', 'dynamic auto')
        if pc.routed:
            return 'access'
        if pmode == 'trunk' and not pc.sw.get('noneg'):
            return 'trunk'
        if pmode == 'dynamic desirable' or (mode == 'dynamic desirable' and pmode == 'dynamic auto'):
            return 'trunk'
        return 'access'

    def vlan_ok(self, d, v):
        return v in d.cfg.vlans

    def build_l2(self):
        uf = UF()
        self.uf = uf
        self.port_up = set()
        self.trunk_vlans = {}   # (dev, port) -> set of vlans carried
        ok_pairs = {('active', 'active'), ('active', 'passive'), ('passive', 'active'),
                    ('desirable', 'desirable'), ('desirable', 'auto'), ('auto', 'desirable'), ('on', 'on')}
        for (a, pa), (b, pb) in self.links:
            da, db = self.dev[a], self.dev[b]
            if not (self.admin_up(da, pa) and self.admin_up(db, pb)):
                continue
            if self.is_switch(da) and self.is_switch(db):
                ca = (da.cfg.ifs.get(pa) or Iface(pa)).channel
                cb = (db.cfg.ifs.get(pb) or Iface(pb)).channel
                if ca or cb:
                    if not (ca and cb and (ca[1], cb[1]) in ok_pairs):
                        self.errors.append(f'EtherChannel {a} {pa} ({ca and ca[1]}) <-> {b} {pb} '
                                           f'({cb and cb[1]}) will not form')
                        continue
                    for d, p in ((da, pa), (db, pb)):
                        i, pc = self.port_cfg(d, p)
                        if pc is not i and any(i.sw.get(k) != pc.sw.get(k) for k in ('mode', 'native', 'allowed')):
                            self.errors.append(f'{d.name} {p}: member settings differ from '
                                               f'Port-channel{i.channel[0]} (port would be suspended)')
            ea = self.l2_end(da, pa, (b, pb)) if self.is_switch(da) else None
            eb = self.l2_end(db, pb, (a, pa)) if self.is_switch(db) else None
            self.port_up.add((a, pa))
            self.port_up.add((b, pb))
            if ea and eb and ea[0] != 'routed' and eb[0] != 'routed':
                (ma, na, va), (mb, nb, vb) = ea, eb
                if ma == 'trunk' and mb == 'trunk':
                    if na != nb:
                        self.warnings.append(f'native VLAN mismatch {a} {pa} ({na}) <-> {b} {pb} ({nb})')
                    uf.union(('dom', a, na), ('dom', b, nb))
                    common = {v for v in va & vb if self.vlan_ok(da, v) and self.vlan_ok(db, v)}
                    for v in common:
                        uf.union(('dom', a, v), ('dom', b, v))
                    self.trunk_vlans[(a, pa)] = common | {na}
                    self.trunk_vlans[(b, pb)] = common | {nb}
                elif ma == 'access' and mb == 'access':
                    if self.vlan_ok(da, va) and self.vlan_ok(db, vb):
                        uf.union(('dom', a, va), ('dom', b, vb))
                    self.trunk_vlans[(a, pa)] = {va}
                    self.trunk_vlans[(b, pb)] = {vb}
                else:
                    self.errors.append(f'trunk/access mismatch {a} {pa} ({ma}) <-> {b} {pb} ({mb})')
            elif (ea and ea[0] != 'routed') or (eb and eb[0] != 'routed'):
                if ea and ea[0] != 'routed':
                    sd, sp, other, op, (m, nat, vl) = a, pa, db, pb, ea
                else:
                    sd, sp, other, op, (m, nat, vl) = b, pb, da, pa, eb
                self.trunk_vlans[(sd, sp)] = vl if m == 'trunk' else {vl}
                self.attach_to_switch(other, op, sd, m, nat, vl)
            else:
                seg = ('seg', a, pa)
                uf.union(('if', a, pa), seg)
                uf.union(('if', b, pb), seg)
        # SVIs
        for d in self.dev.values():
            if not self.is_switch(d):
                continue
            for name, i in d.cfg.ifs.items():
                if not name.startswith('Vlan'):
                    continue
                v = int(name[4:])
                shut = i.shutdown if i.shutdown is not None else (v == 1)
                active = self.vlan_ok(d, v) and any(
                    (d.name, p) in self.port_up and v in self.trunk_vlans.get((d.name, p), set())
                    for p in MODEL_PORTS.get(d.model, []))
                if not shut and active:
                    uf.union(('if', d.name, name), ('dom', d.name, v))
                elif not shut:
                    self.errors.append(f'{d.name} {name} would be up/down (VLAN {v} missing or no active port)')

    def l2_end(self, d, port, peer):
        i, c = self.port_cfg(d, port)
        mode = self.op_mode(d, port, peer)
        if mode == 'routed':
            return ('routed', None, None)
        if mode == 'trunk':
            if d.kind == 'mls' and c.sw.get('mode') == 'trunk' and c.sw.get('encap') != 'dot1q':
                self.errors.append(f'{d.name} {port}: 3650 needs "switchport trunk encapsulation dot1q" '
                                   f'before "switchport mode trunk"')
            allowed = set(c.sw.get('allowed', range(1, 4095)))
            return ('trunk', c.sw.get('native', 1), allowed)
        v = c.sw.get('access', 1)
        if not self.vlan_ok(d, v):
            self.errors.append(f'{d.name} {port}: access VLAN {v} does not exist (port inactive)')
        return ('access', None, v)

    def attach_to_switch(self, other, op, sw, mode, native, vlans):
        """Router/host port `op` on device `other`, cabled to switch `sw`."""
        uf = self.uf
        untagged = native if mode == 'trunk' else vlans
        if other.kind == 'host':
            uf.union(('if', other.name, op), ('dom', sw, untagged))
            return
        phys = other.cfg.ifs.get(op) or Iface(op)
        if phys.ip or phys.ipv6 or phys.routed:
            uf.union(('if', other.name, op), ('dom', sw, untagged))
        for name, i in other.cfg.ifs.items():
            if not name.startswith(op + '.') or not i.dot1q:
                continue
            vid, is_native = i.dot1q
            if mode != 'trunk':
                self.errors.append(f'{other.name} {name}: switch port on {sw} is not a trunk')
                continue
            if is_native:
                if vid != native:
                    self.warnings.append(f'{other.name} {name}: native {vid} vs switch native {native}')
                uf.union(('if', other.name, name), ('dom', sw, native))
                continue
            if vid not in vlans:
                self.errors.append(f'{other.name} {name}: VLAN {vid} not allowed on the {sw} trunk')
                continue
            uf.union(('if', other.name, name), ('dom', sw, vid))

    # ---- Layer 3 ---------------------------------------------------------
    def l3_ifaces(self, d):
        """List of (name, ipv4 iface, [ipv6 ifaces], link-local, segment)."""
        out = []
        if d.kind == 'host':
            h = d.host
            if h.get('ip') or h.get('ipv6'):
                out.append(('Fa0', h.get('ip'), h.get('ipv6', []), h.get('lla'),
                            self.uf.find(('if', d.name, 'Fa0'))))
            return out
        for name, i in d.cfg.ifs.items():
            if not (i.ip or i.ipv6):
                continue
            if name.startswith('Loopback'):
                out.append((name, i.ip, list(i.ipv6), i.lla, ('lo', d.name, name)))
                continue
            base = name.split('.')[0]
            if not name.startswith('Vlan'):
                if not self.admin_up(d, base) or (d.name, base) not in self.port_up:
                    continue
            key = ('if', d.name, name)
            if key not in self.uf.p:
                continue
            lla = i.lla or (ipa.ip_address(f'fe80::{abs(hash((d.name, name))) % 65535:x}') if i.ipv6 else None)
            out.append((name, i.ip, list(i.ipv6), lla, self.uf.find(key)))
        return out

    def routes_enabled(self, d, v6=False):
        if d.kind == 'router':
            return d.cfg.ipv6_routing if v6 else True
        if d.kind == 'mls':
            return d.cfg.ip_routing and not v6
        return False

    def build_l3(self):
        self.ifs = {n: self.l3_ifaces(d) for n, d in self.dev.items()}
        for d in self.dev.values():         # SLAAC
            if d.kind == 'host' and d.host.get('slaac'):
                seg = self.uf.find(('if', d.name, 'Fa0'))
                for rn, rd in self.dev.items():
                    if rd.kind != 'router' or not rd.cfg.ipv6_routing:
                        continue
                    for name, ip4, v6s, lla, s in self.ifs[rn]:
                        if s == seg and v6s:
                            net = v6s[0].network
                            d.host['ipv6'] = [ipa.ip_interface(f'{net.network_address + 0x2aa}/{net.prefixlen}')]
                            d.host['gw6'] = lla
                self.ifs[d.name] = self.l3_ifaces(d)
        self.check_segments()
        self.rib = {n: self.compute_rib(d, False) for n, d in self.dev.items()}
        self.rib6 = {n: self.compute_rib(d, True) for n, d in self.dev.items()}
        self.ospf_routes()

    def check_segments(self):
        """All IPv4 addresses on one Layer 2 segment must share the same subnet; no duplicates."""
        segs = {}
        for n, lst in self.ifs.items():
            for name, ip4, v6s, lla, seg in lst:
                if ip4 and seg[0] != 'lo':
                    segs.setdefault(seg, []).append((n, name, ip4))
        for members in segs.values():
            nets = {m[2].network for m in members}
            if len(nets) > 1:
                desc = ', '.join(f'{n} {name} {ip}' for n, name, ip in members)
                self.errors.append(f'subnet mismatch on one segment: {desc}')
            seen = {}
            for n, name, ip in members:
                if ip.ip in seen:
                    self.errors.append(f'duplicate IP {ip.ip} on {seen[ip.ip]} and {n}')
                seen[ip.ip] = n
        for d in self.dev.values():
            gw = d.host.get('gw') if d.kind == 'host' else d.cfg.default_gw
            ip4 = next((x[1] for x in self.ifs[d.name] if x[1]), None)
            if gw and ip4 and gw not in ip4.network:
                self.errors.append(f'{d.name}: default gateway {gw} is outside its subnet {ip4.network}')

    def owner(self, seg, ip):
        for n, lst in self.ifs.items():
            for name, ip4, v6s, lla, s in lst:
                if s != seg:
                    continue
                if (ip4 and ip4.ip == ip) or any(x.ip == ip for x in v6s) or lla == ip:
                    return n, name
                # IOS answers ARP for static NAT global addresses on the outside subnet
                i = self.dev[n].cfg.ifs.get(name)
                if i and i.nat == 'outside' and ip4 and ip in ip4.network and \
                        any(g == ip for _, g in self.dev[n].cfg.nat_static):
                    return n, name
        return None

    def compute_rib(self, d, v6):
        rib = []
        for name, ip4, v6s, lla, seg in self.ifs[d.name]:
            for a in (v6s if v6 else ([ip4] if ip4 else [])):
                rib.append(dict(net=a.network, ad=0, metric=0, nh=None, ifname=name, src='C'))
        if d.kind == 'host':
            gw = d.host.get('gw6' if v6 else 'gw')
            if gw:
                rib.append(dict(net=ipa.ip_network('::/0' if v6 else '0.0.0.0/0'), ad=1, metric=0,
                                nh=gw, ifname='Fa0', src='S'))
            return rib
        if not self.routes_enabled(d, v6):
            if d.cfg.default_gw and not v6:
                rib.append(dict(net=ipa.ip_network('0.0.0.0/0'), ad=1, metric=0, nh=d.cfg.default_gw,
                                ifname=None, src='S'))
            return rib
        for net, nh, exitif, ad in (d.cfg.routes6 if v6 else d.cfg.routes):
            rib.append(dict(net=net, ad=ad, metric=0, nh=nh, ifname=exitif, src='S'))
        return self.best(rib)

    def best(self, rib):
        best = {}
        for r in rib:
            if r['src'] == 'S' and r['nh'] is not None and not r['nh'].is_link_local:
                if not self.nh_resolvable(rib, r):
                    continue      # recursive lookup fails -> route not installed
            cur = best.get(r['net'])
            if cur is None or (r['ad'], r['metric']) < (cur['ad'], cur['metric']):
                best[r['net']] = r
        return list(best.values())

    @staticmethod
    def nh_resolvable(rib, r):
        return any(r['nh'] in x['net'] and x['src'] == 'C' and (r['ifname'] in (None, x['ifname']))
                   for x in rib) or any(r['nh'] in x['net'] and x['src'] != 'C' and x is not r
                                        and x['net'].prefixlen > 0 for x in rib)

    def resolve(self, dname, dst, v6, depth=0):
        """Return (egress ifname, next-hop ip) or None."""
        if depth > 8:
            return None
        rib = (self.rib6 if v6 else self.rib)[dname]
        cands = [r for r in rib if dst in r['net']]
        if not cands:
            return None
        r = max(cands, key=lambda r: r['net'].prefixlen)
        if r['src'] == 'C' or r['nh'] is None:
            return r['ifname'], dst
        if r['nh'].is_link_local:
            return r['ifname'], r['nh']
        res = self.resolve(dname, r['nh'], v6, depth + 1)
        if res is None:
            return None
        ifname, nh = res
        if r['ifname'] and r['ifname'] != ifname:
            return None
        return ifname, (r['nh'] if nh == r['nh'] else nh)

    def seg_of(self, dname, ifname):
        for name, ip4, v6s, lla, seg in self.ifs[dname]:
            if name == ifname:
                return seg
        return None

    # ---- OSPF ------------------------------------------------------------
    def ospf_ifaces(self, d):
        o = d.cfg.ospf
        out = {}
        if not o:
            return out
        up = {x[0] for x in self.ifs[d.name]}
        for name, i in d.cfg.ifs.items():
            if not i.ip or name not in up:
                continue
            area = i.ospf.get('area')
            if area is None:
                for addr, wild, a in o['networks']:
                    mask = (~int(wild)) & 0xFFFFFFFF
                    if int(i.ip.ip) & mask == int(addr) & mask:
                        area = a
                        break
            if area is None:
                continue
            cost = i.ospf.get('cost') or max(1, o['refbw'] // port_bw(name.split('.')[0]))
            p2p = i.ospf.get('p2p', False)
            prefix = i.ip.network
            if name.startswith('Loopback') and not p2p:
                prefix = ipa.ip_network(f'{i.ip.ip}/32')
            out[name] = dict(area=area, cost=cost, passive=name in o['passive'], p2p=p2p,
                             hello=i.ospf.get('hello-interval', 10), dead=i.ospf.get('dead-interval', 40),
                             ip=i.ip, prefix=prefix)
        return out

    def ospf_routes(self):
        routers = {n: d for n, d in self.dev.items() if d.cfg.ospf and self.routes_enabled(d)}
        if not routers:
            return
        oif = {n: self.ospf_ifaces(d) for n, d in routers.items()}
        rids = {}
        for n, d in routers.items():
            rid = d.cfg.ospf['rid']
            if rid in rids:
                self.errors.append(f'duplicate OSPF router-id {rid} on {n} and {rids[rid]}')
            rids[rid] = n
        adj = {n: [] for n in routers}
        self.ospf_nbrs = {n: [] for n in routers}
        for a, b in itertools.combinations(routers, 2):
            for na, ia in oif[a].items():
                for nb, ib in oif[b].items():
                    if ia['passive'] or ib['passive']:
                        continue
                    sa = self.seg_of(a, na)
                    if sa is None or sa != self.seg_of(b, nb):
                        continue
                    problems = []
                    if ia['area'] != ib['area']:
                        problems.append('area mismatch')
                    if (ia['hello'], ia['dead']) != (ib['hello'], ib['dead']):
                        problems.append('hello/dead mismatch')
                    if ia['p2p'] != ib['p2p']:
                        problems.append('network type mismatch')
                    if ia['ip'].network != ib['ip'].network:
                        problems.append('subnet/mask mismatch')
                    if problems:
                        self.errors.append(f'OSPF {a} {na} <-> {b} {nb}: no adjacency ({", ".join(problems)})')
                        continue
                    adj[a].append((b, ia['cost'], ib['ip'].ip, na))
                    adj[b].append((a, ib['cost'], ia['ip'].ip, nb))
                    self.ospf_nbrs[a].append(b)
                    self.ospf_nbrs[b].append(a)
        defaults = [n for n, d in routers.items() if d.cfg.ospf['dio'] and
                    any(r['net'].prefixlen == 0 and r['src'] == 'S' for r in self.rib[n])]
        for src in routers:
            dist, first, pq = {src: 0}, {src: None}, [(0, src)]
            while pq:
                c, u = heapq.heappop(pq)
                if c > dist[u]:
                    continue
                for v, cost, nbr_ip, ifname in adj[u]:
                    nc = c + cost
                    if nc < dist.get(v, 1 << 30):
                        dist[v] = nc
                        first[v] = first[u] or (ifname, nbr_ip)
                        heapq.heappush(pq, (nc, v))
            connected = {r['net'] for r in self.rib[src] if r['src'] == 'C'}
            byp = {}
            for r, c in dist.items():
                if r == src:
                    continue
                ifname, nh = first[r]
                cands = [dict(net=info['prefix'], ad=110, metric=c + info['cost'], nh=nh, ifname=ifname, src='O')
                         for info in oif[r].values() if info['prefix'] not in connected]
                if r in defaults:
                    cands.append(dict(net=ipa.ip_network('0.0.0.0/0'), ad=110, metric=1, nh=nh, ifname=ifname,
                                      src='O*E2', fwd=c))
                for x in cands:
                    k = x['net']
                    if k not in byp or (x['metric'], x.get('fwd', 0)) < (byp[k]['metric'], byp[k].get('fwd', 0)):
                        byp[k] = x
            self.rib[src] = self.best(self.rib[src] + list(byp.values()))

    # ---- Packet forwarding -----------------------------------------------
    def forward(self, start, pkt):
        """Forward a locally originated packet. Returns (device, packet) or (None, reason)."""
        pkt = dict(pkt)
        v6 = pkt['dst'].version == 6
        node, ingress = start, None
        for _ in range(32):
            d = self.dev[node]
            ingress_if = self.iface_cfg(d, ingress)
            if ingress_if and ingress_if.acl_in and not acl_permits(d.cfg.acls.get(ingress_if.acl_in), pkt):
                return None, f'denied by ACL {ingress_if.acl_in} in on {node} {ingress}'
            if ingress_if and ingress_if.nat == 'outside':
                pkt = self.nat_in(d, pkt)
            if self.owns(node, pkt['dst']):
                return node, pkt
            if ingress is not None and not self.routes_enabled(d, v6):
                return None, f'{node} does not route'
            res = self.resolve(node, pkt['dst'], v6)
            if res is None:
                return None, f'no route on {node} to {pkt["dst"]}'
            ifname, nh = res
            egress_if = self.iface_cfg(d, ifname)
            if ingress_if and egress_if and ingress_if.nat == 'inside' and egress_if.nat == 'outside':
                pkt = self.nat_out(d, pkt)
            if ingress is not None and egress_if and egress_if.acl_out and \
                    not acl_permits(d.cfg.acls.get(egress_if.acl_out), pkt):
                return None, f'denied by ACL {egress_if.acl_out} out on {node} {ifname}'
            o = self.owner(self.seg_of(node, ifname), nh)
            if o is None:
                return None, f'{node}: next hop {nh} not reachable out {ifname} (ARP/ND fails)'
            node, ingress = o
        return None, 'TTL expired (routing loop)'

    def iface_cfg(self, d, name):
        if name is None or d.kind == 'host':
            return None
        return d.cfg.ifs.get(name)

    def owns(self, node, ip):
        return any((ip4 and ip4.ip == ip) or any(x.ip == ip for x in v6s)
                   for name, ip4, v6s, lla, seg in self.ifs[node])

    def nat_in(self, d, pkt):
        for local, glob in d.cfg.nat_static:
            if pkt['dst'] == glob:
                return {**pkt, 'dst': local}
        key = (pkt['dst'], pkt['proto'], pkt.get('dport'))
        if key in getattr(d, 'pat', {}):
            local, lport = d.pat[key]
            return {**pkt, 'dst': local, 'dport': lport}
        return pkt

    def nat_out(self, d, pkt):
        for local, glob in d.cfg.nat_static:
            if pkt['src'] == local:
                return {**pkt, 'src': glob}
        for aclname, ifname in d.cfg.nat_pat:
            if acl_permits(d.cfg.acls.get(aclname), {**pkt, 'proto': 'ip'}):
                gip = d.cfg.ifs[ifname].ip.ip
                d.pat = getattr(d, 'pat', {})
                d.nat_port = getattr(d, 'nat_port', 1024) + 1
                d.pat[(gip, pkt['proto'], d.nat_port)] = (pkt['src'], pkt.get('sport'))
                return {**pkt, 'src': gip, 'sport': d.nat_port}
        return pkt

    def service_ok(self, node, pkt):
        d = self.dev[node]
        if pkt['proto'] == 'icmp':
            return True, None
        port = pkt.get('dport')
        if d.kind == 'host':
            svc = d.host.get('services', [])
            ok = (port == 80 and 'http' in svc) or (port == 53 and 'dns' in svc) or (port == 67 and 'dhcp' in svc)
            return ok, None if ok else f'{node} has no service on port {port}'
        if port in (22, 23):
            vty = d.cfg.lines.get('vty', {})
            if port == 23 and vty.get('transport') == 'ssh':
                return False, f'{node}: telnet refused (transport input ssh)'
            if port == 22:
                c = d.cfg
                miss = [x for x, ok in (('hostname', c.hostname not in (None, 'Router', 'Switch')),
                                        ('ip domain-name', c.domain), ('RSA key >= 768 bits', (c.rsa or 0) >= 768),
                                        ('transport input ssh', vty.get('transport') == 'ssh'),
                                        ('login local + username', vty.get('login') == 'local' and c.users))
                        if not ok]
                if miss:
                    return False, f'{node}: SSH not usable (missing {", ".join(miss)})'
            ac = vty.get('access_class')
            if ac and not acl_permits(d.cfg.acls.get(ac), {**pkt, 'proto': 'ip'}):
                return False, f'{node}: VTY access-class {ac} refuses {pkt["src"]}'
            return True, None
        return False, f'{node}: no service on port {port}'

    def talk(self, src, dst, proto='icmp', dport=None):
        """Request + reply between two devices. Returns (ok, reason)."""
        dst = ipa.ip_address(dst)
        v6 = dst.version == 6
        srcip = None
        res = self.resolve(src, dst, v6)
        for name, ip4, v6s, lla, seg in self.ifs[src]:
            addr = (v6s[0].ip if v6s else None) if v6 else (ip4.ip if ip4 else None)
            if addr is None:
                continue
            if srcip is None or (res and res[0] == name):
                srcip = addr
        if srcip is None:
            return False, f'{src} has no address'
        pkt = dict(src=srcip, dst=dst, proto=proto, sport=40000, dport=dport, icmp='echo')
        node, p2 = self.forward(src, pkt)
        if node is None:
            return False, 'request: ' + p2
        ok, why = self.service_ok(node, p2)
        if not ok:
            return False, why
        reply = dict(src=p2['dst'], dst=p2['src'], proto=proto, sport=p2.get('dport'),
                     dport=p2.get('sport'), icmp='echo-reply')
        back, p3 = self.forward(node, reply)
        if back != src:
            return False, 'reply: ' + (p3 if back is None else f'delivered to {back}')
        if p3['src'] != dst:
            return False, f'reply comes from {p3["src"]} instead of {dst}'
        return True, None

    # ---- DHCP ------------------------------------------------------------
    def dhcp(self, host):
        d = self.dev[host]
        seg = self.uf.find(('if', host, 'Fa0'))
        gws = [(n, name, ip4) for n, lst in self.ifs.items() for name, ip4, v6s, lla, s in lst
               if s == seg and ip4 and self.dev[n].kind in ('router', 'mls')]
        if not gws:
            return False, 'no router interface in the client VLAN'
        rn, ifname, ip4 = gws[0]
        r = self.dev[rn]
        icfg = r.cfg.ifs[ifname]
        disc = dict(src=ipa.ip_address('0.0.0.0'), dst=ipa.ip_address('255.255.255.255'), proto='udp',
                    sport=68, dport=67)
        if icfg.acl_in and not acl_permits(r.cfg.acls.get(icfg.acl_in), disc):
            return False, f'Discover denied by ACL {icfg.acl_in} on {rn} {ifname}'
        why = self.snoop_check(host)
        if why:
            return False, why
        lease = None
        for name, pool in r.cfg.pools.items():
            if 'network' in pool and ip4.ip in pool['network']:
                if pool.get('gw') not in pool['network']:
                    return False, f'pool {name}: default-router not in the pool subnet'
                lease = self.allocate(r, pool['network'], pool['gw'], pool.get('dns'), r.cfg.dhcp_excl)
                break
        if lease is None and icfg.helper:
            node, p = self.forward(rn, dict(src=ip4.ip, dst=icfg.helper, proto='udp', sport=67, dport=67))
            if node is None:
                return False, 'relay: ' + p
            srv = self.dev[node]
            if 'dhcp' not in srv.host.get('services', []):
                return False, f'{node} runs no DHCP service'
            back, p = self.forward(node, dict(src=p['dst'], dst=ip4.ip, proto='udp', sport=67, dport=67))
            if back != rn:
                return False, 'relay reply: ' + str(p)
            for pool in srv.host.get('pools', []):
                if pool['gw'] in ip4.network:
                    lease = self.allocate(srv, ip4.network, pool['gw'], pool.get('dns'), [], pool['start'])
            if lease is None:
                return False, f'{node} has no pool for giaddr {ip4.ip}'
        if lease is None:
            return False, f'{rn} {ifname}: no matching DHCP pool and no helper-address'
        ip, gw, dns = lease
        d.host.update(ip=ip, gw=gw, dns=dns)
        self.ifs[host] = self.l3_ifaces(d)
        self.rib[host] = self.compute_rib(d, False)
        return True, f'{ip} gw {gw}'

    @staticmethod
    def allocate(server, net, gw, dns, excl, start=None):
        used = getattr(server, 'leased', set())
        server.leased = used
        for h in net.hosts():
            if (start and h < start) or h == gw or h in used or any(lo <= h <= hi for lo, hi in excl):
                continue
            used.add(h)
            return ipa.ip_interface(f'{h}/{net.prefixlen}'), gw, dns
        return None

    def snoop_check(self, host):
        sw, port = self.peer[(host, 'Fa0')]
        s = self.dev[sw]
        if not s.cfg.snooping:
            return None
        if self.port_cfg(s, port)[1].sw.get('access', 1) not in s.cfg.snoop_vlans:
            return None
        if s.cfg.snoop_opt82:
            return f'{sw}: option 82 is inserted (needs "no ip dhcp snooping information option")'
        for (dn, p), (pd, pp) in self.peer.items():
            if dn == sw and self.dev[pd].kind in ('router', 'switch', 'mls'):
                i = s.cfg.ifs.get(p)
                if not (i and i.snoop_trust):
                    return f'{sw} {p}: uplink is untrusted, DHCP server replies would be dropped'
        return None

    # ---- STP -------------------------------------------------------------
    def stp_root(self, vlan):
        prios = sorted((d.cfg.stp_prio.get(vlan, 32768), n) for n, d in self.dev.items() if self.is_switch(d))
        if len(prios) > 1 and prios[0][0] == prios[1][0]:
            return None
        return prios[0][1]

# ---------------------------------------------------------------------------
# Lab definitions
# ---------------------------------------------------------------------------


def P(s):
    return s if s == 'Fa0' else norm(s)


def L(a, pa, b, pb):
    return ((a, P(pa)), (b, P(pb)))


def load(lab, name):
    path = os.path.join(ROOT, 'labs', lab, 'solutions', name + '.txt')
    return Config(open(path).read(), os.path.relpath(path, ROOT))


def host(name, ip=None, gw=None, **kw):
    h = dict(kw)
    if ip:
        h['ip'] = ipa.ip_interface(ip)
    if gw:
        h['gw'] = ipa.ip_address(gw)
    if 'ipv6' in h:
        h['ipv6'] = [ipa.ip_interface(h['ipv6'])]
    if 'gw6' in h:
        h['gw6'] = ipa.ip_address(h['gw6'])
    return Device(name, 'host', host=h)


def lab1():
    lab = 'lab01-pt-intro-basic-config'
    devs = [Device('R1', 'router', '4331', load(lab, 'R1')), Device('S1', 'switch', '2960', load(lab, 'S1')),
            Device('S2', 'switch', '2960', load(lab, 'S2')),
            host('PC1', '192.168.10.10/24', '192.168.10.1'), host('PC2', '192.168.20.10/24', '192.168.20.1')]
    links = [L('PC1', 'Fa0', 'S1', 'F0/6'), L('S1', 'G0/1', 'R1', 'G0/0/0'), L('R1', 'G0/0/1', 'S2', 'G0/1'),
             L('S2', 'F0/6', 'PC2', 'Fa0')]
    T = [('ping', 'PC1', '192.168.10.1', True), ('ping', 'PC1', '192.168.20.10', True),
         ('ping', 'PC1', '192.168.10.11', True), ('ping', 'PC1', '192.168.20.11', True),
         ('ping', 'PC2', '192.168.10.11', True),
         ('ssh', 'PC1', '192.168.10.1', True), ('ssh', 'PC1', '192.168.10.11', True),
         ('ssh', 'PC1', '192.168.20.11', True), ('telnet', 'PC1', '192.168.10.1', False)]
    return Net(devs, links), T, []


def lab2():
    lab = 'lab02-ipv4-subnetting-ipv6'
    devs = [Device('R1', 'router', '4331', load(lab, 'R1')), Device('R2', 'router', '4331', load(lab, 'R2')),
            Device('SW-A', 'switch', '2960'), Device('SW-B', 'switch', '2960'), Device('SW-C', 'switch', '2960'),
            host('PC-A', '192.168.1.126/25', '192.168.1.1', slaac=True),
            host('PC-B', '192.168.1.190/26', '192.168.1.129', ipv6='2001:db8:acad:b::10/64', gw6='fe80::1'),
            host('PC-C', '192.168.1.222/27', '192.168.1.193', slaac=True)]
    links = [L('PC-A', 'Fa0', 'SW-A', 'F0/1'), L('SW-A', 'G0/1', 'R1', 'G0/0/0'), L('PC-B', 'Fa0', 'SW-B', 'F0/1'),
             L('SW-B', 'G0/1', 'R1', 'G0/0/1'), L('R1', 'G0/0/2', 'R2', 'G0/0/2'),
             L('R2', 'G0/0/0', 'SW-C', 'G0/1'), L('SW-C', 'F0/1', 'PC-C', 'Fa0')]
    net = Net(devs, links)
    c6 = net.dev['PC-C'].host.get('ipv6')
    ipc6 = str(c6[0].ip) if c6 else '2001:db8:acad:c::dead'
    T = [('ping', 'PC-A', '192.168.1.190', True), ('ping', 'PC-A', '192.168.1.222', True),
         ('ping', 'PC-B', '192.168.1.222', True), ('ping', 'R1', '192.168.1.226', True),
         ('ping', 'PC-A', '2001:db8:acad:b::10', True), ('ping', 'PC-A', ipc6, True),
         ('ping', 'PC-B', ipc6, True)]
    checks = [('PC-A and PC-C get an IPv6 address by SLAAC',
               bool(net.dev['PC-A'].host.get('ipv6') and c6), '')]
    return net, T, checks


def lab3():
    lab = 'lab03-vlans-intervlan-routing'
    devs = [Device('R1', 'router', '4331', load(lab, 'R1')), Device('S1', 'switch', '2960', load(lab, 'S1')),
            Device('S2', 'switch', '2960', load(lab, 'S2')), Device('S3', 'switch', '2960', load(lab, 'S3')),
            Device('MLS1', 'mls', '3650', load(lab, 'MLS1')),
            host('PC1', '192.168.10.10/24', '192.168.10.1'), host('PC2', '192.168.20.10/24', '192.168.20.1'),
            host('PC3', '192.168.10.11/24', '192.168.10.1'), host('PC4', '192.168.20.11/24', '192.168.20.1'),
            host('PC5', '192.168.30.10/24', '192.168.30.1'),
            host('PC6', '172.16.10.10/24', '172.16.10.1'), host('PC7', '172.16.20.10/24', '172.16.20.1')]
    links = [L('R1', 'G0/0/1', 'S1', 'G0/1'), L('S1', 'F0/1', 'S2', 'F0/1'), L('PC1', 'Fa0', 'S1', 'F0/6'),
             L('PC2', 'Fa0', 'S1', 'F0/11'), L('PC3', 'Fa0', 'S2', 'F0/6'), L('PC4', 'Fa0', 'S2', 'F0/11'),
             L('PC5', 'Fa0', 'S2', 'F0/18'), L('MLS1', 'G1/0/1', 'S3', 'G0/1'), L('MLS1', 'G1/0/24', 'R1', 'G0/0/2'),
             L('PC6', 'Fa0', 'S3', 'F0/6'), L('PC7', 'Fa0', 'S3', 'F0/11')]
    T = [('ping', 'PC1', '192.168.10.11', True), ('ping', 'PC2', '192.168.20.11', True),
         ('ping', 'PC1', '192.168.20.10', True), ('ping', 'PC1', '192.168.30.10', True),
         ('ping', 'PC4', '192.168.99.11', True), ('ping', 'S1', '192.168.99.12', True),
         ('ping', 'PC6', '172.16.20.10', True), ('ping', 'PC6', '192.168.10.10', True),
         ('ping', 'PC7', '192.168.30.10', True)]
    return Net(devs, links), T, []


def lab4():
    lab = 'lab04-stp-etherchannel-port-security'
    devs = [Device(n, 'switch', '2960', load(lab, n)) for n in ('S1', 'S2', 'S3')] + [
        host('PC1', '192.168.10.11/24'), host('PC2', '192.168.20.12/24'),
        host('PC3', '192.168.10.13/24'), host('PC4', '192.168.20.14/24')]
    links = [L('S1', 'F0/1', 'S2', 'F0/1'), L('S1', 'F0/2', 'S2', 'F0/2'), L('S1', 'F0/3', 'S3', 'F0/3'),
             L('S1', 'F0/4', 'S3', 'F0/4'), L('S2', 'F0/3', 'S3', 'F0/1'), L('S2', 'F0/4', 'S3', 'F0/2'),
             L('PC1', 'Fa0', 'S1', 'F0/6'), L('PC2', 'Fa0', 'S2', 'F0/18'), L('PC3', 'Fa0', 'S3', 'F0/6'),
             L('PC4', 'Fa0', 'S3', 'F0/18')]
    net = Net(devs, links)
    T = [('ping', 'PC1', '192.168.10.13', True), ('ping', 'PC2', '192.168.20.14', True),
         ('ping', 'PC1', '192.168.20.12', False), ('ping', 'S1', '192.168.99.2', True),
         ('ping', 'S1', '192.168.99.3', True)]
    checks = []
    for v, exp in ((1, 'S1'), (10, 'S1'), (99, 'S1'), (20, 'S2')):
        got = net.stp_root(v)
        checks.append((f'STP root for VLAN {v} is {exp}', got == exp, f'got {got}'))
    for sw, port, vlan in (('S1', 'F0/6', 10), ('S2', 'F0/18', 20), ('S3', 'F0/6', 10), ('S3', 'F0/18', 20)):
        i = net.dev[sw].cfg.ifs.get(norm(port))
        ok = bool(i and i.portsec.get('enabled') and {'portfast', 'bpduguard'} <= i.stp and i.sw.get('access') == vlan)
        checks.append((f'{sw} {port}: VLAN {vlan}, port security, PortFast, BPDU Guard', ok, ''))
    for n in ('S1', 'S2', 'S3'):
        checks.append((f'{n} runs Rapid PVST+', net.dev[n].cfg.stp_mode == 'rapid-pvst', ''))
    return net, T, checks


LAB5 = 'lab05-static-routing-ospf'


def lab5_devices(variant):
    cfgs = {n: open(os.path.join(ROOT, 'labs', LAB5, 'solutions', n + '.txt')).read()
            for n in ('R1', 'R2', 'R3', 'ISP')}
    if variant == 'static':
        static = open(os.path.join(ROOT, 'labs', LAB5, 'solutions', 'static-routes-part2.txt')).read()
        blocks = dict(re.findall(r'! --- (\S+) ---\n(.*?)(?=\n! ---|\Z)', static, re.S))
        for n in ('R1', 'R2', 'R3'):
            txt = re.sub(r'router ospf 10\n( .*\n)*', '', cfgs[n])
            txt = re.sub(r'\n ip ospf .*', '', txt)
            txt = re.sub(r'\nip route .*', '', txt)
            cfgs[n] = txt.replace('\nend\n', '\n' + blocks[n].strip() + '\nend\n')
    devs = [Device(n, 'router', '4331', Config(cfgs[n], f'labs/{LAB5}/solutions/{n}.txt ({variant})'))
            for n in cfgs]
    devs += [Device('S1', 'switch', '2960'), Device('S2', 'switch', '2960'),
             host('PC1', '192.168.1.10/24', '192.168.1.1'), host('PC2', '192.168.2.10/24', '192.168.2.1'),
             host('Web-Server', '203.0.113.10/24', '203.0.113.1', services=['http'])]
    return devs


LAB5_LINKS = [L('PC1', 'Fa0', 'S1', 'F0/1'), L('S1', 'G0/1', 'R1', 'G0/0/0'), L('PC2', 'Fa0', 'S2', 'F0/1'),
              L('S2', 'G0/1', 'R2', 'G0/0/0'), L('R1', 'G0/0/1', 'R2', 'G0/0/1'), L('R1', 'G0/0/2', 'R3', 'G0/0/1'),
              L('R2', 'G0/0/2', 'R3', 'G0/0/2'), L('R3', 'G0/0/0', 'ISP', 'G0/0/0'),
              L('ISP', 'G0/0/1', 'Web-Server', 'Fa0')]
LAB5_TESTS = [('ping', 'PC1', '192.168.2.10', True), ('ping', 'PC1', '192.168.3.1', True),
              ('ping', 'PC1', '203.0.113.10', True), ('http', 'PC1', '203.0.113.10', True),
              ('ping', 'PC2', '203.0.113.10', True), ('ping', 'PC2', '192.168.3.1', True)]


def lab5_static():
    net = Net(lab5_devices('static'), LAB5_LINKS)
    devs = lab5_devices('static')
    n2 = Net(devs, [l for l in LAB5_LINKS if l != L('R1', 'G0/0/1', 'R2', 'G0/0/1')])   # R1-R2 cable removed
    ok, why = n2.talk('PC1', '192.168.2.10')
    r = [x for x in n2.rib['R1'] if str(x['net']) == '192.168.2.0/24']
    p = [x for x in net.rib['R1'] if str(x['net']) == '192.168.2.0/24']
    checks = [('primary static route (AD 1) used while R1-R2 link is up', bool(p and p[0]['ad'] == 1), str(p)),
              ('floating route (AD 5) installed when R1-R2 link is down', bool(r and r[0]['ad'] == 5), str(r)),
              ('PC1 -> PC2 still works via R3 when R1-R2 link is down', ok, why or '')]
    n2.errors = [e for e in n2.errors if 'connected but shut' not in e]
    net.errors += [f'(link-down scenario) {e}' for e in n2.errors]
    return net, LAB5_TESTS, checks


def lab5_ospf():
    net = Net(lab5_devices('ospf'), LAB5_LINKS)
    checks = []
    for n in ('R1', 'R2', 'R3'):
        checks.append((f'{n} has 2 OSPF neighbours', len(net.ospf_nbrs.get(n, [])) == 2,
                       str(net.ospf_nbrs.get(n))))
    rib = {str(r['net']): r for r in net.rib['R1']}
    checks.append(('R1 learns 192.168.3.0/24 (loopback advertised as /24)',
                   rib.get('192.168.3.0/24', {}).get('src') == 'O', ''))
    checks.append(('R1 has an O*E2 default route', rib.get('0.0.0.0/0', {}).get('src') == 'O*E2', ''))
    checks.append(('R1 metric to 192.168.2.0/24 is 20 (ref-bw 10000)',
                   rib.get('192.168.2.0/24', {}).get('metric') == 20, str(rib.get('192.168.2.0/24'))))
    return net, LAB5_TESTS, checks


def lab6():
    lab = 'lab06-dhcp-nat-acl-capstone'
    devs = [Device('R1', 'router', '4331', load(lab, 'R1')), Device('ISP', 'router', '4331', load(lab, 'ISP')),
            Device('S1', 'switch', '2960', load(lab, 'S1')),
            host('Admin-PC', '192.168.99.10/24', '192.168.99.1'), host('PC1'), host('PC2'), host('Guest-Laptop'),
            host('Int-Server', '192.168.30.10/24', '192.168.30.1', services=['http', 'dhcp'],
                 pools=[dict(gw=ipa.ip_address('192.168.20.1'), start=ipa.ip_address('192.168.20.11'),
                             dns=ipa.ip_address('203.0.113.10'))]),
            host('Internet-Web', '203.0.113.10/24', '203.0.113.1', services=['http', 'dns'])]
    links = [L('ISP', 'G0/0/1', 'Internet-Web', 'Fa0'), L('ISP', 'G0/0/0', 'R1', 'G0/0/0'),
             L('R1', 'G0/0/1', 'S1', 'G0/1'), L('Admin-PC', 'Fa0', 'S1', 'F0/2'), L('PC1', 'Fa0', 'S1', 'F0/6'),
             L('PC2', 'Fa0', 'S1', 'F0/7'), L('Guest-Laptop', 'Fa0', 'S1', 'F0/11'),
             L('Int-Server', 'Fa0', 'S1', 'F0/24')]
    net = Net(devs, links)
    checks = []
    for h, exp in (('PC1', '192.168.10.11/24'), ('PC2', '192.168.10.12/24'), ('Guest-Laptop', '192.168.20.11/24')):
        ok, info = net.dhcp(h)
        checks.append((f'DHCP {h} gets {exp}', ok and str(net.dev[h].host['ip']) == exp, info))
    T = [('ping', 'PC1', '203.0.113.10', True), ('http', 'PC1', '203.0.113.10', True),
         ('ping', 'PC2', '203.0.113.10', True),
         ('ping', 'Guest-Laptop', '203.0.113.10', True), ('http', 'Guest-Laptop', '203.0.113.10', True),
         ('dns', 'Guest-Laptop', '203.0.113.10', True),
         ('ping', 'Guest-Laptop', '192.168.10.11', False), ('ping', 'Guest-Laptop', '192.168.30.10', False),
         ('http', 'Guest-Laptop', '192.168.30.10', False), ('ping', 'Guest-Laptop', '192.168.20.1', False),
         ('http', 'Internet-Web', '209.165.200.230', True), ('ping', 'Internet-Web', '209.165.200.230', False),
         ('ping', 'PC1', '192.168.30.10', True), ('http', 'PC1', '192.168.30.10', True),
         ('ping', 'Admin-PC', '192.168.30.10', True), ('ssh', 'Admin-PC', '192.168.99.1', True),
         ('ssh', 'PC1', '192.168.10.1', False), ('ping', 'Admin-PC', '203.0.113.10', False),
         ('ping', 'Internet-Web', '192.168.10.11', False)]
    return net, T, checks


LABS = [('1', 'Lab 01', lab1), ('2', 'Lab 02', lab2), ('3', 'Lab 03', lab3), ('4', 'Lab 04', lab4),
        ('5', 'Lab 05 (static routing, end of Part 2)', lab5_static), ('5', 'Lab 05 (OSPF, final)', lab5_ospf),
        ('6', 'Lab 06', lab6)]
PROTO = {'ping': ('icmp', None), 'http': ('tcp', 80), 'ssh': ('tcp', 22), 'telnet': ('tcp', 23),
         'dns': ('udp', 53)}


def main(argv):
    want = set(argv)
    total = 0
    for num, title, fn in LABS:
        if want and num not in want:
            continue
        net, tests, checks = fn()
        lines, fails = [], 0
        for name, ok, info in checks:
            lines.append(('PASS' if ok else 'FAIL', name + ('' if ok or not info else f' ({info})')))
            fails += not ok
        for kind, src, dst, expect in tests:
            proto, port = PROTO[kind]
            ok, why = net.talk(src, dst, proto, port)
            good = ok == expect
            lines.append(('PASS' if good else 'FAIL',
                          f'{kind:6} {src} -> {dst}: expect {"OK" if expect else "blocked"}, '
                          f'got {"OK" if ok else "blocked"}' + ('' if ok else f' ({why})')))
            fails += not good
        for e in net.errors:
            lines.append(('FAIL', e))
            fails += 1
        for w in net.warnings:
            lines.append(('WARN', w))
        print(f'\n=== {title}: {"OK" if not fails else str(fails) + " problem(s)"} ===')
        for status, text in lines:
            print(f'  [{status}] {text}')
        total += fails
    print(f'\nTotal problems: {total}')
    return 1 if total else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
