# -*- perl -*-
#
###############################################################################
#
#     Title : MyLOG.pm  -- package for logging messages.
#    Author : Zaihua Ji,  zji@ucar.edu
#      Date : 06/24/2004
#   Purpose : perl library module to log message and also do other things
#             according to the value of $logact, like display the error
#             message on screen and exit script
#
# Test File : $DSSHOME/lib/perl/MyLOG_test.pm
# Work File : $DSSHOME/lib/perl/MyLOG.pm
#  SVN File : $HeadURL: https://subversion.ucar.edu/svndss/zji/perl/lib/MyLOG.pm $
#             $Id: MyLOG.pm 8280 2015-06-26 16:17:29Z zji $
# 
###############################################################################
package MyLOG;

require Exporter;
use Sys::Hostname;
use File::Basename;
use strict;

our @ISA    = qw(Exporter);
our @EXPORT = qw(send_customized_email send_email set_email get_email log_email
                 mylog mydbg myrec mytrim get_country get_hpss_command
                 show_usage check_hosts get_host get_short_host
                 get_local_command get_remote_command get_sync_command
                 current_datetime cmdlog %MYLOG $MYATTR %WTYPE %MTYPE
                 SUCCESS FINISH FAILURE MSGLOG WARNLG EXITLG LOGWRN LOGEXT
                 WRNEXT LGWNEX LGWNEM LWEMEX EMLLOG ERRLOG LOGERR DOSUDO
                 LGEREX LGEREM DOLOCK ENDLCK AUTOID DODFLT SNDEML RETMSG FRCLOG
                 MISLOG SEPLIN BRKLIN EMLTOP EMLSUM EMEROL EMLALL NOTLOG
                 mysystem tosystem mytar join_paths valid_command add_carbon_copy
                 set_suid untaint_suid untaint_string untaint_hash untaint_array
                 get_environment convert_chars escape_chars
                 break_long_string get_command set_specialist_environments
                 replace_environments current_process_info check_process_host
                 argv_to_string get_lsf_host set_lsf_host seconds_to_string_time);

# define some constants for logging actions
use constant MSGLOG => (0x0001);   # logging message
use constant WARNLG => (0x0002);   # show logging message as warning 
use constant EXITLG => (0x0004);   # exit after logging 
use constant LOGWRN => (0x0003);   # MSGLOG|WARNLG
use constant LOGEXT => (0x0005);   # MSGLOG|EXITLG
use constant WRNEXT => (0x0006);   # WARNLG|EXITLG
use constant LGWNEX => (0x0007);   # MSGLOG|WARNLG|EXITLG
use constant EMLLOG => (0x0008);   # append message to email buffer
use constant LGWNEM => (0x000B);   # MSGLOG|WARNLG|EMLLOG
use constant LWEMEX => (0x000F);   # MSGLOG|WARNLG|EMLLOG|EXITLG
use constant ERRLOG => (0x0010);   # error log only, output to STDERR
use constant LOGERR => (0x0011);   # MSGLOG|ERRLOG
use constant LGEREX => (0x0015);   # MSGLOG|ERRLOG|EXITLG
use constant LGEREM => (0x0019);   # MSGLOG|ERRLOG|EMLLOG
use constant DOLOCK => (0x0020);   # action to lock table record(s)
use constant ENDLCK => (0x0040);   # action to end locking table record(s)
use constant AUTOID => (0x0080);   # action to retrieve the last auto added id
use constant DODFLT => (0x0100);   # action to set empty values to default ones
use constant SNDEML => (0x0200);   # action to send email now
use constant RETMSG => (0x0400);   # action to return the message back
use constant FRCLOG => (0x0800);   # force logging message
use constant SEPLIN => (0x1000);   # add a separating line for email/STDOUT/STDERR
use constant BRKLIN => (0x2000);   # add a line break for email/STDOUT/STDERR
use constant EMLTOP => (0x4000);   # prepend message to email buffer
use constant RCDMSG => (0x0814);   # make sure to record logging message
use constant MISLOG => (0x0811);   # cannot access logfile
use constant EMLSUM => (0x8000);   # record as email summary
use constant EMEROL => (0x10000);   # record error as email only
use constant EMLALL => (0x1D208);   # all email acts
use constant DOSUDO => (0x20000);   # add 'sudo -u $MYLOG{RDAUSER}' 
use constant NOTLOG => (0x40000);   # do not log any thing 

use constant SUCCESS => 1;   # Successful function call
use constant FINISH  => 2;   # go through a function, including time out
use constant FAILURE => 0;   # Unsuccessful function call

our %MYLOG = (  # more defined in untaint_suid() with environment variables
   EMLADDR  => '',
   CCDADDR  => '',
   SEPLINE  => "===========================================================\n",
   TWOGBS   => 2147483648,
   MINSIZE  => 100,      # minimal file size in bytes to be valid
   LOGMASK  => (0xFFFFF), # log mask to turn off certain log action bits
   BCKGRND  => 0,        # background process flag -b
   ERRCNT   => 0,        # record number of errors for email
   ERRMSG   => '',       # record error message for email
   SUMMSG   => '',       # record summary message for email
   EMLMSG   => '',       # record detail message for email
   PRGMSG   => '',       # record progressing message for email, replaced each time
   GMTZ     => 0,        # 0 - use local time, 1 - use greenwich mean time
   NOLEAP   => 0,        # 1 - skip 29 of Feburary while add days to date
   GMTDIFF  => 6,        # gmt is 6 hours ahead of us
   CURUID   => undef,    # the login name for currecnt user id who executes the program
   SETUID   => '',       # the login name for suid if it is different to the CURUID
   FILEMODE => 664,      # default file mode
   EXECMODE => 775,      # default executable file mode or directory mode
   ARCHHOST => "hpss",   # change to hpss from mss
   ARCHROOT => "/FS/DSS", # root path for segregated tape on hpss
   BACKROOT => "/DRDATA/DSS", # backup path for desaster recovering tape on hpss
   OLDAROOT => "/DSS",   # old root path on hpss
   OLDBROOT => "/DSSBCK", # old backup tape on hpss 
   RDAUSER  => "rdadata", # common rda user name
   SUDORDA  => 0,        # 1 to allow sudo to $MYLOG{RDAUSER}
   GPFSNAME => "glade",
   LSFNAME  => "LSF",
   LSFTIME  => 864000,   # max runtime for LSF bath job, (10x24x60x60 seconds)
   MSSGRP   => undef,    # set if set to different HPSS group
   RDAGRP   => "dss",
   DSCHECK  => undef,    # carry some cached dscheck information
   HPSSLMT  => 15,       # up limit of HPSS streams 
   NOQUIT   => 0,        # do not quit if this flag is set for daemons
   TIMEOUT  => 15,       # default timeout (in seconds) for tosystem()
   SYSERR   => undef,    # cache the error message generated inside mysystem()
   ERR2STD  => undef,    # if non-empty reference to array of strings, change stderr to stdout if match
   STD2ERR  => undef,    # if non-empty reference to array of strings, change stdout to stderr if match
   MISSFILE => "No such file or directory"
);

our %WTYPE = (
   D => "DATA",
   A => "ARCHIVING",
   N => "NCAR",
   U => "UNKNOWN",
   O => "DOCUMENT",
   S => "SOFTWARE"
);

our %MTYPE = (
   P => "PRIMARY",
   A => "ARCHIVING",
   V => "VERSION",
   W => "WORKING",
   R => "ORIGINAL",
   B => "BACKUP",
   O => "OFFSITE",
   C => "CHRONOPOLIS",
   U => "UNKNOWN"
);

our %COMMANDS = ();    # caching valid command
our (@LSFHOSTS, %LSFSTATS);    # caching lsf host info

our %CPID = (
   PID => "",
   CTM => time,
   CMD => "",
   CPID => "",
);

our $MYATTR; # 1 -- database calls perl warn()/die() in case of error
$MYATTR->{PrintError} = get_environment("PrintError", 0);
$MYATTR->{RaiseError} = get_environment("RaiseError", 0);

# cache system down information
our %MYDOWN = (
   pchktime   => 0,        # previous check time
   interval   => 300,      # number of seconds each check of config file down.cnf
   curdowns   => undef,    # reference to hash of system currently down, hpss => UntilDateTime
);

# untaint info for setuid
untaint_suid();

our $VERSION = 2.00;

