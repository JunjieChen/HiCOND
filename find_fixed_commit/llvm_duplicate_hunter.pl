#!/usr/bin/perl -w
#################################################################

use strict; 
use warnings;
use Text::Trim qw(trim);
use File::stat;
use Time::HiRes qw( time );
use File::Find::Rule;
use File::Basename qw(basename);
use Data::Dumper;
use List::MoreUtils qw{ any };
use List::MoreUtils qw(firstidx);
use Scalar::Util qw(looks_like_number);

#################################################################
#################### user-configurable stuff ####################

# programs shorter than this many bytes are too boring to test
my $MIN_PROGRAM_SIZE = 100000;

# kill Csmith after this many seconds
my $CSMITH_TIMEOUT = 90; 

# kill a compiler after this many seconds
my $COMPILER_TIMEOUT = 60;

# kill a compiler's output after this many seconds
my $PROG_TIMEOUT = 120;

# extra options here
#my $CSMITH_USER_OPTIONS = " --bitfields --packed-struct"; 
my $CSMITH_USER_OPTIONS = " ";


################# end user-configurable stuff ###################
#################################################################

my $RUN_PROGRAM = 1;

################# start user-configuration ###################
my $CSMITH_HOME = $ENV{"CSMITH_HOME"}; 
my $WORK_HOME = $ENV{WORK_HOME}; 
my $USED_GCC = "$ENV{USED_GCC}";
my $HEADER_SELF = "";
our $llvm_commitstr = ""; # needs to be set.
our $clang_commitstr = ""; # needs to be set.

my $HEADER = "-I$CSMITH_HOME/runtime $HEADER_SELF";
my $CYGWIN_HEADER = "-I`cygpath -d ${CSMITH_HOME}/runtime`";
my $COMPILE_OPTIONS = "";
my @COMPILERS;

my @gccs = ('llvm-2.6'); # needs to be set.
my @exist_gccs;
my @fail_gccs;
our $bufdir;
################# end user-configuration ###################

sub read_value_from_file($$) {
    my ($fn, $match) = @_;
    open INF, "<$fn" or die;
    while (my $line = <INF>) {
        $line =~ s/\r?\n?$//;            # get rid of LF/CR 
        if ($line =~ /$match/) {
            close INF;
            return $1;
        }     
    }
    close INF;
    return "";
}

sub write_bug_desc_to_file($$) {
    my ($fn, $desc) = @_;
    open OUT, ">>$fn" or die "cannot write to $fn\n";
    print OUT "/* $desc */\n";
    close OUT;
}

# properly parse the return value from system()
sub runit ($$$) {
    my ($cmd, $timeout, $out) = @_; 
    my $res;
    if ($RUN_PROGRAM) {
	#$res = system "timeout $timeout $cmd > $out 2>&1";
	$res = system "timeout $timeout $cmd > $out";
    print "$cmd\n";
    print "signal code in runit:$res,$?\n";
    } else {
	$res = system "$cmd > $out 2>&1";
    }
    my $success = 0; 
    if ($? == -1) {
        print "can't execute $cmd\n";
    }
    elsif ($? & 127) {
        print "died while executing $cmd\n";
    }
    elsif ($res == -1) {
        print "can't execute $cmd\n";
    }
    #elsif ($res == 256 or $res == 64000) {
    #    return (0,-1);
    #    print "clang error $cmd\n";
    #}
    else {
        $success = 1;
    }
    my $exit_value  = $? >> 8;
    if ($exit_value == 124) {
        print "hangs while executing $cmd\n";
        $success = 0;
    }
    return ($success, $exit_value);
}

# compile a program and execute
# return code 0: normal; 
#                     1: compiler crashes; 
#                     2: compiler hangs; 
#                     3: executable crashes; 
#                     4: executable hangs
sub compile_and_run($$$$) {
    my ($compiler, $src_file, $exe, $out) = @_; 
    my $command = "$compiler $src_file $COMPILE_OPTIONS $HEADER -o $exe";  

    my @a = split(" ", $compiler);
    # special treatment of MS compiler: convert header path to unix-style
    if ($a[0] =~ /cl$/) {
        $command = "$compiler $src_file $COMPILE_OPTIONS $CYGWIN_HEADER -o $exe"; 
    }  

    # compile random program
    my ($res, $exit_value) = runit($command, $COMPILER_TIMEOUT,  "compiler.out"); 
    # print "after run compiler: $res, $exit_value\n";
    if (($res == 0) || (!(-e $exe))) {
        # exit code 124 means time out
        return ($exit_value == 124 ? 2 : 1);         
    }

    # run random program 
    if ($RUN_PROGRAM) {
        ($res, $exit_value) = runit("./$exe", $PROG_TIMEOUT, $out);
        # print "after run program: $res, $exit_value\n";
        if (($res == 0) || (!(-e $out))) {
            # exit code 124 means time out
            return ($exit_value == 124 ? 4 : 3);      
        }
    }
    return 0;
}

