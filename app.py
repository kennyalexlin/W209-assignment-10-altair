import altair as alt
import pandas as pd
import streamlit as st

st.header("W209 Assignment #10")

if "df" not in st.session_state:
    st.session_state["df"] = pd.read_csv("players_20.csv")
    alt.data_transformers.enable("vegafusion")

# data transforms
df = st.session_state["df"].copy()
# st.dataframe(df)
df = df[df["body_type"].isin(["Normal", "Lean", "Stocky"])]
df["player_positions_ls"] = df["player_positions"].str.split(",")
df["player_positions_ls"] = df['player_positions_ls'].apply(lambda x: [i.strip() for i in x])
df["num_positions"] = df["player_positions_ls"].map(len)
to_plot = df[["body_type", "player_positions_ls", "num_positions"]].explode(
    column="player_positions_ls"
)
to_plot = pd.get_dummies(to_plot, columns=["player_positions_ls"])

dummies = [col for col in to_plot.columns if "player_positions" in col]
for col in dummies:
    to_plot[col] = to_plot[col].map({True: 1, False: 0}) / to_plot["num_positions"]
to_plot = to_plot.groupby(by="body_type").agg("sum").reset_index()
to_plot = to_plot.melt(id_vars="body_type", value_vars=dummies)
rename_dict = {k: k.split("player_positions_ls_")[1] for k in dummies}
to_plot["variable"] = to_plot["variable"].map(rename_dict)
# st.dataframe(to_plot.head())

options = to_plot["body_type"].unique().tolist()
selected_body_types = st.pills(
    label="Selected Body Type",
    options=options,
    selection_mode="multi",
    default=options,
)
st.info("Select bars on the graph to view the distribution of weights within the selected body type and position. Shift + Click to select multiple", icon="💬")

height = max(len(selected_body_types) * 120, 200)
to_plot = to_plot[to_plot["body_type"].isin(selected_body_types)]


select = alt.selection_point(on="click", name="selected_bar")
highlight = alt.selection_point(name="highlighted_bar", on="pointerover", empty=False)
stroke_width = (
    alt.when(select)
    .then(alt.value(2, empty=False))
    .when(highlight)
    .then(alt.value(1))
    .otherwise(alt.value(0))
)
# plot chart
chart = (
    alt.Chart(data=to_plot)
    .mark_bar(cursor="pointer", stroke="white")
    .encode(
        x=alt.X("value:Q", title="Proportion", stack="normalize"),
        y=alt.Y("body_type:N", title="Body Type"),
        color=alt.Color("variable:N", title="Position", legend=alt.Legend(columns=2)),
        strokeWidth=stroke_width,
        fillOpacity=alt.when(select).then(alt.value(1)).otherwise(alt.value(0.5)),
        tooltip=[
            alt.Tooltip("value:Q", title="Number of Players", format=".0f"),
            alt.Tooltip("variable:N", title="Position"),
        ],
    )
).add_params(select, highlight)
selected = st.altair_chart(
    chart.properties(
        # width=600,
        height=height,
        title="Representation of Positions by Body Type",
    ),
    use_container_width=True,
    on_select="rerun",
)
plot_dfs = []
if "selected_bar" in selected["selection"]:
    if len(selected["selection"]["selected_bar"]):
        for i in selected["selection"]["selected_bar"]:
            cur = df[df["body_type"] == i["body_type"]]
            cur["is_player_position"] = cur["player_positions_ls"].apply(
                lambda x: True if i["variable"] in x else False
            )
            cur = cur[cur['is_player_position']]
            plot_dfs.append(cur)

        columns = st.columns(len(plot_dfs))
        for idx, df in enumerate(plot_dfs):
            chart = (
                alt.Chart(df)
                .mark_bar()
                .encode(
                    x=alt.X("weight_kg:Q", bin=True),
                    y='count()'
                )
            )
            columns[idx].altair_chart(chart)
