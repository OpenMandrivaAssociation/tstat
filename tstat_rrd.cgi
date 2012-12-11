#! /usr/bin/perl
#==============================================================================
# tstat_rrd.cgi	-*- v2.1 -*- Wed Jun  8 18:44:35 CEST 2005 -*- Dario Rossi
#------------------------------------------------------------------------------
# url parameters:
# dir=	       	the directory where the rrd files are (i.e., a specific trace)
# var=         	one of Tstat parameters (e.g., rtt_avg_in, ip_len_in, ...)
# template=    	one of (avg|stdev|idx|prc|hit), developed by applyTemplate() below
# duration=    	temporal window size (until end of samples)
# logscale=    	flag; toggle logscale
# agg=		flag; toggle wether to aggregate in/out and c2s/s2c flows
# bigpic=      	flag; doubles the picture size
# advopt=      	flag; toggle other options, such as:
# describe=	flag; toggle description
#   advcmd=	flag; toggle wether to plot picture or dump RRDtool command
#   yauto=     	flag; whether to use autoscaling
#   ymin=      	minimum yscale value
#   ymax=      	maximum yscale value
# format=	(png*|eps|pdf|rrd) used for creating download links
#
#	NOTE: $RRD_DATA/url_param("dir")/url_param("var").rrd
#	should be an existent file; the script enforce this check
#	by automatically selecting the available templates and
#	neglecting the one that whould cause an error
#
#
# other parameters:
#       every rrd directory may contain a HEADER, a FOOTER and a README
#       files, allowing custom informations to be naturally embedded in
#       each of the traces ``main page'' (i.e., when no parameter has been
#       chosen yet).
#       By default, the cgi tries to load the html version (thus,
#       FILE.html); otherwise, tries to displays "<pre> `cat FILE` </pre>" 
#       if such a file exists; finally, it will display a default message
#       held in $default{README} hardcoded in the script
#
# internal cgi configuration:
# 	see the configuration section below
#
# maintenance:
#	this has gone quite complex... for extensions, look for #NEWVAR 
#	comments below


#   ____________________________  
#  /				\ 
# /    libraries      __________/ 
# \__________________/.:nonsns:.  
# 				  
# makes things work when run without install
#	use lib qw( ../perl-shared/blib/lib ../perl-shared/blib/arch );
# this is after RRDtool `make install`... check your directory settings
# 
use lib qw(/usr/lib/perl);

use RRDs;
use Date::Manip;
use Data::Dumper;
use CGI qw/:standard/;
use CGI::Carp qw(fatalsToBrowser set_message);
BEGIN {
   sub handle_errors {
      my $msg = "@_";
      print "<h1>Oh gosh</h1>";
      print "<p>tstat_rrd.cgi got an error:  <br><pre>$msg</pre></p>";
  }
  set_message(\&handle_errors);
}


#   ____________________________  
#  /				\ 
# /    configuration  __________/ 
# \__________________/.:nonsns:.  
# 				  
$debug=0;
$standalone_html = 1;  # add <html><body> ... </body></html>

#
# tstat_rrd output configuration: parameter separator 
# depends on tstat's RRD_TREE compilation option
# may be '/' if param/prc90.rrd, by default is param.prc90.rrd
$RRD_TREE = '.'; 

# specify path to the root of the rrd database tree
# by default, I assume there is a symbolic link in cgi-bin/ 
# named rrd_data
$RRD_DATA = 'rrd_data'; 

# same thing for image directory
# in my case, var/www/cgi-bin/rrd_images is
# a symbolic link to "/var/www/html/rrd_images"; 
# from the html browser's perspective
$IMG_DIR = "rrd_images"; 


# starting from v2.5, you have two differenent timescales
@RRD_TIME_LO  =  qw(12h 3d 1w  1m  1y);
@RRD_TIME_HI  =  qw(1h  4h 12h 24h 48h);
@RRD_TIME = @RRD_TIME_LO;


%tstat_css = (
  '<h1>' => '<H1>',
  '<h2>' => '<H2>',
);
%eurongi_css = (
  '<h1>' => '<H1 class="rouge">',
  '<h2>' => '<H2 class="noir">',
  '<h3>' => '<H3 class="noir">',
  '<a '  => '<span class="rouge:hover"><a ',
  '</a>' => '</a></span>',
  '<b>'  => '<span class="rouge"><b>',
  '</b>' => '</b></span>',
);  

%default = (
   HEADER => '',
   FOOTER => 'Tstat/RRD Web Interface (Dario Rossi)',	
   README => <<END,
<hr>
<h3> CGI interface </h3>
The CGI interface has been designed to quickly respond
to your actions, meaning that the dropdown menus and
the checkbuttons automatically trigger plot changes.
<ul>
<li> Two dropdown menus allow to select the <B>trace</b>
and the <b>variable</b> to observe.
<li> The two buttons <b> start over</b> and <b> home</b>
bring the user up a level or to the root of the
Round Robin Database; optionally, you can directly
browse and download the <b> RRData</b>
<li> Different options allows the user to, e.g., read the 
<b>description</b> of the metric and templates, or
toggle the use of <B>bigger pictures</b>, or allow to
select different <b>time windows</b> for short traces
processed with a higher sampling rate.
<li> An interesting feature allow to <b>aggregate</b> in 
a single plot several directions: specifically, outgoing (top,+)
incoming (bottom,-) flows will be aggregated together as well
as client-2-server (top,+) and server-2-client (bottom,-)
flows.
<li> The <b>advanced...</b> checkbox gives the user the opportunity
of finely tuning the y-axis scale (e.g., <b>autoscaling</b>,
<b>logscale</b>), or plot the RRDtool command used to produce 
the plot.
<li> Finally, you can select among the available <b>templates</b> and
<b>timespans</b>.
</ul>

Have a good Tstat!
END
);

=pod
<hr>
<h3> Navigation Instructions </h3>
<ul>
	<li> To	inspect traffic that has different <i>geographical</i>
	and <i>temporal</i> properties you can browse through different
	<b>traces</b>, 
	</li>
	
	<li> You may then select one of the different <b>parameters</b>, to
	gather significative insights on the <i>statistical properties</i> of
	the traffic. </li>

	<li> Several <b>templates</b> allow to browse through different 
	visual <i>presentation</i> of the same statistical dataset
	<ul>
	<li>
	moreover, the same template can be applied to different temporal views.
	</li>
	</ul>
	</li>
	
	<li> Several <b>temporal views</b> allow to observe complex traffic
	pattern at different <i>time granularity</i> 
	<ul>
	</ul>
	</li>
	
	<li>
	Besides, you can <b>finely tune</b> several properties of the graph, 
	such as the size of the graph, wether to use logarithmic scales,  or the
	y-axis scale, ...
	</li>
	<li>
	Finally, the <b>start over</b> button will bring you to the main page of
	each separate trace, whereas the <b>home</b> button will bring you to
	the main page common to all the traces.
	</li>

</ul>
=cut

# sub scaleDuration {
# my $scale = shift;
#    $RRD_TIMEh *= $scale;
#    $RRD_TIMEd *= $scale;
#    $RRD_TIMEw *= $scale;
#    $RRD_TIMEm *= $scale;
#    $RRD_TIMEy *= $scale;
# }
# sub shiftDuration {
# my $shift = shift;
#    $RRD_TIMEh += $shift;
#    $RRD_TIMEd += $shift;
#    $RRD_TIMEw += $shift;
#    $RRD_TIMEm += $shift;
#    $RRD_TIMEy += $shift;
# }
# 

#NEWVAR	    
# global parameters have the form ``$pXxx''
use vars qw($pLog $pTpl $pLen $pDir $pReadme $pHeader $pFooter $pStyle 
            $pBigpic $pAggpic $pAdvcmd $pLogscale $pDescribe
	    $pFormat %pFormat $pHifreq
	    $pNEWVAR );
#NEWVAR	    

# global data
use vars qw($idx2value %description2param %description @defColor %color %css); 

#   ____________________________  
#  /				\ 
# /    main           __________/ 
# \__________________/.:nonsns:.  
# 				  
#
# we will call main() at the end of file, after all global vars are defined
#
sub main {
    $menu=1; #GCI output by default
    if (url_param()) {
	     $pLog = url_param('logscale');
             $pTpl = url_param('template');
             $pLen = url_param('duration');	     
             $pBigpic = url_param('bigpic');	     
             $pAdvopt = url_param('advopt');	     
  	          $pAdvopt ||= 'true';     
             $pAdvcmd = url_param('advcmd');	     
             $pAggpic = url_param('aggpic');	
  	          $pAggpic ||= 'false';     
	     $pAutoconf = url_param('yauto');	     
	     $pYmin = url_param('ymin');	     
	     $pYmax = url_param('ymax');	     
	     $pFormat = url_param('format');
   	     $pHifreq = url_param('hifreq');	     
	     $pHifreq ||=  'false';
	     @RRD_TIME = ($pHifreq eq 'true') ? @RRD_TIME_HI : @RRD_TIME_LO;

	     #NEWVAR	     
		 $pDescribe = url_param('describe');	     
		 #$pNewvar = url_param('newvar');	     
	     #NEWVAR


             $pDir = url_param('dir');
	     $pDir = "$RRD_DATA/$pDir" unless $pDir =~ $RRD_DATA;

             $pVar  = url_param('var'); 
	     
	     # used for first time in dir $pDir
	     $pReadme =  ( -e "$pDir/README.html" ) ?
		 	    join(" ", "<hr>",`cat $pDir/README.html`) :
 			 ( -e "$pDir/README" ) ?
		 	    join(" ","<hr><pre>",`cat $pDir/README`,"</pre>") : "";
	     $pReadme .= $default{README};                 				

             $pFooter = "";
	     $pHeader = ""; 
	     $pStyle = url_param('style') ne '' ? 'EuroNGI' : 'home';
	     if ($pStyle eq 'EuroNGI') {
      	         $pCSS = '<LINK href="eurongi.css" rel=stylesheet>';	     
	     	 %css = %eurongi_css; 
		 $pHeader .= "<font size=-2>";
		 $pFooter .= "</font>";
             } else {
      	         $pCSS = "<STYLE type='text/css'>
		 	body {  font-family: Arial, sans-serif; }
			h1, h2, h3, h4, h5, h6 {  font-family: Verdana, sans-serif, bold; }
			p {   padding-left: 3em; }
        		 </STYLE>";	     		 
	     	 %css = %tstat_css; 
             }		 
	     $pHeader .= ( -e "$RRD_DATA/HEADER.html" )  ?
	 		    join(" ",`cat $pDir/HEADER.html`) :
 			( -e "$pDir/HEADER" ) ?
		 	    join(" ","<hr><pre>",`cat $pDir/HEADER`,"</pre>") : "";
	     $pFooter .= ( -e "$RRD_DATA/FOOTER.html" )  ?
	 		    join(" ",`cat $RRD_DATA/FOOTER.html`) :
                	    "<hr>";
 
  
	     # scaleDuration(param('timescale')) if param('timescale');
	     # shiftDuration(param('timeshift')) if param('timeshift');
	     # resetDuration() if param('timereset');
    } 

    $pLen =~ s/(\d+)w$/$1wk/;
    print menuHtml();
}

#   ____________________________  
#  /				\ 
# /    returnHtml     __________/ 
# \__________________/.:nonsns:.  
# 				  
 
sub returnHtml { 
   my $html = "$pCSS $pHeader\n@_\n$pFooter";
   map {
       $html =~ s/$_/$css{$_}/sig;
   } keys %css;
   return ( $standalone_html ) ? 
	    join(" ", header, start_html("$0"), $html) :
	    $html;
}


