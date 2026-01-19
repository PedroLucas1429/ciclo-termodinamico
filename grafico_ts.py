import matplotlib.pyplot as plt
import numpy as np
from CoolProp.CoolProp import PropsSI
import io

def gerar_grafico_ts(circuito_data):
    """
    Gera um gráfico T-s (Temperatura x Entropia) para o Ciclo de Rankine.
    Inclui curva de saturação e linhas isobáricas (pressão constante).
    """
    tipo_ciclo = circuito_data.get("tipo_ciclo", "Rankine")
    if tipo_ciclo != "Rankine":
        return None
    
    fluido = circuito_data.get("fluido", "Water")
    pifs = circuito_data.get("pifs", [])
    
    # Extrair dados dos PIFs
    s_pontos = []
    t_pontos = []
    p_pontos = []
    
    # Mapear PIFs para ordenação
    pif_map = {(p["from"], p["to"]): p for p in pifs}
    conexoes = circuito_data.get("connections", [])
    
    if not conexoes:
        return None
        
    sequencia_pifs = []
    try:
        atual = conexoes[0]
        visitados = set()
        while atual and tuple(atual) not in visitados:
            visitados.add(tuple(atual))
            pif = pif_map.get(tuple(atual))
            if pif:
                sequencia_pifs.append(pif)
            proximo = next((c for c in conexoes if c[0] == atual[1]), None)
            if not proximo or tuple(proximo) in visitados:
                break
            atual = proximo
    except:
        sequencia_pifs = pifs

    for pif in sequencia_pifs:
        s = pif.get("entropia")
        t = pif.get("temperatura")
        p = pif.get("pressao")
        if s is not None and t is not None and s != "" and t != "":
            s_pontos.append(float(s))
            t_pontos.append(float(t))
            if p: p_pontos.append(float(p))
    
    if len(s_pontos) < 2:
        return None

    # Criar o gráfico
    plt.figure(figsize=(10, 8))
    
    try:
        # 1. Curva de Saturação
        t_crit = PropsSI("T_critical", fluido)
        t_min_ciclo = min(t_pontos)
        t_min_plot = max(273.16, (t_min_ciclo - 20) + 273.15)
        t_range_sat = np.linspace(t_min_plot, t_crit - 0.01, 150)
        
        s_liq = [PropsSI("S", "T", t, "Q", 0, fluido) / 1000 for t in t_range_sat]
        s_vap = [PropsSI("S", "T", t, "Q", 1, fluido) / 1000 for t in t_range_sat]
        
        plt.plot(s_liq, [t - 273.15 for t in t_range_sat], 'k-', linewidth=1.5, label="Curva de Saturação")
        plt.plot(s_vap, [t - 273.15 for t in t_range_sat], 'k-', linewidth=1.5)
        
        # 2. Linhas Isobáricas (Pressão Constante)
        # Identificar pressões únicas (geralmente alta e baixa)
        pressões_unicas = sorted(list(set([round(p, 2) for p in p_pontos])))
        
        s_min_plot = min(s_pontos) - 0.5
        s_max_plot = max(s_pontos) + 0.5
        s_range_iso = np.linspace(s_min_plot, s_max_plot, 100)
        
        colors = ['blue', 'green', 'orange', 'purple']
        for i, p_kpa in enumerate(pressões_unicas):
            p_pa = p_kpa * 1000
            t_iso = []
            s_iso_valid = []
            
            for s_val in s_range_iso:
                try:
                    # T = f(P, s)
                    temp = PropsSI("T", "P", p_pa, "S", s_val * 1000, fluido) - 273.15
                    if temp < (t_crit - 273.15 + 100): # Limite razoável
                        t_iso.append(temp)
                        s_iso_valid.append(s_val)
                except:
                    continue
            
            if t_iso:
                color = colors[i % len(colors)]
                plt.plot(s_iso_valid, t_iso, ':', color=color, alpha=0.6, label=f"P = {p_kpa} kPa")

    except Exception as e:
        print(f"Erro na plotagem técnica: {e}")
    
    # 3. Ciclo Rankine
    s_plot = s_pontos + [s_pontos[0]]
    t_plot = t_pontos + [t_pontos[0]]
    plt.plot(s_plot, t_plot, 'ro-', linewidth=2.5, markersize=8, label="Ciclo Rankine")
    
    # Numerar pontos
    for i, (s, t) in enumerate(zip(s_pontos, t_pontos)):
        plt.annotate(f"P{i+1}", (s, t), textcoords="offset points", xytext=(5,5), 
                     ha='left', fontweight='bold', color='darkred', fontsize=10)

    plt.xlabel("Entropia (kJ/kg.K)", fontsize=12)
    plt.ylabel("Temperatura (°C)", fontsize=12)
    plt.title(f"Diagrama T-s Técnico - Ciclo {tipo_ciclo}", fontsize=14)
    plt.grid(True, which='both', linestyle='--', alpha=0.3)
    plt.legend(loc='upper left', fontsize=9)
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight', dpi=150)
    buf.seek(0)
    plt.close()
    return buf
