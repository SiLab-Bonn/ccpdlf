import time, string, os ,sys

import numpy as np
np.set_printoptions(linewidth="nan", threshold="nan")
import matplotlib.pyplot as plt
import bitarray
import logging

sys.path.append(r"D:\workspace\basil\v2.4.0")

from basil.dut import Dut

class ccpdlf():
    def __init__(self,conf=""):
        if conf=="":
            conf="ccpdlfA.yaml"
        self.dut=Dut(conf)
        self.init_log()
        self.debug=0
        self._build_img=np.vectorize(self._build_img_one)
        self.tdac=np.zeros([24,114],int)
        
        self.dut.init()
        self.set_DACcurrent()
        self.power()
        
    def init_log(self,logfile='ccpdlf.log'):
        self.logfile=logfile
        self.logger=logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        fh=logging.FileHandler(logfile)
        ch=logging.StreamHandler()
        fh.setLevel(logging.INFO)
        ch.setLevel(logging.DEBUG)
        formatter=logging.Formatter('%(asctime)s %(funcName)s %(message)s')
        fh.setFormatter(formatter)
        formatterc=logging.Formatter('%(message)s')
        ch.setFormatter(formatterc)
        self.logger.addHandler(ch)
        self.logger.addHandler(fh)

    def _build_img_one(self,spix):
            frame=spix/2736
            spix=2735-spix%2736
            col=spix/114
            row=spix%114
            if col%4==0:
                pass
            elif col%4==1:
                row=113-row
            elif col%4==2:
                col=col+1
            elif col%4==3:
                col=col-1
                row=113-row
            return frame,col,row

    def archive(self):
        with open('archive_%s'%self.logfile, 'a') as fo:
            try:
                with open(self.logfile) as f:
                    for line in f:
                        fo.write(line)
                with open(self.logfile,"w") as f:
                    f.write("")
            except:
                pass

    def power(self,pwr_en=True,Vdda=1.8,Vddp=1.5,Vddd=1.8,VCasc=1.0,BL=0.75,TH=0.80,PCBTH=1.3):    
        self.dut['CCPD_Vdda'].set_current_limit(250,unit="raw")
        
        self.dut['CCPD_Vdda'].set_voltage(Vdda, unit='V')
        self.dut['CCPD_Vdda'].set_enable(pwr_en)
        
        self.dut['CCPD_vddaPRE'].set_voltage(Vddp, unit='V')
        self.dut['CCPD_vddaPRE'].set_enable(pwr_en)
        
        self.dut['CCPD_vddd'].set_voltage(Vddd, unit='V')
        self.dut['CCPD_vddd'].set_enable(pwr_en)

        self.dut['CCPD_VCasc'].set_voltage(VCasc, unit='V')
        self.dut['CCPD_PCBTH'].set_voltage(PCBTH, unit='V')
        self.dut['CCPD_BL'].set_voltage(BL, unit='V')
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        
        self.logger.info("Vdda:%f Vddp:%f Vddd:%f VCasc:%f BL:%f TH:%f PCBTH:%f"%(
                        Vdda,Vddp,Vddd,VCasc,BL,TH,PCBTH))
                        
    def set_DACcurrent(self,VN=0,VPLoad=0,VPFB=0,VNFoll=0,BLRes=0,IComp=0,PBIAS=0,WGT0=0,WGT1=0,WGT2=0,LSBdacL=0):
        self.dut['probeVN'].set_current(VN,unit="uA")
        self.dut['probeVPLoad'].set_current(VPLoad,unit="uA")
        self.dut['probeVPFB'].set_current(VPFB,unit="uA")
        self.dut['probeVNFoll'].set_current(VNFoll,unit="uA")
        self.dut['probeBLRes'].set_current(BLRes,unit="uA")
        self.dut['probeIComp'].set_current(IComp,unit="uA")
        self.dut['probePBIAS'].set_current(PBIAS,unit="uA")
        self.dut['probeWGT0'].set_current(WGT0,unit="uA")
        self.dut['probeWGT1'].set_current(WGT1,unit="uA")
        self.dut['probeWGT2'].set_current(WGT2,unit="uA")
        self.dut['probeLSBdacL'].set_current(LSBdacL,unit="uA")
        
        self.logger.info("VN:%f VPLoad:%f VPFB:%f VNFoll:%f BLRes:%f IComp:%f PBIAS:%f WGT0:%f WGT1:%f WGT2:%f LSBdacL:%f "%(
                        VN,VPLoad,VPFB,VNFoll,BLRes,IComp,PBIAS,WGT0,WGT1,WGT2,LSBdacL)) 

    def set_pulser(self,inj_high=4.0,inj_low=0.0,period=100,repeat=1,delay=700,ext=True):
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        
        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=repeat
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=period/2
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=period-period/2
        self.dut["CCPD_PULSE_INJ"]["EN"]=1
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=period*repeat+10
        self.dut["CCPD_PULSE_GATE"]["EN"]=ext
        
        self.logger.info("inj:%.4f,%.4f period:%d repeat:%d delay:%d ext:%d"%(
            inj_high,inj_low,period,repeat,delay,int(ext)))
    def inject(self):
        self.dut["CCPD_PULSE_INJ"].start()

    def set_th(self,TH):
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        THvol=self.dut['CCPD_TH'].get_voltage(unit='V')
        self.logger.info("th_set:%f th:%f"%(TH,THvol))

    def get_status(self):
        stat={"Vdda": self.dut['CCPD_Vdda'].get_voltage(unit='V'),
            "Vdda_curr": self.dut['CCPD_Vdda'].get_current(unit="mA"),
            "Vddp": self.dut['CCPD_vddaPRE'].get_voltage(unit='V'),
            "Vddp_curr": self.dut['CCPD_vddaPRE'].get_current(unit="mA"),
            "Vddd": self.dut['CCPD_vddd'].get_voltage(unit='V'),
            "Vddd_curr": self.dut['CCPD_vddd'].get_current(unit="mA"),
            "VCasc": self.dut['CCPD_VCasc'].get_voltage(unit='V'),
            "VCasc_curr": self.dut['CCPD_VCasc'].get_current(unit="mA"),
            "PCBTH": self.dut['CCPD_PCBTH'].get_voltage(unit='V'),
            'PCBTH_curr': self.dut['CCPD_PCBTH'].get_current(unit="mA"),
            'BL': self.dut['CCPD_BL'].get_voltage(unit='V'),
            'BL_curr': self.dut['CCPD_BL'].get_current(unit="mA"),
            'TH': self.dut['CCPD_TH'].get_voltage(unit='V'),
            'TH_curr': self.dut['CCPD_TH'].get_current(unit="mA"),
            ##### TODO make data from get_data
            'BLRes':self.dut['CCPD_SR']['BLRes'].tovalue(),
            'VN':self.dut['CCPD_SR']['VN'].tovalue(),
            'VPFB':self.dut['CCPD_SR']['VPFB'].tovalue(),
            'VPFoll':self.dut['CCPD_SR']['VPFoll'].tovalue(),
            'VPLoad':self.dut['CCPD_SR']['VPLoad'].tovalue(),
            'LSBdacL':self.dut['CCPD_SR']['LSBdacL'].tovalue(),
            'IComp':self.dut['CCPD_SR']['IComp'].tovalue(),
            'VSTRETCH':self.dut['CCPD_SR']['VSTRETCH'].tovalue(),
            'WGT0':self.dut['CCPD_SR']['WGT0'].tovalue(),
            'WGT1':self.dut['CCPD_SR']['WGT1'].tovalue(),
            'WGT2':self.dut['CCPD_SR']['WGT2'].tovalue(),
            'IDacTEST':self.dut['CCPD_SR']['IDacTEST'].tovalue(),
            'IDacLTEST':self.dut['CCPD_SR']['IDacLTEST'].tovalue(),
            "SW_ANA":self.dut["CCPD_SR"]["SW_ANA"].tovalue(),
            "Pixels":" ".join(hex(ord(n)) for n in self.dut["CCPD_SR"]["Pixels"].tobytes()),
            'CCPD_SW':self.dut["CCPD_SW"].get_data()[0],
            'rx_SW':self.dut["rx"].get_data()[0],
            'INJ_DELAY':self.dut["CCPD_PULSE_INJ"]["DELAY"],
            'INJ_WIDTH':self.dut["CCPD_PULSE_INJ"]["WIDTH"],
            'INJ_REPEAT':self.dut["CCPD_PULSE_INJ"]["REPEAT"],
            'INJ_EN':self.dut["CCPD_PULSE_INJ"]["EN"],
            'GATE_DELAY':self.dut["CCPD_PULSE_GATE"]["DELAY"],
            'GATE_WIDTH':self.dut["CCPD_PULSE_GATE"]["WIDTH"],
            'GATE_REPEAT':self.dut["CCPD_PULSE_GATE"]["REPEAT"],
            'GATE_EN':self.dut["CCPD_PULSE_GATE"]["EN"]
            } 
        stat.update(self.get_DACcurrent())           
        return stat

    def show(self):
        r= self.get_status()
        self.logger.info('BLRes:%d VN:%d VPFB:%d VPFoll:%d VPLoad:%d LSBdacL:%d IComp:%d VSTRETCH:%d WGT0:%d WGT1:%d WGT2:%d IDacTEST:%d IDacLTEST:%d'%(
               r["BLRes"],r["VN"],r["VPFB"],r["VPFoll"],r["VPLoad"],r["LSBdacL"],r["IComp"],
               r["VSTRETCH"],r["WGT0"],r["WGT1"],r["WGT2"],r["IDacTEST"],r["IDacLTEST"]))
        self.logger.info("INJ width:%d delay:%d repeat:%d en:%d"%(
               r["INJ_WIDTH"],r["INJ_DELAY"],r["INJ_REPEAT"],r["INJ_EN"]))
        self.logger.info("GATE width:%d delay:%d repeat:%d en:%d"%(
               r["GATE_WIDTH"],r["GATE_DELAY"],r["GATE_REPEAT"],r["GATE_EN"]))

    def get_DACcurrent(self):
        stat={'probeVN': self.dut['probeVN'].get_voltage(unit="V"),
            'probeVN_curr': self.dut['probeVN'].get_current(unit="uA"),
            'probeVPLoad': self.dut['probeVPLoad'].get_voltage(unit="V"),
            'probeVPLoad_curr': self.dut['probeVPLoad'].get_current(unit="mA"),
            'probeVPFB': self.dut['probeVPFB'].get_voltage(unit="V"),
            'probeVNFoll': self.dut['probeVNFoll'].get_voltage(unit="V"),
            'probeVNFoll_curr': self.dut['probeVNFoll'].get_current(unit="mA"),
            'probeBLRes': self.dut['probeBLRes'].get_voltage(unit="V"),
            'probeBLRes_curr': self.dut['probeBLRes'].get_current(unit="mA"),
            'probeIComp': self.dut['probeIComp'].get_voltage(unit="V"),
            'probeIComp_curr': self.dut['probeIComp'].get_current(unit="mA"),
            'probePBIAS': self.dut['probePBIAS'].get_voltage(unit="V"),
            'probePBIAS_curr': self.dut['probePBIAS'].get_current(unit="mA"),
            'probeWGT0': self.dut['probeWGT0'].get_voltage(unit="V"),
            'probeWGT0_curr': self.dut['probeWGT0'].get_current(unit="mA"),
            'probeWGT1': self.dut['probeWGT1'].get_voltage(unit="V"),
            'probeWGT1_curr': self.dut['probeWGT1'].get_current(unit="mA"),
            'probeWGT2': self.dut['probeWGT2'].get_voltage(unit="V"),
            'probeWGT2_curr': self.dut['probeWGT2'].get_current(unit="mA"),
            'probeLSBdacL': self.dut['probeLSBdacL'].get_voltage(unit="V"),
            'probeLSBdacL_curr': self.dut['probeLSBdacL'].get_current(unit="mA")}
        return stat

    def _write_SR(self,sw="SW_LDDAC"):
        if sw=="SW_LDDAC":
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=1
            self.dut['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_LDPIX":
            self.dut['CCPD_SW']['SW_LDPIX']=1
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_HIT":
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=1
        else:
            self.dut['CCPD_SW']['SW_LDPIX']=0
            self.dut['CCPD_SW']['SW_LDDAC']=0
            self.dut['CCPD_SW']['SW_HIT']=0
        self.dut['CCPD_SW'].write()

        self.dut['CCPD_SR'].set_size(2843)
        self.dut['CCPD_SR'].set_repeat(1)
        self.dut['CCPD_SR'].set_wait(0)
        self.dut['CCPD_SR'].write()
        self.dut['CCPD_SR'].start()
        i=0
        while i<10000:
            if self.dut['CCPD_SR'].is_done():
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        if i==10000:
            self.logger.info("ERROR timeout")    

    def set_global(self,BLRes=17,VN=32,VPFB=28,VPFoll=17,VPLoad=14,LSBdacL=12,IComp=17,
               VSTRETCH=15,WGT0=10,WGT1=35,WGT2=63,IDacTEST=0,IDacLTEST=0):
        self.dut['CCPD_SR']['BLRes']=BLRes
        self.dut['CCPD_SR']['VN']=VN
        self.dut['CCPD_SR']['VPFB']=VPFB
        self.dut['CCPD_SR']['VPFoll']=VPFoll
        self.dut['CCPD_SR']['VPLoad']=VPLoad
        self.dut['CCPD_SR']['LSBdacL']=LSBdacL
        self.dut['CCPD_SR']['IComp']=IComp
        self.dut['CCPD_SR']['VSTRETCH']=VSTRETCH
        self.dut['CCPD_SR']['WGT0']=WGT0
        self.dut['CCPD_SR']['WGT1']=WGT1
        self.dut['CCPD_SR']['WGT2']=WGT2
        self.dut['CCPD_SR']['IDacTEST']=IDacTEST
        self.dut['CCPD_SR']['IDacLTEST']=IDacLTEST

        self._write_SR()

        self.logger.info('BLRes:%d VN:%d VPFB:%d VPFoll:%d VPLoad:%d LSBdacL:%d IComp:%d VSTRETCH:%d WGT0:%d WGT1:%d WGT2:%d IDacTEST:%d IDacLTEST:%d'%(
               BLRes,VN,VPFB,VPFoll,VPLoad,LSBdacL,IComp,VSTRETCH,WGT0,WGT1,WGT2,IDacTEST,IDacLTEST))
               
    def _cal_Pixels(self,pix):
        if isinstance(pix,str):
            if pix=="all":
                en_pix=bitarray.bitarray('1'*2736)
            else:
                en_pix=bitarray.bitarray('0'*2736)
        elif isinstance(pix,int):
            if pix==0:
                en_pix=bitarray.bitarray('0'*2736)
            else:
                en_pix=bitarray.bitarray('1'*2736)
        elif isinstance(pix,type(bitarray.bitarray())):
            en_pix=bitarray.bitarray('0'*2736)
            for i in range(0,24,4):
                a0=pix[114*(i):114*(i+1)].copy()
                a1=pix[114*(i+1):114*(i+2)].copy()
                a2=pix[114*(i+2):114*(i+3)].copy()
                a3=pix[114*(i+3):114*(i+4)].copy()
                a1.reverse()
                a2.reverse()
                en_pix[114*(i):114*(i+4)]=a0+a1+a3+a2
        else:
            en_pix=bitarray.bitarray('0'*2736)
            if isinstance(pix[0],int):
                pix=[pix]
            for p in pix:
                r=p[0]%4
                if r==0:
                    en_pix[p[0]*114+p[1]]=1
                elif r==1:
                    en_pix[(p[0]+1)*114-p[1]-1]=1
                elif r==2:
                    en_pix[(p[0]+2)*114-p[1]-1]=1
                elif r==3:
                    en_pix[(p[0]-1)*114+p[1]]=1
        return en_pix
               
    def set_mon_en(self,pix="none"):
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
        
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=1
        self.dut['CCPD_SR']['PREAMP_EN']=0
        
        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix

        for i in range(0,2736,114):
            self.dut['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        
        self.preamp_en=self.dut["CCPD_SR"]["Pixels"].copy()
        self.sw_ana=self.dut['CCPD_SR']['SW_ANA'].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x "%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue())
        if self.debug==1:
            s="%s pixel_all:%s"%(s,self.dut["CCPD_SR"]["Pixels"].to01())
        else:
            s="%s pixel_any:%d"%(s,self.dut["CCPD_SR"]["Pixels"].any())
        self.logger.info(s)

    def set_preamp_en(self,pix="all"):
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)

        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=1

        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix

        self._write_SR(sw="SW_LDPIX")
        
        self.preamp_en=self.dut["CCPD_SR"]["Pixels"].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x"%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue())
        if self.debug==1:
            s="%s pixel_all:%s"%(s,self.dut["CCPD_SR"]["Pixels"].to01())
        else:
            s="%s pixel_any:%d"%(s,self.dut["CCPD_SR"]["Pixels"].any())
        self.logger.info(s)

    def set_inj_en(self,pix="all"):
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
    
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=1
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0

        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix.copy()

        self._write_SR(sw="SW_LDPIX")
        
        self.inj_en=self.dut["CCPD_SR"]["Pixels"].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x"%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue())
        if self.debug==1:
            s="%s pixel_all:%s"%(s,self.dut["CCPD_SR"]["Pixels"].to01())
        else:
            s="%s pixel_any:%d"%(s,self.dut["CCPD_SR"]["Pixels"].any())
        self.logger.info(s)
        
    def set_tdac(self,tdac):
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
    
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0
        
        for i_trim in [1,2,4,8]:
            if isinstance(tdac, int):
                if (tdac & i_trim)==0:
                    pix=0
                else:
                    pix=1
                self.tdac=np.ones([24,114],int)*tdac
            else:
                ## define tdac=np.zeros([24,114])
                pix=bitarray.bitarray(((np.reshape(tdac, 114*24) & i_trim) !=0).tolist())
                self.tdac=np.copy(tdac)
            en_pix=self._cal_Pixels(pix)
            self.dut['CCPD_SR']['Pixels']=en_pix
            self.dut['CCPD_SR']['TRIM_EN']=i_trim
            self._write_SR(sw="SW_LDPIX")
        if self.debug==1:
            s="tdac:%s"%(str(tdac))
        else:
            s="tdac %d-%d:%d"%(0,0,self.tdac[0,0])
        self.logger.info(s)

    def sel_pix(self,pix=[14,14],inj_en=1,mon_en=1,preamp_en=1,trim_en=0):
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)

        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=inj_en
        self.dut['CCPD_SR']['MONITOR_EN']=mon_en
        self.dut['CCPD_SR']['PREAMP_EN']=preamp_en
        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix
        if mon_en==1:
            for i in range(0,2736,114):
                self.dut['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        s="pix:%s inj_en:%d mon_en:%d preamp_en:%d"%(str(pix),inj_en,mon_en,preamp_en)
        self.logger.info(s)

    def set_hit(self,exp=5100,repeat=100,delay=700,inj_width=50,gate_width=-1):
        # set gpio
        self.dut['rx']['FE'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 1
        self.dut['rx'].write()
        
        # reset spi
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate first
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        self.dut["CCPD_SR"].set_size(2736)
        self.dut["CCPD_SR"].set_repeat(repeat)
        self.dut["CCPD_SR"].set_wait(exp)
        
        ## set LD switches
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=1
        self.dut['CCPD_SW'].write()
        
        # set pulser
        self.dut["CCPD_Injection_high"].set_voltage(4,unit="V")
        self.dut["CCPD_Injection_low"].set_voltage(0,unit="V")
        
        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=1
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["EN"]=1
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=delay
        if gate_width==-1:
            gate_width=inj_width*2+250
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=1
        
        # set TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=False
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(True)
        
        s="exp:%d repeat:%d delay:%d inj_width:%d gate_width:%d"%(
            exp,repeat,delay,inj_width,gate_width)
        self.logger.info(s)

    def set_tdc(self,gate_width=-1,repeat=100,inj_width=50,delay=10,inj_high=4):
        # set gpio
        self.dut['rx']['FE'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 1
        self.dut['rx']['CCPD_RX'] = 0
        self.dut['rx'].write()
        
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=0
        self.dut['CCPD_SW'].write()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)

        # set pulser
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.dut["CCPD_Injection_low"].set_voltage(0,unit="V")
        
        self.dut["CCPD_PULSE_INJ"].reset()
        if inj_width==0:
            self.dut["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self.dut["CCPD_PULSE_INJ"]["REPEAT"]=repeat
            self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_width
            self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self.dut["CCPD_PULSE_INJ"]["EN"]=1
        if gate_width==-1:
            gate_width=inj_width*2*repeat+10
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=0 

        # reset TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['EN_INVERT_TDC']=True
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=True
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()

        s="gate_width:%d repeat:%d inj_width:%d delay:%d"%(
            gate_width,repeat,inj_width,delay)
        self.logger.info(s)
        
    def get_hit(self):
        self.dut['sram'].reset()
        self.dut["CCPD_SR"].start()
        wait=self.dut["CCPD_SR"].get_wait()
        repeat=self.dut["CCPD_SR"].get_repeat()
        i=0
        while not self.dut['CCPD_SR'].is_done():
            if i>10000+wait*repeat/1000:
                self.logger.info("ERROR timeout")
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        return self.dut['sram'].get_data()

    def set_hit2(self,inj_width=50,inj_high=4):
        # set gpio
        self.dut['rx']['FE'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 1
        self.dut['rx'].write()
        
        # disable gate
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate
        
        # reset spi
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        self.dut["CCPD_SR"].set_size(2736)
        self.dut["CCPD_SR"].set_repeat(1)
        self.dut["CCPD_SR"].set_wait(0)
        
        ## set LD switches
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=0
        self.dut['CCPD_SW'].write()
        
        # set pulser
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.dut["CCPD_Injection_low"].set_voltage(0,unit="V")
        
        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=1
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["EN"]=0
        
        # disable TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=False
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(True)
        
        s="inj_high:%f inj_width:%d"%(
            inj_high,inj_width)
        self.logger.info(s)
        
    def get_hit2(self,th,th0):
        self.dut['sram'].reset()
        self.set_th(th0)
        ## open gate
        self.dut["CCPD_SW"]["TEST_HIT"]=1
        self.dut["CCPD_SW"].write()
        self.set_th(th)
        ## inject
        self.dut["CCPD_PULSE_INJ"].start()
        i=0
        while not self.dut['CCPD_SR'].is_done():
            if i>1000:
                self.logger.info("ERROR ccpd_pulse_inj timeout")
                break
            i=i+1
        ## close gate
        self.dut["CCPD_SW"]["TEST_HIT"]=0
        self.dut["CCPD_SW"].write()
        self.set_th(th0)
        ## readout
        self.dut["CCPD_SR"].start()
        i=0
        while not self.dut['CCPD_SR'].is_done():
            if i>10000:
                self.logger.info("ERROR timeout")
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        return self.dut['sram'].get_data()
    
    def get_tdc(self):
        self.dut['sram'].reset()
        self.dut["CCPD_PULSE_GATE"].start()
        i=0
        while i<10000:
            if self.dut['CCPD_PULSE_GATE'].is_done():
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        if i==10000:
            self.logger.info("ERROR timeout")
        return self.dut['sram'].get_data()
    
    def scan_th(self,b=1.1,e=0.7,s=-0.01,n=100,exp=5100,pix=[14,14]):
        self.set_hit(repeat=n,exp=exp)
        self.dut['CCPD_TH'].set_voltage(b, unit='V')
        for th in np.arange(b+s,e+s,s):
            d=self.get_hit()
            th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
            self.dut['CCPD_TH'].set_voltage(th, unit='V')
            p=self.analyse_hit(d)
            if len(p)==0:
                cnt=0
            else:
                p=p[np.bitwise_and(p[:,1]==14,p[:,2]==14)]
                cnt=len(p[p[:,0]!=0])
            self.logger.info("%f,%s"%(th_meas,cnt))

    def scan_th_tdc(self,b=1.1,e=0.7,s=-0.01,n=1,exp=100000,inj_width=0):
        self.set_tdc(repeat=n,gate_width=exp,inj_width=inj_width)
        self.dut['CCPD_TH'].set_voltage(b, unit='V')
        self.logger.info("th cnt ave std")
        for th in np.arange(b+s,e+s,s):
            d=self.get_tdc()
            th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
            self.dut['CCPD_TH'].set_voltage(th, unit='V')
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("%f %d %f %f"%(th_meas,cnt,ave,std))

    def find_th(self,start=1.5,stop=0.5,step=-0.05,exp=100000,full_scurve=False):
        self.set_tdc(repeat=1,exp=exp,inj_width=0)
        #self.logger.info("step:%f exp:%d"%(step,exp))
        i=0
        scurve_flg=0
        th_list=np.arange(start,stop,step)
        while len(th_list)!=i:
            self.dut['CCPD_TH'].set_voltage(th_list[i], unit='V')
            d=self.get_tdc()
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            th=self.dut['CCPD_TH'].get_voltage(unit='V')
            self.logger.info("%f %d %f %f"%(th,cnt,ave,std))
            if abs(step)>abs(-0.05*0.99) and cnt>5:
                if self.debug==1:
                    print "debug change step to 0.005"
                step=-0.005
                th_list=np.arange(th-9*step,stop,step)
                i=0
            elif abs(step)>abs(-0.005*0.99) and cnt>100*0.5:
                if self.debug==1:
                    print "debug change step to 0.001"
                step=-0.001
                th_list=np.arange(th-6*step,stop,step)
                i=0
            elif abs(step)>abs(-0.001*0.99) and  cnt> 100*0.6 and scurve_flg==0:
                if full_scurve==False:
                    break
                else:
                    scurve_flg=1
            elif scurve_flg==1 and cnt==0:
                break
            else:
                i=i+1
            
    def scan_inj_tdc(self,b=1.81,e=0.0,s=-0.05,n=1,exp=100000,inj_low=0):
        self.set_tdc(repeat=n,exp=exp,inj_width=0)
        self.dut['PULSER'].set_voltage(low=inj_low, high=b,unit="V")
        self.logger.info("th cnt ave std")
        for inj in np.arange(b+s,e+s,s):
            d=self.get_tdc()
            inj_low_meas,inj_high_meas=self.dut['PULSER'].get_voltage(channel=0,unit='V')
            self.dut['PULSER'].set_voltage(low=inj_low, high=inj,unit="V")
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("%f %f %d %f %f"%(inj_low_meas,inj_high_meas,cnt,ave,std))

    def init_oscillo(self,addr="131.220.167.99"):
        sys.path.append(r"D:\workspace\hcmos\app\trunk\host\MSO4104B")
        import MSO4104B_sock
        self.m=MSO4104B_sock.Mso_sock(addr)

    def timewalk(self,inj=[1.5,1.25,1.,0.75,0.5,0.4,0.3,0.2,0.1,0.05],inj_low=0,n=10):
        th=self.dut['CCPD_TH'].get_voltage(unit='V')
        self.m.init(chs=[1,2,3,4])
        self.logger.info("th,inj,i,fname")
        for i in inj:
            self.dut["PULSER"].set_voltage(low=inj_low, high=i,unit="V")
            for j in range(n):
                f=self.m.measure()
                self.logger.info("%f %f %d %s"%(th,i,j,f))
        
    
    def spectrum(self,exp=100,interval=1):
        # reset TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['EN_INVERT_TDC']=True
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=False
        self.dut['CCPD_TDC']['ENABLE']=False
        # reset fifo
        self.dut['sram'].reset()

        self.dut['CCPD_TDC']['ENABLE']=True
        t=time.time()+exp
        while time.time()< t:
            if self.dut["sram"].get_fifo_size()==0:
                time.sleep(interval)
            else:
                d=self.dut["sram"].get_data()
                width,delay=self.analyse_tdc(d)
                self.logger.info(str(width))

    def analyse_hit(self,dat):
        dat=dat[dat & 0xF0000000==0x60000000]
        ret=np.empty([16,len(dat)],dtype=bool)
        for i in range(16):
            ret[15-i,:]= (dat & 2**i ==0)  ### the first bit goes to ret[15,0]
        ret=np.reshape(ret,len(dat)*16,order="F")
        ret=np.argwhere(ret==True)[:,0]
        if len(ret)!=0:
            frame,col,row=self._build_img(ret)
            ret=np.transpose(np.array([frame,col,row]))
        return ret

    def analyse_tdc(self,dat):
        dat=dat[dat & 0xF0000000==0x50000000]
        ret0=dat & 0x00000FFF
        ret1=np.right_shift(dat & 0x0FFFF000,12)
        return ret0,ret1
    
 
class ccpdlfB(ccpdlf):
    def __init__(self,conf=""):
        self.init_log()
        if conf=="":
            conf="ccpdlf.yaml"
        self.dut=Dut(conf)
        self.debug=0
        self._build_img=np.vectorize(self._build_img_oneB)
        self.tdac=np.zeros([24,114],int)
        self.dut.init()
        self.set_DACcurrent()
        self.power()   
     
    def set_DACcurrent(self,VN=0,VPLoad=0,VPFB=0,VNFoll=0,BLRes=0,VSTRETCH=0,WGT0=0,WGT1=0,WGT2=0,LSBdacL=0):
        self.dut['probeVN'].set_current(0,unit="uA")
        self.dut['probeVPLoad'].set_current(0,unit="uA")
        self.dut['probeVPFB'].set_current(0,unit="uA")
        self.dut['probeVNFoll'].set_current(0,unit="uA")
        self.dut['probeBLRes'].set_current(0,unit="uA")
        self.dut['probeIComp'].set_current(0,unit="uA")
        self.dut['probeVSTRETCH'].set_current(0,unit="uA")
        self.dut['probeWGT0'].set_current(0,unit="uA")
        self.dut['probeWGT1'].set_current(0,unit="uA")
        self.dut['probeWGT2'].set_current(0,unit="uA")
        self.dut['probeLSBdacL'].set_current(0,unit="uA")
        
        self.logger.info("VN:%f VPLoad:%f VPFB:%f VNFoll:%f BLRes:%f VSTRETCH:%f WGT0:%f WGT1:%f WGT2:%f LSBdacL:%f "%(
                        VN,VPLoad,VPFB,VNFoll,BLRes,VSTRETCH,WGT0,WGT1,WGT2,LSBdacL))
    def get_DACcurrent(self):
        stat={'probeVN': self.dut['probeVN'].get_voltage(unit="V"),
            'probeVN_curr': self.dut['probeVN'].get_current(unit="uA"),
            'probeVPLoad': self.dut['probeVPLoad'].get_voltage(unit="V"),
            'probeVPLoad_curr': self.dut['probeVPLoad'].get_current(unit="mA"),
            'probeVPFB': self.dut['probeVPFB'].get_voltage(unit="V"),
            'probeVNFoll': self.dut['probeVNFoll'].get_voltage(unit="V"),
            'probeVNFoll_curr': self.dut['probeVNFoll'].get_current(unit="mA"),
            'probeBLRes': self.dut['probeBLRes'].get_voltage(unit="V"),
            'probeBLRes_curr': self.dut['probeBLRes'].get_current(unit="mA"),
            'probeIComp': self.dut['probeIComp'].get_voltage(unit="V"),
            'probeIComp_curr': self.dut['probeIComp'].get_current(unit="mA"),
            'probeVSTRETCH': self.dut['probeVSTRETCH'].get_voltage(unit="V"),
            'probeVSTRETCH_curr': self.dut['probeVSTRETCH'].get_current(unit="mA"),
            'probeWGT0': self.dut['probeWGT0'].get_voltage(unit="V"),
            'probeWGT0_curr': self.dut['probeWGT0'].get_current(unit="mA"),
            'probeWGT1': self.dut['probeWGT1'].get_voltage(unit="V"),
            'probeWGT1_curr': self.dut['probeWGT1'].get_current(unit="mA"),
            'probeWGT2': self.dut['probeWGT2'].get_voltage(unit="V"),
            'probeWGT2_curr': self.dut['probeWGT2'].get_current(unit="mA"),
            'probeLSBdacL': self.dut['probeLSBdacL'].get_voltage(unit="V"),
            'probeLSBdacL_curr': self.dut['probeLSBdacL'].get_current(unit="mA")}
        return stat
    def _cal_Pixels(self,pix):
        if isinstance(pix,str):
            if pix=="all":
                en_pix=bitarray.bitarray('1'*2736)
            else:
                en_pix=bitarray.bitarray('0'*2736)
        elif isinstance(pix,int):
            if pix==0:
                en_pix=bitarray.bitarray('0'*2736)
            else:
                en_pix=bitarray.bitarray('1'*2736)
        elif isinstance(pix,type(bitarray.bitarray())):
            en_pix=bitarray.bitarray('0'*2736)
            for i in range(0,24,4):
                a0=pix[114*(i):114*(i+1)].copy()
                a1=pix[114*(i+1):114*(i+2)].copy()
                a2=pix[114*(i+2):114*(i+3)].copy()
                a3=pix[114*(i+3):114*(i+4)].copy()
                a0.reverse()
                a3.reverse()
                en_pix[114*(i):114*(i+4)]=a1+a0+a2+a3
        else:
            en_pix=bitarray.bitarray('0'*2736)
            if isinstance(pix[0],int):
                pix=[pix]
            for p in pix:
                r=p[0]%4
                if r==0:
                    en_pix[(p[0]+2)*114-p[1]-1]=1
                elif r==1:
                    en_pix[(p[0]-1)*114+p[1]]=1
                elif r==2:
                    en_pix[p[0]*114+p[1]]=1
                elif r==3:
                    en_pix[(p[0]+1)*114-p[1]-1]=1
        return en_pix
        
    def _build_img_oneB(self,spix):
            frame=spix/2736
            spix=2735-spix%2736
            col=spix/114
            row=spix%114
            if col%4==0:
                col=col+1
            elif col%4==1:
                col=col-1
                row=113-row
            elif col%4==2:
                pass
            elif col%4==3:
                row=113-row
            return frame,col,row
        
if __name__=="__main__":
    c=ccpdlf.ccpdlf()
    c.init()
    c.set_gl()



 



 
