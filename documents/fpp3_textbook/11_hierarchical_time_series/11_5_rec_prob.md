
# Forecasting: Principles and Practice(3rd ed)


## 11.5Reconciled distributional forecasts


So far we have only discussed the reconciliation of point forecasts. However, we are usually also interested in the forecast distributions so that we can compute prediction intervals.


Panagiotelis et al. (2023)present several important results for generating reconciled probabilistic forecasts. We focus here on two fundamental results that are implemented in thereconcile()function.

- If the base forecasts are normally distributed, i.e.,\[
  \hat{\bm{y}}_h\sim N(\hat{\bm\mu}_h,\hat{\bm\Sigma}_h),
\]then the reconciled forecasts are also normally distributed,\[
  \tilde{\bm{y}}_h \sim N(\bm{S}\bm{G}\hat{\bm{\mu}}_h,\bm{S}\bm{G}\hat{\bm{\Sigma}}_{h}\bm{G}'\bm{S}').
\]

If the base forecasts are normally distributed, i.e.,\[
  \hat{\bm{y}}_h\sim N(\hat{\bm\mu}_h,\hat{\bm\Sigma}_h),
\]then the reconciled forecasts are also normally distributed,\[
  \tilde{\bm{y}}_h \sim N(\bm{S}\bm{G}\hat{\bm{\mu}}_h,\bm{S}\bm{G}\hat{\bm{\Sigma}}_{h}\bm{G}'\bm{S}').
\]

- If it is unreasonable to assume normality for the base forecasts, we can use bootstrapping. Bootstrapped prediction intervals were introduced in Section5.5. The same idea can be used here. We can simulate future sample paths from the model(s) that produce the base forecasts, and then reconcile these sample paths. Coherent prediction intervals can be computed from the reconciled sample paths.Suppose that\((\hat{\bm{y}}_h^{[1]},\dots,\hat{\bm{y}}_h^{[B]})\)are a set of\(B\)simulated sample paths, generated independently from the models used to produce the base forecasts. Then\((\bm{S}\bm{G}\hat{\bm{y}}_h^{[1]},\dots,\bm{S}\bm{G}\hat{\bm{y}}_h^{[B]})\)provides a set of reconciled sample paths, from which percentiles can be calculated in order to construct coherent prediction intervals.To generate bootstrapped prediction intervals in this way, we simply setbootstrap = TRUEin theforecast()function.

If it is unreasonable to assume normality for the base forecasts, we can use bootstrapping. Bootstrapped prediction intervals were introduced in Section5.5. The same idea can be used here. We can simulate future sample paths from the model(s) that produce the base forecasts, and then reconcile these sample paths. Coherent prediction intervals can be computed from the reconciled sample paths.


Suppose that\((\hat{\bm{y}}_h^{[1]},\dots,\hat{\bm{y}}_h^{[B]})\)are a set of\(B\)simulated sample paths, generated independently from the models used to produce the base forecasts. Then\((\bm{S}\bm{G}\hat{\bm{y}}_h^{[1]},\dots,\bm{S}\bm{G}\hat{\bm{y}}_h^{[B]})\)provides a set of reconciled sample paths, from which percentiles can be calculated in order to construct coherent prediction intervals.


To generate bootstrapped prediction intervals in this way, we simply setbootstrap = TRUEin theforecast()function.


### Bibliography
