# Lab 04 – Answer Key

## Part 1, Step 6
With 3 switches and 6 links, a loop-free tree needs only **2** links. Before tuning, the root bridge is the switch with the lowest MAC address (priority 32768+VLAN is equal on all). Results vary because Packet Tracer assigns random MAC addresses, but the pattern is always:
- Root bridge: all its ports are **Designated / FWD**.
- Each non-root switch: exactly **one Root port** (lowest cost to root, tie → lowest sender BID → lowest sender port ID, i.e. usually F0/1 or F0/3 rather than F0/2 or F0/4).
- On the non-root ↔ non-root links, the switch with the lower BID has the designated port; the other end is **Alternate / BLK**.
- Only **2 links** (the root ports' links) forward on both ends; on the other 4 links one end blocks.

## Part 5 – Faults
| Fault | Symptom | Command | Fix |
|-------|---------|---------|-----|
| F1 | Po1 down `(SD)`, traffic takes S1–S3–S2 | `show etherchannel summary` | Set one side to `active` |
| F2 | S3 becomes root for VLAN 10; suboptimal paths | `show spanning-tree vlan 10` | `no spanning-tree vlan 10 priority 0` (and Root Guard, see challenge) |
| F3 | Fa0/2 shows `(s)` suspended or `(I)` in Po3 | `show etherchannel summary`, `show run int f0/2` | Make member settings identical to the port-channel |
| F4 | PC1 isolated, port `err-disabled` | `show interfaces status`, `show port-security` | Remove offending device, `shutdown`/`no shutdown` |
| F5 | Po3 down: auto + auto never forms | `show etherchannel summary` | One side `desirable` |
| F6 | PC4 can't reach PC2 | `show vlan brief` | `switchport access vlan 20` on S3 F0/18 |

## Challenge
1. ```
   S1(config)# interface port-channel 2
   S1(config-if)# spanning-tree guard root
   S2(config)# interface port-channel 3
   S2(config-if)# spanning-tree guard root
   ```
   When S3 sends a superior BPDU (priority 0), the port goes into `root-inconsistent` (BKN*) state: `show spanning-tree inconsistentports`.
2. With Po1 down, S2 loses its direct link to S1 (root of VLAN 10). Po3 on S2 becomes its root port, and the previously alternate end of Po3 changes to forwarding. Verify with `show spanning-tree vlan 10` on S2 and S3. For VLAN 20 (S2 root), S1 uses Po2 → S3 → Po3.

## Review Questions
1. Bridge priority (4 bits, multiples of 4096), extended system ID (12 bits = VLAN ID) and MAC address (48 bits). PVST+ runs one STP instance per VLAN, so the VLAN ID makes each instance's BID unique while letting the same switch be root for some VLANs and not for others.
2. RSTP roles: Root, Designated, Alternate, Backup (and Disabled). States: Discarding, Learning, Forwarding.
3. A PortFast port goes straight to forwarding; if a switch is connected, a temporary Layer 2 loop can form before STP detects it. (BPDU Guard protects against this mistake.)
4. Active sends LACP PDUs to initiate negotiation; passive only responds. Two passive ports never form a channel.
5. Speed, duplex, switchport mode (access/trunk), access VLAN or native VLAN, allowed VLAN list, and (for LACP/PAgP) compatible modes.
6. **protect** drops silently; **restrict** drops, logs and increments the violation counter; **shutdown** (default) err-disables the port.
7. `sticky` dynamically learns MAC addresses and adds them to the running-config as secure addresses. If the running-config is saved, the learned addresses survive a reload.
