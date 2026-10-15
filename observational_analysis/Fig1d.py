import os
import numpy as np
import matplotlib
import matplotlib.pyplot as plt


# ============================================================
# Matplotlib settings
# ============================================================

font = {
    "family": "serif",
    "size": 24,
}

matplotlib.rc("font", **font)

plt.rc("legend", fontsize=24)
plt.rc("legend", frameon=False)
plt.rc("text", usetex=True)

matplotlib.rcParams["axes.linewidth"] = 1.3
matplotlib.rcParams["xtick.major.width"] = 1.2
matplotlib.rcParams["ytick.major.width"] = 1.2


# ============================================================
# Input directories
# ============================================================
#
# out  = baseline threshold
# out2 = alternative threshold 1
# out3 = alternative threshold 2
#
# Example:
#
# out  : 0.10 mm h^-1
# out2 : 0.05 mm h^-1
# out3 : 0.20 mm h^-1
#
# ============================================================

NY_FILES = {
    "baseline":
        "../1NY/out/NYC__NORM_PROFILE_BY_WIND.npz",

    "threshold2":
        "../1NY/out2/NYC__NORM_PROFILE_BY_WIND.npz",

    "threshold3":
        "../1NY/out3/NYC__NORM_PROFILE_BY_WIND.npz",
}


KS_FILES = {
    "baseline":
        "../20Kansas/out123/NYC__NORM_PROFILE_BY_WIND.npz",

    "threshold2":
        "../20Kansas/out2/NYC__NORM_PROFILE_BY_WIND.npz",

    "threshold3":
        "../20Kansas/out3/NYC__NORM_PROFILE_BY_WIND.npz",
}


# ============================================================
# Output
# ============================================================

FIG_DIR = "./"

os.makedirs(
    FIG_DIR,
    exist_ok=True,
)

OUT_PNG = os.path.join(
    FIG_DIR,
    "Fig1d.png",
)


# ============================================================
# Plot settings
# ============================================================

XLIM = (-1.5, 3.5)
YLIM = (-0.05, 1.05)


# ============================================================
# Threshold line styles
# ============================================================
#
# Same city = same color
#
# Different threshold = different linestyle
#
# ============================================================

threshold_styles = {

    "baseline": {
        "linestyle": "-",
        "linewidth": 3.2,
    },

    "threshold2": {
        "linestyle": "--",
        "linewidth": 2.6,
    },

    "threshold3": {
        "linestyle": ":",
        "linewidth": 3.0,
    },

}


# ============================================================
# City settings
# ============================================================

cases = [

    {
        "label":
            "New York",

        "files":
            NY_FILES,

        "color":
            "black",
    },

    {
        "label":
            "Kansas",

        "files":
            KS_FILES,

        "color":
            "tab:blue",
    },

]


# ============================================================
# Read one profile
# ============================================================

def read_profile(infile):

    if not os.path.exists(
        infile
    ):

        raise FileNotFoundError(
            f"Cannot find file:\n{infile}"
        )


    data = np.load(
        infile,
        allow_pickle=True,
    )


    x = np.asarray(
        data["x_centers"],
        dtype=float,
    )


    # ========================================================
    # Group 0 = all events
    # ========================================================

    y = np.asarray(
        data["mean_profile_norm"][0, :],
        dtype=float,
    )


    # ========================================================
    # Confidence interval
    # ========================================================

    lo = None
    hi = None


    if (
        "mean_profile_norm_ci_lo" in data.files
        and
        "mean_profile_norm_ci_hi" in data.files
    ):

        lo = np.asarray(
            data["mean_profile_norm_ci_lo"][0, :],
            dtype=float,
        )

        hi = np.asarray(
            data["mean_profile_norm_ci_hi"][0, :],
            dtype=float,
        )


    # ========================================================
    # Event statistics
    # ========================================================

    n_events = np.nan
    mean_speed = np.nan
    mean_lc = np.nan


    if "group_n" in data.files:

        n_events = int(
            data["group_n"][0]
        )


    if "group_mean_speed" in data.files:

        mean_speed = float(
            data["group_mean_speed"][0]
        )


    if "group_mean_lc" in data.files:

        mean_lc = float(
            data["group_mean_lc"][0]
        )


    return (
        x,
        y,
        lo,
        hi,
        n_events,
        mean_speed,
        mean_lc,
    )


# ============================================================
# Plot one city with three thresholds
# ============================================================

