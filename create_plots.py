import numpy as np
import os
import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
import argparse
import seaborn as sns
sns.set_style('white')

COLORS = lambda n: list(reversed(sns.color_palette("hls", n)))

get_experiment_name = lambda folder_name: list(filter(lambda x: len(x)>2, folder_name.split('/')))[-2]


def plot_metric_curves(folders, metrics, ax=None, size_of_acquisitions=10):
    """
    Plots the curve for the metric in `metrics` for 
    each experiment found in `folders`
    """
    if not ax:
        plt.clf()
        ax = plt.gca()

    for color, folder in zip(COLORS(len(folders)), folders):
        for line_style, metric in zip(['-', '--', ':', '-.'], metrics):
            curve = np.load(os.path.join(folder, metric +'.npy'))
            ax.plot(curve, label=get_experiment_name(folder)+'-'+metric, linestyle=line_style, color=color)
    ax.legend(loc=(1,0)) # put the legend outside
    xticks = ax.get_xticks()
    ax.set_xticklabels(np.array(xticks)*size_of_acquisitions)
    ax.set_xlabel('Training set size')
    sns.despine()
    return ax


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    named_args = parser.add_argument_group('named arguments')

    named_args.add_argument('-f', '--folders',
        help="""folders with the experiments""",
        nargs='+', required=True, type=str)

    named_args.add_argument('-m', '--metrics',
        help="""metrics to plot""",
        nargs='+', required=True, type=str)

    named_args.add_argument('-name', '--name',
        help="""name of the figure""",
        required=True, type=str)

    f = plt.figure()
    ax = f.gca()

    args = parser.parse_args()
    ax = plot_metric_curves(args.folders, args.metrics, ax=ax)
    ax.set_title(args.name)
    f.savefig(args.name+'.pdf', bbox_inches='tight')
