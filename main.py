from flask import Flask, render_template, request, jsonify, send_file
import networkx as nx
import threading
import webbrowser
from relatorio_pdf import gerar_pdf_relatorio
from regras_calculo import RegraCalculoBomba, RegraCalculoCompressor, RegraCalculoTurbina, RegraPropagacaoEntropia, RegraPropagacaoPressao, CalculadoraPropriedadesTermodinamicas

class Circuito:
    def __init__(self, data, fluido="Water", densidade=1000.0):
        self.data = data
        self.components = data.get("components", [])
        self.connections = data.get("connections", [])
        self.pifs = data.get("pifs", [])
        
        # Detecção do tipo de ciclo
        self.tipo_ciclo = self._detectar_tipo_ciclo()
        self.data["tipo_ciclo"] = self.tipo_ciclo
        
        # Se for Brayton, o fluido padrão deve ser Ar (Air)
        if self.tipo_ciclo == "Brayton":
            self.fluido = "Air"
        else:
            self.fluido = fluido
            
        self.densidade = densidade
        self.graph = self._build_graph()
        self.pifs_in, self.pifs_out = self._index_pifs()
        self.calculadora = CalculadoraPropriedadesTermodinamicas(self.fluido)
        
        # Configuração de regras
        # Herança de pressão nos trocadores de calor (caldeira, condesador, reaquecedor, TrocadorDeCalor)
        self.regras_passo1 = [RegraPropagacaoPressao(['caldeira', 'condensador', 'reaquecedor', 'TrocadorDeCalor'])]
        
        # No ciclo Brayton, a entropia não é propagada da mesma forma se usarmos a fórmula de gás ideal
        self.regras_passo3 = [RegraPropagacaoEntropia(['turbina', 'compressor'])]
        
        self.regras_passo_bomba = [RegraCalculoBomba(['bomba'], densidade)]
        
        # Regra específica para o compressor no ciclo Brayton
        self.regras_passo_compressor = [RegraCalculoCompressor(['compressor'], self.fluido)]
        
        # Regra específica para a turbina no ciclo Brayton
        self.regras_passo_turbina = [RegraCalculoTurbina(['turbina'], self.fluido)]

    def _detectar_tipo_ciclo(self):
        tipos = [c["type"] for c in self.components]
        # Se houver compressor, identificamos como Brayton
        if "compressor" in tipos:
            return "Brayton"
        return "Rankine"

    def _build_graph(self):
        G = nx.DiGraph()
        for comp in self.components: G.add_node(comp["id"], tipo=comp["type"])
        for a, b in self.connections: G.add_edge(a, b)
        return G

    def _index_pifs(self):
        pifs_in, pifs_out = {}, {}
        for p in self.pifs:
            pifs_out.setdefault(p["from"], []).append(p)
            pifs_in.setdefault(p["to"], []).append(p)
        return pifs_in, pifs_out

    def _calcular_eficiencia_ciclo(self):
        w_turbina_total = sum(c.get("trabalho_turbina", 0) for c in self.components)
        w_bomba_total = sum(c.get("trabalho_bomba", 0) for c in self.components)
        w_compressor_total = sum(c.get("trabalho_compressor", 0) for c in self.components)
        
        # No ciclo Brayton, o calor é adicionado no trocador de calor pós-compressor
        q_entrada_total = sum(c.get("trabalho_caldeira", 0) for c in self.components)
        
        eficiencia = None
        trabalho_liquido = w_turbina_total - (w_bomba_total + w_compressor_total)
        
        if q_entrada_total != 0:
            eficiencia = (trabalho_liquido / q_entrada_total) * 100
            
        self.data["resultados_ciclo"] = {
            "trabalho_turbina_total": round(w_turbina_total, 4),
            "trabalho_bomba_total": round(w_bomba_total, 4),
            "trabalho_compressor_total": round(w_compressor_total, 4),
            "trabalho_caldeira_total": round(q_entrada_total, 4),
            "eficiencia_ciclo": round(eficiencia, 4) if eficiencia is not None else None
        }

    def _calcular_trabalhos_componentes(self):
        # Identificar componentes que vêm após um compressor (para o caso do Brayton)
        pos_compressor = []
        if self.tipo_ciclo == "Brayton":
            for comp in self.components:
                if comp["type"] == "compressor":
                    # Encontrar o que vem depois do compressor no grafo
                    sucessores = list(self.graph.successors(comp["id"]))
                    pos_compressor.extend(sucessores)

        for comp in self.components:
            entrada, saida = self.pifs_in.get(comp["id"], []), self.pifs_out.get(comp["id"], [])
            if len(entrada) == 1 and len(saida) == 1:
                h_in, h_out = entrada[0].get("entalpia"), saida[0].get("entalpia")
                
                # Se for Brayton, calculamos trabalho via Cp * deltaT
                if self.tipo_ciclo == "Brayton":
                    t_in, t_out = entrada[0].get("temperatura"), saida[0].get("temperatura")
                    if t_in not in [None, "", "null"] and t_out not in [None, "", "null"]:
                        cp = 1.004 if self.fluido == "Air" else 1.005
                        t_in, t_out = float(t_in), float(t_out)
                        
                        if comp["type"] in ["caldeira", "TrocadorDeCalor"]:
                            # Apenas se vier após o compressor
                            if comp["id"] in pos_compressor:
                                comp["trabalho_caldeira"] = round(cp * (t_out - t_in), 4)
                        elif comp["type"] == "turbina": 
                            comp["trabalho_turbina"] = round(cp * (t_in - t_out), 4)
                        elif comp["type"] == "compressor": 
                            comp["trabalho_compressor"] = round(cp * (t_out - t_in), 4)
                        continue

                if h_in not in [None, "", "null"] and h_out not in [None, "", "null"]:
                    h_in, h_out = float(h_in), float(h_out)
                    if comp["type"] == "caldeira": comp["trabalho_caldeira"] = round(h_out - h_in, 4)
                    elif comp["type"] == "turbina": comp["trabalho_turbina"] = round(h_in - h_out, 4)
                    elif comp["type"] == "compressor": comp["trabalho_compressor"] = round(h_out - h_in, 4)

    def processar(self):
        # Passo 1: Propagação de Pressão (Herança nos trocadores)
        for comp in self.components:
            for r in self.regras_passo1: r.aplicar(comp, self.pifs_in, self.pifs_out)
        
        # Passo 2: Cálculo de Propriedades (Primeira tentativa)
        for p in self.pifs: self.calculadora.processar_pif(p)
        
        # Passo 3: Propagação de Entropia (Isentrópica)
        for comp in self.components:
            for r in self.regras_passo3: r.aplicar(comp, self.pifs_in, self.pifs_out)
        
        # Passo 4: Cálculo de Propriedades (Segunda tentativa)
        for p in self.pifs: self.calculadora.processar_pif(p)
        
        # Passo 5: Cálculos Específicos (Bomba, Compressor e Turbina)
        for comp in self.components:
            for r in self.regras_passo_bomba: r.aplicar(comp, self.pifs_in, self.pifs_out)
            for r in self.regras_passo_compressor: r.aplicar(comp, self.pifs_in, self.pifs_out)
            for r in self.regras_passo_turbina: r.aplicar(comp, self.pifs_in, self.pifs_out)
        
        # Passo 6: Cálculo de Propriedades Final
        for p in self.pifs: self.calculadora.processar_pif(p)

        self._calcular_trabalhos_componentes()
        self._calcular_eficiencia_ciclo()
        return self.data

app = Flask(__name__)

@app.route("/")
def home(): return render_template("index.html")

@app.route("/processar-circuito", methods=["POST"])
def processar_circuito():
    data = request.get_json()
    circuito = Circuito(data, data.get("fluido", "Water"), data.get("densidade", 1000.0))
    circuito_processado = circuito.processar()
    try:
        pdf_buffer = gerar_pdf_relatorio(circuito_processado)
        filename = f"relatorio_ciclo_{circuito.tipo_ciclo.lower()}.pdf"
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=filename)
    except Exception as e:
        return jsonify({"erro": "Falha ao gerar PDF.", "detalhes": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