def plot_one_city(
    ax,
    city,
):

    label = city["label"]
    color = city["color"]
    files = city["files"]


    for threshold_name in [

        "baseline",
        "threshold2",
        "threshold3",

    ]:


        infile = files[
            threshold_name
        ]


        (
            x,
            y,
            lo,
            hi,
            n_events,
            mean_speed,
            mean_lc,

        ) = read_profile(
            infile
        )


        style = threshold_styles[
            threshold_name
        ]


        # ====================================================
        # Only baseline appears in legend
        # ====================================================

        if threshold_name == "baseline":

            plot_label = label

        else:

            plot_label = "_nolegend_"


        # ====================================================
        # Line
        # ====================================================

        ax.plot(

            x,
            y,

            color=color,

            linestyle=style[
                "linestyle"
            ],

            linewidth=style[
                "linewidth"
            ],

            label=plot_label,

            zorder=3,

        )


        # ====================================================
        # CI shading
        #
        # ONLY for baseline
        # ====================================================

        if (
            threshold_name == "baseline"
            and
            lo is not None
            and
            hi is not None
        ):

            ax.fill_between(

                x,
                lo,
                hi,

                color=color,

                alpha=0.13,

                linewidth=0,

                zorder=1,

            )


        # ====================================================
        # Print information
        # ====================================================

        print(
            f"{label:12s} | "
            f"{threshold_name:10s} | "
            f"N={n_events:6.0f} | "
            f"U={mean_speed:6.2f} m/s | "
            f"Lc={mean_lc:6.2f} km"
        )


# ============================================================
# Main
# ============================================================

def main():


    # ========================================================
    # Figure
    # ========================================================

    fig, ax1 = plt.subplots(

        figsize=(
            8.3,
            5.5,
        )

    )


    plt.subplots_adjust(

        left=0.12,

        bottom=0.16,

        right=0.95,

        top=0.95,

    )


    # ========================================================
    # Plot cities
    # ========================================================

    for city in cases:

        plot_one_city(

            ax=ax1,

            city=city,

        )


    # ========================================================
    # Urban region
    # ========================================================

    ax1.axvline(

        0,

        linestyle="--",

        color="lightgray",

        linewidth=1,

        zorder=0,

    )


    ax1.axvline(

        1,

        linestyle="--",

        color="lightgray",

        linewidth=1,

        zorder=0,

    )


    ax1.axvspan(

        0,
        1,

        color="lightgray",

        alpha=0.5,

        zorder=0,

    )


    # ========================================================
    # Axis labels
    # ========================================================

    ax1.set_xlabel(
        r"$x^*$",fontsize =40
    )


    ax1.set_ylabel(
        r"$P^*$",fontsize =40
    )


    # ========================================================
    # Limits
    # ========================================================

    ax1.set_xlim(
        XLIM
    )


    ax1.set_ylim(
        YLIM
    )


    # ========================================================
    # Region labels
    # ========================================================

    ax1.text(

        0.5,
        0.03,

        "Urban",

        transform=ax1.get_xaxis_transform(),

        ha="center",

        va="bottom",

        fontsize=25,

    )


    ax1.text(

        -1.0,
        0.03,

        "Upwind",

        transform=ax1.get_xaxis_transform(),

        ha="center",

        va="bottom",

        fontsize=25,

    )


    ax1.text(

        2.5,
        0.03,

        "Downwind",

        transform=ax1.get_xaxis_transform(),

        ha="center",

        va="bottom",

        fontsize=25,

    )


    # ========================================================
    # Legend
    #
    # Only city names
    # ========================================================

    ax1.legend(

        fontsize=30,

        loc="upper left",

    )


    # ========================================================
    # Tick settings
    # ========================================================

    ax1.tick_params(

        axis="both",

        which="major",

        direction="out",

        length=6,

        width=1.2,

    )


    # ========================================================
    # Save
    # ========================================================

    plt.savefig(

        OUT_PNG,

        dpi=300,

        bbox_inches="tight",

    )


    plt.close()


    print("")
    print(
        f"Wrote {OUT_PNG}"
    )


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":

    main()



# ============================================================
# Calculate differences between thresholds for each city
# ============================================================

