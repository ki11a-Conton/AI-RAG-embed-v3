
# Forecasting: Principles and Practice(3rd ed)


## 8.4A taxonomy of exponential smoothing methods


Exponential smoothing methods are not restricted to those we have presented so far. By considering variations in the combinations of the trend and seasonal components, nine exponential smoothing methods are possible, listed in Table8.5. Each method is labelled by a pair of letters (T,S) defining the type of ‘Trend’ and ‘Seasonal’ components. For example, (A,M) is the method with an additive trend and multiplicative seasonality; (A\(_d\),N) is the method with damped trend and no seasonality; and so on.


Some of these methods we have already seen using other names:


This type of classification was first proposed byPegels (1969), who also included a method with a multiplicative trend. It was later extended byGardner (1985)to include methods with an additive damped trend and byJ. W. Taylor (2003)to include methods with a multiplicative damped trend. We do not consider the multiplicative trend methods in this book as they tend to produce poor forecasts. SeeHyndman et al. (2008)for a more thorough discussion of all exponential smoothing methods.


Table8.6gives the recursive formulas for applying the nine exponential smoothing methods in Table8.5. Each cell includes the forecast equation for generating\(h\)-step-ahead forecasts, and the smoothing equations for applying the method.


### Bibliography
