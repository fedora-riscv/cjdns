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
