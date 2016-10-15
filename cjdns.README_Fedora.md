# cjdns

[Upstream](README.md)

#### *Networking Reinvented*

Cjdns implements an encrypted IPv6 network using public-key cryptography for
address allocation and a distributed hash table for routing. This provides
near-zero-configuration networking, and prevents many of the security and
scalability issues that plague existing networks.

## Startup

The key part of cjdns is the cjdroute background daemon.  To start cjdroute:

    systemctl start cjdns

This will generate `/etc/cjdroute.conf` pre-populated with random keys and
passwords.  At first startup, cjdroute looks for neighboring cjdns peers
on all active network interfaces using a layer 2 (e.g. ethernet) protocol.
This is exactly what you want if you are on a wifi mesh.  If you only have a
conventional "clearnet" ISP, see the [upstream](README.md) README for
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

##Security

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

##Routing security

If cjdns is not running, cjdns packets will get routed in plaintext
to your default gateway by default.  An attacker could then play
man-in-the-middle.  If your default gateway is running cjdns, this
could even happen accidentally.

This can be blocked by restricting ```fc00::/8``` to the interface 
used by cjdroute in the firewall. 

## Advanced config

You may install a network service that depends on cjdns, for instance you might
install thttpd to serve up
[nodeinfo.json](https://docs.meshwith.me/en/cjdns/nodeinfo.json.html).  If
thttpd is configured to listen only on your cjdns IP, then it will not start
until cjdns is up and running.  Add ```After=cjdns-wait-online.service``` to
```thttpd.service``` to hold off starting the service until cjdns has the
tunnel up and ready.

