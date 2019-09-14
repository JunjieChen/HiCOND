import os
import datetime
import os.path
import subprocess as subp
import sys
import thread
import time,random
from random import *
import collections

start_idx = int(sys.argv[1])
end_idx = int(sys.argv[2])
work_path = str(sys.argv[3]).rstrip('/')
gcc_install_path = str(sys.argv[4]).rstrip('/')
gcc_version = str(sys.argv[5]).rstrip('/')
csmith_home = str(sys.argv[6]).rstrip('/')

if "llvm" in gcc_version:
    gcc = gcc_install_path + "/" + gcc_version.split("_")[0] + "/bin/clang"
else:
    gcc = gcc_install_path + "/" + gcc_version.split("_")[0] + "/bin/gcc"

csmith = csmith_home + '/src/csmith'
library = csmith_home + '/runtime'

os.system('mkdir ' + work_path + '/' + gcc_version)
os.system("mkdir " + work_path + '/' + gcc_version + "/tmp"+str(start_idx)+"-"+str(end_idx))
addprefix = work_path + '/' + gcc_version + "/tmp" + str(start_idx)+"-"+str(end_idx) + "/"
os.system('mkdir ' + work_path + '/' + gcc_version + '/generated_config')

def exccmd(cmd):
    p=os.popen(cmd,"r")
    rs=[]
    line=""
    while True:
         line=p.readline()
         if not line:
              break
    return rs

def arrayTomap(v_map, v_array):
    keys = v_map.keys()
    for idx in range(len(keys)):
        v_map[keys[idx]] = v_array[idx]

randBinList = lambda n: [randint(0,1) for b in range(1,n+1)]
# In random array, value 1 means the feature should be disable.
def gen_write_single(fopen_lines, fout):
    random_linenum = randBinList(24)
    random_linenum[19] = 1
    print random_linenum
    for idx in range(len(fopen_lines)):
        # only write single probabilities here.
        if idx < 24:
            str2w = fopen_lines[idx].strip()
            if random_linenum[idx] == 1:
                str2w_sp = str2w.split("=")
                str2w = str2w_sp[0] + "=0.0"
            str2w = str2w + "\n"
            fout.write(str2w)

def gen_write_g_stmt(fout):
    # rand for group probabilities.
    map_stmt = collections.OrderedDict()
    map_stmt['statement_assign_prob='] = 0
    map_stmt['statement_block_prob='] = 0
    map_stmt['statement_for_prob='] = 0
    map_stmt['statement_ifelse_prob='] = 0
    map_stmt['statement_return_prob='] = 0
    map_stmt['statement_continue_prob='] = 0
    map_stmt['statement_break_prob='] = 0
    map_stmt['statement_goto_prob='] = 0
    map_stmt['statement_arrayop_prob='] = 0

    random_stmt = randBinList(9)
    # 'statement_return_prob' shouldn't be zero.
    random_stmt[4] = 0
    array_stmt = random_stmt
    step_stmt = 100 / array_stmt.count(0)
    last_0_idx = len(array_stmt) - 1 - array_stmt[::-1].index(0)
    k = 1
    for idx in range(len(array_stmt)):
        if array_stmt[idx] == 0:
            array_stmt[idx] = step_stmt * k
            k = k + 1
    array_stmt[last_0_idx] = 100
    for idx_rev in range(len(array_stmt)):
        if array_stmt[idx_rev] == 1:
            array_stmt[idx_rev] = 0
    arrayTomap(map_stmt, array_stmt)
    str_stmt = "[statement_prob"
    for elm in map_stmt.keys():
        str_stmt = str_stmt + "," + elm + str(map_stmt[elm])
    str_stmt = str_stmt + "]\n"
    fout.write(str_stmt)

def gen_write_g_unary(fout):
    # rand for group probabilities.
    map_unary = collections.OrderedDict()
    map_unary['unary_plus_prob='] = 0
    map_unary['unary_minus_prob='] = 0
    map_unary['unary_not_prob='] = 0
    map_unary['unary_bit_not_prob='] = 0
    random_unary = randBinList(4)
    while random_unary.count(1) == 0:
        random_unary = randBinList(4)
    array_unary = random_unary
    arrayTomap(map_unary, array_unary)
    str_out = "(assign_unary_ops_prob"
    for elm in map_unary.keys():
        str_out = str_out + "," + elm + str(map_unary[elm])
    str_out = str_out + ")\n"
    fout.write(str_out)

