# Laudo de qualidade — ChamaTI

> ⚠️ **Este arquivo é um modelo preenchido com dados de exemplo.**
> Substitua os nomes, as datas e os resultados pelos dos seus testadores reais
> antes de entregar. As evidências vão em `evidencias/`.

## Resumo

| | |
|---|---|
| **Versão testada** | 1.0 |
| **Versão após correções** | 1.1 |
| **Período dos testes** | `[DD/MM/AAAA]` a `[DD/MM/AAAA]` |
| **Testadores** | 5 colegas de curso, nos perfis solicitante, técnico e gestor |
| **Método** | Teste exploratório com roteiro sugerido, registro em formulário padronizado |
| **Evidências** | Prints de tela e logs em [`evidencias/`](evidencias/) |
| **Ocorrências** | 5 (1 alta, 3 médias, 1 baixa) |
| **Situação** | Todas corrigidas e revalidadas · nenhum defeito conhecido em aberto |

## Ocorrências

| ID | Defeito | Origem | Severidade | Correção aplicada | Teste de regressão | Status |
|---|---|---|:-:|---|---|:-:|
| **E-01** | Listagem lenta (6,2 s) com mais de 200 chamados | Colega 5 | Alta | Paginação de 25 itens, índices em `status_id` e `data_abertura`, e `joinedload` para eliminar o N+1 | `test_regressao_e01_listagem_e_paginada` | ✅ 0,4 s |
| **E-02** | Filtro por período excluía chamados do último dia do intervalo | Colega 2 | Média | Fim do intervalo passou a ser o fim do dia (`23:59:59`), com tratamento de fuso via `TIMESTAMPTZ` | `test_regressao_e02_filtro_inclui_o_dia_final` | ✅ |
| **E-03** | Upload acima de 5 MB travava a tela, sem mensagem | Colega 1 | Média | Validação no navegador, no serviço e no banco (`CHECK`), com mensagem informando tamanho real e limite | `test_regressao_e03_anexo_acima_do_limite_e_recusado` | ✅ |
| **E-04** | Descrição só com espaços era aceita; área restrita acessível pela URL | Colega 4 | Média | `trim` + tamanho mínimo no back-end e `CHECK` no banco; permissões verificadas por decorador no servidor | `test_regressao_e04_descricao_so_com_espacos_e_recusada` · `test_regressao_e04_painel_e_bloqueado_para_solicitante_via_url` | ✅ |
| **E-05** | Mensagens de erro fora do campo de visão no celular | Colega 3 | Baixa | Rolagem automática e foco no campo com problema; tabela virou lista de cartões em telas pequenas | Verificação manual em 360 px | ✅ |

## Análise

Três dos cinco defeitos têm a mesma raiz: **confiar no navegador**. O limite de
anexo (E-03), o tamanho da descrição (E-04) e a permissão de acesso (E-04) eram
verificados apenas no front-end. A correção foi arquitetural, não pontual — as
regras migraram para a camada `services/`, com o banco como última defesa.

O E-01 é de outra natureza: não era um erro de lógica, mas de escala. O sistema
funcionava perfeitamente com os 20 chamados que eu usava em desenvolvimento. Só
apareceu quando um testador entrou com a base cheia. Vale a lição: testar com
volume realista desde cedo.

## Melhorias adotadas a partir das sugestões

| Sugestão | Origem | Situação |
|---|---|---|
| Mostrar a contagem total de resultados na listagem | Colega 5 | ✅ Implementada |
| Explicar o motivo na página de acesso negado | Colega 4 | ✅ Implementada |
| Mostrar o prazo de atendimento ao lado da prioridade | Colega 1 | ✅ Implementada |
| Exportar a lista em PDF | Colega 3 | ⏳ Fase 2 |
| Notificar por e-mail ao encerrar | Colega 2 | ⏳ Fase 2 |

## Reteste

Após as correções, os cinco testadores reexecutaram os cenários que haviam
falhado. Todos foram aprovados. A suíte automatizada passou a ter **55 testes**,
dos quais 5 são de regressão dos defeitos acima.

---

## Como preencher com seus dados reais

1. Envie o [formulário de teste](formulario-de-teste.md) aos 5 colegas.
2. Salve cada retorno como `laudo-01.md` … `laudo-05.md` nesta pasta.
3. Salve os prints em `evidencias/`, nomeados por ocorrência
   (`e01-listagem-lenta.png`).
4. Atualize a tabela de ocorrências acima com os defeitos reais.
5. Grave o vídeo mostrando as correções aplicadas e registre o link aqui.
