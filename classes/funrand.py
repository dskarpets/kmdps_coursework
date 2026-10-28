import math
import random


class FunRand:

    @staticmethod
    def exponential(time_mean):
        a = 0.0
        while a == 0.0:
            a = random.random()
        return -time_mean * math.log(a)

    @staticmethod
    def uniform(time_min, time_max):
        a = 0.0
        while a == 0.0:
            a = random.random()
        return time_min + a * (time_max - time_min)

    @staticmethod
    def normal(time_mean, time_deviation):

        val = random.gauss(time_mean, time_deviation)
        while val < 0:
            val = random.gauss(time_mean, time_deviation)
        return val

    @staticmethod
    def erlang(time_mean, k):

        if k <= 0:
            raise ValueError("k must be >= 1")
        phase_mean = time_mean / k
        total = 0.0
        for _ in range(k):
            total += FunRand.exponential(phase_mean)
        return total
