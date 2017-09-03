bt-periodicity
===========

BallTree Periodicity decompose a signal in order to find its principal period.<br>
The interesting part here relies on the fact it does not use harmonics to do so and therefore,<br>
is resilient to time shift.


## Algorithm
The idea is to use BallTree to 'fuzzy index' portions of the signal into clusters.<br>
_NB: those portions are defined by local extremas of the signal._<br>

We can then use Hidden Markov Model to find the most likely sequence of cluster which is the principal period.<br>

## Visually speaking

__The distance metric__<br>
In order to cluster together parts of the signal, we need to define a distance between 2 curve portion.<br>
Here a and b.<br>

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicity/master/img/curve_portion.png)


Then, we align the 2 segments (to the left and to the right) and average the integralsi.<br>

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicity/master/img/alignment.gif)

As a result, a minimized distance would be equivalent to having the same shape on those 2 curve portions.


__Clustering__<br>
Using the distance defined above,<br>
We can now apply BallTree to get a tag for each portion of the curve.<br>

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicity/master/img/signal.png)


This tag sequence is finally parsed by a HMM and the most likely state will be a fix point in the principal period.

Here is the final result:<br>

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicity/master/img/period.png)


## Formally speaking

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicity/master/img/formal_def.gif)

## Implementation notes

__Integral computation__<br>
In practice the integral is approximated. At the moment we just sum 10 points on the segment.<br>
This approximation is valid because segments have maximum one variation by construction.<br>
However if someone know how to shift an interpolation on the time axis, it would be a great contribution.<br>
<br>

__Handling extremas__<br>
In practice the algorithm run 2 times: on minimas and on maximas.<br>
The cluster are then joined by common component since they have same index, it is valid because:<br>

 * We do not capture constant portions.
 * The interpolation is continuous.

We can also note it introduce robustness to amplitude shift.


## Conclusion

The results are quite good, allowing to detect periodicity on really noisy signals.<br>
But not only the principal period also patterns in the signal.<br>
We can note the importance of the tolerance parameter used for fuzzy indexing as well and the interpolation.<br>
<br>
A future update could allow usage of an external interpolation.

