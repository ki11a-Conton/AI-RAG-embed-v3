
# Forecasting: Principles and Practice(3rd ed)


## 9.7ARIMA modelling infable


### How doesARIMA()work?


TheARIMA()function in thefablepackage uses a variation of the Hyndman-Khandakar algorithm(Hyndman & Khandakar, 2008), which combines unit root tests, minimisation of the AICc and MLE to obtain an ARIMA model. The arguments toARIMA()provide for many variations on the algorithm. What is described here is the default behaviour.

- The number of differences\(0 \le d\le 2\)is determined using repeated KPSS tests.
- The values of\(p\)and\(q\)are then chosen by minimising the AICc after differencing the data\(d\)times. Rather than considering every possible combination of\(p\)and\(q\), the algorithm uses a stepwise search to traverse the model space.
- Four initial models are fitted:ARIMA\((0,d,0)\),ARIMA\((2,d,2)\),ARIMA\((1,d,0)\),ARIMA\((0,d,1)\).A constant is included unless\(d=2\). If\(d \le 1\), an additional model is also fitted:ARIMA\((0,d,0)\)without a constant.
- ARIMA\((0,d,0)\),
- ARIMA\((2,d,2)\),
- ARIMA\((1,d,0)\),
- ARIMA\((0,d,1)\).
- ARIMA\((0,d,0)\)without a constant.
- The best model (with the smallest AICc value) fitted in step (a) is set to be the “current model”.
- Variations on the current model are considered:vary\(p\)and/or\(q\)from the current model by\(\pm1\);include/exclude\(c\)from the current model.The best model considered so far (either the current model or one of these variations) becomes the new current model.
- vary\(p\)and/or\(q\)from the current model by\(\pm1\);
- include/exclude\(c\)from the current model.
- Repeat Step 2(c) until no lower AICc can be found.

Figure 9.11: An illustrative example of the Hyndman-Khandakar stepwise search process


Figure9.11illustrates diagrammatically how the Hyndman-Khandakar algorithm traverses the space of the ARMA orders, through an example. The grid covers combinations of ARMA(\(p,q\)) orders starting from the top-left corner with an ARMA(\(0,0\)), with the AR order increasing down the vertical axis, and the MA order increasing across the horizontal axis.


The orange cells show the initial set of models considered by the algorithm. In this example, the ARMA(2,2) model has the lowest AICc value amongst these models. This is called the “current model” and is shown by the black circle. The algorithm then searches over neighbouring models as shown by the blue arrows. If a better model is found then this becomes the new “current model”. In this example, the new “current model” is the ARMA(3,3) model. The algorithm continues in this fashion until no better model can be found. In this example the model returned is an ARMA(4,2) model.


The default procedure will switch to a new “current model” as soon as a better model is identified, without going through all the neighbouring models. The full neighbourhood search is done whengreedy=FALSE.


The default procedure also uses some approximations to speed up the search. These approximations can be avoided with the argumentapproximation=FALSE. It is possible that the minimum AICc model will not be found due to these approximations, or because of the use of the stepwise procedure. A much larger set of models will be searched if the argumentstepwise=FALSEis used. See the help file for a full description of the arguments.


### Modelling procedure


When fitting an ARIMA model to a set of (non-seasonal) time series data, the following procedure provides a useful general approach.

- Plot the data and identify any unusual observations.
- If necessary, transform the data (using a Box-Cox transformation) to stabilise the variance.
- If the data are non-stationary, take first differences of the data until the data are stationary.
- Examine the ACF/PACF: Is an ARIMA(\(p,d,0\)) or ARIMA(\(0,d,q\)) model appropriate?
- Try your chosen model(s), and use the AICc to search for a better model.
- Check the residuals from your chosen model by plotting the ACF of the residuals, and doing a portmanteau test of the residuals. If they do not look like white noise, try a modified model.
- Once the residuals look like white noise, calculate forecasts.

The Hyndman-Khandakar algorithm only takes care of steps 3–5. So even if you use it, you will still need to take care of the other steps yourself.


The process is summarised in Figure9.12.


