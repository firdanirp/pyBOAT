## TFApy - Time Frequency Analysis UI - Beta :rocket: ##


Tools for time-frequency analysis with Morlet Wavelets
Inspired by 'A Practical Guide to Wavelet Analysis' (Torrence
and Compo 1998), 'Identification of Chirps with Continuous Wavelet Transform'
(Carmona, Hwang and Torresani 1995)
and [The Scientist and Engineer's Guide to Digital Signal Processing](http://www.dspguide.com/).

Version 0.5 June 2018, Frieda Sorgenfrei and Gregor Mönke. 

Questions etc. please to gregor.moenke@embl.de.

**Contributers are welcome!**

### Features ###

* Optimal sinc filter
* Fourier analysis
* Wavelet analysis 
* Ridge detection
* Phase extraction 

### Things not ready yet ###

* Synthetic signal generator

### Installation and Requirements ###

The program needs some scientific python libraries (detailed list will come), it's most
convenient to install [Anaconda 3] (https://conda.io/docs/user-guide/install/download.html) to
get all required Python libraries.

No real 'installation' yet, just download (or clone) the
repository (it's the tiny button sporting a cloud icon on the right).


##### Mac OS #####

After downloading the repository, double click the 
``` TFApy_MacOS.command ``` file. It will open a 
terminal in the background and runs the TFApy program.
You might have to 'allow' 3rd-party apps to run, this
can be done for **El Capitan** by:

``` System Preferences -> Security & Privacy -> Allow Apps downloaded from -> Anywhere ```

For the newest version **Sierra** do a right click on that file,
and choose open.

##### Anaconda troubleshooting #####

In case of errors from Anaconda, you can try to update
your installation by typing

```conda update --all ```

in the terminal.

##### Linux #####

Just run ```python3 TFApy.py ``` on the terminal 
from the ``` /src ``` directory.

##### Windows #####

Everything is a bit more complicated here, so no 'double-clickable' file yet. 
With the windows command line navigate to the``` /tfapy ``` directory
and run ```python3 TFApy.py ```. For some people double-clicking the ```TFApy.py ```
does the trick.

### Usage ###
-------------

##### Data import #####

Just open your saved time-series data by using ``` Open ``` 
from the (small) main window. Supported input formats are:
``` .xls, .xlsx, .csv, .tsv and .txt ```. For other file
extensions, white space separation of the data is assumed.
Please see examples of the supported formats in the 
``` data_examples ``` directory.

##### Detrending and Analysis Setup #####

After successful import, you can simply click on the table representing
your data to select a specific time-series in the ``` DataViewer ```. 
Alternatively, select a specific time-series from the drop-down menu in the upper left.
To get the correct numbers/units you can change the sampling interval 
and unit name in the top line of the ``` DataViewer ```.
To apply the sinc-filter detrending, enter a (positive) Number for the ``` cut-off-period ```. 
All periods bigger than the one entered will be removed from the data. Click ``` Refresh Plot ```
and check the ``` Trend ``` and/or ``` Detrended Signal ``` checkbox(es) to see the effect of the filter.

Finally, set the parameters for the Wavelet Analysis in the lower right:

| Input Field | Meaning  |
| :------------ |:---------------:| -----:|
| Smallest Period | Lower period bound <br> (Nyquist limit built-in)  |
| Number of Periods | Resolution of the transform <br> or number of convolutions             |   
| Highest Period | Upper period bound <br> Should not exceed observation time     |
| Expected maximal power | Upper bound for the colormap <br> of the Wavelet power spectrum <br> normalized to white noise |



*to be continued*
