
# Fedora review: http://bugzilla.redhat.com/1268716

# Option to enable SUBNODE mode (WIP)
# Fedora generally runs on systems that easily support a full node
%bcond_with subnode
# Option to use the optimized libnacl embedded with cjdns
# Required since v20 due to use of private cnacl APIs
%bcond_without embedded
# Option to enable CPU specific optimization
# Default to generic for distro builds
%bcond_without generic
# Option to use libsodium instead of nacl (broken since v20)
%bcond_with libsodium
# Option to disable SECCOMP: confusing backward logic
# Needed to run on openvz and other container systems
%bcond_without seccomp
# Option to use system libuv instead of bundled libuv-0.11.19
%bcond_with libuv

%if %{with embedded}
%global use_embedded 1
%else
%global use_embedded 0
%endif

%if %{with libuv}
%global use_libuv 1
%else
%global use_libuv 0
%endif

%if %{with generic}
%global generic_build 1
%else
%global generic_build 0
%endif

%if %{with libsodium}
%global use_libsodium 1
%global nacl_name libsodium
%global nacl_version 1.0.14
%global nacl_lib %{_libdir}/libsodium.so
%else
%global use_libsodium 0
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

%if 0 && 0%{?fedora} > 30
%global use_marked 1
%global makeman marked-man
%else
%global use_marked 0
%global makeman ../../ronn
%endif

# FIXME: Needs dependencies and install www dir someplace reasonable.
%global with_admin 0

# FIXME: python tools need to make cjdnsadmin a proper python package
%global with_python 1
%global __python %{__python2}

%{!?__restorecon: %global __restorecon /sbin/restorecon}

Name:           cjdns
# major version is cjdns protocol version:
Version:        20.3
Release:        8%{?dist}
Summary:        The privacy-friendly network without borders
# cjdns is all GPLv3 except libuv which is MIT and BSD and ISC
# cnacl is unused except when use_embedded is true
License:        GPLv3 and MIT and BSD and ISC
URL:            http://hyperboria.net/
Source0: https://github.com/cjdelisle/cjdns/archive/%{name}-v%{version}.tar.gz
Source1: cjdns.README_Fedora.md
Source2: cjdns.service
# nroff overlay for nodejs-marked
Source3: https://github.com/kapouer/marked-man/archive/0.7.0.tar.gz#/marked-man-0.7.0.tar.gz
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
# Patch to use _LINUX_CAPABILITY_3 (cjdns < 18)
#Patch7:  cjdns.cap3.patch
# Patch some source files to ignore selected warnings that break gcc6 builds
Patch8:  cjdns.warnings.patch
# Man pages
Patch9:  cjdns.man.patch
# Patch some bugs in nodejs tools
Patch10: cjdns.tools.patch
# Alternate dynamic library patch to use libsodium
Patch11: cjdns.sodium.patch
# Disable WIP subnode code when SUBNODE not enabled
Patch12: cjdns.sign.patch
# Recognize ppc64, ppc64le, and s390x arches
#Patch13: cjdns.ppc64.patch
# getentropy(2) added to glibc in Fedora 26
# included in cjdns-20.1 
#Patch14: cjdns.entropy.patch
# Fix buffer overrun in JsonBencSerializer.c
# included in cjdns-20.1
#Patch15: cjdns.benc.patch
# Specify python2 for systems that default to python3
Patch16: cjdns.python3.patch
# s390x support for embedded cnacl library from Dan Horák <dan@danny.cz>
# Included upstream since 20.3
#Patch17: cjdns.s390x.patch
# patch build to use system libuv
Patch18: cjdns.libuv.patch
Patch19: cjdns.fuzz.patch
# patch to use /proc/sys/kernel/random/uuid instead of sysctl
Patch20: cjdns.sysctl.patch
# Patch ronn to stop using deprecated util.puts and util.debug
Patch21: cjdns.puts.patch

%if %{use_marked}
BuildRequires:  nodejs, nodejs-marked, python2
%else
BuildRequires:  nodejs, nodejs-ronn, python2
%endif

# Automated package review hates explicit BR on make, but it *is* needed
BuildRequires:  make gcc

%if !0%{use_embedded}
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
%if 0%{use_libuv}
BuildRequires: libuv-devel
%else
Provides: bundled(libuv) = 0.11.19
%endif
%if 0%{use_embedded}
Provides: bundled(nacl) = 20110221
%endif
# build system requires nodejs, unfortunately
ExclusiveArch: %{nodejs_arches}

