from flask import Flask, render_template, request
import pyodbc
import os
from io import BytesIO
from datetime import date
import datetime
import pandas as pd


app = Flask(__name__)

server = 'AYTAC'
database = 'textile'
username = 'sa'
password = '1'
driver = '{ODBC Driver 17 for SQL Server}'

@app.route('/')
def login():
    return render_template('login.html', date=date)

@app.route('/results', methods=['POST'])
def show_results():
   
    start_date_str = request.form['start_date']
    end_date_str = request.form['end_date']

    
    start_date = datetime.datetime.strptime(start_date_str, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end_date_str, '%Y-%m-%d').date()
    end_date = end_date + datetime.timedelta(days=1)
    
    oya_start_date = start_date - datetime.timedelta(days=365)
    oya_end_date = end_date - datetime.timedelta(days=365)

    
    conn = pyodbc.connect('DRIVER=' + driver + ';SERVER=' + server + ';DATABASE=' + database + ';UID=' + username + ';PWD=' + password)
    cursor = conn.cursor()
    # Miktar sorgusu
    cursor.execute("SELECT SUM(qty1) from trInvoiceLine LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID WHERE IsReturn = 0  AND trInvoiceLine.CreatedDate BETWEEN ? AND ?", (start_date, end_date))
    fatura_miktari = cursor.fetchone()[0]
    
    # Fatura Adeti sorgusu
    
    cursor.execute("SELECT ROUND(COUNT(InvoiceNumber),0) AS FaturaAdeti FROM trInvoiceHeader WHERE IsReturn = 0 AND InvoiceDate BETWEEN ? AND ?", (start_date, end_date))
    fatura_adeti = cursor.fetchone()[0]

    # Geçen Sene Fatura Adeti sorgusu
    cursor.execute("SELECT ROUND(COUNT(InvoiceNumber),0) AS FaturaAdeti FROM trInvoiceHeader WHERE IsReturn = 0 AND InvoiceDate BETWEEN ? AND ?", (oya_start_date, oya_end_date))
    fatura_adeti_gy = cursor.fetchone()[0]

    # İade Fatura Adeti sorgusu
    cursor.execute("SELECT ROUND(COUNT(InvoiceNumber),0) AS IadeFaturaAdeti FROM trInvoiceHeader WHERE IsReturn = 1 AND InvoiceDate BETWEEN ? AND ?", (start_date, end_date))
    iade_fatura_adeti = cursor.fetchone()[0]

    # İade Fatura Tutari sorgusu
    cursor.execute("SELECT ROUND(SUM(qty1*price),0) AS Tutar from trInvoiceLine  LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID WHERE IsReturn = 1 AND trInvoiceLine.CreatedDate BETWEEN ? AND ?", (start_date, end_date))
    iade_fatura_tutari = cursor.fetchone()[0]

    # İade Fatura Miktari sorgusu
    cursor.execute("SELECT ROUND(SUM(qty1),0) AS ADET from trInvoiceLine  LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID WHERE IsReturn = 1 AND trInvoiceLine.CreatedDate BETWEEN ? AND ?", (start_date, end_date))
    iade_fatura_miktari = cursor.fetchone()[0]

    # Toplam Satış Adeti sorgusu
    cursor.execute("SELECT CAST( SUM(QTY1) as DECIMAL(15,0)) AS SatisAdet FROM trInvoiceLine LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID WHERE IsReturn = 0 AND trInvoiceLine.CreatedDate BETWEEN ? AND ?", (start_date, end_date))
    satis_adeti = cursor.fetchone()[0]

    # Toplam Magaza Sayisi sorgusu
    cursor.execute("SELECT ROUND(COUNT(DISTINCT WareHouseCode),0) AS DEPO from trInvoiceHeader WHERE InvoiceDate BETWEEN ? AND ?", (start_date, end_date))
    magaza_adeti = cursor.fetchone()[0]

    # Toplam Müşteri Sayısı sorgusu
    cursor.execute("SELECT ROUND(COUNT (CurrAccCode),0) AS CURRACCCODE from trInvoiceHeader WHERE InvoiceDate BETWEEN ? AND ?", (start_date, end_date))
    customer_count = cursor.fetchone()[0]

    # Cirovh sorgusu
    cursor.execute("SELECT ROUND(SUM(qty1*price),0) AS TUTAR from trInvoiceLine WHERE CreatedDate BETWEEN ? AND ?", (start_date, end_date))
    cirovh = cursor.fetchone()[0]

    # Cirovhgy sorgusu
    cursor.execute("SELECT ROUND(SUM(qty1*price),0) AS TUTAR from trInvoiceLine WHERE CreatedDate BETWEEN ? AND ?", (oya_start_date, oya_end_date))
    cirovhgy = cursor.fetchone()[0]

    
    
    # Grafik sorgusu
    
    cursor.execute("SELECT DISTINCT CurrAccDescription, SUM(trInvoiceLine.qty1*trInvoiceLine.price) AS TotalAmount "
                   "FROM trInvoiceLine "
                   "LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID "
                   "LEFT JOIN cdCurrAccDesc ON cdCurrAccDesc.CurrAccCode = trInvoiceHeader.CurrAccCode "
                   "WHERE CurrAccDescription IS NOT NULL AND trInvoiceLine.CreatedDate BETWEEN ? AND ? "
                   "GROUP BY trInvoiceHeader.CurrAccCode,cdCurrAccDesc.CurrAccDescription "
                   "ORDER BY TotalAmount DESC", (start_date, end_date))
    data = cursor.fetchall()
    
    
    curr_acc_codes = [row[0] for row in data]
    total_amounts = [row[1] for row in data]
    
    
    df = pd.DataFrame({'CurrAccCode': curr_acc_codes, 'TotalAmount': total_amounts})

     
    # Parantez işaretlerini kaldırmak için regex kullanımı
    #data = [re.sub(r'\([^)]*\)', '', code[0]) for code in curr_acc_codes]
    
    
    total_amount = df['TotalAmount'].sum()
    
    # CurrAccCode bazında oran hesaplama
    df['Percentage'] = ((df['TotalAmount'] / total_amount) * 100).round(2)


    
    chart_data = df[['CurrAccCode', 'Percentage']].to_dict(orient='records')





    
    # Grafik sorgusu2
    
    cursor.execute("SELECT DISTINCT TOP 5 ISNULL(cdItemAttributeDesc.AttributeDescription,space(0)) as CurrAccDescription, SUM(trInvoiceLine.qty1*trInvoiceLine.price) AS TotalAmount "
                   "FROM trInvoiceLine "
                   "LEFT JOIN trInvoiceHeader ON trInvoiceHeader.InvoiceHeaderID = trInvoiceLine.InvoiceHeaderID "
                   "LEFT JOIN cdCurrAccDesc ON cdCurrAccDesc.CurrAccCode = trInvoiceHeader.CurrAccCode "
                   "LEFT JOIN prItemAttribute ON prItemAttribute.ItemCode=trInvoiceLine.ItemCode "
                   "LEFT JOIN cdItemAttributeDesc ON  cdItemAttributeDesc.AttributeTypeCode=prItemAttribute.AttributeTypeCode AND cdItemAttributeDesc.AttributeCode=prItemAttribute.AttributeCode "
                   "WHERE trInvoiceLine.CreatedDate BETWEEN ? AND ? " 
                   "GROUP BY trInvoiceHeader.CurrAccCode,cdItemAttributeDesc.AttributeDescription "
                   "ORDER BY TotalAmount DESC", (start_date, end_date))
    data = cursor.fetchall()
    
    
    curr_acc_codes = [row[0] for row in data]
    total_amounts = [row[1] for row in data]
    
    
    df = pd.DataFrame({'CurrAccCode': curr_acc_codes, 'TotalAmount': total_amounts})

     
    # Parantez işaretlerini kaldırmak için regex kullanımı
    #data = [re.sub(r'\([^)]*\)', '', code[0]) for code in curr_acc_codes]
    
    # Toplam TotalAmount
    total_amount = df['TotalAmount'].sum()
    
    
    df['Percentage'] = ((df['TotalAmount'] / total_amount) * 100).round(2)


    
    chart_data2 = df[['CurrAccCode', 'Percentage']].to_dict(orient='records')





    
    conn.close()

    
    return render_template('results.html', fatura_miktari=fatura_miktari,fatura_adeti=fatura_adeti,fatura_adeti_gy=fatura_adeti_gy, iade_fatura_adeti=iade_fatura_adeti,iade_fatura_tutari=iade_fatura_tutari,iade_fatura_miktari=iade_fatura_miktari, satis_adeti=satis_adeti, magaza_adeti=magaza_adeti, customer_count=customer_count, cirovh=cirovh,cirovhgy=cirovhgy, chart_data=chart_data,chart_data2=chart_data2)

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000)
