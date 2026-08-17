# Diagrama de sequência — Encerrar chamado

```mermaid
sequenceDiagram
    actor T as Técnico
    participant V as View<br/>(detalhe.html + app.js)
    participant C as Controller<br/>(chamados.py)
    participant SV as Service<br/>(chamado_service.py)
    participant M as Model
    participant DB as PostgreSQL

    T->>V: Seleciona o status "Resolvido"
    V->>V: Exibe o campo de solução (obrigatório)
    T->>V: Descreve a solução e confirma
    V->>V: Pede confirmação da ação
    V->>C: POST /chamados/{id}/status

    C->>SV: obter(id, usuario)
    SV->>M: consulta o chamado
    M->>DB: SELECT
    DB-->>M: chamado
    SV->>SV: pode_ver_chamado()

    alt Sem permissão de acesso
        SV-->>C: PermissaoNegada
        C-->>V: 403 Acesso negado
    else Acesso permitido
        C->>SV: mudar_status(chamado, autor, "Resolvido", solucao)
        SV->>SV: Transição está em TRANSICOES[status atual]?

        alt Transição inválida
            SV-->>C: ErroDeNegocio("Não é possível mudar de X para Y")
            C-->>V: Mensagem de erro
        else Autor é solicitante
            SV-->>C: PermissaoNegada("Somente o técnico ou o gestor…")
            C-->>V: Mensagem de erro
        else Solução ausente ou curta
            SV-->>C: ErroDeNegocio(campo="solucao")
            C-->>V: Mensagem de erro
        else Tudo válido
            SV->>M: solucao, data_encerramento, status_id
            SV->>M: registrar() — Interacao "sistema"
            SV->>DB: COMMIT
            DB-->>SV: ok
            SV-->>C: chamado atualizado
            C-->>V: 302 + "Status atualizado."
            V-->>T: Chamado resolvido, com a solução no histórico
        end
    end
```

## Regras exercitadas neste fluxo

| Regra | Efeito |
|---|---|
| RN04 | Só encerra a partir de *Em atendimento* |
| RN05 | Solicitante não resolve o próprio chamado |
| RN06 | Solução com no mínimo 10 caracteres |
| RN07 | O chamado precisa ser visível para quem age sobre ele |
