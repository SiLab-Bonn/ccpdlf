# ccpdlf

## branches

- master : Malte's PCB v1.1
- th_sw : PCB for threshold switching
- cppm : firmware and software costmized for CPPM

## installation

- install anaconda python
  - https://store.continuum.io/cshop/anaconda/
- install driver and APIs of MultiIO board
  - https://silab-redmine.physik.uni-bonn.de/projects/pysilibusb/wiki
- install basil
  - https://github.com/SiLab-Bonn/basil
  - recommended version: https://github.com/SiLab-Bonn/basil/tree/c66e34a9f214116aa3bdad2a5af496cd5e858e83
- get a copy of ccpdlf
  - https://github.com/SiLab-Bonn/ccpdlf
- modify ipython.bat or ipython.sh
```sh
<path to ipython> qtconsole --matplotlib=inline --autocall=2
```

## quick start

- run ipython.bat or ipython.sh
- make an instance and init
```python
import ccpdlf
c=ccpdlf.ccpdlf()
```
- call functions
```python
c.set_global(VN=2)
c.scan_tdc()
etc..
```
