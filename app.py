import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from io import BytesIO
import base64
from openai import OpenAI
import json

# ==================== Page Configuration ====================
st.set_page_config(
    page_title="AI Data Visualization Tool",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==================== Custom CSS ====================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        background: linear-gradient(120deg, #1f77b4, #17becf);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(120deg, #1f77b4, #17becf);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.6rem 1rem;
        font-weight: 600;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(31, 119, 180, 0.3);
    }
    .insight-box {
        background: linear-gradient(135deg, #f0f8ff 0%, #e6f3ff 100%);
        border-left: 5px solid #1f77b4;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 1rem 0;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==================== Initialization ====================
if 'df' not in st.session_state:
    st.session_state.df = None
if 'insights' not in st.session_state:
    st.session_state.insights = None
if 'charts' not in st.session_state:
    st.session_state.charts = []

# ==================== Color Themes ====================
COLOR_THEMES = {
    "Blue": px.colors.sequential.Blues,
    "Green": px.colors.sequential.Greens,
    "Purple": px.colors.sequential.Purples,
    "Orange": px.colors.sequential.Oranges,
    "Pink": px.colors.sequential.RdPu,
    "Business": ["#2E4057", "#048A81", "#54C6EB", "#8FC93A", "#E4B363"],
    "Modern": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8"]
}

# ==================== Core Functions ====================

def load_data(file):
    """Load data file"""
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8')
        elif file.name.endswith(('.xlsx', '.xls')):
            df = pd.read_excel(file)
        else:
            st.error("❌ Unsupported format! Please upload CSV or Excel.")
            return None
        return df
    except UnicodeDecodeError:
        try:
            df = pd.read_csv(file, encoding='gbk')
            return df
        except:
            st.error("❌ File encoding error")
            return None
    except Exception as e:
        st.error(f"❌ Reading error: {str(e)}")
        return None

def generate_ai_insights(df, api_key):
    """Generate AI insights"""
    try:
        client = OpenAI(api_key=api_key)
        
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        summary = {
            "shape": f"{df.shape[0]} rows × {df.shape[1]} columns",
            "columns": df.columns.tolist()[:10],
            "numeric": numeric_cols[:5],
            "sample": df.head(3).to_dict('records')
        }
        
        prompt = f"""Analyze this dataset and provide insights:

Data: {json.dumps(summary, ensure_ascii=False)}

Please provide:
1. Data Overview (2-3 sentences)
2. 3 Key Findings
3. Recommended Chart Types
4. 2 Actionable Recommendations

Be concise and professional, use bullet points."""
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a data analysis expert."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        return response.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error: {str(e)}\n\nPlease check API Key and network connection."

def create_chart(df, chart_type, x_col, y_col, color_theme, title=""):
    """Create chart"""
    colors = COLOR_THEMES[color_theme]
    
    try:
        if chart_type == "Line Chart":
            fig = px.line(df, x=x_col, y=y_col, title=title, 
                         color_discrete_sequence=colors, markers=True)
        elif chart_type == "Bar Chart":
            fig = px.bar(df, x=x_col, y=y_col, title=title,
                        color_discrete_sequence=colors)
        elif chart_type == "Pie Chart":
            # Aggregate data for pie chart if needed
            if pd.api.types.is_numeric_dtype(df[y_col]):
                pie_data = df.groupby(x_col)[y_col].sum().reset_index()
                fig = px.pie(pie_data, names=x_col, values=y_col, title=title,
                            color_discrete_sequence=colors)
            else:
                st.warning("⚠️ Pie chart requires numeric Y-axis. Showing value counts.")
                pie_data = df[x_col].value_counts().reset_index()
                pie_data.columns = [x_col, 'count']
                fig = px.pie(pie_data, names=x_col, values='count', title=title,
                            color_discrete_sequence=colors)
        elif chart_type == "Scatter Plot":
            fig = px.scatter(df, x=x_col, y=y_col, title=title,
                           color_discrete_sequence=colors)
        elif chart_type == "Area Chart":
            fig = px.area(df, x=x_col, y=y_col, title=title,
                         color_discrete_sequence=colors)
        else:
            return None
        
        fig.update_layout(
            template="plotly_white",
            font=dict(size=12),
            height=450,
            margin=dict(l=50, r=50, t=80, b=50),
            hovermode='x unified'
        )
        
        return fig
    except Exception as e:
        st.error(f"❌ Chart error: {str(e)}")
        return None

# ==================== Main Interface ====================

st.markdown('<h1 class="main-header">📊 AI Data Visualization Tool</h1>', unsafe_allow_html=True)
st.markdown("<p style='text-align: center; color: #666;'>Quickly convert Excel/CSV into professional reports</p>", unsafe_allow_html=True)
st.markdown("---")

# ==================== Sidebar ====================
with st.sidebar:
    st.header("⚙️ Settings")
    
    # API Key
    openai_api_key = st.text_input(
        "OpenAI API Key",
        type="password",
        help="Enter API Key to enable AI features"
    )
    
    if openai_api_key:
        st.success("✅ API Configured")
    else:
        st.info("💡 Configure API Key to use AI analysis")
    
    st.markdown("---")
    
    # Theme selection
    color_theme = st.selectbox("🎨 Color Theme", list(COLOR_THEMES.keys()))
    
    st.markdown("---")
    st.markdown("### 📖 Usage Steps")
    st.markdown("""
    1. Upload data file
    2. Generate AI insights
    3. Create charts
    4. Export reports
    """)
    
    st.markdown("---")
    st.markdown("Made with ❤️ by DataViz Agent")

# ==================== Main Content Area ====================
tab1, tab2, tab3 = st.tabs(["📤 Upload Data", "📊 Create Charts", "📥 Export Reports"])

# TAB 1: Upload Data
with tab1:
    st.header("📤 Upload Data File")
    
    uploaded_file = st.file_uploader(
        "Choose CSV or Excel file",
        type=['csv', 'xlsx', 'xls'],
        help="Supports .csv, .xlsx, .xls formats"
    )
    
    if uploaded_file:
        df = load_data(uploaded_file)
        if df is not None:
            st.session_state.df = df
            st.success(f"✅ Successfully loaded! {len(df)} rows × {len(df.columns)} columns")
            
            # Data preview
            st.subheader("📋 Data Preview")
            st.dataframe(df.head(10), use_container_width=True)
            
            # Statistical summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Rows", f"{len(df):,}")
            with col2:
                st.metric("Total Columns", len(df.columns))
            with col3:
                numeric_count = len(df.select_dtypes(include=['number']).columns)
                st.metric("Numeric Fields", numeric_count)
            
            # Descriptive statistics
            if len(df.select_dtypes(include=['number']).columns) > 0:
                st.subheader("📊 Statistical Summary")
                st.dataframe(df.describe(), use_container_width=True)
            
            # AI Insights
            st.markdown("---")
            if openai_api_key:
                if st.button("🤖 Generate AI Insights", type="primary", use_container_width=True):
                    with st.spinner("AI analyzing..."):
                        insights = generate_ai_insights(df, openai_api_key)
                        st.session_state.insights = insights
            else:
                st.info("💡 Enter OpenAI API Key to use AI insights feature")
            
            # Display insights
            if st.session_state.insights:
                st.markdown('<div class="insight-box">', unsafe_allow_html=True)
                st.markdown("### 🧠 AI Data Insights")
                st.markdown(st.session_state.insights)
                st.markdown('</div>', unsafe_allow_html=True)

# TAB 2: Create Charts
with tab2:
    if st.session_state.df is not None:
        df = st.session_state.df
        
        st.header("📊 Create Visualization Charts")
        
        col1, col2 = st.columns(2)
        with col1:
            chart_type = st.selectbox(
                "Chart Type",
                ["Bar Chart", "Line Chart", "Pie Chart", "Scatter Plot", "Area Chart"]
            )
        with col2:
            chart_title = st.text_input("Chart Title", f"{chart_type} Analysis")
        
        # Select fields
        all_cols = df.columns.tolist()
        numeric_cols = df.select_dtypes(include=['number']).columns.tolist()
        
        col1, col2 = st.columns(2)
        with col1:
            x_col = st.selectbox("X Axis", all_cols)
        with col2:
            y_col = st.selectbox("Y Axis", numeric_cols if numeric_cols else all_cols)
        
        # Generate chart
        if st.button("🎨 Generate Chart", type="primary", use_container_width=True):
            fig = create_chart(df, chart_type, x_col, y_col, color_theme, chart_title)
            if fig:
                st.plotly_chart(fig, use_container_width=True)
                st.session_state.charts.append({
                    'fig': fig,
                    'title': chart_title,
                    'type': chart_type
                })
                st.success("✅ Chart generated!")
        
        # Display generated charts
        if st.session_state.charts:
            st.markdown("---")
            st.subheader(f"📊 Generated {len(st.session_state.charts)} Chart(s)")
            for idx, chart in enumerate(st.session_state.charts):
                with st.expander(f"Chart {idx + 1}: {chart['title']}"):
                    st.plotly_chart(chart['fig'], use_container_width=True)
    else:
        st.info("👈 Please upload file in 'Upload Data' tab first")

# TAB 3: Export Reports
with tab3:
    if st.session_state.df is not None:
        st.header("📥 Export Reports")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Export Data")
            csv = st.session_state.df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Download CSV",
                data=csv,
                file_name="data_report.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            st.subheader("📈 Export Charts")
            if st.session_state.charts:
                st.write(f"Total {len(st.session_state.charts)} chart(s)")
                for idx, chart in enumerate(st.session_state.charts):
                    try:
                        img_bytes = chart['fig'].to_image(format="png", width=1200, height=800)
                        st.download_button(
                            label=f"📥 Chart {idx + 1}",
                            data=img_bytes,
                            file_name=f"chart_{idx + 1}.png",
                            mime="image/png",
                            use_container_width=True,
                            key=f"download_{idx}"
                        )
                    except:
                        st.info(f"Chart {idx + 1}: Use Plotly's camera icon 📷 in top right")
            else:
                st.info("No charts generated yet")
        
        # HTML Report
        st.markdown("---")
        st.subheader("📄 Complete HTML Report")
        
        if st.button("📑 Generate HTML Report", use_container_width=True):
            html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>Data Analysis Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; background: #f5f5f5; }}
                    .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 40px; border-radius: 10px; }}
                    h1 {{ color: #1f77b4; border-bottom: 3px solid #1f77b4; padding-bottom: 10px; }}
                    .insight {{ background: #f0f8ff; padding: 20px; border-left: 5px solid #1f77b4; margin: 20px 0; border-radius: 5px; }}
                    .stats {{ display: flex; gap: 20px; margin: 20px 0; }}
                    .stat-box {{ flex: 1; background: #e8f4f8; padding: 15px; border-radius: 8px; text-align: center; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>📊 Data Analysis Report</h1>
                    <p><strong>Generated:</strong> {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    
                    <h2>Data Overview</h2>
                    <div class="stats">
                        <div class="stat-box"><h3>{len(st.session_state.df):,}</h3><p>Total Rows</p></div>
                        <div class="stat-box"><h3>{len(st.session_state.df.columns)}</h3><p>Total Columns</p></div>
                        <div class="stat-box"><h3>{len(st.session_state.charts)}</h3><p>Charts Generated</p></div>
                    </div>
                    
                    {'<div class="insight"><h2>🧠 AI Insights</h2><pre>' + st.session_state.insights + '</pre></div>' if st.session_state.insights else ''}
                    
                    <h2>Data Details</h2>
                    <p><strong>Columns:</strong> {', '.join(st.session_state.df.columns.tolist())}</p>
                    
                    <p style="text-align: center; margin-top: 40px; color: #888;">
                        <small>Auto-generated by DataViz Agent</small>
                    </p>
                </div>
            </body>
            </html>
            """
            
            st.download_button(
                label="💾 Download HTML Report",
                data=html,
                file_name="report.html",
                mime="text/html",
                use_container_width=True
            )
            st.success("✅ HTML report is ready for download!")
    else:
        st.info("👈 Please upload data and generate charts first")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #888; padding: 20px;'>
    <p><strong>📊 AI Data Visualization Tool</strong></p>
    <p>Fast • Intelligent • Professional</p>
</div>
""", unsafe_allow_html=True)