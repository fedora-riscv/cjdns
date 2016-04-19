
# Fedora review: http://bugzilla.redhat.com/1268716

# Use the optimized libnacl embedded with cjdns
%global use_embedded 0
# Use libsodium instead of nacl
%global use_libsodium 0

%if 0%{use_libsodium}
%global nacl_name libsodium
%global nacl_version 1.0.5
%global nacl_lib %{_libdir}/libsodium.so
%else
%global nacl_name nacl
%global nacl_version 20110221
%global nacl_lib %{_libdir}/libnacl.so
%endif

%if 0%{?rhel} >= 5 && 0%{?rhel} < 7
%global use_systemd 0
%else
%global use_systemd 1
%endif

%if 0%{?rhel} == 6
%global use_upstart 1
%else
%global use_upstart 0
%endif

# FIXME: Needs dependencies and install www dir someplace reasonable.
%global with_admin 0

# FIXME: python tools need to make cjdnsadmin a proper python package
%global with_python 1

%{!?__restorecon: %global __restorecon /sbin/restorecon}

Name:           cjdns
# major version is cjdns protocol version:
Version:        17.3
Release:        12%{?dist}
Summary:        The privacy-friendly network without borders
Group:          System Environment/Base
# cjdns is all GPLv3 except libuv which is MIT and BSD and ISC
# cnacl is unused except when use_embedded is true
License:        GPLv3 and MIT and BSD and ISC
URL:            http://hyperboria.net/
Source0: https://github.com/cjdelisle/cjdns/archive/%{name}-v%{version}.tar.gz
Source1: cjdns.README_Fedora.md
# Add targeted selinux policy
Patch0: cjdns.selinux.patch
# Allow python2.6 for build.  Python is not used during the build
# process.  The python tools allegedly depend on python2.7, but that can
# be in Requires for the subpackage.
Patch1: cjdns.el6.patch
# Fix RLIMIT_NPROC - setuid() bug.   In its low priv process, cjdroute calls 
#
#   setrlimit(RLIMIT_NPROC, &(struct rlimit){ 0, 0 })
#
# which on recent kernels prevents fork() or exec() after the following
# setuid().  This is due to changes discussed here:
#
# https://lwn.net/Articles/451985/
# 
# On the 2.6.32 kernel used by EL6, the above causes setuid() to fail.
# This patch sets RLIMIT_NPROC to { 1, 1 } instead, which prevents
# fork(), but not exec, and calls setgroups() before setuid().
Patch2:  cjdns.nprocs.patch
# Change defaults generated by cjdroute --genconf
Patch4:  cjdns.genconf.patch
# Patch contributed init scripts to put cjdroute in /usr/sbin and
# add additional service options.
Patch5:  cjdns.sbin.patch
# Patch make.js to use dynamic nacl library
Patch6:  cjdns.dyn.patch
# Patch to use _LINUX_CAPABILITY_3
Patch7:  cjdns.cap3.patch
# Patch some source files to ignore selected warnings that break gcc6 builds
Patch8:  cjdns.warnings.patch
# Man pages
Patch9:  cjdns.man.patch
# Patch some bugs in nodejs tools
Patch10: cjdns.tools.patch
# Alternate dynamic library patch to use libsodium
Patch11: cjdns.sodium.patch

BuildRequires:  nodejs, nodejs-ronn

# Automated package review hates explicit BR on make, but it *is* needed
BuildRequires:  make

%if !%{use_embedded}
# x86_64 and ARM libnacl are not compiled with -fPIC before Fedora release 11.
BuildRequires:  %{nacl_name}-devel >= %{nacl_version}
%endif
%if %{use_systemd}
# systemd macros are not defined unless systemd is present
BuildRequires: systemd
Requires: systemd
Requires(post): systemd
Requires(preun): systemd
Requires(postun): systemd
%endif
Requires(pre): shadow-utils
Provides: bundled(libuv) = 0.11.4

%description
Cjdns implements an encrypted IPv6 network using public-key cryptography for
address allocation and a distributed hash table for routing. This provides
near-zero-configuration networking, and prevents many of the security and
scalability issues that plague existing networks.

