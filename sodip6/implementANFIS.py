import json
import matlab.engine
eng = matlab.engine.start_matlab()

def get_anfis_status(device_no):
    #read Knowledge Base (KB) and Dependency Fuzzy System (DFS) output
    # get L, S, M, T, C

    datain = []
    with open('D:\PhD-Study\Experimental\SoDIP6\sodip6\deviceKB.json') as readKB:
        lsm = json.load(readKB)
        datain.append(lsm[device_no]["L"])
        datain.append(lsm[device_no]["S"])
        datain.append(lsm[device_no]["M"])
        datain.append(lsm[device_no]["T"])
        datain.append(lsm[device_no]["C"])

    readKB.close()
    check_anfis = eng.readfis('D:\PhD-Study\Experimental\MATLAB-TEST\ANFIS-100EPH22-GBLMF.fis', nargout=1)
    input_anfis = matlab.double(datain)
    observed_value = eng.evalfis(check_anfis, input_anfis)

    return 'U' if observed_value > 2 else 'R'

