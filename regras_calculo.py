from CoolProp.CoolProp import PropsSI
import io 

# -----------------------------
# CLASSES DE DOMÍNIO (POO)
# -----------------------------

class RegraCalculoBomba:
    def __init__(self, tipos_componentes, densidade_fluido):
        self.tipos_componentes = [tipos_componentes] if isinstance(tipos_componentes, str) else tipos_componentes
        self.densidade_fluido = densidade_fluido
    
    def _valor_valido(self, valor):
        if valor == 0: return True
        return valor not in [None, "", "null"]
        
    def aplicar(self, componente, pifs_in, pifs_out):
        if componente["type"] not in self.tipos_componentes: return False
        entrada, saida = pifs_in.get(componente["id"], []), pifs_out.get(componente["id"], [])
        if len(entrada) == 1 and len(saida) == 1:
            p_in, p_out = entrada[0], saida[0]
            p_in_kpa, p_out_kpa, h_in_kjkg = p_in.get("pressao"), p_out.get("pressao"), p_in.get("entalpia")
            if not (self._valor_valido(p_in_kpa) and self._valor_valido(p_out_kpa) and self._valor_valido(h_in_kjkg)):
                return False
            try:
                p_in_pa, p_out_pa = float(p_in_kpa) * 1000.0, float(p_out_kpa) * 1000.0
                trabalho_kjkg = ((p_out_pa - p_in_pa) / self.densidade_fluido) / 1000.0
                h_out_kjkg = float(h_in_kjkg) + trabalho_kjkg
                componente["trabalho_bomba"] = round(trabalho_kjkg, 4)
                if not self._valor_valido(p_out.get("entalpia")):
                    p_out["entalpia"] = round(h_out_kjkg, 4)
                    return True
            except: pass
        return False

class RegraCalculoCompressor:
    def __init__(self, tipos_componentes, fluido, k=1.4):
        self.tipos_componentes = [tipos_componentes] if isinstance(tipos_componentes, str) else tipos_componentes
        self.fluido = fluido
        self.k = k # Razão de calores específicos (Cp/Cv), padrão 1.4 para Ar

    def _valor_valido(self, valor):
        if valor == 0: return True
        return valor not in [None, "", "null"]

    def aplicar(self, componente, pifs_in, pifs_out):
        if componente["type"] not in self.tipos_componentes: return False
        entrada, saida = pifs_in.get(componente["id"], []), pifs_out.get(componente["id"], [])
        
        if len(entrada) == 1 and len(saida) == 1:
            p_in_pif, p_out_pif = entrada[0], saida[0]
            
            t_in = p_in_pif.get("temperatura")
            t_out = p_out_pif.get("temperatura")
            p_in = p_in_pif.get("pressao")
            p_out = p_out_pif.get("pressao")

            # Verifica se temos as pressões necessárias
            if not (self._valor_valido(p_in) and self._valor_valido(p_out)):
                return False

            try:
                p_in, p_out = float(p_in), float(p_out)
                exp = (self.k - 1) / self.k

                # Caso 1: Temos T_entrada, queremos T_saida
                if self._valor_valido(t_in) and not self._valor_valido(t_out):
                    t_in_k = float(t_in) + 273.15
                    t_out_k = t_in_k * (p_out / p_in)**exp
                    p_out_pif["temperatura"] = round(t_out_k - 273.15, 4)
                    p_out_pif["manual_temp"] = True # Flag para evitar sobrescrita pelo CoolProp
                    return True

                # Caso 2: Temos T_saida, queremos T_entrada
                if self._valor_valido(t_out) and not self._valor_valido(t_in):
                    t_out_k = float(t_out) + 273.15
                    t_in_k = t_out_k / ((p_out / p_in)**exp)
                    p_in_pif["temperatura"] = round(t_in_k - 273.15, 4)
                    p_in_pif["manual_temp"] = True # Flag para evitar sobrescrita pelo CoolProp
                    return True
            except:
                pass
        return False

class RegraCalculoTurbina:
    def __init__(self, tipos_componentes, fluido, k=1.4):
        self.tipos_componentes = [tipos_componentes] if isinstance(tipos_componentes, str) else tipos_componentes
        self.fluido = fluido
        self.k = k # Razão de calores específicos (Cp/Cv), padrão 1.4 para Ar

    def _valor_valido(self, valor):
        if valor == 0: return True
        return valor not in [None, "", "null"]

    def aplicar(self, componente, pifs_in, pifs_out):
        if componente["type"] not in self.tipos_componentes: return False
        entrada, saida = pifs_in.get(componente["id"], []), pifs_out.get(componente["id"], [])
        
        if len(entrada) == 1 and len(saida) == 1:
            p_in_pif, p_out_pif = entrada[0], saida[0]
            
            t_in = p_in_pif.get("temperatura")
            t_out = p_out_pif.get("temperatura")
            p_in = p_in_pif.get("pressao")
            p_out = p_out_pif.get("pressao")

            # Verifica se temos as pressões necessárias
            if not (self._valor_valido(p_in) and self._valor_valido(p_out)):
                return False

            try:
                p_in, p_out = float(p_in), float(p_out)
                exp = (self.k - 1) / self.k

                # Caso 1: Temos T_entrada, queremos T_saida
                # T_in / T_out = (P_in / P_out)^exp => T_out = T_in / (P_in / P_out)^exp
                if self._valor_valido(t_in) and not self._valor_valido(t_out):
                    t_in_k = float(t_in) + 273.15
                    t_out_k = t_in_k / ((p_in / p_out)**exp)
                    p_out_pif["temperatura"] = round(t_out_k - 273.15, 4)
                    p_out_pif["manual_temp"] = True # Flag para evitar sobrescrita pelo CoolProp
                    return True

                # Caso 2: Temos T_saida, queremos T_entrada
                # T_in = T_out * (P_in / P_out)^exp
                if self._valor_valido(t_out) and not self._valor_valido(t_in):
                    t_out_k = float(t_out) + 273.15
                    t_in_k = t_out_k * ((p_in / p_out)**exp)
                    p_in_pif["temperatura"] = round(t_in_k - 273.15, 4)
                    p_in_pif["manual_temp"] = True # Flag para evitar sobrescrita pelo CoolProp
                    return True
            except:
                pass
        return False

