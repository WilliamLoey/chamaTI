# Plano de testes

## Estratégia

O projeto segue o **Modelo V**: cada nível de especificação tem um nível de
teste correspondente.

```mermaid
flowchart LR
    A[Escopo] -.verifica.-> A2[Teste de aceitação<br/>com usuários]
    B[Requisitos] -.verifica.-> B2[Teste de sistema<br/>rotas HTTP]
    C[Arquitetura] -.verifica.-> C2[Teste de integração<br/>serviço + banco]
    D[Detalhamento] -.verifica.-> D2[Teste unitário<br/>regras de negócio]
    A --> B --> C --> D --> E[Codificação]
    E --> D2 --> C2 --> B2 --> A2
```

## Verificação × validação

Os dois termos são frequentemente confundidos, então vale a distinção explícita:

| | Verificação | Validação |
|---|---|---|
| **Pergunta** | Estamos construindo o produto **corretamente**? | Estamos construindo o **produto certo**? |
| **Quando** | Durante o desenvolvimento | Após o módulo estar pronto |
| **Como** | Revisão de código, conferência com a especificação, testes automatizados | Teste de aceitação com usuários reais |
| **Neste projeto** | 113 testes pytest + revisão crítica do código, que encontrou 9 defeitos reais ([`verificacao-v1.md`](verificacao-v1.md)) | 5 testadores, 5 ocorrências relatadas e corrigidas ([`validacao-laudos.md`](validacao-laudos.md) e `laudos/`) |

## Níveis de teste

### Testes unitários — regras de negócio

Rodam contra a camada de serviço, sem cliente HTTP. Um teste que falha aponta
diretamente para a regra quebrada.

| Arquivo | Testes | Cobre |
|---|---:|---|
| `test_usuario_service.py` | 8 | Cadastro, validação de e-mail e senha, hash, autenticação, conta inativa |
| `test_chamado_service.py` | 26 | Abertura, protocolo, validações, atribuição, transições de status, permissões, filtros, SLA |
| `test_indicadores_service.py` | 5 | Totais, tempo médio, taxa de SLA, carga por técnico, banco vazio |

### Testes de integração e sistema — rotas

| Arquivo | Testes | Cobre |
|---|---:|---|
| `test_rotas.py` | 16 | Login, logout, cadastro, abertura pela tela, permissões por URL, códigos HTTP, páginas de erro |
| `test_verificacao_v2.py` | 27 | Regressão dos nove defeitos da **verificação**: escalada de privilégio, CSRF, anexos, fuso, concorrência |
| `test_validacao_laudos.py` | 31 | Regressão das cinco ocorrências da **validação** (21): botão travado no anexo grande, filtros no celular, mensagem do 403, justificativa de atraso, erro junto do campo — mais a L-06 (10), o SLA do chamado cancelado, encontrada na revisão das correções |

**Total: 113 testes.**

```bash
pytest          # tudo
pytest -v       # detalhado
pytest -k sla   # apenas os testes de SLA
```

### Teste de banco de dados

O DDL foi executado contra **PostgreSQL 16** real, verificando que as
restrições barram dados inválidos:

| Cenário | Resultado esperado | Resultado obtido |
|---|---|---|
| Chamado com descrição só de espaços | Rejeitado | `ck_chamado_descricao_minima` ✅ |
| Anexo de 6 MB | Rejeitado | `ck_anexo_tamanho` ✅ |
| Perfil fora dos três previstos | Rejeitado | `ck_usuario_perfil` ✅ |
| Visão `vw_chamado_sla` | Calcula prazo e horas | ✅ |

### Teste de aceitação — com usuários

Os formulários estão prontos em [`laudos/`](../laudos/), um por testador, com
perfil e roteiro próprios para que juntos cubram o sistema inteiro. Os
resultados serão registrados no [laudo de qualidade](../laudos/README.md).

## Testes de regressão

Todo defeito encontrado vira um teste automatizado **antes** de ser corrigido.
Assim o mesmo problema não retorna sem que a suíte acuse.

Os nove defeitos da verificação da versão 1.0 estão em
[`docs/verificacao-v1.md`](verificacao-v1.md), e cada um tem seu teste em
`tests/test_verificacao_v2.py`, identificado pelo código do defeito
(`test_v01_…`, `test_v02_…`).

```bash
pytest tests/test_verificacao_v2.py -v
```

Os defeitos que os testadores relatarem seguirão o mesmo caminho: teste que
reproduz o problema, correção, teste passando.

## Casos de teste manuais

Roteiro dos testes manuais, também distribuído aos testadores.

| ID | Cenário | Passos | Resultado esperado |
|---|---|---|---|
| CT01 | Cadastro e login | Criar conta, sair e entrar novamente | Acesso concedido, nome no cabeçalho |
| CT02 | Abrir chamado | Preencher os quatro campos e enviar | Protocolo gerado, status *Aberto* |
| CT03 | Descrição vazia | Enviar com espaços na descrição | Erro claro, dados preservados |
| CT04 | Anexo grande | Anexar arquivo de 6 MB | Aviso com tamanho e limite |
| CT05 | Filtro por período | Filtrar pelo dia de hoje | Chamados de hoje aparecem, inclusive os da noite |
| CT06 | Busca por protocolo | Informar um protocolo existente | Vai direto ao chamado |
| CT07 | Atribuição | Como técnico, atribuir a si mesmo | Status vira *Em atendimento* |
| CT08 | Encerramento sem solução | Resolver deixando a solução em branco | Recusado com mensagem |
| CT09 | Encerramento válido | Resolver com solução descrita | Status *Resolvido*, data e tempo total |
| CT10 | Isolamento | Como solicitante, abrir a URL do chamado de outro | 403 explicativo |
| CT11 | Área restrita | Como solicitante, acessar `/painel/` pela URL | 403 explicativo |
| CT12 | Desempenho | Listar com mais de 200 chamados | Resposta abaixo de 1 s, paginada |
| CT13 | Celular | Percorrer as telas em 360 px | Sem rolagem horizontal, tudo legível |
| CT14 | Teclado | Navegar só com Tab e Enter | Todos os controles alcançáveis, foco visível |

## Critérios de saída

- [x] 100% dos testes automatizados passando (113)
- [x] Todo requisito funcional com ao menos um teste
- [x] Todo defeito da verificação corrigido e com teste de regressão
- [x] Nenhum defeito conhecido em aberto
- [x] DDL validado contra PostgreSQL 16 real
- [x] Testes de aceitação com usuários concluídos (5 testadores, 18 a 22 de agosto de 2026, formulários em `laudos/`)