sub get_call_trace {
   my (@locs) = @_;

   my ($loc, $file, $sp);
   my $trace = "";

   $sp = "Called:";
   foreach $loc (@locs) {
      next if(!$loc);
      if($loc =~ /^\d+$/) {
         $trace .= "($loc)";
      } elsif(!$file || $loc ne $file) {
         $trace .= $sp . basename($loc);
         $file = $loc;
         $sp = "->";
      }
   }
   $trace .= "\n" if($trace);

   return $trace;
}

#
# $logact = 0/undef - replace
#
sub set_email {
   my ($msg, $logact) = @_;

   if($logact && $msg) {
      if($logact&EMLTOP) {
         if($MYLOG{PRGMSG}) {
            $msg = $MYLOG{PRGMSG} ."\n" . $msg;
            $MYLOG{PRGMSG} = "";
         }
         if($MYLOG{ERRCNT} == 0) {
            $msg .= "!\n" if($msg !~ /\n$/);
         } else {
            if($MYLOG{ERRCNT} == 1) {
               $msg .= " with 1 Error:\n";
            } else {
               $msg .= " with $MYLOG{ERRCNT} Errors:\n";
            }
            $msg .=  $MYLOG{ERRMSG};
            $MYLOG{ERRCNT} = 0;
            $MYLOG{ERRMSG} = "";
         }
         if($MYLOG{SUMMSG}) {
            $msg .= $MYLOG{SEPLINE};
            $msg .= "Summary:\n" if($MYLOG{EMLLOG});
            $msg .= $MYLOG{SUMMSG};
         }
         if($MYLOG{EMLMSG}) {
            $msg .= $MYLOG{SEPLINE};
            $msg .= "Detail Information:\n" if($MYLOG{SUMMSG});
         }
         $MYLOG{EMLMSG} = $msg . $MYLOG{EMLMSG};    # prepend
         $MYLOG{SUMMSG} = "";   # in case not
      } else {
         if($logact&ERRLOG) { # record error for email summary
            $MYLOG{ERRCNT}++;
            $MYLOG{ERRMSG} .= $MYLOG{ERRCNT} . ". " . $msg;
         } elsif($logact&EMLSUM) {
            if($MYLOG{SUMMSG}) {
               $MYLOG{SUMMSG} .= "\n" if($logact&BRKLIN);
               $MYLOG{SUMMSG} .= $MYLOG{SEPLINE} if($logact&SEPLIN);
            }
            $MYLOG{SUMMSG} .= $msg; # append
         }
         if($logact&EMLLOG) {
            if($MYLOG{EMLMSG}) {
               $MYLOG{EMLMSG} .= "\n" if($logact&BRKLIN);
               $MYLOG{EMLMSG} .= $MYLOG{SEPLINE} if($logact&SEPLIN);
            }
            $MYLOG{EMLMSG} .= $msg; # append
         }
      }
   } elsif(! defined $msg) {
      $MYLOG{EMLMSG} = "";
   }
}

sub get_email {
   return $MYLOG{EMLMSG};
}

#
#  send a customized email with all entries included
#
sub send_customized_email {
   my ($logmsg, $emlmsg, $logact, @locs) = @_;

   my ($entry, $key);
   my %entries = (
      fr   => ["From",    1, undef],
      to   => ["To",      1, undef],
      cc   => ["Cc",      0, undef],
      sb   => ["Subject", 1, undef]
   );

   push @locs, __FILE__;
   $logmsg = ($logmsg ? "$logmsg: " : "");
   foreach $key (keys %entries) {
      $entry = $entries{$key}[0];
      if($emlmsg !~ /$entry:\s*\n/ && $emlmsg =~ /$entry:\s*(.+)\n/) {
         $entries{$key}[2] = $1;
      } elsif($entries{$key}[1] == 1 && $logact) {
         return mylog($logmsg . "Missing Entry '$entry' for sending email",
                      $logact|ERRLOG, @locs, __LINE__);
      }
   }

   if(open OUT, "| $MYLOG{EMLSEND}") {
      print OUT $emlmsg;
      close(OUT);
      log_email($emlmsg);
      if($logact) {
         $entry = $logmsg . "Email $entries{to}[2] ";
         $entry .= "Cc'd $entries{cc}[2] " if($entries{cc}[2]);
         $entry .= "Subject: $entries{sb}[2]";   
         mylog($entry, $logact&(~EXITLG));
      }
      return SUCCESS;
   } else {
      return mylog("Error open '| $MYLOG{EMLSEND}', $!", $logact|ERRLOG, @locs, __LINE__);
   }
}

#
#  send email, if empty $msg, send $MYLOG{EMLMSG} instead
#
sub send_email {
   my ($subject, $receiver, $msg, $sender, $logact) = @_;

   my ($logmsg, $emlmsg);
   my $docc = 0;

   if(!$msg && $MYLOG{EMLMSG}) {
      $msg = $MYLOG{EMLMSG};
      $MYLOG{EMLMSG} = '';
   }
   if($msg) {
      if($sender) {
         $sender .= "\@ucar.edu" if($sender !~ /\@/);
      } else {
         $sender = "$MYLOG{CURUID}\@ucar.edu";
         $docc = 1;
      }
      if($receiver) {
         $receiver .= "\@ucar.edu" if($receiver !~ /\@/);
      } else {
         $receiver = ($MYLOG{EMLADDR} ? $MYLOG{EMLADDR} : "$MYLOG{CURUID}\@ucar.edu");
      }
      add_carbon_copy($sender, 1) if($docc && $receiver !~ /$sender/);
      $emlmsg = "From: $sender\nTo: $receiver\n";
      $logmsg = "Email $receiver";
      if($MYLOG{CCDADDR}) {
          $emlmsg .= "Cc: $MYLOG{CCDADDR}\n";
          $logmsg .= " Cc'd $MYLOG{CCDADDR}";
      }
      $emlmsg .= "Subject: " . ($subject ? $subject : ("Message from $MYLOG{HOSTNAME}-" . get_command()));
      $emlmsg .= "!\n\n$msg\n";
      $logmsg .= " in $CPID{CPID}" if($CPID{CPID});
      $logmsg .= ", Subject: $subject!" if($subject);
      $logmsg .= "\n";

      if(open MAIL, "| $MYLOG{EMLSEND}") {
         print MAIL $emlmsg;
         close(MAIL);
         log_email($emlmsg);
         mylog($logmsg, $logact&(~EXITLG)) if($logact);
         return $logmsg;
      } else {
         mylog("Error Open '| $MYLOG{EMLSEND}': $!", ERRLOG);
      }
   }
   return "";
}

#
# log email sent
#
sub log_email {
   my ($emlmsg) = @_;

   my $cmd;
   $CPID{PID} =  "$MYLOG{HOSTNAME}-" . get_command() . "-$MYLOG{CURUID}" if(!$CPID{PID});
   $cmd = $CPID{PID} . " " . break_long_string($CPID{CMD}, 40, "...", 1);
   $cmd .= "  at " . current_datetime(time) . "\n";
   if(open EML, ">> $MYLOG{LOGPATH}/$MYLOG{EMLFILE}") {
      print EML $cmd;
      print EML $emlmsg;
      close(EML);
   }
}

#
# Function: check_hosts(@hosts: array of hosts the program is OK to run) 
#
#   Return: no return, exit directly if not valid hosts
#
sub check_hosts {
   my ($progname, $msg, @hosts) = @_;

   my $ok = 0;
   my $host;

   foreach $host (@hosts) {
      if($MYLOG{HOSTNAME} eq $host) {
         $ok = 1;
         last;
      }
   }

   if(!$ok) {
      my $tmp = "\n***********************************************************\n";
      $tmp .= "** You Must Run $progname On ";
      $tmp .= join " Or ", @hosts;
      if($msg) {
         $tmp .= "\n** For $msg\n";
      }
      $tmp .= "***********************************************************\n",

      mylog($tmp, LGWNEX);
   }
}

sub current_datetime {
   my ($time) = @_;

   my @date =  (defined $time) ? localtime($time) : localtime;

   return sprintf "%02d%02d%02d%02d%02d%02d",  $date[5]%100, ($date[4] + 1),
                  $date[3],  $date[2], $date[1], $date[0];
}

