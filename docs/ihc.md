# IHC — Interface Humano-Computador

Documento de decisões de interface. Cada princípio do material teórico está
ligado ao que foi efetivamente implementado — não é uma lista de boas intenções.

## Princípios aplicados

### Clareza

A interface evita jargão. O usuário lê "Aberto em" e não `created_at`; lê
"atendimento em até 24h" ao lado da prioridade, em vez de precisar saber o que
significa "SLA Médio".

Todo campo tem `label` visível, e os que exigem algo específico trazem um texto
de apoio abaixo: *"Explique o que aconteceu, quando começou e o que você já
tentou (mínimo de 10 caracteres)"*.

### Consistência

- Um único componente de botão, em três variações (primário, secundário, texto).
- Toda ação principal fica à direita do título da página.
- Toda tela de formulário usa o mesmo bloco de erro, no mesmo lugar.
- Datas sempre no formato `dd/mm/aaaa às hh:mm`, via filtro Jinja único.
- Vocabulário padronizado: sempre "chamado", nunca "ticket" ou "ocorrência".

### Simplicidade

O formulário de abertura pede quatro campos obrigatórios. Nada além. Campos
opcionais são marcados como tal.

O campo de solução **só aparece** quando o status escolhido é "Resolvido" —
divulgação progressiva: o usuário não vê o que ainda não precisa.

### Controle pelo usuário

Nenhuma ação acontece sozinha. Filtros não se aplicam ao digitar; existe um
botão "Filtrar" e um "Limpar". Ações que mudam o estado do chamado pedem
confirmação explícita.

### Relação visível entre causa e efeito

Após qualquer ação, o sistema responde na hora: mensagem de confirmação no topo,
botão que muda para "Enviando…" durante o processamento, e o resultado visível
na tela seguinte.

### Empatia e reversibilidade

- Erro de validação **preserva tudo o que foi digitado** — o usuário nunca
  precisa preencher de novo.
- Chamado resolvido pode ser reaberto.
- Todo formulário tem "Cancelar" ao lado de "Enviar".

### Feedback

| Situação | Resposta |
|---|---|
| Ação concluída | Faixa verde com `role="status"` e `aria-live="polite"` |
| Erro de validação | Bloco vermelho com `role="alert"`, campo destacado e foco automático |
| Processando | Botão desabilitado, texto muda para "Enviando…" |
| Lista vazia | Estado vazio explicando o que fazer, com atalho para a ação |
| Sem permissão | Página 403 explicando o motivo e oferecendo caminhos válidos |

### Estética

Paleta reduzida: um azul de ação, um verde de sucesso, um vermelho de erro,
âmbar para atenção e uma escala de cinzas. Cor nunca é o único indicador —
prioridade e status também vêm escritos por extenso, o que atende a quem não
distingue certas cores.

## Padrão de mensagem de erro

Toda mensagem segue a fórmula **o que aconteceu + como resolver**:

| ❌ Mensagem genérica | ✅ Padrão adotado |
|---|---|
| "Erro ao salvar" | "A descrição deve ter pelo menos 10 caracteres. Explique o que aconteceu e o que você já tentou." |
| "Arquivo inválido" | "O arquivo 'print.png' tem 6,2 MB e o limite é 5 MB. Compacte o arquivo ou envie uma imagem menor." |
| "Acesso negado" | "Esta área é restrita e o seu perfil não tem acesso a ela. Se você precisa dessa permissão, fale com o gestor da equipe." |
| "Transição inválida" | "Não é possível mudar de 'Aberto' para 'Resolvido'. Confira o fluxo de atendimento na documentação." |

A mensagem nasce na camada de serviço, já redigida para o usuário final, e
carrega junto o nome do campo com problema — é isso que permite destacar o
campo certo na tela.

**Exceção deliberada:** o erro de login é genérico ("E-mail ou senha
incorretos"). Dizer "este e-mail não existe" revelaria quais contas existem no
sistema.

![Erro de validação](img/tela-erro-validacao.png)

## Responsividade

Três pontos de quebra, verificados em 360 px, 768 px e 1280 px.

A decisão mais relevante: **em telas pequenas a tabela de chamados vira uma
lista de cartões**. Cada célula passa a exibir seu
rótulo (via `data-rotulo` no HTML e `::before` no CSS), eliminando a rolagem
horizontal.

O menu vira um botão sanduíche com `aria-expanded` correto, e todo alvo de
toque tem no mínimo 44 px de altura.

![Interface no celular](img/tela-celular.png)

## Acessibilidade

| Item | Como foi resolvido |
|---|---|
| Navegação por teclado | Ordem natural do DOM; nenhum `tabindex` positivo |
| Foco visível | `:focus-visible` com contorno âmbar de 3 px |
| Pular para o conteúdo | Primeiro link da página, visível ao receber foco |
| Rótulos | Todo campo tem `label` associado por `for`/`id` |
| Erros | `role="alert"` e foco programático no campo |
| Mensagens de status | `role="status"` com `aria-live="polite"` |
| HTML semântico | `header`, `nav`, `main`, `footer`, `table` com `caption` |
| Estrutura de títulos | Um `h1` por página, hierarquia sem saltos |
| Contraste | Texto principal 4,5:1 ou superior sobre o fundo |
| Movimento reduzido | `prefers-reduced-motion` desliga as transições |
| Idioma | `lang="pt-BR"` no documento |

## Melhorias previstas

As decisões acima vieram de análise e dos princípios do material teórico. A
próxima rodada de ajustes virá dos **testes de aceitação** com usuários reais,
cujos formulários estão em [`laudos/`](../laudos/) — usabilidade é justamente o
tipo de problema que revisão de código não encontra.
