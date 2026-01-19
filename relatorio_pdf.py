from fpdf import FPDF
import io

def gerar_pdf_relatorio(data):
    # Inicializa o PDF de forma simples para evitar erros de herança
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    
    # Função auxiliar para formatar valores com segurança total
    def fmt(val):
        try:
            if val is None or val == "" or val == "null":
                return "0.0000"
            return f"{float(val):.4f}"
        except:
            return "0.0000"

    # --- CABEÇALHO ESTILIZADO ---
    pdf.set_fill_color(31, 73, 125)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(0, 15, 'RELATÓRIO DO CICLO TERMODINÂMICO', 0, 1, 'C', True)
    pdf.ln(5)

    # --- SEÇÃO 1: INFORMAÇÕES GERAIS ---
    pdf.set_fill_color(220, 230, 241)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, ' 1. INFORMAÇÕES GERAIS', 0, 1, 'L', True)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 8, 'Tipo de Ciclo:', 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, str(data.get('tipo_ciclo', 'N/A')), 0, 1)
    
    pdf.set_font('Arial', '', 10)
    pdf.cell(50, 8, 'Fluido de Trabalho:', 0, 0)
    pdf.set_font('Arial', 'B', 10)
    pdf.cell(0, 8, str(data.get('fluido', 'Water')), 0, 1)
    pdf.ln(5)

    # --- SEÇÃO 2: RESULTADOS DO CICLO ---
    res = data.get("resultados_ciclo", {})
    pdf.set_fill_color(220, 230, 241)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, ' 2. RESULTADOS DO CICLO', 0, 1, 'L', True)
    pdf.ln(2)
    
    pdf.set_font('Arial', '', 10)
    col_w = 95
    pdf.cell(col_w, 8, f"Trabalho Turbina Total: {fmt(res.get('trabalho_turbina_total', 0))} kJ/kg", 0, 0)
    pdf.cell(col_w, 8, f"Trabalho Bomba Total: {fmt(res.get('trabalho_bomba_total', 0))} kJ/kg", 0, 1)
    
    pdf.cell(col_w, 8, f"Trabalho Compressor Total: {fmt(res.get('trabalho_compressor_total', 0))} kJ/kg", 0, 0)
    pdf.cell(col_w, 8, f"Calor Caldeira Total: {fmt(res.get('trabalho_caldeira_total', 0))} kJ/kg", 0, 1)
    
    q_reaq = float(res.get('trabalho_reaquecedor_total', 0) or 0)
    if q_reaq > 0:
        pdf.set_text_color(0, 102, 204)
        pdf.cell(col_w, 8, f"Calor Reaquecedor Total: {fmt(q_reaq)} kJ/kg", 0, 0)
        pdf.cell(col_w, 8, f"Calor Entrada Total: {fmt(res.get('calor_entrada_total', 0))} kJ/kg", 0, 1)
        pdf.set_text_color(0, 0, 0)
    
    pdf.ln(2)
    pdf.set_font('Arial', 'B', 11)
    pdf.set_fill_color(255, 255, 153)
    pdf.cell(0, 10, f" EFICIÊNCIA TÉRMICA DO CICLO: {res.get('eficiencia_ciclo', 'N/A')}%", 0, 1, 'L', True)
    pdf.ln(8)

    # --- SEÇÃO 3: DETALHES POR COMPONENTE ---
    pdf.set_fill_color(220, 230, 241)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, ' 3. DETALHES POR COMPONENTE', 0, 1, 'L', True)
    pdf.ln(2)

    for comp in data.get("components", []):
        pdf.set_font('Arial', 'B', 10)
        pdf.set_text_color(31, 73, 125)
        pdf.cell(0, 7, f" - {str(comp.get('id', 'N/A'))} [{str(comp.get('type', 'N/A')).upper()}]", 0, 1)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font('Arial', '', 9)
        
        c_type = comp.get("type")
        label, val = "", 0
        if c_type == "turbina": label, val = "Trabalho Produzido:", comp.get('trabalho_turbina', 0)
        elif c_type == "bomba": label, val = "Trabalho Consumido:", comp.get('trabalho_bomba', 0)
        elif c_type == "compressor": label, val = "Trabalho Consumido:", comp.get('trabalho_compressor', 0)
        elif c_type == "caldeira": label, val = "Calor Adicionado:", comp.get('trabalho_caldeira', 0)
        elif c_type == "reaquecedor": label, val = "Calor de Reaquecimento:", comp.get('trabalho_reaquecedor', 0)
        
        if label:
            pdf.cell(10)
            pdf.cell(50, 6, label, 0, 0)
            pdf.set_font('Arial', 'B', 9)
            pdf.cell(0, 6, f"{fmt(val)} kJ/kg", 0, 1)
        pdf.ln(1)

    # --- SEÇÃO 4: TABELA DE PROPRIEDADES ---
    pdf.ln(5)
    pdf.set_fill_color(220, 230, 241)
    pdf.set_font('Arial', 'B', 12)
    pdf.cell(0, 10, ' 4. PROPRIEDADES NOS PONTOS (PIFs)', 0, 1, 'L', True)
    pdf.ln(2)
    
    pdf.set_fill_color(31, 73, 125)
    pdf.set_text_color(255, 255, 255)
    pdf.set_font('Arial', 'B', 8)
    
    h = 8
    pdf.cell(15, h, "ID", 1, 0, 'C', True)
    pdf.cell(30, h, "Pressão (kPa)", 1, 0, 'C', True)
    pdf.cell(30, h, "Temp. (C)", 1, 0, 'C', True)
    pdf.cell(40, h, "Entalpia (kJ/kg)", 1, 0, 'C', True)
    pdf.cell(40, h, "Entropia (kJ/kg.K)", 1, 0, 'C', True)
    pdf.cell(35, h, "Título", 1, 1, 'C', True)

    pdf.set_text_color(0, 0, 0)
    pdf.set_font('Arial', '', 8)
    fill = False
    for p in data.get("pifs", []):
        if fill: pdf.set_fill_color(240, 240, 240)
        else: pdf.set_fill_color(255, 255, 255)
        
        pdf.cell(15, 7, str(p.get("id", "")), 1, 0, 'C', fill)
        pdf.cell(30, 7, str(p.get("pressao", "")), 1, 0, 'C', fill)
        pdf.cell(30, 7, str(p.get("temperatura", "")), 1, 0, 'C', fill)
        pdf.cell(40, 7, str(p.get("entalpia", "")), 1, 0, 'C', fill)
        pdf.cell(40, 7, str(p.get("entropia", "")), 1, 0, 'C', fill)
        pdf.cell(35, 7, str(p.get("titulo", "")), 1, 1, 'C', fill)
        fill = not fill

    # Geração do buffer de forma compatível com múltiplas versões do FPDF
    buffer = io.BytesIO()
    try:
        # Tenta obter como bytes diretamente (FPDF2)
        output = pdf.output(dest='S')
        if isinstance(output, str):
            output = output.encode('latin-1')
        buffer.write(output)
    except:
        # Fallback para métodos alternativos
        pdf_str = pdf.output(dest='S')
        buffer.write(pdf_str.encode('latin-1'))
        
    buffer.seek(0)
    return buffer
