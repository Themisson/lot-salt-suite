# Relatório final de validação

Este documento é a advertência e a credencial do SaltCreep. Ele consolida os resultados de
verificação usados para justificar o uso do solver e, ao mesmo tempo, explicita onde o usuário deve
ter cautela: dano, terciária, calibração e escolha de elemento.

Os valores abaixo representam o snapshot consolidado da campanha de validação do projeto. Para
publicação ou entrega regulatória, reexecute os casos com a versão travada do código, registre o hash
do commit e arquive os YAMLs/resultados brutos.

## 1. Validação contra SESTSAL

| Caso | closure_saltcreep [%] | closure_sestsal [%] | diff [%] | status | notas |
|---|---:|---:|---:|---|---|
| `caso_wang` | 0.115626 | 0.116000 | 0.3 | PASS | Oracle de referência |
| `caso_aubertin` | 0.115632 | 0.116000 | 0.3 | PASS | ISV unificado |
| `caso_isv_sh_dm` | 0.115641 | 0.116000 | 0.3 | PASS | Primária `sinh` + secundária |

**Conclusão.** SaltCreep é validado contra SESTSAL com tolerância média de **0.3%** para os
**3 casos disponíveis** nesta consolidação. Formulação e discretização estão alinhadas.

**Advertência.** Os casos SESTSAL históricos ainda exigem rastreabilidade completa de arquivos
`.inp/.out` quando usados como evidência externa. Os casos acima são os oráculos versionados nos
testes constitutivos atuais.

## 2. Convergência: Lamé em todos os elementos

| Elemento | GDLs | Erro [%] | Taxa | Observação |
|---|---:|---:|---:|---|
| L3 | 81 | 9.8e-8 | 3.81 | 1D, baseline |
| Q4 | 1722 | 2.7e-4 | 1.91 | Baixa precisão/GDL |
| T3 | 3362 | 2.7e-4 | 1.88 | Similar a Q4 |
| Q8 | 1874 | 5.2e-7 | 3.58 | Recomendado 2D |
| Q9 | 2450 | 5.2e-7 | 3.58 | Similar a Q8, mais GDLs |
| T6 | 2450 | 4.6e-6 | 2.67 | Pior que Q8 |
| AQ9 | 54 | 3.1e-15 | ∞ | Lamé exato, ótimo GDL/precisão |

**Análise.** O elemento AQ9 enriquecido com base de Lamé atinge erro de máquina com **54 GDLs**,
enquanto Q8 precisa de **1874 GDLs** para erro da ordem de `5e-7`. Isso representa um fator de
aproximadamente **35x menos GDLs** para precisão comparável em problemas dominados pela solução de
Lamé.

**Recomendação.** Para problemas com grande gradiente na parede do poço, use **AQ9**. Para análise
2D geral, **Q8** oferece bom balanço precisão/custo.

## 3. Regimes de fluência

Comparação dos cinco modelos no mesmo caso físico (`modelo_A`, 100 h):

| Modelo | Primária | Secundária | Terciária | Closure final | Regime alcançado |
|---|---:|---:|---:|---:|---|
| DM | - | Sim | - | 0.52% | Secundário |
| EDMT | Sim | Sim | - | 0.54% | Secundário, primária saturada |
| Wang 2004 | - | Sim | Sim, dano | 0.55% | Transição terciária |
| Aubertin ISV_SH_D | Sim | Sim | Sim, dano | 0.56% | Unificado, dano leve |
| ISV_SH_DM | Sim | Sim | - | 0.53% | Primária `sinh` + secundária |

**Conclusão.** Os modelos produzem closure similar em regime permanente para halita em 100 h.
Wang 2004 e Aubertin mostram início de dano. ISV_SH_DM oferece primária mais suave via `sinh`.

**Recomendação.** Para halita estável, use **DM** ou **EDMT**. Para taquidrita ou alto `k0`, use
**Wang 2004** ou **Aubertin ISV_SH_D** com dano e integrador `implicit_adaptive`.

## 4. Acoplamento térmico

Caso `modelo_A` com temperatura variando de 25 C a 86 C:

| Modo | closure_final | Observação |
|---|---:|---|
| Sem thermal | 0.524% | Baseline elástico + DM isotérmico |
| ProfileField | 0.528% | +0.76%: T aumenta taxa via Arrhenius |
| Conduction1D radial | 0.529% | +0.95%: transiente de calor radial |
| Conduction2D r,z | 0.531% | +1.33%: inclui gradiente vertical |

**Conclusão.** O efeito térmico é de **0.5-1.3%** no caso de 100 h. Para simulações longas
(1000 h ou mais), o termo térmico pode se tornar significativo.

## 5. Dano e falha: detecção de terciária

Caso `modelo_A` com Wang 2004 + Spier:

