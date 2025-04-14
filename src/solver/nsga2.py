#    This file is part of DEAP.
#
#    DEAP is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Lesser General Public License as
#    published by the Free Software Foundation, either version 3 of
#    the License, or (at your option) any later version.
#
#    DEAP is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Lesser General Public License for more details.
#
#    You should have received a copy of the GNU Lesser General Public
#    License along with DEAP. If not, see <http://www.gnu.org/licenses/>.

from deap import base, creator, tools, algorithms
from dask.distributed import Client
import array
import random
import json

import numpy

from math import sqrt

from deap import algorithms
from deap import base
from deap import benchmarks
from deap.benchmarks.tools import diversity, convergence, hypervolume
from deap import creator
from deap import tools

from simenv.world import WorldHybridOffline
from solver.encdec import RawNSGA2Encoder, WorldEnDecoder

# min makespan, max security, min cost
# creator.create("FitnessMin", base.Fitness, weights=(-1.0, 1.0, -1.0))
creator.create("FitnessMin", base.Fitness, weights=(-1.0, -1.0, -1.0))
creator.create("Individual", array.array, typecode='d',
               fitness=creator.FitnessMin)

toolbox = base.Toolbox()

# Problem definition
BOUND_LOW, BOUND_UP = 0.0, 1.0


random.seed(64)


def uniform(low, up, size=None):
    try:
        return [random.uniform(a, b) for a, b in zip(low, up)]
    except TypeError:
        return [random.uniform(a, b) for a, b in zip([low] * size, [up] * size)]


toolbox.register("mate", tools.cxSimulatedBinaryBounded,
                 low=BOUND_LOW, up=BOUND_UP, eta=20.0)
toolbox.register("select", tools.selNSGA2)


def main(NGEN=10, MU=100,  seed=42, CXPB=0.9, hv_ref=[24.0, -98.0,  12.0], conf_path='src/config1.yml'):
    random.seed(seed)

    world = WorldHybridOffline({'stdout'}, conf_path)
    encoder = RawNSGA2Encoder(world)
    NDIM = len(encoder.encode_sequence())
    toolbox.register("attr_float", uniform, BOUND_LOW, BOUND_UP, NDIM)
    # toolbox.register("evaluate", encoder.two_obj)
    toolbox.register("evaluate", encoder.three_obj)
    toolbox.register("individual", tools.initIterate,
                     creator.Individual, toolbox.attr_float)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mutate", tools.mutPolynomialBounded,
                     low=BOUND_LOW, up=BOUND_UP, eta=20.0, indpb=1.0/NDIM)

    stats = tools.Statistics()
    stats.register("HV", hypervolume, ref=hv_ref)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "HV", "best"

    pop = toolbox.population(n=MU)

    # Evaluate the individuals with an invalid fitness
    invalid_ind = [ind for ind in pop if not ind.fitness.valid]
    fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
    for ind, fit in zip(invalid_ind, fitnesses):
        ind.fitness.values = fit

    # This is just to assign the crowding distance to the individuals
    # no actual selection is done
    pop = toolbox.select(pop, len(pop))

    record = stats.compile(pop)
    logbook.record(gen=0, evals=len(invalid_ind), **record)
    print(logbook.stream)
    # Begin the generational process
    for gen in range(1, NGEN):
        # Vary the population
        offspring = tools.selTournamentDCD(pop, len(pop))
        offspring = [toolbox.clone(ind) for ind in offspring]

        for ind1, ind2 in zip(offspring[::2], offspring[1::2]):
            if random.random() <= CXPB:
                toolbox.mate(ind1, ind2)

            toolbox.mutate(ind1)
            toolbox.mutate(ind2)
            del ind1.fitness.values, ind2.fitness.values

        # Evaluate the individuals with an invalid fitness
        invalid_ind = [ind for ind in offspring if not ind.fitness.valid]
        fitnesses = toolbox.map(toolbox.evaluate, invalid_ind)
        for ind, fit in zip(invalid_ind, fitnesses):
            ind.fitness.values = fit

        # Select the next generation population
        pop = toolbox.select(pop + offspring, MU)
        record = stats.compile(pop)
        logbook.record(gen=gen, evals=len(invalid_ind), **record)
        print(logbook.stream)

    print("Final population hypervolume is %f" %
          hypervolume(pop, hv_ref))
    wobj = numpy.array([ind.fitness.wvalues for ind in pop]) * -1
    ref = numpy.max(wobj, axis=0)
    print(f'recommend ref set: {list(int(n) for n in ref)}')

    return pop, logbook, encoder


# client = Client()
if __name__ == "__main__":
    # toolbox.register("map", client.map)
    # hv_ref=
    main(hv_ref=[639, 2155, 1], NGEN=100, conf_path='config/base.yml')
