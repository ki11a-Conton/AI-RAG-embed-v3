
# Forecasting: Principles and Practice(3rd ed)


## 4.4Other features


Many more features are possible, and thefeastspackage computes only a few dozen features that have proven useful in time series analysis. It is also easy to add your own features by writing an R function that takes a univariate time series input and returns a numerical vector containing the feature values.


The remaining features in thefeastspackage, not previously discussed, are listed here for reference. The details of some of them are discussed later in the book.

- coef_hurstwill calculate the Hurst coefficient of a time series which is a measure of “long memory”. A series with long memory will have significant autocorrelations for many lags.
- feat_spectralwill compute the (Shannon) spectral entropy of a time series, which is a measure of how easy the series is to forecast. A series which has strong trend and seasonality (and so is easy to forecast) will have entropy close to 0. A series that is very noisy (and so is difficult to forecast) will have entropy close to 1.
- box_piercegives the Box-Pierce statistic for testing if a time series is white noise, and the corresponding p-value. This test is discussed in Section5.4.
- ljung_boxgives the Ljung-Box statistic for testing if a time series is white noise, and the corresponding p-value. This test is discussed in Section5.4.
- The\(k\)th partial autocorrelation measures the relationship between observations\(k\)periods apart after removing the effects of observations between them. So the first partial autocorrelation (\(k=1\)) is identical to the first autocorrelation, because there is nothing between consecutive observations to remove. Partial autocorrelations are discussed in Section9.5. Thefeat_pacffunction contains several features involving partial autocorrelations including the sum of squares of the first five partial autocorrelations for the original series, the first-differenced series and the second-differenced series. For seasonal data, it also includes the partial autocorrelation at the first seasonal lag.
- unitroot_kpssgives the Kwiatkowski-Phillips-Schmidt-Shin (KPSS) statistic for testing if a series is stationary, and the corresponding p-value. This test is discussed in Section9.1.
- unitroot_ppgives the Phillips-Perron statistic for testing if a series is non-stationary, and the corresponding p-value.
- unitroot_ndiffsgives the number of differences required to lead to a stationary series based on the KPSS test. This is discussed in Section9.1
- unitroot_nsdiffsgives the number of seasonal differences required to make a series stationary. This is discussed in Section9.1.
- var_tiled_meangives the variances of the “tiled means” (i.e., the means of consecutive non-overlapping blocks of observations). The default tile length is either 10 (for non-seasonal data) or the length of the seasonal period. This is sometimes called the “stability” feature.
- var_tiled_vargives the variances of the “tiled variances” (i.e., the variances of consecutive non-overlapping blocks of observations). This is sometimes called the “lumpiness” feature.
- shift_level_maxfinds the largest mean shift between two consecutive sliding windows of the time series. This is useful for finding sudden jumps or drops in a time series.
- shift_level_indexgives the index at which the largest mean shift occurs.
- shift_var_maxfinds the largest variance shift between two consecutive sliding windows of the time series. This is useful for finding sudden changes in the volatility of a time series.
- shift_var_indexgives the index at which the largest variance shift occurs.
- shift_kl_maxfinds the largest distributional shift (based on the Kulback-Leibler divergence) between two consecutive sliding windows of the time series. This is useful for finding sudden changes in the distribution of a time series.
- shift_kl_indexgives the index at which the largest KL shift occurs.
- n_crossing_pointscomputes the number of times a time series crosses the median.
- longest_flat_spotcomputes the number of sections of the data where the series is relatively unchanging.
- stat_arch_lmreturns the statistic based on the Lagrange Multiplier (LM) test of Engle (1982) for autoregressive conditional heteroscedasticity (ARCH).
- guerrerocomputes the optimal\(\lambda\)value for a Box-Cox transformation using the Guerrero method (discussed in Section3.1).