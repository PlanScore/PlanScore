Unified District Model
===

_May 2022_

In order to score new plans, it is necessary to create a statistical model of the relationship between districts’ latent partisanship and candidates’ incumbency status with election outcomes. This enables us to estimate district-level vote shares for a new map and the corresponding partisan gerrymandering metrics. This page describes the details of our methodology and how we validate the results of this model.

Results for uncontested elections are imputed as described in [*The Impact of Partisan Gerrymandering on Political Parties*](https://onlinelibrary.wiley.com/doi/abs/10.1111/lsq.12276) and [its appendix](https://onlinelibrary.wiley.com/action/downloadSupplement?doi=10.1111%2Flsq.12276&file=lsq12276-sup-0001-Supinfo.pdf), by Nicholas Stephanopoulos and Christopher Warshaw.

Methodology
---

#### The Big Picture

We use the correlation between the presidential vote on the one hand and state legislative or congressional votes on the other to predict how new districts will likely vote and so how biased a plan will be. Our correlations come from the last 10 years of elections and are estimated separately for state legislatures and Congress. They factor in how much each state’s and election year’s results might differ from others and—where appropriate—any extra advantage incumbents might have. We also allow our predictions to be imperfect by quantifying how much our method missed the actual outcomes of past elections, including the degree to which partisan tides have changed party performance from one election to the next. This enables us to generate the most accurate, data-driven, and transparent prediction we can.

#### The Details

We use a Bayesian hierarchical model of district-level election returns, run on either state legislatures or congressional delegations (depending on the outcome of interest), for the elections from 2012 through 2020. Formally, the model is:

<p style="text-align:center"><img src="matrix.png" style="width:399px;height:348px"></p>

where

- <var style="font-family:serif">i</var> indexes district level elections
- <var style="font-family:serif">s</var> indexes states, with <var style="font-family:serif">s(i)</var> denoting the state of district election <var style="font-family:serif">i</var>
- <var style="font-family:serif">c</var> indexes election cycles, with <var style="font-family:serif">c(i)</var> denoting the election cycle of district election <var style="font-family:serif">i</var>
- <var style="font-family:serif">k ∈ [1, 2]</var> indexes covariates, with 0 identifying intercepts
- <var style="font-family:serif">y<sub>i</sub></var> is the Democratic share of the two-party vote in district election <var style="font-family:serif">i</var>
- <var style="font-family:serif"><b>X</b><sub>i</sub></var> is a matrix of covariate values for district election <var style="font-family:serif">i</var>
- <var style="font-family:serif">β</var> is a matrix of population-level intercept and slopes corresponding to covariates <var style="font-family:serif"><b>X</b></var>
- <var style="font-family:serif">β<sub>s(i)</sub></var> and <var style="font-family:serif">β<sub>c(i)</sub></var> are matrices of coefficients for the state and election cycle, respectively, of district election <var style="font-family:serif">i</var>
- <var style="font-family:serif">σ<sub>y</sub></var> is the residual population-level error term

The model allows the slope for all our covariates—as well as the corresponding intercept—to vary across both states and election cycles. Based on exploration of different model specifications, we allow for correlated random effects across cycles but assume no such correlation across states to facilitate convergence.

We run separate models for state legislative and congressional outcomes and with and without incumbency as a covariate. PlanScore identifies a plan as state legislative or congressional based on the number of seats in the plan and the state for which it is submitted.

<var>k</var> ranges between 1 and 2: if a user designates incumbency for any seat in a plan, predictions come from the model that includes both presidential vote and incumbency as covariates; if all seats are left open, predictions come from a model with only presidential vote. Presidential vote is the two-party district-level Democratic presidential vote share, centered around its global mean (Congress = 0.521; State legislatures = 0.494), while incumbency status in district election <var>i</var> is coded -1 for Republican, 0 for open, and 1 for Democratic. We do not have the 2020 presidential vote for estimating new plans in two states—Kentucky and South Dakota—so we used the 2016 presidential vote in the model for those states. In the small number of state-cycle combinations that were missing presidential vote we used the presidential vote for the same district in the next presidential election (or the previous presidential election where the next one was not available).

When generating predictions, PlanScore draws 1000 samples from the posterior distribution of model parameters, and uses them to calculate means and probabilities. We also add in the offsets for the 2020 presidential election cycle, and then also add in samples from the covariance matrix of cycle random effects to allow the uncertainty of predicting for an unknown election cycle to propagate into our predictions. This has the effect of predicting for an election like 2020 in most respects, but with error bounds that encompass the full range of partisan tides that occurred over the last decade.

Full results for our four separate models can be found below.

<table>
    <caption>Table 1: Congress prediction model with incumbency (<var>k</var> = 2)</caption>
    <thead>
        <tr>
            <th></th>
            <th style="text-align:right">Estimate</th>
            <th style="text-align:center">95% Credible Interval</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th colspan="3" style="padding-top:.5em">POPULATION-LEVEL</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">β<sub>0</sub></var>)</td>
            <td align="right">0.52</td>
            <td align="center">[0.47, 0.56]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">β<sub>1</sub></var>)</td>
            <td align="right">0.85</td>
            <td align="center">[0.77, 0.94]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">β<sub>2</sub></var>)</td>
            <td align="right">0.04</td>
            <td align="center">[0.02, 0.06]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">STATE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0s</sub></sub></var>)</td>
            <td align="right">0.01</td>
            <td align="center">[0.01, 0.01]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1s</sub></sub></var>)</td>
            <td align="right">0.10</td>
            <td align="center">[0.07, 0.13]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">σ<sub>β<sub>2s</sub></sub></var>)</td>
            <td align="right">0.01</td>
            <td align="center">[0.01, 0.02]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">CYCLE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0c</sub></sub></var>)</td>
            <td align="right">0.04</td>
            <td align="center">[0.02, 0.09]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">0.08</td>
            <td align="center">[0.03, 0.18]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">σ<sub>β<sub>2c</sub></sub></var>)</td>
            <td align="right">0.02</td>
            <td align="center">[0.01, 0.05]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Correlations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Pres. vote (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">−0.08</td>
            <td align="center">[−0.77, 0.65]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Incumbency (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>2s</sub></sub></var>)</td>
            <td align="right">−0.31</td>
            <td align="center">[−0.88, 0.54]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Pres. vote - Incumbency (<var style="font-family:serif">ρσ<sub>β<sub>1c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>2c</sub></sub></var>)</td>
            <td align="right">−0.45</td>
            <td align="center">[−0.93, 0.40]</td>
        </tr>
        <tr>
            <td colspan="3" style="padding-top:1em;font-weight:normal">
                Note: Model estimated in brms for R. Model based on 4 MCMC chains run for 6000 iterations each with a 2000 iteration warm-up. All model parameters converged well with <var>Rˆ</var> &lt; 1.01.
            </td>
        </tr>
    </tbody>
</table>

<table>
    <caption>Table 2: Congress prediction model without incumbency (<var>k</var> = 1)</caption>
    <thead>
        <tr>
            <th></th>
            <th style="text-align:right">Estimate</th>
            <th style="text-align:center">95% Credible Interval</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th colspan="3" style="padding-top:.5em">POPULATION-LEVEL</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">β<sub>0</sub></var>)</td>
            <td align="right">0.52</td>
            <td align="center">[0.49, 0.55]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">β<sub>1</sub></var>)</td>
            <td align="right">1.04</td>
            <td align="center">[0.97, 1.10]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">STATE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0s</sub></sub></var>)</td>
            <td align="right">0.02</td>
            <td align="center">[0.01, 0.02]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1s</sub></sub></var>)</td>
            <td align="right">0.09</td>
            <td align="center">[0.06, 0.13]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">CYCLE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0c</sub></sub></var>)</td>
            <td align="right">0.03</td>
            <td align="center">[0.02, 0.08]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">0.06</td>
            <td align="center">[0.03, 0.14]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Correlations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Pres. vote (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">−0.68</td>
            <td align="center">[−0.99, 0.29]</td>
        </tr>
        <tr>
            <td colspan="3" style="padding-top:1em;font-weight:normal">
                Note: Model estimated in brms for R. Model based on 4 MCMC chains run for 6000 iterations each with a 2000 iteration warm-up. All model parameters converged well with <var>Rˆ</var> &lt; 1.01.
            </td>
        </tr>
    </tbody>
</table>

<table>
    <caption>Table 3: State legislature prediction model with incumbency (<var>k</var> = 2)</caption>
    <thead>
        <tr>
            <th></th>
            <th style="text-align:right">Estimate</th>
            <th style="text-align:center">95% Credible Interval</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th colspan="3" style="padding-top:.5em">POPULATION-LEVEL</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">β<sub>0</sub></var>)</td>
            <td align="right">0.49</td>
            <td align="center">[0.47, 0.52]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">β<sub>1</sub></var>)</td>
            <td align="right">0.77</td>
            <td align="center">[0.65, 0.88]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">β<sub>2</sub></var>)</td>
            <td align="right">0.05</td>
            <td align="center">[0.03, 0.07]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">STATE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0s</sub></sub></var>)</td>
            <td align="right">0.02</td>
            <td align="center">[0.02, 0.03]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1s</sub></sub></var>)</td>
            <td align="right">0.11</td>
            <td align="center">[0.09, 0.14]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">σ<sub>β<sub>2s</sub></sub></var>)</td>
            <td align="right">0.02</td>
            <td align="center">[0.01, 0.02]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">CYCLE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0c</sub></sub></var>)</td>
            <td align="right">0.03</td>
            <td align="center">[0.01, 0.07]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">0.14</td>
            <td align="center">[0.07, 0.25]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Incumbency (<var style="font-family:serif">σ<sub>β<sub>2c</sub></sub></var>)</td>
            <td align="right">0.02</td>
            <td align="center">[0.01, 0.05]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Correlations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Pres. vote (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">−0.12</td>
            <td align="center">[−0.78, 0.63]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Incumbency (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>2s</sub></sub></var>)</td>
            <td align="right">−0.22</td>
            <td align="center">[−0.83, 0.58]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Pres. vote - Incumbency (<var style="font-family:serif">ρσ<sub>β<sub>1c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>2c</sub></sub></var>)</td>
            <td align="right">−0.56</td>
            <td align="center">[−0.95, 0.30]</td>
        </tr>
        <tr>
            <td colspan="3" style="padding-top:1em;font-weight:normal">
                Note: Model estimated in brms for R. Model based on 4 MCMC chains run for 6000 iterations each with a 2000 iteration warm-up. All model parameters converged well with <var>Rˆ</var> &lt; 1.01.
            </td>
        </tr>
    </tbody>
</table>

<table>
    <caption>Table 4: State legislature prediction model without incumbency (<var>k</var> = 1)</caption>
    <thead>
        <tr>
            <th></th>
            <th style="text-align:right">Estimate</th>
            <th style="text-align:center">95% Credible Interval</th>
        </tr>
    </thead>
    <tbody>
        <tr>
            <th colspan="3" style="padding-top:.5em">POPULATION-LEVEL</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">β<sub>0</sub></var>)</td>
            <td align="right">0.49</td>
            <td align="center">[0.46, 0.52]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">β<sub>1</sub></var>)</td>
            <td align="right">0.91</td>
            <td align="center">[0.80, 1.03]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">STATE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0s</sub></sub></var>)</td>
            <td align="right">0.03</td>
            <td align="center">[0.02, 0.03]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1s</sub></sub></var>)</td>
            <td align="right">0.11</td>
            <td align="center">[0.09, 0.13]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">CYCLE-LEVEL</th>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Standard Deviations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept (<var style="font-family:serif">σ<sub>β<sub>0c</sub></sub></var>)</td>
            <td align="right">0.03</td>
            <td align="center">[0.01, 0.08]</td>
        </tr>
        <tr>
            <td style="font-weight:normal">Presidential vote (<var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">0.12</td>
            <td align="center">[0.06, 0.24]</td>
        </tr>
        <tr>
            <th colspan="3" style="padding-top:.5em">Correlations</th>
        </tr>
        <tr>
            <td style="font-weight:normal">Intercept - Pres. vote (<var style="font-family:serif">ρσ<sub>β<sub>0c</sub></sub></var><var style="font-family:serif">σ<sub>β<sub>1c</sub></sub></var>)</td>
            <td align="right">−0.17</td>
            <td align="center">[−0.85, 0.69]</td>
        </tr>
        <tr>
            <td colspan="3" style="padding-top:1em;font-weight:normal">
                Note: Model estimated in brms for R. Model based on 4 MCMC chains run for 6000 iterations each with a 2000 iteration warm-up. All model parameters converged well with <var>Rˆ</var> &lt; 1.01.
            </td>
        </tr>
    </tbody>
</table>

Predictions
---

The charts below show comparisons between this model’s in-sample predictions and observed historical scores for plans with at least 7 districts. The results were broadly similar for cross-validated predictions with 10 percent of the sample set aside for testing. The predictions were also quite strong for 2020 in states where we were able to obtain election results for comparison.

![model_v_historical_cycles_cycles_cong.png](model_v_historical_cycles_cycles_cong.png)

![model_v_historical_states_cycles_cong.png](model_v_historical_states_cycles_cong.png)

![model_v_historical_cycles_cycles_cong_pvote_only.png](model_v_historical_cycles_cycles_cong_pvote_only.png)

![model_v_historical_states_cycles_cong_pvote_only.png](model_v_historical_states_cycles_cong_pvote_only.png)

![model_v_historical_cycles_cycles_leg.png](model_v_historical_cycles_cycles_leg.png)

![model_v_historical_states_cycles_leg.png](model_v_historical_states_cycles_leg.png)

![model_v_historical_cycles_cycles_leg_pvote_only.png](model_v_historical_cycles_cycles_leg_pvote_only.png)

![model_v_historical_states_cycles_leg_pvote_only.png](model_v_historical_states_cycles_leg_pvote_only.png)

Data Sources
---

Precinct-level presidential vote data used by this model is mostly sourced from the [Voting and Election Science Team](https://dataverse.harvard.edu/dataverse/electionscience) at University of Florida and Wichita State University.
