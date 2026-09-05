# Diagramas UML

Os diagramas estão escritos em **Mermaid**, que o GitHub renderiza direto no
navegador — não é preciso abrir nenhuma ferramenta para vê-los.

| Diagrama | Arquivo | O que mostra |
|---|---|---|
| Casos de uso | [casos-de-uso.md](casos-de-uso.md) | Atores e funcionalidades, com `include` e `extend` |
| Classes | [classes.md](classes.md) | Entidades, atributos, métodos e relacionamentos |
| Sequência — abrir chamado | [sequencia-abrir-chamado.md](sequencia-abrir-chamado.md) | Percurso da requisição pelas camadas |
| Sequência — encerrar chamado | [sequencia-encerrar-chamado.md](sequencia-encerrar-chamado.md) | Validação da solução e mudança de status |
| Atividades — triagem | [atividades-triagem.md](atividades-triagem.md) | Fluxo do chamado da abertura ao encerramento |

## O que mudou em relação ao PIT I

| Diagrama | Situação no PIT I | Correção aplicada |
|---|---|---|
| Casos de uso | Sem relacionamentos entre casos | Incluídos `«include»` de autenticação e `«extend»` de reabertura |
| Classes | Multiplicidades ausentes; status e prioridade como texto | Multiplicidades explícitas; domínios viraram classes próprias |
| Sequência | Não existia | Criados dois diagramas para os fluxos principais |
| Atividades | Não existia | Criado o fluxo de triagem |
