Welcome to HiCOND homepage!

There are three folders in the root folder, including tool, find_correct_commit, and configfile. We introduce each folder in detail as follows.

1. tool, which is our tool implementation for finding a set of bug-revealing and diverse test configurations. There are three folders:

	1) csmith_recorder, which includes our adapted Csmith that can record all the decisions for all program features. Here the file install.sh is the installation script of the Csmith

	2) source, which includes the source code of our tool HiCOND. There are two files:
	
		>> pso_autoconfig.py, includes the three steps in our approach: range inferring, diversity measuring, and pso-based searching. 

		>> genconfig.py, is used to generate the test configurations that meet the format of the Csmith configuration.

        >> OriSwarm.py, is the original Swarm Testing way which it's called OriSwarm baseline in our paper.

        >> VarSwarm.py, is the variant Swarm Testing way which it's called VarSwarm baseline in our paper.

	3) data, which includes the data that is used in the searching process in our study. There are six files:

		>> prob.txt, is the default test configuration of Csmith

		>> oriprob.txt, is the probabilities extracted from the default test configuration

		>> probforfailing440pass.csv, is the probabilities computed from the historical failing test program set (the test programs failed at GCC-4.3.0 but passed at all the used subjects in our study)

		>> probforpassing.csv, is the probabilities computed from the historical passing test program set

		>> status_first.txt, is the testing results of all the historical test programs

		>> training_prob_calc.csv, is the probabilities of all the program features for all the historical test programs

2. find_fixed_commit, which is used for finding the correcting commit for each bug-triggering test program, where the file gcc_duplicate_hunter.pl is used for GCC and the file llvm_duplicate_hunter.pl is used for LLVM

3. configfile, which contains the found test configurations using our tool HiCOND and each file in the folder is a test configuration for Csmith.


Thanks!