sub verb { print STDERR ("@_\n") if $debug };
#sub verb { CGI::Carp::confess("@_\n") if $debug };


#   ____________________________  
#  /				\ 
# /    filter         __________/ 
# \__________________/.:nonsns:.  
# 				  
# filter out unwanted components
#
sub is_valid {
  my ($trace,$param) = @_;
  # no need for local flows in Polito or GARR traces
  return 0 if ($trace =~ m/(Polito|GARR)/) && $param =~ m/_loc$/;  
  return 1;
}


# look for statistical rrd parameters in directory
# passed as argument.
sub dir2var {
my $dir = shift;
my $rrd = "$dir/*rrd";

   #possibly have to quote if dir contains spaces	
   my @par = glob (($rrd =~ m/\s/ ) ? "'$rrd'" : $rrd);
   map { 
     $_ = (split '\.', (split '/', $_)[-1])[0];
   } @par;

   undef %uniq;   
   @uniq{@par} = ();
   undef @keys;   
   map {
   	push @keys, $_ if( $description{$_} ne "" ) && is_valid($dir,$_);
   } keys %uniq;
   return sort { $description{$a} cmp $description{$b} } @keys;  # remove sort if undesired
}   



#   ____________________________  
#  /				\ 
# /    formHtml       __________/ 
# \__________________/.:nonsns:.  
# 				  
#
#  generate form to apply templates and browse through dirs
#  this is the core of the human-interface: everything is a
#  mix of CGI, javascript and html references. Good luck if 
#  you wish to modify it... in this case, adding a flag should
#  be still relatively easy.
# 
sub formHtml {
   #
   # available traces in RRD_DATA
   #
   my @pDir, %pDir, $long, $short;
   open FIND_DIR, "find $RRD_DATA/ -type d | sort |";
   while (<FIND_DIR>) { 
     chomp; 
     if( @glob = glob("$_/*.rrd") ) {
        ### $f .= "$_ : @glob";
	$long = $_;
	s/^.*$RRD_DATA\///g;    
	$short = $_;
	push @pDir, $_ unless m/^\s+$/;
	$pDir{$short} ||= "$short";
     }	else {
     	$f .= "Dir $_ do not glob";
     }
   }   
   close FIND_DIR;
   
   ( $pDir_default = $pDir ) =~  s/^.*$RRD_DATA\///g;    
   @pDir = sort { $a cmp $b } @pDir;	   
   if( $pDir eq $RRD_DATA ) {
  	$pDir{$RRD_DATA}='--Select a trace--';
	unshift @pDir, $RRD_DATA;
   }  

   
   #
   # available vars in pDir
   #
   my %pVar;
   my @pVar = dir2var( $pDir );
   #map { $pVar{$_} = "<font size=-2> $description{$_} </font>" } @pVar;
   map { $pVar{$_} = "$description{$_}" } @pVar;


   my %pVarAttr, %pDirAttr, %class = ( style=>"{ font-family : sans-serif; font-size : 10px; }" );
   map { $pVarAttr{$_} = \%class; } @pVar;
   map { $pDirAttr{$_} = \%class; } @pDir;

   if( $pVar eq 'NULL' ) {
  	$pVar{'NULL'}='--Select a parameter--';
	unshift @pVar, 'NULL';
   } 
   
#NEWVAR
   $js{"XXX"} = "";
   $js{loc} = "tstat_rrd.cgi?";
   $js{loc}.="duration=$pLen&" if $pLen; 
   $js{loc}.="template=$pTpl&" unless $pLen;
   $js{dir} = "dir=$pDir&";
   $js{log} = "logscale=$pLog&";
   $js{big} = "bigpic=$pBigpic&";
   $js{var} = "var=$pVar&";
   $js{agg} = "aggpic=$pAggpic&";
   $js{des} = "describe=$pDescribe&";

   $pYmax = $pYmin='' if( $pAutofconf eq 'true');
   $js{cmd} = "advcmd=$pAdvcmd&";
   $js{adv} = "advopt=$pAdvopt&";
   $js{ymn} = "ymin=$pYmin&"   if $pAdvopt && ($pAutoconf eq 'false') && $pYmin ne '';
   $js{ymx} = "ymax=$pYmax&"   if $pAdvopt && ($pAutoconf eq 'false') && $pYmax ne '';;
   $js{yac} = "yauto=$pAutoconf&";
   $js{yA1} = "yauto=true&"; #when the template changes, set autoconf
   $js{yA0} = "yauto=false&"; #when the template changes, set autoconf
   $js{hif} = "hifreq=$pHifreq&";
#
# add a new parameter to the url
# 	 $js{NEW} = "newvar=$pNewvar&";

   $jsMenuBtn ="location.href=\"tstat_rrd.cgi?$js{dir}var=NULL\"";
   $jsHomeBtn ="location.href=\"tstat_rrd.cgi?var=NULL&dir=$RRD_DATA\"";
   $jsMenuVar ="location.href=\"$js{loc}$js{XXX}$js{dir}$js{log}$js{big}$js{adv}$js{yA1}$js{XXX}$js{XXX}$js{agg}$js{cmd}$js{des}$js{hif}var=\"+this.options[this.selectedIndex].value;";
   $jsMenuDir ="location.href=\"$js{loc}$js{var}$js{XXX}$js{log}$js{big}$js{adv}$js{yac}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}dir=\"+this.options[this.selectedIndex].value;";
   $jsCheckLog="location.href=\"$js{loc}$js{var}$js{dir}$js{XXX}$js{big}$js{adv}$js{yac}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}logscale=\"+document.forms.tstatForm['tstatCheckLog'].checked;";
   $jsCheckBig="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{XXX}$js{adv}$js{yac}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}bigpic=\"+document.forms.tstatForm['tstatCheckBig'].checked;";
   $jsCheckAdv="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{XXX}$js{yac}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}advopt=\"+document.forms.tstatForm['tstatCheckAdv'].checked;";
   $jsAutoconf="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{XXX}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}yauto=\"+document.forms.tstatForm['tstatAutoconf'].checked;";
   $jsYmin    ="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{XXX}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}ymin=\"+document.forms.tstatForm['tstatYmin'].value;";
   $jsYmax    ="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{XXX}$js{agg}$js{cmd}$js{des}$js{hif}ymax=\"+document.forms.tstatForm['tstatYmax'].value;";
   $jsCheckAgg="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{XXX}$js{cmd}$js{des}$js{hif}aggpic=\"+document.forms.tstatForm['tstatCheckAgg'].checked;";
   $jsCheckCmd="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{agg}$js{XXX}$js{des}$js{hif}advcmd=\"+document.forms.tstatForm['tstatCheckCmd'].checked;";
   $jsCheckDes="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{XXX}$js{hif}describe=\"+document.forms.tstatForm['tstatCheckDes'].checked;";
   $jsCheckHif="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{XXX}hifreq=\"+document.forms.tstatForm['tstatCheckHif'].checked;";
   
   map {
      $pFormat{$_} ="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{agg}$js{cmd}$js{des}$js{hif}format=$_";	     
   } qw(eps pdf rrd);   
#
# javascript to execute -onClik when the NEW's Checkbox state is toggled. 
# note that js{NEW} has to be added to ALL the other javascripts BUT this
# one (where you should use $js{XXX} instead for visual padding)
#
#  $jsCheckNEW="location.href=\"$js{loc}$js{var}$js{dir}$js{log}$js{big}$js{adv}$js{yA0}$js{ymn}$js{ymx}$js{agg}$js{XXX}newvar=\"+document.forms.tstatForm['tstatCheckNew'].checked;";
#
#NEWVAR


   
   ### (Dumper( [ $pDir_default, \@pDir, \%pDir ] )); #"3) pDir=$pDir pDirVEC @pDir pDirHASH %pDir");
    my $timeSpan = "";
    if( $pDir ) {
      my $tspanFile = (glob("$pDir/*rrd"))[0];
      if ( $tspanFile ) {        
          ####RRD BUG
	  my $first = ParseDateString("epoch @{[RRDs::first('--rraindex' ,'3', $tspanFile)]}");
	  #### my $first = ParseDateString("epoch @{[RRDs::first($tspanFile)]}");
	  ####RRD 
	  my $last  = ParseDateString("epoch @{[RRDs::last($tspanFile)]}");
	  my $start = UnixDate($first,'%A the %E of %B %Y, at %H:%M ');
	  my $end   = UnixDate($last,'%A the %E of %B %Y, at %H:%M');
	  my $err;
          # YY:MM:WK:DD:HH:MM:SS  the years, months, etc. between
	  my @unit = qw(year month week day hour minute second);
	  my ($offset,$length) = (0,"");	  
          map { 
	     s/^\+//g;
	     $length .= $_>1 ? "$_ $unit[$offset]s, " : 
	                $_   ? "$_ $unit[$offset], " : "";
	     $offset++;
	  } split ':', DateCalc($first,$last,\$err,1);
	  $length =~ s/,\s+$//g;
	  $length =~ s/^+//g;
	  #$length = DateCalc($last,$first	,\$err,1);

	  $timeSpan = "
	     <tr>
	         <td><b> Start: </b> </td>
	         <td><font size=-1>$start</font> </td>
      	     </tr><tr>
	         <td><b> End:   </b> </td>
		 <td><font size=-1>$end  </font> </td>
      	     </tr><tr>
	         <td><b> Length:   </b> </td>
		 <td><font size=-1>$length  </font> </td>
	     </tr>
	  ";
	  #################### RRD BUG
	   $timeSpan = "";
	  #################### RRD BUG
       }
    }       	     
	   
   return join("\n", 
           start_form(-name => tstatForm ),	     
	   "\n<TABLE width='100%'>",	   
 	       "<hidden NAME=menu 	VALUE='1'>\n",
	       "<hidden NAME=var 	VALUE='$pVar'>\n",
	       "<hidden NAME=dir 	VALUE='$pDir'>\n",
	       "<hidden NAME=template 	VALUE='$pTpl'>\n",
	       "<hidden NAME=duration 	VALUE='$pLen'>\n",
	       "<hidden NAME=logscale 	VALUE='$pLog'>\n",
	       "<hidden NAME=bigpic 	VALUE='$pBigpic'>\n",
	       "<hidden NAME=hifreq 	VALUE='$pHifreq'>\n",
	       "<hidden NAME=aggpic 	VALUE='$pAggpic'>\n",
	   "\n<tr><td>",	       
               "<b> Trace: </b>",
           "</td><td>",   
		    popup_menu(-name=>'tstatMenuDir',
 		       	       -onChange => $jsMenuDir,
			       -default  => $pDir_default,
                               -values   => \@pDir,
			       -attributes => \%pDirAttr,
			       -labels   => \%pDir, ),		
		    button(-name=>'tstatMenuBtn',
                             -value=>'Start Over ',
                             -onClick=>$jsMenuBtn),			       
		    button(-name=>'tstatMenuBtn',
                             -value=>'Home',
                             -onClick=>$jsHomeBtn),	
	   ( $pDir eq "$RRD_DATA" ) ? '' :			     
  		    button(-name=>'tstatMenuBtn',
                             -value=>'RRdata',
                             -onClick=>"location.href='/$pDir'"),			  
	   ## Access to RRD database
           ##"<a href='/$pDir'>[RRData]",
	   
			     
           "\n</td></tr> $timeSpan",   
 	       # "<br>",
	   "<tr><td>",	       
	       "<b> Variable: </b>",
           "</td><td>",   
		    popup_menu(-name=>'tstatMenuVar',
 		       	       -onChange => $jsMenuVar,
			       -default  => $pVar,
                               -values   => \@pVar,
			       -attributes => \%pVarAttr,
			       -labels   => \%pVar, ),			  
           "</td></tr>",   
 	       # "<br>",
	       $pVar =~ m/NULL/ ? '' :
		     join(" ",
        		  # "<br>",     
	   	      "\n<tr><td>",	       
        		  "<b> Options: </b>",
	               "</td><td>",   
 		      checkbox_group(-name=>'tstatCheckDes',
 			  -values =>['Describe...'],
 			  -default => [$pDescribe eq 'true' ? 'Describe...' : ''],
 			  -onClick => $jsCheckDes) ,
                       checkbox_group(-name=>'tstatCheckBig',
                	     -values =>['Bigpic'],
			     -default => [$pBigpic eq 'true' ? 'Bigpic' : ''],
			     -onClick => $jsCheckBig) ,
                       checkbox_group(-name=>'tstatCheckHif',
                	     -values =>['HiFreq'],
			     -default => [$pHifreq eq 'true' ? 'HiFreq' : ''],
			     -onClick => $jsCheckHif) ,
                       checkbox_group(-name=>'tstatCheckAgg',
                	     -values =>['Aggregated'],
			     -default => [$pAggpic eq 'true' ? 'Aggregated' : ''],
			     -onClick => $jsCheckAgg) ,
                       checkbox_group(-name=>'tstatCheckAdv',
                	     -values =>['Advanced...'],
			     -default => [$pAdvopt eq 'true' ? 'Advanced...' : ''],
			     -onClick => $jsCheckAdv) ,
           		"</td></tr>",   
        	     ),		   
		     
		        
            ($pVar !~ m/NULL/ ) && 
            $pAdvopt eq 'true' ?
	       join( " ", 
	   	      "\n<tr><td>",	       
        		  "<b> Advanced: </b>",
	               "</td><td>",  
		       "Ymin: ",
		       textfield(-name=>'tstatYmin',
                                   -default=>$pAutoconf eq 'true'? 'auto' : $pYmin,
                                   -override=>1,
                                   -size=>5,
                                   -maxlength=>10, 
				   -onChange => $jsYmin),
		       "Ymax: ",
		       textfield(-name=>'tstatYmax',
                                   -default=>$pAutoconf eq 'true' ? 'auto' : $pYmax,
                                   -override=>1,
                                   -size=>5,
                                   -maxlength=>10,
				   -onChange => $jsYmax), 
                       checkbox_group(-name=>'tstatAutoconf',
                	     -values =>['Autoconf'],
			     -default => [$pAutoconf eq 'true' ? 'Autoconf' : ''],
			     -onClick => $jsAutoconf) ,
                       checkbox_group(-name=>'tstatCheckLog',
                	     -values =>['Logscale'],
			     -default => [ $pLog eq 'true' ? 'Logscale' : ''],
			     -onClick => $jsCheckLog) ,
                       checkbox_group(-name=>'tstatCheckCmd',
                	     -values =>['RRDcmd'],
			     -default => [$pAdvcmd eq 'true' ? 'RRDcmd' : ''],
	 		     -onClick => $jsCheckCmd) ,

	   	      "</td></tr>",	       
# 	   	      "<tr>
# 		       <td> &nbsp </td>
# 		       <td>",	       
#NEWVAR 
#                        checkbox_group(-name=>'tstatCheckNEWVAR',
#                 	     -values =>['NEWVAR'],
# 			     -default => [$pNEWVAR eq 'true' ? 'NEWVAR' : ''],
# 			     -onClick => $jsCheckNEWVAR) ,
#NEWVAR 
	   	      "</td></tr>",	       
	       ) : "",		     
           end_form,
        );
}


