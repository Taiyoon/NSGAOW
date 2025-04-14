
import random
import numpy

from simenv.world import WorldHybridOffline
from solver.encdec import WorldEnDecoder
from deap import creator, base, tools, algorithms


random.seed(64)
rng = numpy.random.default_rng(42)
world = WorldHybridOffline({'stdout'}, 'src/config1.yml')
encoder = WorldEnDecoder(world)


creator.create("Fitness", base.Fitness, weights=(-1.0,))
creator.create("Individual", list, fitness=creator.Fitness)

toolbox = base.Toolbox()


# Structure initializers
toolbox.register("individual", tools.initIterate,
                 creator.Individual, encoder.rand_init)
toolbox.register("population", tools.initRepeat, list, toolbox.individual)


def mut_a(individual):
    size = len(individual)
    for i in range(size):
        if random.random() < 0.1:
            new = tools.initIterate(creator.Individual, encoder.rand_init)
            individual, _ = tools.cxPartialyMatched(individual, new)
    return individual,


toolbox.register("evaluate", encoder.makespan)
toolbox.register("mate", tools.cxOrdered)
toolbox.register("mutate", mut_a)
toolbox.register("select", tools.selRandom)


def main():
    random.seed(64)
    NGEN = 50
    MU = 50
    pop = toolbox.population(n=MU)
    hof = tools.HallOfFame(1)
    stats = tools.Statistics(lambda ind: ind.fitness.values)
    stats.register("avg", numpy.mean, axis=0)
    stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)
    algorithms.eaSimple(pop, toolbox, 0.2, 0.2, NGEN, stats, hof)
    return pop, stats, hof


ans = main()
