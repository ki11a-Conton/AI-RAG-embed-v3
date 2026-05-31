
# Forecasting: Principles and Practice(3rd ed)


# Chapter 11Forecasting hierarchical and grouped time series


Time series can often be naturally disaggregated by various attributes of interest. For example, the total number of bicycles sold by a cycling manufacturer can be disaggregated by product type such as road bikes, mountain bikes and hybrids. Each of these can be disaggregated into finer categories. For example hybrid bikes can be divided into city, commuting, comfort, and trekking bikes; and so on. These categories are nested within the larger group categories, and so the collection of time series follows a hierarchical aggregation structure. Therefore we refer to these as “hierarchical time series”.


Hierarchical time series often arise due to geographic divisions. For example, the total bicycle sales can be disaggregated by country, then within each country by state, within each state by region, and so on down to the outlet level.


Alternative aggregation structures arise when attributes of interest are crossed rather than nested. For example, the bicycle manufacturer may be interested in attributes such as frame size, gender, price range, etc. Such attributes do not naturally disaggregate in a unique hierarchical manner as the attributes are not nested. We refer to the resulting time series of crossed attributes as “grouped time series”.


More complex structures arise when attributes of interest are both nested and crossed. For example, it would be natural for the bicycle manufacturer to be interested in sales by product type and also by geographic division. Then both the product groupings and the geographic hierarchy are mixed together. We introduce alternative aggregation structures in Section11.1.


Forecasts are often required for all disaggregate and aggregate series, and it is natural to want the forecasts to add up in the same way as the data. For example, forecasts of regional sales should add up to forecasts of state sales, which should in turn add up to give a forecast for national sales.


In this chapter we discuss forecasting large collections of time series that aggregate in some way. The challenge is that we require forecasts that arecoherentacross the entire aggregation structure. That is, we require forecasts to add up in a manner that is consistent with the aggregation structure of the hierarchy or group that defines the collection of time series.