%package selinux
Summary: Targeted SELinux policy module for cjdns
Group: System Environment/Base
BuildRequires: policycoreutils, checkpolicy, selinux-policy-devel
Requires: policycoreutils, selinux-policy-targeted
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description selinux
Targeted SELinux policy module for cjdns.

# FIXME: keep C tools separate?
%package tools
Summary: Nodejs tools for cjdns
Group: System Environment/Base
Requires: nodejs, %{name} = %{version}-%{release}
BuildArch: noarch

%description tools
Nodejs tools for cjdns. Highlights:
peerStats          show current peer status
cjdnslog           display cjdroute log
cjdns-traceroute   trace route to cjdns IP
sessionStats       show current crypto sessions

%package python
Summary: Python tools for cjdns
Group: System Environment/Base
Requires: python, %{name} = %{version}-%{release}
BuildArch: noarch

%description python
Python tools for cjdns.

%package graph
Summary: Python tools for cjdns
Group: System Environment/Base
Requires: %{name}-python = %{version}-%{release}, python-networkx
BuildArch: noarch

%description graph
Python graphing tools for cjdns.

%prep
%setup -qn cjdns-%{name}-v%{version}
%patch0 -b .selinux
%if 0%{?rhel} == 6
%patch1 -b .el6
%endif

%patch2 -b .nprocs
%patch4 -b .genconf
%patch5 -b .sbin

%if !%{use_embedded}
# use system nacl library if provided.  
if test -x %{nacl_lib}; then
%if 0%{use_libsodium}
%patch11 -b .sodium
%else
%patch6 -b .dyn
%endif
  rm -rf node_build/dependencies/cnacl
# use static library if system nacl doesn't provide dynamic
elif test -d %{_includedir}/nacl && test -r %{_libdir}/libnacl.a; then
  cd node_build/dependencies
  rm -rf cnacl
  mkdir -p cnacl/jsbuild
  ln -s %{_libdir}/libnacl.a cnacl/jsbuild
  ln -s %{_includedir}/nacl cnacl/jsbuild/include
  cd -
fi
%endif

%patch7 -b .cap3

%if !0%{?rhel} || 0%{?rhel} > 6
%patch8 -b .warnings
%endif

%patch9 -b .man
%patch10 -b .tools

cp %{SOURCE1} README_Fedora.md

# Remove #!env from python scripts
chmod a+x contrib/python/cjdnsadmin/cli.py
find contrib/python/cjdnsadmin ! -executable -name "*.py" |
        xargs sed -e '\,^#!/usr/bin/env, d' -i
find contrib/python -type f |
        xargs sed -e '1 s,^#!/usr/bin/env ,#!/usr/bin/,' -i 

# Remove #!env from nodejs scripts
find tools -type f | xargs grep -l '^#!\/usr\/bin\/env ' |
        xargs sed -e '1 s,^#!/usr/bin/env ,#!/usr/bin/,' -i

# Remove unpackaged code with undeclared licenses
%if %{with_admin}
rm -rf contrib/nodejs   # GPLv3 and ASL 2.0
%endif
rm -rf contrib/http     # GPLv2 and MIT

# FIXME: grep Version_CURRENT_PROTOCOL util/version/Version.h and
# check that it matches major %%{version}

%build
cd contrib/selinux
ln -s /usr/share/selinux/devel/Makefile .
make 
cd -
# nodejs based build system
CJDNS_RELEASE_VERSION="%{name}-%{version}-%{release}" ./do

# FIXME: use system libuv on compatible systems
# bundled libuv is 0.11.4 with changes:
# https://github.com/cjdelisle/cjdns/commits/master/node_build/dependencies/libuv

%install
%if 0%{?rhel} == 5
 rm -rf %{buildroot}  # needed on RHEL5
%endif

# the main switch process
mkdir -p %{buildroot}%{_sbindir}
install -p cjdroute %{buildroot}%{_sbindir}

# init support
%if %{use_upstart}
mkdir -p %{buildroot}%{_sysconfdir}/init
install -pm 644 contrib/upstart/cjdns.conf %{buildroot}%{_sysconfdir}/init
%endif
%if %{use_systemd}
mkdir -p %{buildroot}%{_unitdir}
install -pm 644 contrib/systemd/cjdns*.service %{buildroot}%{_unitdir}
%endif

