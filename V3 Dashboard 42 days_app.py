import streamlit as st
import pandas as pd
import json

st.set_page_config(page_title="Oncology Dashboard SKMCH & RC", layout="wide")

st.markdown("""
<style>
.stApp { background-color:#f5f7fb; }

h1 { font-family: Arial; font-weight:700; }

/* Upload box */
.upload-box {
    background:white;
    padding:25px;
    border-radius:10px;
    box-shadow:0px 3px 10px rgba(0,0,0,0.1);
}

/* 🔥 SINGLE ROW FILTER LAYOUT */
.filters {
    display: flex;
    flex-wrap: nowrap;
    gap: 20px;
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
    align-items: flex-start;
    overflow-x: auto;
}

/* Filter box */
.filter-box {
    display: flex;
    flex-direction: column;
    font-size: 14px;
}

/* Benchmark box */
.benchmark-box {
    background: #ffffff;
    padding: 15px 20px;
    border-radius: 10px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.15);
    font-size: 13px;
    line-height: 1.6;
    min-width: 280px;
}

/* Chart containers */
#chart, #runChart {
    margin-top: 30px;
    background: white;
    padding: 20px;
    border-radius: 10px;
    box-shadow: 0px 3px 10px rgba(0,0,0,0.08);
}

footer {
    text-align:center;
    margin-top:40px;
    font-size:12px;
    color:gray;
}
</style>
""", unsafe_allow_html=True)

st.title("Oncology Dashboard SKMCH & RC")

