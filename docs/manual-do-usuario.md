# Manual do usuário — ChamaTI

## Antes de começar

Acesse o endereço do sistema pelo navegador. Funciona em computador, tablet e
celular; não é preciso instalar nada.

Seu acesso é o **e-mail** cadastrado e a senha que você definiu.

---

## Para quem pede ajuda (Solicitante)

### Abrir um chamado

1. Clique em **Abrir chamado**.
2. Preencha:

| Campo | O que escrever |
|---|---|
| **Título** | O problema em uma frase. *"Impressora do 2º andar não imprime"* funciona melhor que *"Problema"* |
| **Descrição** | O que aconteceu, quando começou e o que você já tentou |
| **Categoria** | O assunto mais próximo |
| **Prioridade** | O quanto está travando seu trabalho — o prazo de atendimento aparece ao lado |
| **Anexo** | Opcional. Um print da tela de erro acelera muito o atendimento |

3. Clique em **Abrir chamado**.

Você recebe um **protocolo** no formato `2026-000123`. Guarde-o: com ele você
encontra o chamado a qualquer momento.

> **Dica:** quanto mais específica a descrição, menos idas e vindas. "Aparece a
> mensagem 'erro 0x8007' ao imprimir em PDF, desde a atualização de ontem" é
> muito melhor que "não funciona".

### Acompanhar

Em **Chamados** você vê os seus. Clique em um para ver o histórico completo, com
tudo que o técnico registrou.

Para responder ao técnico, use **Adicionar comentário** — não abra um chamado
novo para o mesmo assunto.

### Entender o status

| Status | O que significa |
|---|---|
| **Aberto** | Recebido, aguardando um técnico assumir |
| **Em atendimento** | Alguém está cuidando; o nome aparece em "Técnico" |
| **Resolvido** | Concluído; a solução aplicada fica registrada |
| **Cancelado** | Encerrado sem atendimento (duplicado ou fora do escopo) |

### Se não ficou resolvido

Abra o chamado e mude o status para **Aberto** novamente. Ele volta para a fila
com todo o histórico preservado.

---

## Para quem atende (Técnico)

### Trabalhar a fila

Em **Chamados** você vê a fila completa. Use os filtros para priorizar:

- **Prioridade** *Crítica* e *Alta* primeiro;
- a etiqueta vermelha **SLA vencido** marca o que já passou do prazo;
- **Status** *Aberto* mostra o que ainda não tem responsável.

### Assumir

Abra o chamado, selecione seu nome em **Técnico responsável** e clique em
**Atribuir**. O status passa automaticamente para *Em atendimento*.

### Durante o atendimento

Registre o que fizer em **Adicionar comentário**. Vale o esforço: se o chamado
for reaberto ou passar para outra pessoa, o histórico evita começar do zero.

Precisa de informação? Comente pedindo — o solicitante responde no próprio
chamado.

### Encerrar

1. Em **Mudar status**, escolha **Resolvido**.
2. O campo **Solução aplicada** aparece. Descreva a **causa** e a **correção**.
3. Clique em **Atualizar status**.

> O sistema exige no mínimo 10 caracteres na solução. Não é burocracia: essa é a
> informação que resolve o próximo chamado igual em metade do tempo.

### Fluxo permitido

```
Aberto ──> Em atendimento ──> Resolvido ──> (reabertura) ──> Aberto
   │              │
   └──────────────┴──> Cancelado
```

Não é possível pular de *Aberto* direto para *Resolvido*.

---

## Para quem coordena (Gestor)

### Painel de indicadores

O menu **Painel** mostra:

| Indicador | Como ler |
|---|---|
| **Total de chamados** | Volume acumulado |
| **Em aberto** | O que ainda demanda trabalho |
| **Tempo médio de atendimento** | Horas entre abertura e encerramento |
| **Dentro do SLA** | Percentual encerrado no prazo — abaixo de 80% pede atenção |
| **Por status** | Onde a fila está represada |
| **Por prioridade** | Muita coisa *Crítica* costuma indicar prioridade mal calibrada |
| **Carga por técnico** | Desequilíbrio grande sugere redistribuir |

### Suas permissões

O gestor vê **todos** os chamados, pode atribuir qualquer técnico e alterar
qualquer status.

---

## Perguntas frequentes

**Esqueci meu protocolo.** Entre em **Chamados** — os seus estão todos lá.

**Meu anexo não sobe.** O limite é 5 MB por arquivo. Para prints, salve em JPG
em vez de PNG, ou recorte apenas a parte relevante.

**Abri no chamado errado.** Peça ao técnico para cancelar e abra outro; o
histórico do cancelado é preservado.

**Não vejo o menu "Painel".** Ele é exclusivo do perfil Gestor.

**Não consigo abrir um chamado que me passaram por link.** Solicitantes só
acessam os próprios chamados. Peça ao gestor ou ao técnico responsável.

**A senha não funciona.** Confira maiúsculas e o teclado. Persistindo, peça ao
gestor da equipe para verificar se a conta está ativa.
