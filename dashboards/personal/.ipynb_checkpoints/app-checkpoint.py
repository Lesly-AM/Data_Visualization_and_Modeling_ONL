"""Personal dashboard starter: replace the placeholder before submission."""
from pathlib import Path
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output


def build_dashboard(data):
    """
    Build and return a new Dash app for the daily bike-rental dataset.
    Does not start the server.

    Expected input: a pandas DataFrame with the columns used below, such as
    the supplied day.csv loaded into rentals_df.
    """
    # Work from a copy of the original data and reproduce the requested subset.
    required = [
        "instant", "dteday", "mnth", "workingday",
        "weathersit", "windspeed", "cnt"
    ]
    missing = [column for column in required if column not in data.columns]
    if missing:
        raise ValueError(f"Input data is missing required columns: {missing}")

    bike_rentals_df = data.copy()
    bike_rentals_df = bike_rentals_df[
        ["instant", "dteday", "mnth", "workingday",
         "weathersit", "windspeed", "cnt"]
    ].copy()

    bike_rentals_df["dteday"] = pd.to_datetime(
        bike_rentals_df["dteday"], errors="coerce"
    )
    for col in ["mnth", "workingday", "weathersit", "windspeed", "cnt"]:
        bike_rentals_df[col] = pd.to_numeric(
            bike_rentals_df[col], errors="coerce"
        )

    # Remove only rows unusable for the requested views; report the resulting n.
    bike_rentals_df = bike_rentals_df.dropna(
        subset=["dteday", "mnth", "workingday", "weathersit", "windspeed", "cnt"]
    ).copy()
    bike_rentals_df["mnth"] = bike_rentals_df["mnth"].astype(int)
    bike_rentals_df["workingday"] = bike_rentals_df["workingday"].astype(int)
    bike_rentals_df["weathersit"] = bike_rentals_df["weathersit"].astype(int)

    pastel = {0: "#9DBAD5", 1: "#E8A598"}
    workingday_labels = {0: "Non-working day", 1: "Working day"}
    weather_labels = {
        1: "1 — Clear",
        2: "2 — Misty / cloudy",
        3: "3 — Light snow / rain",
        4: "4 — Inclement"
    }
    month_labels = {
        1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr",
        5: "May", 6: "Jun", 7: "Jul", 8: "Aug",
        9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec"
    }
    font = "Arial, sans-serif"

    def empty_figure(message, title):
        fig = go.Figure()
        fig.update_layout(
            title=title,
            annotations=[dict(
                text=message, x=0.5, y=0.5, xref="paper", yref="paper",
                showarrow=False, font=dict(size=15)
            )],
            template="plotly_white",
            font=dict(family=font),
            height=420,
            margin=dict(l=55, r=25, t=75, b=65)
        )
        return fig

    def style(fig, title, x_title, y_title):
        fig.update_layout(
            title=title,
            xaxis_title=x_title,
            yaxis_title=y_title,
            template="plotly_white",
            font=dict(family=font, size=12),
            title_font=dict(size=19),
            height=420,
            margin=dict(l=55, r=25, t=75, b=65),
            legend_title_text="Working-day status"
        )
        return fig

    def n_label(frame):
        return f"Records shown: n = {len(frame):,}"

    app = Dash(__name__)
    weather_options = [
        {"label": weather_labels[w], "value": w}
        for w in [1, 2, 3, 4]
    ]

    app.layout = html.Div(
        style={
            "fontFamily": font, "maxWidth": "1400px", "margin": "0 auto",
            "padding": "22px", "backgroundColor": "#FAFBFD",
            "color": "#263238"
        },
        children=[
            html.H1("Daily Bike Rental Demand: Weather and Working-Day Status",
                    style={"marginBottom": "6px"}),
            html.P(
                "Explore how daily rental counts vary by working-day status, "
                "windspeed, month, and weather conditions.",
                style={"color": "#536471", "marginTop": "0"}
            ),
            html.Div(
                id="overall-summary",
                style={
                    "padding": "14px 16px", "backgroundColor": "#EEF3F7",
                    "borderRadius": "8px", "marginBottom": "20px"
                }
            ),
            html.Div([
                html.H2("Daily rental counts by working-day status"),
                html.P(
                    "Box plot of daily cnt values, grouped by workingday "
                    "(0 = non-working day; 1 = working day). Each point is "
                    "one day; units are bikes rented per day."
                ),
                dcc.Graph(id="workingday-box")
            ], style={"backgroundColor": "white", "padding": "16px",
                      "borderRadius": "8px", "marginBottom": "18px"}),

            html.Div([
                html.H2("Daily rental counts versus windspeed"),
                html.P(
                    "Each point is one day. Windspeed is normalized "
                    "(0–1, lower to higher); cnt is total bikes rented that day. "
                    "Color indicates working-day status."
                ),
                dcc.Graph(id="windspeed-scatter")
            ], style={"backgroundColor": "white", "padding": "16px",
                      "borderRadius": "8px", "marginBottom": "18px"}),

            html.Div([
                html.H2("Monthly average daily rentals"),
                html.P(
                    "Lines show mean daily cnt for each month and working-day "
                    "status. The month selector filters this view only; means "
                    "and sample sizes are recalculated from the selected rows."
                ),
                html.Label("Month range"),
                dcc.RangeSlider(
                    id="month-range", min=1, max=12, step=1, value=[1, 12],
                    marks={m: month_labels[m] for m in range(1, 13)},
                    allowCross=False,
                    tooltip={"placement": "bottom", "always_visible": False}
                ),
                html.Div(id="month-sample-size",
                         style={"marginTop": "12px", "color": "#536471"}),
                dcc.Graph(id="monthly-line")
            ], style={"backgroundColor": "white", "padding": "16px",
                      "borderRadius": "8px", "marginBottom": "18px"}),

            html.Div([
                html.H2("Daily rental counts by weather and working-day status"),
                html.P(
                    "Bars show mean daily cnt for each weather category, split "
                    "by working-day status. This uses average daily rentals, "
                    "not the number of days in each category."
                ),
                html.Label("Weather categories"),
                dcc.Dropdown(
                    id="weather-filter", options=weather_options,
                    value=[1, 2, 3, 4], multi=True, clearable=False,
                    placeholder="Select one or more weather categories"
                ),
                html.Div(id="weather-sample-size",
                         style={"marginTop": "12px", "color": "#536471"}),
                dcc.Graph(id="weather-bar")
            ], style={"backgroundColor": "white", "padding": "16px",
                      "borderRadius": "8px", "marginBottom": "18px"}),

            html.H2("Research question, interpretation, and limitations"),
            html.P(
                "Research question: How does daily rental demand vary with "
                "weather and working-day status?"
            ),
            html.P(
                "Source: the supplied day.csv dataset. One row represents one "
                "day of rentals and its associated weather/calendar information. "
                "The dashboard uses only the requested seven columns."
            ),
            html.P(
                "Interpretation note: comparisons of daily demand use cnt "
                "(total bikes rented per day). The monthly and weather bar "
                "charts use mean daily cnt so categories with different numbers "
                "of observed days can be compared fairly. The box plot shows "
                "the distribution of individual days, and the scatter plot "
                "shows individual days rather than aggregated values."
            ),
            html.P(
                "Limitations: the dataset covers the recorded 2011–2012 period; "
                "windspeed is normalized rather than expressed in a physical "
                "unit; weather categories are ordinal labels, not equal numeric "
                "steps; and associations do not establish that weather or "
                "working-day status caused a change in demand. The supplied "
                "daily dataset has no category 4 weather records, so that "
                "category may appear empty."
            )
        ]
    )

    @app.callback(
        Output("overall-summary", "children"),
        Input("month-range", "value"),
        Input("weather-filter", "value")
    )
    def update_overall_summary(month_range, selected_weather):
        # Explicitly label these as full-dataset results, independent of filters.
        total_n = len(bike_rentals_df)
        means = bike_rentals_df.groupby("workingday")["cnt"].mean()
        medians = bike_rentals_df.groupby("workingday")["cnt"].median()
        if 0 in means.index and 1 in means.index:
            summary = (
                f"All usable records (not filtered by the controls): n = {total_n:,}. "
                f"Mean daily rentals — non-working days: {means.loc[0]:,.1f}; "
                f"working days: {means.loc[1]:,.1f}. "
                f"Median daily rentals — non-working days: {medians.loc[0]:,.0f}; "
                f"working days: {medians.loc[1]:,.0f}. "
                "These are full-dataset descriptive statistics."
            )
        else:
            summary = (
                f"All usable records (not filtered by the controls): n = {total_n:,}. "
                "At least one working-day group is absent, so the comparison "
                "cannot be calculated."
            )
        return html.Div([
            html.Strong("Full-dataset reference — "),
            html.Span(summary)
        ])

    @app.callback(
        Output("workingday-box", "figure"),
        Input("month-range", "value"),
        Input("weather-filter", "value")
    )
    def update_workingday_box(_month_range, _selected_weather):
        # This view always shows all usable records; controls do not filter it.
        df = bike_rentals_df
        if df.empty:
            return empty_figure("No usable records.", "Bike Rentals based on Working Day (2011-2012)")
        fig = px.box(
            df, x="workingday", y="cnt", points="outliers",
            category_orders={"workingday": [0, 1]},
            color="workingday",
            color_discrete_map=pastel,
            labels={"workingday": "Working-day status", "cnt": "Daily rentals (bikes)"},
            hover_data=["dteday"]
        )
        fig.update_xaxes(
            tickmode="array", tickvals=[0, 1],
            ticktext=["0 — Non-working day", "1 — Working day"]
        )
        fig.update_layout(showlegend=False)
        return style(fig, "Bike Rentals based on Working Day (2011-2012)",
                     "Working-day status", "Daily rental count (bikes/day)")

    @app.callback(
        Output("windspeed-scatter", "figure"),
        Input("month-range", "value"),
        Input("weather-filter", "value")
    )
    def update_windspeed_scatter(_month_range, _selected_weather):
        # This view always shows all usable records; controls do not filter it.
        df = bike_rentals_df
        if df.empty:
            return empty_figure("No usable records.", "Bike Rentals based on Windspeed (2011-2012)")
        # Use text categories so Plotly Express treats workingday as discrete,
        # producing separate traces with stable legend labels and pastel colors.
        df = df.copy()
        df["workingday_label"] = df["workingday"].map(workingday_labels)
        fig = px.scatter(
            df, x="windspeed", y="cnt", color="workingday_label",
            color_discrete_map={
                "Non-working day": pastel[0], "Working day": pastel[1]
            },
            category_orders={
                "workingday_label": ["Non-working day", "Working day"]
            },
            labels={
                "windspeed": "Normalized windspeed (0–1)",
                "cnt": "Daily rental count (bikes/day)",
                "workingday_label": "Working-day status"
            },
            hover_data=["dteday", "weathersit"]
        )
        return style(fig, "Bike Rentals based on Windspeed (2011-2012)",
                     "Normalized windspeed (0–1)", "Daily rental count (bikes/day)")

    @app.callback(
        Output("monthly-line", "figure"),
        Output("month-sample-size", "children"),
        Input("month-range", "value")
    )
    def update_monthly_line(month_range):
        if not month_range or len(month_range) != 2:
            return empty_figure("Choose a month range.", "Bike Rentals based on Months of the Year (2011-2012)"), "No month range selected."
        low, high = sorted([int(month_range[0]), int(month_range[1])])
        df = bike_rentals_df[bike_rentals_df["mnth"].between(low, high)].copy()
        sample_text = f"Selected months: {month_labels[low]}–{month_labels[high]}. {n_label(df)}."
        if df.empty:
            return empty_figure("No records for this month range.", "Bike Rentals based on Months of the Year (2011-2012)"), sample_text

        summary = (
            df.groupby(["mnth", "workingday"], as_index=False)
              .agg(mean_cnt=("cnt", "mean"), days=("cnt", "size"))
        )
        summary["workingday_label"] = summary["workingday"].map(workingday_labels)
        fig = px.line(
            summary, x="mnth", y="mean_cnt", color="workingday_label",
            markers=True, color_discrete_map={
                "Non-working day": pastel[0], "Working day": pastel[1]
            },
            category_orders={"workingday_label": ["Non-working day", "Working day"]},
            custom_data=["days"],
            labels={
                "mnth": "Month", "mean_cnt": "Mean daily rentals (bikes/day)",
                "workingday_label": "Working-day status"
            }
        )
        fig.update_traces(
            hovertemplate="Month: %{x}<br>Mean daily rentals: %{y:.1f}"
                          "<br>Days in group: %{customdata[0]}<extra></extra>"
        )
        fig.update_xaxes(
            tickmode="array", tickvals=list(range(low, high + 1)),
            ticktext=[month_labels[m] for m in range(low, high + 1)]
        )
        return style(fig, "Bike Rentals based on Months of the Year (2011-2012)",
                     "Month", "Mean daily rental count (bikes/day)"), sample_text

    @app.callback(
        Output("weather-bar", "figure"),
        Output("weather-sample-size", "children"),
        Input("weather-filter", "value")
    )
    def update_weather_bar(selected_weather):
        if selected_weather is None:
            selected_weather = []
        selected_weather = [int(w) for w in selected_weather if int(w) in [1, 2, 3, 4]]
        df = bike_rentals_df[bike_rentals_df["weathersit"].isin(selected_weather)].copy()
        weather_text = ", ".join(weather_labels[w] for w in selected_weather) if selected_weather else "none"
        sample_text = f"Selected weather: {weather_text}. {n_label(df)}."
        if df.empty:
            return empty_figure(
                "No records for the selected weather categories.",
                "Daily Bike Rental Count by Weather"
            ), sample_text

        summary = (
            df.groupby(["weathersit", "workingday"], as_index=False)
              .agg(mean_cnt=("cnt", "mean"), days=("cnt", "size"))
        )
        summary["workingday_label"] = summary["workingday"].map(workingday_labels)
        fig = px.bar(
            summary, x="weathersit", y="mean_cnt", color="workingday_label",
            barmode="group",
            category_orders={"weathersit": [1, 2, 3, 4],
                             "workingday_label": ["Non-working day", "Working day"]},
            color_discrete_map={
                "Non-working day": pastel[0], "Working day": pastel[1]
            },
            custom_data=["days"],
            labels={
                "weathersit": "Weather category",
                "mean_cnt": "Mean daily rentals (bikes/day)",
                "workingday_label": "Working-day status"
            }
        )
        fig.update_traces(
            hovertemplate="%{x}<br>Mean daily rentals: %{y:.1f}"
                          "<br>Days in group: %{customdata[0]}<extra></extra>"
        )
        fig.update_xaxes(
            tickmode="array", tickvals=[1, 2, 3, 4],
            ticktext=[weather_labels[w] for w in [1, 2, 3, 4]]
        )
        fig = style(fig, "Daily Bike Rental Count by Weather",
                    "Weather category (1 = clearest; 4 = most inclement)",
                    "Mean daily rental count (bikes/day)")
        return fig, sample_text

    return app


# After copying your original dataset into data/, replace None below:
# Use the loader appropriate for your actual file format.
data = pd.read_csv(Path(__file__).resolve().parent / 'data' / 'day.csv')
app = build_dashboard(data)
server = app.server

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=8055, debug=False)