# evaluate a random program
# return code:  -2: crashes (a likely wrong-code bug)
#                        -1: hangs (not interesting)
#                        0: normal, but found no compiler error (not interesting)
#                        1: found compiler crash error(s)
#                        2: found compiler wrong code error(s) 
sub evaluate_program ($) {
    my ($test_file) = @_; 
    my @checksums;
    my @tested_compilers; 
    my $interesting = 0;
    my $i = 0;     
    foreach my $compiler (@COMPILERS) { 
        my $out = "out$i.log";
        my $exe = "a.out$i";
        $i++; 
        my $res = compile_and_run($compiler, $test_file, $exe, $out);
        print "signal code in compile_and_run: $res for $exe\n";

        if ($res) {
	    if ($res == 1 || $res == 2) { 
		write_bug_desc_to_file($test_file, 
		  "Compiler error! Can't compile with $compiler $COMPILE_OPTIONS $HEADER"); 
		$interesting = 1;
            }
            elsif ($res == 3) { 
		write_bug_desc_to_file($test_file, "random program crashed!"); 
		# random program crashes, a likely wrong-code bug, but
		# can't rule out the probablity of a Csmith bug
		$interesting = -2;     
                last;
	    } else {
		print "random program hangs!\n";  
                # program hangs, not interesting
		$interesting = -1;    
                last;
            }
        }
        else {
            if ($RUN_PROGRAM) {
                die "cannot find $out.\n" if (!(-e $out));
                my $sum = read_value_from_file($out, "checksum = (.*)");
                $interesting = 2 if 
		    (scalar(@checksums) > 0 && $sum ne $checksums[0]); 
                push @checksums, $sum;
                push @tested_compilers, "$compiler $COMPILE_OPTIONS";
            }             
        }
    } 
    if ($interesting >= 1) {
        if ($interesting == 2) { 
            write_bug_desc_to_file ($test_file, 
				    "Found checksum difference between compiler implementations"); 
            for (my $i=0; $i < scalar (@checksums); $i++) {
                write_bug_desc_to_file ($test_file, 
		  "$tested_compilers[$i]: $checksums[$i]");
            }
        }
        write_bug_desc_to_file($test_file, 
	  "please refer to http://embed.cs.utah.edu/csmith/using.html on how to report a bug");
    }
    system "rm -f out*.log a.out* test*.obj compiler.out csmith.out";
    return $interesting;
}

# 2 arguments: test file and test revision, respectively.
sub test_one ($$$$) {
    my ($cfile,$rev_llvm,$rev_clang,$testbranch) = @_;
    print "testing $cfile on llvm $rev_llvm and clang $rev_clang in branch $testbranch ......\n";
    @fail_gccs = getfailgccs();
    my $dirname;
    if ($rev_clang ne "") {
        $dirname = join "-", $rev_llvm,$rev_clang;
    } else {
        $dirname = $rev_llvm;
    }
    if (any {$_ eq $dirname} @fail_gccs) {
        print "test revision $dirname is a fail llvm revision, continue.\n";
        return -1;
    }
    genCOMPILERS($rev_llvm,$rev_clang,$testbranch)==0 or return -1;
    my $seed;
    my $filesize;
    my $good_ = -1;

    my $cmd = "cp $cfile $main::bufdir";
    system($cmd);
    
    my @field_cfile = split /\//, $cfile;
    $cfile = $main::bufdir . $field_cfile[-1];
    # test if the random program is interesting
    chdir($main::bufdir) or return -1;
    my $ret = evaluate_program($cfile); 
    print "signal code in evaluate_program: $ret\n";
    chdir("$WORK_HOME/source") or return -1;
    if ($ret >= 0) {
        $good_ = 0;
        if ($ret == 1) {
            $good_ = 1;
        }
        if ($ret == 2 || $ret == -2) {
            $good_ = 1;
        } 
    }
    unlink $cfile;
    return $good_;
}

