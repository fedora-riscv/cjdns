# cjdns

[Upstream](README.md)

#### *Networking Reinvented*

Cjdns implements an encrypted IPv6 network using public-key cryptography for
address allocation and a distributed hash table for routing. This provides
near-zero-configuration networking, and prevents many of the security and
scalability issues that plague existing networks.

## Why?

If you're here from the hyperboria docs, you're already sold - proceed to
Installing.  But why should a Fedora user install cjdns?  I'll mention just two
contrasting use cases, one mundane and the other paranoid.

### VPN Mesh

Configuring a point to point VPN connection with openvpn is fairly
straightforward, as is configuring a centralized VPN server and clients.
However, when every node in the VPN network needs to talk securely with many
other nodes, relaying every packet through the central server becomes a drag on
performance, and a single point of failure.  Mesh VPNs, like tinc and cjdns
automatically create point to point connections based on a shared overall
configuration.  Each node only needs a connection to one or more peers (that
can be reused) to get things started.  

With cjdns, however, things are much better than with tinc.  On a local LAN or
mesh with broadcast, it is zero configuration.  Peers are automatically
discovered via the 0xFC00 layer 2 protocol.  There is no shared configuration -
the only thing required is adding one or more (for redundancy) internet peers
when no peers on the local LAN or mesh are available.  Even better, when your
node is mobile, and you have geographically separated peers configured, cjdns
automatically switches to a faster peer as the relative performance changes.

### Darknet

In a widespread VPN, address assignment must be coordinated by a central
authority.  The internet also uses centralized IP assignment, which means a
government can take away your IP at any time.  Cjdns uses CryptoGraphic
Addressing (CGA).  Your IP6 is the double SHA-512 of your public key truncated
to 128 bits.  Your IP is as safe as the private key pair which produced it, and
cannot [insert standard cryptography disclaimer] be spoofed.  Most mesh VPNs
decrypt packets before routing to a new node.  This means that if a relay node
is compromised in a conventional VPN, it can see and even alter packets.  All
cjdns packets are end to end encrypted - relay nodes are untrusted.  Cjdns is
source routed, there is no centralized routing.  If a node is "blackholing"
your packets for some reason - simply doesn't route through that node anymore.
(But see Security below.)  The usual security problems with source routing
don't apply because cjdns IPs can't be (easily) spoofed.

## Startup

The key part of cjdns is the cjdroute background daemon.  To start cjdroute:

    systemctl start cjdns

This will generate `/etc/cjdroute.conf` pre-populated with random keys and
passwords.  At first startup, cjdroute looks for neighboring cjdns peers
on all active network interfaces using a layer 2 (e.g. ethernet) protocol.
This is exactly what you want if you are on a LAN or wifi mesh.  If you only
have a conventional "clearnet" ISP, see the [upstream](README.md) README for
instructions on adding peers using the UDP protocol.  (Search for "Find a
friend".)

After adding peers to `/etc/cjdroute.conf`, restart cjdroute with:

    systemctl restart cjdns

To have cjdroute start whenever you boot, use

    systemctl enable cjdns

If you are on a laptop and suspend or hibernate it, cjdroute will take a few
minutes to make coffee and figure out what just happened when it wakes up.  You
can speed this up dramatically with:

    systemctl enable cjdns-resume

The resume service restarts cjdns when the system wakes up from sleep.

For rhel6, use ```start cjdns``` instead of systemctl - ditto for restart
and stop.

## Security

By default, Fedora Workstation will treat the tun device created by cjdroute as
"public", with SSH being the only incoming port allowed.  There is no
additional exposure with cjdns and the default Fedora firewall.  If you have
modified the firewall config beyond opening additional incoming ports, be sure
that the cjdns tun is treated as public - because anyone in the world can
attempt to connect to you through it.  Sometimes, people configure their
firewall to treat all tun devices as "VPN", and therefore somewhat more
trusted.  This would be a mistake with cjdns.  It is a VPN, for sure, but one
anyone in the world can join.

Public keys for cjdns are based on Elliptic Curves.  There is a known quantum
algorithm that could be used to crack them if quantum computers with sufficient
qubits are ever built.  The solution when that happens is larger keys - which
are more cumbersome.

The Distributed Hash Table algorithm is a core component of cjdns - which is
vulnerable to a Denial of Service attack known as "Sybil".  This attack can
block specific updates to the DHT - to prevent your node from joining a mesh,
for instance.

On the positive side, you can safely use telnet to cjdns IPs and the http
protocol is automatically encrypted (but you need a secure DNS or raw ip to be
sure you are talking to the right node).  Many other protocols are
automatically encrypted while using cjdns.  In general, connecting to a raw
cjdns IP is functionally equivalent to SSL/TLS with both client and server
authentication.

Since the cjdroute core routing code parses network packets from untrusted
sources, it is a security risk and is heavily sandboxed.  It runs as the cjdns
user in a chroot jail in an empty directory, with RLIMIT_NPROC set to 1 to
disable forking.  Seccomp is used to limit available system calls to only those
actually needed.  Installing the cjdns-selinux package installs a targeted
selinux policy that also restricts what the privileged process can access.

### Routing security

If cjdns is not running, cjdns packets will get routed in plaintext
to your default gateway by default.  An attacker could then play
man-in-the-middle.  If your default gateway is running cjdns, this
could even happen accidentally.

This can be blocked by restricting ```fc00::/8``` to the interface 
used by cjdroute in the firewall.   An even simpler solution is
to not have a "default" route.  Instead route ```2000::/3``` to your
gateway.  All globally routable ips begin with ```001``` as the first
three bits.

### Application security

The squid cache package default config allows ```fc00::/7``` unrestricted
access to the proxy.  If the proxy port is not otherwise firewalled,
you probably want to change this to ```fd00::/8``` when using cjdns
on the proxy server.  Apart from that default config, squid works very
well with cjdns - you can allow specific cjdns ips unrestricted access:

```
acl adultpcs src fc25:dede:dede:dede:dede:dede:dede:dede
acl adultpcs src fc37:daaa:daaa:daaa:daaa:daaa:daaa:daaa 
http_access allow adultpcs
```

## Advanced config

You may install a network service that depends on cjdns, for instance you might
install thttpd to serve up
[nodeinfo.json](https://docs.meshwith.me/en/cjdns/nodeinfo.json.html).  If
thttpd is configured to listen only on your cjdns IP, then it will not start
until cjdns is up and running.  Add ```After=cjdns-wait-online.service``` to
```thttpd.service``` to hold off starting the service until cjdns has the
tunnel up and ready.