#
# Function: cmdlog($cmdline)
# $cmdline - program name and all arguments
# $ctime - time (in seconds) when the command starts 
#
sub cmdlog {
   my ($cmdline, $ctime, $logact) = @_;

   my $cinfo;

   $logact = MSGLOG|FRCLOG if(!defined $logact);
   $ctime = time if(!$ctime);

   if(!$cmdline || $cmdline =~ /^(end|quit|exit|abort)/i) {
      $cmdline = ($cmdline ? ucfirst($cmdline) : "Ends");
      $cinfo = cmd_execute_time("$CPID{PID} $cmdline", ($ctime - $CPID{CTM})) . ": ";
      $cinfo .= "$CPID{CPID} <= " if($CPID{CPID});
      $cinfo .= break_long_string($CPID{CMD}, 40, "...", 1);
      mylog($cinfo, $logact) if($logact);
   } else {
      $cinfo = current_datetime($ctime);
      if($cmdline =~ /^CPID \d+/) {
         $CPID{PID} = "$MYLOG{HOSTNAME}-$MYLOG{CURUID}$cinfo";
         mylog("$CPID{PID}: $cmdline", $logact) if($logact);
         $CPID{CPID} = $cmdline;
      } elsif($CPID{PID} && $cmdline =~ /^(starts|catches) /) {
         mylog("$CPID{PID}: $cmdline at $cinfo", $logact) if($logact);
      } else {
         $CPID{PID} = "$MYLOG{HOSTNAME}-$MYLOG{CURUID}$cinfo";
         mylog("$CPID{PID}: $cmdline", $logact) if($logact);
         $CPID{CMD} = $cmdline;
      }
      $CPID{CTM} = $ctime;
   }
}

#
# Function: mylog($msg, $logact, @locs) return FAILURE if not exit
# $msg  -- message to log
# $locact -- logging actions: MSGLOG, WARNLG, ERRLOG, EXITLG, EMLLOG, & SNDEML
#
# log and display message/error and exit program according $logact value
#
sub mylog {
   my ($msg, $logact, @locs) = @_;

   my ($ctime, $cmd, $retmsg, $title);
   my $output = 0;

   $logact = MSGLOG if(!defined $logact);
   $logact &= $MYLOG{LOGMASK};  # filtering the log actions
   $logact |= MSGLOG if($logact&RCDMSG);
   $logact &= ~EXITLG if($MYLOG{NOQUIT});
   if($logact&EMEROL) {
      $logact &= ~EMLLOG if($logact&EMLLOG);
      $logact &= ~EMEROL if(!($logact&ERRLOG));
   }
   $msg =~ s/^\s+// if($msg); # remove leading whitespaces for logging message
   if($logact&EXITLG) {
      if(!$msg) {
         $msg = "Exit 1";
      } elsif($msg =~ /(\n|\r)$/) {
         $msg =~ s/$1$/; Exit 1/;
      } else {
         $msg .= "; Exit 1";
      }
   } elsif($logact&RETMSG) {
      $retmsg = $msg;
      $retmsg .= "\n" if($retmsg && $retmsg !~ /(\n|\r)$/);
   }

   $msg .= "\n" if($msg && $msg !~ /(\n|\r)$/ && !($logact&SNDEML));

   if($logact&EMLALL) {
      if(($logact&SNDEML) || !$msg) {
         $title = ($msg ? $msg : "Message from $MYLOG{HOSTNAME}-" . get_command());
         $msg = send_email($title);
      } else {
         set_email($msg, $logact) if($msg);
      }
   }
   return ($retmsg ? $retmsg : FAILURE) if(!$msg);

   if($logact&EXITLG && ($MYLOG{EMLMSG} || $MYLOG{SUMMSG} || $MYLOG{ERRMSG} || $MYLOG{PRGMSG})) {
      set_email($msg, $logact) if(!($logact&EMLALL)); 
      $title = "ABORTS $MYLOG{HOSTNAME}-" . get_command();
      set_email(($CPID{PID} ? ("ABORTS " . $CPID{PID}) : $title), EMLTOP);
      $msg .= send_email($title);
   }
   $msg .= get_call_trace(@locs) if(@locs);

   if($logact&LOGERR) { # make sure error is always logged
      $msg = break_long_string($msg);
      if($logact&(ERRLOG|EXITLG)) {
         $ctime = time;
         $CPID{PID} =  "$MYLOG{HOSTNAME}-" . get_command() . "-$MYLOG{CURUID}" if(!$CPID{PID});
         $cmd = ($logact&EXITLG ? ($logact&ERRLOG ? "ABORTS" : "QUITS") : "ERROR") . " $CPID{PID}";
         $cmd = cmd_execute_time($cmd, ($ctime - $CPID{CTM}));
         $cmd .= " $CPID{CPID} <=" if($CPID{CPID});
         $cmd .= " " . break_long_string($CPID{CMD}, 40, "...", 1);
         $cmd .= "  at " . current_datetime($ctime) . "\n";
         $msg = $cmd. $msg;
      }
      if(!($logact&NOTLOG)) {
         if($logact&ERRLOG) {
            if(!$MYLOG{ERRFILE}) {
               $MYLOG{ERRFILE} = $MYLOG{LOGFILE};
               $MYLOG{ERRFILE} =~ s/log$/err/;
            }
            if(open ERR, ">> $MYLOG{LOGPATH}/$MYLOG{ERRFILE}") {
               print ERR $msg;
               close(ERR);
               if($logact&EXITLG && open LOG, ">> $MYLOG{LOGPATH}/$MYLOG{LOGFILE}") {
                  print LOG $cmd;
                  close(LOG);
               }
            }
         } elsif(open LOG, ">> $MYLOG{LOGPATH}/$MYLOG{LOGFILE}") {
            print LOG $msg;
            close(LOG);
         }
      }
   }

   if(!$MYLOG{BCKGRND} && $logact&(ERRLOG|WARNLG)) {
      $output = ($logact&(ERRLOG|EXITLG) ? \*STDERR : \*STDOUT);
      print $output "\n" if($logact&BRKLIN);
      print $output $MYLOG{SEPLINE} if($logact&SEPLIN);
      print $output $msg;
   }
   
   if($logact&EXITLG) {
      exit 1;
   } else {
      return ($retmsg ? $retmsg : FAILURE);
   }
}

# mydbg($level, $msg, @locs) return none
# $msg  -- message to log
# @locs -- array of file names and line numbers of function calling trace
#
# log message for degugging processes 
#
sub mydbg {
   my ($level, $msg, @locs) = @_;

   my ($dfile, @levels);

   return if(!$MYLOG{DBGLEVEL});

   if($MYLOG{DBGLEVEL} =~ /^(\d+)$/) {
      $levels[0] = 0;
      $levels[1] = $1;
   } elsif($MYLOG{DBGLEVEL} =~ /^(\d*)-(\d*)$/) {
      $levels[0] = ($1 ? $1 : 0);
      $levels[1] = ($2 ? $2 : 9999);
      @levels = ($levels[1], $levels[0]) if($levels[1] < $levels[0]);
   }
   if(!@levels || $levels[1] < $levels[0]) {
      mylog("$MYLOG{DBGLEVEL}: Invalid Debug Levels", LGEREX, @locs);
   }

   return if($level > $levels[1] || $level < $levels[0]);

   $dfile = $MYLOG{DBGPATH};
   $dfile .= "/$MYLOG{DBGFILE}" if($dfile);

   if(!$msg) {
      mylog("Append debug Info (levels $levels[0]-$levels[1]) to $dfile", WARNLG);
      $level = "$levels[0]-$levels[1]";
      $msg = "DEBUG for $CPID{PID} ";
      $msg .= "$CPID{CPID} <= " if($CPID{CPID});
      $msg .= break_long_string($CPID{CMD}, 40, "...", 1);
   }

   # logging debug info
   open DBG, ">> $dfile" or mylog("Error open '>> $dfile': $!", LGEREX, @locs);
   print DBG "$level:$msg\n";
   print DBG get_call_trace(@locs) if(@locs);
   close(DBG);
}
 
#
# function: mytrim(string line) return trimed string (no space and comments)
#
# remove comment only if $rmcmt
#
sub mytrim {
   my ($str, $rmcmt) = @_;

   if($str) {
      $str =~ s/^\s+//; # remove leading whitespaces
      $rmcmt = 1 if (!defined $rmcmt);
      if($rmcmt) {
         if($str =~ /^\#/) { # comment line
            $str = "";
         } elsif($rmcmt > 1) {
            $str =~ s/\s\s+\#(.+)$//; # remove comment and its leading whitespaces
         } else {
            $str =~ s/\s+\#(.+)$//; # remove comment and its leading whitespace
         }
      }
      $str =~ s/\s+$//; # remove trailing whitespaces
   }
   return $str;
}


