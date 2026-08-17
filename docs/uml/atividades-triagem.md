# Diagrama de atividades — Triagem e atendimento

```mermaid
flowchart TD
    INICIO([Início]) --> ABRIR[Solicitante abre o chamado]
    ABRIR --> VALIDA{Dados válidos?}
    VALIDA -->|Não| ERRO[Sistema exibe o erro<br/>e devolve o foco ao campo]
    ERRO --> ABRIR
    VALIDA -->|Sim| PROTOCOLO[Sistema gera o protocolo<br/>e grava com status Aberto]

    PROTOCOLO --> FILA[Chamado entra na fila]
    FILA --> TRIAGEM{Técnico ou gestor<br/>avalia o chamado}

    TRIAGEM -->|Fora do escopo<br/>ou duplicado| CANCELA[Status: Cancelado]
    TRIAGEM -->|Válido| ATRIBUI[Atribui técnico responsável<br/>Status: Em atendimento]

    ATRIBUI --> ATENDE[Técnico investiga<br/>e registra interações]
    ATENDE --> PRECISA{Precisa de informação<br/>do solicitante?}
    PRECISA -->|Sim| PERGUNTA[Técnico comenta no chamado]
    PERGUNTA --> RESPONDE[Solicitante responde]
    RESPONDE --> ATENDE
    PRECISA -->|Não| RESOLVEU{Problema resolvido?}

    RESOLVEU -->|Não| ATENDE
    RESOLVEU -->|Sim| SOLUCAO[/Técnico descreve a solução<br/>mínimo de 10 caracteres/]
    SOLUCAO --> ENCERRA[Status: Resolvido<br/>grava data de encerramento]

    ENCERRA --> CONFERE{Solicitante confirma<br/>a resolução?}
    CONFERE -->|Não| REABRE[Reabre o chamado<br/>Status: Aberto]
    REABRE --> FILA
    CONFERE -->|Sim| FIM([Fim])
    CANCELA --> FIM

    style ERRO fill:#fdeceb,stroke:#a3231f
    style CANCELA fill:#f1f2f6,stroke:#5a6478
    style ENCERRA fill:#e4f6ee,stroke:#17694a
    style FIM fill:#e4f6ee,stroke:#17694a
```

## Contagem de SLA

O relógio do SLA começa na **abertura** e para no **encerramento**. O tempo em
que o chamado aguarda resposta do solicitante continua contando — decisão
consciente: pausar a contagem exigiria um status adicional ("Aguardando
solicitante") que ficou para a fase 2. Enquanto isso, o painel mostra o tempo
real de ponta a ponta, que é o que o usuário efetivamente sente.