%description
Cjdns implements an encrypted IPv6 network using public-key cryptography for
address allocation and a distributed hash table for routing. This provides
near-zero-configuration networking, and prevents many of the security and
scalability issues that plague existing networks.

%package selinux
Summary: Targeted SELinux policy module for cjdns
BuildRequires: policycoreutils, checkpolicy, selinux-policy-devel
Requires: policycoreutils, selinux-policy-targeted
Requires: %{name} = %{version}-%{release}
BuildArch: noarch

%description selinux
Targeted SELinux policy module for cjdns.

# FIXME: keep C tools separate?
%package tools
Summary: Nodejs tools for cjdns
Requires: nodejs, %{name} = %{version}-%{release}
BuildArch: noarch

%description tools
Nodejs tools for cjdns. Highlights:
peerStats          show current peer status
cjdnslog           display cjdroute log
cjdns-traceroute   trace route to cjdns IP
sessionStats       show current crypto sessions

%package -n python2-cjdns
%{?python_provide:%python_provide python2-cjdns}
# Remove before F30
Provides: %{name}-python = %{version}-%{release}
Obsoletes: %{name}-python < %{version}-%{release}
Summary: Python tools for cjdns
%if 0%{?fedora} >= 18
BuildRequires: python2-rpm-macros
%else
BuildRequires: python-rpm-macros
%endif
Requires: python2, %{name} = %{version}-%{release}
BuildArch: noarch

%description -n python2-cjdns
Python tools for cjdns.

%package graph
Summary: Python peer graph tools for cjdns
Requires: python2-%{name} = %{version}-%{release}
%if 0%{?rhel} == 6 || 0%{?rhel} == 7
Requires: python-networkx
Requires: python2-matplotlib
%else
Requires: python2-networkx
%endif
BuildArch: noarch

%description graph
Python peer graph tools for cjdns.

%prep
%setup -qn cjdns-%{name}-v%{version}
%patch0 -b .selinux
%if 0%{?rhel} == 6
%patch1 -b .el6
%endif

%patch2 -b .nprocs
%patch4 -b .genconf
%patch5 -b .sbin

cp %{SOURCE2} contrib/systemd

%if %{use_marked}
tar xvfz %{SOURCE3}
%endif

%if 0%{use_embedded}
# disable CPU opt
%else
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
%patch12 -b .sign
%endif

%if !0%{?rhel} || 0%{?rhel} > 6
%patch8 -b .warnings
%endif

%patch9 -b .man
%patch10 -b .tools
#patch13 -b .ppc64
#patch14 -b .entropy
#patch15 -b .benc
%patch16 -b .python3
%if 0%{use_libuv}
%patch18 -p1 -b .libuv
mkdir dependencies
cp node_build/dependencies/libuv/include/tree.h dependencies/uv_tree.h
rm -rf node_build/dependencies/libuv
%endif
%patch19 -p1 -b .fuzz
%patch20 -p1 -b .sysctl

cp %{SOURCE1} README_Fedora.md

# Remove #!env from python scripts
chmod a+x contrib/python/cjdnsadmin/cli.py
find contrib/python/cjdnsadmin ! -executable -name "*.py" |
        xargs sed -e '\,^#!/usr/bin/env, d' -i
find contrib/python -type f |
        xargs sed -e '1 s,^#!/usr/bin/env ,#!/usr/bin/,' -i 
sed -e '$ s,^python ,/usr/bin/python2 ,' -i contrib/python/cjdnsa

# Remove #!env from nodejs scripts
find tools -type f | xargs grep -l '^#!\/usr\/bin\/env ' |
        xargs sed -e '1 s,^#!/usr/bin/env ,#!/usr/bin/,' -i

# Fix deprecated Buffer ctor except on EL6
%if 0%{?rhel} != 6 
sed -e '1,$ s/new Buffer/Buffer.from/' -i \
        tools/lib/publicToIp6.js tools/lib/cjdnsadmin/cjdnsadmin.js
%endif

# Remove unpackaged code with undeclared licenses
%if %{with_admin}
rm -rf contrib/nodejs   # GPLv3 and ASL 2.0
%endif
rm -rf contrib/http     # GPLv2 and MIT

cat >cjdns-up.sh <<'EOF'
#!/bin/sh

cjdev="$(cjdns-online -i)" || exit 1