def gen_write_g_binary(fout):
    map_binary = collections.OrderedDict()
    map_binary['binary_add_prob='] = 0
    map_binary['binary_sub_prob='] = 0
    map_binary['binary_mul_prob='] = 0
    map_binary['binary_div_prob='] = 0
    map_binary['binary_mod_prob='] = 0
    map_binary['binary_gt_prob='] = 0
    map_binary['binary_lt_prob='] = 0
    map_binary['binary_ge_prob='] = 0
    map_binary['binary_le_prob='] = 0
    map_binary['binary_eq_prob='] = 0
    map_binary['binary_ne_prob='] = 0
    map_binary['binary_and_prob='] = 0
    map_binary['binary_or_prob='] = 0
    map_binary['binary_bit_xor_prob='] = 0
    map_binary['binary_bit_and_prob='] = 0
    map_binary['binary_bit_or_prob='] = 0
    map_binary['binary_bit_rshift_prob='] = 0
    map_binary['binary_bit_lshift_prob='] = 0
    random_binary = randBinList(18)
    while random_binary.count(1) == 0:
        random_binary = randBinList(18)
    array_binary = random_binary
    arrayTomap(map_binary, array_binary)
    str_out = "(assign_binary_ops_prob"
    for elm in map_binary.keys():
        str_out = str_out + "," + elm + str(map_binary[elm])
    str_out = str_out + ")\n"
    fout.write(str_out)

def gen_write_g_simplet(fout):
    map_simplet = collections.OrderedDict()
    map_simplet['void_prob='] = 0
    map_simplet['char_prob='] = 0
    map_simplet['int_prob='] = 0
    map_simplet['short_prob='] = 0
    map_simplet['long_prob='] = 0
    map_simplet['long_long_prob='] = 0
    map_simplet['uchar_prob='] = 0
    map_simplet['uint_prob='] = 0
    map_simplet['ushort_prob='] = 0
    map_simplet['ulong_prob='] = 0
    map_simplet['ulong_long_prob='] = 0
    map_simplet['float_prob='] = 0
    random_simplet = randBinList(12)
    while random_simplet.count(1) == 0 or (random_simplet.count(1) == 1 and random_simplet[0] == 1):
        random_simplet = randBinList(12)
    array_simplet = random_simplet
    arrayTomap(map_simplet, array_simplet)
    map_simplet['void_prob='] = 0
    str_out = "(simple_types_prob"
    for elm in map_simplet.keys():
        str_out = str_out + "," + elm + str(map_simplet[elm])
    str_out = str_out + ")\n"
    fout.write(str_out)

def gen_write_g_safeop(fout):
    map_safeop = collections.OrderedDict()
    map_safeop['safe_ops_size_int8='] = 0
    map_safeop['safe_ops_size_int16='] = 0
    map_safeop['safe_ops_size_int32='] = 0
    map_safeop['safe_ops_size_int64='] = 0
    random_safeop = randBinList(4)
    while random_safeop.count(1) == 0:
        random_safeop = randBinList(4)
    array_safeop = random_safeop
    arrayTomap(map_safeop, array_safeop)
    str_out = "(safe_ops_size_prob"
    for elm in map_safeop.keys():
        str_out = str_out + "," + elm + str(map_safeop[elm])
    str_out = str_out + ")\n"
    fout.write(str_out)

def generate_swarm_config(config_idx):
    gen_conf = work_path + "/" + gcc_version + "/generated_config/config" + str(config_idx)

    fopen = open(work_path+"/default.config", "r")
    fopen_lines = fopen.readlines()
    fopen.close()
    
    fout = open(gen_conf, "w")
    gen_write_single(fopen_lines,fout)
    gen_write_g_stmt(fout)
    gen_write_g_unary(fout)
    gen_write_g_binary(fout)
    gen_write_g_simplet(fout)
    gen_write_g_safeop(fout)
    fout.close()
    return gen_conf 

os.system('export LIBRARY_PATH=/usr/lib/x86_64-linux-gnu')

crashres=work_path+'/'+gcc_version+'/crash'
wrongcoderes=work_path+'/'+gcc_version+'/wrongcode'

exccmd('mkdir '+crashres)
exccmd('mkdir '+wrongcoderes)

res=open(work_path+'/'+gcc_version+'/status'+str(start_idx)+"-"+str(end_idx)+".txt",'a')

