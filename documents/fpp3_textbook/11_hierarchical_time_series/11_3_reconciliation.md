
# Forecasting: Principles and Practice(3rd ed)


## 11.3Forecast reconciliation


Warning: the rest of this chapter is more advanced and assumes a knowledge of some basic matrix algebra.


### Matrix notation


Recall that Equations(11.1)and(11.2)represent how data, that adhere to the hierarchical structure of Figure11.1, aggregate. Similarly(11.3)and(11.4)represent how data, that adhere to the grouped structure of Figure11.6, aggregate. These equations can be thought of as aggregation constraints or summing equalities, and can be more efficiently represented using matrix notation.


For any aggregation structure we construct an\(n\times m\)matrix\(\bm{S}\)(referred to as the “summing matrix”) which dictates the way in which the bottom-level series aggregate.


For the hierarchical structure in Figure11.1, we can write\[
  \begin{bmatrix}
    y_{t} \\
    \y{A}{t} \\
    \y{B}{t} \\
    \y{AA}{t} \\
    \y{AB}{t} \\
    \y{AC}{t} \\
    \y{BA}{t} \\
    \y{BB}{t}
  \end{bmatrix}
  =
  \begin{bmatrix}
    1 & 1 & 1 & 1 & 1 \\
    1 & 1 & 1 & 0 & 0 \\
    0 & 0 & 0 & 1 & 1 \\
    1  & 0  & 0  & 0  & 0  \\
    0  & 1  & 0  & 0  & 0  \\
    0  & 0  & 1  & 0  & 0  \\
    0  & 0  & 0  & 1  & 0  \\
    0  & 0  & 0  & 0  & 1
  \end{bmatrix}
  \begin{bmatrix}
    \y{AA}{t} \\
    \y{AB}{t} \\
    \y{AC}{t} \\
    \y{BA}{t} \\
    \y{BB}{t}
  \end{bmatrix}
\]or in more compact notation\[\begin{equation}
  \bm{y}_t=\bm{S}\bm{b}_{t},
  \tag{11.5}
\end{equation}\]where\(\bm{y}_t\)is an\(n\)-dimensional vector of all the observations in the hierarchy at time\(t\),\(\bm{S}\)is the summing matrix, and\(\bm{b}_{t}\)is an\(m\)-dimensional vector of all the observations in the bottom level of the hierarchy at time\(t\). Note that the first row in the summing matrix\(\bm{S}\)represents Equation(11.1), the second and third rows represent(11.2). The rows below these comprise an\(m\)-dimensional identity matrix\(\bm{I}_m\)so that each bottom-level observation on the right hand side of the equation is equal to itself on the left hand side.


Similarly for the grouped structure of Figure11.6we write\[
  \begin{bmatrix}
    y_{t} \\
    \y{A}{t} \\
    \y{B}{t} \\
    \y{X}{t} \\
    \y{Y}{t} \\
    \y{AX}{t} \\
    \y{AY}{t} \\
    \y{BX}{t} \\
    \y{BY}{t}
  \end{bmatrix}
  =
  \begin{bmatrix}
    1 & 1 & 1 & 1 \\
    1 & 1 & 0 & 0 \\
    0 & 0 & 1 & 1 \\
    1 & 0 & 1 & 0 \\
    0 & 1 & 0 & 1 \\
    1 & 0 & 0 & 0 \\
    0 & 1 & 0 & 0 \\
    0 & 0 & 1 & 0 \\
    0 & 0 & 0 & 1
  \end{bmatrix}
  \begin{bmatrix}
    \y{AX}{t} \\
    \y{AY}{t} \\
    \y{BX}{t} \\
    \y{BY}{t}
  \end{bmatrix},
\]or\[\begin{equation}
  \bm{y}_t=\bm{S}\bm{b}_{t},
  \tag{11.6}
\end{equation}\]where the second and third rows of\(\bm{S}\)represent Equation(11.3)and the fourth and fifth rows represent(11.4).


### Mapping matrices


This matrix notation allows us to represent all forecasting methods for hierarchical or grouped time series using a common notation.


Suppose we forecast all series ignoring any aggregation constraints. We call these thebase forecastsand denote them by\(\hat{\bm{y}}_h\)where\(h\)is the forecast horizon. They are stacked in the same order as the data\(\bm{y}_t\).