#   ____________________________  
#  /				\ 
# /    menuHtml       __________/ 
# \__________________/.:nonsns:.  
# 				  
#  if you want to add a templa e or a time-scale,
#  you need to modify this
#
sub menuHtml {
my $html;
my @pTpl = qw(avg stdev hit idx prc normidx);
my %pTpl = ();  
my @pLen;

#tstat v.1.2.0, tstat_rrd.gci 2.5: high frequency RRD for short traces
#map { push @pLen, "$RRD_TIME{$_}$_" } qw(h d wk m y); 
    @pLen =  @RRD_TIME;
    
    $format_loose = 0;
    $space = $format_loose ? " " : "";
    
#===============================================
# check for availablte templates
#-----------------------------------------------
  $pTpl{avg}=1 
   if( -e "$pDir/$pVar${RRD_TREE}avg.rrd" && 
       -e "$pDir/$pVar${RRD_TREE}min.rrd" && 
       -e "$pDir/$pVar${RRD_TREE}max.rrd");

  $pTpl{stdev}=1 
   if( -e "$pDir/$pVar${RRD_TREE}avg.rrd" && 
       -e "$pDir/$pVar${RRD_TREE}stdev.rrd");
	  
  $pTpl{hit}=1 
   if( -e "$pDir/$pVar${RRD_TREE}hit.rrd");
	 
  map {	 
 	 my @file = glob("$pDir/$pVar${RRD_TREE}$_*.rrd");
	  $pTpl{$_}=1 if $#file >= 0; 
  } qw(prc idx);	  
  

  my $templateCount = 0;
  map { $templateCount++ if $pTpl{$_} }	keys %pTpl;
  $pTpl{normidx} = $pTpl{idx};


#===============================================
# menu: pasting formHtml, Template, Time together
#-----------------------------------------------
  if ($pVar eq 'NULL' ) {
      # when you first enter a directory, you MUST set pVar = NULL 
      # this make cgi display the pDir/README[.html] file  
      $form = formHtml();
      return returnHtml( formHtml(), "</table>", $pReadme ); 
      
  } else {
      $html .= "<!-- MENU_START -->\n\n";

      # if not all the files to render $pTpl are there, fall back on first avail	
      $pTpl = '' unless $pTpl{$pTpl};

      #IT's a TABLE now!!!
      $html .= formHtml();
      my $templateFirst = "";
      #
      # display first template available by default
      #
      $html .= "<tr><td>";
      $html .= "<b> Template: </b>";
      $html .= "</td><td>";
      foreach my $t qw(avg stdev hit prc idx normidx) {
	    next unless $pTpl{$t};
	    $templateFirst = $t if $templateFirst eq ""; 
	    my $tlab = describeTemplate($t);
    
            $href = "href=tstat_rrd.cgi?dir=$pDir&var=$pVar&template=$t&hifreq=$pHifreq&duration=&bigpic=$pBigpic&loscale=$pLogscale&aggpic=$pAggpic";
	    if ($pLen ne "") {
	       # specific time chosen: pletora of templates
	       $html .=  "[$space<a $href>$tlab</a>$space]" ;
	       
	    } else {
 	       $html .= (($pTpl eq "") && ($t eq $templateFirst)) || 
	       		(($pTpl ne "") && ($t eq $pTpl)) # || ($templateCount == 1) 
			? "\<<b>$tlab</b>\>" :
			  "[$space<a $href>$tlab</a>$space]";
            }  
	    $html .=  "&nbsp"x($format_loose ? 4:2);
	    $html .=  "\n";
      } 
      $html .= "</td></tr>";
      $pTpl  = $templateFirst  if (($pLen  eq '') and ($pTpl eq ''));
      
      #
      # display h,d,w,m,y timescale by default
      #
      $html .= "<tr><td>";
      $html .= "<b> Time:  </b>&nbsp&nbsp";
      $html .= "</td><td>";
      foreach my $d (@pLen) {
	    my $dlab = describeDuration( $d );
            $dlab =~ s/\s*Graph\s*//g; 
	    
            $href = "href=tstat_rrd.cgi?dir=$pDir&var=$pVar&template=&hifreq=$pHifreq&duration=$d&bigpic=$pBigpic&loscale=$pLogscale&aggpic=$pAggpic";
            $html .= ( $d eq $pLen ) ? "\<<b>$dlab</b>\>" : "[$space<a $href>$dlab</a>$space]";
	    $html .=  "&nbsp"x($format_loose ? 4:2);
	    $html .=  "\n";
      }      
      $html .= "</td></tr>";

      #$html .= "\n<br><b> Time Scale: </b>&nbsp&nbsp";
      #      $html .= "[<a href=tstat_rrd.cgi?param=$param&timescale=0.5><b>/2</b></a>]";
      #      $html .=  "&nbsp"x4;
      #      $html .= "[<a href=tstat_rrd.cgi?param=$param&timeshift=-1><b>-1</b></a>]";
      #      $html .=  "&nbsp"x4;
      #      $html .= "[<a href=tstat_rrd.cgi?param=$param&timereset=1><b>Reset</b></a>]";
      #      $html .=  "&nbsp"x4;
      #      $html .= "[<a href=tstat_rrd.cgi?param=$param&timeshift=+1><b>+1</b></a>]";
      #      $html .=  "&nbsp"x4;
      #      $html .= "[<a href=tstat_rrd.cgi?param=$param&timescale=2><b>*2</b></a>]";
      #      $html .=  "\n";
	
      $html .= "</TABLE>";	
      return returnHtml(   $html, "<h3>No template available</h3>" ) unless $templateCount;
		
      #XXX       } else {
      #        	    verb("Templates available ($param,$template,$duration)");
      #   	    map { verb("\t$_") } keys %tmpl;
      #XXX       }   
  }    	
  $html .= "<!-- MENU_END -->\n\n";  
  $htmlmenu = $html;


#===============================================
# describe
#-----------------------------------------------
    $htmlmenu .= describePlot() if $pDescribe eq 'true';
  
#===============================================
# plots: pasting images and form
#-----------------------------------------------
  if (($pLen eq '') or($pTpl eq '') ) {
      verb("MENU: given template ($pTpl), loop over time") if ($pLen eq '') ;
      verb("MENU: given duration ($pLen), loop over template") if ($pTpl eq '');
  
      my @X = ($pLen eq '') ? @pLen : @pTpl;
 
      $html = "\n";
      X:
      foreach my $x (@X) {
            my ($imagef,$dlab,$epsf);	    
	    if ($pLen eq '') {
            # given template, loop over time
		     $imagef = applyTemplate( graphTemplate($pDir,$pVar,$pTpl,$x) );   	    
		     $dlab = describeDuration( $x );
	    } else {    
            # given duration, loop over template
	    	next X unless $pTpl{$x};
        	      $imagef = applyTemplate( graphTemplate($pDir,$pVar,$x,$pLen)  );   
		      $dlab = describeTemplate( $x );		      
	    }	    
	    $epsf = $imagef; 
	    $epsf =~ s/png/eps/g;

	    #   ____________________________  
	    #  /			    \ 
	    # /    eps            __________/ 
	    # \__________________/.:nonsns:.  
	    # 				  
	    # are hidden to the rest of the world...
	    my $other_formats = (remote_host() =~ m/(polito.it$|^130\.192\.|^192\.168\.)/) ?
	        "&nbsp&nbsp
		<font size=-3> 
		<a href='/$epsf'>[PostScript]</a> &nbsp&nbsp
                </font>" : ""; 
	    
	    $html .= join("", "<h2> $dlab $other_formats </h2>\n",
	                       ( -e $imagef ) ? 
			       		"<img src='/$imagef'></img>" : 
					"<pre> $imagef </pre>",
     			 "\n<br><br><hr>\n");
      }			 
  } else {
     die join("\n", "Oops, I cannot quite make it out...
       dir=$pDir
       var=$pVar
       log=$pLog
       len=$pLen
       tpl=$pTpl
       ");
  }

  return returnHtml(  $htmlmenu, $html  );
}


#   ____________________________  
#  /				\ 
# /    describePlot   __________/ 
# \__________________/.:nonsns:.  
# 	
sub describePlot {
   my $anchor = $pVar;
      $anchor  =~ s/_(in|out|c2s|s2c|loc)$//g;

   
   my $tdes;
   if ($pLen ne '') {
      $tdes = "You are now seeing, for a specific <B>timespan</b> (
       @{[describeDuration($pLen)]} ), 
      all the available templates for the selected metric
      (<a target=help href='http://tstat.tlc.polito.it/measure.html#$anchor'> $description{$pVar}</A>). 
      To get the description of a specific <b>template</b> you have to select it first,
      and observe it at different time granularities.",
   } else {
      $tdes = "You are now seeing, a specific <B>template</b> (
      @{[describeTemplate($pTpl)]} </a>), 
      over all the available timespans for the selected metric (
      <a  target=help href='http://tstat.tlc.polito.it/measure.html#$anchor'> $description{$pVar}</a>). 
      $templateDescription{$pTpl}"
   }
   return "
   <hr>
   <h2> Description </h2>
   <table border=0 width=625>
   <!-- -->
   <tr><td colspan=2><B> Metric Description: </B> </td></tr>
   <tr><td>  &nbsp &nbsp &nbsp </td><td>
   	<iframe SCROLLING=no
	 frameborder=0
	 width=800
	 height=100 src='http://tstat.tlc.polito.it/measure.html#$anchor'>
	</iframe>
   </td></tr>
   <!-- -->
   <tr><td colspan=2> <B> Template Description: </B><br> </td></tr>   	
   <tr><td> &nbsp &nbsp &nbsp </td><td>
     <p align=justify>
	$tdes
	</p>
   </td></tr>
   </table>
   <hr>
   ";
   
}


