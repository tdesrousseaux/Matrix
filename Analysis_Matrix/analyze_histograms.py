import matplotlib
matplotlib.use('Agg') #if used from a window computer
import pandas as pd
import matplotlib.pyplot as plt
from math import sqrt
from matplotlib import cm
import seaborn as sns
from matplotlib.colors import LogNorm
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d import Axes3D
from matplotlib.colors import Normalize
import numpy as np

distribution_label = {"2D_m_Z1-m_Z2" : "", 
                        "pT_ZZ" : "$p_T^{ZZ} (GeV)$", 
                         "m_ZZ" : "$m_{ZZ} (GeV)$", 
                      "absy_ZZ" : "$|y_{ZZ}|$"}

lims = {"m_ZZ" : [0, 500], #[70,200]
     "absy_ZZ" : [0, 5], #[0, 3.15]
       "pT_ZZ" : [0, 250]} 

label_2D = {"2D_m_Z1-m_Z2" : ["$m_{Z1} (GeV)$", "$m_{Z2} (GeV)$"],
         "2D_absy_ZZ-m_ZZ" : ["$|y_{ZZ}|$", "$m_{ZZ} (GeV)$"],
            "2D_m_Z1-m_ZZ" : ["$m_{Z1} (GeV)$", "$m_{ZZ} (GeV)$"]}

def merge_bin_2D_hist(df):
    df = df.reset_index(drop=True)
    # print(df)
    merged_df = pd.DataFrame(columns = ["left-edge1", "left-edge2", "k_factor"])
    len_x = df["left-edge1"].nunique()
    if len_x % 2 == 0 : 
        max_x = len_x
    else : 
        max_x = len_x - 1
    
    len_y = df["left-edge2"].nunique()
    if len_y % 2 == 0 : 
        max_y = len_y
    else : 
        max_y = len_y - 1

    for i in range(0,max_x, 2):
        for j in range(0, max_y, 2):
            k_factor = df.at[i * len_y + j, "k_factor"]
            k_factor += df.at[i * len_y + j + 1, "k_factor"]
            k_factor += df.at[(i+1) * len_y + j, "k_factor"]
            k_factor += df.at[(i+1) * len_y + j + 1, "k_factor"]
            merged_df = merged_df.append({"left-edge1" : df.at[i * len_y + j, "left-edge1"], "left-edge2" : df.at[i * len_y + j, "left-edge2"], "k_factor" : k_factor/4}, 
                    ignore_index = True)
    # print(merged_df)
    return merged_df

