# Índice de Referências Bibliográficas — SaltCreep

Todas as ~52 referências em `docs/references/new_references/`. Status:
- ☑ Extraído — equações e parâmetros em `docs/reference-extraction-log.md` + atualizado em doc operacional.
- ☐ Indexado — apenas metadados; extrair ao implementar a etapa correspondente.

---

## Artigos

### PoiateFalcao2006
- **Arquivo:** `docs/references/new_references/PETRO_COSTA, Well Design for Drilling Through Thick Evaporite Layers in Santos Basin - Brazil_2006.pdf`
- **Autores:** Poiate Jr., Edgard; Costa, A.; Maia, A.; Falcao, Jose L. — Petrobras S.A.
- **Ano:** 2006
- **Publicação:** IADC/SPE 99161, Drilling Conference, Miami
- **Tema:** Metodologia de projeto de fluido e revestimento para perfuração em sal espesso (Santos Basin). Validação da lei DM para halita, carnalita e taquidrita. Tabela de propriedades elásticas por litologia.
- **Relevância:** Etapa base (DM) + calibração de litologias. Origem dos parâmetros elásticos E e ν usados em `data/litologias/`.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### munson1990
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/munson1990.pdf`
- **Autores:** Munson, D.E.; Fossum, A.F.; Senseny, P.E.
- **Ano:** 1990
- **Publicação:** Tunnelling and Underground Space Technology, Vol. 5, No. 1/2, pp. 135–139
- **Tema:** Modelo Munson-Dawson (M-D) revisado para predição de fechamento de galeria WIPP. Formulação completa do M-D com transiente F(ξ), parâmetros para sal limpo e sal argiloso.
- **Relevância:** Etapa 8c (ISV_SH_DM). Base do modelo multi-mecanismo com endurecimento.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### munson1997
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/munson1997.pdf`
- **Autores:** Munson, D.E. et al.
- **Ano:** 1997
- **Tema:** Parâmetros do M-D atualizados para múltiplos tipos de sal do WIPP. Correlações multi-mecanismo.
- **Relevância:** Etapa 8c (ISV_SH_DM). Complementa munson1990 com parâmetros expandidos.
- **Status:** ☐ Indexado

### chan1992
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/chan1992.pdf`
- **Autores:** Chan, K.S.; Bodner, S.R.; Fossum, A.F.; Munson, D.E.
- **Ano:** 1992
- **Publicação:** Journal (WIPP)
- **Tema:** Modelo constitutivo M-D + dano para compressão triaxial (Chan-Fossum-Munson). Equações de taxa de dano ω̇, tensor de taxa viscosa por dano, parâmetros para sal limpo.
- **Relevância:** Etapa 8c (ISV_SH_DM) + Etapa 9 (dilatância). Extensão do M-D com dano acoplado.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### chan1994
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/chan1994.pdf`
- **Autores:** Chan, K.S. et al.
- **Ano:** 1994
- **Tema:** Extensão do modelo Chan1992 com recuperação de dano (healing). Análise de câmara subterrânea.
- **Relevância:** Etapa 8c + 9. Healing é relevante para sal que veda fraturas.
- **Status:** ☐ Indexado

### Chan_e_Musson1998
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/Chan_e_Musson1998.pdf`
- **Autores:** Chan, K.S.; Munson, D.E.
- **Ano:** 1998
- **Tema:** Revisão integrada do M-D com dano e healing. Aplicação a repositório de resíduos nucleares.
- **Relevância:** Etapa 8c. Formulação consolidada Chan-Munson.
- **Status:** ☐ Indexado

### FeiWu2018
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/FeiWu2018.pdf`
- **Autores:** Wu, Fei; Chen, Jie; Zou, Quanle
- **Ano:** 2019 (publicado online 2018)
- **Publicação:** International Journal of Damage Mechanics, Vol. 28(5) 758–771
- **Tema:** Modelo não-linear de dano em fluência para rocha salina. Dano D=1−exp(−a(t−t₀)) na fase acelerada. Acoplamento: σ_efetiva = σ₀/(1−D). Modelo fracionário Maxwell para fluência estável. Ensaio de carga em degraus (10 etapas, 6 meses), sal da China.
- **Relevância:** Etapa 8a (Wang-CDM alternativo) e Etapa 3 (terciária). Parametrização para sal chinês.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### wang2019
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/wang2019.pdf`
- **Autores:** Wang, Chunping; Liu, Jianfeng; Wang, Lu
- **Ano:** 2019
- **Publicação:** Advances in Civil Engineering, Vol. 2019, Article 3073975
- **Tema:** Evolução de dano em sal sob diferentes condições de tensão (tração direta, Brazilian, compressão triaxial). Monitoramento por emissão acústica 3D. Força uniaxial compressiva: 21.58 MPa. Dano na falha: ~0.83 (tração), ~0.75 (Brazilian), ~0.91 (compressão).
- **Relevância:** ⚠️ NÃO é o "Wang 2004" CDM do roadmap. É um paper diferente sobre ensaios cíclicos. Útil como dado experimental de calibração de envoltórias (Etapa 9).
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md` (apenas identificação)

