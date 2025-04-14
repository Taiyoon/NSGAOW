from platypus import DTLZ2, NSGAII, SaveResultsExtension

problem = DTLZ2()

algorithm = NSGAII(problem)
algorithm.add_extension(SaveResultsExtension("results/{algorithm}_{problem}/{nfe}.json", frequency=100))
algorithm.run(10000)