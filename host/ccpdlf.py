
import time, string, os ,sys

import numpy as np
np.set_printoptions(linewidth="nan", threshold="nan")
import matplotlib.pyplot as plt
import bitarray

import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)


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
        
class ccpdlfA():
    def __init__(self,conf=""):
        self.logger=Log()
        if conf=="":
            conf="ccpdlf.yaml"
        self.dut=Dut(conf)
        self.debug=0
        self._build_img=np.vectorize(self._build_img_one)
        self.tdac=np.zeros([24,114],int)
        # init member variables
        self.plot=False
        # init dut
        self.dut.init()
        self.power()
        self.set_global()
        ### do not change the order of mon,preamp,inj
        self.set_mon_en([14,14])
        self.set_preamp_en([14,14])
        self.set_inj_en([14,14])
        self.set_tdac(0)
        self.set_th(1.5)
        self.set_inj_all()
    def init_eudaq(self,addr):
        path="/home/user/Documents/eudaq-1.4-dev-testbeam/python"
        if not path in sys.path:
            sys.path.append(path)
        from PyEUDAQWrapper import PyProducer
        self.prod=PyProducer("ccpdlf",addr)
    def run_eudaq(self,mode="tlu",save=True):
        from StandardEvent_pb2 import StandardEvent
        while True:
            # check if configuration received
            if self.prod.Configuring:
                self.logger.info("run_eudaq Configuring")
                #self.prod.StartingRun = False
                self.prod.Configuring = True
            # check if we are starting:
            if self.prod.StartingRun:
                run=self.prod.GetConfigParameter("RunNum")
                if save==1:
                    fname=time.strftime("%Y%m%d-%H%M%S")
                    fname="eudaq_%s_%s.npy"%(run,fname)
                else:
                    fname="%s no local file"%run
                dat_buffer=np.empty(0,int)
                self.logger.info("run_eudaq StartingRun %s"%fname)
                self.set_hit_trig(mode=mode) ## tlu, tlu_thmod, tlu_test
                self.prod.StartingRun = True  # set status and send BORE
                event=0
                while not self.prod.Error and not self.prod.Terminating and not self.prod.StoppingRun:
                    if event%10000==0 and event!=0:
                        self.logger.info("run_eudaq() event=%d"%event)
                    time.sleep(0.01)
                    dat=self.get_hit_now()
                    if len(dat)==0:
                        continue
                    if save==1:
                        with open(fname,"ab") as f:
                            np.save(f,dat)
                    #### format data and send
                    if len(dat_buffer)==0:
                        dat_buffer=dat
                    else:
                        dat_buffer=np.append(dat_buffer,dat)
                        
                    i=0
                    #arg=np.argwhere((dat_buffer & 0x80000000)==0x80000000)
                    #if len(arg)==0:
                    #    continue
                    #pointer=0
                    #for i in arg[0]:
                    
                    
                    while len(dat_buffer)>=i+172:
                        #if pointer!=i:
                        #    self.logger.info("run_eudaq data mismatch i:%i pointer:%i"%(i,pointer))
                        #if len(dat_buffer) < i+172:
                        #    pointer=i
                        #    break
                        #event = StandardEvent()
                        #plane = event.plane.add()
                        #plane.type = "CCPD_LF"
                        #plane.id = 7
                        #plane.tluevent = int(dat_buffer[i] & 0x7FFFFFFF)
                        #plane.xsize = 114
                        #plane.ysize = 24
                        #frame = plane.frame.add()
                        #zs=self.analyse_hit(dat_buffer[i+1:i+172],"zs_frame")
                        #for j,p in enumerate(zs):
                        #    pix=frame.pixel.add()
                        #    pix.x = p[1]
                        #    pix.y = p[2]
                        #    pix.val = p[0]
                        #self.prod.SendEvent(np.fromstring(
                        #     event.SerializeToString(), dtype=np.uint8))
                        #if plane.tluevent%1000==0:
                        #    if len(zs)> 8:
                        #        zs=zs[:8] 
                        #    print "tlu:%d"%plane.tluevent,"# of pix:%d"%(len(frame.pixel)),zs
                        #print hex(dat_buffer[i]),
                        self.prod.SendEvent(dat_buffer[i:i+172])
                        event=event+1
                        #print "SendEvent"
                        i=i+172
                        #pointer=pointer+172
                    #print pointer
                    dat_buffer=dat_buffer[i:]
            # abort conditions
            if self.prod.Error or self.prod.Terminating:
                self.logger.info("run_eudaq Terminating")
                self.prod.StoppingRun = True  #T or F ??? set status and send EORE
                self.prod.StartingRun = False
                break
                # check if the run is stopping regularly
            if self.prod.StoppingRun:
                self.logger.info("run_eudaq StoppingRun")
                self.prod.StoppingRun = True  # set status and send EORE
                break
            time.sleep(0.1)
            
    ### 1376
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
    def _build_img2(self,dat):
        img=np.empty([24,114],dtype=int)  ##### TODO can be more efficient
        for i in range(0,24,4):
            img[i+0,:]=np.copy(dat[(i+0)*114:(i+1)*114])
            img[i+1,:]=np.copy(dat[(i+1)*114:(i+2)*114][::-1])
            img[i+2,:]=np.copy(dat[(i+3)*114:(i+4)*114][::-1])
            img[i+3,:]=np.copy(dat[(i+2)*114:(i+3)*114])
        return img
    def power(self,pwr_en=True,Vdda=1.8,Vddp=1.5,Vddd=1.8,VCasc=1.0,BL=0.75,TH=0.80,PCBTH=1.3,ADCref=0.7):    
        self.dut['CCPD_Vdda'].set_current_limit(204, unit='mA')
        
        self.dut['CCPD_Vdda'].set_voltage(Vdda, unit='V')
        self.dut['CCPD_Vdda'].set_enable(pwr_en)
        
        self.dut['CCPD_vddaPRE'].set_voltage(Vddp, unit='V')
        self.dut['CCPD_vddaPRE'].set_enable(pwr_en)
        
        self.dut['CCPD_vddd'].set_voltage(Vddd, unit='V')
        self.dut['CCPD_vddd'].set_enable(pwr_en)

        self.dut['CCPD_VCasc'].set_voltage(VCasc, unit='V')
        self.dut['CCPD_VCasc'].set_enable(pwr_en)
        
        self.dut['CCPD_PCBTH'].set_voltage(PCBTH, unit='V')
        self.dut['CCPD_BL'].set_voltage(BL, unit='V')
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        self.dut['CCPD_ADCref'].set_voltage(ADCref, unit='V')
        self.dut['CCPD_NTC'].set_current(100, unit='uA')
        
        self.logger.info("Vdda:%f Vddp:%f Vddd:%f VCasc:%f BL:%f TH:%f PCBTH:%f ADCref:%f"%(
                        Vdda,Vddp,Vddd,VCasc,BL,TH,PCBTH,ADCref))
    def set_inj_all(self,inj_high=1.0,inj_low=0.0,inj_width=500,inj_n=1,delay=700,ext=True):
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        self.inj_low=inj_low

        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=inj_n
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
        self.dut["CCPD_PULSE_INJ"]["EN"]=1
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=inj_n*inj_width*2+10
        self.dut["CCPD_PULSE_GATE"]["EN"]=ext
        self.logger.info("inj:%.4f,%.4f inj_width:%d inj_n:%d delay:%d ext:%d"%(
            inj_high,inj_low,inj_width,inj_n,delay,int(ext)))
    def set_inj(self,inj_high,inj_low=0.0):
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self.dut["CCPD_Injection_low"].set_voltage(inj_low,unit="V")
        self.inj_low=inj_low
        self.logger.info("set_inj inj_high:%f inj_low:%f"%(inj_high, inj_low))
    def set_pulser(self,inj_high=1,inj_low=0.0,burst=True):
        self.dut["PULSER"].set_voltage(0,inj_high,inj_low)
    def inject(self):
        self.dut["CCPD_PULSE_INJ"].start()
    def set_th(self,TH,thmod=False):
        self.dut['CCPD_TH'].set_voltage(TH, unit='V')
        THvol=self.dut['CCPD_TH'].get_voltage(unit='V')
        self.dut['CCPD_SW']['THON_NEG']=1
        self.dut['CCPD_SW'].write()
        self.logger.info("th_set:%f th:%f th_mod:%d"%(TH,THvol,thmod))
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
            "SW_ANA":self.sw_ana.tovalue(),
            "MON_EN":" ".join(hex(ord(n)) for n in self.mon_en.tobytes()),
            "PREAMP_EN":" ".join(hex(ord(n)) for n in self.preamp_en.tobytes()),
            "INJ_EN":" ".join(hex(ord(n)) for n in self.inj_en.tobytes()),
            "Pixels":" ".join(hex(ord(n)) for n in self.dut["CCPD_SR"]["Pixels"].tobytes()),
            #"SR_EN":self.dut["CCPD_SR"].get_enable(),
            "SR_REPEAT":self.dut["CCPD_SR"].get_repeat(),
            "SR_WAIT":self.dut["CCPD_SR"].get_wait(),
            'CCPD_SW':self.dut["CCPD_SW"].get_data()[0],
            'rx_SW':self.dut["rx"].get_data()[0],
            'inj_high':self.inj_high,
            'inj_low':self.inj_low,
            'INJ_DELAY':self.dut["CCPD_PULSE_INJ"]["DELAY"],
            'INJ_WIDTH':self.dut["CCPD_PULSE_INJ"]["WIDTH"],
            'INJ_REPEAT':self.dut["CCPD_PULSE_INJ"]["REPEAT"],
            'INJ_EN':self.dut["CCPD_PULSE_INJ"]["EN"],
            'GATE_DELAY':self.dut["CCPD_PULSE_GATE"]["DELAY"],
            'GATE_WIDTH':self.dut["CCPD_PULSE_GATE"]["WIDTH"],
            'GATE_REPEAT':self.dut["CCPD_PULSE_GATE"]["REPEAT"],
            'GATE_EN':self.dut["CCPD_PULSE_GATE"]["EN"],
            'THON_DELAY':self.dut["CCPD_PULSE_THON"]["DELAY"],
            'THON_WIDTH':self.dut["CCPD_PULSE_THON"]["WIDTH"],
            'THON_REPEAT':self.dut["CCPD_PULSE_THON"]["REPEAT"],
            'THON_EN':self.dut["CCPD_PULSE_THON"]["EN"]
            }         
        return stat
    def show(self):
        # TODO need to complete
        r= self.get_status()
        s="--------Power--------\n"
        s="%sVdda:%f,%f Vddd:%f,%f Vddp:%f,%f VCasc:%f,%f\n"%(s,
            r["Vdda"],r["Vdda_curr"],r["Vddd"],r["Vddd_curr"],r["Vddp"],r["Vddp_curr"],r["VCasc"],r["VCasc_curr"])
        s="%sBL:%f,%f TH:%f,%f PCBTH:%f,%f\n"%(s,
            r["BL"],r["BL_curr"],r["TH"],r["TH_curr"],r["PCBTH"],r["PCBTH_curr"])
        s="%s--------Global DAC--------\n"%s
        s='%sBLRes:%d VN:%d VPFB:%d VPFoll:%d VPLoad:%d LSBdacL:%d IComp:%d \n'%(s,
            r["BLRes"],r["VN"],r["VPFB"],r["VPFoll"],r["VPLoad"],r["LSBdacL"],r["IComp"])
        s='%sVSTRETCH:%d WGT0:%d WGT1:%d WGT2:%d IDacTEST:%d IDacLTEST:%d\n'%(s,
            r["VSTRETCH"],r["WGT0"],r["WGT1"],r["WGT2"],r["IDacTEST"],r["IDacLTEST"])
        s="%s--------Pixels--------\n"%s
        s="%ssw_ana:0x%x\n"%(s,r['SW_ANA'])
        s="%spreamp_en:%s\n"%(s,r["PREAMP_EN"])
        s="%sinj_en:%s\n"%(s,r["INJ_EN"])
        s="%smon_en:%s\n"%(s,r["MON_EN"])
        s="%s--------Pulser--------\n"%s
        s="%sinj_width:%d inj_delay:%d inj_n:%d inj_en:%d\n"%(s,
            r['INJ_WIDTH'],r['INJ_DELAY'],r['INJ_REPEAT'],r['INJ_EN'])
        s="%sinj_high:%f inj_low:%f\n"%(s,r['inj_high'],r['inj_low'])
        s="%sgate_width:%d gate_delay:%d gate_n:%d inj_en:%d\n"%(s,
            r['GATE_WIDTH'],r['GATE_DELAY'],r['GATE_REPEAT'],r['GATE_EN'])
        s="%sthon_width:%d thon_delay:%d thon_n:%d thon_en:%d\n"%(s,
            r['THON_WIDTH'],r['THON_DELAY'],r['THON_REPEAT'],r['THON_EN'])
        s="%s--------Switch--------\n"%s
        s="%s,CCPD_SW:%d,(%s)\n"%(s,r["CCPD_SW"],str(self.dut["CCPD_SW"]).split(",",1)[1][:-1])
        s="%s,rx_SW:%d,(%s)\n"%(s,r["rx_SW"],str(self.dut["rx"]).split(",",1)[1][:-1])
        s="%s--------SPI--------\n"%s
        s="%s sr_repeat:%d sr_wait:%d sr_en:\n"%(s,
            r["SR_REPEAT"],r["SR_WAIT"])
        s="%s--------FPGA--------\n"%s
        s="%stlu:%s\n"%(s,str(self.dut["tlu"]))
        s="%stdc:%s\n"%(s,str(self.dut["CCPD_TDC"]))
        self.logger.info(s)
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
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)
        
        #self.dut["CCPD_PULSE_GATE"].reset()
        #self.dut['CCPD_PULSE_GATE'].set_en(False)
        #self.dut["CCPD_PULSE_INJ"].reset()
        #self.dut['CCPD_PULSE_INJ'].set_en(False)

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
        ###
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
        
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=1
        self.dut['CCPD_SR']['PREAMP_EN']=0
        
        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix

        for i in range(0,2736,114):
            self.dut['CCPD_SR']['SW_ANA'][i/114]=en_pix[i:i+114].any()

        self._write_SR(sw="SW_LDPIX")
        ###
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        self.mon_en=self.dut["CCPD_SR"]["Pixels"].copy()
        self.sw_ana=self.dut['CCPD_SR']['SW_ANA'].copy()
        s="set_mon_en pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self.dut["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)
    def set_preamp_en(self,pix="all"):
        ###
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)

        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=1
        self.dut['CCPD_SR']['SW_ANA']=self.sw_ana

        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix

        self._write_SR(sw="SW_LDPIX")
        ###
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        self.preamp_en=self.dut["CCPD_SR"]["Pixels"].copy()
        s="set_preamp_en pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self.dut["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)
    def set_inj_en(self,pix="all"):
        ###
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
    
        self.dut['CCPD_SR']['TRIM_EN']=0
        self.dut['CCPD_SR']['INJECT_EN']=1
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0
        self.dut['CCPD_SR']['SW_ANA']=self.sw_ana

        en_pix=self._cal_Pixels(pix)
        self.dut['CCPD_SR']['Pixels']=en_pix.copy()
        
        self._write_SR(sw="SW_LDPIX")
        ###
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        self.inj_en=self.dut["CCPD_SR"]["Pixels"].copy()
        s="set_inj_en pix:%s lds:%d,%d,%d,%d sw_ana:0x%x pixels:%s"%(pix,
                self.dut['CCPD_SR']['TRIM_EN'].tovalue(),self.dut['CCPD_SR']['INJECT_EN'].tovalue(),
                self.dut['CCPD_SR']['MONITOR_EN'].tovalue(),self.dut['CCPD_SR']['PREAMP_EN'].tovalue(),
                self.dut['CCPD_SR']['SW_ANA'].tovalue(),"")
                #"".join("%x"%n for n in self.dut["CCPD_SR"]["Pixels"].tobytes()))
        self.logger.info(s)        
    def set_tdac(self,tdac):
        ###
        tmp_spi_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_SPI_RX'].set_en(False)
        tmp_gate_en=self.dut['CCPD_SPI_RX'].get_en()
        self.dut['CCPD_PULSE_GATE'].set_en(False)
    
        self.dut['CCPD_SR']['INJECT_EN']=0
        self.dut['CCPD_SR']['MONITOR_EN']=0
        self.dut['CCPD_SR']['PREAMP_EN']=0
        self.dut['CCPD_SR']['SW_ANA']=self.sw_ana
        
        if isinstance(tdac, int):
            tdac=np.ones([24,114],int)*tdac
       
        for i_trim in [1,2,4,8]:
            pix=bitarray.bitarray(((np.reshape(tdac, 114*24) & i_trim) !=0).tolist())
            en_pix=self._cal_Pixels(pix)
            self.dut['CCPD_SR']['Pixels']=en_pix
            self.dut['CCPD_SR']['TRIM_EN']=i_trim
            self._write_SR(sw="SW_LDPIX")
        
        ###
        self.dut['CCPD_SPI_RX'].set_en(tmp_spi_en)
        self.dut['CCPD_PULSE_GATE'].set_en(tmp_gate_en)
        
        np.argwhere(self.tdac!=tdac)
        s="tdac:"
        for p in np.argwhere(self.tdac!=tdac):
            s="%s,[%d,%d]=%d"%(s,p[0],p[1],tdac[p[0],p[1]])
        self.logger.info(s)
        self.tdac=np.copy(tdac)
    def set_adc(self,pix=[14,14],howmuch=1000,extrig=False,ADCref=0.7):
        # set gpio
        self.dut['rx']['CCPD_ADC'] = 1
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 0
        self.dut['rx'].write()
        
        self.dut['CCPD_ADCref'].set_voltage(ADCref, unit='V')
        
        self.dut["CCPD_AMPOUT"].reset()
        self.dut["CCPD_AMPOUT"].set_data_count(howmuch)
        self.dut["CCPD_AMPOUT"].set_align_to_sync(extrig)
        
        s="set_adc: howmuch=%d extrig=%d ADCref=%f"%(howmuch,extrig,ADCref)
        self.logger.info(s)
    def get_adc(self):
        self.dut['sram'].reset()
        self.dut['CCPD_AMPOUT'].start()
        
        nmdata = self.dut['sram'].get_data()
        i=0
        while not (self.dut['CCPD_AMPOUT'].is_done()):
            nmdata = np.append(nmdata, self.dut['sram'].get_data())
            i=i+1
            if i>500:
                time.sleep(0.001)
        nmdata = np.append(nmdata, self.dut['sram'].get_data())

        val1 = np.bitwise_and(nmdata, 0x00003fff)
        #vals = np.bitwise_and(nmdata, 0x10000000)
        #valc = np.bitwise_and(nmdata, 0x60000000)
        #if np.any(vals!=1):
        #    print "get_adc: WARN sync might be failed"
        val0 = np.right_shift(np.bitwise_and(nmdata, 0x0fffc000), 14)
        
        return np.reshape(np.vstack((val0, val1)), -1, order='F')
    def set_hit(self,mode="inj",inj=None,repeat=None,inj_delay=None,inj_width=None,gate_delay=None,
                gate_width=None,thmod=None,thon_width=None,thon_delay=None,sr_wait=None):
        tmp_inj_delay=inj_delay
        tmp_inj_width=inj_width
        tmp_inj=inj
        tmp_gate_delay=gate_delay
        tmp_gate_width=gate_width
        tmp_thmod=thmod
        tmp_thon_width=thon_width
        tmp_thon_delay=thon_delay
        tmp_sr_wait=sr_wait
        tmp_repeat=repeat
        if mode=="inj":
            repeat=100
            inj_delay=100
            inj_width=50
            gate_delay=5
            gate_width=inj_delay+inj_width/2
            thmod=False
            thon_width=0
            thon_delay=gate_delay
            sr_wait=gate_width+gate_delay+5
        elif mode=="inj_ext": ### external should be 1kHz
            repeat=100
            inj_delay=0
            inj_width=0
            gate_delay=5
            gate_width=1000
            thmod=False
            thon_width=1
            thon_delay=1
            sr_wait=gate_width+gate_delay+5
        elif mode=="inj_thmod":
            repeat=100
            gate_width=9900
            inj_width=50
            inj_delay=gate_width-inj_width/2
            gate_delay=5
            thmod=True
            thon_width=gate_width-10
            thon_delay=gate_delay+10
            sr_wait=gate_width+gate_delay+5
        elif mode=="src":
            inj_delay=0
            inj_width=0
            inj=False
            gate_delay=5
            gate_width=9900
            thmod=False
            thon_width=0
            thon_delay=0
            sr_wait=gate_width+10
            repeat=100
        elif mode=="src_thmod":
            inj_delay=0
            inj_width=0
            inj=False
            gate_delay=5
            gate_width=9900
            thmod=True
            thon_width=gate_width-10
            thon_delay=gate_delay+10
            sr_wait=gate_width+gate_delay+5
            repeat=100
        if tmp_inj_delay!=None:
            inj_delay=tmp_inj_delay
        if tmp_inj_width!=None:
            inj_width=tmp_inj_width
        if tmp_inj!=None:
            inj=tmp_inj
        if tmp_gate_delay!=None:
            gate_delay=tmp_gate_delay
        if tmp_gate_width!=None:
            gate_width=tmp_gate_width
        if tmp_thmod!=None:
            thmod=tmp_thmod
        if tmp_thon_width!=None:
            thon_width=tmp_thon_width
        if tmp_thon_delay!=None:
            thon_delay=tmp_thon_delay
        if tmp_sr_wait!=None:
            sr_wait=tmp_sr_wait
        if tmp_repeat!=None:
            repeat=tmp_repeat

        # set gpio
        self.dut['rx']['CCPD_ADC'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 1
        self.dut['rx'].write()
        
        self.dut["CCPD_PULSE_THON"].reset()
        if thmod==False:
            self.dut["CCPD_PULSE_THON"].set_en(0)
        else:
            self.dut["CCPD_PULSE_THON"].set_delay(thon_delay)
            self.dut["CCPD_PULSE_THON"].set_repeat(1)
            self.dut["CCPD_PULSE_THON"].set_width(thon_width)
            self.dut["CCPD_PULSE_THON"].set_en(1)

        # reset spi
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate first
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        self.dut["CCPD_SR"].set_size(2736)
        self.dut["CCPD_SR"].set_repeat(repeat)
        self.dut["CCPD_SR"].set_wait(sr_wait)

        ## set LD switches
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        if thmod==False:
            self.dut['CCPD_SW']['THON_NEG']=1
        else:
            self.dut['CCPD_SW']['THON_NEG']=0
        self.dut["CCPD_SW"]["SW_HIT"]=1
        self.dut['CCPD_SW'].write()

        # set pulser
        if inj==False:
            self.dut["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self.dut["CCPD_PULSE_INJ"].reset()
            self.dut["CCPD_PULSE_INJ"]["REPEAT"]=1
            self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_delay
            self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self.dut["CCPD_PULSE_INJ"]["EN"]=1

        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=gate_delay
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

        s="repeat:%d inj_delay:%d inj_width:%d gate_delay:%d gate_width:%d\n"%(
            repeat,inj_delay,inj_width,gate_delay,gate_width)
        s="%sthod:%d thon_width:%d thon_delay:%d sr_wait:%d"%(
            s,thmod,thon_width,thon_delay,sr_wait)
        self.logger.info(s)
    def set_hit_trig(self,mode="tlu", \
                     delay=None,close_delay=None,thon_delay=None,inj_high=None, \
                     inj_n=None,inj=None):
        tmp_delay=delay    #### TODO simplify here
        tmp_colse_delay=close_delay
        tmp_thon_delay=thon_delay
        tmp_inj_high=inj_high
        tmp_inj_n=inj_n
        tmp_inj=inj
        if mode=="tlu":
            delay=0
            close_delay=1
            thon_delay=10
            thmod=False
            tlu=True
            inj_high=0
            inj_n=1
            inj=False
        elif mode=="tlu_inj":
            delay=0
            close_delay=1
            thon_delay=10
            thmod=False
            tlu=True
            inj_high=0.5
            inj_n=0
            inj=False
        elif mode=="tlu_thmod":
            delay=10
            close_delay=1
            thon_delay=10
            thmod=True
            tlu=True
            inj_high=0
            inj_n=1
            inj=False
        elif mode=="rx0":
            delay=10
            close_delay=10
            thon_delay=10
            thmod=False
            tlu=False
            inj_high=0
            inj_n=1
            inj=False
        else:
            delay=10
            close_delay=10
            thon_delay=10
            thmod=True
            tlu=False
            inj_high=0
            inj_n=1
            inj=False  
        if tmp_delay!=None:
            delay=tmp_delay
        if tmp_colse_delay!=None:
            close_delay=tmp_delay
        if tmp_thon_delay!=None:
            thon_delay=tmp_delay
            thmod=False
        if tmp_inj_high!=None:
            inj_high=tmp_inj_high
        if tmp_inj_n!=None:
            inj_n=tmp_inj_n
        if tmp_inj !=None:
            inj=tmp_inj

        # set tlu
        self.dut["tlu"]["RESET"]=0
        if tlu==True:
            self.dut["tlu"]["TRIGGER_MODE"]=3
            self.dut["tlu"]["TRIGGER_LOW_TIMEOUT"]=0
            self.dut["tlu"]["TRIGGER_VETO_SELECT"]=0
    
        # set gpio
        self.dut['rx']['NC'] = 0
        self.dut['rx']['TLU'] = tlu
        self.dut['rx']['CCPD_TDC'] = 0
        self.dut['rx']['CCPD_RX'] = 1
        self.dut['rx'].write()
        
        self.dut["CCPD_PULSE_THON"].reset()
        self.dut["CCPD_PULSE_THON"]["EN"]=thmod
        if thmod==True:
            self.dut["CCPD_PULSE_THON"]["DELAY"]=1
            self.dut["CCPD_PULSE_THON"]["REPEAT"]=1
            self.dut["CCPD_PULSE_THON"]["WIDTH"]=2736+delay+thon_delay
        
        # reset spi
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["EN"]=0 ##disable gate first
        self.dut["CCPD_SR"].reset()
        self.dut["CCPD_SR"]=bitarray.bitarray('1'*2843)
        self._write_SR(sw="NONE")
        #set spi
        self.dut["CCPD_SR"].set_size(2736)
        self.dut["CCPD_SR"].set_repeat(1)
        self.dut["CCPD_SR"].set_wait(0)
        self.dut["CCPD_SR"].set_en(1)
        
        ## set LD switches
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['THON_NEG']=True
        self.dut['CCPD_SW']['GATE_NEG']=1 ## GATE will be triggered by negative edge of RX0
        self.dut["CCPD_SW"]["SW_HIT"]=1
        self.dut['CCPD_SW']['EXT_START_TLU']=int(tlu)
        self.dut['CCPD_SW'].write()
        
        # set inj amplitude 0
        self.dut["CCPD_Injection_high"].set_voltage(inj_high,unit="V")
        self.inj_high=inj_high
        self.dut["CCPD_Injection_low"].set_voltage(0,unit="V")
        self.inj_low=0
        # disable inj
        self.dut["CCPD_PULSE_INJ"].reset()
        self.dut["CCPD_PULSE_INJ"]["EN"]=inj
        self.dut["CCPD_PULSE_INJ"]["DELAY"]=50 ### need to find good parameter
        self.dut["CCPD_PULSE_INJ"]["WIDTH"]=50
        print "inj_n",inj_n  
        self.dut["CCPD_PULSE_INJ"]["REPEAT"]=inj_n
        if inj_n==0:
            self.dut["CCPD_PULSE_INJ"].start()
        
        # set gate
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=close_delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=2740+delay
        self.dut["CCPD_PULSE_GATE"]["EN"]=1
        
        # disable TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=False
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()
        print self.dut['sram'].get_fifo_size()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(True)
        
        s="set_hit_trig delay:%d close_delay:%d thmod_delay:%d thmod:%d tlu:%d\n"%(
            delay,close_delay,thon_delay,thmod,tlu)
        s="%s inj_high:%f inj_n:%d inj:%d"%(s,inj_high,inj_n,inj)
        self.logger.info(s)
    def set_tdc(self,mode="inj", \
                gate_width=None,repeat=100,inj_width=None,gate_delay=None, \
                inj_delay=None,inj=None):
        tmp_gate_width=gate_width ## here should be improved
        tmp_repeat=repeat
        tmp_inj_width=inj_width
        tmp_gate_delay=gate_delay
        tmp_inj_delay=inj_delay
        tmp_inj=inj
        if mode=="inj":
            inj_width=500
            inj_delay=inj_width
            repeat=100
            gate_width=inj_width*2*repeat+10
            gate_delay=5
            inj=True
        else: # mode=="src"
            inj_width=500
            repeat=100
            gate_width=9900
            gate_delay=5
            inj=False
        if tmp_gate_width!=None:
            gate_width=tmp_gate_width
        if tmp_repeat!=None:
            repeat=tmp_repeat
        if tmp_inj_width!=None:
            inj_width=tmp_inj_width
        if tmp_gate_delay!=None:
            gate_delay=tmp_gate_delay
        if tmp_inj_delay!=None:
            inj_delay=tmp_inj_delay
        if tmp_inj!=None:
            inj=tmp_inj
        # set gpio
        self.dut['rx']['NC'] = 0
        self.dut['rx']['TLU'] = 0
        self.dut['rx']['CCPD_TDC'] = 1
        self.dut['rx']['CCPD_RX'] = 0
        self.dut['rx'].write()
        
        self.dut['CCPD_SW']['SW_LDPIX']=0
        self.dut['CCPD_SW']['SW_LDDAC']=0
        self.dut['CCPD_SW']['SW_HIT']=0
        self.dut["CCPD_SW"]['THON_NEG']=1
        self.dut['CCPD_SW'].write()
        
        # reset rx
        self.dut['CCPD_SPI_RX'].reset()
        self.dut['CCPD_SPI_RX'].set_en(False)

        # set pulser
        self.dut["CCPD_PULSE_INJ"].reset()
        if inj==False:
            self.dut["CCPD_PULSE_INJ"]["EN"]=0
        else:
            self.dut["CCPD_PULSE_INJ"]["REPEAT"]=repeat
            self.dut["CCPD_PULSE_INJ"]["DELAY"]=inj_delay
            self.dut["CCPD_PULSE_INJ"]["WIDTH"]=inj_width
            self.dut["CCPD_PULSE_INJ"]["EN"]=1
        
        
        self.dut["CCPD_PULSE_GATE"].reset()
        self.dut["CCPD_PULSE_GATE"]["REPEAT"]=1
        self.dut["CCPD_PULSE_GATE"]["DELAY"]=gate_delay
        self.dut["CCPD_PULSE_GATE"]["WIDTH"]=gate_width
        self.dut["CCPD_PULSE_GATE"]["EN"]=1 

        # reset TDC
        self.dut["CCPD_TDC"].reset()
        self.dut['CCPD_TDC']['EN_INVERT_TDC']=True
        self.dut['CCPD_TDC']['ENABLE_EXTERN']=True
        self.dut['CCPD_TDC']['ENABLE']=False

        # reset fifo
        self.dut['sram'].reset()
        print gate_width,repeat,inj,inj_width,inj_delay,gate_delay
        s="set_tdc gate_width:%d repeat:%d inj:%d inj_width:%d inj_delay:%d gate_delay:%d"%(
            gate_width,repeat,inj,inj_width,inj_delay,gate_delay)
        self.logger.info(s)
    def get_hit(self):
        self.dut['sram'].reset()
        while self.dut["sram"].get_fifo_size()!=0:
           self.dut['sram'].get_data()
           self.dut['sram'].reset()
        self.dut["CCPD_SR"].start()
        wait=self.dut["CCPD_SR"].get_wait()
        repeat=self.dut["CCPD_SR"].get_repeat()
        i=0
        while self.dut["sram"].get_fifo_size()<684*repeat:
        #while not self.dut['CCPD_SR'].is_done():  ## this dose not work any more
            if i>10000+wait*repeat/1000:
                self.logger.info("ERROR timeout")
                break
            elif i> 100:
                time.sleep(0.001) # avoid CPU 100%
            i=i+1
        #print self.dut["sram"].get_fifo_size()
        return self.dut['sram'].get_data()
    def get_hit_now(self):
       return self.dut["sram"].get_data()
    def tune_tdac(self,mode="src_thmod",LSBdacL=63,th=0.725,th_cnt=5):
        self.set_th(th)
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
                self.set_hit(mode=mode)
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
                self.ax[1].pcolor(d,vmax=100,vmin=0)
                self.ax[0].pcolor(tdac,vmax=15,vmin=0)
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
    def tune_tdac_mod2(self,thmod=True,exp=9900,th_cnt=5,b=0.77,e=0.742,s=-0.001):
        tdac=np.copy(self.tdac)
        flg=np.ones([24,114])*2
        for th in np.arange(b,e,s):
            p=20
            while p>10:
                self.set_th(th)
                self.set_tdac(tdac)
                self.set_hit(gate_width=exp,inj_width=0,repeat=100,delay=10,thon=thmod) 
                d=self.analyse_hit(self.get_hit(),"img")
                if self.plot==True:
                    self.ax[1].pcolor(d,vmax=100,vmin=0)
                    self.ax[0].pcolor(tdac,vmax=15,vmin=0)
                    plt.pause(0.001)
                p=0
                for i in range(23):
                    for j in range(114):
                        if d[i,j]>th_cnt:
                            if tdac[i,j]==15:
                                pass
                            else:
                                tdac[i,j]=tdac[i,j]+1
                                p=p+1
                    if p>=50:
                        break
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
    def scan_th(self,b=0.78,e=0.7,s=-0.01,mode="src_thmod",save=True,pix=[14,14]):
        if "inj" in mode: #
            self.set_inj_en(pix)
            self.set_preamp_en(pix)
        else:
            self.set_inj_en("none")
            self.set_preamp_en("all")
        if isinstance(pix[0],int):
            pix=np.array([pix])
        else:
            pix=np.array(pix)
        self.set_hit(mode=mode)
        self.dut['CCPD_TH'].set_voltage(b, unit='V')
        if save==True:
            fname=time.strftime("hit_%y%m%d-%H%M%S.npy")
            self.logger.info("fname:%s"%fname)
            with open(fname,"ab+") as f:
                np.save(f,np.arange(b,e,s))
        for th in np.arange(b+s,e+s,s):
            d=self.get_hit()
            th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
            self.dut['CCPD_TH'].set_voltage(th, unit='V')
            d=self.analyse_hit(d,"img")
            if self.plot==True:
                self.ax[0].pcolor(d,vmin=0)
                plt.pause(0.001)
            self.logger.info("scan_th %f %d %s"%(th_meas,np.sum(d),str(d[pix[:,0],pix[:,1]])))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
        if save==True:
            return fname
    def scan_th_auto(self,b=1.2,e=0.7,s=-0.01,mode="src_thmod",save=True,pix=[14,14]):
        if "inj" in mode: #
            self.set_inj_en(pix)
            self.set_preamp_en(pix)
        else:
            self.set_inj_en("none")
            self.set_preamp_en("all")
        if isinstance(pix[0],int):
            pix=np.array([pix])
        else:
            pix=np.array(pix)
        self.set_hit(mode=mode)
        self.dut['CCPD_TH'].set_voltage(b, unit='V')
        if save==True:
            fname=time.strftime("hitauto_%y%m%d-%H%M%S.npy")
            self.logger.info("fname:%s"%fname)
        next=b+s
        state=np.ones(len(pix))*-1
        #print state
        th=[]
        while True:
            d=self.get_hit()
            th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
            th.append(th_meas)
            self.dut['CCPD_TH'].set_voltage(next, unit='V')
            d=self.analyse_hit(d,"img")
            self.logger.info("scan_th %f %d %s"%(th_meas,np.sum(d),str(d[pix[:,0],pix[:,1]])))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
                    f.flush()
            if self.plot==True:
                self.ax[0].pcolor(d,vmin=0)
                plt.pause(0.001)
                
            ### state machine
            if state[0]==-1 and np.all(d[pix[:,0],pix[:,1]]==0):
                next=next+s
            elif state[0]==-1:
                print next, d[pix[:,0],pix[:,1]]==0
                next=next-2*s
                s=-0.001
                state=state*0
            elif state[0]==-1:
                next=next+s
            elif state[0]==1 or state[0]==0:
                state[d[pix[:,0],pix[:,1]]!=0]=1
                #print state
                if np.all(state==1):
                   print state
                   state[0]=2
                next=next+s
            elif state[0]==20:
                break
            elif state[0]>=2:
                state[0]=state[0]+1
                next=next+s
            elif next<e:
                break
                
        if save==True:
            with open(fname,"ab+") as f:
                np.save(f,th)
                f.flush()
            return fname
    def scan_source(self,n=1000,mode="src_thmod",save=True):
        if self.plot==True:
           img=np.zeros([24,114])
        self.set_preamp_en("all")
        self.set_inj_en("none")
        self.set_mon_en("none")
        self.set_hit(mode=mode)
        if save==True:
            fname=time.strftime("source_%y%m%d-%H%M%S.npy")
            self.logger.info("fname:%s"%fname)
        i=0
        while i <n:
            d=self.get_hit()
            if self.plot==True:
                self.ax[0].pcolor(self.analyse_hit(d,"img"),vmin=0)
                plt.pause(0.001)
            d=self.analyse_hit(d,"zs")
            self.logger.info("%f,%d"%(i,len(d)))
            if save==True:
                with open(fname,"ab+") as f:
                    np.save(f,d)
            i=i+1
    def scan_th_tdc_simple(self,b=1.1,e=0.7,s=-0.01):
            self.dut['CCPD_TH'].set_voltage(b, unit='V')       
            self.logger.info("scan_th_tdc_simple th cnt ave std")
            for th in np.arange(b+s,e+s,s):
                d=self.get_tdc()
                th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
                self.dut['CCPD_TH'].set_voltage(th, unit='V')
                width,delay=self.analyse_tdc(d)
                cnt=len(width)
                ave=np.average(width)
                std=np.std(width)
                self.logger.info("scan_th_tdc_simple %f %d %f %f"%(th_meas,cnt,ave,std))
    def scan_th_tdc(self,b=1.1,e=0.7,s=-0.01,mode="inj",pix=[14,14]):
        self.logger.archive()
        if isinstance(pix,str):
            pix=np.empty([24*114,2],int)
            for i in range(24):   ## TODO code without for-loops
                    for j in range(114):
                        pix[i*114+j,:]=[i,j]
        elif isinstance(pix[0],int):
            pix=[pix]
        for p in pix:
            self.set_preamp_en(p)
            self.set_mon_en(p)
            if mode=="inj":
                self.set_inj_en(p)
 
            self.dut['CCPD_SR']['WGT0']=0
            self.dut['CCPD_SR']['WGT1']=0
            self.dut['CCPD_SR']['WGT2']=0
            self.dut['CCPD_SR']['WGT%d'%(p[1]%3)]=63
            self._write_SR(sw="SW_LDDAC")
            
            self.logger.info("scan_th_tdc WGT:%d,%d,%d"%(
                 self.dut['CCPD_SR']['WGT0'].tovalue(),
                 self.dut['CCPD_SR']['WGT1'].tovalue(),
                 self.dut['CCPD_SR']['WGT2'].tovalue()))
            self.set_tdc(mode="inj")       
            self.logger.info("scan_th_tdc th cnt ave std")
            
            self.dut['CCPD_TH'].set_voltage(b, unit='V') 
            for th in np.arange(b+s,e+s,s):
                d=self.get_tdc()
                th_meas=self.dut['CCPD_TH'].get_voltage(unit='V')
                self.dut['CCPD_TH'].set_voltage(th, unit='V')
                width,delay=self.analyse_tdc(d)
                cnt=len(width)
                ave=np.average(width)
                std=np.std(width)
                self.logger.info("scan_th_tdc %f %d %f %f"%(th_meas,cnt,ave,std))
    def find_th_tdc(self,start=1.5,stop=0.5,step=-0.05,mode="inj",th_cnt=50,full_scurve=False):
        self.set_tdc(mode=mode)
        #self.logger.info("step:%f exp:%d"%(step,exp))
        i=0
        scurve_flg=0
        th_list=np.arange(start,stop,step)
        print th_list
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
            elif abs(step)>abs(-0.005*0.99) and cnt>th_cnt:
                if self.debug==1:
                    print "debug change step to 0.001"
                step=-0.001
                th_list=np.arange(th-6*step,stop,step)
                i=0
            elif abs(step)>abs(-0.001*0.99) and  cnt> th_cnt and scurve_flg==0:
                if full_scurve==False:
                    break
                else:
                    scurve_flg=1
            elif scurve_flg==1 and cnt==0:
                break
            else:
                i=i+1
    def find_tdac_tdc(self,mode="inj",pix=[14,14]):
        #self.set_preamp_en("all")
        self.set_mon_en(pix)
        self.set_inj_en(pix)
        self.set_tdc(mode=mode)
        tdac=self.tdac
        for t in range(15,-1,-1):
            tdac[pix[0],pix[1]]=t
            self.set_tdac(tdac)
            d=self.get_tdc()
            width,delay=self.analyse_tdc(d)
            self.logger.info("find_tdac_tdc %d %d %f %f"%(t,len(d),np.average(width),np.average(delay)))
            if len(d)>5:
                if t!=15:
                    tdac[pix[0],pix[1]]=t+1
                break
        self.logger.info("find_tdac_tdc pix:[%d,%d] tdac:%d"%(
            pix[0],pix[1],tdac[pix[0],pix[1]]))
        
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
    def analyse_hit(self,dat,fmt="zs"):
        dat=dat[(dat & 0xF0000000)==0x60000000]
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
        elif fmt=="zs_frame":
            ret=np.argwhere(ret==True)[:,0]
            if len(ret)!=0:
                frame,col,row=self._build_img(ret)
                frame=(dat[ret/16] & 0x0FFF0000)>>16
                ret=np.transpose(np.array([frame,col,row]))
                return ret
            else:
                return np.array([])
        elif fmt=="img":    ##### TODO can be more efficient
            img=np.zeros([24,114])
            for i in range(0,len(ret),2736):
                img=np.add(img,self._build_img2(ret[i:i+2736][::-1]))
            return img
        else:
            return "ERROR!! fmt=img,zs,zs_frame" ### TODO make this exception
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
        
class ccpdlfB(ccpdlfA):
    def __init__(self,conf="ccpdlf.yaml"):
        self.logger=Log()
        if conf=="":
            conf="ccpdlf.yaml"
        self.dut=Dut(conf)
        self.debug=0
        self._build_img=np.vectorize(self._build_img_oneB)
        self.tdac=np.zeros([24,114],int)
        # init member variables
        self.plot=False
        # init dut
        self.dut.init()
        self.power()
        self.set_global()
        self.set_mon_en([14,14])
        self.set_preamp_en([14,14])
        self.set_inj_en([14,14])
        self.set_tdac(0)
        self.set_th(1.5)
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
        img=np.empty([24,114],dtype=int)  ##### TODO can be more efficient
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



 



 