### wu2020
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/wu2020.pdf`
- **Autores:** Wu et al.
- **Ano:** 2020
- **Tema:** Extensão do modelo Wu/Chen (2018) para sal, com foco em aceleração da fluência terciária.
- **Relevância:** Etapa 8a. Complementa FeiWu2018.
- **Status:** ☐ Indexado

### Firme2016
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/Firme2016_Article_AnAssessmentOfTheCreepBehaviou.pdf`
- **Autores:** Firme, Pedro A.L.P.; Roehl, Deane; Romanel, Celso
- **Ano:** 2016
- **Publicação:** Artigo (journal)
- **Tema:** Avaliação do comportamento de fluência de rochas salinas brasileiras usando o modelo multi-mecanismo de deformação (MD). Parâmetros para halita da Formação Muribeca (Sergipe). Validação: ensaios triaxiais, galeria da mina Taquari-Vassouras, poço pré-sal. Dois conjuntos de parâmetros (A e B).
- **Relevância:** Base para implementação do MD completo e EDMT. Parâmetros específicos para sal brasileiro.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### Firme2018
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/Firme2018_Article_EnhancedDouble-mechanismCreepL.pdf`
- **Autores:** Firme, Pedro A.L.P.; Brandao, Nuno B.; Roehl, Deane; Romanel, Celso
- **Ano:** 2018
- **Publicação:** Artigo (journal)
- **Tema:** Leis de fluência DM aprimoradas para rochas salinas: EDMT (Enhanced DM with Transient function) e EDMP (Enhanced DM with Power law). Parâmetros para halita brasileira. Validação vs ensaios triaxiais e galeria de mina.
- **Relevância:** Referência principal para EDMT. Fornece parâmetros K₀, c, α_a, β_a, δ para transiente. **Atenção:** a função F do Firme é o F de Munson-Dawson, diferente do K₁·exp(-K₂·εv) implementado no SaltCreep.
- **Status:** ☑ Extraído em `docs/reference-extraction-log.md`

### Hou2003
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/Hou2003.pdf`
- **Autores:** Hou, Zhiming
- **Ano:** 2003
- **Tema:** Envoltória de dilatância Hou/Lux: critério de início de dano baseado em I₁ e J₂. Inclui healing (selagem de fraturas).
- **Relevância:** Etapa 9 (envoltórias de dilatância).
- **Status:** ☐ Indexado

### CavalcanteRamos2010
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/CavalcanteRamos2010.pdf`
- **Autores:** Cavalcante, A.L.B.; Ramos, A.C.S.
- **Ano:** 2010
- **Tema:** Modelo viscoelástico com dano aplicado à mecânica de rochas salinas.
- **Relevância:** Etapa 8a. Modelo CDM alternativo para sal.
- **Status:** ☐ Indexado

### A_coupled_Viscoelastic_Damage
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/A coupled Viscoelastic Damage Model Applied to Salt Rock Mechanics.pdf`
- **Autores:** (verificar no PDF)
- **Ano:** (verificar)
- **Tema:** Modelo viscoelástico-dano acoplado para mecânica de rochas salinas.
- **Relevância:** Etapa 8a. Alternativa CDM.
- **Status:** ☐ Indexado

### Incorporation_of_a_damage_model
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/Incorporation of a damage model to salt rocks viscoelastic modelling.pdf`
- **Autores:** (verificar)
- **Ano:** (verificar)
- **Tema:** Incorporação de dano em modelo viscoelástico para sal.
- **Relevância:** Etapa 8a.
- **Status:** ☐ Indexado

### Numerical_modeling_triaxial
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/Numerical modeling of triaxial tests on salt rocks using a creep law with.pdf`
- **Autores:** (verificar)
- **Tema:** Modelagem numérica de ensaios triaxiais em sal com lei de fluência (EDMT ou similar).
- **Relevância:** Etapa 2 (EDMT) — validação numérica.
- **Status:** ☐ Indexado