def merge_bin_1D_hist(df, nb_bins): #suppose the total number of bins is a multiple of nb_bins
    merged_df = pd.DataFrame(columns = ["left-edge", "right-edge", "scale-central" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down", "rel-up"])
    # print(df.columns)
    df.columns = ["left-edge", "right-edge", "scale-central" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down", "rel-up"]
    len_x = df["left-edge"].nunique()
    for i in range(len_x/nb_bins):
        scale_central = 0
        central_error = 0
        scale_min = 0
        min_error = 0
        scale_max = 0
        max_error = 0

        for j in range(nb_bins):
            idx = i*nb_bins+j
            scale_central += df.at[idx, "scale-central"]
            central_error += df.at[idx, "central-error"]**2
            scale_min += (df.at[idx, "scale-min"] - df.at[idx, "scale-central"])**2
            min_error = df.at[idx, "min-error"]**2
            scale_max += (df.at[idx, "scale-max"] - df.at[idx, "scale-central"])**2
            max_error = df.at[idx, "max-error"]**2

        merged_df = merged_df.append({"left-edge" : df.at[i*nb_bins, "left-edge"],
                                     "right-edge" : df.at[(i+1)*nb_bins - 1, "right-edge"],
                                  "scale-central" : scale_central,
                                  "central-error" : sqrt(central_error),
                                      "scale-min" : scale_central - sqrt(scale_min),
                                      "min-error" : sqrt(min_error),
                                      "scale-max" : scale_central + sqrt(scale_max),
                                      "max-error" : sqrt(max_error),
                                       "rel-down" : (-sqrt(scale_min)/scale_central*100).astype(str),
                                         "rel-up" : (sqrt(scale_min)/scale_central*100).astype(str)}, ignore_index = True )
    # print(merged_df)
    return merged_df

def merge_process(df_list, hist_2D): #FIXME: merge computation errors
    df = df_list[0]
    df_2 = df_list[1]
    if hist_2D:
        header = ["left-edge1", "right-edge1", "left-edge2", "right-edge2", "scale-central" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down", "rel-up"]
    else:
        header = ["left-edge", "right-edge", "scale-central" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down", "rel-up"]
    df.columns = header
    df_2.columns = header
    df_merged = df.copy()
    df_merged["scale-central"] = 3 * df["scale-central"] + 3 * df_2["scale-central"]
    df_merged["scale-min"] = df_merged["scale-central"] - np.sqrt(3*(df["scale-central"] - df["scale-min"])**2 + 3*(df_2["scale-central"] - df_2["scale-min"])**2)
    df_merged["scale-max"] = df_merged["scale-central"] + np.sqrt(3*(df["scale-central"] - df["scale-max"])**2 + 3*(df_2["scale-central"] - df_2["scale-max"])**2)
    df_merged["rel-down"] = 100 * (df_merged["scale-min"] - df_merged["scale-central"]) / df_merged["scale-central"] 
    df_merged["rel-down"] = df_merged["rel-down"].astype(str)
    df_merged["rel-up"] = 100 * (df_merged["scale-max"] - df_merged["scale-central"]) / df_merged["scale-central"] 
    df_merged["rel-up"] = df_merged["rel-up"].astype(str)
    # print(df_merged)
    return df_merged



def compute_k_factor(path_hists, order_LO, order_NLO, distribution, hist_2D = False, nb_bins = 1):

    df_LO_list=[]
    df_NLO_list=[]
    for path_hist in path_hists:

        file_LO = path_hist + "/distributions_%s/%s_%s.dat" %(order_LO, distribution, order_LO)
        file_NLO = path_hist + "/distributions_%s/%s_%s.dat" %(order_NLO, distribution, order_NLO)

        df_LO_list.append(pd.read_csv(file_LO, delimiter='\s+', skiprows = 1, header = None))
        df_NLO_list.append(pd.read_csv(file_NLO, delimiter='\s+', skiprows = 1, header = None))

    if len(path_hists) == 1:
        df_LO = df_LO_list[0]
        df_NLO = df_NLO_list[0]

    else:
        df_LO = merge_process(df_LO_list, hist_2D)
        df_NLO = merge_process(df_NLO_list, hist_2D)
    if hist_2D:
        header = ["left-edge1", "right-edge1", "left-edge2", "right-edge2", "scale-central_LO" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down_LO", "rel-up_LO"]
        idx_scale_central = 4
    else:
        if nb_bins != 1: 
            df_LO = merge_bin_1D_hist(df_LO, nb_bins)
            df_NLO = merge_bin_1D_hist(df_NLO, nb_bins)

        header = ["left-edge", "right-edge", "scale-central_LO" , "central-error", "scale-min", "min-error", "scale-max", "max-error", "rel-down_LO", "rel-up_LO"]
        idx_scale_central = 2
    df_LO.columns = header
    header[idx_scale_central] = "scale-central_NLO"
    header[-1] = "rel-up_NLO"
    header[-2] = "rel-down_NLO"
    df_NLO.columns = header
    if hist_2D:
        df_LO = df_LO[["left-edge1", "left-edge2", "scale-central_LO", "rel-down_LO", "rel-up_LO"]]
        df = pd.merge(df_NLO, df_LO, on=["left-edge1", "left-edge2"])
    else:
        df_LO = df_LO[["left-edge", "scale-central_LO", "rel-down_LO", "rel-up_LO"]]
        df = pd.merge(df_NLO, df_LO, on="left-edge")

    df["rel-down_LO"] = df["rel-down_LO"].str.replace('%','').astype(float)
    df["rel-down_NLO"] = df["rel-down_NLO"].str.replace('%','').astype(float)
    df["rel-up_LO"] = df["rel-up_LO"].str.replace('%','').astype(float)
    df["rel-up_NLO"] = df["rel-up_NLO"].str.replace('%','').astype(float)
    df["k_factor"] = df["scale-central_NLO"] / df["scale-central_LO"]
    df["rel_up_ratio"] = np.sqrt(df["rel-up_NLO"]**2 + df["rel-up_LO"]**2)
    df["rel_down_ratio"] = np.sqrt(df["rel-down_NLO"]**2 + df["rel-down_LO"]**2)
    df["scale_min_ratio"] = df["k_factor"] * (1 - df["rel_down_ratio"]/100.)
    df["scale_max_ratio"] = df["k_factor"] * (1 + df["rel_up_ratio"]/100.)

    return df

def plot_k_factor(df, distribution, process, order_LO, order_NLO, run_number="00", plot_uncertainties=True, ylims=0): 
    df_cut = df[(df["scale-central_LO"] > 0) & (df["scale-central_NLO"] > 0)]
    df_cut.plot(x= "left-edge", y="k_factor", color = 'red')
    # print(df_cut)
    uncertainties = ""
    if plot_uncertainties:
        plt.fill_between(df["left-edge"], df["scale_min_ratio"], df["scale_max_ratio"], color='yellow', label = "scale uncertainties")
        uncertainties = "_unc"
    plt.xlabel(distribution_label[distribution])
    plt.ylabel(r"$k-factor$")
    plt.title(process)
    plt.xlim(lims[distribution])
    if ylims!=0:
        plt.ylim(ylims)
    plt.grid()
    plt.legend()
    if run_number == "00":
        plt.savefig("k_factor%s_%s_%s.png" % (uncertainties, process, distribution))
    else:
        plt.savefig("k_factor%s_%s_%s_run_%s%s.png" % (uncertainties, process, distribution, run_number[0], order_NLO))
    plt.close()

def plot_uncertainties_NLO(df, distribution, process, run_number="00"):
    df.plot(x= "left-edge", y="rel-up")
    # print(df_cut)
    plt.xlabel(distribution_label[distribution])
    plt.ylabel("rel_up_error")
    plt.title(process)
    plt.xlim([0,250])
    plt.grid()
    if run_number == "00":
        plt.savefig("rel_up_error_%s_%s.png" % (process, distribution))
    else:
        plt.savefig("rel_up_error_%s_%s_run_%s.png" % (process, distribution, run_number[0]))
    plt.close()


def k_factor_2D_plots(df, distribution, process, order_NLO, run_number="00", view_3D = False, merged = False):
    x_range = [40,500]
    y_range = [20,500]
    df_wide = df[(df['left-edge1'].between(*x_range)) & (df['left-edge2'].between(*y_range))]
    if merged:
        df_wide = merge_bin_2D_hist(df_wide)
        merged_bin = "_merged"
    else:
        merged_bin = ""

    df_pivot = df_wide.pivot(index = 'left-edge2', columns = 'left-edge1', values='k_factor')
    if view_3D :
        view = "3D"
        Z = np.array(df_pivot.values)
        # print(Z)
        # vmin = 0
        # vmax = 2
        # norm = Normalize(vmin=vmin, vmax=vmax)
        mask = np.isnan(Z)
        # print(Z[~mask])
        X, Y = np.meshgrid(np.array(df_pivot.columns), np.array(df_pivot.index))
        fig, ax = plt.subplots(subplot_kw={"projection": "3d"})
        # surf = ax.plot_surface(np.ma.masked_array(X, mask), np.ma.masked_array(Y, mask), np.ma.masked_array(Z, mask), cmap='viridis')
        ax.plot_wireframe(X, Y, Z)
        ax.set_zlim([0, 2])
        # fig.colorbar(surf, shrink=0.5, aspect=5)
        ax.view_init(elev= 20, azim=-70)

    else:
        view = "2D"
        ax = sns.heatmap(df_pivot, square=True, vmin=0, vmax=2)
        ax.invert_yaxis()

    plt.xlabel(label_2D[distribution][0])
    plt.ylabel(label_2D[distribution][1])
    plt.title("k-factor %s" %process)

   
    plt.savefig("k_factor_%s_%s_run_%s%s_%s%s.png" % (process, distribution, run_number[0], order_NLO, view, merged_bin))
    plt.close()

def plot_cross_sections(df, distribution, process, order_LO, order_NLO, run_number, lim=0):
    ax = df.plot(x= "left-edge", y=["scale-central_LO","scale-central_NLO"])
    # print(order_LO[1:])
    ax.legend([order_LO[1:], order_NLO[1:]])
    plt.xlabel(distribution_label[distribution])
    plt.ylabel(r"$\sigma (fb)$")
    if lim !=0 :
        plt.xlim(lim)
    plt.title("cross-section %s" %process)
    plt.grid()
    plt.savefig("cross_section_%s_%s_run_%s%s.png" % (process, distribution, run_number[0], order_NLO))
    plt.close()

if __name__ == "__main__" :
    process = "ppeeexex04"
    # process = "ppemexmx04"
    # process = "4lep"
    if process == "4lep":
        process_list = ["ppeeexex04", "ppemexmx04"]
    else:
        process_list=[process]
    # run_number = ["25", "14"]
    # run_number = ["35", "24"]
    run_number = ["32"]
    run_order = "NNLO"
    path_hists=[]
    path_Matrix = "/eos/user/t/tdesrous/private/CMSSW_10_2_13/src/Matrix"
    for i in range(len(process_list)):
        path_hists.append(path_Matrix + "/run/%s_MATRIX/result/run_%s/%s-run" % (process_list[i], run_number[i], run_order))

    # order_NLO = "_NLO_QCD"
    # order_NLO = "_NLO_QCD+NLO_EW"
    # order_LO = "_LO"

    order_NLO = "_loopNLOgg_QCD"
    order_LO = "_loopLOgg_QCD"

    # order_NLO = "_NNLO_QCD"
    # order_LO = "_NLO_QCD"

    distributions = ["m_ZZ", "absy_ZZ"]
    # distributions = ["m_ZZ"]
    # distributions = ["pT_ZZ"]
    for distribution in distributions:
        df = compute_k_factor(path_hists, order_LO, order_NLO, distribution, hist_2D = False, nb_bins = 5)
        plot_k_factor(df, distribution, process, order_LO, order_NLO, run_number, ylims=[0,4])
        plot_cross_sections(df, distribution, process, order_LO, order_NLO, run_number, lims[distribution])

    # print(df)
    # plot_uncertainties_NLO(df, distribution, process, run_number)
    # distributions = ["2D_m_Z1-m_Z2", "2D_absy_ZZ-m_ZZ", "2D_m_Z1-m_ZZ"]
    # distributions = ["2D_m_Z1-m_Z2", "2D_m_Z1-m_ZZ"]
    # for distribution in distributions:
    #     df = compute_k_factor(path_hists, order_LO, order_NLO, distribution, hist_2D = True) 
    #     # k_factor_2D_plots(df, distribution, process, order_NLO, run_number, view_3D=True, merged = False)
    #     # k_factor_2D_plots(df, distribution, process, order_NLO, run_number, view_3D=True, merged = True)
    #     k_factor_2D_plots(df, distribution, process, order_NLO, run_number, view_3D=False, merged = False)
    #     # k_factor_2D_plots(df, distribution, process, order_NLO, run_number, view_3D=False, merged = True)