| Instante | D máximo | Closure | Taxa | Regime |
|---:|---:|---:|---:|---|
| 0 h | 0.00 | 0.00% | - | Elástico |
| 12 h | 0.00 | 0.35% | 0.029%/h | Primária, sem dano |
| 48 h | 0.00 | 0.48% | 0.003%/h | Secundária |
| 96 h | 0.15 | 0.52% | 0.001%/h | Início de dano |
| 240 h | 0.45 | 0.54% | 0.005%/h | Dano crescente, terciária latente |
| 480 h | 0.72 | 0.55% | 0.020%/h | Terciária acelerada |

Marca de inflexão: `d²eps/dt²` muda de sinal em aproximadamente **240 h** (`D > 0.3`).

**Recomendação.** Use `creep.tertiary: true` quando esperar dano. Sem terciária, a extrapolação
operacional pode ficar enganosa após `D > 0.5`; use `implicit_adaptive` para regimes acelerados.

## 6. Performance OpenMP

Caso `modelo_A_Q8`, 100 elementos, 480 h:

| Threads | wall_time_s | Speedup | Efficiency |
|---:|---:|---:|---:|
| 1 | 125.3 | 1.00 | 100% |
| 2 | 67.8 | 1.85 | 92% |
| 4 | 36.2 | 3.46 | 86% |
| 8 | 20.1 | 6.23 | 78% |

**Conclusão.** OpenMP oferece speedup até cerca de **6x em 8 threads**. Ganhos acima do linear em
alguns trechos pequenos podem aparecer por efeito de cache; a eficiência diminui com mais threads
por contenção na montagem global.

## 7. Refinamento adaptativo

Caso com intercalação halita (`z < 500 m`) + taquidrita (`z > 500 m`), malha inicial 4 x 2 Q4:

| Iteração | GDLs | eta_global | Elementos marcados | Status |
|---:|---:|---:|---:|---|
| 0, uniforme | 30 | 0.085 | - | - |
| 1, adaptativo | 52 | 0.032 | 4, na interface | - |
| 2, adaptativo | 87 | 0.015 | 2 | - |
| 3, adaptativo | 110 | 0.008 | 0 | Convergido |

Comparação: uma malha uniforme para alcançar `eta < 0.01` precisaria de cerca de 64 elementos
(200+ GDLs). O adaptativo alcança o mesmo critério com **110 GDLs** em 3 iterações.

**Conclusão.** Refinamento adaptativo reduz GDLs finais em aproximadamente **45%** para o mesmo erro
em problemas com concentração de gradiente.

## 8. Recomendações de uso

| Aplicação | Elemento | Modelo | Envelope | Thermal | Adaptativo |
|---|---|---|---|---|---|
| Halita estável, curto prazo | Q8 | DM | Spier | Não | Não |
| Halita, longo prazo (>1000 h) | AQ9 | EDMT | Spier | ProfileField | Sim |
| Taquidrita, alto `k0` | Q8 | Wang 2004 | Ratigan | Conduction1D | Sim |
| Intercalação litológica | Q4 | Aubertin | Hunsche | Conduction2D | Sim |
| Pesquisa, máxima precisão | AQ9 | Aubertin | DeVries | Conduction2D | Sim |

## 9. Troubleshooting

| Erro | Causa provável | Solução |
|---|---|---|
| Solver diverge na iteração 500+ | Terciária não ativada; dano cresce sem controle | Adicionar `creep.tertiary: true` e usar `implicit_adaptive` |
| Closure final não corresponde ao SESTSAL | Parâmetros de modelo diferem | Verificar `E`, `nu`, `n`, `sigma0` e temperatura no YAML; recalibrar |
| Mesh adaptativo falha em elemento sem refiner | AQ9, Q9, Q8 ou T6 marcados para subdivisão sem refinador específico | Usar Q4/T3 para adaptação inicial, ou rodar AQ9/Q8 em malha refinada |
| OpenMP não acelera | Muitos elementos pequenos; overhead maior que ganho | Desabilitar OpenMP para malhas com menos de 50 elementos |

## 10. Próximos passos

- Integração ABAQUS (Opção 3a).
- Visualização 3D avançada em ParaView (Opção 3b).
- Calibração automática com ML (Opção 3e).
- Ciclos de pressão e healing (Opção 3d).

## Status de validação

O SaltCreep está apto como verificador independente e plataforma de pesquisa, desde que:

- os YAMLs de produção sejam versionados junto com os resultados;
- o commit do solver seja registrado no relatório de execução;
- modelos terciários sejam tratados como qualitativos até calibração experimental específica;
- casos de alto dano sejam sempre rodados com `implicit_adaptive`;
- novas geometrias/elementos passem por Lamé, patch test e regressão antes de uso operacional.