#   ____________________________  
#  /				\ 
# /    applyTemplate  __________/ 
# \__________________/.:nonsns:.  
# 	
sub applyTemplate {
   # support library or system call   
    verb("RRDs::graph($param,$template,$duration)");
    $filename = $_[0];

    if ( $pAdvcmd eq 'true' ) {
         return join( "", 
	 "/usr/local/rrdtool/bin/rrdtool graph \\\n\t'", (join "' \\\n\t'", @_), "'");
    }

    # png
    #     shift @_;
    #     unshift @_, ($filename, '--vertical-label','Tstat/RRD');
    RRDs::graph(@_);
    my $ERR=RRDs::error;
    die "ERROR while drawing: $ERR in\n\nrrdtool graph @_\n"
 		if $ERR;

    #eps 
    shift @_;
    unshift @_, ($filename, '--font','DEFAULT:14:TimesBold');
    map { 
    	m/PNG/ and s/PNG/EPS/; 
   	m/png/ and s/png/eps/; 
    } @_;
    RRDs::graph(@_);
    my $ERR=RRDs::error;
    die "ERROR while drawing: $ERR in\n\nrrdtool graph @_\n"
 		if $ERR;

   return $filename; #image filename
}

#   ____________________________  
#  /				\ 
# /   graphTemplate   __________/ 
# \__________________/.:nonsns:.  
# 				  
#
#  the intelligence of tstat_rrd.cgi
#  this turns files into nice and colored graphs
#
sub graphTemplate {
my ($dir,$var,$template,$duration)=@_;
my (@RRDpar,@RRDoth);
   $param = "$dir/$var";

   $imagef = "$param$RRD_TREE$template.$duration.png"; 
   $imagef =~ s{^/+}{}g; # chomp initial /
   $imagef =~ s{/+}{/}g; # chomp multiple //
   $imagef =~ s{/}{.}g;  # turn / into . 
   $imagef = "$IMG_DIR/$imagef";
   #--imginfo '<IMG SRC="/img/%s" WIDTH="%lu" HEIGHT="%lu" ALT="Demo">'

   my $par;
   if($RRD_TREE=='.') {
      $par = (split '\.', (split '\/', $param)[-1])[0]
   } else {
      $par = (split '\/', $param)[-2]
   }

   # aggregate 
   my ($other,$oth,@oth);
   my ($partag,$othtag)=("","");
   if ($pAggpic eq 'true') {
      my ($adir,$apar);
      ( $adir = $param ) =~ s/_(in|out|c2s|s2c)$//;
      ( $apar = $par   ) =~ s/_(in|out|c2s|s2c)$//;
      my $pfix = $1;
      if ( $pfix =~ m/(in|out)$/ ) {
         $param  = "${adir}_out";
	 $par    = "${apar}_out";
         $partag = " (out)";  
         $other  = "${adir}_in";  
	 $oth    = "${apar}_in";
	 $othtag = " (in)";
	 
      } elsif ( $pfix =~ m/(c2s|s2c)$/ )  {
         $param  = "${adir}_c2s";  
	 $par    = "${apar}_c2s";
	 $partag = " (c2s)";
         $other  = "${adir}_s2c";  
	 $oth    = "${apar}_s2c";
	 $othtag = " (s2c)";
	 
      } else {
         $other = "NULL";
      }      
   } else {
         $other = "NULL"
   }


   my $title = "$description{$par} [@{[ describeTemplate($template) ]}]";
   if ( $other ne "NULL" ) {
   	$title =~ s/incoming/outgoing (+) and incoming (-)/ or
   	$title =~ s/outgoing/outgoing (+) and incoming (-)/ or
   	$title =~ s/client/client (+) and server (-)/ or
   	$title =~ s/server/client (+) and server (-)/;
   }

   push @RRDpar, $imagef, 
                 '--imgformat', 'PNG', 
		 '--title', $title;
		 '--color', "'BACK=$color{gray}'";
   push @RRDpar, '--logarithmic' 
   		if $pLog eq 'true'; 		
   # any satanic reference is purely coincidental:
   # 666 is closest integer such that multiplied by
   # the selected zoom factor picture width is 800
   push @RRDpar, '--width', '666',  '--height', '200' 
   		if $pBigpic eq 'true';
   push @RRDpar, '--zoom', '1.18';
     
   # upper limit
   my $rigid=0;
   if ( $template =~ m/normidx/ && 
      (( $pAutoconf eq 'true') || ($pYmax eq ""))) {
      $rigid=1;
      push @RRDpar, "--rigid", "--upper-limit", 100;
   } elsif( ($pYmax ne "") && ( $pAutoconf ne 'true' )) {
      $rigid=1;
      push @RRDpar, "--rigid", "--upper-limit", "$pYmax";
   }		   
 
   if( ($pYmin ne "") && ( $pAutoconf ne 'true' )) {
   	push @RRDpar, "--rigid" unless $rigid;
   	push @RRDpar, "--lower-limit", "$pYmin";
   }
		

   my $template_suffix = ( $template eq 'normidx' ) ? 'idx' : $template;
   if( $duration ne "" && 
      -e ($file = (glob "$param${RRD_TREE}${template_suffix}*.rrd")[0] )) {         
      #AWFUL trick to account for (idx|prc)*
       $last = RRDs::last("$file");
       push @RRDpar, "--end", "$last",
       		     "--start", "end-$duration";
		     
   } else {
   	warn "Duration $duration was specified, but no file $file 
	found by globbing $param${RRD_TREE}${template}*.rrd 
        ... ignoring"
   }	      
   
   # At this point, 
   #
   # $param = rrd_data/Polito/2000/May/protocol_out 
   # $par = protocol_out
   #
   my ($x,$X)=(0,'A');
   my @par;
    
   
   if ($template =~ m/(stdev)/ ) { 
       #
       # this one is special
       #
       push @RRDpar, 	
       	"DEF:avg=$param${RRD_TREE}avg.rrd:$par:AVERAGE",
        "DEF:stdev=$param${RRD_TREE}stdev.rrd:$par:AVERAGE",
        "CDEF:p3s=avg,stdev,3,*,+",
        "CDEF:p1s=avg,stdev,+",
      	"LINE1:p3s$color{dred}: Average + 3*Stdev",
	"LINE2:p1s$color{red}: Average + Stdev",
        "LINE3:avg$color{orange}: Average";

	if ($other ne 'NULL') {
	  push @RRDpar, 	
       	   "DEF:oth_avg=$other${RRD_TREE}avg.rrd:$oth:AVERAGE",
           "DEF:oth_stdev=$other${RRD_TREE}stdev.rrd:$oth:AVERAGE",
           "CDEF:neg_avg=0,oth_avg,-",
           "CDEF:neg_p3s=neg_avg,oth_stdev,3,*,-",
           "CDEF:neg_p1s=neg_avg,oth_stdev,-",
       	   "LINE1:neg_p3s$color{dred}:",
       	   "LINE2:neg_p1s$color{red}:",
       	   "LINE3:neg_avg$color{orange}:";	
	}
	
#die join "\n", @RRDpar;
        return @RRDpar;			

   } elsif ($template =~ m/(hit)/ ) {
       @par = qw(hit);

   } elsif ($template =~ m/(avg|max|min)/ ) {
       @par = qw(min avg max);
	
   } elsif ($template =~ m/(normidx|idx|prc)/ ) {
   	my $template_suffix = ( $template eq 'normidx' ) ? 'idx' : $template;
	map { 
		push @par, "$1$2" if m/(idx|prc)(\d+\.*\d*|oth)\.rrd/;
	} glob "$param${RRD_TREE}$template_suffix*rrd";
	@par or die "No indexes for $template_suffix for $param";
	@par = sort { 
	   ($numA=$a) =~ s/(idx|prc)//;
	   ($numB=$b) =~ s/(idx|prc)//;
	   #oth is always last"
	   return ( $a eq "oth" ) ? 1 :
	          ( $b eq "oth" ) ? -1 :
	          m/idx/ ? $numA <=> $numB :
		           $numB <=> $numA;  # care to this order
        } @par;
   } else {
   	die "Man, $template is no template I know";
   }

	
   $kind = lineStyle($template,0);

   my @RRD_posdef;
   my @RRD_negdef;
   my @RRD_poscdef;
   my @RRD_negcdef;
   my @RRD_posline;
   my @RRD_negline;
   
   #for normidx
   my $sumpos="CDEF:pos_sum=0";
   my $sumneg="CDEF:neg_sum=0";
   map {

      if( -e ($file = "$param$RRD_TREE$_.rrd" )) {
         $kind = lineStyle($template,$x);
	 ####XXX $line = "$kind:$X$defColor[$x]:$description{$par} (@{[labelOf($_)]})";

	 #partag is empty if Aggpic=false
	 $line = "$kind:pos_$X$defColor[$x]:@{[labelOf($par,$_)]}";
         $def = "DEF:$X=$file:$par:AVERAGE";
         $cdef = "CDEF:pos_$X=$X";
         $cdef .= ",100.0,*,pos_sum,/" if $template =~ m/normidx/;
	 $sumpos .= ",$X,+";
	 	 
	 push @RRD_posdef, $def;
	 push @RRD_poscdef, $cdef;
	 push @RRD_posline, $line;	            

  	 if ($other ne 'NULL') {
	    if(-e ($othfile="$other$RRD_TREE$_.rrd") ) {
	       
	       #$kind='STACK' if ( $kind eq 'AREA' and $par =~ m/idx/ );
	       
	       $line = "$kind:neg_$X$defColor[$x]:";#@{[labelOf($par,$_)]}$othtag";
               $def = "DEF:oth_$X=$othfile:$oth:AVERAGE";
  	
	       $cdef = "CDEF:neg_$X=0,oth_$X,-";
	       $cdef .= ",100.0,*,neg_sum,/" if $template =~ m/normidx/;
	       
               $sumneg .= ",oth_$X,+";
	       push @RRD_negdef, $def;
	       push @RRD_negcdef, $cdef;
	       push @RRD_negline, $line;	            
	    }      	    
	 }
	 
	 $X++ and $x++;	 
      } else {
	 die "Warning: file $file was not found to build template $template";
      }   
   } @par;
   
   push @RRDpar, (@RRD_posdef, $sumpos, @RRD_poscdef, @RRD_posline);
   push @RRDpar, (@RRD_negdef, $sumneg, @RRD_negcdef, @RRD_negline)
	   if ($other ne 'NULL');


  return @RRDpar;

  # do not wanna die...
  #
  #   # GRAPH
  #   die "/usr/local/rrdtool/bin/rrdtool graph \\\n'", (join "' \\\n\t'", @RRDpar);
  # 
  #   # EXPORT
  #   die "/usr/local/rrdtool/bin/rrdtool xport \\\n'", (join "' \\\n\t'", 
  #   @RRD_posdef, $sumpos, @RRD_poscdef,  'XPORT:pos_sum	', 'XPORT:pos_A'), "'\n";
}

