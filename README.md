bt-periodicity
===========

BallTree Periodicity decompose a signal in order to find its principal period.<br>
Its particularity relies on the fact it does not use the harmonics to do and therefore,<br>
is resilient to time shift.


## Algorithm
The idea is to use BallTree to 'fuzzy index' portions of the signal into clusters.<br>
_NB: those portions are defined by local extremas of the signal._<br>

We can then use Hidden Markov Model to find the most likely sequence of cluster which is the principal period.<br>

## Visually speaking

__The distance metric__<br>
In order to cluster together parts of the signal, we need to define a distance between 2 curve portion.

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicty/master/img/curve_portion.png)

Then, we align the 2 segments and average the integrals of the curve portion aligned to the left and to the right.

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicty/master/img/alignment.png)

Applying BallTree then gives us a tag for each portion of the curve.

![](https://raw.githubusercontent.com/pelodelfuego/bt-periodicty/master/img/signal.png)

## Formally speaking

![]()

## Implementation notes


## Conclusion

