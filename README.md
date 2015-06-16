# ccpdlf
## installation
- install anaconda python
https://store.continuum.io/cshop/anaconda/
- install driver and APIs for multiIO board
https://silab-redmine.physik.uni-bonn.de/projects/pysilibusb/wiki
- install basil
https://github.com/SiLab-Bonn/basil
- get a copy of ccpdlf
https://github.com/SiLab-Bonn/ccpdlf

## quick start
- run ipython.bat or ipython.sh
- make an instance and init
```python
import ccpdlf
c=ccpdlf.ccpdlf()
c.init()
```
- call functions
```python
c.set_global(VN=2)
etc..
```