#   ____________________________  
#  /				\ 
# /    label & Co.    __________/ 
# \__________________/.:nonsns:.  
# 				  
#
#  description of labels, lineSyles, durations, etc.
# 
sub labelOf {
my ($par,$idx) = @_; 
  local $_ = lc("$idx");
       if( m/min/ )     {  return 'Minimum'
  } elsif( m/max/ )     {  return 'Maximum'
  } elsif( m/avg/ )     {  return 'Average'
  } elsif( m/var/ )     {  return 'Variance' 
  } elsif( m/stdev/ )   {  return 'Standard Deviation'
  } elsif( m/idx(.*)/ ) {  return $1 ne "oth" ? describeIdx($par,$1) : "Others"
  } elsif( m/prc(.*)/ ) {  return $1 ne "oth" ? "$1-th Percentile" : "Others"
  } elsif( m/hit/ )     {  return "Hit Counter"
  } else {
	  return "Unknown parameter statistics $1 ... "
  }	  
}

sub describeIdx {
my ($par,$idx) = @_; 
   if( exists $idx2value->{$par}{$idx} && $idx2value->{$par}{$idx} ne "" ) {
        $longest = 0;
	map { 
		$len = length($idx2value->{$par}{$_});
 	        $longest = $len if  $longest < $len;
        } keys %{ $idx2value->{$par} };
	$longest += 3;
	return sprintf "%-${longest}s", $idx2value->{$par}{$idx};
   	# return join(" ", $idx2value->{$par}{$idx}, " "x20)
   }
   return "$par = $idx";
} 
 

sub lineStyle {
  local $_ = lc(shift);
  $num = shift;
  if( m/(min|max|avg|var|stdev|hit)/ )     {  
  	return 'LINE2'
  } elsif( m/idx/ )     {  
  	return $num ? 'STACK' : 'AREA'
  } elsif( m/prc/ )     {  
  	return 'AREA'; #they must be carefully sorted
  } else {
	return "Unknown parameter statistics $1 ... "
  }	  
}

sub describeTemplate {
local $_ = shift;
    return "Hit Counter"	if m/hit/;
    return "Mean and Bounds"    if m/(avg|max|min)/; 
    return "Mean and Stdev"     if m/stdev/; 
    return "Normalized Values"  if m/normidx/;  
    return "Specific Values"    if m/idx/;  
    return "Distribution"       if m/prc/; 
    return "Unknown Template"   
}   	


%templateDescription = (
 	hit => "
Though I have coded this template, I have never seen one of these,
so I do not have any idea of what it should look like.",
 	avg => "
This template shows, as three distinct lines, the <B>minimum</b>, <B>average</b> and
<B>maximum</b> values achieved by the observed metric in the
given timespan, practically bounding the extent of its distribution.",
 	stdev => "
This template shows three distinct lines: the lowest is the <B>average</b> 
value achieved by the observed metric in the given timespan; the intermediate
is given by the sum of  <B>average + standard deviation</b>  and the 
upper is given by the sum of the former plus three times the latter.
This plot should not be interpreted in a B<quantitative> way, but in a rather
the <B>qualitative</b> way: indeed, these curves reflect the rate of change,
in the sense that a sharp peak correspond to an abrupt change of the observed 
metric, change which is further amplified by the intermediate and upper curves.",
	idx => "
This template shows several stacked areas, corresponding to the <b>raw amount</b>
of the observed metric the given timespan: each of the curves is a simple counter
of the number of times that  the observed metric achieved a specific value.
For example, these areas can count the number of packets of a given size as
well as the number of flows on a given port, or the TCP options negotiated;
finally, note that there is a corresponding normalized template.",
	normidx => "
This template shows several stacked areas, corresponding to the <b>normalized amount</b>
of the observed metric the given timespan: each of the curves are simple counters 
of the number of times that  the observed metric achieved a specific value,
normalized over the number of samples observed over the same timespan.
For example, these areas can count the percentage of packets of a given size as
well as the percentage of flows on a given port; finally, note that there is a 
corresponding  template which no not make use of normalization.",
	prc => "
This template shows several stacked areas, corresponding to the <b>quantiles</b>
of the distribution of the observed metric the given timespan; the time-varying 
distributions usually show the <B>statistical median</b> (which corresponds
to the 50-th percentile of the distribution) as well as the 90-th, 95-th and 99-th 
quantiles.",
);
 
	
$templateDescription{min}=$templateDescription{max}=$templateDescription{avg};



sub describeDuration {
local $_ = shift;

   if ( $pHifreq eq 'true' ) {
    return "1hr"  	        if m/^1h/;
    return "4hrs" 		if m/^4h/;
    return "12hrs"		if m/^12h/;
    return "24hrs"		if m/^24h/;
    return "48hrs"		if m/^48h/;
  } else {    
    return "Hourly Graph"  	if m/$RRD_TIME{h}h/;
    return "Daily Graph"  	if m/$RRD_TIME{d}d/;
    return "Weekly Graph"  	if m/$RRD_TIME{w}w/;
    return "Monthly Graph" 	if m/$RRD_TIME{m}m/;
    return "Yearly Graph"  	if m/$RRD_TIME{y}y/;
  }    
  return "Custom Duration ($_)"	      
}

 

 
 
#   ____________________________  
#  /				\ 
# /    Global Vars.   __________/ 
# \__________________/.:nonsns:.  
# 				  


#===============================================
#  I see your true colors... 
#-----------------------------------------------
# NAMING NOTATION
#
# (gp|d|m|l)s*{color}   
#  |  | | | |	    
#  |  | | | + slate 
#  |  | | + light   
#  |  | + medium    
#  |  + dark
#  + gnuplot	  
#
%color = ( 
#gnuplot colors
	   gpblue => '#0000FF',
	   gpcyan => '#00FFFF',
	   gpgreen => '#00FF00',
	   gpbrown => '#A0522D',
	   gporange => '#FFA500',
	   gpyellow => '#FFFF00',
	   gpred => '#FF0000',
	   gpmagenta => '#FF00FF',

#lucy in the sky with diamonds
          'msblue' => '#7B68EE',
          'sblue' => '#6A5ACD',
          'dblue' => '#00008B',
          'dsblue' => '#483D8B',
          'mblue' => '#0000CD',
          'lsblue' => '#8470FF',
          'blue' => '#0000FF',
          'lblue' => '#ADD8E6',

          'cyan' => '#00FFFF',
          'dscyan' => '#00CED1',
          'mscyan' => '#48D1CC',
          'mcyan' => '#66CDAA',
          'dcyan' => '#008B8B',
          'lcyan' => '#E0FFFF',

#tequila sunrise
          'red' => '#FF0000',
          'dred' => '#8B0000',

          'yellow' => '#FFFF00',
          'lyellow' => '#FFFFE0',
          'dyellow' => '#B8860B',

          'orange' => '#FFA500',
          'dorange' => '#FF8C00',

#the color of money
          'green' => '#00FF00',
          'lgreen' => '#90EE90',
          'dsgreen' => '#8FBC8F',
          'msgreen' => '#00FA9A',
          'mgreen' => '#3CB371',
          'dgreen' => '#006400',

#the ping panther
          'dpink' => '#E9967A',
          'pink' => '#FFC0CB',
          'lpink' => '#FFB6C1',
          'dspink' => '#FF1493',
          'mpink' => '#FF69B4',

          'lmagenta' => '#FFA07A',
          'dmagenta' => '#8B008B',
          'magenta' => '#FF00FF',
          'lmagenta' => '#FFA07A',

          'lviolet' => '#DB7093',
          'mviolet' => '#C71585',
          'violet' => '#EE82EE',
          'dviolet' => '#9400D3',

#black and white, unite
          'white' => '#FFFFFF',
          'dsgray' => '#2F4F4F',
          'lgray' => '#D3D3D3',
          'black' => '#000000',
          'gray' => '#BEBEBE',
          'dgray' => '#A9A9A9',
          'lsgray' => '#778899',
);


# Default colors - these are from gnuplot:
@defColor = qw(gpblue gpcyan gpgreen gpbrown gporange gpyellow gpred gpmagenta
	        dblue   dcyan  dgreen  dgray  dorange  dpink  dred  dmagenta
	        lblue   lcyan  lgreen  lgray  lorange  lpink  lred  lmagenta
	 	 blue    cyan   green   gray   orange   pink   red   magenta
               dsblue  dscyan dsgreen dsgray          dspink );
map { $_ = $color{$_} } @defColor;