for s in %{_sysconfdir}/cjdns/up.d/*.sh; do
  if test -x "$s"; then
    "$s" up $cjdev
  fi
done
EOF

chmod a+x cjdns-up.sh

%if %{generic_build}
%ifarch s390x
sed -i -e 's/-march=native/-mtune=native/' node_build/make.js
%else
sed -i -e 's/-march=native/-mtune=generic/' node_build/make.js
%endif
rm node_build/dependencies/cnacl/node_build/plans/*_AVX_plan.json
# Leaving SSE2 code in since x86 is secondary arch and pretty much everyone
# is going to have SSE2, except things like XO-1 which needs custom build.
#rm node_build/dependencies/cnacl/node_build/plans/x86_SSE2_plan.json
%endif

%if !%{use_marked}
cp -r /usr/lib/node_modules/ronn node_modules
%patch21 -p1 -b .puts
ln -s node_modules/ronn/bin/ronn.js ronn
%endif

# remove hidden files from node_modules/nthen
cd node_modules/nthen
rm -f .f* .j* .t*
cd -

# FIXME: grep Version_CURRENT_PROTOCOL util/version/Version.h and
# check that it matches major %%{version}

%build
cd contrib/selinux
ln -s /usr/share/selinux/devel/Makefile .
make 
cd -

# nodejs based build system

%if !%{with seccomp}
export Seccomp_NO=1
%endif
%if %{with subnode}
export SUBNODE=1
%endif
NO_TEST=1 CJDNS_RELEASE_VERSION="%{name}-%{version}-%{release}" ./do

# FIXME: use system libuv on compatible systems
# bundled libuv is 0.11.19 with changes:
# https://github.com/cjdelisle/cjdns/commits/master/node_build/dependencies/libuv

%check
build_linux/test_testcjdroute_c all >test.out

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
mkdir -p %{buildroot}%{_sysconfdir}/cjdns/up.d

# chroot 
mkdir -p %{buildroot}/var/empty/cjdns

# install selinux modules
mkdir -p %{buildroot}%{_datadir}/selinux/targeted
install -pm 644 contrib/selinux/cjdns.pp %{buildroot}%{_datadir}/selinux/targeted
ln -f contrib/selinux/cjdns.{te,fc} .  # for doc dir

# install c and nodejs tools
mkdir -p %{buildroot}%{_libexecdir}/cjdns/{node_build,contrib}
install -p publictoip6 privatetopublic mkpasswd makekeys randombytes sybilsim \
        %{buildroot}%{_libexecdir}/cjdns
rm -f node_modules/nthen/.npmignore
cp -pr tools node_modules %{buildroot}%{_libexecdir}/cjdns
# but not local copy of ronn
rm -rf %{buildroot}%{_libexecdir}/cjdns/node_modules/ronn

%if %{with_admin}
rm -f contrib/nodejs/admin/.gitignore
cp -pr contrib/nodejs/admin %{buildroot}%{_libexecdir}/cjdns
%endif

cp -p cjdns-up.sh %{buildroot}%{_libexecdir}/cjdns/cjdns-up

# symlinks for selected nodejs tools
mkdir -p %{buildroot}%{_bindir}
for t in peerStats sessionStats cjdnslog search dumpLinks dumptable \
         dumpRumorMill pathfinderTree pingAll; do
  ln -sf %{_libexecdir}/cjdns/tools/$t %{buildroot}%{_bindir}
done
for t in traceroute; do
  ln -sf %{_libexecdir}/cjdns/tools/$t %{buildroot}%{_bindir}/cjdns-$t
done

# symlinks for selected C tools that don't conflict with other packages
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
    %{makeman} $m >%{buildroot}%{_mandir}/man$M/cjdns-${m%.md}.$M
    continue ;;
  privatetopublic|sybilsim) M="8" ;;
  *) M="1" ;;
  esac
  %{makeman} $m >%{buildroot}%{_mandir}/man$M/${m%.md}.$M
done
cd -

%if %{with_python}

# install python tools that pull in networkx for graphing
cp -pr contrib/python %{buildroot}%{_libexecdir}/cjdns

# These files are installed via doc and license
rm %{buildroot}%{_libexecdir}/cjdns/python/README.md
rm %{buildroot}%{_libexecdir}/cjdns/python/cjdns-dynamic.conf
rm %{buildroot}%{_libexecdir}/cjdns/python/cjdnsadmin/bencode.py.LICENSE.txt

# Move cjdnsadmin to site-packages
mkdir -p %{buildroot}%{python2_sitelib}
mv %{buildroot}%{_libexecdir}/cjdns/python/cjdnsadmin %{buildroot}%{python2_sitelib}

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
%dir %{_sysconfdir}/cjdns/up.d
%{_libexecdir}/cjdns/cjdns-up
%{_libexecdir}/cjdns/randombytes
%{_libexecdir}/cjdns/publictoip6
%{_libexecdir}/cjdns/privatetopublic
%{_libexecdir}/cjdns/sybilsim
%{_libexecdir}/cjdns/makekeys
%{_libexecdir}/cjdns/mkpasswd
%{_bindir}/randombytes
%{_bindir}/publictoip6
%{_bindir}/makekeys
%{_bindir}/cjdns-online
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
%{_mandir}/man1/cjdnslog.1.gz

%files -n python2-cjdns
%doc contrib/python/README.md contrib/python/cjdns-dynamic.conf
%license contrib/python/cjdnsadmin/bencode.py.LICENSE.txt
%{python2_sitelib}/cjdnsadmin
%dir %{_libexecdir}/cjdns/python
%{_libexecdir}/cjdns/python/cexec
%{_libexecdir}/cjdns/python/cjdnsadminmaker.py*
%{_libexecdir}/cjdns/python/cjdnslog
%{_libexecdir}/cjdns/python/dumptable
%{_libexecdir}/cjdns/python/dynamicEndpoints.py*
%{_libexecdir}/cjdns/python/peerStats
%{_libexecdir}/cjdns/python/sessionStats
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
* Sat Aug 24 2019 Stuart Gathman <stuart@gathman.org> - 20.3-8
- Don't package local copy of ronn 
- Remove hidden files from node_modules/nthen

* Thu Aug 15 2019 Stuart Gathman <stuart@gathman.org> - 20.3-7
- Don't audit /var/lib/sss access bz#1589395

* Tue Aug 06 2019 Stuart Gathman <stuart@gathman.org> - 20.3-6
- Much simpler solution to removing sysctl calls :-)

* Sat Aug 03 2019 Stuart Gathman <stuart@gathman.org> - 20.3-5
- Remove deprecated sysctl() call in getUUID (read from /proc/.../random/uuid)
- Patch a local copy of ronn to stop calling util.puts/util.debug

* Wed Jul 24 2019 Fedora Release Engineering <releng@fedoraproject.org> - 20.3-4
- Rebuilt for https://fedoraproject.org/wiki/Fedora_31_Mass_Rebuild

* Thu May 09 2019 Stuart Gathman <stuart@gathman.org> - 20.3-3
- Move running test suite to check

* Wed May 08 2019 Stuart Gathman <stuart@gathman.org> - 20.3-2
- Increase timeout for fuzz tests to allow slower arches to succeed

* Wed May 08 2019 Stuart Gathman <stuart@gathman.org> - 20.3-1
- New upstream version 20.3

* Fri May 03 2019 Stuart Gathman <stuart@gathman.org> - 20.2-7
- Option to use system libuv
- Fix scope of Pipe_PATH String_CONST in config.

* Thu Jan 31 2019 Fedora Release Engineering <releng@fedoraproject.org> - 20.2-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_30_Mass_Rebuild

* Thu Nov  8 2018 Stuart Gathman <stuart@gathman.org> - 20.2-5
- Install cjdnsadmin python module in site-packages
- Work around missing python2-networkx Provides in python-networkx bz#1647987
- Fix deprecated Buffer ctor in nodejs tools except on el6

* Wed Jul 18 2018 Stuart Gathman <stuart@gathman.org> - 20.2-4
- cjdns-20.2 bundles libuv-0.11.19
- disable CPU specific optimization

* Thu Jul 12 2018 Fedora Release Engineering <releng@fedoraproject.org> - 20.2-3
- Rebuilt for https://fedoraproject.org/wiki/Fedora_29_Mass_Rebuild

* Thu May 31 2018 Stuart Gathman <stuart@gathman.org> - 20.2-2
- Add cnacl s390x support BZ#1584480

* Tue May 22 2018 Stuart Gathman <stuart@gathman.org> - 20.2-1
- New upstream release BZ#1464671

* Wed Mar 14 2018 Stuart Gathman <stuart@gathman.org> - 20.1-4
- Explicit python version in Requires
- Fix possible unterminated interface name in ifreq

* Tue Mar 13 2018 Iryna Shcherbina <ishcherb@redhat.com> - 20.1-3
- Update Python 2 dependency declarations to new packaging standards
  (See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3)

* Tue Mar  6 2018 Stuart Gathman <stuart@gathman.org> - 20.1-2
- selinux: Allow map access to cjdns_exec_t
- disable subnode by default

* Wed Feb 21 2018 Stuart Gathman <stuart@gathman.org> - 20.1-1
- New upstream release

* Fri Feb 09 2018 Igor Gnatenko <ignatenkobrain@fedoraproject.org> - 19.1-10
- Escape macros in %%changelog

* Wed Feb 07 2018 Fedora Release Engineering <releng@fedoraproject.org> - 19.1-9
- Rebuilt for https://fedoraproject.org/wiki/Fedora_28_Mass_Rebuild

* Mon Oct 02 2017 Remi Collet <remi@fedoraproject.org> - 19.1-8
- rebuild for libsodium

* Sat Aug 19 2017 Zbigniew Jędrzejewski-Szmek <zbyszek@in.waw.pl> - 19.1-7
- Python 2 binary package renamed to python2-cjdns
  See https://fedoraproject.org/wiki/FinalizingFedoraSwitchtoPython3

* Wed Aug 02 2017 Fedora Release Engineering <releng@fedoraproject.org> - 19.1-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Binutils_Mass_Rebuild

* Wed Jul 26 2017 Fedora Release Engineering <releng@fedoraproject.org> - 19.1-5
- Rebuilt for https://fedoraproject.org/wiki/Fedora_27_Mass_Rebuild

* Wed May 24 2017 Stuart D. Gathman <stuart@gathman.org> 19.1-4
- Add calls to sodium_init()
- Include mkpasswd (but not in /usr/bin)

* Fri Feb 24 2017 Stuart D. Gathman <stuart@gathman.org> 19.1-3
- Test and fix --with=subnode 

* Fri Feb 24 2017 Stuart D. Gathman <stuart@gathman.org> 19.1-2
- Adjust for moving in6_ifreq to linux/ipv6.h in kernel-headers-4.11

* Fri Feb 24 2017 Stuart D. Gathman <stuart@gathman.org> 19.1-1
- New upstream release

* Sat Feb 18 2017 Stuart D. Gathman <stuart@gathman.org> 18-7
- Fix errors and document nits found by gcc7

* Fri Feb 10 2017 Fedora Release Engineering <releng@fedoraproject.org> - 18-6
- Rebuilt for https://fedoraproject.org/wiki/Fedora_26_Mass_Rebuild

* Sat Jan  7 2017 Stuart D. Gathman <stuart@gathman.org> 18-5
- Run scripts in %%{sysconfdir}/cjdns/up.d when cjdns comes up.

* Sun Nov  6 2016 Stuart D. Gathman <stuart@gathman.org> 18-4
- update cjdns-online man page
- Support ppc64, ppc64le, s390x

* Fri Oct 14 2016 Stuart D. Gathman <stuart@gathman.org> 18-3
- libstdc++ not needed with libsodium

* Fri Oct 14 2016 Stuart D. Gathman <stuart@gathman.org> 18-2
- Remove Sign.c which uses a private API and isn't needed until supernodes.
- Use libsodium by default: seems best performance of dynamic libraries

* Wed Oct 12 2016 Stuart D. Gathman <stuart@gathman.org> 18-1
- Update to 18 upstream release

* Mon Aug 15 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-7
- Move modprobe to cjdns-loadmodules.service

* Wed Aug 10 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-6
- Fix logic for %%bcond_without seccomp

* Wed Aug 10 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-5
- cjdns.service: add CapabilityBoundingSet

* Fri Jun 24 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-4
- cjdns-selinux: allow cjdroute to manipulate route table

* Thu Jun 23 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-3
- Remove cjdns-resume.service patch, incorporated upstream
- Add --interface option to cjdns-online.sh

* Thu Jun 23 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-2
- Move tool manpages to tool subpackage.

* Thu Jun 23 2016 Stuart D. Gathman <stuart@gathman.org> 17.4-1
- Update to 17.4 upstream release
- Remove cap3 patch, as it is incorporated upstream
- Remove Constant.js patch, as it is incorporated upstream

* Tue May  3 2016 Stuart D. Gathman <stuart@gathman.org> 17.3-13
- man page for cjdnslog
- Fix running on Fedora as well as openVZ. :-P
- Make cjdns exclusive to nodejs_arches. Rafael Fonseca <rdossant@redhat.com> 

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