sub usage () {
    print "usage: compiler_test.pl <test_case_count>(0 for unlimited) <config-file>\n";
    exit -1;
}

sub get_passversion_branchname($) {
    my ($gcc_version) = @_;
    my $firstsign = substr($gcc_version,5,1);
    my $secondsign = substr($gcc_version,7,1);
    return "release_$firstsign$secondsign";
}

sub getexistgccs() {
    my @exist;
    my $path = $ENV{'LLVM_INSTALL_PATH'};
    opendir( my $DIR, $path );
    while ( my $entry = readdir $DIR ) {
        next unless -d $path . '/' . $entry;
        next if $entry eq '.' or $entry eq '..';
        push @exist,$entry;
    }
    closedir $DIR;
    return @exist;
}

sub getfailgccs() {
    my @fail;
    my $path = $ENV{'LLVM_HOME'};
    opendir( my $DIR, $path );
    while ( my $entry = readdir $DIR ) {
        next unless -d $path . '/' . $entry;
        next if $entry eq '.' or $entry eq '..';
        push @fail,$entry;
        my $lastchar = substr $entry,-1;
        if ($lastchar eq "/") {
            system("rm -rf $path/$entry*");
        } else {
            system("rm -rf $path/$entry/*");
        }
    }
    closedir $DIR;
    return @fail;
}

sub installRevision($$$) {
	my ($rev_llvm,$rev_clang,$testbranch) = @_;
    my $dirname = join "-",$rev_llvm,$rev_clang;
	my $srchome = "$ENV{'LLVM_HOME'}/$dirname";
    my $installhome = "$ENV{'LLVM_INSTALL_PATH'}/$dirname";	
    my $srcdirname = "$dirname" . "_src";
    my $cmd2mkdir = "mkdir -p $srchome/build";
    print "Downloading revision $dirname in branch $testbranch ......\n";
	my $cmd2downloadllvm = "svn checkout -r $rev_llvm https://llvm.org/svn/llvm-project/llvm/branches/$testbranch $srcdirname 2>&1 1>/dev/null";
	my $cmd2downloadcfe = "svn checkout -r $rev_clang https://llvm.org/svn/llvm-project/cfe/branches/$testbranch clang 2>&1 1>/dev/null";
    my $cmd2config = "cmake -G Ninja -DCMAKE_EXPORT_COMPILER_COMMANDS=ON -DCMAKE_INSTALL_PREFIX=$installhome -DCMAKE_C_COMPILER=$USED_GCC/bin/gcc -DCMAKE_CXX_COMPILER=$USED_GCC/bin/g++ ../$srcdirname";
	my $cmd2make_install = "ninja -j16 && ninja install";
    system($cmd2mkdir)==0 or return -1;
    chdir($srchome) or return -1;
    system($cmd2downloadllvm)==0 or return -1;
    system($cmd2downloadcfe)==0 or return -1;
    system("mv clang $srcdirname/tools/")==0 or return -1;
    chdir("$srchome/build") or return -1;
    system($cmd2config)==0 or return -1;
    system($cmd2make_install)==0 or return -1;
    system("rm -rf $srchome");
    chdir("$WORK_HOME/source") or return -1;
	return 0;
}

sub installRelease($) {
    my ($rev) = @_;
    my $srchome = "$ENV{'LLVM_HOME'}/$rev";
    my $releasename = $rev;
    $releasename =~ s/llvm-//;
    $releasename =~ s/\.//g;
    $releasename = "RELEASE_" . $releasename . "/final";
    my $installhome = "$ENV{'LLVM_INSTALL_PATH'}/$rev";
    my $srcdirname = "$rev" . "_src";
    my $cmd2mkdir = "mkdir -p $srchome/build";
    print "Downloading llvm release $releasename ......\n";
	my $cmd2downloadllvm = "svn co https://llvm.org/svn/llvm-project/llvm/tags/$releasename $srcdirname 2>&1 1>/dev/null";
	my $cmd2downloadcfe = "svn co https://llvm.org/svn/llvm-project/cfe/tags/$releasename clang 2>&1 1>/dev/null";
    my $idx = firstidx {$_ eq $rev} @gccs;
    my $cmd2config;
    if ($idx > 8) {
        $cmd2config = "cmake -G Ninja -DCMAKE_EXPORT_COMPILER_COMMANDS=ON -DCMAKE_INSTALL_PREFIX=$installhome ../$srcdirname";
    } else {
        $cmd2config = "cmake -G Ninja -DCMAKE_EXPORT_COMPILER_COMMANDS=ON -DCMAKE_INSTALL_PREFIX=$installhome -DCMAKE_C_COMPILER=$USED_GCC/bin/gcc -DCMAKE_CXX_COMPILER=$USED_GCC/bin/g++ ../$srcdirname";
    }
	my $cmd2make_install = "ninja -j16 && ninja install";
    system($cmd2mkdir)==0 or return -1;
    chdir($srchome) or return -1;
    system($cmd2downloadllvm)==0 or return -1;
    system($cmd2downloadcfe)==0 or return -1;
    system("mv clang $srcdirname/tools/")==0 or return -1;
    chdir("$srchome/build") or return -1;
    system($cmd2config)==0 or return -1;
    system($cmd2make_install)==0 or return -1;
    system("rm -rf $srchome");
    chdir("$WORK_HOME/source") or return -1;
    return 0;
}

