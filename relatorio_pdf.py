from fpdf import FPDF
import io

def gerar_pdf_relatorio(circuito_data):
    tipo_ciclo = circuito_data.get("tipo_ciclo", "Rankine")
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, f"Relatório de Cálculo do Ciclo {tipo_ciclo}", 0, 1, "C")
    pdf.ln(5)
    
    # 1. Resultados Globais
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "1. Resultados Globais do Ciclo", 0, 1, "L")
    pdf.set_font("Arial", "", 10)
    
    resultados_ciclo = circuito_data.get("resultados_ciclo", {})
    col_width = 50
    line_height = 8
    pdf.set_fill_color(200, 220, 255)
    pdf.set_font("Arial", "B", 10)
    pdf.cell(col_width, line_height, "Métrica", 1, 0, "C", 1)
    pdf.cell(col_width, line_height, "Valor", 1, 0, "C", 1)
    pdf.cell(col_width, line_height, "Unidade", 1, 1, "C", 1)
    
    pdf.set_font("Arial", "", 10)
    
    metrics = [
        ("Trabalho Total da Turbina", resultados_ciclo.get("trabalho_turbina_total"), "kJ/kg"),
        ("Trabalho Total da Bomba", resultados_ciclo.get("trabalho_bomba_total"), "kJ/kg"),
        ("Trabalho Total Compressor", resultados_ciclo.get("trabalho_compressor_total"), "kJ/kg"),
        ("Calor Total da Caldeira", resultados_ciclo.get("trabalho_caldeira_total"), "kJ/kg"),
        ("Eficiência do Ciclo", resultados_ciclo.get("eficiencia_ciclo"), "%")
    ]
    
    for label, value, unit in metrics:
        if value is not None and value != 0 or "Eficiência" in label:
            pdf.cell(col_width, line_height, label, 1, 0, "L")
            pdf.cell(col_width, line_height, f"{value:.4f}" if value is not None else "N/A", 1, 0, "R")
            pdf.cell(col_width, line_height, unit, 1, 1, "C")
        
    pdf.ln(5)
    
    # 2. PIFs
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "2. Propriedades nos Pontos de Fluxo (PIFs)", 0, 1, "L")
    pifs = circuito_data.get("pifs", [])
    col_widths_pif = [30, 25, 25, 25, 25, 25]
    pdf.set_fill_color(220, 230, 255)
    pdf.set_font("Arial", "B", 8)
    headers = ["PIF", "Pressão (kPa)", "Temp. (°C)", "Entalpia (kJ/kg)", "Entropia (kJ/kg.K)", "Título (Q)"]
    for i, h in enumerate(headers):
        pdf.cell(col_widths_pif[i], 7, h, 1, 0 if i < len(headers)-1 else 1, "C", 1)
    
    pdf.set_font("Arial", "", 8)
    for pif in pifs:
        def f(v):
            if v is None or v in ["", "null"]: return "N/A"
            return f"{float(v):.4f}"
        pdf.cell(col_widths_pif[0], 7, f"{pif.get('from')} -> {pif.get('to')}", 1, 0, "L")
        pdf.cell(col_widths_pif[1], 7, f(pif.get("pressao")), 1, 0, "R")
        pdf.cell(col_widths_pif[2], 7, f(pif.get("temperatura")), 1, 0, "R")
        pdf.cell(col_widths_pif[3], 7, f(pif.get("entalpia")), 1, 0, "R")
        pdf.cell(col_widths_pif[4], 7, f(pif.get("entropia")), 1, 0, "R")
        pdf.cell(col_widths_pif[5], 7, f(pif.get("titulo")), 1, 1, "R")
        
    pdf.ln(5)
    
    # 3. Componentes
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "3. Trabalhos e Calores dos Componentes", 0, 1, "L")
    componentes = circuito_data.get("components", [])
    col_widths_comp = [40, 30, 30, 30, 30]
    pdf.set_fill_color(255, 230, 220)
    pdf.set_font("Arial", "B", 9)
    headers_comp = ["ID", "Tipo", "Trab. Bomba", "Trab. Turbina", "Calor Caldeira"]
    for i, h in enumerate(headers_comp):
        pdf.cell(col_widths_comp[i], 7, h, 1, 0 if i < len(headers_comp)-1 else 1, "C", 1)
    
    pdf.set_font("Arial", "", 9)
    for comp in componentes:
        def f(v): return f"{float(v):.4f}" if v is not None else "N/A"
        pdf.cell(col_widths_comp[0], 7, comp.get("id"), 1, 0, "L")
        pdf.cell(col_widths_comp[1], 7, comp.get("type"), 1, 0, "C")
        pdf.cell(col_widths_comp[2], 7, f(comp.get("trabalho_bomba") or comp.get("trabalho_compressor")), 1, 0, "R")
        pdf.cell(col_widths_comp[3], 7, f(comp.get("trabalho_turbina")), 1, 0, "R")
        pdf.cell(col_widths_comp[4], 7, f(comp.get("trabalho_caldeira")), 1, 1, "R")
        
    return io.BytesIO(pdf.output(dest='S'))
