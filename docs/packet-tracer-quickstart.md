# Packet Tracer Quick-Start Guide

## 1. Installing Packet Tracer

1. Create a free account at the Cisco Networking Academy (Skills for All) website.
2. Enroll in the free *Getting Started with Cisco Packet Tracer* course – the download link is available there.
3. Download the installer for your OS (Windows, macOS or Ubuntu) and install it.
4. On first launch, log in with your Networking Academy account (or choose *Guest Login* for limited saving).

> ⚠️ Use version **8.2 or newer**. Older versions may not include the ISR4331 or 3650 models.

## 2. The Main Window

```
+---------------------------------------------------------------------------+
| Menu bar  (File, Edit, Options, View, Tools, Extensions, Window, Help)     |
| Main toolbar (New, Open, Save, Print, Activity Wizard, Zoom, ...)          |
+---------------------------------------------------------------------------+
| Logical / Physical tabs                                     | Common tools |
|                                                             | Select       |
|                      WORKSPACE                              | Inspect      |
|                                                             | Delete       |
|                                                             | Resize       |
|                                                             | Note / Draw  |
|                                                             | Add PDU      |
+---------------------------------------------------------------------------+
| Device-Type Selection box | Device-Specific Selection box | Realtime/Sim  |
+---------------------------------------------------------------------------+
```

| Area | Use |
|------|-----|
| **Logical workspace** | Where you place devices and draw cables (used in all labs) |
| **Physical workspace** | Shows racks, buildings, cities – not used in these labs |
| **Device-Type Selection** (bottom-left) | Categories: Network Devices (Routers, Switches, Hubs, Wireless), End Devices, Components, Connections |
| **Device-Specific Selection** | Specific models, e.g. ISR4331, 2960-24TT, PC-PT |
| **Realtime / Simulation** (bottom-right) | Realtime = live network; Simulation = step through packets one at a time |

## 3. Placing and Renaming Devices

1. Click **Network Devices → Routers**, then drag **4331** into the workspace.
2. Click the device label (e.g. *Router0*) and type a new display name (e.g. *R1*).
   > 💡 The display name is **not** the hostname. You still need the `hostname` command in the CLI.

## 4. Cabling

Click **Connections** (lightning bolt icon) and pick a cable:

| Cable | Use |
|-------|-----|
| **Automatically Choose Connection Type** | Avoid in labs – you should learn to choose cables |
| **Console** (light blue) | PC RS-232 → device Console port |
| **Copper Straight-Through** (solid black) | Different device types: PC ↔ switch, switch ↔ router |
| **Copper Cross-Over** (dashed black) | Same device types: switch ↔ switch, PC ↔ PC, router ↔ router, PC ↔ router |
| **Fiber** (orange) | Fiber ports (e.g. `G0/0/2` SFP on some models) |
| **Serial DCE / DTE** (red) | Serial WAN links (requires a serial module) |

> 💡 Modern Cisco devices support Auto-MDIX, so in Packet Tracer a straight-through cable between two switches usually still comes up. In these labs, use the *correct* cable anyway.

Link lights:

| Color | Meaning |
|-------|---------|
| 🟢 Green triangle | Link up and forwarding |
| 🟠 Orange/amber | Switch port in STP listening/learning or blocking |
| 🔴 Red | Link down (interface shut down or wrong cable) |

## 5. Accessing a Device

| Method | How |
|--------|-----|
| **CLI tab** | Click the device → **CLI** tab. Quickest way. |
| **Console from a PC** | Connect a console cable, then on the PC: **Desktop → Terminal → OK** |
| **SSH/Telnet from a PC** | PC **Desktop → Command Prompt** → `ssh -l admin 192.168.10.1` |

## 6. Configuring End Devices

On a PC: **Desktop → IP Configuration**

- Choose **Static** and enter IPv4 Address, Subnet Mask, Default Gateway, DNS Server.
- Or choose **DHCP** to request an address.
- IPv6 section: **Automatic** (SLAAC) or **Static**.

Use **Desktop → Command Prompt** for `ping`, `tracert`, `ipconfig /all`, `arp -a`.

## 7. Simulation Mode

1. Click **Simulation** (bottom-right).
2. Click **Edit Filters** and select only the protocols you want to see (e.g. ICMP, ARP).
3. Use the **Add Simple PDU** (closed envelope) tool: click source device, then destination.
4. Press **Capture/Forward** (or **Play**) to watch packets hop by hop. Click a packet envelope to inspect OSI layers.

## 8. Useful Shortcuts and Tips

- **Ctrl+S** – Save often! Packet Tracer has no autosave.
- **Fast Forward Time** (bottom-left clock) – speeds up STP convergence and link-up.
- **Options → Preferences → Show Port Labels When Mouse Over / Always Show Port Labels** – very useful.
- **Options → Preferences → Hide → uncheck "Hide Link Lights"** if link lights are not shown.
- Adding modules to a device: click device → **Physical** tab → turn the **power switch off**, drag module into slot, turn power back **on**.
