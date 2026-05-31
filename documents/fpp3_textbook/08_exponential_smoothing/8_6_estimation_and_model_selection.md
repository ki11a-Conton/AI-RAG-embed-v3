
# Forecasting: Principles and Practice(3rd ed)


## 8.6Estimation and model selection


### Estimating ETS models


An alternative to estimating the parameters by minimising the sum of squared errors is to maximise the “likelihood.” The likelihood is the probability of the data arising from the specified model. Thus, a large likelihood is associated with a good model. For an additive error model, maximising the likelihood (assuming normally distributed errors) gives the same results as minimising the sum of squared errors. However, different results will be obtained for multiplicative error models. In this section, we will estimate the smoothing parameters\(\alpha\),\(\beta\),\(\gamma\)and\(\phi\), and the initial states\(\ell_0\),\(b_0\),\(s_0,s_{-1},\dots,s_{-m+1}\), by maximising the likelihood.


The possible values that the smoothing parameters can take are restricted. Traditionally, the parameters have been constrained to lie between 0 and 1 so that the equations can be interpreted as weighted averages. That is,\(0< \alpha,\beta^*,\gamma^*,\phi<1\). For the state space models, we have set\(\beta=\alpha\beta^*\)and\(\gamma=(1-\alpha)\gamma^*\). Therefore, the traditional restrictions translate to\(0< \alpha <1\),\(0 < \beta < \alpha\)and\(0< \gamma < 1-\alpha\). In practice, the damping parameter\(\phi\)is usually constrained further to prevent numerical difficulties in estimating the model. In thefablepackage, it is restricted so that\(0.8<\phi<0.98\).


Another way to view the parameters is through a consideration of the mathematical properties of the state space models. The parameters are constrained in order to prevent observations in the distant past having a continuing effect on current forecasts. This leads to someadmissibilityconstraints on the parameters, which are usually (but not always) less restrictive than the traditional constraints region(Hyndman et al., 2008, p. Ch10). For example, for the ETS(A,N,N) model, the traditional parameter region is\(0< \alpha <1\)but the admissible region is\(0< \alpha <2\). For the ETS(A,A,N) model, the traditional parameter region is\(0<\alpha<1\)and\(0<\beta<\alpha\)but the admissible region is\(0<\alpha<2\)and\(0<\beta<4-2\alpha\).


### Model selection


A great advantage of the ETS statistical framework is that information criteria can be used for model selection. The AIC, AIC\(_{\text{c}}\)and BIC, introduced in Section7.5, can be used here to determine which of the ETS models is most appropriate for a given time series.


For ETS models, Akaike’s Information Criterion (AIC) is defined as\[
  \text{AIC} = -2\log(L) + 2k,
\]where\(L\)is the likelihood of the model and\(k\)is the total number of parameters and initial states that have been estimated (including the residual variance).


The AIC corrected for small sample bias (AIC\(_\text{c}\)) is defined as\[
  \text{AIC}_{\text{c}} = \text{AIC} + \frac{2k(k+1)}{T-k-1},
\]and the Bayesian Information Criterion (BIC) is\[
  \text{BIC} = \text{AIC} + k[\log(T)-2].
\]


Three of the combinations of (Error, Trend, Seasonal) can lead to numerical difficulties. Specifically, the models that can cause such instabilities are ETS(A,N,M), ETS(A,A,M), and ETS(A,A\(_d\),M), due to division by values potentially close to zero in the state equations. We normally do not consider these particular combinations when selecting a model.


Models with multiplicative errors are useful when the data are strictly positive, but are not numerically stable when the data contain zeros or negative values. Therefore, multiplicative error models will not be considered if the time series is not strictly positive. In that case, only the six fully additive models will be applied.


### Example: Domestic holiday tourist visitor nights in Australia


We now employ the ETS statistical framework to forecast Australian holiday tourism over the period 2016–2019. We let theETS()function select the model by minimising the AICc.


```
aus_holidays <- tourism %>%
  filter(Purpose == "Holiday") %>%
  summarise(Trips = sum(Trips)/1e3)
fit <- aus_holidays %>%
  model(ETS(Trips))
report(fit)
#> Series: Trips 
#> Model: ETS(M,N,A) 
#>   Smoothing parameters:
#>     alpha = 0.3484 
#>     gamma = 1e-04 
#> 
#>   Initial states:
#>   l[0]    s[0]   s[-1]   s[-2] s[-3]
#>  9.727 -0.5376 -0.6884 -0.2934 1.519
#> 
#>   sigma^2:  0.0022
#> 
#>   AIC  AICc   BIC 
#> 226.2 227.8 242.9
```


The model selected is ETS(M,N,A)\[\begin{align*}
y_{t} &= (\ell_{t-1}+s_{t-m})(1 + \varepsilon_t)\\
\ell_t &= \ell_{t-1} + \alpha(\ell_{t-1}+s_{t-m})\varepsilon_t\\
s_t &=  s_{t-m} + \gamma(\ell_{t-1}+s_{t-m}) \varepsilon_t.
\end{align*}\]


The parameter estimates are\(\hat\alpha= 0.3484\), and\(\hat\gamma=0.0001\). The output also returns the estimates for the initial states\(\ell_0\),\(s_{0}\),\(s_{-1}\),\(s_{-2}\)and\(s_{-3}.\)Compare these with the values obtained for the Holt-Winters method with additive seasonality presented in Table8.3.


Figure8.10shows the states over time, while Figure8.12shows point forecasts and prediction intervals generated from the model. The small values of\(\gamma\)indicate that the seasonal components change very little over time.


```
components(fit) %>%
  autoplot() +
  labs(title = "ETS(M,N,A) components")
```


Figure 8.10: Graphical representation of the estimated states over time.


Because this model has multiplicative errors, the innovation residuals are not equivalent to the regular residuals (i.e., the one-step training errors). The innovation residuals are given by\(\hat{\varepsilon}_t\), while the regular residuals are defined as\(y_t - \hat{y}_{t|t-1}\). We can obtain both using theaugment()function. They are plotted in Figure8.11.


Figure 8.11: Residuals and one-step forecast errors from the ETS(M,N,A) model.


### Bibliography