# chroot 
mkdir -p %{buildroot}/var/empty/cjdns

# install selinux modules
mkdir -p %{buildroot}%{_datadir}/selinux/targeted
install -pm 644 contrib/selinux/cjdns.pp %{buildroot}%{_datadir}/selinux/targeted
ln -f contrib/selinux/cjdns.{te,fc} .  # for doc dir

# install c and nodejs tools
mkdir -p %{buildroot}%{_libexecdir}/cjdns/{node_build,contrib}
install -p publictoip6 privatetopublic makekeys randombytes sybilsim \
        %{buildroot}%{_libexecdir}/cjdns
rm -f node_modules/nthen/.npmignore
cp -pr tools node_modules %{buildroot}%{_libexecdir}/cjdns


%if %{with_admin}
rm -f contrib/nodejs/admin/.gitignore
cp -pr contrib/nodejs/admin %{buildroot}%{_libexecdir}/cjdns
%endif

# symlinks for selected nodejs tools
mkdir -p %{buildroot}%{_bindir}
for t in peerStats sessionStats cjdnslog search dumpLinks dumptable \
         dumpRumorMill pathfinderTree pingAll; do
  ln -sf %{_libexecdir}/cjdns/tools/$t %{buildroot}%{_bindir}
done
for t in traceroute; do
  ln -sf %{_libexecdir}/cjdns/tools/$t %{buildroot}%{_bindir}/cjdns-$t
done

# symlinks for selected C tools
for t in publictoip6 randombytes makekeys; do
  ln -sf %{_libexecdir}/cjdns/$t %{buildroot}%{_bindir}
done

# cjdns-online script
install -pm 755 contrib/systemd/cjdns-online.sh \
        %{buildroot}%{_bindir}/cjdns-online

# man pages
mkdir -p %{buildroot}%{_mandir}/man1
mkdir -p %{buildroot}%{_mandir}/man5
mkdir -p %{buildroot}%{_mandir}/man8
install -pm 644 doc/man/cjdroute.conf.5 %{buildroot}%{_mandir}/man5
cd contrib/doc
for m in *.md; do
  case ${m%.md} in
  traceroute) M="1"
    ronn-nodejs $m >%{buildroot}%{_mandir}/man$M/cjdns-${m%.md}.$M
    continue ;;
  privatetopublic|sybilsim) M="8" ;;
  *) M="1" ;;
  esac
  ronn-nodejs $m >%{buildroot}%{_mandir}/man$M/${m%.md}.$M
done
cd -

%if %{with_python}

# install python tools that pull in networkx for graphing
cp -pr contrib/python %{buildroot}%{_libexecdir}/cjdns

# These files are installed via doc and license
rm %{buildroot}%{_libexecdir}/cjdns/python/README.md
rm %{buildroot}%{_libexecdir}/cjdns/python/cjdns-dynamic.conf
rm %{buildroot}%{_libexecdir}/cjdns/python/cjdnsadmin/bencode.py.LICENSE.txt

# symlink python tools w/o conflict with nodejs tools or needing networkx
for t in pingAll.py trashroutes \
         getLinks ip6topk pktoip6 cjdnsa searches findnodes; do
  ln -sf %{_libexecdir}/cjdns/python/$t %{buildroot}%{_bindir}
done

# symlink python tools that pull in networkx for graphing
for t in drawgraph dumpgraph graphStats; do
  ln -sf %{_libexecdir}/cjdns/python/$t %{buildroot}%{_bindir}
done

%endif

