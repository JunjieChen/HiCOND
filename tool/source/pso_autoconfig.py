from multiprocessing import Pool
import os 
import sys
import numpy as np
import random

max_iterations = 200
cut = 2/3 # if configuration always fails to generate programs.
gen4feature_number = 500
particle_number = 15
defaultprob_filename = '../data/oriprob.txt'
trainingdataprob_filename = '../data/training_prob_calc.csv'
pstatus_filename = '../data/status_first.txt'
pass_prob_filename = '../data/probforpassing.csv'
fail_prob_filename = '../data/probforfailing440pass.csv'
prob_searchspace_filename = 'prob_searchspace.txt'
gprob_minmax_filename = 'prob_searchspace.txt'
configfile_prefix = 'particle_prob_config_t'

c = 2
pset = []
vset = np.ones((particle_number,71))
vmax = np.ones((71,))
gbest = np.zeros((5,71))
pbest = np.zeros((particle_number,71))
pbest_score = np.zeros((particle_number,))
gbest_score = np.zeros((5,))

def test_prob(prob):
    os.system('rm training_prob_t*')
    convertParticle2config(prob,'test_probconf.txt')
    prefix = '../csmith_recorder/csmith_record_2.3.0_t1'
    postfix = '/install_files/bin/csmith --probability-configuration test_probconf.txt'
    os.system('timeout 20 ' + prefix + postfix)
    if os.path.isfile('training_prob_t1.csv'):
        return True
    else:
        return False
    
def getProbfromConfig():
    prob = []
    fp_base = open(defaultprob_filename,'r')
    fp_baselines = fp_base.readlines()
    fp_base.close()
    for itm in fp_baselines:
        itm_txt = itm.strip().lstrip('[').lstrip('(').rstrip(']').rstrip(')')
        if itm_txt is '':
            continue
        txtsp = itm_txt.split(',')
        for sp in txtsp:
            p_sp = sp.split('=')
            if len(p_sp) == 1:
                continue
            p = p_sp[-1]
            prob.append(float(p))
    return np.asarray(prob)
    
def getSearchSpace(): 
    fp_d = open(defaultprob_filename,'r')
    fp_dlines = fp_d.readlines()
    fp_d.close()
    fp_p = open(pass_prob_filename,'r')
    fp_plines = fp_p.readlines()
    fp_p.close()
    fp_f = open(fail_prob_filename,'r')
    fp_flines = fp_f.readlines()
    fp_f.close()
    vald = []
    valp = []
    valf = []
    for i in range(0,99):
        if fp_dlines[i].strip() is not '':
            val = fp_dlines[i].strip().split(',')[-1]
            vald.append(float(val))
        if fp_plines[i].strip() is not '':
            val = fp_plines[i].strip().split(',')[-1]
            valp.append(float(val))
        if fp_flines[i].strip() is not '':
            val = fp_flines[i].strip().split(',')[-1]
            valf.append(float(val))
    vald = np.asarray(vald)
    valp = np.asarray(valp)
    valf = np.asarray(valf)
    newprob = vald + valf - valp 
    prob_min = np.zeros((71,))
    prob_max = np.zeros((71,))
    for j in range(0,71):
        if vald[j] < newprob[j]:
            prob_min[j] = vald[j]
            prob_max[j] = newprob[j]
        else:
            prob_max[j] = vald[j]
            prob_min[j] = newprob[j]
    prob_min[prob_min<0] = 0
    prob_max[prob_max>100] = 100
    #prob_max = np.amax(training_data_prob, axis=0)
    #prob_min = np.amin(training_data_prob, axis=0)
    prob_searchspace = np.concatenate(([prob_min],[prob_max]))
    np.savetxt(prob_searchspace_filename, prob_searchspace, fmt='%.8f', delimiter=',', newline='\n')
    exit()
    return prob_searchspace

def randGroup(minmaxarray, pos_s, pos_e):
    elm_number = minmaxarray.shape[0]
    gensize = pos_e - pos_s + 1
    rand = np.random.multinomial(100, np.ones(gensize)/gensize, size=1)[0]
    return rand 

