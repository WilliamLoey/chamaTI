# Diagrama de sequência — Abrir chamado

Mostra o percurso da requisição pelas camadas MVC, incluindo o caminho de erro.

```mermaid
sequenceDiagram
    actor S as Solicitante
    participant V as View<br/>(novo.html + app.js)
    participant C as Controller<br/>(chamados.py)
    participant SV as Service<br/>(chamado_service.py)
    participant M as Model<br/>(SQLAlchemy)
    participant DB as PostgreSQL

    S->>V: Preenche o formulário
    V->>V: Confere o tamanho do anexo (aviso antecipado)
    V->>C: POST /chamados/novo
    C->>C: Verifica a sessão (login_obrigatorio)
    C->>SV: abrir(solicitante, titulo, descricao, categoria, prioridade, anexos)

    SV->>SV: validar_dados() — trim, tamanhos mínimos, domínios existentes

    alt Dados inválidos
        SV-->>C: ErroDeNegocio(mensagem, campo)
        C-->>V: 400 + formulário preenchido
        V-->>S: Mensagem de erro e foco no campo com problema
    else Dados válidos
        SV->>M: gerar_protocolo()
        M->>DB: SELECT último protocolo do ano
        DB-->>M: 2026-000059
        M-->>SV: 2026-000060

        SV->>M: novo Chamado(status = Aberto)
        SV->>SV: validar_anexo() para cada arquivo
        SV->>M: novo Anexo(...)
        SV->>M: registrar() — Interacao do tipo "sistema"
        SV->>DB: COMMIT
        DB-->>SV: ok

        SV-->>C: chamado
        C-->>V: 302 para /chamados/{id} + mensagem de sucesso
        V-->>S: Tela do chamado com o protocolo
    end
```

## Pontos de atenção

- A conferência do anexo no navegador é **cortesia**, não segurança: o serviço
  refaz a verificação. Um envio direto por `curl` cai na mesma regra.
- O protocolo é gerado dentro da transação, junto com a inserção do chamado.
- A interação inicial do tipo `sistema` garante que todo chamado nasça com
  histórico — nenhum registro fica sem rastro de origem.