#===============================================
#  description (reverse of the former)
#-----------------------------------------------
# describe Tstat parameter in a human readable format
# automatically generated by:
#
#  /home17/mellia/LIPAR/mellia/tstat/tstat_v1.0beta/tstat -H | tr -d '#' | grep -v '^$' | awk -F'|' 'BEGIN{ print "%description = ("} (NR>1) {  printf "\t%s => \"%s\",\n", $1, $5  } END { print ");"}' > descr.txt
#
%description = (
        flow_number      => "Number of tracked TCP/UDP/RTP/RTCP flow",
	rtcp_avg_inter_delay_loc	 => "RTCP interarrival delay - local flows",
	rtcp_avg_inter_delay_out	 => "RTCP interarrival delay - outgoing flows",
	rtcp_avg_inter_delay_in	 => "RTCP interarrival delay - incoming flows",
	rtcp_cl_p_loc	 => "RTCP flow lenght [packet] - local flows",
	rtcp_cl_p_in	 => "RTCP flow lenght [packet] - incoming flows",
	rtcp_cl_p_out	 => "RTCP flow lenght [packet] - outgoing flows",
	rtp_oos_p_loc	 => "RTP number of  out of sequence packets - local flows",
	rtp_oos_p_out	 => "RTP number of  out of sequence packets - outgoing flows",
	rtp_oos_p_in	 => "RTP number of  out of sequence packets - incoming flows",
	rtp_reord_delay_loc	 => "RTP delay of reordered packets - local flows",
	rtp_reord_delay_out	 => "RTP delay of reordered packets - outgoing flows",
	rtp_reord_delay_in	 => "RTP delay of reordered packets - incoming flows ",
	rtp_reord_p_n_loc	 => "RTP number of reordered packets - local flows",
	rtp_reord_p_n_out	 => "RTP number of reordered packets - outgoing flows",
	rtp_reord_p_n_in	 => "RTP number of reordered packets - incoming flows ",
	rtp_burst_loss_loc	 => "RTP burst lenght [packet] - local flows",
	rtp_burst_loss_out	 => "RTP burst lenght [packet] - outgoing flows",
	rtp_burst_loss_in	 => "RTP burst lenght [packet]- incoming flows ",
	rtp_p_late_loc	 => "RTP prob of late packets - local flows",
	rtp_p_late_out	 => "RTP prob of late packets - outgoing flows",
	rtp_p_late_in	 => "RTP prob of late packets - incoming flows ",
	rtp_p_lost_loc	 => "RTP prob of lost packets - local flows",
	rtp_p_lost_out	 => "RTP prob of lost packets - outgoing flows",
	rtp_p_lost_in	 => "RTP prob of lost packets - incoming flows ",
	rtp_p_dup_loc	 => "RTP prob of duplicate packets - local flows",
	rtp_p_dup_out	 => "RTP prob of duplicate packets - outgoing flows",
	rtp_p_dup_in	 => "RTP prob of duplicate packets - incoming flows ",
	rtp_p_oos_loc	 => "RTP percentage of  out-of-sequence packets local flows",
	rtp_p_oos_out	 => "RTP percentage of  out-of-sequence packets - outgoing flows",
	rtp_p_oos_in	 => "RTP percentage of  out-of-sequence packets - incoming flows",
	rtp_n_oos_loc	 => "RTP number of  out-of-sequence packets - local flows",
	rtp_n_oos_out	 => "RTP number of  out-of-sequence packets - outgoing flows",
	rtp_n_oos_in	 => "RTP number of  out-of-sequence packets - incoming flows ",
	rtp_avg_jitter_loc	 => "RTP average jitter - local flows",
	rtp_avg_jitter_out	 => "RTP average jitter - outgoing flows",
	rtp_avg_jitter_in	 => "RTP average jitter - incoming flows",
	rtp_avg_delay_loc	 => "RTP average delay - local flows",
	rtp_avg_delay_out	 => "RTP average delay - outgoing flows",
	rtp_avg_delay_in	 => "RTP average delay - incoming flows",
	rtp_cl_p_loc	 => "RTP flow lenght [packet] - local flows",
	rtp_cl_p_in	 => "RTP flow lenght [packet] - incoming flows",
	rtp_cl_p_out	 => "RTP flow lenght [packet] - outgoing flows",
	rtp_tot_time_loc	 => "RTP flow lifetime [ms] - local flows",
	rtp_tot_time_out	 => "RTP flow lifetime [ms] - outgoing flows",
	rtp_tot_time_in	 => "RTP flow lifetime [ms] - incoming flows",
	udp_port_flow_dst	 => "UDP destination port per flow",
	udp_port_dst_loc	 => "UDP destination port - local packets",
	udp_port_dst_out	 => "UDP destination port - outgoing packets",
	udp_port_dst_in	 => "UDP destination post - incoming packets",
	udp_tot_time	 => "UDP flow lifetime [ms]",
	udp_cl_b_l_loc	 => "UDP flow lenght [byte] - local",
	udp_cl_b_l_in	 => "UDP flow lenght [byte] - incoming",
	udp_cl_b_l_out	 => "UDP flow lenght [byte] - outgoing",
	udp_cl_b_s_loc	 => "UDP flow lenght [byte] - local",
	udp_cl_b_s_in	 => "UDP flow lenght [byte] - incoming",
	udp_cl_b_s_out	 => "UDP flow lenght [byte] - outgoing",
	udp_cl_p_loc	 => "UDP flow lenght [packet] - local",
	udp_cl_p_in	 => "UDP flow lenght [packet] - incoming",
	udp_cl_p_out	 => "UDP flow lenght [packet] - outgoing",
	tcp_interrupted	 => "TCP Early interrupted flows",
	tcp_thru_s2c	 => "TCP throughput [Kbps] - server flows",
	tcp_thru_c2s	 => "TCP throughput [Kbps] - client flows",
	tcp_tot_time	 => "TCP flow lifetime [ms]",
	tcp_unnecessary_rtx_FR_s2c	 => "TCP number of Unneeded FR retransmission - server flows",
	tcp_unnecessary_rtx_FR_c2s	 => "TCP number of Unneeded FR retransmission - client flows",
	tcp_unnecessary_rtx_FR_loc	 => "TCP number of Unneeded FR retransmission - local flows",
	tcp_unnecessary_rtx_FR_out	 => "TCP number of Unneeded FR retransmission - outgoing flows",
	tcp_unnecessary_rtx_FR_in	 => "TCP number of Unneeded FR retransmission - incoming flows",
	tcp_unnecessary_rtx_RTO_s2c	 => "TCP number of Unneeded RTO retransmission - server flows",
	tcp_unnecessary_rtx_RTO_c2s	 => "TCP number of Unneeded RTO retransmission - client flows",
	tcp_unnecessary_rtx_RTO_loc	 => "TCP number of Unneeded RTO retransmission - local flows",
	tcp_unnecessary_rtx_RTO_out	 => "TCP number of Unneeded RTO retransmission - outgoing flows",
	tcp_unnecessary_rtx_RTO_in	 => "TCP number of Unneeded RTO retransmission - incoming flows",
	tcp_flow_control_s2c	 => "TCP number of Flow Control - server flows",
	tcp_flow_control_c2s	 => "TCP number of Flow Control - client flows",
	tcp_flow_control_loc	 => "TCP number of Flow Control - local flows",
	tcp_flow_control_out	 => "TCP number of Flow Control - outgoing flows",
	tcp_flow_control_in	 => "TCP number of Flow Control - incoming flows",
	tcp_unknown_s2c	 => "TCP number of unknown anomalies - server flows",
	tcp_unknown_c2s	 => "TCP number of unknown anomalies - client flows",
	tcp_unknown_loc	 => "TCP number of unknown anomalies - local flows",
	tcp_unknown_out	 => "TCP number of unknown anomalies - outgoing flows",
	tcp_unknown_in	 => "TCP number of unknown anomalies - incoming flows",
	tcp_net_dup_s2c	 => "TCP number of Network duplicates - server flows",
	tcp_net_dup_c2s	 => "TCP number of Network duplicates - client flows",
	tcp_net_dup_out	 => "TCP number of Network duplicates - local flows",
	tcp_net_dup_out	 => "TCP number of Network duplicates - outgoing flows",
	tcp_net_dup_in	 => "TCP number of Network duplicates - incoming flows",
	tcp_reordering_s2c	 => "TCP number of packet reordering - server flows",
	tcp_reordering_c2s	 => "TCP number of packet reordering - client flows",
	tcp_reordering_loc	 => "TCP number of packet reordering - local flows",
	tcp_reordering_out	 => "TCP number of packet reordering - outgoing flows",
	tcp_reordering_in	 => "TCP number of packet reordering - incoming flows",
	tcp_rtx_FR_s2c	 => "TCP number of FR Retransmission - server flows",
	tcp_rtx_FR_c2s	 => "TCP Number of FR Retransmission - client flows",
	tcp_rtx_FR_loc	 => "TCP Number of FR Retransmission - local flows",
	tcp_rtx_FR_out	 => "TCP Number of FR Retransmission - outgoing flows",
	tcp_rtx_FR_in	 => "TCP number of FR Retransmission - incoming flows",
	tcp_rtx_RTO_s2c	 => "TCP Number of RTO Retransmission - server flows",
	tcp_rtx_RTO_c2s	 => "TCP Number of RTO Retransmission - client flows",
	tcp_rtx_RTO_loc	 => "TCP Number of RTO Retransmission - local flows",
	tcp_rtx_RTO_out	 => "TCP Number of RTO Retransmission - outgoing flows",
	tcp_rtx_RTO_in	 => "TCP Number of RTO Retransmission - incoming flows",
	tcp_anomalies_s2c	 => "TCP total number of anomalies - server flows",
	tcp_anomalies_c2s	 => "TCP total number of anomalies - client flows",
	tcp_anomalies_loc	 => "TCP total number of anomalies - local flows",
	tcp_anomalies_out	 => "TCP total number of anomalies - outgoing flows",
	tcp_anomalies_in	 => "TCP total number of anomalies - incoming flows",
	tcp_rtt_cnt_s2c	 => "TCP flow RTT valid samples - server flows",
	tcp_rtt_cnt_c2s	 => "TCP flow RTT valid samples - client flows",
	tcp_rtt_cnt_loc	 => "TCP flow RTT valid samples - local flows",
	tcp_rtt_cnt_in	 => "TCP flow RTT valid samples - incoming flows",
	tcp_rtt_cnt_out	 => "TCP flow RTT valid samples - outgoing flows",
	tcp_rtt_stdev_s2c	 => "TCP flow RTT standard deviation [ms] - server flows",
	tcp_rtt_stdev_c2s	 => "TCP flow RTT standard deviation [ms] - client flows",
	tcp_rtt_stdev_loc	 => "TCP flow RTT standard deviation [ms] - local flows",
	tcp_rtt_stdev_in	 => "TCP flow RTT standard deviation [ms] - incoming flows",
	tcp_rtt_stdev_out	 => "TCP flow RTT standard deviation [ms] - outgoing flows",
	tcp_rtt_max_s2c	 => "TCP flow maximum RTT [ms] - server flows",
	tcp_rtt_max_c2s	 => "TCP flow maximum RTT [ms] - client flows",
	tcp_rtt_max_loc	 => "TCP flow maximum RTT [ms] - local flows",
	tcp_rtt_max_in	 => "TCP flow maximum RTT [ms] - incoming flows",
	tcp_rtt_max_out	 => "TCP flow maximum RTT [ms] - outgoing flows",
	tcp_rtt_avg_s2c	 => "TCP flow average RTT [ms] - server flows",
	tcp_rtt_avg_c2s	 => "TCP flow average RTT [ms] - client flows",
	tcp_rtt_avg_loc	 => "TCP flow average RTT [ms] - local flows",
	tcp_rtt_avg_in	 => "TCP flow average RTT [ms] - incoming flows",
	tcp_rtt_avg_out	 => "TCP flow average RTT [ms] - outgoing flows",
	tcp_rtt_min_s2c	 => "TCP flow minimum RTT [ms] - server flows",
	tcp_rtt_min_c2s	 => "TCP flow minimum RTT [ms] - client flows",
	tcp_rtt_min_loc	 => "TCP flow minimum RTT - local flows",
	tcp_rtt_min_in	 => "TCP flow minimum RTT [ms]- incoming flows",
	tcp_rtt_min_out	 => "TCP flow minimum RTT [ms] - outgoing flows",
	tcp_cl_b_l_s2c	 => "TCP flow lenght [byte] - coarse granularity histogram - server flows",
	tcp_cl_b_l_c2s	 => "TCP flow lenght [byte] - coarse granularity histogram - client flows",
	tcp_cl_b_s_s2c	 => "TCP flow lenght [byte] - fine granularity histogram - server flows",
	tcp_cl_b_s_c2s	 => "TCP flow lenght [byte] - fine granularity histogram - client flows",
	tcp_cl_b_l_loc	 => "TCP flow lenght [byte] - coarse granularity histogram - local flows",
	tcp_cl_b_l_in	 => "TCP flow lenght [byte] - coarse granularity histogram - incoming flows",
	tcp_cl_b_l_out	 => "TCP flow lenght [byte] - coarse granularity histogram - outgoing flows",
	tcp_cl_b_s_loc	 => "TCP flow lenght [byte] - fine granularity histogram - local flows",
	tcp_cl_b_s_in	 => "TCP flow lenght [byte] - fine granularity histogram - incoming flows",
	tcp_cl_b_s_out	 => "TCP flow lenght [byte] - fine granularity histogram - outgoing flows",
	tcp_cl_p_s2c	 => "TCP flow lenght [packet] - server flows",
	tcp_cl_p_c2s	 => "TCP flow lenght [packet] - clientflows",
	tcp_cl_p_loc	 => "TCP flow lenght [packet] - local flows",
	tcp_cl_p_in	 => "TCP flow lenght [packet] - incoming flows",
	tcp_cl_p_out	 => "TCP flow lenght [packet] - outgoing flows",
	tcp_cwnd	 => "TCP in-flight-size [byte]",
	tcp_win_max	 => "TCP max RWND [byte]",
	tcp_win_avg	 => "TCP average RWND [byte]",
	tcp_win_ini	 => "TCP initial RWND [byte]",
	tcp_mss_used	 => "TCP negotiated MSS [byte]",
	tcp_mss_b	 => "TCP declared server MSS [byte]",
	tcp_mss_a	 => "TCP declared client MSS [byte]",
	tcp_opts_TS	 => "TCP option: Timestamp",
	tcp_opts_WS	 => "TCP option: WindowScale",
	tcp_opts_SACK	 => "TCP option: SACK",
	tcp_port_syn_dst_loc	 => "TCP destination port of SYN segments - local segments",
	tcp_port_syn_dst_out	 => "TCP destination port of SYN segments - outgoing segments",
	tcp_port_syn_dst_in	 => "TCP destination port of SYN segments - incoming segments",
	tcp_port_syn_src_loc	 => "TCP source port of SYN segments - local segments",
	tcp_port_syn_src_out	 => "TCP source port of SYN segments - outgoing segments",
	tcp_port_syn_src_in	 => "TCP source port of SYN segments - incoming segments",
	tcp_port_dst_loc	 => "TCP destination port - local segments",
	tcp_port_dst_out	 => "TCP destination port - outgoing segments",
	tcp_port_dst_in	 => "TCP destination port - incoming segments",
	tcp_port_src_loc	 => "TCP source port - local segments",
	tcp_port_src_out	 => "TCP source port - outgoing segments",
	tcp_port_src_in	 => "TCP source port - incoming segments",
	ip_tos_loc	 => "IP TOS - local packets",
	ip_tos_in	 => "IP TOS - incoming packets",
	ip_tos_out	 => "IP TOS - outgoing packets",
	ip_ttl_loc	 => "IP TTL - local packets",
	ip_ttl_in	 => "IP TTL - incoming packets",
	ip_ttl_out	 => "IP TTL - outgoing packtes",
	ip_len_loc	 => "IP packet lenght [byte] - local packets",
	ip_len_in	 => "IP packet lenght [byte] - incoming packets",
	ip_len_out	 => "IP packet lenght [byte] - outgoing packets",
	ip_protocol_loc	 => "IP protocol - local packets",
	ip_protocol_out	 => "IP protocol - outgoing packets",
	ip_protocol_in	 => "IP protocol - incoming packets",
);