def genprob(minmaxarray):
    while 1:
        single_elm_number = minmaxarray.shape[0] - 47
        randarray = np.zeros(single_elm_number)
        for j in range(0,single_elm_number):
            minmax = minmaxarray[j]
            randarray[j] = random.uniform(minmax[0], minmax[1])
        randarray = np.append(randarray,randGroup(minmaxarray,24,32))
        randarray = np.append(randarray,randGroup(minmaxarray,33,36))
        randarray = np.append(randarray,randGroup(minmaxarray,37,54))
        randarray = np.append(randarray,randGroup(minmaxarray,55,66))
        randarray = np.append(randarray,randGroup(minmaxarray,67,70))
        if test_prob(randarray):
            return randarray
    
# init pset and vset
# vset should be constrained by Vmax and Vmin
def init(minmaxarray):
    # initilization of pset
    for i in range(0,particle_number):
        randarray = genprob(minmaxarray)
        pset.append(randarray)
    # initilization of vmax and vset
    for k in range(0,particle_number):
        for idx in range(0,minmaxarray.shape[0]):
            minmax = minmaxarray[idx]
            vmax[idx] = minmax[1] - minmax[0]
            vset[k][idx] = random.uniform(0,vmax[idx])

def convertParticle2config(pconf,file2w):
    base_itm = []
    fp_base = open('data/prob.txt','r')
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
        

def genEvaluate(idx):
    prefix = '../csmith_recorder/csmith_record_2.3.0_t'
    postfix = '/install_files/bin/csmith --probability-configuration ' + configfile_prefix + str(idx)
    csmith_tn_exec_cmd = prefix + str(idx) + postfix
    featurefile = "training_prob_t" + str(idx) + '.csv'
    fp_new = open(featurefile,'w')
    fp_new.close()
    for p_id in range(0,gen4feature_number):
        os.system('timeout 20 ' + csmith_tn_exec_cmd)

def getdistwithidx(features,idx):
    ndim = features.ndim
    if ndim == 1:
        rows = features.shape[0]
        cols = 1
    else:
        rows = features.shape[0]
        cols = features.shape[1]
    idx2get = list(range(0,rows))
    idx2get.remove(idx)
    tmp = []
    f = features[idx2get]
    for i in range(0,rows-1):
        if ndim == 1:
            d = np.linalg.norm(np.asarray([features[idx]])-np.asarray([f[i]]),ord=1)
        else:    
            d = np.linalg.norm(features[idx]-f[i],ord=1)
        tmp.append(d)
    tmp = np.asarray(tmp)
    return np.amin(tmp)

def score():
    evals = []
    features = []
    particle2del = []
    for i in range(0,particle_number):
        feature = np.genfromtxt("record_iters/feature_p" + str(i+1), delimiter=',')
        if feature.ndim == 0 or feature.shape[0] < gen4feature_number*cut:
            particle2del.append(i)
        else:
            features.append(np.mean(feature,axis=0))
    features = np.asarray(features)
    for j in range(0,particle_number):
        if j in particle2del:
            evals.append(-1)
        else:
            evals.append(getdistwithidx(features,j))
    return np.asarray(evals)

def evaluate():
    p = Pool(10)
    p.map(genEvaluate, [1,2,3,4,5])

# get top-5
def update_best(evals):
    size = np.shape(evals)[0]
    tmp_max = np.zeros((5,))
    tmp_prob = np.zeros((5,71))
    for n in range(0,size):
        if evals[n] > pbest_score[n]:
            pbest_score[n] = evals[n]
            pbest[n] = pset[n]
    for k in range(0,5):
        pos_max = np.argmax(evals)
        tmp_max[k] = evals[pos_max]
        tmp_prob[k] = pset[pos_max]
        evals[pos_max] = 0
    for i in range(0,5):
        for j in range(i,5):
            if tmp_max[i] > gbest_score[j]:
                gbest_score[j] = tmp_max[i]
                gbest[j] = tmp_prob[i]
                break

