from flask import Flask, render_template, request, send_file
import matplotlib
matplotlib.use('Agg')
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import io
import base64
from matplotlib.figure import Figure

app = Flask(__name__)

df = pd.read_csv('data/accurate_quarterly_births_sp500.csv')
df['Year'] = df['Quarter'].str[:4].astype(int)
years = sorted(df['Year'].unique())

def create_plot():
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plot_url = base64.b64encode(buf.getvalue()).decode('utf8')
    plt.close()
    return plot_url

@app.route('/')
def home():
    return render_template('index.html', years=years)

@app.route('/download_csv')
def download_csv():
    start_year = int(request.args.get('start_year'))
    end_year = int(request.args.get('end_year'))
    
    mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
    filtered_df = df[mask]
    
    buf = io.StringIO()
    filtered_df.to_csv(buf, index=False)
    buf.seek(0)
    
    return send_file(
        io.BytesIO(buf.getvalue().encode('utf-8')),
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'birth_sp500_data_{start_year}_{end_year}.csv'
    )

@app.route('/analyze')
def analyze():
    start_year = int(request.args.get('start_year'))
    end_year = int(request.args.get('end_year'))
    
    mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
    filtered_df = df[mask]
    
    # Izveido dzimstību stabiņu diagrammu
    plt.figure(figsize=(12, 6))
    plt.bar(filtered_df['Quarter'], filtered_df['Estimated_Global_Births'])
    plt.title('Globālie Dzimstības Rādītāji pa Ceturkšņiem')
    plt.xlabel('Gads-Ceturksnis')
    plt.ylabel('Dzimstību Skaits')
    plt.xticks(rotation=45)
    plt.tight_layout()
    birth_chart = create_plot()
    
    # Izveido dzimstību histogrammu
    plt.figure(figsize=(12, 6))
    plt.hist(filtered_df['Estimated_Global_Births'], bins=15, edgecolor='black')
    plt.title('Globālais Dzimstību Sadalījums')
    plt.xlabel('Dzimstību Skaits')
    plt.ylabel('Biežums')
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    birth_hist = create_plot()
    
    # Izveido S&P500 returus grafiku
    plt.figure(figsize=(12, 6))
    plt.plot(filtered_df['Quarter'], filtered_df['S&P500_Quarterly_Return(%)'], marker='o')
    plt.title('S&P500 Ceturkšņa Ienesīgums')
    plt.xlabel('Gads-Ceturksnis')
    plt.ylabel('Ienesīgums (%)')
    plt.xticks(rotation=45)
    plt.grid(True)
    plt.tight_layout()
    sp500_chart = create_plot()
    
    # Aprēķina korelāciju
    correlation = filtered_df['Estimated_Global_Births'].corr(filtered_df['S&P500_Quarterly_Return(%)'])
    
    # Korelācijas scatter plot
    plt.figure(figsize=(12, 6))
    plt.scatter(filtered_df['Estimated_Global_Births'], filtered_df['S&P500_Quarterly_Return(%)'])
    
    # Korelācijas tendences līnija
    z = np.polyfit(filtered_df['Estimated_Global_Births'], filtered_df['S&P500_Quarterly_Return(%)'], 1)
    p = np.poly1d(z)
    plt.plot(filtered_df['Estimated_Global_Births'], p(filtered_df['Estimated_Global_Births']), 
             "r--", alpha=0.8, label='Tendences Līnija')
    
    plt.title('Korelācija starp Dzimstības Rādītājiem un S&P500 Ienesīgumu')
    plt.xlabel('Dzimstību Skaits')
    plt.ylabel('S&P500 Ienesīgums (%)')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    corr_chart = create_plot()
    
    if abs(correlation) < 0.2:
        corr_text = "Nav nozīmīgas korelācijas"
    elif correlation > 0:
        corr_text = "Pozitīva korelācija"
    else:
        corr_text = "Negatīva korelācija"
    
    corr_text += f" (korelācijas koeficients: {correlation:.2f})"
    
    return render_template(
        'analysis.html',
        birth_chart=birth_chart,
        birth_hist=birth_hist,
        sp500_chart=sp500_chart,
        corr_chart=corr_chart,
        correlation_text=corr_text
    )

if __name__ == '__main__':
    app.run(debug=True) 