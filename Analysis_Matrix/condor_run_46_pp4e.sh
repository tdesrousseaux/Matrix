#!/bin/bash

CURRENT=${PWD}
source /cvmfs/cms.cern.ch/cmsset_default.sh
export SITECONFIG_PATH=/cvmfs/cms.cern.ch/SITECONF/T2_FR_GRIF_LLR/GRIF-LLR
cd /eos/user/t/tdesrous/private/CMSSW_10_2_13/src/
eval $(scram ru -sh)
cd ${CURRENT}

cp -r /eos/user/t/tdesrous/private/CMSSW_10_2_13/src/Matrix/run/ppeeexex04_MATRIX .
cd ppeeexex04_MATRIX/
./bin/run_process run_46 --run_mode run

pwd
cp -r ./result/run_46  /eos/user/t/tdesrous/private/CMSSW_10_2_13/src/Matrix/run/ppeeexex04_MATRIX/result/