exccmd('rm '+addprefix+'trainprogram*')
for i in range(start_idx, end_idx+1):
    config_loc = generate_swarm_config(i)
    wholestart=time.time()
    res.flush()
    start=time.time()
    hasfile = False
    filesize = 0
    while (not hasfile or not filesize):
        exccmd('timeout 30 '+csmith+' --probability-configuration '+config_loc+' -o ' + addprefix + 'trainprogram'+str(i)+'.c')
        hasfile = os.path.isfile(addprefix + 'trainprogram'+str(i)+'.c')
        filesize = os.stat(addprefix + 'trainprogram'+str(i)+'.c').st_size
    end=time.time()
    if (end-start) >= 30:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',generation,AAA,'+str(wholediff)+'\n')
        # i=i-1
        continue

    pf=open(addprefix+'trainprogram'+str(i)+'.c')
    plines=pf.readlines()
    pf.close()
    seedrec='AAA'
    for pi in range(len(plines)):
        if 'Seed:' in plines[pi]:
            seedrec=plines[pi].strip().split('Seed:')[-1].strip()
            break

    start=time.time()
    exccmd('timeout 60 '+gcc+' -O0 ' + addprefix + 'trainprogram'+str(i)+'.c -I '+library+' -o ' + addprefix + 'trainprogram'+str(i)+'_0')
    end=time.time()
    if (end-start) >= 60:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',compile,'+seedrec+','+str(wholediff)+'\n')
        # i=i-1
        continue

    start=time.time()
    exccmd('timeout 60 '+gcc+' -O1 ' + addprefix + 'trainprogram'+str(i)+'.c -I '+library+' -o ' + addprefix + 'trainprogram'+str(i)+'_1')
    end=time.time()
    if (end-start) >= 60:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',compile,'+seedrec+','+str(wholediff)+'\n')
        # i=i-1
        continue

    start=time.time()
    exccmd('timeout 60 '+gcc+' -O2 ' + addprefix + 'trainprogram'+str(i)+'.c -I '+library+' -o ' + addprefix + 'trainprogram'+str(i)+'_2')
    end=time.time()
    if (end-start) >= 60:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',compile,'+seedrec+','+str(wholediff)+'\n')
        # i=i-1
        continue

    start=time.time()
    exccmd('timeout 60 '+gcc+' -O3 ' + addprefix + 'trainprogram'+str(i)+'.c -I '+library+' -o ' + addprefix + 'trainprogram'+str(i)+'_3')
    end=time.time()
    if (end-start) >= 60:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',compile,'+seedrec+','+str(wholediff)+'\n')
        # i=i-1
        continue

    start=time.time()
    exccmd('timeout 60 '+gcc+' -Os ' + addprefix + 'trainprogram'+str(i)+'.c -I '+library+' -o ' + addprefix + 'trainprogram'+str(i)+'_s')
    end=time.time()
    if (end-start) >= 60:
        exccmd('rm '+addprefix+'trainprogram*')
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',compile,'+seedrec+','+str(wholediff)+'\n')
        # i=i-1
        continue

    if not os.path.exists(addprefix + 'trainprogram'+str(i)+'_0') or not os.path.exists(addprefix+'trainprogram'+str(i)+'_1') or not os.path.exists(addprefix+'trainprogram'+str(i)+'_2') or not os.path.exists(addprefix+'trainprogram'+str(i)+'_3') or not os.path.exists(addprefix+'trainprogram'+str(i)+'_s'):

        exccmd('mkdir '+crashres+'/trainprogram'+str(i))
        exccmd('mv '+addprefix+'trainprogram* '+crashres+'/trainprogram'+str(i))
        wholeend=time.time()
        wholediff=wholeend-wholestart
        res.write(str(i)+',crash,'+seedrec+','+str(wholediff)+'\n')

    else:
        start=time.time()
        exccmd('timeout 60 ' + addprefix+'trainprogram'+str(i)+'_0 > ' + addprefix+'trainprogram_out_0')
        cmd2print = 'timeout 60 ' + addprefix+'trainprogram'+str(i)+'_0 > ' + addprefix+'trainprogram_out_0'
        print cmd2print
        end=time.time()
        if (end-start) >= 60:
            exccmd('rm '+addprefix+'trainprogram*')
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',execute,'+seedrec+','+str(wholediff)+'\n')
            # i=i-1
            continue

        start=time.time()
        exccmd('timeout 60 ' + addprefix+'trainprogram'+str(i)+'_1 > ' +addprefix + 'trainprogram_out_1')
        cmd2print = 'timeout 60 ' + addprefix+'trainprogram'+str(i)+'_1 > ' + addprefix+'trainprogram_out_1'
        print cmd2print
        end=time.time()
        if (end-start) >= 60:
            exccmd('rm '+addprefix+'trainprogram*')
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',execute,'+seedrec+','+str(wholediff)+'\n')
            # i=i-1
            continue

        start=time.time()
        exccmd('timeout 60 ' + addprefix +'trainprogram'+str(i)+'_2 > ' + addprefix +'trainprogram_out_2')
        cmd2print = 'timeout 60 ' + addprefix+'trainprogram'+str(i)+'_2 > ' + addprefix+'trainprogram_out_2'
        print cmd2print
        end=time.time()
        if (end-start) >= 60:
            exccmd('rm '+addprefix+'trainprogram*')
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',execute,'+seedrec+','+str(wholediff)+'\n')
            # i=i-1
            continue

        start=time.time()
        exccmd('timeout 60 ' + addprefix +'trainprogram'+str(i)+'_3 > ' + addprefix +'trainprogram_out_3')
        cmd2print = 'timeout 60 ' + addprefix+'trainprogram'+str(i)+'_3 > ' + addprefix+'trainprogram_out_3'
        print cmd2print
        end=time.time()
        if (end-start) >= 60:
            exccmd('rm '+addprefix+'trainprogram*')
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',execute,'+seedrec+','+str(wholediff)+'\n')
            # i=i-1
            continue

        start=time.time()
        exccmd('timeout 60 '+addprefix+'trainprogram'+str(i)+'_s > '+addprefix+'trainprogram_out_s')
        cmd2print = 'timeout 60 ' + addprefix+'trainprogram'+str(i)+'_s > ' + addprefix+'trainprogram_out_s'
        print cmd2print
        end=time.time()
        if (end-start) >= 60:
            exccmd('rm '+addprefix+'trainprogram*')
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',execute,'+seedrec+','+str(wholediff)+'\n')
            # i=i-1
            continue

        f=open(addprefix+'trainprogram_out_0')
        lines=f.readlines()
        f.close()

        if len(lines)==0:
            exccmd('mkdir '+wrongcoderes+'/trainprogram'+str(i))
            exccmd('mv '+addprefix+'trainprogram* '+wrongcoderes+'/trainprogram'+str(i))
            wholeend=time.time()
            wholediff=wholeend-wholestart
            res.write(str(i)+',wrongcode,'+seedrec+','+str(wholediff)+'\n')
        else:
            exccmd('diff '+addprefix+'trainprogram_out_0 '+addprefix+'trainprogram_out_1 > '+addprefix+'trainprogram_diff_1')
            exccmd('diff '+addprefix+'trainprogram_out_0 '+addprefix+'trainprogram_out_2 > '+addprefix+'trainprogram_diff_2')
            exccmd('diff '+addprefix+'trainprogram_out_0 '+addprefix+'trainprogram_out_3 > '+addprefix+'trainprogram_diff_3')
            exccmd('diff '+addprefix+'trainprogram_out_0 '+addprefix+'trainprogram_out_s > '+addprefix+'trainprogram_diff_s')

            f=open(addprefix+'trainprogram_diff_1')
            lines1=f.readlines()
            f.close()

            f=open(addprefix+'trainprogram_diff_2')
            lines2=f.readlines()
            f.close()

            f=open(addprefix+'trainprogram_diff_3')
            lines3=f.readlines()
            f.close()

            f=open(addprefix+'trainprogram_diff_s')
            lines4=f.readlines()
            f.close()

            if not (len(lines1)==0 and len(lines2)==0 and len(lines3)==0 and len(lines4)==0):
                exccmd('mkdir '+wrongcoderes+'/trainprogram'+str(i))
                exccmd('mv '+addprefix+'trainprogram* '+wrongcoderes+'/trainprogram'+str(i))
                wholeend=time.time()
                wholediff=wholeend-wholestart
                res.write(str(i)+',wrongcode,'+seedrec+','+str(wholediff)+'\n')
            else:
                exccmd('rm '+addprefix+'trainprogram*')
                wholeend=time.time()
                wholediff=wholeend-wholestart
                res.write(str(i)+',correct,'+seedrec+','+str(wholediff)+'\n')

res.close()







