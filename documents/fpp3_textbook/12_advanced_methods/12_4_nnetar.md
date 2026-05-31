
# Forecasting: Principles and Practice(3rd ed)


## 12.4Neural network models


Artificial neural networks are forecasting methods that are based on simple mathematical models of the brain. They allow complex nonlinear relationships between the response variable and its predictors.


### Neural network architecture


A neural network can be thought of as a network of “neurons” which are organised in layers. The predictors (or inputs) form the bottom layer, and the forecasts (or outputs) form the top layer. There may also be intermediate layers containing “hidden neurons”.


Figure 12.15:  A simple neural network equivalent to a linear regression.


The simplest networks contain no hidden layers and are equivalent to linear regressions. Figure12.15shows the neural network version of a linear regression with four predictors. The coefficients attached to these predictors are called “weights”. The forecasts are obtained by a linear combination of the inputs. The weights are selected in the neural network framework using a “learning algorithm” that minimises a “cost function” such as the MSE. Of course, in this simple example, we can use linear regression which is a much more efficient method of training the model.


Once we add an intermediate layer with hidden neurons, the neural network becomes non-linear. A simple example is shown in Figure12.16.


Figure 12.16: A neural network with four inputs and one hidden layer with three hidden neurons.


This is known as amultilayer feed-forward network, where each layer of nodes receives inputs from the previous layers. The outputs of the nodes in one layer are inputs to the next layer. The inputs to each node are combined using a weighted linear combination. The result is then modified by a nonlinear function before being output. For example, the inputs into each hidden neuron in Figure12.16are combined linearly to give\[
  z_j = b_j + \sum_{i=1}^4 w_{i,j} x_i.
\]In the hidden layer, this is then modified using a nonlinear function such as a sigmoid,\[
  s(z) = \frac{1}{1+e^{-z}},
\]to give the input for the next layer. This tends to reduce the effect of extreme input values, thus making the network somewhat robust to outliers.


The parameters\(b_1,b_2,b_3\)and\(w_{1,1},\dots,w_{4,3}\)are “learned” (or estimated) from the data. The values of the weights are often restricted to prevent them from becoming too large. The parameter that restricts the weights is known as the “decay parameter”, and is often set to be equal to 0.1.


The weights take random values to begin with, and these are then updated using the observed data. Consequently, there is an element of randomness in the predictions produced by a neural network. Therefore, the network is usually trained several times using different random starting points, and the results are averaged.


The number of hidden layers, and the number of nodes in each hidden layer, must be specified in advance. Usually, these would be selected using cross-validation.


### Neural network autoregression


With time series data, lagged values of the time series can be used as inputs to a neural network, just as we used lagged values in a linear autoregression model (Chapter9). We call this a neural network autoregression or NNAR model.


In this book, we only consider feed-forward networks with one hidden layer, and we use the notation NNAR(\(p,k\)) to indicate there are\(p\)lagged inputs and\(k\)nodes in the hidden layer. For example, a NNAR(9,5) model is a neural network with the last nine observations\((y_{t-1},y_{t-2},\dots,y_{t-9}\)) used as inputs for forecasting the output\(y_t\), and with five neurons in the hidden layer. A NNAR(\(p,0\)) model is equivalent to an ARIMA(\(p,0,0\)) model, but without the restrictions on the parameters to ensure stationarity.


With seasonal data, it is useful to also add the last observed values from the same season as inputs. For example, an NNAR(3,1,2)\(_{12}\)model has inputs\(y_{t-1}\),\(y_{t-2}\),\(y_{t-3}\)and\(y_{t-12}\), and two neurons in the hidden layer. More generally, an NNAR(\(p,P,k\))\(_m\)model has inputs\((y_{t-1},y_{t-2},\dots,y_{t-p},y_{t-m},y_{t-2m},\dots,y_{t-Pm})\)and\(k\)neurons in the hidden layer. A NNAR(\(p,P,0\))\(_m\)model is equivalent to an ARIMA(\(p,0,0\))(\(P\),0,0)\(_m\)model but without the restrictions on the parameters that ensure stationarity.