Figure 9.12: General process for forecasting using an ARIMA model.


### Portmanteau tests of residuals for ARIMA models


With ARIMA models, more accurate portmanteau tests are obtained if the degrees of freedom of the test statistic are adjusted to take account of the number of parameters in the model. Specifically, we use\(\ell - K\)degrees of freedom in the test, where\(\ell\)is the number of lags used in the test, and\(K\)is the number of AR and MA parameters in the model. So for the non-seasonal models that we have considered so far,\(K=p+q\). The value of\(K\)is passed to theljung_boxfunction via the argumentdof, as shown in the example below.


### Example: Central African Republic exports


We will apply this procedure to the exports of the Central African Republic shown in Figure9.13.


```
global_economy |>
  filter(Code == "CAF") |>
  autoplot(Exports) +
  labs(title="Central African Republic exports",
       y="% of GDP")
```


Figure 9.13: Exports of the Central African Republic as a percentage of GDP.

- The time plot shows some non-stationarity, with an overall decline. The improvement in 1994 was due to a new government which overthrew the military junta and had some initial success, before unrest caused further economic decline.

The time plot shows some non-stationarity, with an overall decline. The improvement in 1994 was due to a new government which overthrew the military junta and had some initial success, before unrest caused further economic decline.

- There is no evidence of changing variance, so we will not do a Box-Cox transformation.

There is no evidence of changing variance, so we will not do a Box-Cox transformation.

- To address the non-stationarity, we will take a first difference of the data. The differenced data are shown in Figure9.14.global_economy|>filter(Code=="CAF")|>gg_tsdisplay(difference(Exports),plot_type='partial')Figure 9.14: Time plot and ACF and PACF plots for the differenced Central African Republic Exports.These now appear to be stationary.

To address the non-stationarity, we will take a first difference of the data. The differenced data are shown in Figure9.14.


```
global_economy |>
  filter(Code == "CAF") |>
  gg_tsdisplay(difference(Exports), plot_type='partial')
```


Figure 9.14: Time plot and ACF and PACF plots for the differenced Central African Republic Exports.


These now appear to be stationary.

- The PACF shown in Figure9.14is suggestive of an AR(2) model; so an initial candidate model is an ARIMA(2,1,0). The ACF suggests an MA(3) model; so an alternative candidate is an ARIMA(0,1,3).

The PACF shown in Figure9.14is suggestive of an AR(2) model; so an initial candidate model is an ARIMA(2,1,0). The ACF suggests an MA(3) model; so an alternative candidate is an ARIMA(0,1,3).

- We fit both an ARIMA(2,1,0) and an ARIMA(0,1,3) model along with two automated model selections, one using the default stepwise procedure, and one working harder to search a larger model space.caf_fit<-global_economy|>filter(Code=="CAF")|>model(arima210 =ARIMA(Exports~pdq(2,1,0)),arima013 =ARIMA(Exports~pdq(0,1,3)),stepwise =ARIMA(Exports),search =ARIMA(Exports,stepwise=FALSE))caf_fit|>pivot_longer(!Country,names_to ="Model name",values_to ="Orders")#> # A mable: 4 x 3#> # Key:     Country, Model name [4]#>   Country                  `Model name`         Orders#>   <fct>                    <chr>               <model>#> 1 Central African Republic arima210     <ARIMA(2,1,0)>#> 2 Central African Republic arima013     <ARIMA(0,1,3)>#> 3 Central African Republic stepwise     <ARIMA(2,1,2)>#> 4 Central African Republic search       <ARIMA(3,1,0)>glance(caf_fit)|>arrange(AICc)|>select(.model:BIC)#> # A tibble: 4 × 6#>   .model   sigma2 log_lik   AIC  AICc   BIC#>   <chr>     <dbl>   <dbl> <dbl> <dbl> <dbl>#> 1 search     6.52   -133.  274.  275.  282.#> 2 arima210   6.71   -134.  275.  275.  281.#> 3 arima013   6.54   -133.  274.  275.  282.#> 4 stepwise   6.42   -132.  274.  275.  284.The four models have almost identical AICc values. Of the models fitted, the full search has found that an ARIMA(3,1,0) gives the lowest AICc value, closely followed by the ARIMA(2,1,0) and ARIMA(0,1,3) — the latter two being the models that we guessed from the ACF and PACF plots. The automated stepwise selection has identified an ARIMA(2,1,2) model, which has the highest AICc value of the four models.

