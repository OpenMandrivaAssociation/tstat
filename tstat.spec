%define name tstat
%define version 1.01
%define release %mkrel 3

Summary: Sniffer able to provide several insight on the traffic patterns
Name: %{name}
Version: %{version}
Release: %{release}
Source0: http://tstat.tlc.polito.it/download/%{name}-%{version}.tar.gz
Source1: tstat.init
Source2: tstat_rrd.cgi
Source3: tstat_net.conf
Source4: tstat_rrd.conf
Source5: tstat_global.conf
Patch0: tstat-Makefile.in.patch.bz2
Patch1: tstat.h.patch.bz2
License: GPL
Group: Monitoring
Url: http://tstat.tlc.polito.it/
BuildRoot: %{_tmppath}/%{name}-%{version}-%{release}-buildroot
Buildrequires: %{mklibname pcap0}-devel %{mklibname rrdtool2}-devel
requires: rrdtool
Requires(post,preun):		rpm-helper

%description
The lack of automatic tools able to produce statistical data from network
packet traces was a major motivation to develop Tstat, a tool which, starting
from standard software libraries, offers to network managers and researchers
audit important information about classic and novel performance indexes and
statistical data about Internet traffic. Started as evolution of TCPtrace, 
Tstat analyzes either real-time captured packet traces, using either common PC 
hardware or more sophisticated ad-hoc cards such as the DAG cards. Beside live 
capture, Tstat can analyze previously recorded packet-level traces, supporting
various dump formats, such as the one supported by the libpcap library, and 
many more.

please adjust: %{_sysconfdir}/tstat/global.conf

%package -n %{name}-www
Summary:        Provides the CGI file for the tstat web interface
Group:          Networking/WWW
Requires: apache perl-CGI apache-mod_fastcgi perl-DateManip

%description -n %{name}-www
Provides the CGI file for the tstat web interface

%prep
%setup -q -n %name
%patch0 -p0
%patch1 -p0

%build
%configure
%make

%install
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/%{_bindir}
mkdir -p $RPM_BUILD_ROOT/%{_sysconfdir}/tstat
mkdir -p $RPM_BUILD_ROOT/%{_initrddir}
mkdir -p $RPM_BUILD_ROOT/var/lib/%name/rrd_data/localhost
cp -v $RPM_BUILD_DIR/%name/tstat $RPM_BUILD_ROOT/%{_bindir}/tstat
cp -v %{SOURCE4} $RPM_BUILD_ROOT/%{_sysconfdir}/%name/rrd.conf
cp -v %{SOURCE1} $RPM_BUILD_ROOT/%{_initrddir}/%{name}
cp -v %{SOURCE3} $RPM_BUILD_ROOT/%{_sysconfdir}/%name/net.conf.sample
cp -v %{SOURCE5} $RPM_BUILD_ROOT/%{_sysconfdir}/%name/global.conf

mkdir -p $RPM_BUILD_ROOT/var/www/cgi-bin
mkdir -p $RPM_BUILD_ROOT/var/www/html/rrd_images
cp -v %{SOURCE2} $RPM_BUILD_ROOT/var/www/cgi-bin/%{name}_rrd.cgi

%clean
rm -rf $RPM_BUILD_ROOT

%post
%_post_service tstat

%post -n %{name}-www
if [ ! -e "/var/www/cgi-bin/rrd_data" ];then
	ln -sf /var/lib/%name/rrd_data /var/www/cgi-bin/rrd_data
fi
if [ ! -e "/var/www/cgi-bin/rrd_images" ];then
	ln -sf /var/www/html/rrd_images /var/www/cgi-bin/rrd_images
fi
chown -R apache.apache /var/www/html/rrd_images

%preun
%_preun_service tstat

%files
%defattr(-,root,root)
%doc docs/*
%{_bindir}/%name
%attr(755,root,root) %{_initrddir}/%{name}
%config(noreplace) %{_sysconfdir}/%{name}/rrd.conf
%config(noreplace) %{_sysconfdir}/%{name}/net.conf.sample
%config(noreplace) %{_sysconfdir}/%{name}/global.conf
/var/lib/%name/*

%files -n %{name}-www
%doc docs/CHANGES docs/README.RRDtool
%attr(755,apache,apache) /var/www/html/rrd_images
%attr(755,root,root) /var/www/cgi-bin/tstat_rrd.cgi