TheNNETAR()function fits an NNAR(\(p,P,k\))\(_m\)model. If the values of\(p\)and\(P\)are not specified, they are selected automatically. For non-seasonal time series, the default is the optimal number of lags (according to the AIC) for a linear AR(\(p\)) model. For seasonal time series, the default values are\(P=1\)and\(p\)is chosen from the optimal linear model fitted to the seasonally adjusted data. If\(k\)is not specified, it is set to\(k=(p+P+1)/2\)(rounded to the nearest integer).


When it comes to forecasting, the network is applied iteratively. For forecasting one step ahead, we simply use the available historical inputs. For forecasting two steps ahead, we use the one-step forecast as an input, along with the historical data. This process proceeds until we have computed all the required forecasts.


### Example: Sunspots


The surface of the sun contains magnetic regions that appear as dark spots. These affect the propagation of radio waves, and so telecommunication companies like to predict sunspot activity in order to plan for any future difficulties. Sunspots follow a cycle of length between 9 and 14 years. In Figure12.17, forecasts from an NNAR(9,5) are shown for the next 30 years. We have used a square root transformation to ensure the forecasts stay positive.


```
sunspots <- sunspot.year |> as_tsibble()
fit <- sunspots |>
  model(NNETAR(sqrt(value)))
fit |>
  forecast(h = 30) |>
  autoplot(sunspots) +
  labs(x = "Year", y = "Counts", title = "Yearly sunspots")
```


Figure 12.17: Forecasts from a neural network with nine lagged inputs and one hidden layer containing five neurons.


Here, the last 9 observations are used as predictors, and there are 5 neurons in the hidden layer. The cyclicity in the data has been modelled well. We can also see the asymmetry of the cycles has been captured by the model, where the increasing part of the cycle is steeper than the decreasing part of the cycle. This is one difference between a NNAR model and a linear AR model — while linear AR models can model cyclicity, the modelled cycles are always symmetric.


### Prediction intervals


Unlike most of the methods considered in this book, neural networks are not based on a well-defined stochastic model, and so it is not straightforward to derive prediction intervals for the resultant forecasts. However, we can still compute prediction intervals using simulation where future sample paths are generated using bootstrapped residuals (as described in Section5.5).


The neural network fitted to the sunspot data can be written as\[
  y_t = f(\bm{y}_{t-1}) + \varepsilon_t
\]where\(\bm{y}_{t-1} = (y_{t-1},y_{t-2},\dots,y_{t-9})'\)is a vector containing lagged values of the series, and\(f\)is a neural network with 5 hidden nodes in a single layer. The error series\(\{\varepsilon_t\}\)is assumed to be homoscedastic (and possibly also normally distributed).


We can simulate future sample paths of this model iteratively, by randomly generating a value for\(\varepsilon_t\), either from a normal distribution, or by resampling from the historical values. So if\(\varepsilon^*_{T+1}\)is a random draw from the distribution of errors at time\(T+1\), then\[
  y^*_{T+1} = f(\bm{y}_{T}) + \varepsilon^*_{T+1}
\]is one possible draw from the forecast distribution for\(y_{T+1}\). Setting\(\bm{y}_{T+1}^* = (y^*_{T+1}, y_{T}, \dots, y_{T-7})'\), we can then repeat the process to get\[
  y^*_{T+2} = f(\bm{y}^*_{T+1}) + \varepsilon^*_{T+2}.
\]In this way, we can iteratively simulate a future sample path. By repeatedly simulating sample paths, we build up knowledge of the distribution for all future values based on the fitted neural network.


Here is a simulation of 9 possible future sample paths for the sunspot data. Each sample path covers the next 30 years after the observed data.


```
fit |>
  generate(times = 9, h = 30) |>
  autoplot(.sim) +
  autolayer(sunspots, value) +
  theme(legend.position = "none")
```


Figure 12.18: Future sample paths for the annual sunspot data.


If we do this many times, we can get a good picture of the forecast distributions. This is how theforecast()function produces prediction intervals for NNAR models. Thetimesargument inforecast()controls how many simulations are done (default 1000). By default, the errors are drawn from a normal distribution. Thebootstrapargument allows the errors to be “bootstrapped” (i.e., randomly drawn from the historical errors).