### chen2006
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/chen2006.pdf`
- **Autores:** Chen et al.
- **Ano:** 2006
- **Tema:** Modelo constitutivo para fluência de sal. (Verificar conteúdo)
- **Relevância:** Geral — constitutive modeling.
- **Status:** ☐ Indexado

### chen2013
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/chen2013.pdf`
- **Autores:** Chen et al.
- **Ano:** 2013
- **Tema:** Modelo constitutivo para fluência de sal (extensão de 2006).
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### justen2013
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/justen2013.pdf`
- **Autores:** Justen et al.
- **Ano:** 2013
- **Tema:** (Verificar) Calibração ou validação de modelo constitutivo para sal.
- **Relevância:** Calibração.
- **Status:** ☐ Indexado

### lao2012
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/lao2012.pdf`
- **Autores:** Lao et al.
- **Ano:** 2012
- **Tema:** (Verificar) Modelo ou análise de fluência para sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### yang1999
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/yang1999.pdf`
- **Autores:** Yang et al.
- **Ano:** 1999
- **Tema:** Fluência de sal — modelo precoce com mecanismo de dislocation.
- **Relevância:** Histórica/base.
- **Status:** ☐ Indexado

### zhang2021
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/zhang2021.pdf`
- **Autores:** Zhang et al.
- **Ano:** 2021
- **Tema:** Fluência de sal — modelo recente.
- **Relevância:** Etapa 8 (modelos alternativos).
- **Status:** ☐ Indexado

### zhao2021
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/zhao2021.pdf`
- **Autores:** Zhao et al.
- **Ano:** 2021
- **Tema:** Fluência de sal ou cavernas de sal — model ou análise de estabilidade.
- **Relevância:** Etapa 8.
- **Status:** ☐ Indexado

### zhao2023
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/zhao2023.pdf`
- **Autores:** Zhao et al.
- **Ano:** 2023
- **Tema:** Fluência de sal — modelo mais recente.
- **Relevância:** Etapa 8.
- **Status:** ☐ Indexado

---

## Artigos Novos

### Analysis_creep_dilatant
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/Analysis of the creep and dilatant behavior.pdf`
- **Ano:** (verificar)
- **Tema:** Análise de fluência e comportamento dilatante. Comparação de envoltórias.
- **Relevância:** Etapa 9 (envoltórias de dilatância). Alta prioridade — Prioridade 2.
- **Status:** ☐ Indexado

### Moslehy2023
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/Moslehy2023.pdf`
- **Autores:** Moslehy et al.
- **Ano:** 2023
- **Tema:** (Verificar) Fluência de evaporitos ou cavernas de sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### Proceedings_LARMS2022
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/Proceedings_LARMS2022_Full_Official.pdf`
- **Ano:** 2022
- **Tamanho:** 53.4 MB — NÃO ABRIR (> 10 MB, não prioritário)
- **Tema:** Anais LARMS 2022 — múltiplos papers sobre mecânica de rochas da América Latina.
- **Relevância:** Vários papers potencialmente relevantes. Extrair individualmente quando necessário.
- **Status:** ☐ Indexado (não processado — arquivo grande)

### arma-2014-7051
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/arma-2014-7051.pdf`
- **Ano:** 2014
- **Tema:** (Verificar) ARMA paper sobre sal ou cavernas.
- **Relevância:** Geral — calibração/validação.
- **Status:** ☐ Indexado

### arma-2018-984
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/arma-2018-984.pdf`
- **Ano:** 2018
- **Tema:** (Verificar) ARMA paper — sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### arma-2019-2079
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/arma-2019-2079.pdf`
- **Ano:** 2019
- **Tema:** (Verificar) ARMA paper — sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### arma-2022-0191
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/arma-2022-0191.pdf`
- **Ano:** 2022
- **Tema:** (Verificar) ARMA paper — sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### azabou2021
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/azabou2021.pdf`
- **Ano:** 2021
- **Tema:** (Verificar) Fluência de sal — Tunísia ou região MENA.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### iptc-21165-ms
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/iptc-21165-ms.pdf`
- **Ano:** (verificar, IPTC)
- **Tema:** (Verificar) IPTC paper — perfuração ou estabilidade de poço em sal.
- **Relevância:** Validação de campo.
- **Status:** ☐ Indexado

### otc-28006-ms
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/novos/otc-28006-ms.pdf`
- **Ano:** (verificar, OTC)
- **Tema:** (Verificar) OTC paper — offshore/sal.
- **Relevância:** Validação de campo.
- **Status:** ☐ Indexado

