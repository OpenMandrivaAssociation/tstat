Summary: Sniffer able to provide several insights on the traffic patterns
Name: tstat
Version: 1.01
Release: 8
Source0: http://tstat.tlc.polito.it/download/%{name}-%{version}.tar.gz
Source1: tstat.service
Source2: tstat_rrd.cgi
Source3: tstat_net.conf
Source4: tstat_rrd.conf
Source5: tstat_global.conf
Patch0: tstat-Makefile.in.patch.bz2
Patch1: tstat.h.patch.bz2
License: GPL
Group: Monitoring
Url: http://tstat.tlc.polito.it/
Buildrequires: pcap-devel rrdtool-devel
Requires: rrdtool

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
%setup -q -n %{name}
%patch0 -p0
%patch1 -p0

%build
%configure
%make

%install
mkdir -p %{buildroot}/%{_bindir}
mkdir -p %{buildroot}/%{_sysconfdir}/tstat
mkdir -p %{buildroot}/%{_unitdir}
mkdir -p %{buildroot}/var/lib/%{name}/rrd_data/localhost
cp -v $RPM_BUILD_DIR/%{name}/tstat %{buildroot}/%{_bindir}/tstat
cp -v %{SOURCE4} %{buildroot}/%{_sysconfdir}/%{name}/rrd.conf
cp -v %{SOURCE1} %{buildroot}/%{_unitdir}/%{name}.service
cp -v %{SOURCE3} %{buildroot}/%{_sysconfdir}/%{name}/net.conf.sample
cp -v %{SOURCE5} %{buildroot}/%{_sysconfdir}/%{name}/global.conf

mkdir -p %{buildroot}/var/www/cgi-bin
mkdir -p %{buildroot}/var/www/html/rrd_images
cp -v %{SOURCE2} %{buildroot}/var/www/cgi-bin/%{name}_rrd.cgi

%clean

%post
%systemd_post tstat

%post -n %{name}-www
if [ ! -e "/var/www/cgi-bin/rrd_data" ];then
	ln -sf /var/lib/%{name}/rrd_data /var/www/cgi-bin/rrd_data
fi
if [ ! -e "/var/www/cgi-bin/rrd_images" ];then
	ln -sf /var/www/html/rrd_images /var/www/cgi-bin/rrd_images
fi
chown -R apache.apache /var/www/html/rrd_images

%preun
%systemd_preun tstat

%files
%doc docs/*
%{_bindir}/%{name}
%attr(0644,root,root) %{_unitdir}/%{name}.service
%config(noreplace) %{_sysconfdir}/%{name}/rrd.conf
%config(noreplace) %{_sysconfdir}/%{name}/net.conf.sample
%config(noreplace) %{_sysconfdir}/%{name}/global.conf
/var/lib/%{name}/*

%files -n %{name}-www
%doc docs/CHANGES docs/README.RRDtool
%attr(755,apache,apache) /var/www/html/rrd_images
%attr(755,root,root) /var/www/cgi-bin/tstat_rrd.cgi
