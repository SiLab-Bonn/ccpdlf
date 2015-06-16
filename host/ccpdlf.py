
import time, string, os ,sys

import numpy as np
np.set_printoptions(linewidth="nan", threshold="nan")
import matplotlib.pyplot as plt
import bitarray
import logging

from basil.dut import Dut

  
class ccpdlf(Dut):
    def __init__(self,conf=""):
        if conf=="":
            conf="ccpdlfA.yaml"
        super(ccpdlf, self).__init__(conf)
        self.init_log()
        self.debug=0
        self._build_img=np.vectorize(self._build_img_one)
        self.tdac=np.zeros([24,114],int)
        
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

    def init(self):
        super(ccpdlf, self).init()
        self.set_DACcurrent()
        self.power()
 
        
    def power(self,pwr_en=True,Vdda=1.8,Vddp=1.5,Vddd=1.8,VCasc=1.0,BL=0.75,TH=0.80,PCBTH=1.3):    
        self['CCPD_Vdda'].set_current_limit(1000, unit='mA')
        
        self['CCPD_Vdda'].set_voltage(Vdda, unit='V')
        self['CCPD_Vdda'].set_enable(pwr_en)
        
        self['CCPD_vddaPRE'].set_voltage(Vddp, unit='V')
        self['CCPD_vddaPRE'].set_enable(pwr_en)
        
        self['CCPD_vddd'].set_voltage(Vddd, unit='V')
        self['CCPD_vddd'].set_enable(pwr_en)

        self['CCPD_VCasc'].set_voltage(VCasc, unit='V')
        self['CCPD_PCBTH'].set_voltage(PCBTH, unit='V')
        self['CCPD_BL'].set_voltage(BL, unit='V')
        self['CCPD_TH'].set_voltage(TH, unit='V')
        
        self.logger.info("Vdda:%f Vddp:%f Vddd:%f VCasc:%f BL:%f TH:%f PCBTH:%f"%(
                        Vdda,Vddp,Vddd,VCasc,BL,TH,PCBTH))
                        
    def set_DACcurrent(self,VN=0,VPLoad=0,VPFB=0,VNFoll=0,BLRes=0,IComp=0,PBIAS=0,WGT0=0,WGT1=0,WGT2=0,LSBdacL=0):
        self['probeVN'].set_current(VN,unit="uA")
        self['probeVPLoad'].set_current(VPLoad,unit="uA")
        self['probeVPFB'].set_current(VPFB,unit="uA")
        self['probeVNFoll'].set_current(VNFoll,unit="uA")
        self['probeBLRes'].set_current(BLRes,unit="uA")
        self['probeIComp'].set_current(IComp,unit="uA")
        self['probePBIAS'].set_current(PBIAS,unit="uA")
        self['probeWGT0'].set_current(WGT0,unit="uA")
        self['probeWGT1'].set_current(WGT1,unit="uA")
        self['probeWGT2'].set_current(WGT2,unit="uA")
        self['probeLSBdacL'].set_current(LSBdacL,unit="uA")
        
        self.logger.info("VN:%f VPLoad:%f VPFB:%f VNFoll:%f BLRes:%f IComp:%f PBIAS:%f WGT0:%f WGT1:%f WGT2:%f LSBdacL:%f "%(
                        VN,VPLoad,VPFB,VNFoll,BLRes,IComp,PBIAS,WGT0,WGT1,WGT2,LSBdacL)) 

    def set_pulser(self,inj_high=4.0,inj_low=0.0,period=100,repeat=1,delay=700,ext=True):
        self["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        
        self["CCPD_PULSE_INJ"].reset()
        self["CCPD_PULSE_INJ"]["REPEAT"]=repeat
        self["CCPD_PULSE_INJ"]["DELAY"]=period/2
        self["CCPD_PULSE_INJ"]["WIDTH"]=period-period/2
        self["CCPD_PULSE_INJ"]["EN"]=1
        
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["REPEAT"]=1
        self["CCPD_PULSE_GATE"]["DELAY"]=delay
        self["CCPD_PULSE_GATE"]["WIDTH"]=period*repeat+200
        self["CCPD_PULSE_GATE"]["EN"]=ext
        
        self.logger.info("inj:%.4f,%.4f period:%d repeat:%d delay:%d ext:%d"%(
            inj_high,inj_low,period,repeat,delay,int(ext)))
    def inject(self):
        self["CCPD_PULSE_INJ"].start()

    def set_th(self,TH):
        self['CCPD_TH'].set_voltage(TH, unit='V')
        THvol=self['CCPD_TH'].get_voltage(unit='V')
        self.logger.info("th_set:%f th:%f"%(TH,THvol))

    def get_status(self):
        stat={"Vdda": self['CCPD_Vdda'].get_voltage(unit='V'),
            "Vdda_curr": self['CCPD_Vdda'].get_current(unit="mA"),
            "Vddp": self['CCPD_vddaPRE'].get_voltage(unit='V'),
            "Vddp_curr": self['CCPD_vddaPRE'].get_current(unit="mA"),
            "Vddd": self['CCPD_vddd'].get_voltage(unit='V'),
            "Vddd_curr": self['CCPD_vddd'].get_current(unit="mA"),
            "VCasc": self['CCPD_VCasc'].get_voltage(unit='V'),
            "VCasc_curr": self['CCPD_VCasc'].get_current(unit="mA"),
            "PCBTH": self['CCPD_PCBTH'].get_voltage(unit='V'),
            'PCBTH_curr': self['CCPD_PCBTH'].get_current(unit="mA"),
            'BL': self['CCPD_BL'].get_voltage(unit='V'),
            'BL_curr': self['CCPD_BL'].get_current(unit="mA"),
            'TH': self['CCPD_TH'].get_voltage(unit='V'),
            'TH_curr': self['CCPD_TH'].get_current(unit="mA"),
            ##### TODO make data from get_data
            'BLRes':self['CCPD_SR']['BLRes'].tovalue(),
            'VN':self['CCPD_SR']['VN'].tovalue(),
            'VPFB':self['CCPD_SR']['VPFB'].tovalue(),
            'VPFoll':self['CCPD_SR']['VPFoll'].tovalue(),
            'VPLoad':self['CCPD_SR']['VPLoad'].tovalue(),
            'LSBdacL':self['CCPD_SR']['LSBdacL'].tovalue(),
            'IComp':self['CCPD_SR']['IComp'].tovalue(),
            'VSTRETCH':self['CCPD_SR']['VSTRETCH'].tovalue(),
            'WGT0':self['CCPD_SR']['WGT0'].tovalue(),
            'WGT1':self['CCPD_SR']['WGT1'].tovalue(),
            'WGT2':self['CCPD_SR']['WGT2'].tovalue(),
            'IDacTEST':self['CCPD_SR']['IDacTEST'].tovalue(),
            'IDacLTEST':self['CCPD_SR']['IDacLTEST'].tovalue(),
            "SW_ANA":self["CCPD_SR"]["SW_ANA"].tovalue(),
            "Pixels":" ".join(hex(ord(n)) for n in self["CCPD_SR"]["Pixels"].tobytes()),
            'CCPD_SW':self["CCPD_SW"].get_data()[0],
            'rx_SW':self["rx"].get_data()[0]
            } 
        stat.update(self.get_DACcurrent())           
        return stat
        
    def get_DACcurrent(self):
        stat={'probeVN': self['probeVN'].get_voltage(unit="V"),
            'probeVN_curr': self['probeVN'].get_current(unit="uA"),
            'probeVPLoad': self['probeVPLoad'].get_voltage(unit="V"),
            'probeVPLoad_curr': self['probeVPLoad'].get_current(unit="mA"),
            'probeVPFB': self['probeVPFB'].get_voltage(unit="V"),
            'probeVNFoll': self['probeVNFoll'].get_voltage(unit="V"),
            'probeVNFoll_curr': self['probeVNFoll'].get_current(unit="mA"),
            'probeBLRes': self['probeBLRes'].get_voltage(unit="V"),
            'probeBLRes_curr': self['probeBLRes'].get_current(unit="mA"),
            'probeIComp': self['probeIComp'].get_voltage(unit="V"),
            'probeIComp_curr': self['probeIComp'].get_current(unit="mA"),
            'probePBIAS': self['probePBIAS'].get_voltage(unit="V"),
            'probePBIAS_curr': self['probePBIAS'].get_current(unit="mA"),
            'probeWGT0': self['probeWGT0'].get_voltage(unit="V"),
            'probeWGT0_curr': self['probeWGT0'].get_current(unit="mA"),
            'probeWGT1': self['probeWGT1'].get_voltage(unit="V"),
            'probeWGT1_curr': self['probeWGT1'].get_current(unit="mA"),
            'probeWGT2': self['probeWGT2'].get_voltage(unit="V"),
            'probeWGT2_curr': self['probeWGT2'].get_current(unit="mA"),
            'probeLSBdacL': self['probeLSBdacL'].get_voltage(unit="V"),
            'probeLSBdacL_curr': self['probeLSBdacL'].get_current(unit="mA")}
        return stat

    def _write_SR(self,sw="SW_LDDAC"):
        if sw=="SW_LDDAC":
            self['CCPD_SW']['SW_LDPIX']=0
            self['CCPD_SW']['SW_LDDAC']=1
            self['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_LDPIX":
            self['CCPD_SW']['SW_LDPIX']=1
            self['CCPD_SW']['SW_LDDAC']=0
            self['CCPD_SW']['SW_HIT']=0
        elif sw=="SW_HIT":
            self['CCPD_SW']['SW_LDPIX']=0
            self['CCPD_SW']['SW_LDDAC']=0
            self['CCPD_SW']['SW_HIT']=1
        else:
            self['CCPD_SW']['SW_LDPIX']=0
            self['CCPD_SW']['SW_LDDAC']=0
            self['CCPD_SW']['SW_HIT']=0
        self['CCPD_SW'].write()

        self['CCPD_SR'].set_size(2843)
        self['CCPD_SR'].set_repeat(1)
        self['CCPD_SR'].set_wait(0)
        self['CCPD_SR'].write()
        self['CCPD_SR'].start()
        i=0
        while i<10000:
            if self['CCPD_SR'].is_done():
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        if i==10000:
            logger.info("ERROR timeout")    

    def set_global(self,BLRes=17,VN=32,VPFB=28,VPFoll=17,VPLoad=14,LSBdacL=12,IComp=17,
               VSTRETCH=15,WGT0=10,WGT1=35,WGT2=63,IDacTEST=0,IDacLTEST=0):
        self['CCPD_SR']['BLRes']=BLRes
        self['CCPD_SR']['VN']=VN
        self['CCPD_SR']['VPFB']=VPFB
        self['CCPD_SR']['VPFoll']=VPFoll
        self['CCPD_SR']['VPLoad']=VPLoad
        self['CCPD_SR']['LSBdacL']=LSBdacL
        self['CCPD_SR']['IComp']=IComp
        self['CCPD_SR']['VSTRETCH']=VSTRETCH
        self['CCPD_SR']['WGT0']=WGT0
        self['CCPD_SR']['WGT1']=WGT1
        self['CCPD_SR']['WGT2']=WGT2
        self['CCPD_SR']['IDacTEST']=IDacTEST
        self['CCPD_SR']['IDacLTEST']=IDacLTEST

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
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
        
        self['CCPD_SR']['TRIM_EN']=0
        self['CCPD_SR']['INJECT_EN']=0
        self['CCPD_SR']['MONITOR_EN']=1
        self['CCPD_SR']['PREAMP_EN']=0
        
        en_pix=self._cal_Pixels(pix)
        self['CCPD_SR']['Pixels']=en_pix

        for i in range(0,2736,114):
            self['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        
        self.preamp_en=self["CCPD_SR"]["Pixels"].copy()
        self.sw_ana=self['CCPD_SR']['SW_ANA'].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self['CCPD_SR']['TRIM_EN'].tovalue(),self['CCPD_SR']['INJECT_EN'].tovalue(),
                self['CCPD_SR']['MONITOR_EN'].tovalue(),self['CCPD_SR']['PREAMP_EN'].tovalue(),
                self['CCPD_SR']['SW_ANA'].tovalue(),
                " ".join(hex(ord(n)) for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)

    def set_preamp_en(self,pix="all"):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)

        self['CCPD_SR']['TRIM_EN']=0
        self['CCPD_SR']['INJECT_EN']=0
        self['CCPD_SR']['MONITOR_EN']=0
        self['CCPD_SR']['PREAMP_EN']=1

        en_pix=self._cal_Pixels(pix)
        self['CCPD_SR']['Pixels']=en_pix

        self._write_SR(sw="SW_LDPIX")
        
        self.preamp_en=self["CCPD_SR"]["Pixels"].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self['CCPD_SR']['TRIM_EN'].tovalue(),self['CCPD_SR']['INJECT_EN'].tovalue(),
                self['CCPD_SR']['MONITOR_EN'].tovalue(),self['CCPD_SR']['PREAMP_EN'].tovalue(),
                self['CCPD_SR']['SW_ANA'].tovalue(),
                " ".join(hex(ord(n)) for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)

    def set_inj_en(self,pix="all"):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
    
        self['CCPD_SR']['TRIM_EN']=0
        self['CCPD_SR']['INJECT_EN']=1
        self['CCPD_SR']['MONITOR_EN']=0
        self['CCPD_SR']['PREAMP_EN']=0

        en_pix=self._cal_Pixels(pix)
        self['CCPD_SR']['Pixels']=en_pix.copy()

        self._write_SR(sw="SW_LDPIX")
        
        self.inj_en=self["CCPD_SR"]["Pixels"].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self['CCPD_SR']['TRIM_EN'].tovalue(),self['CCPD_SR']['INJECT_EN'].tovalue(),
                self['CCPD_SR']['MONITOR_EN'].tovalue(),self['CCPD_SR']['PREAMP_EN'].tovalue(),
                self['CCPD_SR']['SW_ANA'].tovalue(),
                " ".join(hex(ord(n)) for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)
        
    def sel_pix(self,pix=[14,14],inj_en=1,mon_en=1,preamp_en=1,trim_en=0):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)

        self['CCPD_SR']['TRIM_EN']=0
        self['CCPD_SR']['INJECT_EN']=inj_en
        self['CCPD_SR']['MONITOR_EN']=mon_en
        self['CCPD_SR']['PREAMP_EN']=preamp_en
        en_pix=self._cal_Pixels(pix)
        self['CCPD_SR']['Pixels']=en_pix
        if mon_en==1:
            for i in range(0,2736,114):
                self['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        s="pix:%s inj_en:%d mon_en:%d preamp_en:%d"%(str(pix),inj_en,mon_en,preamp_en)
        self.logger.info(s)


    def set_tdc(self,repeat=100,inj_width=50,delay=10,inj_high=1.0):
        # set gpio
        self['rx']['FE'] = 0
        self['rx']['TLU'] = 0
        self['rx']['CCPD_TDC'] = 1
        self['rx']['CCPD_RX'] = 0
        self['rx'].write()
        
        self['CCPD_SW']['SW_LDPIX']=0
        self['CCPD_SW']['SW_LDDAC']=0
        self['CCPD_SW']['SW_HIT']=0
        self['CCPD_SW'].write()
        
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)

        # set pulser
        self["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self["CCPD_Injection_low"].set_voltage(0,unit="V")
        
        self["CCPD_PULSE_INJ"].reset()
        if inj_width==0:
            self["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self["CCPD_PULSE_INJ"]["REPEAT"]=repeat
            self["CCPD_PULSE_INJ"]["DELAY"]=inj_width
            self["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self["CCPD_PULSE_INJ"]["EN"]=1
            exp=inj_width*2*repeat+10
        
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["REPEAT"]=1
        self["CCPD_PULSE_GATE"]["DELAY"]=delay
        self["CCPD_PULSE_GATE"]["WIDTH"]=exp
        self["CCPD_PULSE_GATE"]["EN"]=1 

        # reset TDC
        self["CCPD_TDC"].reset()
        self['CCPD_TDC']['EN_INVERT_TDC']=True
        self['CCPD_TDC']['ENABLE_EXTERN']=True
        self['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self['sram'].reset()

        s="exp:%d repeat:%d inj_width:%d delay:%d"%(
            exp,repeat,inj_width,delay)
        self.logger.info(s)
        
    def get_tdc(self):
        self['sram'].reset()
        self["CCPD_PULSE_GATE"].start()
        i=0
        while i<10000:
            if self['CCPD_PULSE_GATE'].is_done():
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        if i==10000:
            self.logger.info("ERROR timeout")
        return self['sram'].get_data()

    def scan_th_tdc(self,b=1.1,e=0.7,s=-0.01,n=100,inj_high=1):
        self.set_tdc(repeat=n,inj_high=inj_high)
        self['CCPD_TH'].set_voltage(b, unit='V')
        self.logger.info("th cnt ave std")
        for th in np.arange(b+s,e+s,s):
            d=self.get_tdc()
            th_meas=self['CCPD_TH'].get_voltage(unit='V')
            self['CCPD_TH'].set_voltage(th, unit='V')
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("%f %d %f %f"%(th_meas,cnt,ave,std))
            
    def scan_inj_tdc(self,b=1.81,e=0.0,s=-0.05,n=100):
        self.set_tdc(repeat=n,inj_high=b)
        self.logger.info("th cnt ave std")
        for inj in np.arange(b+s,e+s,s):
            d=self.get_tdc()
            inj_low_meas,inj_high_meas=self['PULSER'].get_voltage(channel=0,unit='V')
            self["CCPD_Injection_high"].set_voltage(inj,unit="V")
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("%f %f %d %f %f"%(inj_low_meas,inj_high_meas,cnt,ave,std))


    def analyse_tdc(self,dat):
        dat=dat[dat & 0xF0000000==0x50000000]
        ret0=dat & 0x00000FFF
        ret1=np.right_shift(dat & 0x0FFFF000,12)
        return ret0,ret1
    
    def favorit1(self):
        self.set_mon_en("none")
        self.set_inj_en([14,14])
        self.set_preamp([14,14])
        self.set_global(WGT0=63)
        self.set_th(1.0)
        self.set_pulser()
 
    def favorit2(self):
        c.init()
        c.set_global(WGT0=63)
        c.set_th(0.753)
        c.sel_pix([14,14])
        c.scan_inj_tdc()

 
class ccpdlfB(ccpdlf):
    def __init__(self,conf=""):
        self.init_log()
        if conf=="":
            conf="ccpdlf.yaml"
        super(ccpdlf, self).__init__(conf)
        self.debug=2
        self._build_img=np.vectorize(self._build_img_oneB)
    def set_DACcurrent(self,VN=0,VPLoad=0,VPFB=0,VNFoll=0,BLRes=0,IComp=0,VSTRETCH=0,WGT0=0,WGT1=0,WGT2=0,LSBdacL=0):
        self['probeVN'].set_current(VN,unit="uA")
        self['probeVPLoad'].set_current(VPLoad,unit="uA")
        self['probeVPFB'].set_current(VPFB,unit="uA")
        self['probeVNFoll'].set_current(VNFoll,unit="uA")
        self['probeBLRes'].set_current(BLRes,unit="uA")
        self['probeIComp'].set_current(IComp,unit="uA")
        self['probeVSTRETCH'].set_current(VSTRETCH,unit="uA")
        self['probeWGT0'].set_current(WGT0,unit="uA")
        self['probeWGT1'].set_current(WGT1,unit="uA")
        self['probeWGT2'].set_current(WGT2,unit="uA")
        self['probeLSBdacL'].set_current(LSBdacL,unit="uA")
        
        self.logger.info("VN:%f VPLoad:%f VPFB:%f VNFoll:%f BLRes:%f IComp:%f VSTRETCH:%f WGT0:%f WGT1:%f WGT2:%f LSBdacL:%f "%(
                        VN,VPLoad,VPFB,VNFoll,BLRes,IComp,VSTRETCH,WGT0,WGT1,WGT2,LSBdacL))
    def get_DACcurrent(self):
        stat={'probeVN': self['probeVN'].get_voltage(unit="V"),
            'probeVN_curr': self['probeVN'].get_current(unit="uA"),
            'probeVPLoad': self['probeVPLoad'].get_voltage(unit="V"),
            'probeVPLoad_curr': self['probeVPLoad'].get_current(unit="mA"),
            'probeVPFB': self['probeVPFB'].get_voltage(unit="V"),
            'probeVNFoll': self['probeVNFoll'].get_voltage(unit="V"),
            'probeVNFoll_curr': self['probeVNFoll'].get_current(unit="mA"),
            'probeBLRes': self['probeBLRes'].get_voltage(unit="V"),
            'probeBLRes_curr': self['probeBLRes'].get_current(unit="mA"),
            'probeIComp': self['probeIComp'].get_voltage(unit="V"),
            'probeIComp_curr': self['probeIComp'].get_current(unit="mA"),
            'probeVSTRETCH': self['probeVSTRETCH'].get_voltage(unit="V"),
            'probeVSTRETCH_curr': self['probeVSTRETCH'].get_current(unit="mA"),
            'probeWGT0': self['probeWGT0'].get_voltage(unit="V"),
            'probeWGT0_curr': self['probeWGT0'].get_current(unit="mA"),
            'probeWGT1': self['probeWGT1'].get_voltage(unit="V"),
            'probeWGT1_curr': self['probeWGT1'].get_current(unit="mA"),
            'probeWGT2': self['probeWGT2'].get_voltage(unit="V"),
            'probeWGT2_curr': self['probeWGT2'].get_current(unit="mA"),
            'probeLSBdacL': self['probeLSBdacL'].get_voltage(unit="V"),
            'probeLSBdacL_curr': self['probeLSBdacL'].get_current(unit="mA")}
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
    c=ccpdlf()
    c.init()
    c.set_global()
    c.sel_pix()
    c.scan_th_tdc()



 



 
