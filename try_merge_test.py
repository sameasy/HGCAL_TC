import uproot
import encode2
import pandas as pd
import argparse

def getstring(inp):
    st = ""
    for i in inp :
        st += str(i)
    return st

def getencodedlink(nhgc,nln):
    outputencodedwafer = []
    for i in range(0,nhgc):
#        print ("nHGC:",i)
        for j in range(0,nln):
#            print ("nlink:",j)
#            print (getstring(grouped.get_group((i,j ))['encodedCharge']))
            outputencodedwafer.append(getstring(grouped.get_group((i,j ))['encodedCharge']))
    return outputencodedwafer

parser = argparse.ArgumentParser()
parser.add_argument("-I", "--inputfile",help="input data file",default="root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/NewNtuples/ntuple_hgcalNtuples_vbf_hmm_200PU_1.root")
parser.add_argument("-G", "--geomfile",help="input geom file",default="root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/triggerGeomV9.root")


fName = parser.parse_args().inputfile
#fName='root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/NewNtuples/ntuple_hgcalNtuples_vbf_hmm_200PU_1.root'
_tree = uproot.open(fName,xrootdsource=dict(chunkbytes=1024**3, limitbytes=1024**3))['hgcalTriggerNtuplizer/HGCalTriggerNtuple']

df = _tree.pandas.df( ['tc_subdet','tc_zside','tc_layer','tc_wafer','tc_cell','tc_data','tc_uncompressedCharge','tc_compressedCharge'],entrystart=0,entrystop=10)
df.columns = ['subdet','zside','layer','wafer','triggercell','data','uncompressedCharge','compressedCharge']

df.set_index(['subdet','zside','layer','wafer','triggercell'],append=True,inplace=True)
df.reset_index('subentry',drop=True,inplace=True)
df.sort_index(inplace=True)
#df['encodedCharge'] = df.uncompressedCharge.apply(encode.encode,args=(True,1,4,3,True))
df['encodedCharge'] = df.uncompressedCharge.apply(encode2.encode,args=(1,4,3,True))
df['decodedCharge'] = df.encodedCharge.apply(encode2.decode,args=(1,4,3))

dftest = df.copy()
dftest.reset_index(inplace=True)
nevents = len(dftest['entry'].unique())
print ("total events:",len(dftest['entry'].unique()))

geomName = parser.parse_args().geomfile
#geomName = "root://cmseos.fnal.gov//store/user/dnoonan/HGCAL_Concentrator/triggerGeomV9.root"
geomTree = uproot.open(geomName,xrootdsource=dict(chunkbytes=1024**3, limitbytes=1024**3))["hgcaltriggergeomtester/TreeTriggerCells"]
geomDF = geomTree.pandas.df(['subdet','zside','layer','wafer','triggercell','c_n'])
geomDF.set_index(['subdet','zside','layer','wafer','triggercell'],inplace=True)
geomDF['isHDM'] = geomDF.c_n>4
geomDF.sort_index(inplace=True)

mapd = pd.read_csv('TC_MAP.csv')

enclist = []
declist = []
wafnumb = 38
for nev in range (0,nevents):
#### Get single wafer (event 0, subdet 3, zside 1, layer 5, wafer 99)
    dfWafer = df.loc[nev,3,1,5,wafnumb]
    geomDFWafer = geomDF.loc[3,1,5,99]
    geomDFWafer['encodedCharge'] = dfWafer['encodedCharge']
    geomDFWafer['decodedCharge'] = dfWafer['decodedCharge']
    geomDFWafer.fillna('0000000',inplace=True)
    geomDFWafer.reset_index(inplace=True)
#    geomDFWafer
    merged = pd.merge(geomDFWafer, mapd, on=['triggercell','isHDM'])
    nhgc = len(merged['nHGROC'].unique())
    nln = len(merged['nlink'].unique())
    #merged.set_index(['nlink'],append=True,inplace=True)
    #merged
    grouped = merged.groupby(['nHGROC','nlink'])
    getencodedlink(nhgc,nln)
    enclist.append(getencodedlink(nhgc,nln))
    decodedlist = merged['decodedCharge'].tolist()
    declist.append(decodedlist)
    

#print ("enclist:\n",len(enclist))
#print ("declist:\n",len(declist))
declistlabel = []
for i in range(0,48):
    declistlabel.append("trigcell"+str(i))
print (declistlabel)
enclistlabel = []
for i in range(0,12):
    enclistlabel.append("triglink"+str(i))
print (enclistlabel)
dfenc = pd.DataFrame(enclist,columns=enclistlabel)
dfdec = pd.DataFrame(declist,columns=declistlabel)


if (wafnumb < 40):
    dfenc.to_csv("ENC_HD.csv", encoding='utf-8', index=False)
    dfdec.to_csv("DEC_HD.csv", encoding='utf-8', index=False)
else:
    dfenc.to_csv("ENC_LD.csv", encoding='utf-8', index=False)
    dfdec.to_csv("DEC_LD.csv", encoding='utf-8', index=False)

#print (dfenc)
#print (dfdec)
