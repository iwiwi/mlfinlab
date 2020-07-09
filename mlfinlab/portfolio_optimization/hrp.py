# pylint: disable=missing-module-docstring
import numpy as np
from scipy.cluster.hierarchy import linkage as scipy_linkage, dendrogram, to_tree
from scipy.spatial.distance import squareform


class HierarchicalRiskParity:
    """
    This class implements the Hierarchical Risk Parity algorithm mentioned in the following paper: `López de Prado, Marcos,
    Building Diversified Portfolios that Outperform Out-of-Sample (May 23, 2016). Journal of Portfolio Management,
    2016 <https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2708678>`_; The code is reproduced with modification from his book:
    Advances in Financial Machine Learning, Chp-16
    By removing exact analytical approach to the calculation of weights and instead relying on an approximate
    machine learning based approach (hierarchical tree-clustering), Hierarchical Risk Parity produces weights which are stable to
    random shocks in the stock-market. Moreover, previous algorithms like CLA involve the inversion of covariance matrix which is
    a highly unstable operation and tends to have major impacts on the performance due to slight changes in the covariance matrix.
    By removing dependence on the inversion of covariance matrix completely, the Hierarchical Risk Parity algorithm is fast,
    robust and flexible.
    """

    def __init__(self):
        self.weights = list()
        self.ordered_indices = None
        self.clusters = None
        
        # Taking these out so that those purveying the code don't need to dig around to find these
#         self.returns_estimator = ReturnsEstimators()
#         self.risk_metrics = RiskMetrics()
#         self.risk_estimator = RiskEstimators()

    def allocate(self,
                 asset_names,
                 asset_prices=None,
                 asset_returns=None,
                 covariance_matrix=None,
                 distance_matrix=None,
                 side_weights=None,
                 linkage='single'):
        # pylint: disable=invalid-name, too-many-branches
        """
        Calculate asset allocations using HRP algorithm.

        :param asset_names: (list) A list of strings containing the asset names
        :param asset_prices: (numpy matrix) A matrix with historical asset prices (daily close)
        :param asset_returns: (numpy matrix) User supplied array of asset returns
        :param covariance_matrix: (numpy matrix) User supplied covariance matrix of asset returns
        :param distance_matrix: (numpy matrix) User supplied distance matrix
        :param side_weights: (numpy matrix) With asset_names in index and value 1 for Buy, -1 for Sell
                                                      (default 1 for all)
        :param linkage: (string) Type of linkage used for Hierarchical Clustering. Supported strings - ``single``,
                                 ``average``, ``complete``, ``ward``.
        """

        # Perform error checks
        self._error_checks(asset_prices, asset_returns, covariance_matrix)
        
        # Because we aren't using dfs, asset_names become necessary
#         if asset_names is None:
#             if asset_prices is not None:
#                 asset_names = asset_prices.columns
#             elif asset_returns is not None and isinstance(asset_returns, pd.DataFrame):
#                 asset_names = asset_returns.columns
#             else:
#                 raise ValueError("Please provide a list of asset names")

        # Calculate the returns if the user does not supply a returns dataframe
        if asset_returns is None and covariance_matrix is None:
            asset_returns = np.diff(asset_prices) / asset_prices[:, :-1]

        # Calculate covariance of returns or use the user specified covariance matrix
        if covariance_matrix is None:
            covariance_matrix = np.cov(asset_returns, bias=False)

        # Calculate correlation and distance from asset_returns
        correlation_matrix = np.corrcoef(asset_returns)
        if distance_matrix is None:
            distance_matrix = np.sqrt((1 - correlation_matrix).round(5) / 2)

        # Step-1: Tree Clustering
        self.clusters = scipy_linkage(squareform(distance.values), method=method)

        # Step-2: Quasi Diagnalization
        # Using a prebuilt scipy function is faster and makes the overall code less complicated
        ordered_indices = to_tree(clusters, rd=False).pre_order()
        ordered_tickers = asset_names[ordered_indices]
       
        # Step-3: Recursive Bisection
        self._recursive_bisection(covariance=covariance_matrix, indices=ordered_indices, assets=asset_names)

        # Build Long/Short portfolio
        if side_weights is None:
            side_weights = np.ones(indices, dtype=np.float64)
        self._build_long_short_portfolio(side_weights)

    def plot_clusters(self, assets):
        """
        Plot a dendrogram of the hierarchical clusters.

        :param assets: (list) Asset names in the portfolio
        :return: (dict) Dendrogram
        """

        dendrogram_plot = dendrogram(self.clusters, labels=assets)
        return dendrogram_plot

    def _build_long_short_portfolio(self, side_weights):
        """
        Adjust weights according the shorting constraints specified.

        :param side_weights: (pd.Series/numpy matrix) With asset_names in index and value 1 for Buy, -1 for Sell
                                                      (default 1 for all)
        """

    def build_long_short_portfolio(weights, side_weights):
        """
        Adjust weights according the shorting constraints specified.
        :param side_weights: (pd.Series/numpy matrix) With asset_names in index and value 1 for Buy, -1 for Sell
                                                      (default 1 for all)
        """

        short_ptf = np.where(side_weights == -1)
        buy_ptf = np.where(side_weights == 1)
        if len(short_ptf) > 0:

            # Short half size
            weights[short_ptf] /= np.sum(weights[short_ptf])
            weights[short_ptf] *= -0.5

            # Buy other half
            weights[buy_ptf] /= np.sum(weights[buy_ptf])
            weights[buy_ptf] *= 0.5

        return weights
    def _get_cluster_variance(self, covariance_matrix, cluster_items):
        """
        Calculate cluster variance.

        :param covariance: (numpy matrix) Covariance matrix of assets
        :param cluster_indices: (list) Asset indices for the cluster
        :return: (float) Variance of the cluster
        """

        cluster_covariance = covariance_matrix[np.ix_(cluster_items, cluster_items)]
        # The cluster inverse variance function is unnecessarily confusing
        w = 1 / np.diag(cov_slice)  # Inverse variance weights
        w /= w.sum()
        return np.linalg.multi_dot((w, cov_slice, w))

    def _recursive_bisection(self, covariance, indices, assets):
        """
        Recursively assign weights to the clusters - ultimately assigning weights to the individual assets.

        :param covariance: (pd.Dataframe) The covariance matrix
        :param assets: (list) Asset names in the portfolio
        """
        self.weights = np.ones(indices, dtype=np.float64)
        clustered_alphas = [self.ordered_indices]

        while clustered_alphas:
            clustered_alphas = [cluster[start:end]
                                for cluster in clustered_alphas
                                for start, end in ((0, len(cluster) // 2), (len(cluster) // 2, len(cluster)))
                                if len(cluster) > 1]

            for subcluster in range(0, len(clustered_alphas), 2):
                left_cluster = clustered_alphas[subcluster]
                right_cluster = clustered_alphas[subcluster + 1]

                # Get left and right cluster variances and calculate allocation factor
                left_cluster_variance = self._get_cluster_variance(covariance, left_cluster)
                right_cluster_variance = self._get_cluster_variance(covariance, right_cluster)
                alloc_factor = 1 - left_cluster_variance / (left_cluster_variance + right_cluster_variance)

                # Assign weights to each sub-cluster
                self.weights[left_cluster] *= alloc_factor
                self.weights[right_cluster] *= 1 - alloc_factor

        # Assign actual asset values to weight index
        self.weights = dict(zip(assets, self.weights))
