
# Forecasting: Principles and Practice(3rd ed)


## 9.2Backshift notation


The backward shift operator\(B\)is a useful notational device when working with time series lags:\[
  B y_{t} = y_{t - 1} \: .
\](Some references use\(L\)for “lag” instead of\(B\)for “backshift”.) In other words,\(B\), operating on\(y_{t}\), has the effect of shifting the data back one period. Two applications of\(B\)to\(y_{t}\)shifts the data back two periods:\[
  B(By_{t}) = B^{2}y_{t} = y_{t-2}\: .
\]For monthly data, if we wish to consider “the same month last year,” the notation is\(B^{12}y_{t}\)=\(y_{t-12}\).


The backward shift operator is convenient for describing the process ofdifferencing. A first difference can be written as\[
  y'_{t} = y_{t} - y_{t-1} = y_t - By_{t} = (1 - B)y_{t}\: .
\]So a first difference can be represented by\((1 - B)\). Similarly, if second-order differences have to be computed, then:\[
  y''_{t} = y_{t} - 2y_{t - 1} + y_{t - 2} = (1-2B+B^2)y_t = (1 - B)^{2} y_{t}\: .
\]In general, a\(d\)th-order difference can be written as\[
  (1 - B)^{d} y_{t}.
\]


Backshift notation is particularly useful when combining differences, as the operator can be treated using ordinary algebraic rules. In particular, terms involving\(B\)can be multiplied together.


For example, a seasonal difference followed by a first difference can be written as\[\begin{align*}
(1-B)(1-B^m)y_t &= (1 - B - B^m + B^{m+1})y_t \\
&= y_t-y_{t-1}-y_{t-m}+y_{t-m-1},
\end{align*}\]the same result we obtained earlier.