We fit both an ARIMA(2,1,0) and an ARIMA(0,1,3) model along with two automated model selections, one using the default stepwise procedure, and one working harder to search a larger model space.


```
caf_fit <- global_economy |>
  filter(Code == "CAF") |>
  model(arima210 = ARIMA(Exports ~ pdq(2,1,0)),
        arima013 = ARIMA(Exports ~ pdq(0,1,3)),
        stepwise = ARIMA(Exports),
        search = ARIMA(Exports, stepwise=FALSE))

caf_fit |> pivot_longer(!Country, names_to = "Model name",
                         values_to = "Orders")
#> # A mable: 4 x 3
#> # Key:     Country, Model name [4]
#>   Country                  `Model name`         Orders
#>   <fct>                    <chr>               <model>
#> 1 Central African Republic arima210     <ARIMA(2,1,0)>
#> 2 Central African Republic arima013     <ARIMA(0,1,3)>
#> 3 Central African Republic stepwise     <ARIMA(2,1,2)>
#> 4 Central African Republic search       <ARIMA(3,1,0)>
glance(caf_fit) |> arrange(AICc) |> select(.model:BIC)
#> # A tibble: 4 × 6
#>   .model   sigma2 log_lik   AIC  AICc   BIC
#>   <chr>     <dbl>   <dbl> <dbl> <dbl> <dbl>
#> 1 search     6.52   -133.  274.  275.  282.
#> 2 arima210   6.71   -134.  275.  275.  281.
#> 3 arima013   6.54   -133.  274.  275.  282.
#> 4 stepwise   6.42   -132.  274.  275.  284.
```


The four models have almost identical AICc values. Of the models fitted, the full search has found that an ARIMA(3,1,0) gives the lowest AICc value, closely followed by the ARIMA(2,1,0) and ARIMA(0,1,3) — the latter two being the models that we guessed from the ACF and PACF plots. The automated stepwise selection has identified an ARIMA(2,1,2) model, which has the highest AICc value of the four models.

- The ACF plot of the residuals from the ARIMA(3,1,0) model shows that all autocorrelations are within the threshold limits, indicating that the residuals are behaving like white noise.caf_fit|>select(search)|>gg_tsresiduals()Figure 9.15: Residual plots for the ARIMA(3,1,0) model.A portmanteau test (setting\(K = 3\)) returns a large p-value, also suggesting that the residuals are white noise.augment(caf_fit)|>filter(.model=='search')|>features(.innov, ljung_box,lag =10,dof =3)#> # A tibble: 1 × 4#>   Country                  .model lb_stat lb_pvalue#>   <fct>                    <chr>    <dbl>     <dbl>#> 1 Central African Republic search    5.75     0.569

The ACF plot of the residuals from the ARIMA(3,1,0) model shows that all autocorrelations are within the threshold limits, indicating that the residuals are behaving like white noise.


```
caf_fit |>
  select(search) |>
  gg_tsresiduals()
```


Figure 9.15: Residual plots for the ARIMA(3,1,0) model.


A portmanteau test (setting\(K = 3\)) returns a large p-value, also suggesting that the residuals are white noise.


```
augment(caf_fit) |>
  filter(.model=='search') |>
  features(.innov, ljung_box, lag = 10, dof = 3)
#> # A tibble: 1 × 4
#>   Country                  .model lb_stat lb_pvalue
#>   <fct>                    <chr>    <dbl>     <dbl>
#> 1 Central African Republic search    5.75     0.569
```

- Forecasts from the chosen model are shown in Figure9.16.caf_fit|>forecast(h=5)|>filter(.model=='search')|>autoplot(global_economy)Figure 9.16: Forecasts for the Central African Republic Exports.Note that the mean forecasts look very similar to what we would get with a random walk (equivalent to an ARIMA(0,1,0)). The extra work to include AR and MA terms has made little difference to the point forecasts in this example, although the prediction intervals are much narrower than for a random walk model.

