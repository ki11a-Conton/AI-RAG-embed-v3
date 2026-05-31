
# Forecasting: Principles and Practice(3rd ed)


# Forecasting: Principles and Practice(3rd ed)


Rob J Hyndman and George Athanasopoulos


# Preface


Buy a print version


Welcome to our online textbook on forecasting.


This textbook is intended to provide a comprehensive introduction to forecasting methods and to present enough information about each method for readers to be able to use them sensibly. We don’t attempt to give a thorough discussion of the theoretical details behind each method, although the references at the end of each chapter will fill in many of those details.


The book is written for three audiences: (1) people finding themselves doing forecasting in business when they may not have had any formal training in the area; (2) undergraduate students studying business; (3) MBA students doing a forecasting elective. We use it ourselves for masters students and third-year undergraduate students at Monash University, Australia.


For most sections, we only assume that readers are familiar with introductory statistics, and with high-school algebra. There are a couple of sections that also require knowledge of matrices, but these are flagged.


At the end of each chapter we provide a list of “further reading”. In general, these lists comprise suggested textbooks that provide a more advanced or detailed treatment of the subject. Where there is no suitable textbook, we suggest journal articles that provide more information.


We use R throughout the book and we intend students to learn how to forecast with R. R is free and available on almost every operating system. It is a wonderful tool for all statistical analysis, not just for forecasting. See theUsing R appendixfor instructions on installing and using R.


All R examples in the book assume you have loaded thefpp3package first:


```
library(fpp3)
```


```
#> ── Attaching packages ──────────────────────────────── fpp3 1.0.3 ──
#> ✔ tibble      3.3.1     ✔ tsibble     1.2.0
#> ✔ dplyr       1.2.1     ✔ tsibbledata 0.4.1
#> ✔ tidyr       1.3.2     ✔ ggtime      0.2.0
#> ✔ lubridate   1.9.5     ✔ feasts      0.5.0
#> ✔ ggplot2     4.0.3     ✔ fable       0.5.0
#> ── Conflicts ───────────────────────────────────── fpp3_conflicts ──
#> ✖ lubridate::date()    masks base::date()
#> ✖ dplyr::filter()      masks stats::filter()
#> ✖ tsibble::intersect() masks base::intersect()
#> ✖ tsibble::interval()  masks lubridate::interval()
#> ✖ dplyr::lag()         masks stats::lag()
#> ✖ tsibble::setdiff()   masks base::setdiff()
#> ✖ tsibble::union()     masks base::union()
```


This will load the relevant data sets, and attach several packages as listed above. These include severaltidyversepackages, and packages to handle time series and forecasting in a “tidy” framework.


The above output also shows the package versions we have used in compiling this edition of the book. Some examples in the book will not work with earlier versions of the packages.


Finally, the output lists some conflicts showing which function will be preferenced when a function of the same name is in multiple packages.


The book is different from other forecasting textbooks in several ways.

- It is free and online, making it accessible to a wide audience.
- It uses R, which is free, open-source, and extremely powerful software.
- The online version is continuously updated. You don’t have to wait until the next edition for errors to be removed or new methods to be discussed. We will update the book frequently.
- There are dozens of real data examples taken from our own consulting practice. We have worked with hundreds of businesses and organisations helping them with forecasting issues, and this experience has contributed directly to many of the examples given here, as well as guiding our general philosophy of forecasting.
- We emphasise graphical methods more than most forecasters. We use graphs to explore the data, analyse the validity of the models fitted and present the forecasting results.

### Changes in the third edition


The most important change in edition 3 of the book is that we use thetsibbleandfablepackages rather than theforecastpackage. This allows us to integrate closely with thetidyversecollection of packages. As a consequence, we have replaced many examples to take advantage of the new facilities.


We have also added some new material on time series features, and reorganised the content so Chapters2–4discuss exploratory analysis of time series, before we introduce any forecasting methods. This is because we should first have a good understanding of our time series, their patterns and characteristics, before we attempt to build any models and produce any forecasts.


In the online version of the book, we have included some videos at the start of most sections. These are intended to complement the written material in each section. You can view theentire playlist on YouTube.


Helpful readers of the earlier versions of the book let us know of any typos or errors they had found. These were updated immediately online. No doubt we have introduced some new mistakes, and we will correct them online as soon as they are spotted. Please continue tolet us knowabout such things.


If you have questions about using the R packages discussed in this book, or about forecasting in general, please ask on theOTexts discussion forum.


Happy forecasting!


Rob J Hyndman and George Athanasopoulos


May 2021


To cite the online version of this book, please use the following:


> Hyndman, R.J., & Athanasopoulos, G. (2021)Forecasting: principles and practice, 3rd edition, OTexts: Melbourne, Australia. OTexts.com/fpp3. Accessed on<current date>.


Hyndman, R.J., & Athanasopoulos, G. (2021)Forecasting: principles and practice, 3rd edition, OTexts: Melbourne, Australia. OTexts.com/fpp3. Accessed on<current date>.


> This online version of the book was last updated on 3 May 2026.The print version of the book (available from Amazon) was last updated on 31 May 2021.


This online version of the book was last updated on 3 May 2026.


The print version of the book (available from Amazon) was last updated on 31 May 2021.
