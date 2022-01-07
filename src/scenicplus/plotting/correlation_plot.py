from scipy.cluster.hierarchy import linkage, dendrogram, fcluster
from scipy.spatial.distance import squareform
import seaborn as sns
import numpy as np
import pandas as pd
import plotly.express as px
from typing import Dict, List, Tuple
from typing import Optional, Union
import sklearn
import matplotlib.pyplot as plt

def correlation_heatmap(scplus_obj: 'SCENICPLUS',
                        auc_key: Optional[str] = 'eRegulon_AUC', 
                        signature_keys: Optional[List[str]] = ['Gene_based', 'Region_based'],
                        scale: Optional[bool] = False,
                        linkage_method: Optional[str] = 'average',
                        fcluster_threshold: Optional[float] = 0.1,
                        selected_regulons: Optional[List[int]] = None,
                        cmap: Optional[str] = 'viridis',
                        plotly_height: Optional[int] = 1000,
                        fontsize: Optional[int] = 3,
                        save: Optional[str] = None,
                        use_plotly: Optional[int] = True,
                        figsize: Optional[Tuple[int, int]] = (20, 20)
                       ):
                       
    """
    Plot correlation between eRegulons enrichment,
    
    Parameters
    ---------
    scplus_obj: `class::SCENICPLUS`
        A SCENICPLUS object with eRegulons AUC computed.
    auc_key: str, optional
        Key to extract AUC values from. Default: 'eRegulon_AUC'
    signature_keys: List, optional
        Keys to extract AUC values from. Default: ['Gene_based', 'Region_based']
    scale: bool, optional
        Whether to scale the enrichments prior to the dimensionality reduction. Default: False
    linkage_method: str, optional
        Linkage method to use for clustering. See `scipy.cluster.hierarchy.linkage`.
    fcluster_threshold: float, optional
        Threshold to use to divide hierarchical clustering into clusters. See `scipy.cluster.hierarchy.fcluster`.
    selected_regulons: list, optional
        A list with selected regulons to be used for clustering. Default: None (use all regulons)
    cmap: str or 'matplotlib.cm', optional
        For continuous variables, color map to use for the legend color bar. Default: cm.viridis
    plotly_height: int, optional
        Height of the plotly plot. Width will be adjusted accordingly
    fontsize: int, optional
        Labels fontsize
    save: str, optional
        Path to save heatmap as file
    use_plotly: bool, optional
        Use plotly or seaborn to generate the image
    figsize: tupe, optional
        Matplotlib figsize, used only if use_plotly == False
    """
    if scale:
        data_mat = pd.concat([pd.DataFrame(sklearn.preprocessing.StandardScaler().fit_transform(
            scplus_obj.uns[auc_key][x].T), index=scplus_obj.uns[auc_key][x].T.index.to_list(), columns=scplus_obj.uns[auc_key][x].T.columns) for x in signature_keys]).T
    else:
        data_mat = pd.concat([scplus_obj.uns[auc_key][x] for x in signature_keys], axis = 1)
    if selected_regulons is not None:
        subset = [x for x in selected_regulons if x in data_mat.columns]
        data_mat = data_mat[subset]
    #check if some eRegulon AUC are all 0 and remove them
    all_zero_eregs = data_mat.columns[np.where(data_mat.sum(0) == 0)]
    if len(all_zero_eregs) > 0:
        print(f"Following eregulons have an AUC value of all zero and will be removed: {', '.join(all_zero_eregs)}")
        data_mat.drop(all_zero_eregs, axis = 1, inplace = True)
    correlations = data_mat.corr()
    similarity = 1 - correlations
    #use np.clip: due to floating point impercisions some very small values become negative, clip them to 0
    Z = linkage(np.clip(squareform(similarity), 0, similarity.to_numpy().max()), linkage_method)
    # Clusterize the data
    labels = fcluster(Z, fcluster_threshold)
    # Keep the indices to sort labels
    labels_order = np.argsort(labels)
    # Build a new dataframe with the sorted columns
    for idx, i in enumerate(data_mat.columns[labels_order]):
        if idx == 0:
            clustered = pd.DataFrame(data_mat[i])
        else:
            df_to_append = pd.DataFrame(data_mat[i])
            clustered = pd.concat([clustered, df_to_append], axis=1)
    correlations = clustered.corr()
    if use_plotly:
        fig = px.imshow(clustered.corr(), color_continuous_scale=cmap)
        fig.update_layout(
            height=plotly_height,  # Added parameter
            legend= {'itemsizing': 'trace'},
            plot_bgcolor='rgba(0,0,0,0)',
            yaxis = dict(tickfont = dict(size=fontsize)),
            xaxis = dict(tickfont = dict(size=fontsize)),
        )
        if save is not None:
            fig.write_image(save)
        fig.show()
    else:
        fig, ax = plt.subplots(figsize = figsize)
        sns.heatmap(
            data = correlations,
            cmap = cmap,
            square = True,
            ax = ax,
            robust = True,
            cbar_kws={"shrink": .50, 'label': 'Correlation'},
            xticklabels=False)
        if save is not None:
            fig.tight_layout()
            fig.savefig(save)
        plt.show()
        plt.close(fig)