#===============================================
#  description2param (reverse of the former)
#-----------------------------------------------
#
#   echo "%descrition2param = reverse %description; use Data::Dumper; print Dumper \%descrition2param; exit; " >> descr.txt
#   perl descr.txt > revers.txt
#   
# recall: $VAR1 = { .. } should be  %descrition2param = ( .. )
%descrition2param = (
          'Number of tracked TCP/UDP/RTP/RTCP flow' => 'flow_number',
          'RTP number of  out of sequence packets - incoming flows' => 'rtp_oos_p_in',
          'TCP number of FR Retransmission - server flows' => 'tcp_rtx_FR_s2c',
          'UDP destination port - outgoing packets' => 'udp_port_dst_out',
          'TCP destination port - incoming segments' => 'tcp_port_dst_in',
          'IP protocol - outgoing packets' => 'ip_protocol_out',
          'RTP percentage of  out-of-sequence packets - outgoing flows' => 'rtp_p_oos_out',
          'TCP average RWND [byte]' => 'tcp_win_avg',
          'TCP flow lenght [packet] - outgoing flows' => 'tcp_cl_p_out',
          'TCP source port - outgoing segments' => 'tcp_port_src_out',
          'TCP Early interrupted flows' => 'tcp_interrupted',
          'TCP flow RTT valid samples - outgoing flows' => 'tcp_rtt_cnt_out',
          'IP TTL - outgoing packtes' => 'ip_ttl_out',
          'RTP average delay - incoming flows' => 'rtp_avg_delay_in',
          'RTP percentage of  out-of-sequence packets local flows' => 'rtp_p_oos_loc',
          'RTP delay of reordered packets - incoming flows ' => 'rtp_reord_delay_in',
          'RTP average delay - outgoing flows' => 'rtp_avg_delay_out',
          'TCP flow lenght [byte] - coarse granularity histogram - incoming flows' => 'tcp_cl_b_l_in',
          'IP TOS - local packets' => 'ip_tos_loc',
          'TCP number of packet reordering - client flows' => 'tcp_reordering_c2s',
          'RTP number of  out of sequence packets - local flows' => 'rtp_oos_p_loc',
          'TCP destination port of SYN segments - incoming segments' => 'tcp_port_syn_dst_in',
          'RTP number of  out-of-sequence packets - local flows' => 'rtp_n_oos_loc',
          'UDP flow lenght [packet] - incoming' => 'udp_cl_p_in',
          'UDP destination port - local packets' => 'udp_port_dst_loc',
          'TCP option: WindowScale' => 'tcp_opts_WS',
          'TCP flow RTT standard deviation [ms] - outgoing flows' => 'tcp_rtt_stdev_out',
          'TCP flow average RTT [ms] - outgoing flows' => 'tcp_rtt_avg_out',
          'RTCP interarrival delay - incoming flows' => 'rtcp_avg_inter_delay_in',
          'TCP total number of anomalies - local flows' => 'tcp_anomalies_loc',
          'TCP Number of FR Retransmission - outgoing flows' => 'tcp_rtx_FR_out',
          'TCP initial RWND [byte]' => 'tcp_win_ini',
          'TCP Number of FR Retransmission - local flows' => 'tcp_rtx_FR_loc',
          'RTP average jitter - local flows' => 'rtp_avg_jitter_loc',
          'TCP number of Unneeded RTO retransmission - client flows' => 'tcp_unnecessary_rtx_RTO_c2s',
          'TCP total number of anomalies - outgoing flows' => 'tcp_anomalies_out',
          'TCP flow lenght [byte] - fine granularity histogram - outgoing flows' => 'tcp_cl_b_s_out',
          'TCP Number of RTO Retransmission - incoming flows' => 'tcp_rtx_RTO_in',
          'TCP Number of RTO Retransmission - client flows' => 'tcp_rtx_RTO_c2s',
          'TCP number of Unneeded FR retransmission - incoming flows' => 'tcp_unnecessary_rtx_FR_in',
          'TCP throughput [Kbps] - server flows' => 'tcp_thru_s2c',
          'TCP flow lenght [byte] - fine granularity histogram - local flows' => 'tcp_cl_b_s_loc',
          'UDP flow lenght [packet] - outgoing' => 'udp_cl_p_out',
          'TCP flow average RTT [ms] - server flows' => 'tcp_rtt_avg_s2c',
          'TCP number of packet reordering - outgoing flows' => 'tcp_reordering_out',
          'RTP burst lenght [packet] - outgoing flows' => 'rtp_burst_loss_out',
          'TCP number of Flow Control - local flows' => 'tcp_flow_control_loc',
          'RTP flow lifetime [ms] - local flows' => 'rtp_tot_time_loc',
          'TCP number of Unneeded FR retransmission - local flows' => 'tcp_unnecessary_rtx_FR_loc',
          'RTP prob of late packets - incoming flows ' => 'rtp_p_late_in',
          'TCP source port of SYN segments - local segments' => 'tcp_port_syn_src_loc',
          'TCP number of Network duplicates - incoming flows' => 'tcp_net_dup_in',
          'TCP declared client MSS [byte]' => 'tcp_mss_a',
          'IP TOS - incoming packets' => 'ip_tos_in',
          'TCP flow RTT standard deviation [ms] - incoming flows' => 'tcp_rtt_stdev_in',
          'RTP number of  out of sequence packets - outgoing flows' => 'rtp_oos_p_out',
          'UDP flow lifetime [ms]' => 'udp_tot_time',
          'IP packet lenght [byte] - local packets' => 'ip_len_loc',
          'RTP prob of late packets - local flows' => 'rtp_p_late_loc',
          'TCP total number of anomalies - client flows' => 'tcp_anomalies_c2s',
          'RTP prob of late packets - outgoing flows' => 'rtp_p_late_out',
          'TCP in-flight-size [byte]' => 'tcp_cwnd',
          'TCP source port - local segments' => 'tcp_port_src_loc',
          'TCP max RWND [byte]' => 'tcp_win_max',
          'TCP Number of RTO Retransmission - server flows' => 'tcp_rtx_RTO_s2c',
          'RTP prob of lost packets - local flows' => 'rtp_p_lost_loc',
          'IP TTL - incoming packets' => 'ip_ttl_in',
          'TCP source port of SYN segments - outgoing segments' => 'tcp_port_syn_src_out',
          'RTCP flow lenght [packet] - outgoing flows' => 'rtcp_cl_p_out',
          'RTP flow lifetime [ms] - incoming flows' => 'rtp_tot_time_in',
          'TCP flow RTT valid samples - local flows' => 'tcp_rtt_cnt_loc',
          'TCP flow lenght [byte] - coarse granularity histogram - server flows' => 'tcp_cl_b_l_s2c',
          'TCP Number of RTO Retransmission - outgoing flows' => 'tcp_rtx_RTO_out',
          'IP TTL - local packets' => 'ip_ttl_loc',
          'TCP number of Flow Control - incoming flows' => 'tcp_flow_control_in',
          'TCP number of Unneeded FR retransmission - outgoing flows' => 'tcp_unnecessary_rtx_FR_out',
          'RTP number of  out-of-sequence packets - incoming flows ' => 'rtp_n_oos_in',
          'RTP delay of reordered packets - outgoing flows' => 'rtp_reord_delay_out',
          'TCP destination port of SYN segments - local segments' => 'tcp_port_syn_dst_loc',
          'UDP flow lenght [byte] - incoming' => 'udp_cl_b_s_in',
          'TCP flow RTT valid samples - incoming flows' => 'tcp_rtt_cnt_in',
          'TCP flow lenght [byte] - coarse granularity histogram - local flows' => 'tcp_cl_b_l_loc',
          'TCP number of Unneeded RTO retransmission - server flows' => 'tcp_unnecessary_rtx_RTO_s2c',
          'TCP source port of SYN segments - incoming segments' => 'tcp_port_syn_src_in',
          'TCP destination port - local segments' => 'tcp_port_dst_loc',
          'TCP declared server MSS [byte]' => 'tcp_mss_b',
          'TCP flow maximum RTT [ms] - local flows' => 'tcp_rtt_max_loc',
          'TCP flow average RTT [ms] - client flows' => 'tcp_rtt_avg_c2s',
          'TCP flow lenght [byte] - coarse granularity histogram - outgoing flows' => 'tcp_cl_b_l_out',
          'TCP number of Flow Control - client flows' => 'tcp_flow_control_c2s',
          'TCP flow maximum RTT [ms] - server flows' => 'tcp_rtt_max_s2c',
          'TCP destination port of SYN segments - outgoing segments' => 'tcp_port_syn_dst_out',
          'TCP flow lenght [packet] - incoming flows' => 'tcp_cl_p_in',
          'TCP flow minimum RTT - local flows' => 'tcp_rtt_min_loc',
          'TCP number of Unneeded RTO retransmission - local flows' => 'tcp_unnecessary_rtx_RTO_loc',
          'TCP number of Flow Control - outgoing flows' => 'tcp_flow_control_out',
          'TCP flow RTT standard deviation [ms] - server flows' => 'tcp_rtt_stdev_s2c',
          'TCP flow average RTT [ms] - incoming flows' => 'tcp_rtt_avg_in',
          'TCP number of unknown anomalies - incoming flows' => 'tcp_unknown_in',
          'TCP number of Unneeded FR retransmission - client flows' => 'tcp_unnecessary_rtx_FR_c2s',
          'RTP flow lenght [packet] - outgoing flows' => 'rtp_cl_p_out',
          'TCP flow lenght [packet] - local flows' => 'tcp_cl_p_loc',
          'TCP total number of anomalies - incoming flows' => 'tcp_anomalies_in',
          'TCP option: Timestamp' => 'tcp_opts_TS',
          'RTP prob of lost packets - outgoing flows' => 'rtp_p_lost_out',
          'TCP flow lenght [packet] - clientflows' => 'tcp_cl_p_c2s',
          'RTP flow lenght [packet] - incoming flows' => 'rtp_cl_p_in',
          'TCP flow minimum RTT [ms]- incoming flows' => 'tcp_rtt_min_in',
          'UDP destination port per flow' => 'udp_port_flow_dst',
          'TCP number of Flow Control - server flows' => 'tcp_flow_control_s2c',
          'TCP flow lenght [byte] - fine granularity histogram - server flows' => 'tcp_cl_b_s_s2c',
          'UDP flow lenght [byte] - outgoing' => 'udp_cl_b_s_out',
          'TCP number of packet reordering - local flows' => 'tcp_reordering_loc',
          'TCP number of unknown anomalies - server flows' => 'tcp_unknown_s2c',
          'RTP flow lifetime [ms] - outgoing flows' => 'rtp_tot_time_out',
          'TCP flow maximum RTT [ms] - incoming flows' => 'tcp_rtt_max_in',
          'IP packet lenght [byte] - outgoing packets' => 'ip_len_out',
          'TCP flow maximum RTT [ms] - client flows' => 'tcp_rtt_max_c2s',
          'RTP prob of duplicate packets - outgoing flows' => 'rtp_p_dup_out',
          'TCP number of packet reordering - server flows' => 'tcp_reordering_s2c',
          'TCP number of unknown anomalies - outgoing flows' => 'tcp_unknown_out',
          'UDP destination post - incoming packets' => 'udp_port_dst_in',
          'TCP flow average RTT [ms] - local flows' => 'tcp_rtt_avg_loc',
          'IP protocol - incoming packets' => 'ip_protocol_in',
          'RTP average jitter - outgoing flows' => 'rtp_avg_jitter_out',
          'TCP number of packet reordering - incoming flows' => 'tcp_reordering_in',
          'IP TOS - outgoing packets' => 'ip_tos_out',
          'RTP percentage of  out-of-sequence packets - incoming flows' => 'rtp_p_oos_in',
          'RTP average jitter - incoming flows' => 'rtp_avg_jitter_in',
          'TCP flow minimum RTT [ms] - outgoing flows' => 'tcp_rtt_min_out',
          'RTP average delay - local flows' => 'rtp_avg_delay_loc',
          'RTP number of  out-of-sequence packets - outgoing flows' => 'rtp_n_oos_out',
          'TCP flow lenght [byte] - fine granularity histogram - client flows' => 'tcp_cl_b_s_c2s',
          'TCP flow lenght [packet] - server flows' => 'tcp_cl_p_s2c',
          'TCP Number of FR Retransmission - client flows' => 'tcp_rtx_FR_c2s',
          'TCP flow maximum RTT [ms] - outgoing flows' => 'tcp_rtt_max_out',
          'RTCP interarrival delay - outgoing flows' => 'rtcp_avg_inter_delay_out',
          'TCP flow RTT standard deviation [ms] - client flows' => 'tcp_rtt_stdev_c2s',
          'TCP number of Unneeded RTO retransmission - outgoing flows' => 'tcp_unnecessary_rtx_RTO_out',
          'RTP number of reordered packets - outgoing flows' => 'rtp_reord_p_n_out',
          'TCP Number of RTO Retransmission - local flows' => 'tcp_rtx_RTO_loc',
          'RTCP interarrival delay - local flows' => 'rtcp_avg_inter_delay_loc',
          'UDP flow lenght [byte] - local' => 'udp_cl_b_s_loc',
          'RTP number of reordered packets - incoming flows ' => 'rtp_reord_p_n_in',
          'TCP number of FR Retransmission - incoming flows' => 'tcp_rtx_FR_in',
          'RTCP flow lenght [packet] - incoming flows' => 'rtcp_cl_p_in',
          'TCP number of Unneeded RTO retransmission - incoming flows' => 'tcp_unnecessary_rtx_RTO_in',
          'TCP number of Network duplicates - outgoing flows' => 'tcp_net_dup_out',
          'RTP number of reordered packets - local flows' => 'rtp_reord_p_n_loc',
          'TCP throughput [Kbps] - client flows' => 'tcp_thru_c2s',
          'TCP option: SACK' => 'tcp_opts_SACK',
          'TCP number of unknown anomalies - client flows' => 'tcp_unknown_c2s',
          'TCP number of Network duplicates - client flows' => 'tcp_net_dup_c2s',
          'TCP flow lifetime [ms]' => 'tcp_tot_time',
          'TCP total number of anomalies - server flows' => 'tcp_anomalies_s2c',
          'TCP flow lenght [byte] - coarse granularity histogram - client flows' => 'tcp_cl_b_l_c2s',
          'RTP delay of reordered packets - local flows' => 'rtp_reord_delay_loc',
          'TCP flow RTT valid samples - client flows' => 'tcp_rtt_cnt_c2s',
          'TCP number of Unneeded FR retransmission - server flows' => 'tcp_unnecessary_rtx_FR_s2c',
          'RTP prob of duplicate packets - incoming flows ' => 'rtp_p_dup_in',
          'TCP flow lenght [byte] - fine granularity histogram - incoming flows' => 'tcp_cl_b_s_in',
          'RTP burst lenght [packet]- incoming flows ' => 'rtp_burst_loss_in',
          'TCP flow RTT standard deviation [ms] - local flows' => 'tcp_rtt_stdev_loc',
          'RTP prob of lost packets - incoming flows ' => 'rtp_p_lost_in',
          'TCP source port - incoming segments' => 'tcp_port_src_in',
          'RTP flow lenght [packet] - local flows' => 'rtp_cl_p_loc',
          'TCP flow RTT valid samples - server flows' => 'tcp_rtt_cnt_s2c',
          'IP protocol - local packets' => 'ip_protocol_loc',
          'TCP number of unknown anomalies - local flows' => 'tcp_unknown_loc',
          'UDP flow lenght [packet] - local' => 'udp_cl_p_loc',
          'TCP flow minimum RTT [ms] - client flows' => 'tcp_rtt_min_c2s',
          'TCP flow minimum RTT [ms] - server flows' => 'tcp_rtt_min_s2c',
          'IP packet lenght [byte] - incoming packets' => 'ip_len_in',
          'RTP prob of duplicate packets - local flows' => 'rtp_p_dup_loc',
          'TCP number of Network duplicates - server flows' => 'tcp_net_dup_s2c',
          'RTCP flow lenght [packet] - local flows' => 'rtcp_cl_p_loc',
          'TCP negotiated MSS [byte]' => 'tcp_mss_used',
          'RTP burst lenght [packet] - local flows' => 'rtp_burst_loss_loc',
          'TCP destination port - outgoing segments' => 'tcp_port_dst_out'
        );


