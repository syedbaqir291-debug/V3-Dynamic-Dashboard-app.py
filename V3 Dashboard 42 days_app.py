import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Oncology Dashboard SKMCH & RC", layout="wide")

st.markdown("""
<style>
.stApp { background-color:#eef2f7; }
h1 { font-family: 'Segoe UI', sans-serif; font-weight:700; }
.upload-box {
    background:white;
    padding:25px;
    border-radius:12px;
    box-shadow:0px 4px 15px rgba(0,0,0,0.08);
}
</style>
""", unsafe_allow_html=True)

st.title("Oncology Dashboard SKMCH & RC")

uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])

if uploaded_file:

    df = pd.read_excel(uploaded_file)

    month_col = "Month"
    cancer_col = "Cancer Category"

    parameter_cols = [
        "1st visit - WIC acceptance",
        "WIC acceptance - 1st OPD visit",
        "1st OPD visit - MDT",
        "MDT - 1st day of treatment",
        "Number of days"
    ]

    for col in parameter_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    data_json = df.to_json(orient="records")

    months = sorted(df[month_col].dropna().unique(),
                    key=lambda x: pd.to_datetime(x, errors="coerce"))

    cancers = sorted(df[cancer_col].dropna().unique())

    html = f"""
<!DOCTYPE html>
<html>
<head>

<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

<style>

body {{
    font-family: 'Segoe UI', sans-serif;
    background:#eef2f7;
    margin:0;
}}

.header {{
    background:white;
    padding:20px 40px;
    font-size:22px;
    font-weight:700;
    box-shadow:0 2px 8px rgba(0,0,0,0.05);
}}

.container {{
    padding:30px;
}}

.top-row {{
    display:flex;
    gap:20px;
}}

.filters {{
    flex:3;
    display:flex;
    gap:20px;
    flex-wrap:wrap;
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 4px 15px rgba(0,0,0,0.08);
}}

.filter-box {{
    display:flex;
    flex-direction:column;
    font-size:14px;
}}

select {{
    padding:10px;
    border-radius:8px;
    border:1px solid #ccc;
}}

.benchmark-box {{
    flex:1;
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 4px 15px rgba(0,0,0,0.08);
}}

.benchmark-title {{
    font-weight:700;
    margin-bottom:10px;
}}

.benchmark-item {{
    margin:6px 0;
}}

#chart, #runChart {{
    margin-top:25px;
    background:white;
    padding:20px;
    border-radius:12px;
    box-shadow:0 4px 15px rgba(0,0,0,0.08);
}}

</style>
</head>

<body>

<div class="header">Oncology Dashboard</div>

<div class="container">

<div class="top-row">

<div class="filters">

<div class="filter-box">
<label>Metric</label>
<select id="metric">
<option>Mean</option>
<option>Median</option>
<option>SD</option>
<option>Maximum</option>
<option>Minimum</option>
</select>
</div>

<div class="filter-box">
<label>Month</label>
<select id="month" multiple></select>
</div>

<div class="filter-box">
<label>Cancer Category</label>
<select id="cancer" multiple></select>
</div>

</div>

<div class="benchmark-box">
<div class="benchmark-title">Benchmarks</div>
<div id="benchmarks"></div>
</div>

</div>

<div id="chart"></div>
<div id="runChart"></div>

</div>

<script>

let rawData = {data_json};
let months = {json.dumps(list(months))};
let cancers = {json.dumps(list(cancers))};
let parameters = {json.dumps(parameter_cols)};

let monthSelect = document.getElementById("month");
let cancerSelect = document.getElementById("cancer");

/* Populate */
months.forEach(m => {{
    let opt = new Option(m, m, true, true);
    monthSelect.appendChild(opt);
}});

cancers.forEach((c,i) => {{
    let opt = new Option(c, c, i===0, i===0);
    cancerSelect.appendChild(opt);
}});

/* Helpers */
function getSelected(sel) {{
    return Array.from(sel.selectedOptions).map(o=>o.value)
}}

function calculateMetric(values, metric) {{
    values = values.filter(v => v !== null && !isNaN(v))
    if(values.length===0) return 0

    if(metric==="Mean") return values.reduce((a,b)=>a+b,0)/values.length

    if(metric==="Median") {{
        values.sort((a,b)=>a-b)
        let m=Math.floor(values.length/2)
        return values.length%2 ? values[m] : (values[m-1]+values[m])/2
    }}

    if(metric==="SD") {{
        let mean = values.reduce((a,b)=>a+b,0)/values.length
        let v = values.reduce((a,b)=>a+(b-mean)**2,0)/(values.length-1)
        return Math.sqrt(v)
    }}

    if(metric==="Maximum") return Math.max(...values)
    if(metric==="Minimum") return Math.min(...values)
}}

/* Benchmarks */
let cutoffs = [15,7,10,20,43]

function updateBenchmarks(colors) {{
    let html = `
    <div style="color:${{colors[0]}}">1st visit - WIC acceptance: &lt; 15</div>
    <div style="color:${{colors[1]}}">WIC → OPD: &lt; 7</div>
    <div style="color:${{colors[2]}}">OPD → MDT: &lt; 10</div>
    <div style="color:${{colors[3]}}">MDT → Treatment: &lt; 20</div>
    <div style="color:${{colors[4]}}">Total Days: &lt; 43</div>
    `
    document.getElementById("benchmarks").innerHTML = html
}}

/* Chart */
function updateChart() {{

    let metric = document.getElementById("metric").value
    let mSel = getSelected(monthSelect)
    let cSel = getSelected(cancerSelect)

    let filtered = rawData.filter(r =>
        mSel.includes(r["Month"]) &&
        cSel.includes(r["Cancer Category"])
    )

    let results = []

    cSel.forEach(c => {{
        let obj = {{"Cancer Category": c}}

        parameters.forEach(p => {{
            let vals = filtered.filter(r=>r["Cancer Category"]===c).map(r=>r[p])
            obj[p] = +calculateMetric(vals, metric).toFixed(1)
        }})

        results.push(obj)
    }})

    /* MODERN COLOR PALETTE */
    let colors = ["#4F46E5","#EF4444","#10B981","#F59E0B","#6366F1"]

    let traces = parameters.map((p,i)=>({{
        y: results.map(r=>r["Cancer Category"]),
        x: results.map(r=>r[p]),
        name: p,
        type: "bar",
        orientation: "h",
        marker: {{
            color: colors[i],
            line: {{color:"white", width:1.5}}
        }},
        hovertemplate: "<b>%{{y}}</b><br>"+p+": %{{x}}<extra></extra>"
    }}))

    /* CUT-OFF LINES */
    let shapes = cutoffs.map(c => ({{
        type:"line",
        x0:c, x1:c,
        y0:-0.5,
        y1:results.length-0.5,
        line:{{color:"black", width:3, dash:"dot"}}
    }}))

    let layout = {{
        barmode:"group",
        title:metric+" by Cancer Category",
        height:600,
        shapes:shapes,
        plot_bgcolor:"#ffffff",
        paper_bgcolor:"#ffffff",
        xaxis:{{gridcolor:"#eee"}},
        yaxis:{{gridcolor:"#eee"}}
    }}

    Plotly.newPlot("chart", traces, layout)

    updateBenchmarks(colors)
    updateRunChart()
}}

/* Run Chart */
function updateRunChart() {{

    let mSel = getSelected(monthSelect)
    let cSel = getSelected(cancerSelect)

    let compliance = mSel.map(m => {{
        let rows = rawData.filter(r=>r["Month"]===m && cSel.includes(r["Cancer Category"]))
        if(rows.length===0) return 0
        let met = rows.filter(r=>r["Number of days"]<=42).length
        return +(met/rows.length*100).toFixed(1)
    }})

    Plotly.newPlot("runChart", [{{
        x:mSel,
        y:compliance,
        type:"scatter",
        mode:"lines+markers",
        line:{{color:"#EF4444", width:3}}
    }}], {{
        title:"Monthly Compliance Run Chart",
        yaxis:{{range:[0,100]}}
    }})
}}

document.getElementById("metric").addEventListener("change", updateChart)
monthSelect.addEventListener("change", updateChart)
cancerSelect.addEventListener("change", updateChart)

updateChart()

</script>

</body>
</html>
"""

    st.download_button("Download Dashboard", html, "oncology_dashboard.html")