Forecasts from the chosen model are shown in Figure9.16.


```
caf_fit |>
  forecast(h=5) |>
  filter(.model=='search') |>
  autoplot(global_economy)
```


Figure 9.16: Forecasts for the Central African Republic Exports.


Note that the mean forecasts look very similar to what we would get with a random walk (equivalent to an ARIMA(0,1,0)). The extra work to include AR and MA terms has made little difference to the point forecasts in this example, although the prediction intervals are much narrower than for a random walk model.


### Understanding constants in R


A non-seasonal ARIMA model can be written as\[\begin{equation}
\tag{9.3}
  (1-\phi_1B - \cdots - \phi_p B^p)(1-B)^d y_t = c + (1 + \theta_1 B + \cdots + \theta_q B^q)\varepsilon_t,
\end{equation}\]or equivalently as\[\begin{equation}
\tag{9.4}
  (1-\phi_1B - \cdots - \phi_p B^p)(1-B)^d (y_t - \mu t^d/d!) = (1 + \theta_1 B + \cdots + \theta_q B^q)\varepsilon_t,
\end{equation}\]where\(c = \mu(1-\phi_1 - \cdots - \phi_p )\)and\(\mu\)is the mean of\((1-B)^d y_t\). Thefablepackage uses the parameterisation of Equation(9.3)while most other R implementations use Equation(9.4).


Thus, the inclusion of a constant in a non-stationary ARIMA model is equivalent to inducing a polynomial trend of order\(d\)in the forecasts. (If the constant is omitted, the forecasts include a polynomial trend of order\(d-1\).) When\(d=0\), we have the special case that\(\mu\)is the mean of\(y_t\).


By default, theARIMA()function will automatically determine if a constant should be included. For\(d=0\)or\(d=1\), a constant will be included if it improves the AICc value. If\(d>1\)the constant is always omitted as a quadratic or higher order trend is particularly dangerous when forecasting.


The constant can be specified by including0or1in the model formula (like the intercept inlm()). For example, to automatically select an ARIMA model with a constant, you could useARIMA(y ~ 1 + ...). Similarly, a constant can be excluded withARIMA(y ~ 0 + ...).


### Plotting the characteristic roots


(This is a more advanced section and can be skipped if desired.)


We can re-write Equation(9.3)as\[\phi(B) (1-B)^d y_t = c + \theta(B) \varepsilon_t\]where\(\phi(B)=  (1-\phi_1B - \cdots - \phi_p B^p)\)is a\(p\)th order polynomial in\(B\)and\(\theta(B) = (1 + \theta_1 B + \cdots + \theta_q B^q)\)is a\(q\)th order polynomial in\(B\).


The stationarity conditions for the model are that the\(p\)complex roots of\(\phi(B)\)lie outside the unit circle, and the invertibility conditions are that the\(q\)complex roots of\(\theta(B)\)lie outside the unit circle. So we can see whether the model is close to invertibility or stationarity by a plot of the roots in relation to the complex unit circle.


It is easier to plot the inverse roots instead, as they should all liewithinthe unit circle. This is easily done in R. For the ARIMA(3,1,0) model fitted to the Central African Republic Exports, we obtain Figure9.17.


```
gg_arma(caf_fit |> select(Country, search))
```


Figure 9.17: Inverse characteristic roots for the ARIMA(3,1,0) model fitted to the Central African Republic Exports.


The three orange dots in the plot correspond to the roots of the polynomials\(\phi(B)\). They are all inside the unit circle, as we would expect becausefableensures the fitted model is both stationary and invertible. Any roots close to the unit circle may be numerically unstable, and the corresponding model will not be good for forecasting.


TheARIMA()function will never return a model with inverse roots outside the unit circle. Models automatically selected by theARIMA()function will not contain roots close to the unit circle either. Consequently, it is sometimes possible to find a model with better AICc value thanARIMA()will return, but such models will be potentially problematic.


### Bibliography