%files
%{!?_licensedir:%global license %%doc}
%license LICENSE
%doc README.md README_*.md HACKING.md 
%attr(0100,root,root) /var/empty/cjdns
%attr(0755,root,root) %{_sbindir}/cjdroute
%ghost %attr(0600,root,root) %config(missingok,noreplace) %{_sysconfdir}/cjdroute.conf
%dir %{_libexecdir}/cjdns
%if %{use_upstart}
%{_sysconfdir}/init/*
%endif
%if %{use_systemd}
%{_unitdir}/*
%endif
%{_libexecdir}/cjdns/randombytes
%{_libexecdir}/cjdns/publictoip6
%{_libexecdir}/cjdns/privatetopublic
%{_libexecdir}/cjdns/sybilsim
%{_libexecdir}/cjdns/makekeys
%{_bindir}/randombytes
%{_bindir}/publictoip6
%{_bindir}/makekeys
%{_bindir}/cjdns-online
%{_mandir}/man1/*
%{_mandir}/man5/*
%{_mandir}/man8/*
%{_mandir}/man1/cjdns-online.1.gz
%{_mandir}/man1/cjdroute.1.gz
%{_mandir}/man1/makekeys.1.gz
%{_mandir}/man1/publictoip6.1.gz
%{_mandir}/man1/randombytes.1.gz

%pre
getent group cjdns > /dev/null || groupadd -r cjdns
getent passwd cjdns > /dev/null || /usr/sbin/useradd -g cjdns \
        -c "End to end encrypted IPv6 mesh" \
        -r -d %{_libexecdir}/cjdns -s /sbin/nologin cjdns
exit 0

%if %{use_systemd}

%post
%systemd_post cjdns.service

%postun
%systemd_postun_with_restart cjdns.service

%preun
%systemd_preun cjdns.service

%endif

%if %{use_upstart}

%preun
if [ "$1" -eq 0 ]; then
  /sbin/initctl stop cjdns
fi

%postun
if [ "$1" -ge 1 ]; then
  /sbin/initctl restart cjdns
fi

%endif

%files selinux
%doc cjdns.te cjdns.fc 
%{_datadir}/selinux/targeted/*

%post selinux
/usr/sbin/semodule -s targeted -i %{_datadir}/selinux/targeted/cjdns.pp \
        &>/dev/null || :
%{__restorecon} %{_sbindir}/cjdroute

%postun selinux
if [ $1 -eq 0 ] ; then
/usr/sbin/semodule -s targeted -r cjdns &> /dev/null || :
fi

%files tools
%if %{with_admin}
%{_libexecdir}/cjdns/admin
%endif
%{_libexecdir}/cjdns/tools
%{_libexecdir}/cjdns/node_build
%{_libexecdir}/cjdns/node_modules
%{_bindir}/peerStats
%{_bindir}/sessionStats
%{_bindir}/cjdnslog
%{_bindir}/dumpRumorMill
%{_bindir}/dumpLinks
%{_bindir}/pathfinderTree
%{_bindir}/dumptable
%{_bindir}/pingAll
%{_bindir}/search
%{_bindir}/cjdns-traceroute
%{_mandir}/man1/cjdns-traceroute.1.gz
%{_mandir}/man1/sessionStats.1.gz
%{_mandir}/man1/peerStats.1.gz

%files python
%doc contrib/python/README.md contrib/python/cjdns-dynamic.conf
%license contrib/python/cjdnsadmin/bencode.py.LICENSE.txt
%dir %{_libexecdir}/cjdns/python
%{_libexecdir}/cjdns/python/cexec
%{_libexecdir}/cjdns/python/cjdnsadminmaker.py*
%{_libexecdir}/cjdns/python/cjdnslog
%{_libexecdir}/cjdns/python/dumptable
%{_libexecdir}/cjdns/python/dynamicEndpoints.py*
%{_libexecdir}/cjdns/python/peerStats
%{_libexecdir}/cjdns/python/sessionStats
%{_libexecdir}/cjdns/python/cjdnsadmin
%{_libexecdir}/cjdns/python/pingAll.py*
%{_libexecdir}/cjdns/python/trashroutes
%{_libexecdir}/cjdns/python/getLinks
%{_libexecdir}/cjdns/python/ip6topk
%{_libexecdir}/cjdns/python/pktoip6
%{_libexecdir}/cjdns/python/cjdnsa
%{_libexecdir}/cjdns/python/searches
%{_libexecdir}/cjdns/python/findnodes
%{_bindir}/pingAll.py
%{_bindir}/trashroutes
%{_bindir}/getLinks
%{_bindir}/ip6topk
%{_bindir}/pktoip6
%{_bindir}/cjdnsa
%{_bindir}/searches
%{_bindir}/findnodes

%files graph
%{_libexecdir}/cjdns/python/drawgraph
%{_libexecdir}/cjdns/python/dumpgraph
%{_libexecdir}/cjdns/python/graphStats
%{_bindir}/drawgraph
%{_bindir}/dumpgraph
%{_bindir}/graphStats

%changelog
* Mon Apr 18 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-12
- Run modprobe only if /dev/tun not present - fixes running on openVZ
- Select nacl/libsodium with a macro
- Switch back to nacl for platforms that support it
- man page for peerStats

* Tue Apr  5 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-11
- Patch some bugs in traceroute and symlink to /usr/bin/cjdns-traceroute
- man page for cjdns-traceroute, sessionStats
- switch to libsodium instead of nacl

* Thu Mar 10 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-10
- Mark nodejs and selinux noarch
- Remove _isa from noarch subpackages.

* Thu Mar 10 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-9
- Strip /8 from IPs printed by cjdns-online
- Add GPL3+ to cjdns-online
- ghost /etc/cjdroute.conf
- Include _isa formula in subpackage requires.

* Tue Mar  8 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-8
- Add release to main package dependencies
- More man pages
- Restore missing cjdns-resume.service
- Add empty config to be owned by package

* Tue Mar  1 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-7
- Add explicit systemd dependency
- Add selinux-policy-targeted dependency
- Add version to main package dependencies
- Remove use of #!/usr/bin/env in nodejs tools
- Change all top level define to global
- Remove workaround for missing -fPIC on libnacl for X86_64 on f22.

* Mon Feb 29 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-6
- Man pages
- Move /usr/lib/cjdns to /usr/libexec/cjdns
- Move all C tools to main package, mark (nodejs) tools noarch

* Wed Feb 24 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-5
- Add use_embedded option
- Reorganize with use_systemd, use_upstart
- Set __restorecon only if not defined
- Use install instead of cp to set file modes
- Move randombytes,publictoip6 and /usr/lib/cjdns to main package
- Fix bad #! lines in contrib/python
- Patch util/Security.c to call setgroups(0,...) before setuid().

* Fri Feb 12 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-4
- Add Fedora README
- No libnacl on EL7 or EPEL7

* Tue Feb  2 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-3
- Add node_modules to tools
- Add #pragmas to ignore bogus warnings from gcc6
- Fix shift of signed int

* Mon Feb  1 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-2
- Fix extra line in updated sbin patch

* Mon Feb  1 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-1
- New upstream release
- Add cjdns-resume.service to restart cjdns on resume from sleep

* Tue Jan 19 2016 Stuart D. Gathman <stuart@gathman.org> 17.2-1
- New upstream release

* Sat Nov 07 2015 Stuart D. Gathman <stuart@gathman.org> 17.1-3
- remove defattr
- TODO: generate default config at install time, not first start

* Wed Nov 04 2015 Stuart D. Gathman <stuart@gathman.org> 17.1-2
- use dynamic nacl library backported from rawhide

* Tue Nov 03 2015 Stuart D. Gathman <stuart@gathman.org> 17.1-1
- update to new protocol version

* Tue Oct 27 2015 Stuart D. Gathman <stuart@gathman.org> 16.3-2
- move graphing tools to graph subpackage: networkx has a lot of dependencies.
- use embedded nacl only for i686 (which compiles it with -fPIC)

* Fri Oct 16 2015 Stuart D. Gathman <stuart@gathman.org> 16.3-1
- Allow hostname lookup in selinux policy
- python tools subpackage

* Sun Oct  4 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-6
- restorecon after selinux install to initialize cjdroute context
- remove module_request (to load tun driver) from selinux policy
- make init scripts load tun driver

* Sun Sep 27 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-5
- Restart cjdroute on update, stop on uninstall
- symlink selected tools to bin
- use /var/empty/cjdns for chroot
- patch genconf to change chroot and setuser

* Wed Sep 23 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-4
- Remove doc subpackage - only a meg of docs, and protocol is experimental.
- Fix for RLIMIT_NPROC - setuid bug.
- Add setgid to Security.c
- add contrib/nodejs so tools work

* Wed Sep 23 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-3
- Add selinux, doc and tools subpackages
- Support EL6

* Mon Sep 21 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-2
- nodejs not a runtime dependency of main package
- move binaries to /usr/bin (good idea?)

* Mon Sep 21 2015 Stuart D. Gathman <stuart@gathman.org> 16.0-1
- Initial RPM