#
# Function: show_usage($progname: Perl program name to get file "$progname.usg")
#
# show program usage in file "$MYLOG{PUSGDIR}/$progname.usg" on screen with unix
# system function 'pg', exit program when done.
#
sub show_usage {
   my ($progname, $opts) = @_;

   my $begin = 0;
   my $nilcnt;
   my $opt;
   my $msg;
   
   if($opts) {
      # show usage for individual option of dsarch
      foreach $opt (keys %{$opts}) {
         if($opts->{$opt}[0] == 0) {
            $msg = "Mode";
         } elsif($opts->{$opt}[0] == 1) {
            $msg = "Single-Value Information"; 
         } elsif($opts->{$opt}[0] == 2) {
            $msg = "Multi-Value Information"; 
         } else {
            $msg = "Action";
         }
         print "\nDescription of $msg Option -$opt:\n" if($msg);
         open IN, "<$MYLOG{PUSGDIR}/$progname.usg" or
            mylog("Error open $MYLOG{PUSGDIR}/$progname.usg: $!", LGWNEX);
         $nilcnt = $begin = 0;
         while(<IN>) {
            if($begin == 0) {
               if(/^  -$opt or -/) {
                  $begin = 1;
               }
            } elsif(/^\s*$/) {
               last if($nilcnt);
               $nilcnt = 1;
            } else {
               last if(/^\d[\.\s\d]/); # section title
               last if($nilcnt && /^  -\w\w or -/);
               $nilcnt = 0;
            }
            print if($begin);
         }
         close(IN);
      }
   } else {
      system("more $MYLOG{PUSGDIR}/$progname.usg");
   }
   exit;
}

#
# Function: get_country($country_code: short country code name)
#
#   Return: long country code name
#
sub get_country {
   my ($code) = @_;
   
   my %codes = (
      'br' =>  "BRAZIL",
      'com' => "UNITED.STATES",
      'net' => "UNITED.STATES",
      'gov' => "UNITED.STATES",
      'org' => "UNITED.STATES",
      'us' =>  "UNITED.STATES",
      'mil' => "UNITED.STATES",
      'uk' =>  "UNITED.KINGDOM",
      'cn' =>  "P.R.CHINA",
      'jp' =>  "JAPAN",
      'kr' =>  "SOUTH.KOREA",
      'de' =>  "GERMANY",
   );      

   return $codes{$code};      
}

#
# Function: myrec($record, $is_hash)
# $record -- reference of hash or array
#
# display array info
#
sub myrec {
   my ($record, $is_hash) = @_;
   my $key;
   my $i = 0;

   
   if($is_hash) {
      print "Hash Array:\n";
      if($record) {
         foreach $key (%{$record}) {
            print "$key => $record->{$key}\n";
            $i++;
         }
      }
   } else {
      print "Array:\n";
      if($record) {
         for(; $i < @{$record}; $i++) {
            print "$i => $record->[$i]\n";
         }
      }
   }
   print $i . "Element(s) in Array dispayed\n";
}

#
# Function: mysystem($cmd, $logact, $cmdopt)
# $cmd - unix system command
# $cmdopt - 0 - no log,
#           1 - cmd (catch and pass the previous system calls),
#           2 - log standard output,
#           4 - log error output;
#           7 - log all (cmd, and standard/error outputs),
#           8 - log command with time,
#          16 - return standard output message upon success
#          32 - log error as standard output
#          64 - force returning FAILURE if called process aborts
#         128 - tries 2 times for failed cammand before quits
#         256 - cashe standard error message
#
sub mysystem {
   my ($cmd, $logact, $cmdopt, @locs) = @_;

   my ($line, $act, $stdout, $error, $isstd);
   my ($cmdlog, $stdlog, $errlog, $last, $end, $abort);
   my ($loop, $loops);
   my $ret = SUCCESS;

   return $ret if(!$cmd);  # empty command

   $cmd = untaint_string($cmd);

   if($logact) {
      $act = ($logact&(~EXITLG));
      $act = ($act&(~ERRLOG))|WARNLG if($act&ERRLOG);
   } else {
      $act = $logact = LOGWRN; # set default log action option 
   }
   $act |= FRCLOG if($act&MSGLOG); # make sure system calls always logged
   $cmdopt = 5 if(!defined $cmdopt);   # set default command log option
   $cmdlog = ($cmdopt&1 ? $act : 0);
   ($cmdopt&8) ? cmdlog("starts '$cmd'", undef, $cmdlog) : mylog("> $cmd", $cmdlog) if($cmdlog);
   $stdlog = ($cmdopt&2) ? $act : 0;
   $stdout = ($cmdopt&16) ? "" : undef;
   $MYLOG{SYSERR} = ($cmdopt&256) ? "" : undef;
   $abort = ($cmdopt&64) ? -1 : 0;
   $error = "";
   $loops = ($cmdopt&128) ? 2 : 1;

   for($loop = 1; ; $loop++) {
      $last = time;
      open CMD, "($cmd | sed 's/^/STDOUT /') 2>&1 |"
         or return mylog("open '$cmd': $!", $logact, @locs, __FILE__, __LINE__);
   
      while($line = <CMD>) {
         if(strip_output_line(\$line)) {
            if($MYLOG{STD2ERR} && std2err($line)) {
               $ret  = FAILURE;
               $error .= $line if($cmdopt&4 || defined $MYLOG{SYSERR});
               $abort = 1 if($abort == -1 && $line =~ /^ABORTS /);
            } else {
               $ret  = SUCCESS if($ret == FAILURE && mytrim($line));
               $line = '>' . $line if($line =~ /^>\s/);
               mylog($line, $stdlog) if($stdlog);
               $stdout .= $line if(defined $stdout);
            }
         } elsif($MYLOG{ERR2STD} && err2std($line)) {
            mylog($line, $stdlog) if($stdlog);
            $stdout .= $line if(defined $stdout);
         } elsif($cmdopt&32) {
            mylog($line, $stdlog) if($stdlog);
            $stdout .= $line if(defined $stdout);
            $MYLOG{SYSERR} .= $line if(defined $MYLOG{SYSERR});
         } else {
            $ret  = FAILURE;
            $error .= $line if($cmdopt&4 || defined $MYLOG{SYSERR});
            $abort = 1 if($abort == -1 && $line =~ /^ABORTS /);
         }
      }
      close(CMD);
      $ret = FAILURE if($ret == SUCCESS && $abort == 1);
      $end = time;
      $last = $end - $last;

      if($error) {
         if($ret == FAILURE) {
            $error = "Error Execute: $cmd\n$error";
         } else {
            $error = "Error From: $cmd\n$error";
         }
         $error = "Retry " . $error if($loop > 1);
         $MYLOG{SYSERR} = $error if(defined $MYLOG{SYSERR});
         if($cmdopt&4) {
            $errlog = ($act|ERRLOG);
            $errlog |= $logact if($ret == FAILURE && $loop >= $loops);
            if(@locs) {
               mylog($error, $errlog, @locs, __FILE__, __LINE__);
            } else {
               mylog($error, $errlog);
            }
         }
      }

      if($last > 120 && $cmd !~ /(^|\/|\s)(dsarch|dsupdt|dsrqst|rdacp|rdasub)\s/) {
         $cmd = "> " . break_long_string($cmd, 60, "...", 1) . " Ends";
         cmd_execute_time($cmd, $last, $cmdlog); # more tham 5 minutes
         $cmd .= " by " .  current_datetime();
      }
      last if($ret == SUCCESS || $loop >= $loops);
      sleep(6);
   }

   return (defined $stdout ? $stdout : $ret);
}

sub err2std {
   my ($line) = @_;

   foreach (@{$MYLOG{ERR2STD}}) {
      if($line =~ /$_/) {
         return 1;
      }
   }
   return 0;
}

sub std2err {
   my ($line) = @_;

   foreach (@{$MYLOG{STD2ERR}}) {
      if($line =~ /$_/) {
         return 1;
      }
   }
   return 0;
}