Then all coherent forecasting approaches for either hierarchical or grouped structures can be represented as23\[\begin{equation}
  \tilde{\bm{y}}_h=\bm{S}\bm{G}\hat{\bm{y}}_h,
  \tag{11.7}
\end{equation}\]where\(\bm{G}\)is a matrix that maps the base forecasts into the bottom level, and the summing matrix\(\bm{S}\)sums these up using the aggregation structure to produce a set ofcoherent forecasts\(\tilde{\bm{y}}_h\).


The\(\bm{G}\)matrix is defined according to the approach implemented. For example if the bottom-up approach is used to forecast the hierarchy of Figure11.1, then\[\bm{G}=
  \begin{bmatrix}
    0 & 0 & 0 & 1 & 0 & 0 & 0 & 0\\
    0 & 0 & 0 & 0 & 1 & 0 & 0 & 0\\
    0 & 0 & 0 & 0 & 0 & 1 & 0 & 0\\
    0 & 0 & 0 & 0 & 0 & 0 & 1 & 0\\
    0 & 0 & 0 & 0 & 0 & 0 & 0 & 1\\
  \end{bmatrix}.
  \]Notice that\(\bm{G}\)contains two partitions. The first three columns zero out the base forecasts of the series above the bottom level, while the\(m\)-dimensional identity matrix picks only the base forecasts of the bottom level. These are then summed by the\(\bm{S}\)matrix.


If any of the top-down approaches were used then\[
  \bm{G}=
    \begin{bmatrix}
      p_1 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
      p_2 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
      p_3 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
      p_4 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
      p_5 & 0 & 0 & 0 & 0 & 0 & 0 & 0\\
    \end{bmatrix}.
\]The first column includes the set of proportions that distribute the base forecasts of the top level to the bottom level. These are then summed up by the\(\bm{S}\)matrix. The rest of the columns zero out the base forecasts below the highest level of aggregation.


For a middle out approach, the\(\bm{G}\)matrix will be a combination of the above two. Using a set of proportions, the base forecasts of some pre-chosen level will be disaggregated to the bottom level, all other base forecasts will be zeroed out, and the bottom-level forecasts will then be summed up the hierarchy via the summing matrix.


### Forecast reconciliation


Equation(11.7)shows that pre-multiplying any set of base forecasts with\(\bm{S}\bm{G}\)will return a set of coherent forecasts.


The traditional methods considered so far are limited in that they only use base forecasts from a single level of aggregation which have either been aggregated or disaggregated to obtain forecasts at all other levels. Hence, they use limited information. However, in general, we could use other\(\bm{G}\)matrices, and then\(\bm{S}\bm{G}\)combines and reconciles all the base forecasts in order to produce coherent forecasts.


In fact, we can find the optimal\(\bm{G}\)matrix to give the most accurate reconciled forecasts.


### The MinT optimal reconciliation approach


Wickramasuriya et al. (2019)found a\(\bm{G}\)matrix that minimises the total forecast variance of the set of coherent forecasts, leading to the MinT (Minimum Trace) optimal reconciliation approach.


Suppose we generate coherent forecasts using Equation(11.7). First we want to make sure we have unbiased forecasts. If the base forecasts\(\hat{\bm{y}}_h\)are unbiased, then the coherent forecasts\(\tilde{\bm{y}}_h\)will be unbiased provided24\(\bm{S}\bm{G}\bm{S}=\bm{S}\). This provides a constraint on the matrix\(\bm{G}\). Interestingly, no top-down method satisfies this constraint, so all top-down approaches result in biased coherent forecasts.


Next we need to find the errors in our forecasts.Wickramasuriya et al. (2019)show that the variance-covariance matrix of the\(h\)-step-ahead coherent forecast errors is given by\[\begin{equation*}
\bm{V}_h = \text{Var}[\bm{y}_{T+h}-\tilde{\bm{y}}_h]=\bm{S}\bm{G}\bm{W}_h\bm{G}'\bm{S}'
\end{equation*}\]where\(\bm{W}_h=\text{Var}[(\bm{y}_{T+h}-\hat{\bm{y}}_h)]\)is the variance-covariance matrix of the corresponding base forecast errors.


