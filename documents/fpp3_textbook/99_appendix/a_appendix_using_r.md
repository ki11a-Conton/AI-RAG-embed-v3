
# Forecasting: Principles and Practice(3rd ed)


# Appendix: Using R


This book uses R and is designed to be used with R. R is free, available on almost every operating system, and there are thousands of add-on packages to do almost anything you could ever want to do. We recommend you use R with RStudio.


### Installing R and RStudio

- Download and install R.
- Download and install RStudio.
- Run RStudio. On the “Packages” tab, click on “Install” and install the packagefpp3(make sure “install dependencies” is checked).

That’s it! You should now be ready to go.


### R examples in this book


We provide R code for most examples in shaded boxes like this:


```
# Load required packages
library(fpp3)

# Plot one time series
aus_retail |>
  filter(`Series ID`=="A3349640L") |>
  autoplot(Turnover)

# Produce some forecasts
aus_retail |>
  filter(`Series ID`=="A3349640L") |>
  model(ETS(Turnover)) |>
  forecast(h = "2 years")
```


These examples assume that you have thefpp3package loaded as shown above. This needs to be done at the start of every R session, but it won’t be included in our examples.


Sometimes we assume that the R code that appears earlier in the same chapter of the book has also been run; so it is best to work through the R code in the order provided within each chapter.


### Getting started with R


If you have never previously used R, please work through the first section (chapters 1-8) of“R for Data Science”by Garrett Grolemund and Hadley Wickham. While this does not cover time series or forecasting, it will get you used to the basics of the R language, and thetidyversepackages. TheCoursera R Programmingcourse is also highly recommended.


You will learn how to use R for forecasting using the exercises in this book.