def constrain4p(minmaxarray,p):
    size = minmaxarray.shape[0]
    # write single
    for i in range(0,71):
        minmax = minmaxarray[i]
        if p[i] < minmax[0]:
            p[i] = minmax[0]
        if p[i] > minmax[1]:
            p[i] = minmax[1]
    #  group1
    sum_g1 = np.sum(p[24:33])
    for i_g1 in range(24,33):
        p[i_g1] = p[i_g1] * 100.0 / sum_g1
    #  group2
    sum_g2 = np.sum(p[33:37])
    for i_g2 in range(33,37):
        p[i_g2] = p[i_g2] * 100.0 / sum_g2
    #  group3
    sum_g3 = np.sum(p[37:55])
    for i_g3 in range(37,55):
        p[i_g3] = p[i_g3] * 100.0 / sum_g3
    #  group1
    sum_g4 = np.sum(p[55:67])
    for i_g4 in range(55,67):
        p[i_g4] = p[i_g4] * 100.0 / sum_g4
    #  group1
    sum_g5 = np.sum(p[67:71])
    for i_g5 in range(67,71):
        p[i_g5] = p[i_g5] * 100.0 / sum_g5
    return p

# p represents one position
# v represents p's velocity
def update_particle(p,v,pos,minmaxarray):
    vshape = np.shape(v)
    rand_v1 = np.random.random_sample(vshape)
    rand_v2 = np.random.random_sample(vshape)
    v = v - c*rand_v1*(gbest[0] - p) + c*rand_v2*(pbest[pos] - p)
    p = p + v
    pset[pos] = constrain4p(minmaxarray,p)
    vset[pos] = v

def pso():
    prob_searchspace = getSearchSpace()
    minmaxarray = prob_searchspace.T
    init(minmaxarray)
    cnt = 0
    while cnt < max_iterations:
        cnt = cnt + 1
        evals = []
        # particle_number == len(pset)
        for i in xrange(0,particle_number,5):
            print 'running ' + str(i+1) + '...' + str(i+1+4)
            os.system('rm training_prob_t*')
            curp_1 = pset[i]
            curp_2 = pset[i+1]
            curp_3 = pset[i+2]
            curp_4 = pset[i+3]
            curp_5 = pset[i+4]
            convertParticle2config(curp_1,configfile_prefix+'1')
            convertParticle2config(curp_2,configfile_prefix+'2')
            convertParticle2config(curp_3,configfile_prefix+'3')
            convertParticle2config(curp_4,configfile_prefix+'4')
            convertParticle2config(curp_5,configfile_prefix+'5')
            evaluate()
            os.system("cp training_prob_t1.csv" + " " + "record_iters/feature_p" + str(1+i))
            os.system("cp training_prob_t2.csv" + " " + "record_iters/feature_p" + str(2+i))
            os.system("cp training_prob_t3.csv" + " " + "record_iters/feature_p" + str(3+i))
            os.system("cp training_prob_t4.csv" + " " + "record_iters/feature_p" + str(4+i))
            os.system("cp training_prob_t5.csv" + " " + "record_iters/feature_p" + str(5+i))
        evals = score()
        evals = np.asarray(evals)
        res2w = np.copy(evals)
        update_best(evals)
        for idx in range(0,len(pset)):
            update_particle(pset[idx],vset[idx],idx,minmaxarray)
        if cnt % 20 == 0:
            sorted_idx = np.argsort(res2w)
            np.savetxt("record_iters/last_prob_iter"+str(cnt), pset, fmt='%.8f', delimiter=',', newline='\n')
            np.savetxt("record_iters/last_score_iter"+str(cnt), res2w, fmt='%.2f', delimiter=',', newline='\n')
            np.savetxt("record_iters/last_sorted-index_iter"+str(cnt), np.asarray(sorted_idx), fmt='%d', delimiter=',', newline='\n')

if __name__ == '__main__':
    os.system("mkdir ../record_iters")
    pso()
