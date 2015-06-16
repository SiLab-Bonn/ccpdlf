
import time, string, os ,sys

import numpy as np
np.set_printoptions(linewidth="nan", threshold="nan")
import matplotlib.pyplot as plt
import bitarray

from basil.dut import Dut

class Log():
    def __init__(self,logfile='ccpdlf.log'):
        self.logfile=logfile
    def info(self,s):
        print s
        s.replace("\n","")
        with open(self.logfile,"a") as f:
            f.write("%s %s\n"%(time.strftime("%Y/%m/%d-%H:%M:%S"),s))
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
        
class ccpdlf(Dut):
    def __init__(self,conf=""):
        if conf=="":
            conf="ccpdlf.yaml"
        super(ccpdlf, self).__init__(conf)
        self.init_log()
        self.debug=0
        self._build_img=np.vectorize(self._build_img_one)
        self.tdac=np.zeros([24,114],int)
        # init member variables
        self.plot=False     
    def init_log(self,logfile='ccpdlf.log'):
        self.logger=Log()
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
    def init(self):
        super(ccpdlf, self).init()
        self.set_DACcurrent()
        self.power()
        self.set_global()
        self.set_mon_en([14,14])
        self.set_preamp_en([14,14])
        self.set_inj_en([14,14])
        self.set_tdac(0)
        self.set_th(1.5) 
    def power(self,pwr_en=True,Vdda=1.8,Vddp=1.5,Vddd=1.8,VCasc=1.0,BL=0.75,TH=0.80,PCBTH=1.3,CCPD_ADCref=0.7):    
        self['CCPD_Vdda'].set_current_limit(204, unit='mA')
        
        self['CCPD_Vdda'].set_voltage(Vdda, unit='V')
        self['CCPD_Vdda'].set_enable(pwr_en)
        
        self['CCPD_vddaPRE'].set_voltage(Vddp, unit='V')
        self['CCPD_vddaPRE'].set_enable(pwr_en)
        
        self['CCPD_vddd'].set_voltage(Vddd, unit='V')
        self['CCPD_vddd'].set_enable(pwr_en)

        self['CCPD_VCasc'].set_voltage(VCasc, unit='V')
        self['CCPD_VCasc'].set_enable(pwr_en)
        
        self['CCPD_PCBTH'].set_voltage(PCBTH, unit='V')
        self['CCPD_BL'].set_voltage(BL, unit='V')
        self['CCPD_TH'].set_voltage(TH, unit='V')
        self['CCPD_ADCref'].set_voltage(CCPD_ADCref, unit='V')
        
        self.logger.info("Vdda:%f Vddp:%f Vddd:%f VCasc:%f BL:%f TH:%f PCBTH:%f"%(
                        Vdda,Vddp,Vddd,VCasc,BL,TH,PCBTH))
    def set_DACcurrent(self,VN=0,VPLoad=0,VPFB=0,VNFoll=0,BLRes=0,IComp=0,PBIAS=0,WGT0=0,WGT1=0,WGT2=0,LSBdacL=0):
        self['probeVN'].set_current(0,unit="uA")
        self['probeVPLoad'].set_current(0,unit="uA")
        self['probeVPFB'].set_current(0,unit="uA")
        self['probeVNFoll'].set_current(0,unit="uA")
        self['probeBLRes'].set_current(0,unit="uA")
        self['probeIComp'].set_current(0,unit="uA")
        self['probeVSTRETCH'].set_current(0,unit="uA")
        self['probeWGT0'].set_current(0,unit="uA")
        self['probeWGT1'].set_current(0,unit="uA")
        self['probeWGT2'].set_current(0,unit="uA")
        self['probeLSBdacL'].set_current(0,unit="uA")
        self.logger.info("VN:%f VPLoad:%f VPFB:%f VNFoll:%f BLRes:%f IComp:%f PBIAS:%f WGT0:%f WGT1:%f WGT2:%f LSBdacL:%f "%(
                        VN,VPLoad,VPFB,VNFoll,BLRes,IComp,PBIAS,WGT0,WGT1,WGT2,LSBdacL)) 
    def set_inj(self,inj_high=4.0,inj_low=0.0,inj_width=50,inj_n=1,delay=700,ext=True):
        self["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        
        self["CCPD_PULSE_INJ"].reset()
        self["CCPD_PULSE_INJ"]["REPEAT"]=inj_n
        self["CCPD_PULSE_INJ"]["DELAY"]=inj_width
        self["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self["CCPD_PULSE_INJ"]["EN"]=1
        
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["REPEAT"]=1
        self["CCPD_PULSE_GATE"]["DELAY"]=delay
        self["CCPD_PULSE_GATE"]["WIDTH"]=inj_n*inj_width*2+10
        self["CCPD_PULSE_GATE"]["EN"]=ext
        self.logger.info("inj:%.4f,%.4f inj_width:%d inj_n:%d delay:%d ext:%d"%(
            inj_high,inj_low,inj_width,inj_n,delay,int(ext)))
    def set_pulser(inj_high=1,inj_low=0.0,burst=True):
        self["PULSER"].set_voltage(0,inj_high,inj_low)
    def inject(self):
        self["CCPD_PULSE_INJ"].start()
    def set_th(self,TH,thmod=False):
        self['CCPD_TH'].set_voltage(TH, unit='V')
        THvol=self['CCPD_TH'].get_voltage(unit='V')
        self['CCPD_SW']['THON_NEG']=1
        self['CCPD_SW'].write()
        self.logger.info("th_set:%f th:%f th_mod:%d"%(TH,THvol,thmod))
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
            self.logger.info("ERROR timeout")    
    def set_global(self,BLRes=17,VN=32,VPFB=28,VPFoll=17,VPLoad=14,LSBdacL=12,IComp=17,
               VSTRETCH=15,WGT0=10,WGT1=35,WGT2=63,IDacTEST=0,IDacLTEST=0):
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
        
        self["CCPD_PULSE_GATE"].reset()
        self['CCPD_PULSE_GATE'].set_en(False)
        
        self["CCPD_PULSE_INJ"].reset()
        self['CCPD_PULSE_INJ'].set_en(False)

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

        self._write_SR(sw="SW_LDDAC")

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
        
        self["CCPD_PULSE_GATE"].reset()
        self['CCPD_PULSE_GATE'].set_en(False)
        
        self["CCPD_PULSE_INJ"].reset()
        self['CCPD_PULSE_INJ'].set_en(False)
        
        self['CCPD_SR']['TRIM_EN']=0
        self['CCPD_SR']['INJECT_EN']=0
        self['CCPD_SR']['MONITOR_EN']=1
        self['CCPD_SR']['PREAMP_EN']=0
        
        en_pix=self._cal_Pixels(pix)
        self['CCPD_SR']['Pixels']=en_pix

        for i in range(0,2736,114):
            self['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        
        self.mon_en=self["CCPD_SR"]["Pixels"].copy()
        self.sw_ana=self['CCPD_SR']['SW_ANA'].copy()
        s="pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self['CCPD_SR']['TRIM_EN'].tovalue(),self['CCPD_SR']['INJECT_EN'].tovalue(),
                self['CCPD_SR']['MONITOR_EN'].tovalue(),self['CCPD_SR']['PREAMP_EN'].tovalue(),
                self['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)
    def set_preamp_en(self,pix="all"):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
        
        self["CCPD_PULSE_GATE"].reset()
        self['CCPD_PULSE_GATE'].set_en(False)
        
        self["CCPD_PULSE_INJ"].reset()
        self['CCPD_PULSE_INJ'].set_en(False)

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
                self['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)
    def set_inj_en(self,pix="all"):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
        
        self["CCPD_PULSE_GATE"].reset()
        self['CCPD_PULSE_GATE'].set_en(False)
        
        self["CCPD_PULSE_INJ"].reset()
        self['CCPD_PULSE_INJ'].set_en(False)
    
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
                self['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)        
    def set_tdac(self,tdac):
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)
        
        self["CCPD_PULSE_GATE"].reset()
        self['CCPD_PULSE_GATE'].set_en(False)
        
        self["CCPD_PULSE_INJ"].reset()
        self['CCPD_PULSE_INJ'].set_en(False)
    
        self['CCPD_SR']['INJECT_EN']=0
        self['CCPD_SR']['MONITOR_EN']=0
        self['CCPD_SR']['PREAMP_EN']=0
        self['CCPD_SR']['SW_ANA']=self.sw_ana
        
        if isinstance(tdac, int):
            tdac=np.ones([24,114],int)*tdac
       
        for i_trim in [1,2,4,8]:
            pix=bitarray.bitarray(((np.reshape(tdac, 114*24) & i_trim) !=0).tolist())
            en_pix=self._cal_Pixels(pix)
            self['CCPD_SR']['Pixels']=en_pix
            self['CCPD_SR']['TRIM_EN']=i_trim
            self._write_SR(sw="SW_LDPIX")
            
        np.argwhere(self.tdac!=tdac)
        s="tdac:"
        for p in np.argwhere(self.tdac!=tdac):
            s="%s,[%d,%d]=%d"%(s,p[0],p[1],tdac[p[0],p[1]])
        self.logger.info(s)
        self.tdac=np.copy(tdac)
    def set_hit(self,repeat=100,delay=10,inj_width=50,gate_width=-1,thon=True,inj_high=4):
        # set gpio
        self['rx']['NC'] = 0
        self['rx']['TLU'] = 0
        self['rx']['CCPD_TDC'] = 0
        self['rx']['CCPD_RX'] = 1
        self['rx'].write()
        
        if gate_width==-1:
            gate_width=inj_width*2+250
        sr_wait=gate_width+100
        
        self["CCPD_PULSE_THON"].reset()
        if thon==True:
            self["CCPD_PULSE_THON"].set_delay(delay)
            self["CCPD_PULSE_THON"].set_repeat(1)
            self["CCPD_PULSE_THON"].set_width(gate_width-delay-5)
            self["CCPD_PULSE_THON"].set_en(1)
        else:
            self["CCPD_PULSE_THON"].set_en(0)
        
        # reset spi
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate first
        self["CCPD_SR"].reset()
        self["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        self["CCPD_SR"].set_size(2736)
        self["CCPD_SR"].set_repeat(repeat)
        self["CCPD_SR"].set_wait(sr_wait)
        
        ## set LD switches
        self['CCPD_SW']['SW_LDPIX']=0
        self['CCPD_SW']['SW_LDDAC']=0
        if thon==True:
            self['CCPD_SW']['THON_NEG']=0
        else:
            self['CCPD_SW']['THON_NEG']=1
        self["CCPD_SW"]["SW_HIT"]=1
        self['CCPD_SW'].write()
        
        # set pulser
        self["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self["CCPD_Injection_low"].set_voltage(0,unit="V")
        self.inj_low=0
        
        self["CCPD_PULSE_INJ"].reset()
        if inj_width==0:
           self["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self["CCPD_PULSE_INJ"]["REPEAT"]=1
            self["CCPD_PULSE_INJ"]["DELAY"]=inj_width
            self["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self["CCPD_PULSE_INJ"]["EN"]=1
        
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["REPEAT"]=1
        self["CCPD_PULSE_GATE"]["DELAY"]=delay
        self["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self["CCPD_PULSE_GATE"]["EN"]=1
        
        # set TDC
        self["CCPD_TDC"].reset()
        self['CCPD_TDC']['ENABLE_EXTERN']=False
        self['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self['sram'].reset()
        
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(True)
        
        s="repeat:%d delay:%d inj_width:%d gate_width:%d"%(
            repeat,delay,inj_width,gate_width)
        self.logger.info(s)
    def set_hit_source(self,delay=10,close_delay=10,thmod_delay=10):
        # set gpio
        self['rx']['NC'] = 0
        self['rx']['TLU'] = 0
        self['rx']['CCPD_TDC'] = 0
        self['rx']['CCPD_RX'] = 1
        self['rx'].write()
        
        self["CCPD_PULSE_THON"].reset()
        if thmod_delay==-1:
            self["CCPD_PULSE_THON"]["EN"]=0
        else:
            self["CCPD_PULSE_THON"]["DELAY"]=1
            self["CCPD_PULSE_THON"]["REPEAT"]=1
            self["CCPD_PULSE_THON"]["WIDTH"]=2736+delay+thmod_delay
            self["CCPD_PULSE_THON"]["EN"]=1
        
        # reset spi
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate first
        self["CCPD_SR"].reset()
        self["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        #set spi
        self["CCPD_SR"].set_size(2736)
        self["CCPD_SR"].set_repeat(1)
        self["CCPD_SR"].set_wait(0)
        self["CCPD_SR"].set_en(1)
        
        ## set LD switches
        self['CCPD_SW']['SW_LDPIX']=0
        self['CCPD_SW']['SW_LDDAC']=0
        self['CCPD_SW']['THON_NEG']=1
        self['CCPD_SW']['GATE_NEG']=1 ## GATE will be trigged by negative edge of RX0
        self["CCPD_SW"]["SW_HIT"]=1
        self['CCPD_SW'].write()
        
        # set inj amplitude 0
        self["CCPD_Injection_high"].set_voltage(0,unit="V")
        self.inj_high=0
        self["CCPD_Injection_low"].set_voltage(0,unit="V")
        self.inj_low=0
        # disable inj
        self["CCPD_PULSE_INJ"].reset()
        self["CCPD_PULSE_INJ"]["EN"]=0
        
        # set gate
        self["CCPD_PULSE_GATE"].reset()
        self["CCPD_PULSE_GATE"]["REPEAT"]=1
        self["CCPD_PULSE_GATE"]["DELAY"]=close_delay
        self["CCPD_PULSE_GATE"]["WIDTH"]=2740+delay
        self["CCPD_PULSE_GATE"]["EN"]=1
        
        # disable TDC
        self["CCPD_TDC"].reset()
        self['CCPD_TDC']['ENABLE_EXTERN']=False
        self['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self['sram'].reset()
        
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(True)
        
        s="delay:%d close_delay:%d thmod_delay:%d"%(delay,close_delay,thmod_delay)
        self.logger.info(s)
    def set_tdc(self,exp=100,repeat=100,inj_width=50,delay=10,inj_high=4):
        # set gpio
        self['rx']['NC'] = 0
        self['rx']['TLU'] = 0
        self['rx']['CCPD_TDC'] = 1
        self['rx']['CCPD_RX'] = 0
        self['rx'].write()
        
        self['CCPD_SW']['SW_LDPIX']=0
        self['CCPD_SW']['SW_LDDAC']=0
        self['CCPD_SW']['SW_HIT']=0
        self["CCPD_SW"]['THON_NEG']=1
        self['CCPD_SW'].write()
        
        # reset rx
        self['CCPD_SPI_RX'].reset()
        self['CCPD_SPI_RX'].set_en(False)

        # set pulser
        self["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self["CCPD_Injection_low"].set_voltage(0,unit="V")
        self.inj_low=0
        
        self["CCPD_PULSE_INJ"].reset()
        if inj_width==0:
            self["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self["CCPD_PULSE_INJ"]["REPEAT"]=repeat
            self["CCPD_PULSE_INJ"]["DELAY"]=inj_width
            self["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self["CCPD_PULSE_INJ"]["EN"]=1
            exp=max(inj_width*2*repeat+10,exp)
        
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
    def get_hit(self):
        self['sram'].reset()
        self["CCPD_SR"].start()
        wait=self["CCPD_SR"].get_wait()
        repeat=self["CCPD_SR"].get_repeat()
        i=0
        while not self['CCPD_SR'].is_done():
            if i>10000+wait*repeat/1000:
                self.logger.info("ERROR timeout")
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        return self['sram'].get_data()
    def tune_tdac(self,n=100,exp=9900,LSBdacL=63,th=0.725,thmod=True,th_cnt=5):
        self.set_th(th,thmod=thmod)
        self.set_global(WGT0=0,WGT1=0,WGT2=0,LSBdacL=LSBdacL)
        #tdac=np.ones([24,114],int)*7
        tdac=np.copy(self.tdac)
        for i in range(24):
            flg=np.ones(114)*-1
            ret=np.zeros([114,16])
            for t in np.arange(15,-1,-1):
                for j in range(114):
                    if flg[j]==-1:
                        tdac[i,j]=t
                self.set_tdac(tdac)
                self.set_preamp_en("all")
                self.set_inj_en("none")
                self.set_mon_en([14,14])
                self.set_hit(gate_width=exp,inj_width=0,repeat=n,delay=10,thon=thmod)
                d=self.analyse_hit(self.get_hit(),fmt="img")
                ret[:,t]=d[i,:]
                for j in range(114):
                    self.logger.info("%d-%d,%d,%d,%d"%(i,j,flg[j],tdac[i,j],d[i,j]))
                    if d[i,j]>th_cnt and flg[j]==-1:
                        flg[j]=t
                        tdac[i,j]=min(15,t+1)
            if self.plot==True:
                    self.ax[1].pcolor(d,vmax=100,vmin=0)
                    self.ax[0].pcolor(tdac,vmax=15,vmin=0)
                    plt.pause(0.001)
    def tune_tdac_fast(self,n=100,th_cnt=5,exp=9900,LSBdacL=63,th=0.725,thmod=True):
        th_cnt=n/2
        self.set_th(th,thmod=thmod)
        self.set_global(WGT0=0,WGT1=0,WGT2=0,LSBdacL=LSBdacL)
        tdac=np.ones([24,114],int)*7
        flg=np.zeros([24,114],int)
        for t in np.arange(16):
            self.set_tdac(tdac)
            self.set_hit(gate_width=exp,inj_width=0,repeat=n,delay=10,thon=True)
            cnt=self.analyse_hit(self.get_hit(),"img")
            if self.plot==True:
                ax[1].pcolor(cnt,vmax=n,vmin=0)
                ax[0].pcolor(tdac,vmax=15,vmin=0)
                plt.pause(0.001)
            for i in range(24):
                for j in range(114):
                    if flg[i,j]==1:
                        pass
                    elif tdac[i,j]==7:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=15
                        else:
                            tdac[i,j]=0
                    elif tdac[i,j]==15:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=15
                            flg[i,j]=1
                        else:
                            tdac[i,j]=11
                    elif tdac[i,j]==11:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=13
                        else:
                            tdac[i,j]=9
                    elif tdac[i,j]==13:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=14
                        else:
                            tdac[i,j]=12
                    elif tdac[i,j]==14:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=15
                            flg[i,j]=1
                        else:
                            tdac[i,j]=14
                            flg[i,j]=1
                    elif tdac[i,j]==12:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=13
                            flg[i,j]=1
                        else:
                            tdac[i,j]=12
                    elif tdac[i,j]==9:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=10
                        else:
                            tdac[i,j]=8
                    elif tdac[i,j]==10:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=11
                            flg[i,j]=1
                        else:
                            tdac[i,j]=10
                            flg[i,j]=1
                    elif tdac[i,j]==8:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=9
                            flg[i,j]=1
                        else:
                            tdac[i,j]=8
                            flg[i,j]=1
                    elif tdac[i,j]==0:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=3
                        else:
                            tdac[i,j]=0
                            flg[i,j]=1
                    elif tdac[i,j]==3:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=5
                        else:
                            tdac[i,j]=1
                    elif tdac[i,j]==5:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=6
                        else:
                            tdac[i,j]=4
                    elif tdac[i,j]==6:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=7
                            flg[i,j]=1
                        else:
                            tdac[i,j]=6
                            flg[i,j]=1
                    elif tdac[i,j]==4:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=5
                            flg[i,j]=1
                        else:
                            tdac[i,j]=4
                            flg[i,j]=1
                    elif tdac[i,j]==1:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=2
                        else:
                            tdac[i,j]=1
                            flg[i,j]=1
                    elif tdac[i,j]==2:
                        if cnt[i,j]>th_cnt:
                            tdac[i,j]=3
                            flg[i,j]=1
                        else:
                            tdac[i,j]=2
                            flg[i,j]=1
    def tune_tdac_mod(self,exp=9900,thmod=True,th_cnt=5):
        tdac=np.copy(self.tdac)
        flg=np.ones([24,114])*2
        for t in range(100):
            self.set_tdac(tdac)
            self.set_hit(gate_width=exp,inj_width=0,repeat=100,delay=10,thon=thmod) 
            d=self.analyse_hit(self.get_hit(),"img")
            if self.plot==True:
                ax[1].pcolor(d,vmax=100,vmin=0)
                ax[0].pcolor(tdac,vmax=15,vmin=0)
                plt.pause(0.001)
            p=0
            for i in range(23,-1,-1):
                for j in range(114):
                    if d[i,j]>th_cnt:
                        if tdac[i,j]==15:
                            flg[i,j]=0  ### almost
                        else:
                            tdac[i,j]=tdac[i,j]+1
                            flg[i,j]=1
                            p=p+1 
                    elif flg[i,j]==0:
                        pass
                    elif flg[i,j]==1:
                        flg[i,j]=0
                    elif tdac[i,j]==0: #flg==2
                        flg[i,j]=0
                    else:
                        tdac[i,j]=tdac[i,j]-1
                        p=p-1
                if abs(p)>114:
                    break
            if len(np.argwhere(flg!=0))<10:
                break
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
    def scan_th(self,b=0.78,e=0.7,s=-0.01,n=250,exp=9900,inj_width=0,save=True,thon=True):
        self.set_preamp_en("all")
        self.set_inj_en("none")
        self.set_mon_en([14,14])
        self.set_hit(gate_width=exp,inj_width=inj_width,repeat=n,delay=10,thon=thon)
        self['CCPD_TH'].set_voltage(b, unit='V')
        if save==True:
            fname=time.strftime("hit_%y%m%d-%H%M%S.npy")
            self.logger.info("fname:%s"%fname)
            with open(fname,"ab+") as f:
                np.save(f,np.arange(b,e,s))
        for th in np.arange(b+s,e+s,s):
            d=self.get_hit()
            th_meas=self['CCPD_TH'].get_voltage(unit='V')
            self['CCPD_TH'].set_voltage(th, unit='V')
            d=self.analyse_hit(d,"img")
            if self.plot==True:
                self.ax[0].pcolor(d,vmin=0)
                plt.pause(0.001)
            self.logger.info("%f,%d,%d"%(th_meas,np.sum(d),d[14,14]))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
    def scan_source(self,n=1000,exp=9900,inj_width=0,save=True,thon=True):
        if self.plot==True:
           img=np.zeros([24,114])
        self.set_preamp_en("all")
        self.set_inj_en("none")
        self.set_mon_en("none")
        self.set_hit(gate_width=exp,inj_width=inj_width,repeat=250,delay=10,thon=thon)
        if save==True:
            fname=time.strftime("source_%y%m%d-%H%M%S.npy")
            self.logger.info("fname:%s"%fname)
        i=0
        while i <n:
            d=self.analyse_hit(self.get_hit(),"zs")
            if self.plot==True:
                ax[0].pcolor(d,vmin=0)
                plt.pause(0.001)
            self.logger.info("%f,%d"%(i,len(d)))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
            i=i+1
    def scan_th_tdc(self,b=1.1,e=0.7,s=-0.01,n=1,exp=100000,pix=[14,14]):
        self.set_tdc(repeat=n,exp=exp,inj_width=0)
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
    def find_th_tdc(self,start=1.5,stop=0.5,step=-0.05,exp=100000,full_scurve=False):
        self.set_tdc(repeat=1,exp=exp,inj_width=0)
        #self.logger.info("step:%f exp:%d"%(step,exp))
        i=0
        scurve_flg=0
        th_list=np.arange(start,stop,step)
        while len(th_list)!=i:
            self['CCPD_TH'].set_voltage(th_list[i], unit='V')
            d=self.get_tdc()
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            th=self['CCPD_TH'].get_voltage(unit='V')
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
        self['PULSER'].set_voltage(low=inj_low, high=b,unit="V")
        self.logger.info("th cnt ave std")
        for inj in np.arange(b+s,e+s,s):
            d=self.get_tdc()
            inj_low_meas,inj_high_meas=self['PULSER'].get_voltage(channel=0,unit='V')
            self['PULSER'].set_voltage(low=inj_low, high=inj,unit="V")
            width,delay=self.analyse_tdc(d)
            cnt=len(width)
            ave=np.average(width)
            std=np.std(width)
            self.logger.info("%f %f %d %f %f"%(inj_low_meas,inj_high_meas,cnt,ave,std))
    def spectrum(self,exp=100,interval=1):
        # reset TDC
        self["CCPD_TDC"].reset()
        self['CCPD_TDC']['EN_INVERT_TDC']=True
        self['CCPD_TDC']['ENABLE_EXTERN']=False
        self['CCPD_TDC']['ENABLE']=False
        # reset fifo
        self['sram'].reset()

        self['CCPD_TDC']['ENABLE']=True
        t=time.time()+exp
        while time.time()< t:
            if self["sram"].get_fifo_size()==0:
                time.sleep(interval)
            else:
                d=self["sram"].get_data()
                width,delay=self.analyse_tdc(d)
                self.logger.info(str(width))
    def analyse_hit(self,dat,fmt="zs"):
        dat=dat[dat & 0xF0000000==0x60000000]
        ret=np.empty([16,len(dat)],dtype=bool)
        for i in range(16):
            ret[15-i,:]= (dat & 2**i ==0)  ### the first bit goes to ret[15,0]
        ret=np.reshape(ret,len(dat)*16,order="F")
        if fmt=="zs":
          ret=np.argwhere(ret==True)[:,0]
          if len(ret)!=0:
            frame,col,row=self._build_img(ret)
            ret=np.transpose(np.array([frame,col,row]))
            return ret
          else:
            return np.array([])
        else:    ##### TODO can be more efficient
            img=np.zeros([24,114])
            for i in range(0,len(ret),2736):
              img=np.add(img,self._build_img2(ret[i:i+2736][::-1]))
            return img
    def save_hit(self,dat):
        tmp=np.empty(len(dat),dtype=[("col","i4"),("row","i4")])
        tmp["col"]=dat[:,1]
        tmp["row"]=dat[:,2]
        u=np.unique(tmp,return_counts=True)
        ret=np.empty(len(u[0]),dtype=[("col","i4"),("row","i4"),("cnt","i4")])
        ret["col"]=u[0]["col"]
        ret["row"]=u[0]["row"]
        ret["cnt"]=u[1]
        c.logger.info("hit:%s"%str(ret))
        return ret
    def analyse_tdc(self,dat):
        dat=dat[dat & 0xF0000000==0x50000000]
        ret0=dat & 0x00000FFF
        ret1=np.right_shift(dat & 0x0FFFF000,12)
        return ret0,ret1
    def init_plot(self):
        self.plot=True
        plt.ion()
        fig,self.ax=plt.subplots(2)
        plt.pause(0.001)
        self.ax[0].autoscale(False)
        self.ax[1].autoscale(False)
        self.ax[0].set_xbound(0,114)
        self.ax[0].set_ybound(0,24)
        self.ax[1].set_xbound(0,114)
        self.ax[1].set_ybound(0,24)

class ccpdlfB(ccpdlf):
    def __init__(self,conf=""):
        self.init_log()
        if conf=="":
            conf="ccpdlf.yaml"
        super(ccpdlf, self).__init__(conf)
        self.debug=2
        self._build_img=np.vectorize(self._build_img_oneB)
        self.tdac=np.zeros([24,114],int)

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
        
    def _build_img2(self,dat):
        img=np.empty([24,114],dtype=int)
        for i in range(0,24,4):
            img[i,:]=np.copy(dat[(i+1)*114:(i+2)*114][::-1])
            img[i+1,:]=np.copy(dat[i*114:(i+1)*114])
            img[i+2,:]=np.copy(dat[(i+2)*114:(i+3)*114])
            img[i+3,:]=np.copy(dat[(i+3)*114:(i+4)*114][::-1])
        return img
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



 



 
