import numpy as np

def summary_statistics(data):
    """
    Calculate the 25th percentile (Q1), median, 75th percentile (Q3), and interquartile range (IQR) of the data.
    
    Parameters:
    data (array-like): The input array of numerical data.
    
    Returns:
    tuple: (25th percentile, median, 75th percentile, interquartile range)
    """
    q25 = np.percentile(data, 25)  # 25th percentile (Q1)
    median = np.median(data)       # Median (Q2)
    q75 = np.percentile(data, 75)  # 75th percentile (Q3)
    iqr = q75 - q25                # Interquartile range (IQR)
    
    return q25, median, q75, iqr
def cohen_d(group1, group2):
    mean1, mean2 = np.mean(group1), np.mean(group2)
    sd1, sd2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    pooled_sd = np.sqrt(((n1 - 1) * sd1 ** 2 + (n2 - 1) * sd2 ** 2) / (n1 + n2 - 2))
    d = (mean1 - mean2) / pooled_sd
    return d

def cliffs_delta(group1, group2):
    """
    Calculate Cliff's Delta, which is a measure of how often values in one group
    are larger than values in another group, minus the reverse, and adjusted for ties.

    Parameters:
    group1 (array-like): Numeric values for the first group.
    group2 (array-like): Numeric values for the second group.

    Returns:
    delta (float): The Cliff's Delta statistic.
    """
    group1, group2 = np.array(group1), np.array(group2)
    n1, n2 = len(group1), len(group2)
    mat = np.array(np.meshgrid(group1, group2)).T.reshape(-1, 2)
    greater = np.sum(mat[:, 0] > mat[:, 1])
    less = np.sum(mat[:, 0] < mat[:, 1])
    delta = (greater - less) / (n1 * n2)
    return delta

def vargha_delaney_a(group1, group2):
    """
    Calculate Vargha-Delaney A Effect Size, which is the probability that a randomly picked
    observation from one group exceeds an observation from the second group.

    Parameters:
    group1 (array-like): Numeric values for the first group.
    group2 (array-like): Numeric values for the second group.

    Returns:
    a (float): The Vargha-Delaney A statistic.
    """
    group1, group2 = np.array(group1), np.array(group2)
    n1, n2 = len(group1), len(group2)
    mat = np.array(np.meshgrid(group1, group2)).T.reshape(-1, 2)
    greater = np.sum(mat[:, 0] > mat[:, 1])
    a = greater / (n1 * n2)
    return a
