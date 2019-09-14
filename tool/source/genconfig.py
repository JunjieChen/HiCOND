import os
import sys
import numpy as np

idx = sys.argv[1]

def convertParticle2config(pconf,file2w):
    base_itm = []
    fp_base = open('../data/prob.txt','r')
    fp_baselines = fp_base.readlines()
    fp_base.close()
    for itm in fp_baselines:
        itm_txt = itm.strip().lstrip('[').lstrip('(').rstrip(']').rstrip(')')
        if itm_txt is '':
            continue
        txtsp = itm_txt.split(',')
        for sp in txtsp:
            base_itm.append(sp.split('=')[0])
    base_itm.remove('statement_prob')
    base_itm.remove('assign_unary_ops_prob')
    base_itm.remove('assign_binary_ops_prob')
    base_itm.remove('simple_types_prob')
    base_itm.remove('safe_ops_size_prob')
    fp_w = open(file2w,'w') 
    # write single
    for i in range(0,24):
        fp_w.write(base_itm[i]+'='+str(pconf[i])+'\n')
        fp_w.write('\n')
    # write group1
    probsum = 0
    fp_w.write('[statement_prob,')
    for i_g1 in range(24,33):
        probsum = probsum + float(pconf[i_g1])
        if i_g1 != 32:
            if i_g1 == 25:
                fp_w.write(base_itm[i_g1]+'=0'+',')
            else:
                fp_w.write(base_itm[i_g1]+'='+str(probsum)+',')
        else:
            fp_w.write(base_itm[i_g1]+'=100.0')
    fp_w.write(']\n\n')
    # write group2
    probsum = 0
    fp_w.write('[assign_unary_ops_prob,')
    for i_g2 in range(33,37):
        probsum = probsum + float(pconf[i_g2])
        if i_g2 != 36:
            fp_w.write(base_itm[i_g2]+'='+str(probsum)+',')
        else:
            fp_w.write(base_itm[i_g2]+'=100.0')
    fp_w.write(']\n\n')
    # write group3
    probsum = 0
    fp_w.write('[assign_binary_ops_prob,')
    for i_g3 in range(37,55):
        probsum = probsum + float(pconf[i_g3])
        if i_g3 != 54:
            fp_w.write(base_itm[i_g3]+'='+str(probsum)+',')
        else:
            fp_w.write(base_itm[i_g3]+'=100.0')
    fp_w.write(']\n\n')
    # write group4
    probsum = 0
    fp_w.write('[simple_types_prob,')
    for i_g4 in range(55,67):
        probsum = probsum + float(pconf[i_g4])
        if i_g4 != 66:
            if i_g4 == 55:
                fp_w.write(base_itm[i_g4]+'=0'+',')
            elif i_g4 == 65:
                fp_w.write(base_itm[i_g4]+'=100'+',')
            else:
                fp_w.write(base_itm[i_g4]+'='+str(probsum)+',')
        else:
            fp_w.write(base_itm[i_g4]+'=0')
    fp_w.write(']\n\n')
    # write group5
    probsum = 0
    fp_w.write('[safe_ops_size_prob,')
    for i_g5 in range(67,71):
        probsum = probsum + float(pconf[i_g5])
        if i_g5 != 70:
            fp_w.write(base_itm[i_g5]+'='+str(probsum)+',')
        else:
            fp_w.write(base_itm[i_g5]+'=100.0')
    fp_w.write(']\n\n')
    fp_w.close()

fileprob_prefix = "../record_iters/last_prob_iter" + str(idx)
filescore_prefix = "../record_iters/last_score_iter" + str(idx)
fileidx_prefix = "../record_iters/last_sorted-index_iter" + str(idx)

fp_idx = open(fileidx_prefix,'r')
fp_idxlines = fp_idx.readlines()
fp_idx.close()

sorted_idx = []
for itm in fp_idxlines:
    idx2add = itm.strip()
    sorted_idx.append(int(idx2add))

prob_array = np.genfromtxt(fileprob_prefix, delimiter=',')

prob = []
for idx in sorted_idx:
    prob.append(prob_array[idx])

os.system("mkdir ../configfile")
confprefix = "../configfile/config"
cnt = 0
for p in prob:
    cnt = cnt+1
    print p.shape
    convertParticle2config(p,confprefix+str(cnt))