st.markdown('<div class="upload-box">', unsafe_allow_html=True)
uploaded_file = st.file_uploader("Upload Excel File", type=["xlsx"])
st.markdown('</div>', unsafe_allow_html=True)

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

    months = sorted(df[month_col].dropna().unique(), key=lambda x: pd.to_datetime(x, errors="coerce"))
    cancers = sorted(df[cancer_col].dropna().unique())

    html = f"""
<!DOCTYPE html>
<html>
<head>
<title>Oncology Dashboard</title>
<script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>

<style>
body {{
    font-family: Arial;
    background:#f5f7fb;
    margin:0;
}}

.header {{
    background:#ffffff;
    padding:20px 40px;
    box-shadow:0 2px 6px rgba(0,0,0,0.1);
}}

.container {{
    padding:30px 40px;
}}

select {{
    padding:8px;
    border-radius:6px;
    border:1px solid #ccc;
    min-width:180px;
}}

label {{
    font-weight:bold;
    margin-bottom:5px;
}}

</style>
</head>

<body>

<div class="header">
<h1>Oncology Dashboard</h1>
</div>

<div class="container">

<div class="filters">

<!-- Metric -->
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

<!-- Month -->
<div class="filter-box">
<label>Month</label>
<select id="month" multiple></select>
</div>

<!-- Cancer -->
<div class="filter-box">
<label>Cancer Category</label>
<select id="cancer" multiple></select>
</div>

<!-- Benchmark -->
<div class="benchmark-box">
<strong>Benchmarks:</strong><br><br>

<span style="color:#1f77b4;">1st visit - WIC acceptance: &lt; 15</span><br>
<span style="color:#ff7f0e;">WIC acceptance - 1st OPD visit: &lt; 7</span><br>
<span style="color:#2ca02c;">1st OPD visit - MDT: &lt; 10</span><br>
<span style="color:#d62728;">MDT - 1st day of treatment: &lt; 20</span><br>
<span style="color:#9467bd;">Number of days: &lt; 43</span>

</div>

</div>

<div id="chart"></div>
<div id="runChart"></div>

</div>

<script>

let rawData = {json.dumps(data_json)};
let months = {json.dumps(months)};
let cancers = {json.dumps(cancers)};
let parameters = {json.dumps(parameter_cols)};

let monthSelect = document.getElementById("month");
let cancerSelect = document.getElementById("cancer");

/* Populate Month */
months.forEach(m => {{
    let opt = document.createElement("option");
    opt.value = m;
    opt.text = m;
    opt.selected = true;
    monthSelect.appendChild(opt);
}});

/* Populate Cancer */
cancers.forEach((c, i) => {{
    let opt = document.createElement("option");
    opt.value = c;
    opt.text = c;
    if(i === 0) opt.selected = true;
    cancerSelect.appendChild(opt);
}});

function getSelected(select) {{
    return Array.from(select.selectedOptions).map(o => o.value);
}}

function calculateMetric(values, metric) {{
    values = values.filter(v => v !== null && !isNaN(v));
    if(values.length === 0) return 0;

    if(metric === "Mean") return values.reduce((a,b)=>a+b,0)/values.length;

    if(metric === "Median") {{
        values.sort((a,b)=>a-b);
        let mid = Math.floor(values.length/2);
        return values.length%2 ? values[mid] : (values[mid-1]+values[mid])/2;
    }}

    if(metric === "SD") {{
        let mean = values.reduce((a,b)=>a+b,0)/values.length;
        let variance = values.reduce((a,b)=>a+(b-mean)**2,0)/(values.length-1);
        return Math.sqrt(variance);
    }}

    if(metric === "Maximum") return Math.max(...values);
    if(metric === "Minimum") return Math.min(...values);
}}

function updateChart() {{
    let metric = document.getElementById("metric").value;
    let monthsSelected = getSelected(monthSelect);
    let cancerSelected = getSelected(cancerSelect);

    let filtered = rawData.filter(r =>
        monthsSelected.includes(r["Month"]) &&
        cancerSelected.includes(r["Cancer Category"])
    );

    let results = [];

    cancerSelected.forEach(cancer => {{
        let obj = {{}};
        obj["Cancer Category"] = cancer;

        parameters.forEach(p => {{
            let vals = filtered
                .filter(r => r["Cancer Category"] === cancer)
                .map(r => r[p]);

            obj[p] = Number(calculateMetric(vals, metric).toFixed(1));
        }});

        results.push(obj);
    }});

    let traces = parameters.map(p => ({{
        y: results.map(r => r["Cancer Category"]),
        x: results.map(r => r[p]),
        name: p,
        type: "bar",
        orientation: "h",
        text: results.map(r => r[p]),
        textposition: "auto"
    }}));

    let layout = {{
        barmode: "group",
        height: 600,
        title: metric + " by Cancer Category",
        xaxis: {{
            range: metric === "Maximum" ? [0, 550] :
                   (["Mean","Median","SD","Minimum"].includes(metric) ? [0,150] : null)
        }}
    }};

    Plotly.newPlot("chart", traces, layout);
    updateRunChart();
}}

function updateRunChart() {{
    let monthsSelected = getSelected(monthSelect);
    let cancerSelected = getSelected(cancerSelect);

    let monthlyCompliance = monthsSelected.map(m => {{
        let rows = rawData.filter(r =>
            r["Month"] === m &&
            cancerSelected.includes(r["Cancer Category"])
        );

        if(rows.length === 0) return 0;

        let met = rows.filter(r => r["Number of days"] <= 42).length;
        return +(met / rows.length * 100).toFixed(1);
    }});

    Plotly.newPlot("runChart", [{
        x: monthsSelected,
        y: monthlyCompliance,
        type: "scatter",
        mode: "lines+markers",
        line: {{color:"#FF5733", width:3}},
        marker: {{size:8}}
    }], {{
        title: "Monthly Compliance Run Chart",
        height: 400,
        yaxis: {{range:[0,100], title:"Compliance (%)"}},
        xaxis: {{title:"Month"}}
    }});
}}

document.getElementById("metric").addEventListener("change", updateChart);
monthSelect.addEventListener("change", updateChart);
cancerSelect.addEventListener("change", updateChart);

updateChart();

</script>

</body>
</html>
"""

    st.success("Dashboard ready for download")

    st.download_button(
        "Download Interactive Dashboard",
        html,
        file_name="oncology_dashboard.html",
        mime="text/html"
    )