sub genCOMPILERS($$$) {
    my ($sign,$sign_clang,$testbranch) = @_;
    my $dirname;
    my $LLVM_INSTALL_PATH = $ENV{'LLVM_INSTALL_PATH'};
    if(index($sign, 'llvm') != -1) {
        $dirname = $sign;
        # need to install new gcc with specific version.
        if(-d "$LLVM_INSTALL_PATH/$dirname") {
			;
		} else {
            @exist_gccs = getexistgccs();
            if (scalar(@exist_gccs) > 500) {
               my $rev2del = $exist_gccs[-1]; 
	           my $srchome2del = "$ENV{'LLVM_HOME'}/$rev2del";
               my $installhome2del = "$LLVM_INSTALL_PATH/$rev2del";	
               system("rm -rf $srchome2del");
               system("rm -rf $installhome2del");
            }
        	installRelease($dirname)==0 or return -1;
		}
    } else {
        $dirname = join "-",$sign,$sign_clang;
        # need to install new gcc with specific revision.
        if(-d "$LLVM_INSTALL_PATH/$dirname") {
			;
		} else {
            @exist_gccs = getexistgccs();
            if (scalar(@exist_gccs) > 500) {
               my $rev2del = $exist_gccs[-1]; 
	           my $srchome2del = "$ENV{'LLVM_HOME'}/$rev2del";
               my $installhome2del = "$LLVM_INSTALL_PATH/$rev2del";	
               system("rm -rf $srchome2del");
               system("rm -rf $installhome2del");
            }
        	installRevision($sign,$sign_clang,$testbranch)==0 or return -1;
		}
    }
    my $exepath = "$ENV{'LLVM_INSTALL_PATH'}/$dirname/bin/clang";
    @COMPILERS = ("$exepath -O0", "$exepath -O1", "$exepath -O2", "$exepath -Os", "$exepath -O3");
    print "COMPILERS COMMAND PREFIX:$exepath\n";
	return 0;
}

sub findtestRegion($$) {
    my ($cfilepath,$fail_version) = @_;
    print "find region for testing $cfilepath ......\n";
    my $pass_version = -1;
    my $idx = firstidx { $_ eq $fail_version } @gccs;
    my $start = $idx + 1;
    my $testrev;
    my $last_fail_version = $fail_version;
    while($start < scalar(@gccs)) {
        $testrev = $gccs[$start];	
        print "$testrev\n";
        my $test_res = test_one($cfilepath,$testrev,"","");
        if ($test_res==0) {
            print "TEST PASSED!\n";
            $pass_version = $testrev;
			return ($last_fail_version, $pass_version);
		}
        print "TEST FAILURE. NEXT VERSION!\n";
        $last_fail_version = $testrev;
		$start = $start + 1;
	}
	return ($last_fail_version, -1);
}