#
# strip leading STDOUT and carrage return '\r', but keep ending newline '\n'
#
sub strip_output_line {
   my ($line) = @_;

   my ($stdout, @lines, $ridx);

   $stdout = ($$line =~ s/^STDOUT // ? 1 : 0);

   if($$line =~ /\r/) {
      @lines = split('\r', $$line);
      $ridx = $#lines;
      $$line = $lines[$ridx];
      $$line = $lines[$ridx - 1] . "\n" if($$line eq "\n");
   }
   return ($$line eq "\n" ? 1 : $stdout);
}

sub cmd_execute_time {
   my ($cmd, $last, $logact) = @_;

   my $msg = $cmd;

   if($last >= 60) { # show running for at least one minute
      $msg .= " within " . seconds_to_string_time($last);
   }

   if($logact) {
      return mylog($msg, $logact);
   } else {
      return $msg;
   }      
}

sub seconds_to_string_time {
   my ($seconds, $showzero) = @_;

   my ($h, $m, $s, $minutes, $hours);
   my $msg = '';

   if($seconds > 0) {
      $s = $seconds % 60;               # seconds (0-59)
      $minutes = int($seconds / 60);     # total minutes
      $m = $minutes % 60;               # minutes (0-59)
      if($minutes >= 60) {
         $hours = int($minutes / 60);   # total hours
         $h = $hours % 24;              # hours (0-23)
         if($hours >= 24) {
            $msg .= int($hours / 24) . "D";   # days
         }
         $msg .= $h . "H" if($h);
      }
      $msg .= $m . "M" if($m);
      $msg .= $s . "S" if($s);
   } if($showzero) {
      $msg = "0S";
   }

   return $msg;
}
#
#  wrap function to call mysystem() with a timeout control
#  return FAILURE if error eval or time out
#
sub tosystem {
   my ($cmd, $timeout, $logact, $cmdopt, @locs) = @_;

   my ($stdout, $error, $ret);

   $timeout = $MYLOG{TIMEOUT} if(!$timeout);  # set default timeout if missed
   eval {
     local $SIG{ALRM} = sub {die "alarm\n"};
     alarm $timeout;
     if(@locs) {
        $ret = mysystem($cmd, $logact, $cmdopt, @locs, __FILE__, __LINE__);
     } else {
        $ret = mysystem($cmd, $logact, $cmdopt);        
     }
     alarm 0;
   };

   return $ret if(!$@);

   if($@ eq "alarm\n") {
      $error = "Timeout($timeout) Execute: $cmd";
      system("rdakill -P $$");      # kill child processes in case hung
   } else {
      $error = "Timeout($timeout) Error: $cmd\n$@";
   }

   if($cmdopt) {
      if($cmdopt&32) {
         $stdout = $error;
         $error = undef;
      } elsif($cmdopt&256) {
         $MYLOG{SYSERR} .= $error;
      }
   } else {
      $cmdopt = 4;
   }
   if($error && $cmdopt&4) {
      $logact = ($logact ? ($logact|ERRLOG) : LOGERR);
      if(@locs) {
         mylog($error, $logact, @locs, __FILE__, __LINE__);
      } else {
         mylog($error, $logact);         
      }
   } elsif($stdout && $cmdopt&2) {
      $logact = ($logact ? ($logact|WARNLG) : LOGWRN);
      if(@locs) {
         mylog($stdout, $logact, @locs, __FILE__, __LINE__);
      } else {
         mylog($stdout, $logact);         
      }
   }
   if($cmdopt&16) {
      return ($stdout ? $stdout : "");
   } else {
      return FAILURE;
   }
}

#
# Function: mytar($tarfile, $file, $logact)
# $taract: 1 - force replace (default) if $file included in $tarfile already;
#          0 - do not replace;
#         -1 - check included or not, no tar action
# return SUCCESS or FAILURE
#
sub mytar {
   my ($tarfile, $file, $logact, $taract, @locs) = @_;

   my ($buf, $line, $opt, $included, $tmpfile, $cmd);

   $taract = 1 if(!defined $taract);

   return mylog("$file: Not exists to be tarred to $tarfile", $logact) if(!($taract == -1 || -f $file));

   push @locs, __FILE__;
   if(-f $tarfile) {
      $included = 0;
      $cmd = "tar -tf $tarfile $file";
      $line = mysystem($cmd, LOGWRN, 16, @locs, __LINE__);
      if($line) {
         $line = mytrim($line);
         $included = 1 if($line eq $file); # $file is included in the $tarfile already
      }
   } else {
      $included = -1; # $tarfile not exists
   }
   if($taract == -1) {
      return ($included == 1 ? SUCCESS : FAILURE); # return checking result
   } elsif($included == -1) { # $tarfile not exists yet, create a new one
      $cmd = "tar -cvf $tarfile $file"; 
      return mysystem($cmd, $logact, 5, @locs, __LINE__);
   } elsif($included == 0) { # $tarfile exists, bit $file is not included yet
      $cmd = "tar -uvf $tarfile $file"; 
      return mysystem($cmd, $logact, 5, @locs, __LINE__);
   } elsif($taract == 0) {
      return SUCCESS;   # do not replace $file included in $tarfile already
   }

   # now replace the included $file
   $tmpfile = "MyTeMp.tar";  # temporary tar file name
   $opt = "-cvf";
   $cmd = "tar -tf $tarfile";
   $buf = mysystem($cmd, $logact, 20, @locs, __LINE__);
   return FAILURE if(!$buf);
   foreach $line (split(/\n/, $buf)) {
      if($line eq $file) {
         $cmd = "tar $opt $tmpfile $file";
         return FAILURE if(!mysystem($cmd, $logact, 5, @locs, __LINE__));
      } else {
         $cmd = "tar -xvf $tarfile $line";
         return FAILURE if(!mysystem($cmd, $logact, 4, @locs, __LINE__));
         $cmd = "tar $opt $tmpfile $line";
         return FAILURE if(!mysystem($cmd, $logact, 5, @locs, __LINE__));
         $cmd = "rm -f $line";
         return FAILURE if(!mysystem($cmd, $logact, 4, @locs, __LINE__));
      }
      $opt = "-uvf";
   }
   $cmd = "mv -f $tmpfile $tarfile";
   return mysystem($cmd, $logact, 5, @locs,__LINE__);
}

#
# insert breaks, default to '\n', for every length, default to 255,
# for long string; return specified number lines if $rline given
#
sub break_long_string {
   my ($str, $limit, $break, $rline, $bchars, $minlmt) = @_;

   my ($offset, $length, $pos, $len);
   my ($retstr, $substr, $char);
   my $addbreak;

   $limit = 512 if(!$limit);   # set default line limit
   $length = $str ? length($str) : 0;
   return $str if($length <= $limit);

   $rline = 100 if(!$rline);  # default to maximum 100 lines
   $break = "\n" if(!$break);        # set default break sign
   $bchars = " &;" if(!$bchars);     # set default line break characters
   $minlmt = 20 if(!$minlmt);        # set default minimal line limit
   $addbreak = $offset = 0;
   $retstr = "";

   while($offset < $length) {
      $pos = index($str, $break, $offset);
      $len = ($pos == -1) ? ($length  - $offset) : ($pos - $offset);
      if($len == 0) {
         $offset += 1;
         $substr = $addbreak ? "" : $break;
         $addbreak = 0;
      } elsif($len <= $limit) {
         $substr = substr($str, $offset, ++$len);
         $offset += $len;
         $addbreak = 0;
      } else {
         $substr = substr($str, $offset, $limit);
         $pos = $limit;
         while(--$pos > $minlmt) {
            $char = substr($substr, $pos, 1);
            last if(index($bchars, $char) >= 0);
         }
         if($pos > $minlmt) {
            $pos++;
            $substr = substr($substr, 0, $pos);
            $offset += $pos;
         } else {
            $offset += $limit;
         }
         $addbreak = 1;
         $substr .= $break;
      }
      $retstr .= $substr;
      last if(--$rline < 1);
   }

   return $retstr;
}

#
# join two paths by remove overlapping directories
# $diff = 0: join given pathes
#         1: remove $path1 from $path2
#
sub join_paths {
   my ($path1, $path2, $diff) = @_;
   
   my (@dir1, @dir2, $i, $j, $mcnt);
   my $ret;
   
   return $path1 if(!$path2);
   return $path2 if(!$path1 || ($path2 =~ /^\// && !$diff));
   
   return $1 if($diff && $path2 =~ /^$path1\/(.*)/);

   @dir1 = split '/', $path1;
   @dir2 = split '/', $path2;
   while(@dir2 > 0 && !$dir2[0]) {
      shift @dir2;
   }
   while(@dir2 > 0 && $dir2[0] eq "..") {
      shift @dir2;
      pop @dir1;   
   }
   while(@dir2 > 0 && $dir2[0] eq ".") {
      shift @dir2;
   }
   if(@dir1 > 0 && @dir2 > 0) {
      for($mcnt = $j = 0, $i = $#dir1; $j < @dir1 && $j < @dir2; $j++) {
         if($dir1[$i] eq $dir2[$j]) {
            for($mcnt = 1; $mcnt <= $j; $mcnt++) {
               last if($dir1[$i-$mcnt] ne $dir2[$j-$mcnt]);
            }
            $mcnt = 0 if($mcnt <= $j);
            last;
         }
      }
      shift @dir2 while($mcnt-- > 0); # remove $mcnt matching directories
   }
   if($diff) {
      $ret = join '/', @dir2;
   } else {
      $ret = join '/', @dir1, @dir2;
   }
   return $ret;
}

#
# validate if a given command is accessable and executable
#
# Return SUCCESS if valid command; FAILURE if not, with error message generated in mysystem() cached in $MYLOG{SYSERR} 
#
sub valid_command {
   my ($cmd, $logact, @locs) = @_;

   push @locs, (__FILE__, __LINE__ + 1) if(@locs);
   $COMMANDS{$cmd} = mysystem("which $cmd", $logact, 256, @locs) if(!defined $COMMANDS{$cmd});

   return $COMMANDS{$cmd};
}

#
# add carbon copies to $MYLOG{CCDADDR}
#
sub add_carbon_copy {
   my($cc, $isstr, $exclude, $specialist) = @_;

   my ($email, @emails);

   if(!$cc) {
      $MYLOG{CCDADDR} = '' if(!(defined $cc || defined $isstr)); # clean carbon copy
   } else {
      @emails = $isstr ? (split(/[,\s]+/, $cc)) : @{$cc};
      foreach $email (@emails) {
         next if(!$email || $email =~ /\// || $email eq 'N');
         if($email eq "S") {
            next if(!$specialist);
            $email = $specialist;
         }
         $email .= "\@ucar.edu" if($email !~ /\@/);
         next if($exclude && index($exclude, $email) > -1);
         if($MYLOG{CCDADDR}) {
            next if(index($MYLOG{CCDADDR}, $email) > -1);  # email Cc'd already
            $MYLOG{CCDADDR} .= ", ";
         }
         $MYLOG{CCDADDR} .= $email;
      }
   }
}

#
# get the current host name
#
sub get_host {
   my ($getlsf) = @_;

   my $host;
   if($getlsf && $MYLOG{CURBID} != 0) {
      $host = $MYLOG{LSFNAME};
   } elsif($MYLOG{HOSTNAME}) {
      $host = $MYLOG{HOSTNAME};
   } else {
      $host = hostname();
   }
   return get_short_host($host);
}

sub get_short_host {
   my ($host) = @_;

   return '' if(!$host);
   return $1 if($host =~ /^([^\.]+)\./);
   return $MYLOG{HOSTNAME} if($host eq "localhost");
   return $host;
}

#
# get a live LSF host name
#
sub get_lsf_host {

   my $host;

   if(!%LSFSTATS) {
      if($MYLOG{LSFHOSTS}) {
         @LSFHOSTS = split(':', $MYLOG{LSFHOSTS});
         foreach (@LSFHOSTS) {
            $LSFSTATS{$_} = 1;
         }
      } else {
         @LSFHOSTS = ();
         %LSFSTATS = ();
      }
   }

   foreach $host (@LSFHOSTS) {
      return $host if($LSFSTATS{$host});
   }   
   return undef;
}

#
# set host status, 0 dead & 1 live, for one or all avalaible lsf hosts 
#
sub set_lsf_host {
   my ($host, $stat) = @_;
   
   if($host) {
      $LSFSTATS{$host} = $stat;
   } else {
      foreach $host (@LSFHOSTS) {
         $LSFSTATS{$host} = $stat;
      }   
   }
}

#
# return the basename of command
#
sub get_command {

   my $cmd = basename($0);
   
   if($cmd =~ /^(.+)\.pl$/) {
      return $1;
   } else {
      return untaint_string($cmd);
   }
}

#
# wrap a given command $cmd for either sudo or setuid wrapper mystart_{username}
# to run as user $asuser
#
sub get_local_command {
   my ($cmd, $asuser) = @_;

   my $cuser = $MYLOG{SETUID} ? $MYLOG{SETUID} : $MYLOG{CURUID};
   return $cmd if(!$asuser || $cuser eq $asuser);

   if($cuser eq $MYLOG{RDAUSER}) {
      return "mystart_$asuser " . $cmd if(valid_command("mystart_$asuser"));
   } elsif($MYLOG{SUDORDA} && $asuser eq $MYLOG{RDAUSER}) {
      return "sudo -u $MYLOG{RDAUSER} " . $cmd;  # sudo as user rdadata
   }
   return $cmd;
}

#
# wrap a given command $cmd for either sudo or setuid wrapper mystart_{username}
# to run as user $asuser on a given remote host
#
sub get_remote_command {
   my ($cmd, $host, $asuser) = @_;

   $cmd = "ssh $host $cmd" if($host && $host !~ /^$MYLOG{HOSTNAME}/);
   return get_local_command($cmd, $asuser);
}

#
# wrap a given hpss command $cmd with sudo either before his of after hsi
# to run as user $asuser
#
sub get_hpss_command {
   my ($cmd, $asuser, $hcmd) = @_;

   my $cuser = $MYLOG{SETUID} ? $MYLOG{SETUID} : $MYLOG{CURUID};
   
   $hcmd = 'hsi' if(!$hcmd);
   
   if($asuser && $cuser ne $asuser) {
      if($cuser eq $MYLOG{RDAUSER}) {
         return "$hcmd sudo -u $asuser " . $cmd;      # setuid wrapper as user $asuser
      } elsif($MYLOG{SUDORDA} && $asuser eq $MYLOG{RDAUSER}) {
         return "sudo -u MYLOG{RDAUSER} $hcmd " . $cmd;  # sudo as user rdadata
      }
   }
   if($cuser ne $MYLOG{RDAUSER} && $cmd =~ /^ls /) {
      return "hpss$cmd";    # use 'hpssls' instead of 'hsi ls'
   } else {
      return "$hcmd $cmd";
   }
}

#
# wrap a given sync command for given host name with/without sudo
#
sub get_sync_command {
   my ($host, $asuser) = @_;

   $host = get_short_host($host);
  
   if(!($MYLOG{SETUID} && $MYLOG{SETUID} eq $MYLOG{RDAUSER}) && 
      (!$asuser || $asuser eq $MYLOG{RDAUSER})) {
#      if(valid_command(sync$host)) {
         return "sync$host";
#      } else {
#         return "sudo -u $host-sync";  # sudo as user rdadata
#      }
   }
   return "$host-sync";
}

sub untaint_hash {
   my ($hash, $match) = @_;
   
   my $key;
   
   foreach $key (keys %{$hash}) {
      $hash->{$key} = untaint_string($hash->{$key}, $match);
   }
   return $hash;
}

sub untaint_array {
   my ($array, $match) = @_;
   
   my ($i, $cnt);
   
   $cnt = @{$array};
   for($i = 0; $i < $cnt; $i++) {
      $array->[$i] = untaint_string($array->[$i], $match);
   }
   return $array;
}

sub untaint_string {
   my ($string, $match) = @_;

   return $string if(!$string);
   
   $match = "\t-~Ç-■" if(!$match);
#   $match = "\t-~" if(!$match);

   if($string =~ /^([$match]+)$/) {
      return $1;
   } else {
      mylog("$string: cannot untaint by '$match'", LGEREX);
   }
}

#
# set suid
#
sub set_suid {
   my ($uid) = @_;

   $< = $uid if($< != $uid);
   $> = $uid if($> != $uid);
   if($uid == $MYLOG{EUID} && $uid != $MYLOG{RUID}) {
      $MYLOG{SETUID} = getpwuid($uid);
      set_specialist_environments($MYLOG{SETUID}) if($MYLOG{SETUID} ne $MYLOG{RDAUSER});
   }
}

#
# untaint for using setuid
#
sub untaint_suid {

   my ($locpath, $homepath, $shost);

   # set current real user id
   if(!$MYLOG{CURUID}) {
      $MYLOG{RUID} = $<;
      $MYLOG{EUID} = $>;
      $MYLOG{CURUID} = getpwuid($<);
      if($MYLOG{CURUID} eq $MYLOG{RDAUSER}) {
         $MYLOG{SETUID} = $MYLOG{RDAUSER};
      }
   }

   $MYLOG{NOTAROOT} = "$MYLOG{OLDAROOT}|$MYLOG{OLDBROOT}|$MYLOG{BACKROOT}";
   $MYLOG{NOTBROOT} = "$MYLOG{OLDAROOT}|$MYLOG{OLDBROOT}|$MYLOG{ARCHROOT}";
   $MYLOG{ALLROOTS} = "$MYLOG{OLDAROOT}|$MYLOG{OLDBROOT}|$MYLOG{ARCHROOT}|$MYLOG{BACKROOT}";
   $MYLOG{HOSTNAME} = get_host();
   SETMYLOG("USRHOME", "MYUSRHOME");
   SETMYLOG("DSSHOME", "MYDSSHOME");
   SETMYLOG("ADDPATH", "MYADDPATH");
   SETMYLOG("OTHPATH", "MYOTHPATH");
   SETMYLOG("HSIPATH", "MYHSIPATH");
   SETMYLOG("SQLHOME", "MYSQLHOME");
   SETMYLOG("DSGHOSTS", "MYDSGHOSTS");
   SETMYLOG("VMHOSTS", "MYVMHOSTS");
   $ENV{HOME} = $ENV{HOME} ? untaint_string($ENV{HOME}) : "$MYLOG{USRHOME}/$MYLOG{CURUID}";
   SETMYLOG("HOMEBIN", "$ENV{HOME}/bin");
   $locpath = "";
   $locpath .= ":$MYLOG{SQLHOME}/bin" if($MYLOG{SQLHOME});
   $MYLOG{CURBID} = get_environment("LSB_JOBID", 0);
   if($ENV{LSF_BINDIR} && -d $ENV{LSF_BINDIR}) {
      $locpath .= ":$MYLOG{HSIPATH}" if($MYLOG{HSIPATH} && -d $MYLOG{HSIPATH});
      $locpath .= ":" . untaint_string($ENV{LSF_BINDIR});
      $MYLOG{CURBID} = -1 if(!$MYLOG{CURBID});
      $MYLOG{SUDORDA} = 1;
      $MYLOG{LOCHOME} = "/ncar/rda/setuid";
   } else {
      $MYLOG{LOCHOME} = "/usr/local/dss";
      $locpath .= ":$MYLOG{OTHPATH}" if($MYLOG{OTHPATH});
   }
   $locpath .= ":$MYLOG{ADDPATH}" if($MYLOG{ADDPATH});
   $homepath = "$MYLOG{HOMEBIN}:$MYLOG{LOCHOME}/bin:$MYLOG{DSSHOME}/bin";
   $homepath .= "/dsg_mach:$MYLOG{DSSHOME}/bin" if($MYLOG{DSGHOSTS} && $MYLOG{DSGHOSTS} =~ /(^|:)$MYLOG{HOSTNAME}(:|\.|$)/);
   $homepath .= "/vm:$MYLOG{DSSHOME}/bin" if($MYLOG{VMHOSTS} && $MYLOG{VMHOSTS} =~ /(^|:)$MYLOG{HOSTNAME}(:|\.|$)/);
   $ENV{PATH} = "$homepath:/bin:/usr/bin:/usr/local/bin:/usr/sbin$locpath";

   $ENV{SHELL} = '/bin/sh';
   delete $ENV{IFS} if(defined $ENV{IFS});             # A ksh Internal Field Separator
   delete $ENV{CDPATH} if(defined $ENV{CDPATH});       # A ksh env variable
   delete $ENV{ENV} if(defined $ENV{ENV});             # A system's /bin/sh might be ksh
   delete $ENV{BASH_ENV} if(defined $ENV{BASH_ENV});   # A system's /bin/sh might be bash   

   # set MYLOG values with environments and defaults
   SETMYLOG("DSSDBHM", "$MYLOG{DSSHOME}/dssdb");       # dssdb home dir
   SETMYLOG("LOGPATH", "$MYLOG{DSSDBHM}/log");         # path to log file
   SETMYLOG("LOGFILE", "mydss.log");                   # log file name
   SETMYLOG("EMLFILE", "myemail.log");                 # email log file name
   SETMYLOG("ERRFILE", "");                            # error file name
   SETMYLOG("EMLSEND", "/usr/lib/sendmail -t");        # send email command
   SETMYLOG("DBGLEVEL", 0);                            # debug level
   SETMYLOG("DBGPATH", "$MYLOG{DSSDBHM}/log");         # path to debug log file
   SETMYLOG("DBGFILE", "mydss.dbg");                   # debug file name
   SETMYLOG("CNFPATH", "$MYLOG{DSSHOME}/config");      # path to configuration files
   SETMYLOG("PUSGDIR", "$MYLOG{DSSDBHM}/prog_usage");  # path to program usage files
   SETMYLOG("DSSURL",  "http://rda.ucar.edu");         # current dss web URL
   SETMYLOG("WEBSERVERS", "MYWEBSERVERS");             # webserver names for Web server
   $MYLOG{WEBHOSTS} = split_array_fields($MYLOG{WEBSERVERS}, ':');
   SETMYLOG("LOCDATA", "/data");

   # set dss web homedir
   SETMYLOG("DSSWEB",  "$MYLOG{LOCDATA}/web");
   SETMYLOG("DSWHOME", "$MYLOG{DSSWEB}/datasets");     # datast web root path
   $MYLOG{HOMEROOTS} = "$MYLOG{DSSHOME}|$MYLOG{DSWHOME}";
   SETMYLOG("DSSDATA", "MYDSSDATA");                   # dss data root path
   SETMYLOG("DSDHOME", "$MYLOG{DSSDATA}/data");        # dataset data root path
   SETMYLOG("UPDTWKP", "$MYLOG{DSSDATA}/work");        # dsupdt work root path
   SETMYLOG("TRANSFER", "$MYLOG{DSSDATA}/transfer");   # dss transfer partition
   SETMYLOG("RQSTHOME", "$MYLOG{TRANSFER}/dsrqst");    # dsrqst home
   SETMYLOG("DSAHOME",  "MYDSAHOME");                  # dataset data alternate root path
   SETMYLOG("GPFSHOST", "MYGPFSHOST");                 # empty if writable to glade
   SETMYLOG("SQLHOST",  "MYSQLHOST");                  # host name for mysql server
   SETMYLOG("LSFHOSTS", "MYLSFHOSTS");                 # host names for LSF server
   SETMYLOG("CHKHOSTS", "MYCHKHOSTS");                 # host names for dscheck daemon
   SETMYLOG("VIEWHOST", "MYVIEWHOST");                 # host name for view only mysql server
   SETMYLOG("FTPUPLD",  "$MYLOG{TRANSFER}/rossby");    # ftp upload path
   $MYLOG{GPFSROOTS} = "$MYLOG{DSDHOME}|$MYLOG{UPDTWKP}|$MYLOG{RQSTHOME}";
 
   $ENV{GRIB_DEFINITION_PATH} = "$MYLOG{DSSHOME}/ecmwf_grib_api/share/definitions" if(!$ENV{GRIB_DEFINITION_PATH});
   $ENV{GRIB_INVENTORY_MODE} = "time" if(!$ENV{GRIB_INVENTORY_MODE});
   $ENV{LD_LIBRARY_PATH} = "/usr/local/lib:/fs/local/lib:/fs/local/32/lib" if(!$ENV{LD_LIBRARY_PATH});

   # set tmp dir
   SETMYLOG("TMPPATH", "MYTMPPATH");
   $MYLOG{TMPPATH} = "/$MYLOG{HOSTNAME}/ptmp" if(!$MYLOG{TMPPATH});

   # empty diretory for HOST-sync
   $MYLOG{TMPSYNC} = "$MYLOG{DSSDBHM}/tmp/.syncdir"; 
   if($MYLOG{DSSHOME} && ! -d $MYLOG{TMPSYNC}) {
      tosystem("mkdir $MYLOG{TMPSYNC}", 0, LGWNEX, 4, __FILE__, __LINE__);
      mysystem("chmod 775 $MYLOG{TMPSYNC}", LOGWRN, 4);
   }
   umask("002");
}

#
# set MYLOG value; return a string or an array reference if $sep is not emty
#
sub SETMYLOG {
   my ($name, $value) = @_;

   $MYLOG{$name} = get_environment($name, ($value =~ /^MY\w+/ ? "" : $value));
}

sub split_array_fields {
   my ($str, $sep) = @_;

   my @tmp = split($sep, $str);
   
   return \@tmp;
}

#
# ret specialist home and default shell
#
sub set_specialist_home {
   my ($specialist) = @_;
   
   my ($line, $home, $shell);

   return if($specialist eq $MYLOG{CURUID});   # no need reset
   $ENV{MAIL} =~ s/$MYLOG{CURUID}/$specialist/ if($ENV{MAIL});
   $home = "$MYLOG{USRHOME}/$specialist";
   $shell = "tcsh";

   if(open PSWD, "grep ^$specialist: /etc/passwd|") {
      $line = <PSWD>;
      close(PSWD);
      if($line && $line =~ /:(\/.+):(\/.+)\n/) {
         $home = $1;
         $line = $2;
         $shell = $1 if($line =~ /\/(\w+)$/);
      } 
   }

   if($home ne $ENV{HOME} && -d $home) {
      $ENV{HOME} = $home;
   }
   return $shell;
}

#
#  set environments for a specified specialist
#
sub set_specialist_environments {
   my ($specialist) = @_;

   my ($checkif, $line, $missthen, $shell, $resource);

   $shell = set_specialist_home($specialist);
   $resource = "$ENV{HOME}/.tcshrc";
   $checkif = 0;     # 0 outside of if; 1 start if, 2 check envs, -1 checked already
   $missthen = 0;
   return if(!open RES, "< $resource");
   while($line = <RES>) {
      $line = mytrim($line);
      next if(!$line);
      if($checkif == 0) {
         $checkif = 1 if($line =~ /^if(\s|\()/);    # start if
      } elsif($missthen) {
         $missthen = 0;
         next if($line =~ /^then&/);   # then on next line
         $checkif = 0;                 # end of inline if
      } elsif($line =~ /^endif/) {
         $checkif = 0;                 # end of if
         next;
      } elsif($checkif == -1) {        # skip the line
         next;
      } elsif($checkif == 2 && $line =~ /^else/) {
         $checkif = -1;                # done check envs in if
         next;
      }
      if($checkif == 1) {
         if($line =~ /^else$/) {
            $checkif = 2;
            next;
         } elsif($line =~ /if\W/) {
            $checkif = 2 if($line =~ /host.*!/i && $line !~ /$MYLOG{HOSTNAME}/ ||
                            $line =~ /host.*=/i && $line =~ /$MYLOG{HOSTNAME}/);
            if($line =~ /\sthen$/) {
               next;
            } else {
               $missthen = 1;
               next if($checkif == 1);
            }
         } else {
            next;
         }
      }
      if($line =~ /^setenv\s+(.*)/) {
         one_specialist_environment($1);
      }
   }
   close(RES);

   $line = $MYLOG{HOMEBIN};
   SETMYLOG("HOMEBIN", "$ENV{HOME}/bin");
   $ENV{PATH} =~ s/^$line/$MYLOG{HOMEBIN}/ if($line && $line ne $MYLOG{HOMEBIN});
}

sub one_specialist_environment {
   my ($line) = @_;

   my ($var, $val);

   return if($line !~ /^(\w+)[=\s]+(.+)$/);
   $var = $1;
   $val = $2;
   return if($var =~ /^(PATH|SHELL|IFS|CDPATH|ENV|BASH_ENV)$/);
   $val = replace_environments($val) if($val =~ /\$/);
   $val = $2 if($val =~ /^(\"|\')(.*)(\"|\')$/);   # remove quotes
   $ENV{$var} = $val;
}

#
# get and repalce environment variables in ginve string; defaults to the values in $MYLOG
#
sub replace_environments {
   my ($str, $default, $logact) = @_;

   my ($lead, $rep, $name, $env, $pre);

   while($str =~ /(^|.)\$({*)(\w+)(}*)/) {
      $lead = $1;
      $name = $3;
      $rep = $2 . $name . $4;
      $env = get_environment($name, ($MYLOG{$name} ? $MYLOG{$name} : $default), $logact);
      $pre = ($env || $lead ne ":") ? $lead : "";
      $str =~ s/$lead\$$rep/$pre$env/;
   }
   return $str;
}

#
# validate if the current host is a valid host to process
#
sub check_process_host {
   my ($hosts, $chost, $mflag, $pinfo, $logact) = @_;

   my $error;
   my $ret = 1;

   $mflag = 'G' if(!$mflag);
   $chost = get_host(1) if(!$chost);
 
    if($mflag eq 'M') {  # exact match
      if(!$hosts || $hosts ne $chost) {
         $ret = 0;
         $error = "not matched exactly" if($pinfo);
      }
   } elsif($mflag eq 'I') {  # inclusive match
      if(!$hosts || $hosts !~ /$chost/i || index($hosts, '!') == 0) {
         $ret = 0;
         $error = "not matched inclusively" if($pinfo);
      }
   } elsif($hosts) {
      if($hosts =~ /$chost/i) {
         if(index($hosts, '!') == 0) {
            $ret = 0;
            $error = "matched exclusively" if($pinfo);
         }
      } elsif(index($hosts, '!') != 0) {
         $ret = 0;
         $error = "not matched" if($pinfo);
      }
   }

   if($error) {
      $logact = LOGERR if(!$logact);
      mylog("$pinfo: CANNOT be processed on $chost for hosthame $error", $logact);
   }

   return $ret;
}

#
# get an environment variable and untaint it
#
sub get_environment {
   my ($name, $default, $logact) = @_;

   if(defined $ENV{$name}) {
      return untaint_string($ENV{$name});
   } elsif(defined $default) {
      return $default;
   } elsif($logact) {
      mylog("$name: Environment variable is not defined", $logact);
   }
   return '';
}

#
# convert special characters
#
sub convert_chars {
   my ($name) = @_;

   my ($i, $ch, $idx, $nchrs, $ochrs, $newchrs);

   return $name if($name =~ /^[a-zA-Z0-9]+$/);  # no need convert

   $newchrs = $ochrs = '';
   for($i = 0; $i < length($name); $i++) {
      $ch = substr($name, $i, 1);
      if($ch =~ /[a-zA-Z0-9]/) {
         $newchrs .= $ch;
      } elsif($ch gt 'z' && defined $ochrs) {
         if(!$ochrs) {
            if(open CHR, "< $MYLOG{DSSHOME}/lib/ExtChrs.txt") {
               $ochrs = <CHR>;
               $nchrs = <CHR>;
               close(CHR);               
            } else {
               mylog("Error open '$MYLOG{DSSHOME}/lib/ExtChrs.txt', $!", LOGERR);
               $ochrs = undef;
               next;
            }
         }
         $idx = index($ochrs, $ch);
         $newchrs .= substr($nchrs, $idx, 1) if($idx >= 0);
      } # otherwise remove the char from the name
   } 

   if($newchrs) {
      return $newchrs;
   } else {
      return $name;
   }
}

#
# escape special characters
#
sub escape_chars {
   my ($str, $chars) = @_;

   my ($i, $ch, $nstr);

   return $str if($str =~ /^[a-zA-Z0-9]+$/);  # no need convert

   $nstr = '';
   for($i = 0; $i < length($str); $i++) {
      $ch = substr($str, $i, 1);
      if($ch !~ /[a-zA-Z0-9]/) {
         if($chars) {
            $ch = "\\" . $ch if($ch =~ /^[$chars]$/);
         } elsif($str =~ /^[\s<>]$/) {
            $ch = "\\" . $ch;
         }
      }
      $nstr .= $ch;
   }      

   return $nstr;
}

#
#  Retrieve host and process id
#
sub current_process_info {
   my ($realpid) = @_;
   
   if($realpid || $MYLOG{CURBID} < 1) {
      return ($MYLOG{HOSTNAME}, $$);
   } else {
      return ($MYLOG{LSFNAME}, $MYLOG{CURBID});
   }
}

#
# convert given @ARGV to string. quote the entries with spaces
#
sub argv_to_string {
   my ($argv, $quote, $action) = @_;

   my ($arg, $i, $argcnt);
   my $argstr = '';
   
   $argv = \@ARGV if(!$argv);
   $quote = 1 if(!defined $quote);

   foreach $arg (@{$argv}) {
      next if(!defined $arg);
      $argstr .= ' ' if($argstr);
      if($arg =~ /([<>\|\s])/) {
         if($action) {
            mylog("$arg: Cannot $action for special character '$1' in argument value", LGEREX);
         }
         if($quote) {
            if($arg =~ /\'/) {
               $arg = "\"$arg\"";
            } else {
               $arg = "'$arg'";
            }
         }
      }
      $argstr .= $arg;
   }
   return untaint_string($argstr);
}
