
# Forecasting: Principles and Practice(3rd ed)


## 7.9Matrix formulation


Warning: this is a more advanced, optional section and assumes knowledge of matrix algebra.


Recall that multiple regression model can be written as\[
  y_{t} = \beta_{0} + \beta_{1} x_{1,t} + \beta_{2} x_{2,t} + \cdots +
  \beta_{k} x_{k,t} + \varepsilon_{t}
\]where\(\varepsilon_{t}\)has mean zero and variance\(\sigma^2\). This expresses the relationship between a single value of the forecast variable and the predictors.


It can be convenient to write this in matrix form where all the values of the forecast variable are given in a single equation. Let\(\bm{y} = (y_{1},\dots,y_{T})'\),\(\bm{\varepsilon} = (\varepsilon_{1},\dots,\varepsilon_{T})'\),\(\bm{\beta} = (\beta_{0},\dots,\beta_{k})'\)and\[
  \bm{X} = \left[
    \begin{matrix}
      1 & x_{1,1} & x_{2,1} & \dots & x_{k,1}\\
      1 & x_{1,2} & x_{2,2} & \dots & x_{k,2}\\
      \vdots& \vdots& \vdots&& \vdots\\
      1 & x_{1,T}& x_{2,T}& \dots& x_{k,T}
    \end{matrix}\right].
\]Then\[
  \bm{y} = \bm{X}\bm{\beta} + \bm{\varepsilon}
\]where\(\bm{\varepsilon}\)has mean\(\bm{0}\)and variance\(\sigma^2\bm{I}\). Note that the\(\bm{X}\)matrix has\(T\)rows reflecting the number of observations and\(k+1\)columns reflecting the intercept which is represented by the column of ones plus the number of predictors.


### Least squares estimation


Least squares estimation is performed by minimising the expression\(\bm{\varepsilon}'\bm{\varepsilon} = (\bm{y} - \bm{X}\bm{\beta})'(\bm{y} - \bm{X}\bm{\beta})\). It can be shown that this is minimised when\(\bm{\beta}\)takes the value\[
  \hat{\bm{\beta}} = (\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}.
\]This is sometimes known as the “normal equation”. The estimated coefficients require the inversion of the matrix\(\bm{X}'\bm{X}\). If\(\bm{X}\)is not of full column rank then matrix\(\bm{X}'\bm{X}\)is singular and the model cannot be estimated. This will occur, for example, if you fall for the “dummy variable trap”, i.e., having the same number of dummy variables as there are categories of a categorical predictor, as discussed in Section7.4.


The residual variance is estimated using\[
  \hat{\sigma}_e^2 = \frac{1}{T-k-1}(\bm{y} - \bm{X}\hat{\bm{\beta}})'
  (\bm{y} - \bm{X}\hat{\bm{\beta}}).
\]


### Fitted values and cross-validation


The normal equation shows that the fitted values can be calculated using\[
  \bm{\hat{y}} = \bm{X}\hat{\bm{\beta}} = \bm{X}(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y} = \bm{H}\bm{y},
\]where\(\bm{H} = \bm{X}(\bm{X}'\bm{X})^{-1}\bm{X}'\)is known as the “hat-matrix” because it is used to compute\(\bm{\hat{y}}\)(“y-hat”).


If the diagonal values of\(\bm{H}\)are denoted by\(h_{1},\dots,h_{T}\), then the cross-validation statistic can be computed using\[
  \text{CV} = \frac{1}{T}\sum_{t=1}^T [e_{t}/(1-h_{t})]^2,
\]where\(e_{t}\)is the residual obtained from fitting the model to all\(T\)observations. Thus, it is not necessary to actually fit\(T\)separate models when computing the CV statistic.


### Forecasts and prediction intervals


Let\(\bm{x}^*\)be a row vector containing the values of the predictors (in the same format as\(\bm{X}\)) for which we want to generate a forecast. Then the forecast is given by\[
  \hat{y} = \bm{x}^*\hat{\bm{\beta}}=\bm{x}^*(\bm{X}'\bm{X})^{-1}\bm{X}'\bm{y}
\]and the estimated forecast variance is given by\[
  \hat\sigma_e^2 \left[1 + \bm{x}^* (\bm{X}'\bm{X})^{-1} (\bm{x}^*)'\right].
\]A 95% prediction interval can be calculated (assuming normally distributed errors) as\[
  \hat{y} \pm 1.96 \hat{\sigma}_e \sqrt{1 + \bm{x}^* (\bm{X}'\bm{X})^{-1} (\bm{x}^*)'}.
\]This takes into account the uncertainty due to the error term\(\varepsilon\)and the uncertainty in the coefficient estimates. However, it ignores any errors in\(\bm{x}^*\). Thus, if the future values of the predictors are uncertain, then the prediction interval calculated using this expression will be too narrow.
