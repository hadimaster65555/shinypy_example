# load library
import faicons as fa
import plotly.express as px
from shinywidgets import output_widget, render_plotly
from shiny import App, reactive, render, req, ui

import numpy as np
import pandas as pd


# data loader
data_link = "https://raw.githubusercontent.com/hadimaster65555/dataset_for_teaching/main/dataset/superstore_dataset/global_superstore.csv"
raw_data = pd.read_csv(data_link)

# data preprocessing
raw_data["ship_date"] = pd.to_datetime(raw_data["ship_date"])
raw_data["order_date"] = pd.to_datetime(raw_data["order_date"])

last_order_date = raw_data["order_date"].max()
earlier_order_date = raw_data["order_date"].min()

# Load data and compute static values
tips = px.data.tips()
bill_rng = (min(tips.total_bill), max(tips.total_bill))

ICONS = {
    "user": fa.icon_svg("user", "regular"),
    "wallet": fa.icon_svg("wallet"),
    "currency-dollar": fa.icon_svg("dollar-sign"),
    "gear": fa.icon_svg("gear")
}

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_date_range(
        "date_range", "Input Tanggal",
            start="2015-01-06", end="2015-01-07",
            min=earlier_order_date, max=last_order_date
        ),
        ui.input_slider("total_bill", "Bill amount", min=bill_rng[0], max=bill_rng[1], value=bill_rng, pre="$"),
        ui.input_checkbox_group("time", "Food service", ["Lunch", "Dinner"], selected=["Lunch", "Dinner"], inline=True),
        ui.input_action_button("reset", "Reset filter"),
        title="SuperStore Dashboard"
    ),
    ui.layout_columns(
        ui.value_box(
            "Total tippers",
            ui.output_ui("total_tippers"),
            showcase=ICONS["user"],
            showcase_layout="left center",
        ),
        ui.value_box(
            "Average tip",
            ui.output_ui("average_tip"),
            showcase=ICONS["wallet"],
            showcase_layout="left center",
        ),
        ui.value_box(
            "Average bill",
            ui.output_ui("average_bill"),
            showcase=ICONS["currency-dollar"],
            showcase_layout="left center",
        ),
        fill=False,
    ),
    ui.layout_columns(
        ui.card(
            ui.card_header("Tips data"),
            ui.output_data_frame("table"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header(
                "Total bill vs tip",
                ui.popover(
                    ICONS["gear"],
                    ui.input_radio_buttons(
                        "scatter_color", None,
                        ["none", "sex", "smoker", "day", "time"],
                        inline=True,
                    ),
                    title="Add a color variable",
                    placement="top",
                ),
                class_="d-flex justify-content-between align-items-center"
            ),
            output_widget("scatterplot"),
            full_screen=True,
        ),
        ui.card(
            ui.card_header(
                "Tip percentages",
                ui.popover(
                    ICONS["gear"],
                    ui.input_radio_buttons(
                        "tip_perc_y", "Split by:",
                        ["sex", "smoker", "day", "time"],
                        selected="day",
                        inline=True,
                    ),
                    title="Add a color variable",
                ),
                class_="d-flex justify-content-between align-items-center",
            ),
            output_widget("tip_perc"),
            full_screen=True,
        ),
        col_widths=[6, 6, 12],
    ),
    title="SuperStore Dashboard",
    fillable=True,
)

def server(input, output, session):

    # --------------------------------------------------------
    # Reactive calculations and effects
    # --------------------------------------------------------

    @reactive.calc
    def tips_data():
        bill = input.total_bill()
        idx1 = tips.total_bill.between(bill[0], bill[1])
        idx2 = tips.time.isin(input.time())
        return tips[idx1 & idx2]

    @reactive.effect
    @reactive.event(input.reset)
    def _():
        ui.update_slider("total_bill", value=bill_rng)
        ui.update_checkbox_group("time", selected=["Lunch", "Dinner"])

    # --------------------------------------------------------
    # Outputs
    # --------------------------------------------------------

    @render.ui
    def total_tippers():
        return tips_data().shape[0]

    @render.ui
    def average_tip():
        d = tips_data()
        req(d.shape[0] > 0)
        perc = d.tip / d.total_bill
        return f"{perc.mean():.1%}"

    @render.ui
    def average_bill():
        d = tips_data()
        req(d.shape[0] > 0)
        bill = d.total_bill.mean()
        return f"${bill:.2f}"

    @render.data_frame
    def table():
        return render.DataGrid(tips_data())


    @render_plotly
    def scatterplot():
        color = input.scatter_color()
        return px.scatter(
            tips_data(),
            x="total_bill",
            y="tip",
            color=None if color == "none" else color,
            trendline="lowess"
        )

    @render_plotly
    def tip_perc():
        from ridgeplot import ridgeplot
        dat = tips_data().copy()
        dat.loc[:, "percent"] = dat.tip / dat.total_bill
        yvar = input.tip_perc_y()
        uvals = dat[yvar].unique()

        samples = [
            [ dat.percent[dat[yvar] == val] ]
            for val in uvals
        ]

        plt = ridgeplot(
            samples=samples, labels=uvals, bandwidth=0.01,
            colorscale="viridis", colormode="row-index"
        )

        plt.update_layout(
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="center", x=0.5)
        )

        return plt

app = App(app_ui, server)