#===============================================
#  idx2value
#-----------------------------------------------
#  human readable description for tstat index values
#  this one is hand-written
#
$idx2value = {
   ip_len => {
   	40 => "40 Bytes", 
	1500 => "1500 Bytes" 
   },
   flow_number  => {
   	0 => "TCP Flows", 
	1 => "UDP Flows",
	2 => "RTP Flows",
	3 => "RTCP Flows" 
   },
   ip_protocol => {
   	1  => "ICMP", 
	6  =>"TCP", 
	17 =>"UDP"
   }, 
   udp_port_dst => {   	
	53    =>"DNS",      
	67    =>"BOOTPS",      
	68    =>"BOOTPC",	      
	69    =>"TFTP",
	123   =>"NTP",
	137   =>"NETBIOS",
	4672  =>"eDonkey",
	6346  =>"Gnutella-svc",
	6667  =>"Ircd",
   },
   tcp_port_dst => {   	
	20   =>"FTP-DATA",	
	21   =>"FTP",	      
	22   =>"SSH",	      
	23   =>"telnet",	
	25   =>"SMTP",        
	80   =>"HTTP",        
	110  =>"POP3",
	119  =>"NNTP",
	143  =>"IMAP",
	443  =>"HTTPS", 	
	445  =>"Microsoft-ds",  
	1214 =>"KaZaa", 	
	1433 =>"Ms-SQL",
	4662 =>"eDonkey-DATA",  
	4661 =>"eDonkey-Lookup",
	6667 =>"Ircd",
	6881 =>"BitTorrent",	
	6699 =>"WinMX", 	
	8080 =>"Squid"
   },
   tcp_interrupted => { 
   	0 => 'Completed Flow',
	1 => 'Early Interrupted Flow',
   },
   tcp_opts_SACK => { 
   	1 => 'SACK Ok', 
	2 => 'SACK Client Offer', 
	3 => 'SACK Server Offer', 
	4 => 'No SACK',
	},
   tcp_opts_WS => { 
      	1 => 'Window Scale Ok', 
	2 => 'Window Scale Client Offer', 
	3 => 'Window Scale Server Offer', 
	4 => 'No Window Scale',
	},
   tcp_opts_TS => { 
	1 => 'Timestamp Ok', 
	2 => 'Timestamp Client Offer', 
	3 => 'Timestamp Server Offer', 
	4 => 'No Timestamp',
   },
   tcp_anomalies => {
	0=> "In Sequence",
	1=> "Retr. by RTO",
	2=> "Retr. by Fast Retransmit",
	3=> "Network Reordering",
	4=> "Network Duplicate",
	5=> "Flow Control (Window Probing)",
	6=> "Unnecessary Retr. by RTO",
	7=> "Unnecessary Retr. by Fast Retransmit",
	63=>"Unknown",
   },
   ip_tos => {
       0=> "Normal Service",
       2=> "Minimize Cost",
       4=> "Maximize Reliability",
       8=> "Maximize Throughput",
       16=> "Minimize Delay",
   },
};  

#--- append _in and _out and _loc ---
map { 
  $idx2value->{"${_}_loc"} = $idx2value->{"${_}_out"} = $idx2value->{"${_}_in"} = $idx2value->{$_} 
} keys %{$idx2value};

# ---Check---
#	use Data::Dumper;
#	print Dumper( \$idx2value );
#	print $idx2value->{tcp_anomalies_out}{0};
#	exit;



main();
