#include <iostream>
#include "Record.h"
#include <map>
#include <cstring>
#include <fstream>
#include <iomanip>

using namespace std;

std::map<string, int> Record::pname_to_cnt = std::map<string, int>();
std::map<string, int> Record::tmp_pname_to_cnt = std::map<string, int>();

string Record::cntName[111] = {"pMoreStructUnionCnt","pBitFieldsCreationCnt","pBitFieldsSignedCnt","pBitFieldInNormalStructCnt","pScalarFieldInFullBitFieldsCnt","pExhaustiveBitFieldsCnt","pSafeOpsSignedCnt","pSelectDerefPointerCnt","pRegularVolatileCnt","pRegularConstCnt","pStricterConstCnt","pLooserConstCnt","pFieldVolatileCnt","pFieldConstCnt","pStdUnaryFuncCnt","pShiftByNonConstantCnt","pPointerAsLTypeCnt","pStructAsLTypeCnt","pUnionAsLTypeCnt","pFloatAsLTypeCnt","pNewArrayVariableCnt","pAccessOnceVariableCnt","pInlineFunctionCnt","pBuiltinFunctionCnt","pAssignCnt","pBlockCnt","pForCnt","pIfElseCnt","pInvokeCnt","pReturnCnt","pContinueCnt","pBreakCnt","pGotoCnt","pArrayOpCnt","pSimpleAssignCnt","pMulAssignCnt","pDivAssignCnt","pRemAssignCnt","pAddAssignCnt","pSubAssignCnt","pLShiftAssignCnt","pRShiftAssignCnt","pBitAndAssignCnt","pBitXorAssignCnt","pBitOrAssignCnt","pPreIncrCnt","pPreDecrCnt","pPostIncrCnt","pPostDecrCnt","pPlusCnt","pMinusCnt","pNotCnt","pBitNotCnt","pAddCnt","pSubCnt","pMulCnt","pDivCnt","pModCnt","pCmpGtCnt","pCmpLtCnt","pCmpGeCnt","pCmpLeCnt","pCmpEqCnt","pCmpNeCnt","pAndCnt","pOrCnt","pBitXorCnt","pBitAndCnt","pBitOrCnt","pRShiftCnt","pLShiftCnt","pVoidCnt","pCharCnt","pIntCnt","pShortCnt","pLongCnt","pLongLongCnt","pUCharCnt","pUIntCnt","pUShortCnt","pULongCnt","pULongLongCnt","pFloatCnt","pInt8Cnt","pInt16Cnt","pInt32Cnt","pInt64Cnt","pMoreStructUnionTotalCnt","pBitFieldsCreationTotalCnt","pBitFieldsSignedTotalCnt","pBitFieldInNormalStructTotalCnt","pScalarFieldInFullBitFieldsTotalCnt","pExhaustiveBitFieldsTotalCnt","pSafeOpsSignedTotalCnt","pSelectDerefPointerTotalCnt","pRegularVolatileTotalCnt","pRegularConstTotalCnt","pStricterConstTotalCnt","pLooserConstTotalCnt","pFieldVolatileTotalCnt","pFieldConstTotalCnt","pStdUnaryFuncTotalCnt","pShiftByNonConstantTotalCnt","pPointerAsLTypeTotalCnt","pStructAsLTypeTotalCnt","pUnionAsLTypeTotalCnt","pFloatAsLTypeTotalCnt","pNewArrayVariableTotalCnt","pAccessOnceVariableTotalCnt","pInlineFunctionTotalCnt","pBuiltinFunctionTotalCnt"};


//87 111
Record::Record()
{

}

Record::~Record()
{

}

void
Record::initialize()
{
	for(int i = 0; i < 111; i++)
	{
		pname_to_cnt[cntName[i]] = 0;
	}
}

void
Record::initialize_tmp()
{
	for(int i = 0; i < 111; i++)
	{
		tmp_pname_to_cnt[cntName[i]] = 0;
	}
}

void
Record::set_name_cnt(string pname, int cnt)
{
	pname_to_cnt[pname] += cnt;
}

void
Record::set_name_cnt_tmp(string pname, int cnt)
{
	tmp_pname_to_cnt[pname] += cnt;
}

void
Record::print_name_cnt()
{
	
	ofstream ofile;
	ofile.open("../training_prob_t1.csv",ios::app);

	// for(int i = 0; i < 110; i++)
	// {
	// 	ofile<<cntName[i]<<",";
	// }
	// ofile<<cntName[110]<<endl;

	for(int i = 0; i < 110; i++)
	{
		ofile<<pname_to_cnt[cntName[i]]<<",";
	}
	ofile<<pname_to_cnt[cntName[110]]<<endl;
	
	ofile.close();
}

void
Record::print_name_cnt_tmp()
{
	for(int i = 0; i < 111; i++)
	{
		cout<<cntName[i]<<" ===== "<<tmp_pname_to_cnt[cntName[i]]<<endl;
	}
}


