# HFCCT
A tool for vulnerability detection of Hyperledger Fabric smart contracts (chaincodes).

# Introduction

`CCAST.go`：Parse the golang chaincodes into an AST (Abstract Syntax Tree) and provide some external interfaces, then extract the corresponding information from AST according to the input parameters and return it.

`CCSE.py`：Execute symbolic execution to detect vulnerabilities.

`CCSA.py`：Use AST to detect vulnerabilities.

`HFCCT.py`：Call CCSE.py and CCSA.py for vulnerability detection and generate the final test report. It is also the entry file of HFCCT.

`chaincodes/`：Some chaincodes samples.

# Usage

1. Download. `git clone https://github.com/PerryLee69/HFCCT.git`

2. Use your python IDE to Run `HFCCT.py` , to detect vulnerabilities for sample projects in `chaincodes/` .

3. You can add projects to `chaincodes/` and modify "test_list"  of `HFCCT.py` , to detect vulnerabilities for more projects you want to detect.