The objective is to find a matrix\(\bm{G}\)that minimises the error variances of the coherent forecasts. These error variances are on the diagonal of the matrix\(\bm{V}_h\), and so the sum of all the error variances is given by the trace of the matrix\(\bm{V}_h\).Wickramasuriya et al. (2019)show that the matrix\(\bm{G}\)which minimises the trace of\(\bm{V}_h\)such that\(\bm{S}\bm{G}\bm{S}=\bm{S}\), is given by\[
  \bm{G}=(\bm{S}'\bm{W}_h^{-1}\bm{S})^{-1}\bm{S}'\bm{W}_h^{-1}.
\]Therefore, the optimally reconciled forecasts are given by\[\begin{equation}
\tag{11.8}
  \tilde{\bm{y}}_h=\bm{S}(\bm{S}'\bm{W}_h^{-1}\bm{S})^{-1}\bm{S}'\bm{W}_h^{-1}\hat{\bm{y}}_h.
\end{equation}\]


We refer to this as the MinT (or Minimum Trace) optimal reconciliation approach. MinT is implemented bymin_trace()within thereconcile()function.


To use this in practice, we need to estimate\(\bm{W}_h\), the forecast error variance of the\(h\)-step-ahead base forecasts. This can be difficult, and so we provide four simplifying approximations that have been shown to work well in both simulations and in practice.

- Set\(\bm{W}_h=k_h\bm{I}\)for all\(h\), where\(k_{h} > 0\).25This is the most simplifying assumption to make, and means that\(\bm{G}\)is independent of the data, providing substantial computational savings. The disadvantage, however, is that this specification does not account for the differences in scale between the levels of the structure, or for relationships between series.Setting\(\bm{W}_h=k_h\bm{I}\)in(11.8)gives the ordinary least squares (OLS) estimator we introduced in Section7.9with\(\bm{X}=\bm{S}\)and\(\bm{y}=\hat{\bm{y}}\). Hence this approach is usually referred to as OLS reconciliation. It is implemented inmin_trace()by settingmethod = "ols".

Set\(\bm{W}_h=k_h\bm{I}\)for all\(h\), where\(k_{h} > 0\).25This is the most simplifying assumption to make, and means that\(\bm{G}\)is independent of the data, providing substantial computational savings. The disadvantage, however, is that this specification does not account for the differences in scale between the levels of the structure, or for relationships between series.


Setting\(\bm{W}_h=k_h\bm{I}\)in(11.8)gives the ordinary least squares (OLS) estimator we introduced in Section7.9with\(\bm{X}=\bm{S}\)and\(\bm{y}=\hat{\bm{y}}\). Hence this approach is usually referred to as OLS reconciliation. It is implemented inmin_trace()by settingmethod = "ols".

- Set\(\bm{W}_{h} = k_{h}\text{diag}(\hat{\bm{W}}_{1})\)for all\(h\), where\(k_{h} > 0\),\[
     \hat{\bm{W}}_{1} = \frac{1}{T}\sum_{t=1}^{T}\bm{e}_{t}\bm{e}_{t}',
\]and\(\bm{e}_{t}\)is an\(n\)-dimensional vector of residuals of the models that generated the base forecasts stacked in the same order as the data.This specification scales the base forecasts using the variance of the residuals and it is therefore referred to as the WLS (weighted least squares) estimator usingvariance scaling. The approach is implemented inmin_trace()by settingmethod = "wls_var".

Set\(\bm{W}_{h} = k_{h}\text{diag}(\hat{\bm{W}}_{1})\)for all\(h\), where\(k_{h} > 0\),\[
     \hat{\bm{W}}_{1} = \frac{1}{T}\sum_{t=1}^{T}\bm{e}_{t}\bm{e}_{t}',
\]and\(\bm{e}_{t}\)is an\(n\)-dimensional vector of residuals of the models that generated the base forecasts stacked in the same order as the data.


This specification scales the base forecasts using the variance of the residuals and it is therefore referred to as the WLS (weighted least squares) estimator usingvariance scaling. The approach is implemented inmin_trace()by settingmethod = "wls_var".

- Set\(\bm{W}_{h}=k_{h}\bm{\Lambda}\)for all\(h\), where\(k_{h} > 0\),\(\bm{\Lambda}=\text{diag}(\bm{S}\bm{1})\), and\(\bm{1}\)is a unit vector of dimension\(m\)(the number of bottom-level series). This specification assumes that the bottom-level base forecast errors each have variance\(k_{h}\)and are uncorrelated between nodes. Hence each element of the diagonal\(\bm{\Lambda}\)matrix contains the number of forecast error variances contributing to each node. This estimator only depends on the structure of the aggregations, and not on the actual data. It is therefore referred to asstructural scaling. Applying the structural scaling specification is particularly useful in cases where residuals are not available, and so variance scaling cannot be applied; for example, in cases where the base forecasts are generated by judgmental forecasting (Chapter6). The approach is implemented inmin_trace()by settingmethod = "wls_struct".

Set\(\bm{W}_{h}=k_{h}\bm{\Lambda}\)for all\(h\), where\(k_{h} > 0\),\(\bm{\Lambda}=\text{diag}(\bm{S}\bm{1})\), and\(\bm{1}\)is a unit vector of dimension\(m\)(the number of bottom-level series). This specification assumes that the bottom-level base forecast errors each have variance\(k_{h}\)and are uncorrelated between nodes. Hence each element of the diagonal\(\bm{\Lambda}\)matrix contains the number of forecast error variances contributing to each node. This estimator only depends on the structure of the aggregations, and not on the actual data. It is therefore referred to asstructural scaling. Applying the structural scaling specification is particularly useful in cases where residuals are not available, and so variance scaling cannot be applied; for example, in cases where the base forecasts are generated by judgmental forecasting (Chapter6). The approach is implemented inmin_trace()by settingmethod = "wls_struct".

- Set\(\bm{W}_h = k_h \hat{\bm{W}}_1\)for all\(h\), where\(k_h>0\). Here we only assume that the error covariance matrices are proportional to each other, and we directly estimate the full one-step covariance matrix\(\bm{W}_1\). The most obvious and simple way would be to use the sample covariance. This is implemented inmin_trace()by settingmethod = "mint_cov".However, for cases where the number of bottom-level series\(m\)is large compared to the length of the series\(T\), this is not a good estimator. Instead we use a shrinkage estimator which shrinks the sample covariance to a diagonal matrix. This is implemented inmin_trace()by settingmethod = "mint_shrink".

Set\(\bm{W}_h = k_h \hat{\bm{W}}_1\)for all\(h\), where\(k_h>0\). Here we only assume that the error covariance matrices are proportional to each other, and we directly estimate the full one-step covariance matrix\(\bm{W}_1\). The most obvious and simple way would be to use the sample covariance. This is implemented inmin_trace()by settingmethod = "mint_cov".


However, for cases where the number of bottom-level series\(m\)is large compared to the length of the series\(T\), this is not a good estimator. Instead we use a shrinkage estimator which shrinks the sample covariance to a diagonal matrix. This is implemented inmin_trace()by settingmethod = "mint_shrink".


In summary, unlike any other existing approach, the optimal reconciliation forecasts are generated using all the information available within a hierarchical or a grouped structure. This is important, as particular aggregation levels or groupings may reveal features of the data that are of interest to the user and are important to be modelled. These features may be completely hidden or not easily identifiable at other levels.


For example, consider the Australian tourism data introduced in Section11.1, where the hierarchical structure followed the geographic division of a country into states and regions. Some areas will be largely summer destinations, while others may be winter destinations. We saw in Figure11.4the contrasting seasonal patterns between the northern and the southern states. These differences will be smoothed at the country level due to aggregation.


### Bibliography

- Actually, some recent nonlinear reconciliation methods require a slightly more complicated equation. This equation is for general linear reconciliation methods.↩︎

Actually, some recent nonlinear reconciliation methods require a slightly more complicated equation. This equation is for general linear reconciliation methods.↩︎

- This “unbiasedness preserving” constraint was first introduced inHyndman et al. (2011).Panagiotelis et al. (2021)show that this is equivalent to\(\bm{S}\bm{G}\)being a projection matrix onto the\(m\)-dimensional coherent subspace for which the aggregation constraints hold.↩︎

This “unbiasedness preserving” constraint was first introduced inHyndman et al. (2011).Panagiotelis et al. (2021)show that this is equivalent to\(\bm{S}\bm{G}\)being a projection matrix onto the\(m\)-dimensional coherent subspace for which the aggregation constraints hold.↩︎

- Note that\(k_{h}\)is a proportionality constant. It does not need to be estimated or specified here as it gets cancelled out in(11.8).↩︎

Note that\(k_{h}\)is a proportionality constant. It does not need to be estimated or specified here as it gets cancelled out in(11.8).↩︎