---

## Equações Constitutivas (diretório raiz)

### TCC_OTAVIO
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/TCC_OTAVIO_Estudo numérico de ensaios triaxiais aplicado à perfuração de poços em rochas salinas.pdf`
- **Autores:** Otávio (sobrenome a confirmar)
- **Ano:** (verificar)
- **Tema:** TCC — estudo numérico de ensaios triaxiais em sal. Calibração DM. Casos A–F numéricos.
- **Relevância:** Alta — Etapa base (DM) + calibração de litologias + casos de validação.
- **Status:** ☐ Indexado (prioridade 3 — extrair para validação)

### correlation_of_creep_musson
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/correlation_of_creep_musson.pdf`
- **Autores:** Munson et al.
- **Tema:** Correlações do modelo multi-mecanismo para diferentes tipos de sal.
- **Relevância:** Etapa 8c (ISV_SH_DM). Tabelas de parâmetros multi-litologia.
- **Status:** ☐ Indexado (prioridade 3)

### fossum1993
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/fossum1993.pdf`
- **Autores:** Fossum, A.F. et al.
- **Ano:** 1993
- **Tema:** Potencial de fluxo de Fossum/Munson. Envoltória de dilatância.
- **Relevância:** Etapa 9 (envoltórias). Prioridade 2.
- **Status:** ☐ Indexado

### multimechanism_domal_salts
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/multimechanism-deformation parameters of domal salts.pdf`
- **Tema:** Parâmetros M-D para sal de domos.
- **Relevância:** Etapa 8c. Complementa munson1990 com parâmetros de domos salinos.
- **Status:** ☐ Indexado

### Dissertacao_primariaEsecundaria
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/Dissertacao_primariaEsecundaria.pdf`
- **Tema:** Dissertação sobre fluência primária e secundária em sal.
- **Relevância:** Etapa 2 (EDMT/ISV_SH_DM).
- **Status:** ☐ Indexado

---

## Teses e Dissertações

### Poiate_tese
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/Poiate_tese.pdf`
- **Autores:** Poiate Jr., Edgard
- **Tema:** Tese de doutorado — mecânica de rochas salinas. Casos A–F expandidos, constantes por litologia, análise de poço.
- **Tamanho:** 14.68 MB — usar `pages:` ao ler seções específicas.
- **Relevância:** Alta — base dos casos TCC A–F. Prioridade 3.
- **Status:** ☐ Indexado

### Firme_dissertacao_completa
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/Firme_posgrad/Firme_dissertacao_completa.pdf`
- **Autores:** Firme, Pedro A.L.P.
- **Tema:** Dissertação completa sobre modelos constitutivos para sal (EDMT, MD). Formulação unificada ISV_SH_D.
- **Tamanho:** 9.41 MB — usar `pages:` ao ler seções específicas.
- **Relevância:** Alta — Etapa 8b (Aubertin ISV_SH_D). Prioridade 1.
- **Status:** ☐ Indexado (prioridade 1 — extrair seções de equações)

### firme2019
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/artigos/firme2019.pdf`
- **Autores:** Firme, Pedro A.L.P.
- **Ano:** 2019
- **Tamanho:** 7.51 MB
- **Tema:** Formulação unificada ISV_SH_D. Artigo derivado da tese.
- **Relevância:** Etapa 8b (Aubertin ISV_SH_D). Prioridade 1.
- **Status:** ☐ Indexado