# get start point and terminal point of testing.
sub getboundary($$) {
    my ($fail_v, $pass_v) = @_;
    print "getting boundary for testing from $fail_v to $pass_v ......\n";
    my @parts_v = split("-", $pass_v);
    my $vnum = $parts_v[-1]; #vnum represents "version number"
    my $testsvnbranch_pass = get_passversion_branchname($pass_v);
    #llvm
    my $cmd;
    my $logfile = "llvm_log_$testsvnbranch_pass";
    $cmd = "svn log https://llvm.org/svn/llvm-project/llvm/branches/$testsvnbranch_pass > $logfile";
    if (!(-e $logfile)) {
        print "dumping log for llvm $testsvnbranch_pass ......\n";
        system($cmd);
    }
    open my $info, $logfile or die "Could not open $logfile, $!";
    my $start_point;
    my $terminal_point;
    my $buf_point;
    my $cnt = 0;
    my $record4terminal;
    while (my $line = <$info>) {
        $cnt = $cnt + 1;
        chomp $line;
        $line = trim($line);
        if ($line eq "") {next;}
        my @parts = split(" ", $line);
        my $looklike = $parts[0];
        $looklike = substr($looklike,1,length($parts[0])-1);
        if ($cnt == 2 and looks_like_number($looklike)) {$terminal_point = $parts[0];}
        if (looks_like_number($looklike) and index($parts[0], "r") != -1) {$buf_point = $parts[0];}
        if (index($line, $main::llvm_commitstr) != -1) {
            $start_point = $buf_point;last;
        }
    }
    #clang
    my $cmd_clang;
    my $logfile_clang = "clang_log_$testsvnbranch_pass";
    $cmd_clang = "svn log https://llvm.org/svn/llvm-project/cfe/branches/$testsvnbranch_pass > $logfile_clang";
    if (!(-e $logfile_clang)) {
        print "dumping log for clang $testsvnbranch_pass ......\n";
        system($cmd_clang);
    }
    open my $info_clang, $logfile_clang or die "Could not open $logfile_clang, $!";
    my $start_point_clang;
    my $terminal_point_clang;
    my $buf_point_clang;
    my $cnt_clang = 0;
    my $record4terminal_clang;
    while (my $line = <$info_clang>) {
        $cnt_clang = $cnt_clang + 1;
        chomp $line;
        $line = trim($line);
        if ($line eq "") {next;}
        my @parts = split(" ", $line);
        my $looklike = $parts[0];
        $looklike = substr($looklike,1,length($parts[0])-1);
        if ($cnt_clang == 2 and looks_like_number($looklike)) {$terminal_point_clang = $parts[0];}
        if (looks_like_number($looklike) and index($parts[0], "r") != -1) {$buf_point_clang = $parts[0];}
        if (index($line, $main::clang_commitstr) != -1) {
            $start_point_clang = $buf_point_clang;last;
        }
    }
    return ($start_point, $terminal_point, $start_point_clang, $terminal_point_clang, $testsvnbranch_pass);
}

sub binaryfind_clang($$$$$) {
    my ($cfilepath,$rev_llvm,$start_rev_clang,$end_rev_clang,$testbranch) = @_;
    print "binary finding for llvm $rev_llvm, from clang $start_rev_clang to clang $end_rev_clang in branch $testbranch ......\n";
    # get all revisions to be tested
    #my $gcc_svnbase = $ENV{'LLVM_SVNBASE'};
    #chdir($gcc_svnbase);
    my @revs2test;
    my $cmd = "svn log -r $start_rev_clang:$end_rev_clang -v https://llvm.org/svn/llvm-project/cfe/branches/$testbranch| grep -o ^r[0-9][0-9]*";
    print "$cmd\n";
    open(EXEC, '-|', $cmd) 
        or return -1;
    # Now read the output just like a file
    while(my $line = <EXEC>) {
        chomp $line;
        push @revs2test, $line;
    }
    close(EXEC);
    chdir("$WORK_HOME/source");
    my $left = 0;
    my $right = scalar(@revs2test);
    print "length of revs2test for clang is: $right\n";
    if (test_one($cfilepath,$rev_llvm,$revs2test[0],$testbranch)==0) {
        print "The first clang revision TEST PASSED!\n";
        return $revs2test[0];
    }
    my $mid = int(($left + $right)/2);
    my $find_revision = -1;
    while($left < $right) {
        print "left is: clang $left\nmid is: clang $mid\nright is: clang $right\n";
        my $test_res = test_one($cfilepath,$rev_llvm,$revs2test[$mid],$testbranch);
        if($test_res==0) {
            print "binaryfind clang TEST PASSED!\n";
            $right = $mid - 1;
            $find_revision = $revs2test[$mid];
        } elsif($test_res==1 or $test_res == -1){
            print "binaryfind clang TEST FAILED!\n";
            $left = $mid + 1;
        }
        $mid = int(($left + $right)/2);
    }
    return $find_revision;
}