class RegraPropagacaoEntropia:
    def __init__(self, tipos_componentes):
        self.tipos_componentes = [tipos_componentes] if isinstance(tipos_componentes, str) else tipos_componentes
    
    def aplicar(self, componente, pifs_in, pifs_out):
        if componente["type"] not in self.tipos_componentes: return False
        entrada, saida = pifs_in.get(componente["id"], []), pifs_out.get(componente["id"], [])
        if len(entrada) == 1 and len(saida) == 1:
            p_in, p_out = entrada[0], saida[0]
            s_in, s_out = p_in.get("entropia"), p_out.get("entropia")
            if s_in not in [None, "", "null"] and s_out in [None, "", "null"]:
                p_out["entropia"] = s_in
                return True
            if s_out not in [None, "", "null"] and s_in in [None, "", "null"]:
                p_in["entropia"] = s_out
                return True
        return False

class RegraPropagacaoPressao:
    def __init__(self, tipos_componentes):
        self.tipos_componentes = [tipos_componentes] if isinstance(tipos_componentes, str) else tipos_componentes
    
    def aplicar(self, componente, pifs_in, pifs_out):
        if componente["type"] not in self.tipos_componentes: return False
        entrada, saida = pifs_in.get(componente["id"], []), pifs_out.get(componente["id"], [])
        if len(entrada) == 1 and len(saida) == 1:
            p_in, p_out = entrada[0], saida[0]
            pres_in, pres_out = p_in.get("pressao"), p_out.get("pressao")
            if pres_in not in [None, "", "null"] and pres_out in [None, "", "null"]:
                p_out["pressao"] = pres_in
                return True
            if pres_out not in [None, "", "null"] and pres_in in [None, "", "null"]:
                p_in["pressao"] = pres_out
                return True
        return False

class CalculadoraPropriedadesTermodinamicas:
    def __init__(self, fluido="Water"):
        self.fluido = fluido
        self.prop_map = {"pressao": "P", "temperatura": "T", "entalpia": "H", "entropia": "S", "titulo": "Q"}
    
    def _valor_valido(self, valor):
        if valor == 0: return True
        return valor not in [None, "", "null"]
    
    def _converter_unidades_entrada(self, prop_nome, valor):
        v = float(valor)
        if prop_nome == "pressao": return v * 1000
        if prop_nome == "temperatura": return v + 273.15
        if prop_nome in ["entalpia", "entropia"]: return v * 1000
        return v

    def _converter_unidades_saida(self, prop_nome, valor):
        if prop_nome == "pressao": return valor / 1000
        if prop_nome == "temperatura": return valor - 273.15
        if prop_nome in ["entalpia", "entropia"]: return valor / 1000
        return valor

    def processar_pif(self, pif):
        # Se for ciclo Brayton (Ar), evitamos usar CoolProp para propriedades que dependem de mudança de fase ou se já calculamos manualmente
        if self.fluido == "Air":
            # Para o Ar no ciclo Brayton, muitas vezes tratamos como gás ideal
            pass

        props_conhecidas = {}
        for nome, cod in self.prop_map.items():
            valor = pif.get(nome)
            if self._valor_valido(valor):
                props_conhecidas[cod] = self._converter_unidades_entrada(nome, valor)
        
        if self.fluido == "Air" and "Q" in props_conhecidas:
            del props_conhecidas["Q"]
            pif["titulo"] = ""

        if len(props_conhecidas) < 2: return False
        
        # Se for Ar, vamos restringir o uso do CoolProp ou usar modelo de gás ideal
        if self.fluido == "Air":
            return False

        try:
            chaves = list(props_conhecidas.keys())
            v1, v2 = props_conhecidas[chaves[0]], props_conhecidas[chaves[1]]
            for nome, cod in self.prop_map.items():
                if nome == "temperatura" and pif.get("manual_temp"):
                    continue
                if cod not in props_conhecidas:
                    if self.fluido == "Air" and cod == "Q": continue
                    res = PropsSI(cod, chaves[0], v1, chaves[1], v2, self.fluido)
                    pif[nome] = round(self._converter_unidades_saida(nome, res), 4)
            return True
        except: return False