### Firme_posgrad_Salt_geomechanics
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/Firme_posgrad/Salt geomechanics applied to strategic engineering.PDF`
- **Autores:** Firme et al.
- **Tamanho:** 10.69 MB — usar `pages:` ao ler.
- **Tema:** Validação do ISV_SH_D vs campo (pós-doutorado Firme).
- **Relevância:** Etapa 8b (Aubertin ISV_SH_D). Prioridade 1.
- **Status:** ☐ Indexado

### BRUNETTA2022
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/BRUNETTA2022.pdf`
- **Autores:** Brunetta (2022)
- **Tema:** (Verificar) Tese sobre sal — modelo constitutivo ou análise de estabilidade.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### Florencio_Doutorado
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/Florencio_Doutorado.pdf`
- **Tema:** Tese de doutorado sobre sal (Florêncio).
- **Tamanho:** 9.45 MB.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### Gravina_CarlosCabral_M
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/Gravina_CarlosCabral_M.pdf`
- **Tema:** Dissertação de mestrado — mecânica de sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### MODELO_VISCOPLASTICO_DANO_NAO_LOCAL
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/MODELO VISCOPLASTICO COM DANO NAO LOCAL APLICADO A ROCHAS.pdf`
- **Tema:** Modelo viscoplástico com dano não-local. Potencialmente relevante para Etapa 8 (modelo de dano avançado).
- **Relevância:** Etapa 8 (CDM avançado).
- **Status:** ☐ Indexado

### Ruiz2015
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/Ruiz2015.pdf`
- **Autores:** Ruiz (2015)
- **Tema:** (Verificar) Tese — fluência em sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### Thesis_Veronica_Donadio
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/Thesis_Veronica_Donadio.pdf`
- **Tamanho:** 9.72 MB.
- **Tema:** (Verificar) Tese — sal ou cavernas.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

### dissertacao_cavalcante
- **Arquivo:** `docs/references/new_references/EquacoesConstitutivas/teses_dissertacoes/dissertacao_cavalcante.pdf`
- **Tamanho:** 9.51 MB.
- **Tema:** Dissertação Cavalcante — mecânica de sal.
- **Relevância:** Geral.
- **Status:** ☐ Indexado

---

## Petrobras / Campo

### PETRO_Triaxial_Creep_Tests
- **Arquivo:** `docs/references/new_references/PETRO_Triaxial Creep Tests in Salt – Applied in drilling through thick.pdf`
- **Autores:** (Petrobras — verificar)
- **Tema:** Ensaios triaxiais em sal aplicados à perfuração em espessas camadas de sal. Dados de fluência por litologia.
- **Relevância:** Alta — Prioridade 3. Dados de ensaios triaxiais Petrobras para calibração DM/EDMT.
- **Status:** ☐ Indexado (prioridade 3 — extrair dados de ensaio)

### PETRO_COSTA_Well_Design
- **Arquivo:** `docs/references/new_references/PETRO_COSTA, Well Design for Drilling Through Thick Evaporite Layers in Santos Basin - Brazil_2006.pdf`
- **Autores:** Poiate Jr., Edgard; Costa, A.; Maia, A.; Falcao, Jose L.
- **Ano:** 2006
- **Publicação:** IADC/SPE 99161
- **Tema:** Idem PoiateFalcao2006 (mesmo paper, cópia duplicada ou versão diferente).
- **Relevância:** Mesma do PoiateFalcao2006.
- **Status:** ☑ Extraído (via PoiateFalcao2006)

---

## Resumo de Status

| Categoria | Total | Extraído | Indexado |
|---|---|---|---|
| Artigos principais | 13 | 6 | 7 |
| Artigos novos (ARMA/OTC/IPTC) | 10 | 0 | 10 |
| Equações Constitutivas (raiz) | 5 | 1 | 4 |
| Teses e dissertações | 10 | 0 | 10 |
| Petrobras | 2 | 1 | 1 |
| **Total** | **52** | **8** | **32** |

---

## Modelos prontos para implementar (com equações completas)

1. **EDMT simplificado** (K₁·exp(−K₂·εv)) — ☑ já implementado em `include/constitutive/edmt.hpp`
2. **M-D (Munson-Dawson)** — equações completas disponíveis em `docs/reference-extraction-log.md`. Pronto para Etapa 8c.
3. **Wu2018 CDM** — equações completas disponíveis. Pronto para Etapa 8a como alternativa ao Wang 2004.

## Modelos precisando de decisão humana antes de implementar

- **Wang 2004 CDM (Lemaitre)**: o arquivo `wang2019.pdf` no repo é um paper diferente (Wang 2019, não Wang 2004). Precisamos localizar o paper correto "Wang 2004" antes de implementar.
- **Aubertin ISV_SH_D**: equações completas estão em `firme2019.pdf` e `Firme_dissertacao_completa.pdf` — extrair antes da Etapa 8b.
- **ISV_SH_DM (seno-hiperbólico)**: extrair de `chan1992.pdf` + `munson1990.pdf` + `firme2019.pdf`.