sub binaryfind($$$) {
    my ($cfilepath,$start_v,$end_v) = @_;
    my ($start_rev,$end_rev,$start_rev_clang,$end_rev_clang,$testbranch) = getboundary($start_v,$end_v);
    print "$start_v,$end_v,llvm $start_rev,llvm $end_rev,clang $start_rev_clang,clang $end_rev_clang\n";
    # get all revisions to be tested
    my @revs2test;
    my $cmd = "svn log -r $start_rev:$end_rev -v https://llvm.org/svn/llvm-project/llvm/branches/$testbranch| grep -o ^r[0-9][0-9]*";
    print "$cmd\n";
    open(EXEC, '-|', $cmd) 
        or return -1;
    # Now read the output just like a file
    while(my $line = <EXEC>) {
        chomp $line;
        push @revs2test, $line;
    }
    close(EXEC);
    chdir("$WORK_HOME/source");
    my $left = 0;
    my $right = scalar(@revs2test);
    print "length of llvm's revs2test is: $right\n";
    my $findclang = binaryfind_clang($cfilepath,$revs2test[0],$start_rev_clang,$end_rev_clang,$testbranch);
    if ($findclang!=-1) {
        print "The first llvm revision TEST PASSED!\n";
        return ($revs2test[0],$findclang);
    }
    print "llvm revs2test[-1] is: $revs2test[-1]\n";
    $findclang = binaryfind_clang($cfilepath,$revs2test[-1],$start_rev_clang,$end_rev_clang,$testbranch);
    if ($findclang==-1) {
        print "llvm last revision TEST FAILED!\n";
        return -1;
    }
    print "llvm last revision TEST PASSED!\nStart binary finding ......\n";
    my $mid = int(($left + $right)/2);
    my $find_revision = -1;
    my $find_revision_clang = -1;
    while($left < $right) {
        print "left is: $left\nmid is: $mid\nright is: $right\n";
        my $test_res = binaryfind_clang($cfilepath,$revs2test[$mid],$start_rev_clang,$end_rev_clang,$testbranch);
        if($test_res!=-1) {
            print "TEST PASSED!\n";
            $right = $mid - 1;
            $find_revision = $revs2test[$mid];
            $find_revision_clang = $test_res;
        } elsif($test_res == -1){
            print "TEST FAILED!\n";
            $left = $mid + 1;
        }
        $mid = int(($left + $right)/2);
    }
    return ($find_revision,$find_revision_clang);
}

########################### main ##################################

my $nargs = scalar(@ARGV);
my $dataname = $ARGV[0];
my $fail_version = $ARGV[1];

$bufdir = "$WORK_HOME/" . $dataname . "_buf/";
system("mkdir $bufdir");

# @COMPILERS needs to be assigned.
# MAIN LOOP
@exist_gccs = getexistgccs();
my $path = "$WORK_HOME/data/$dataname";
my @full_pathes = File::Find::Rule->file->name('train*.c')->in($path);

my @existcfile;
if (-e $dataname) {
    open my $fpdata, $dataname or die "Could not open $dataname, $!";
    while (my $line = <$fpdata>) {
        chomp $line;
        $line = trim($line);
        my @spline = split(",",$line);
        push @existcfile,$spline[0];
    }
    foreach(@existcfile) {
        print $_;
    }
    close $fpdata or die $!;
}

open my $fh, '>>', $dataname or die $!;
foreach(@full_pathes) {
    print "=========================================================================\n";
    my $output;
    my $testcrash = $_;
    print "$testcrash\n";
    if (any {$_ eq $testcrash} @existcfile) {next;}
    my ($s, $e) = findtestRegion($testcrash,$fail_version);
    my $idx_end = firstidx {$_ eq $e} @gccs;
    if ($idx_end > 8) {
        $HEADER = "-I$CSMITH_HOME/runtime";
    }
    my $pass_version_llvm="not assign";
    my $pass_version_clang="not assign";
    if($e != -1){
        ($pass_version_llvm,$pass_version_clang) = binaryfind($testcrash,$s,$e);
        print "find: $pass_version_llvm,$pass_version_clang\n";
    }
    $output = "$testcrash,$s,$e:$pass_version_llvm,$pass_version_clang\n";
    print $fh $output;
    print "=========================================================================\n";
}
close $fh or die $!;



#################################################################