def calculate_threshold_differences():

    print("\n")
    print("=" * 80)
    print("THRESHOLD DIFFERENCE ANALYSIS")
    print("=" * 80)

    # --------------------------------------------------------
    # Only calculate difference over this x* range
    # Same as plotting range
    # --------------------------------------------------------

    X_RANGE = (-1.5, 3.5)

    # --------------------------------------------------------
    # Threshold pairs to compare
    # --------------------------------------------------------

    comparison_pairs = [

        (
            "baseline",
            "threshold2",
        ),

        (
            "baseline",
            "threshold3",
        ),

        (
            "threshold2",
            "threshold3",
        ),

    ]


    # ========================================================
    # Loop over cities
    # ========================================================

    for city in cases:

        city_name = city["label"]

        files = city["files"]


        print("\n")
        print("-" * 80)

        print(
            f"City: {city_name}"
        )

        print("-" * 80)


        # ----------------------------------------------------
        # Read three threshold profiles
        # ----------------------------------------------------

        profiles = {}


        for threshold_name in [

            "baseline",
            "threshold2",
            "threshold3",

        ]:

            (
                x,
                y,
                lo,
                hi,
                n_events,
                mean_speed,
                mean_lc,

            ) = read_profile(

                files[
                    threshold_name
                ]

            )


            profiles[
                threshold_name
            ] = {

                "x": x,
                "y": y,
                "n_events": n_events,

            }


        # ====================================================
        # Compare threshold pairs
        # ====================================================

        for name1, name2 in comparison_pairs:


            x1 = profiles[name1]["x"]

            y1 = profiles[name1]["y"]


            x2 = profiles[name2]["x"]

            y2 = profiles[name2]["y"]


            # ------------------------------------------------
            # Make sure x grids are identical
            # ------------------------------------------------

            if not np.allclose(
                x1,
                x2,
                equal_nan=True,
            ):

                raise ValueError(

                    f"{city_name}: "
                    f"x grid differs between "
                    f"{name1} and {name2}"

                )


            # ------------------------------------------------
            # Select x* range
            # ------------------------------------------------

            mask = (

                (x1 >= X_RANGE[0])

                &

                (x1 <= X_RANGE[1])

                &

                np.isfinite(y1)

                &

                np.isfinite(y2)

            )


            x_use = x1[mask]

            y1_use = y1[mask]

            y2_use = y2[mask]


            # =================================================
            # Point-by-point difference
            #
            # positive means:
            #
            # profile 1 > profile 2
            # =================================================

            difference = (

                y1_use
                -
                y2_use

            )


            abs_difference = np.abs(
                difference
            )


            # =================================================
            # Summary statistics
            # =================================================

            mean_difference = np.mean(
                difference
            )


            mean_absolute_difference = np.mean(
                abs_difference
            )


            rmse = np.sqrt(

                np.mean(

                    difference ** 2

                )

            )


            max_absolute_difference = np.max(
                abs_difference
            )


            # -------------------------------------------------
            # Location where maximum difference occurs
            # -------------------------------------------------

            i_max = np.argmax(
                abs_difference
            )


            x_max_difference = x_use[
                i_max
            ]


            # =================================================
            # Integrated absolute difference
            # =================================================

            integrated_abs_difference = np.trapz(

                abs_difference,

                x_use,

            )


            # =================================================
            # Print
            # =================================================

            print("")

            print(
                f"{name1} - {name2}"
            )

            print(
                f"    Mean difference           = "
                f"{mean_difference:.5f}"
            )

            print(
                f"    Mean absolute difference  = "
                f"{mean_absolute_difference:.5f}"
            )

            print(
                f"    RMSE                      = "
                f"{rmse:.5f}"
            )

            print(
                f"    Max absolute difference   = "
                f"{max_absolute_difference:.5f}"
            )

            print(
                f"    x* of max difference      = "
                f"{x_max_difference:.2f}"
            )

            print(
                f"    Integrated abs difference = "
                f"{integrated_abs_difference:.5f}"
            )


            # =================================================
            # Save point-by-point differences
            # =================================================

            city_safe = (

                city_name
                .replace(" ", "_")
                .replace(",", "")

            )


            outfile = (

                f"{city_safe}_"
                f"{name1}_minus_{name2}_difference.npz"

            )


            np.savez(

                outfile,

                x=x_use,

                profile1=y1_use,

                profile2=y2_use,

                difference=difference,

                absolute_difference=abs_difference,

                mean_difference=mean_difference,

                mean_absolute_difference=
                    mean_absolute_difference,

                rmse=rmse,

                max_absolute_difference=
                    max_absolute_difference,

                x_max_difference=
                    x_max_difference,

                integrated_absolute_difference=
                    integrated_abs_difference,

            )


            print(
                f"    Saved: {outfile}"
            )


# ============================================================
# Run threshold difference analysis
# ============================================================

calculate_threshold_differences()










