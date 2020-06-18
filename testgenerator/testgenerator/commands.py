
import click
# import testgenerator.helper.stefan_generator as stefan
# import testgenerator.helper.michael_generator as michael
# import testgenerator.helper.deap_test.deap_generator as deap


@click.group()
def cli():
    pass

# @cli.command()
# def use_stefan_script():
#     test_output = stefan.ReferenceTestGenerator.generate_random_test()
#     print(test_output)

# @cli.command()
# @click.option('-d','--difficulty', 'difficulty', default='medium')
# def use_michael_script(difficulty):
#     generator = michael.TestGenerator(difficulty)
#     generator.genetic_algorithm()
#     print('test')


# @cli.command()
# def use_deap_script():
#     deap.main()
#     print('test')


if __name__ == '__main__':
    cli()
    # use_deap_script()