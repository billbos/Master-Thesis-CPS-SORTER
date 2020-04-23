
import array
import random
import json
import numpy
import random
from tempfile import NamedTemporaryFile
from os.path import basename
from deap import base
from deap import creator
from deap import tools
from deap.benchmarks.tools import diversity, convergence, hypervolume
from copy import deepcopy
from testgenerator.helper.stefan_generator import ReferenceTestGenerator
from asfault.tests import RoadTest
from asfault.network import SEG_FACTORIES
from asfault import mutations

import logging as l



# toolbox.register("population", generator._create_start_population)
# toolbox.register("mutate", generator._mutation, creator.Individual)
# toolbox.register("select", generator._choose_elite, toolbox.population)
# toolbox.register("crossover", generator._crossover, creator.Individual, creator.Individual)
# toolbox.register("spline_population", generator._spline_population, toolbox.population)



rng=random.Random()

def main():
    # generator = TestGenerator('medium')
    ReferenceTestGenerator._configure_asfault()
    mutators = init_mutators()
    creator.create("FitnessMulti", base.Fitness, weights=(1.0, -1.0))
    creator.create("Individual", array.array, typecode="d", fitness=creator.FitnessMulti)

    toolbox = base.Toolbox()
    toolbox.register("generate_road", ReferenceTestGenerator._generate_asfault_test)
    toolbox.register("individual", tools.initRepeat, creator.Individual, RoadTest.to_dict(ReferenceTestGenerator._generate_asfault_test), 1)
    toolbox.register("population", tools.initRepeat, list, toolbox.individual)
    toolbox.register("mutate", mutate, toolbox.individual, mutators)
    toolbox.register("select", tools.selNSGA2)
    toolbox.register("evaluate", evaluate)



    stats = tools.Statistics(lambda ind: ind.fitness.values)
    # stats.register("avg", numpy.mean, axis=0)
    # stats.register("std", numpy.std, axis=0)
    stats.register("min", numpy.min, axis=0)
    stats.register("max", numpy.max, axis=0)

    logbook = tools.Logbook()
    logbook.header = "gen", "evals", "std", "min", "avg", "max"

    pop = toolbox.population(10)

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
            # if random.random() <= CXPB:
            #     toolbox.mate(ind1, ind2)
            
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

    print("Final population hypervolume is %f" % hypervolume(pop, [11.0, 11.0]))

def init_mutators():
    mutators = {}
    for key, factory in SEG_FACTORIES.items():
        name = 'repl_' + key
        mutators[name] = mutations.SegmentReplacingMutator(rng, name, key, factory)
    return mutators

def mutate(resident, mutators):
        mutators = [*mutators.values()]
        rng.shuffle(mutators)
        while mutators:
            mutator = mutators.pop()
            mutated, aux = attempt_mutation(resident, mutator)
            if not aux:
                aux = {}

            aux['type'] = mutator
            if mutated:
                test = test_from_network(mutated)
                l.info('Successfully applied mutation: %s', str(type(mutator)))
                return test, aux

        return None, {}

def attempt_mutation(resident, mutator):
        epsilon = 0.25
        while True:
            try:
                mutated, aux = mutator.apply(resident)
                if mutated and mutated.complete_is_consistent():
                    test = test_from_network(mutated)
                    return mutated, aux
            except Exception as e:
                l.error('Exception while creating test from child: ')
                l.exception(e)
            failed = self.rng.random()
            if failed < epsilon:
                break

            epsilon *= 1.1

        return None, {}

def test_from_network(network):
    start, goal, path = self.determine_start_goal_path(network)
    l.debug('Got start, goal, and path for network.')
    test = RoadTest(-1, network, start, goal)
    if path:
        l.debug('Setting path of new test: %s', test.test_id)
        test.set_path(path)
        l.debug('Set path of offspring.')
    return test

def select(population):
    pass

def evaluate(candidate):
    score = 0
    for seg in candidate.network.nodes:
        score += seg.angle
    return score, len(candidate.network.nodes)

if __name__ == '__main__':
    main()